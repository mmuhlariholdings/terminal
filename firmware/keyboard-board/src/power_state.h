/*
 * power_state.h: the power manager state machine (pure logic, unit-tested on the host).
 *
 * The RP2040 is always powered. It switches the TPS61089 boost (+5V_CM4) and the CM4's GLOBAL_EN, and turns the CM4 off
 * only after Linux has halted, the way a phone does. Times come in as millisecond ticks, so the tests can drive it.
 *
 *   OFF --short press--> STARTING (boost on, CM4 still held off) --50 ms--> BOOTING (GLOBAL_EN released)
 *   BOOTING --RUN_PG high, or 15 s--> ON
 *   ON / BOOTING --long press 2 s or critical battery--> SHUTTING_DOWN (HID System Power Down sent; CM4_SHUTDOWN_REQ
 *       pulsed as a backup when USB is not mounted) --CM4_POWEROFF high--> CUTTING --1 s--> OFF;  --30 s timeout--> OFF
 *   ON --CM4_POWEROFF high (Linux halted by itself)--> CUTTING --1 s--> OFF
 *   any state --button held 10 s--> OFF (hard cut)
 * Service mode: Fn + Back held while the power button is pressed in OFF: the USB switch connects the CM4 to the USB-C
 * port and CM4_nRPIBOOT is held low until 3 s after the CM4 is seen running; it ends at the next power-off.
 * Power-on is refused when the battery is critical and no USB power is present.
 */
#ifndef TERMINAL_POWER_STATE_H
#define TERMINAL_POWER_STATE_H

#include <stdbool.h>
#include <stdint.h>

#define POWER_START_DELAY_MS 50
#define POWER_LONG_PRESS_MS 2000
#define POWER_HARD_CUT_MS 10000
#define POWER_BOOT_TIMEOUT_MS 15000
#define POWER_SHUTDOWN_TIMEOUT_MS 30000
#define POWER_POWEROFF_MARGIN_MS 1000
#define POWER_RPIBOOT_HOLD_MS 3000
#define POWER_SHUTDOWN_REQUEST_PULSE_MS 200
#define POWER_LOW_BATTERY_PERCENT 10
#define POWER_LOW_BATTERY_CLEAR_PERCENT 15
#define POWER_CRITICAL_BATTERY_PERCENT 3
#define POWER_CRITICAL_BATTERY_MILLIVOLTS 3350

enum power_state {
    POWER_STATE_OFF = 0,
    POWER_STATE_STARTING,
    POWER_STATE_BOOTING,
    POWER_STATE_ON,
    POWER_STATE_SHUTTING_DOWN,
    POWER_STATE_CUTTING,
};

enum power_event {
    POWER_EVENT_BUTTON_SHORT = 1u << 0,        /* "PWR button-short" */
    POWER_EVENT_BUTTON_LONG = 1u << 1,         /* "PWR button-long" */
    POWER_EVENT_LOW_BATTERY = 1u << 2,         /* "PWR low-battery" */
    POWER_EVENT_CRITICAL_BATTERY = 1u << 3,    /* "PWR critical-battery" */
    POWER_EVENT_SEND_POWER_DOWN = 1u << 4,     /* send HID System Power Down */
    POWER_EVENT_POWER_ON_REFUSED = 1u << 5,    /* battery too low to start */
    POWER_EVENT_POWERED_ON = 1u << 6,
    POWER_EVENT_POWERED_OFF = 1u << 7,
    POWER_EVENT_HARD_CUT = 1u << 8,
};

struct power_inputs {
    uint32_t now_ms;
    bool button_down;          /* debounced power button */
    bool function_key_down;    /* debounced Fn key (service mode) */
    bool back_key_down;        /* debounced Back key (service mode) */
    bool cm4_running;          /* CM4_RUN_PG */
    bool cm4_3v3_present;      /* CM4_3V3_SENSE */
    bool cm4_poweroff;         /* CM4_POWEROFF: Linux has halted */
    bool usb_host_mounted;     /* the RP2040's USB device is configured by Linux */
    bool external_power;       /* BQ25895 power good: USB-C supply present */
    bool battery_present;
    int battery_percent;       /* -1 = unknown */
    int battery_millivolts;    /* -1 = unknown */
};

struct power_outputs {
    bool boost_enable;          /* PIN_BOOST_ENABLE */
    bool hold_cm4_off;          /* PIN_CM4_GLOBAL_ENABLE_HOLD */
    bool rpiboot_low;           /* PIN_CM4_RPIBOOT */
    bool usb_to_usb_c;          /* PIN_USB_SELECT */
    bool shutdown_request_low;  /* PIN_CM4_SHUTDOWN_REQUEST */
};

struct power_machine {
    uint8_t state; /* enum power_state */
    bool service_mode;
    uint32_t state_since_ms;
    /* button */
    bool button_was_down;
    uint32_t button_down_since_ms;
    bool button_consumed;      /* long press or hard cut already acted on: ignore the release */
    bool service_keys_at_press;
    /* service mode */
    bool cm4_seen;
    uint32_t cm4_seen_since_ms;
    /* shutdown request pulse */
    bool shutdown_request_active;
    uint32_t shutdown_request_until_ms;
    /* battery */
    bool low_battery_reported;
    bool critical_battery_reported;
    struct power_outputs outputs;
};

void power_init(struct power_machine *machine);

/* Run one step; returns a mask of enum power_event. Outputs are in machine->outputs. */
uint32_t power_update(struct power_machine *machine, const struct power_inputs *inputs);

const char *power_state_name(uint8_t state);

#endif
