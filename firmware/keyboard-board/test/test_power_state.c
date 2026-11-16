/* test_power_state.c: host tests for the power manager state machine (src/power_state.c). */
#include "power_state.h"
#include "test_framework.h"

static struct power_machine machine;
static struct power_inputs inputs;
static uint32_t events_seen;

static void reset(void)
{
    power_init(&machine);
    inputs = (struct power_inputs){0};
    inputs.now_ms = 1000;
    inputs.battery_present = true;
    inputs.battery_percent = 80;
    inputs.battery_millivolts = 3900;
    events_seen = 0;
}

/* advance time in 10 ms steps, collecting events */
static void run_for(uint32_t milliseconds)
{
    for (uint32_t t = 0; t < milliseconds; t += 10) {
        inputs.now_ms += 10;
        events_seen |= power_update(&machine, &inputs);
    }
}

static void press_for(uint32_t milliseconds)
{
    inputs.button_down = true;
    run_for(milliseconds);
    inputs.button_down = false;
    run_for(20);
}

static void power_on(void)
{
    press_for(200);
    run_for(100);
    inputs.cm4_running = true;
    inputs.cm4_3v3_present = true;
    run_for(20);
}

static void test_power_on_and_off(void)
{
    reset();
    events_seen |= power_update(&machine, &inputs);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state);
    CHECK(machine.outputs.hold_cm4_off);
    CHECK(!machine.outputs.boost_enable);

    /* short press: boost first, GLOBAL_EN released 50 ms later */
    inputs.button_down = true;
    run_for(200);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state); /* acts on release */
    inputs.button_down = false;
    run_for(10);
    CHECK_EQUAL(POWER_STATE_STARTING, machine.state);
    CHECK(machine.outputs.boost_enable);
    CHECK(machine.outputs.hold_cm4_off);
    CHECK(events_seen & POWER_EVENT_POWERED_ON);
    run_for(60);
    CHECK_EQUAL(POWER_STATE_BOOTING, machine.state);
    CHECK(!machine.outputs.hold_cm4_off);
    CHECK(!machine.outputs.rpiboot_low);
    CHECK(!machine.outputs.usb_to_usb_c);
    inputs.cm4_running = true;
    run_for(10);
    CHECK_EQUAL(POWER_STATE_ON, machine.state);

    /* short press while on: just an event */
    events_seen = 0;
    press_for(300);
    CHECK(events_seen & POWER_EVENT_BUTTON_SHORT);
    CHECK_EQUAL(POWER_STATE_ON, machine.state);

    /* long press: power-down request, then wait for CM4_POWEROFF */
    events_seen = 0;
    inputs.usb_host_mounted = true;
    inputs.button_down = true;
    run_for(2100);
    CHECK(events_seen & POWER_EVENT_BUTTON_LONG);
    CHECK(events_seen & POWER_EVENT_SEND_POWER_DOWN);
    CHECK_EQUAL(POWER_STATE_SHUTTING_DOWN, machine.state);
    CHECK(!machine.outputs.shutdown_request_low); /* USB mounted: no backup pulse */
    inputs.button_down = false;
    run_for(5000);
    CHECK_EQUAL(POWER_STATE_SHUTTING_DOWN, machine.state);
    CHECK(machine.outputs.boost_enable);
    inputs.cm4_poweroff = true;
    run_for(500);
    CHECK_EQUAL(POWER_STATE_CUTTING, machine.state);
    CHECK(machine.outputs.boost_enable); /* margin before the cut */
    run_for(600);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state);
    CHECK(!machine.outputs.boost_enable);
    CHECK(machine.outputs.hold_cm4_off);
    CHECK(events_seen & POWER_EVENT_POWERED_OFF);
}

static void test_shutdown_timeout_and_backup_pulse(void)
{
    reset();
    power_on();
    CHECK_EQUAL(POWER_STATE_ON, machine.state);
    inputs.usb_host_mounted = false;
    inputs.button_down = true;
    run_for(2010);
    CHECK_EQUAL(POWER_STATE_SHUTTING_DOWN, machine.state);
    CHECK(machine.outputs.shutdown_request_low); /* backup pulse on CM4_SHUTDOWN_REQ */
    inputs.button_down = false;
    run_for(300);
    CHECK(!machine.outputs.shutdown_request_low); /* pulse ended */
    run_for(POWER_SHUTDOWN_TIMEOUT_MS - 2000);
    CHECK_EQUAL(POWER_STATE_SHUTTING_DOWN, machine.state);
    run_for(2000);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state); /* 30 s timeout */
}

static void test_hard_cut(void)
{
    reset();
    power_on();
    events_seen = 0;
    inputs.button_down = true;
    run_for(9900);
    CHECK_EQUAL(POWER_STATE_SHUTTING_DOWN, machine.state);
    run_for(200);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state);
    CHECK(events_seen & POWER_EVENT_HARD_CUT);
    run_for(3000); /* still held: stays off */
    inputs.button_down = false;
    run_for(100);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state); /* release after a hard cut does not power on */
}

static void test_linux_halts_by_itself(void)
{
    reset();
    power_on();
    inputs.cm4_poweroff = true;
    run_for(100);
    CHECK_EQUAL(POWER_STATE_CUTTING, machine.state);
    run_for(1000);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state);
}

static void test_long_press_when_off_does_nothing(void)
{
    reset();
    press_for(3000);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state);
}

static void test_service_mode(void)
{
    reset();
    inputs.function_key_down = true;
    inputs.back_key_down = true;
    inputs.button_down = true;
    run_for(100);
    inputs.function_key_down = false; /* keys may be let go before the button */
    inputs.back_key_down = false;
    inputs.button_down = false;
    run_for(10);
    CHECK_EQUAL(POWER_STATE_STARTING, machine.state);
    CHECK(machine.service_mode);
    CHECK(machine.outputs.usb_to_usb_c);
    CHECK(machine.outputs.rpiboot_low); /* low before GLOBAL_EN is released */
    CHECK(machine.outputs.hold_cm4_off);
    run_for(100);
    CHECK(!machine.outputs.hold_cm4_off);
    CHECK(machine.outputs.rpiboot_low);
    inputs.cm4_3v3_present = true;
    run_for(2000);
    CHECK(machine.outputs.rpiboot_low);
    run_for(1100);
    CHECK(!machine.outputs.rpiboot_low); /* released 3 s after the CM4 was seen */
    CHECK(machine.outputs.usb_to_usb_c); /* USB stays on USB-C until power-off */
    /* hard cut ends service mode */
    inputs.button_down = true;
    run_for(10100);
    inputs.button_down = false;
    run_for(20);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state);
    CHECK(!machine.service_mode);
    CHECK(!machine.outputs.usb_to_usb_c);
    /* a normal power-on afterwards is not in service mode */
    inputs.cm4_3v3_present = false;
    press_for(100);
    CHECK(!machine.service_mode);

    /* only one of the two keys: normal start */
    reset();
    inputs.function_key_down = true;
    press_for(100);
    CHECK(!machine.service_mode);
}

static void test_battery(void)
{
    reset();
    power_on();
    events_seen = 0;
    inputs.battery_percent = 10;
    run_for(20);
    CHECK(events_seen & POWER_EVENT_LOW_BATTERY);
    events_seen = 0;
    run_for(1000);
    CHECK(!(events_seen & POWER_EVENT_LOW_BATTERY)); /* once per discharge */
    inputs.battery_percent = 3;
    run_for(20);
    CHECK(events_seen & POWER_EVENT_CRITICAL_BATTERY);
    CHECK(events_seen & POWER_EVENT_SEND_POWER_DOWN);
    CHECK_EQUAL(POWER_STATE_SHUTTING_DOWN, machine.state);
    inputs.cm4_poweroff = true;
    run_for(1100);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state);
    inputs.cm4_poweroff = false;
    inputs.cm4_running = false;
    inputs.cm4_3v3_present = false;

    /* refuse power-on when critical, unless USB power is present */
    events_seen = 0;
    press_for(100);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state);
    CHECK(events_seen & POWER_EVENT_POWER_ON_REFUSED);
    inputs.external_power = true;
    press_for(100);
    CHECK(machine.state != POWER_STATE_OFF);

    /* critical by voltage alone */
    reset();
    power_on();
    events_seen = 0;
    inputs.battery_percent = 20;
    inputs.battery_millivolts = 3300;
    run_for(20);
    CHECK(events_seen & POWER_EVENT_CRITICAL_BATTERY);

    /* no battery (bench or USB only): never a battery event */
    reset();
    inputs.battery_present = false;
    inputs.battery_percent = 0;
    inputs.battery_millivolts = 0;
    power_on();
    events_seen = 0;
    run_for(1000);
    CHECK(!(events_seen & (POWER_EVENT_LOW_BATTERY | POWER_EVENT_CRITICAL_BATTERY)));
    CHECK_EQUAL(POWER_STATE_ON, machine.state);
}

static void test_boot_timeout_without_cm4(void)
{
    reset();
    press_for(100);
    run_for(POWER_BOOT_TIMEOUT_MS + 100);
    CHECK_EQUAL(POWER_STATE_ON, machine.state); /* bench: no CM4, still usable */
}

static void test_tick_wrap(void)
{
    reset();
    inputs.now_ms = 0xFFFFFF00u;
    power_on();
    CHECK_EQUAL(POWER_STATE_ON, machine.state);
    inputs.cm4_poweroff = true;
    run_for(1100);
    CHECK_EQUAL(POWER_STATE_OFF, machine.state);
    CHECK(power_state_name(POWER_STATE_SHUTTING_DOWN)[0] == 's');
}

int main(void)
{
    test_power_on_and_off();
    test_shutdown_timeout_and_backup_pulse();
    test_hard_cut();
    test_linux_halts_by_itself();
    test_long_press_when_off_does_nothing();
    test_service_mode();
    test_battery();
    test_boot_timeout_without_cm4();
    test_tick_wrap();
    return test_summary("power_state");
}
