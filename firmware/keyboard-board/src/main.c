/*
 * main.c: Terminal 1 keyboard and power board firmware (RP2040, Pico SDK + TinyUSB).
 *
 * One cooperative loop, no RTOS:
 *   every 1 ms   scan the key matrix and power button, debounce, apply the key map, queue HID reports
 *   always       read trackpad motion when its MOTION line is low; run the power state machine; service USB
 *   every 1 s    (or at once on the PMIC interrupt line) read the BQ25895 charger and MAX17048 gauge
 *   every 10 s   and on change: "BAT <percent> <millivolts> <state>" on the CDC status port
 * The pure logic lives in keymap.c, sticky_modifiers.c, debounce.c, hid_report.c, trackpad_logic.c, power_state.c and
 * status_protocol.c, and is unit-tested on a computer (test/).
 *
 * Bench build (TERMINAL_BOARD_BENCH = 1, plain Raspberry Pi Pico): never drives GPIO 23 or reads GPIO 24 / 29 (Pico
 * SMPS mode, VBUS sense and VSYS/3); GPIO 25 (Pico LED) shows the boost-enable output; missing I2C devices are skipped.
 */
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "backlight.h"
#include "board.h"
#include "bq25895.h"
#include "debounce.h"
#include "hardware/gpio.h"
#include "hardware/watchdog.h"
#include "hid_report.h"
#include "i2c_bus.h"
#include "keyboard_matrix.h"
#include "keymap.h"
#include "max17048.h"
#include "pico/stdlib.h"
#include "power_state.h"
#include "status_protocol.h"
#include "trackpad.h"
#include "trackpad_logic.h"
#include "tusb.h"
#include "usb_descriptors.h"
#include "version.h"

#define SCAN_PERIOD_MS 1
#define BATTERY_READ_PERIOD_MS 1000
#define INTERRUPT_READ_MINIMUM_MS 50 /* a stuck interrupt line must not flood the I2C bus */
#define BATTERY_PRESENT_MILLIVOLTS 2500
#define DEFAULT_BACKLIGHT_PERCENT 30
#define REFUSED_FLASH_MS 300
#define WATCHDOG_TIMEOUT_MS 2000

static struct debounce debounce;
static struct keymap_state keymap;
static struct hid_report_state reports;
static struct trackpad_logic trackpad_motion;
static struct power_machine power;
static struct status_line_reader reader;

static bool charger_present;
static bool gauge_present;
static bool trackpad_present;
static struct bq25895_status charger;
static struct max17048_reading gauge;

static uint8_t backlight_percent = DEFAULT_BACKLIGHT_PERCENT;
static uint32_t backlight_flash_until_ms;
static uint8_t mouse_buttons;
static int mouse_x;
static int mouse_y;
static bool mouse_changed;
static uint8_t power_down_pending; /* 2 = send press, 1 = send release */

/* ------------------------------------------------------------------ status port */

static void status_send(const char *line, size_t length)
{
    if (length == 0 || !tud_cdc_n_connected(CDC_STATUS_PORT)) {
        return; /* nobody listening: battery lines are repeated every 10 s anyway */
    }
    if (tud_cdc_n_write_available(CDC_STATUS_PORT) < length) {
        return;
    }
    tud_cdc_n_write(CDC_STATUS_PORT, line, (uint32_t)length);
    tud_cdc_n_write_flush(CDC_STATUS_PORT);
}

static void status_send_power_event(const char *event)
{
    char line[STATUS_LINE_MAX];
    status_send(line, status_format_power_event(line, sizeof(line), event));
}

static void handle_status_input(void)
{
    char line[STATUS_LINE_MAX];
    while (tud_cdc_n_available(CDC_STATUS_PORT)) {
        const int32_t character = tud_cdc_n_read_char(CDC_STATUS_PORT);
        if (character < 0) {
            break;
        }
        if (!status_reader_feed(&reader, (char)character, line, sizeof(line))) {
            continue;
        }
        const struct status_command command = status_parse_line(line);
        if (command.kind == STATUS_COMMAND_BACKLIGHT) {
            backlight_percent = (uint8_t)command.value;
        } else if (command.kind == STATUS_COMMAND_MODE) {
            keymap.trackpad_mode = (uint8_t)command.value;
        }
        char reply[STATUS_LINE_MAX];
        status_send(reply, status_reply(&command, reply, sizeof(reply), FIRMWARE_VERSION, BOARD_REVISION));
    }
}

/* ------------------------------------------------------------------ battery */

static bool battery_present(void)
{
    return gauge_present && gauge.present && gauge.cell_millivolts > BATTERY_PRESENT_MILLIVOLTS;
}

static void read_battery(void)
{
    if (charger_present) {
        bq25895_read_status(&charger);
    }
    if (gauge_present) {
        max17048_read(&gauge);
        max17048_clear_alert();
    }
}

static void report_battery(uint32_t now, bool force)
{
    static uint32_t last_report_ms;
    static int last_percent = -1;
    static uint8_t last_state = 0xFF;
    const bool present = battery_present();
    const int percent = present ? gauge.percent : 0;
    const int millivolts = present ? gauge.cell_millivolts : 0;
    const uint8_t state = status_battery_state(present, charger.present && charger.power_good, charger.charge_status);
    if (force || percent != last_percent || state != last_state ||
        (uint32_t)(now - last_report_ms) >= STATUS_BATTERY_PERIOD_MS) {
        char line[STATUS_LINE_MAX];
        status_send(line, status_format_battery(line, sizeof(line), percent, millivolts, state));
        last_report_ms = now;
        last_percent = percent;
        last_state = state;
    }
}

/* ------------------------------------------------------------------ keys and trackpad */

static bool keyboard_active(void)
{
    return power.state != POWER_STATE_OFF;
}

static void queue_keyboard_report(void)
{
    hid_report_queue_current(&reports, keymap_base_modifiers(&keymap));
}

static void apply_key_action(struct keymap_action action)
{
    switch (action.kind) {
    case KEYMAP_ACTION_KEY_PRESS:
        hid_report_press(&reports, action.slot, action.usage, action.modifiers);
        break;
    case KEYMAP_ACTION_KEY_RELEASE:
        hid_report_release(&reports, action.slot);
        break;
    case KEYMAP_ACTION_MOUSE_PRESS:
        mouse_buttons |= 0x01;
        mouse_changed = true;
        break;
    case KEYMAP_ACTION_MOUSE_RELEASE:
        mouse_buttons &= (uint8_t)~0x01;
        mouse_changed = true;
        break;
    default:
        break;
    }
    queue_keyboard_report(); /* modifier keys change the report too (Ctrl held for Ctrl + click) */
}

static void scan_keys(void)
{
    const uint64_t changed = debounce_update(&debounce, keyboard_matrix_scan());
    if (!changed || !keyboard_active()) {
        return;
    }
    for (uint8_t key = 0; key < KEY_COUNT; key++) {
        if (changed & ((uint64_t)1 << key)) {
            apply_key_action(keymap_handle_key(&keymap, key, debounce_is_pressed(&debounce, key)));
        }
    }
}

static void read_trackpad(uint32_t now)
{
    int dx, dy;
    if (!trackpad_present || !keyboard_active() || !trackpad_read_motion(&dx, &dy)) {
        return;
    }
    if (keymap.trackpad_mode == TRACKPAD_MODE_MOUSE) {
        mouse_x += dx;
        mouse_y += dy;
        return;
    }
    uint8_t arrows[TRACKPAD_MAX_ARROWS_PER_UPDATE];
    const int count = trackpad_logic_arrows(&trackpad_motion, dx, dy, now, arrows, TRACKPAD_MAX_ARROWS_PER_UPDATE);
    for (int i = 0; i < count; i++) {
        const uint8_t modifiers = keymap_take_modifiers_for_synthetic_key(&keymap);
        hid_report_press(&reports, HID_REPORT_SYNTHETIC_SLOT, trackpad_arrow_usage(arrows[i]), modifiers);
        queue_keyboard_report();
        hid_report_release(&reports, HID_REPORT_SYNTHETIC_SLOT);
        queue_keyboard_report();
    }
}

static void send_usb_reports(void)
{
    if (!tud_mounted()) {
        struct hid_keyboard_report report;
        while (hid_report_peek(&reports, &report)) {
            hid_report_pop(&reports); /* no host: nothing to type into */
        }
        mouse_x = mouse_y = 0;
        mouse_changed = false;
        return;
    }
    if (tud_suspended()) {
        struct hid_keyboard_report report;
        if (hid_report_peek(&reports, &report) || power_down_pending) {
            tud_remote_wakeup();
        }
        return;
    }
    struct hid_keyboard_report report;
    if (tud_hid_n_ready(HID_INSTANCE_KEYBOARD) && hid_report_peek(&reports, &report)) {
        if (tud_hid_n_keyboard_report(HID_INSTANCE_KEYBOARD, 0, report.modifiers, report.keys)) {
            hid_report_pop(&reports);
        }
    }
    if (tud_hid_n_ready(HID_INSTANCE_MOUSE) && (mouse_changed || mouse_x || mouse_y)) {
        int8_t x, y;
        trackpad_logic_mouse(mouse_x, mouse_y, &x, &y);
        if (tud_hid_n_mouse_report(HID_INSTANCE_MOUSE, 0, mouse_buttons, x, y, 0, 0)) {
            mouse_x = mouse_y = 0;
            mouse_changed = false;
        }
    }
    if (power_down_pending && tud_hid_n_ready(HID_INSTANCE_CONTROL)) {
        const uint8_t value = power_down_pending == 2 ? SYSTEM_CONTROL_POWER_DOWN : SYSTEM_CONTROL_NONE;
        if (tud_hid_n_report(HID_INSTANCE_CONTROL, REPORT_ID_SYSTEM, &value, 1)) {
            power_down_pending--;
        }
    }
}

/* ------------------------------------------------------------------ power */

static void output_pin(uint8_t pin, bool level)
{
    gpio_init(pin);
    gpio_put(pin, level);
    gpio_set_dir(pin, GPIO_OUT);
}

static void input_pin_pulled_down(uint8_t pin)
{
    gpio_init(pin);
    gpio_set_dir(pin, GPIO_IN);
    gpio_pull_down(pin);
}

static void power_pins_init(void)
{
    output_pin(PIN_CM4_GLOBAL_ENABLE_HOLD, true); /* CM4 held off first */
    output_pin(PIN_BOOST_ENABLE, false);
    output_pin(PIN_CM4_RPIBOOT, false);
    output_pin(PIN_USB_SELECT, false);
    input_pin_pulled_down(PIN_CM4_POWEROFF);
#if !TERMINAL_BOARD_BENCH
    output_pin(PIN_CM4_SHUTDOWN_REQUEST, false);
    input_pin_pulled_down(PIN_CM4_RUN_POWER_GOOD);
    input_pin_pulled_down(PIN_CM4_3V3_SENSE);
#endif
    gpio_init(PIN_POWER_INTERRUPT);
    gpio_set_dir(PIN_POWER_INTERRUPT, GPIO_IN);
    gpio_pull_up(PIN_POWER_INTERRUPT);
}

static void apply_power_outputs(void)
{
    gpio_put(PIN_BOOST_ENABLE, power.outputs.boost_enable); /* bench: the Pico LED */
    gpio_put(PIN_CM4_GLOBAL_ENABLE_HOLD, power.outputs.hold_cm4_off);
    gpio_put(PIN_CM4_RPIBOOT, power.outputs.rpiboot_low);
    gpio_put(PIN_USB_SELECT, power.outputs.usb_to_usb_c);
#if !TERMINAL_BOARD_BENCH
    gpio_put(PIN_CM4_SHUTDOWN_REQUEST, power.outputs.shutdown_request_low);
#endif
}

static void run_power(uint32_t now)
{
    struct power_inputs inputs = {0};
    inputs.now_ms = now;
    inputs.button_down = debounce_is_pressed(&debounce, INPUT_INDEX_POWER_BUTTON);
    inputs.function_key_down = debounce_is_pressed(&debounce, KEY_INDEX_FUNCTION);
    inputs.back_key_down = debounce_is_pressed(&debounce, KEY_INDEX_BACK);
#if !TERMINAL_BOARD_BENCH
    inputs.cm4_running = gpio_get(PIN_CM4_RUN_POWER_GOOD);
    inputs.cm4_3v3_present = gpio_get(PIN_CM4_3V3_SENSE);
#endif
    inputs.cm4_poweroff = gpio_get(PIN_CM4_POWEROFF);
    inputs.usb_host_mounted = tud_mounted() && !tud_suspended();
    inputs.external_power = charger.present && charger.power_good;
    inputs.battery_present = battery_present();
    inputs.battery_percent = inputs.battery_present ? gauge.percent : -1;
    inputs.battery_millivolts = inputs.battery_present ? gauge.cell_millivolts : -1;

    const uint8_t previous_state = power.state;
    const uint32_t events = power_update(&power, &inputs);
    apply_power_outputs();

    if (events & POWER_EVENT_BUTTON_SHORT) {
        status_send_power_event("button-short");
    }
    if (events & POWER_EVENT_BUTTON_LONG) {
        status_send_power_event("button-long");
    }
    if (events & POWER_EVENT_LOW_BATTERY) {
        status_send_power_event("low-battery");
    }
    if (events & POWER_EVENT_CRITICAL_BATTERY) {
        status_send_power_event("critical-battery");
    }
    if (events & POWER_EVENT_SEND_POWER_DOWN) {
        power_down_pending = 2;
    }
    if (events & POWER_EVENT_POWER_ON_REFUSED) {
        backlight_flash_until_ms = now + REFUSED_FLASH_MS; /* a short flash says "battery too low" */
    }
    if (previous_state == POWER_STATE_OFF && power.state != POWER_STATE_OFF) {
        keymap_init(&keymap);
        hid_report_init(&reports);
        if (trackpad_present) {
            trackpad_set_shutdown(false);
        }
    }
    if (previous_state != POWER_STATE_OFF && power.state == POWER_STATE_OFF) {
        hid_report_release_all(&reports);
        mouse_buttons = 0;
        power_down_pending = 0;
        if (trackpad_present) {
            trackpad_set_shutdown(true); /* save power while the device is off */
        }
    }

    const bool flashing = (int32_t)(backlight_flash_until_ms - now) > 0;
    backlight_set_percent(flashing ? 100 : (power.state == POWER_STATE_OFF ? 0 : backlight_percent));
}

/* ------------------------------------------------------------------ TinyUSB callbacks */

uint16_t tud_hid_get_report_cb(uint8_t instance, uint8_t report_id, hid_report_type_t report_type, uint8_t *buffer,
                               uint16_t length)
{
    (void)instance;
    (void)report_id;
    (void)report_type;
    (void)buffer;
    (void)length;
    return 0;
}

void tud_hid_set_report_cb(uint8_t instance, uint8_t report_id, hid_report_type_t report_type, uint8_t const *buffer,
                           uint16_t size)
{
    /* keyboard LEDs (Caps Lock...) are not shown: the Q20 has no LEDs of its own */
    (void)instance;
    (void)report_id;
    (void)report_type;
    (void)buffer;
    (void)size;
}

void tud_cdc_line_state_cb(uint8_t port, bool data_terminal_ready, bool request_to_send)
{
    (void)request_to_send;
    if (port == CDC_STATUS_PORT && data_terminal_ready) {
        report_battery(to_ms_since_boot(get_absolute_time()), true); /* a new listener gets the battery at once */
    }
}

/* ------------------------------------------------------------------ main */

int main(void)
{
    power_pins_init();
    power_init(&power);
    apply_power_outputs();

    keyboard_matrix_init();
    debounce_init(&debounce, INPUT_COUNT);
    keymap_init(&keymap);
    hid_report_init(&reports);
    trackpad_logic_init(&trackpad_motion);
    status_reader_init(&reader);
    backlight_init();

    i2c_bus_init();
    charger_present = bq25895_init();
    gauge_present = max17048_init(POWER_LOW_BATTERY_PERCENT);
    trackpad_present = trackpad_init();
    if (trackpad_present) {
        trackpad_set_shutdown(true); /* off until the device is switched on */
    }
    read_battery();

    tusb_init();
    watchdog_enable(WATCHDOG_TIMEOUT_MS, true);

    uint32_t last_scan_ms = 0;
    uint32_t last_battery_ms = 0;
    while (true) {
        watchdog_update();
        tud_task();
        const uint32_t now = to_ms_since_boot(get_absolute_time());

        if ((uint32_t)(now - last_scan_ms) >= SCAN_PERIOD_MS) {
            last_scan_ms = now;
            scan_keys();
        }
        read_trackpad(now);

        const uint32_t since_battery = (uint32_t)(now - last_battery_ms);
        if ((!gpio_get(PIN_POWER_INTERRUPT) && since_battery >= INTERRUPT_READ_MINIMUM_MS) ||
            since_battery >= BATTERY_READ_PERIOD_MS) {
            last_battery_ms = now;
            read_battery();
            report_battery(now, false);
        }

        run_power(now);
        handle_status_input();
        send_usb_reports();
    }
}
