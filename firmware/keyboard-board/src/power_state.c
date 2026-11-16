/* power_state.c: power manager state machine (see power_state.h). Pure logic, no hardware access. */
#include "power_state.h"

#include <string.h>

static uint32_t elapsed(uint32_t now, uint32_t since)
{
    return (uint32_t)(now - since); /* wraps correctly after 49 days */
}

static void enter(struct power_machine *machine, uint8_t state, uint32_t now)
{
    machine->state = state;
    machine->state_since_ms = now;
}

static void set_outputs_off(struct power_machine *machine)
{
    machine->outputs.boost_enable = false;
    machine->outputs.hold_cm4_off = true;
    machine->outputs.rpiboot_low = false;
    machine->outputs.usb_to_usb_c = false;
    machine->outputs.shutdown_request_low = false;
}

void power_init(struct power_machine *machine)
{
    memset(machine, 0, sizeof(*machine));
    machine->state = POWER_STATE_OFF;
    set_outputs_off(machine);
}

static uint32_t cut_power(struct power_machine *machine, uint32_t now)
{
    enter(machine, POWER_STATE_OFF, now);
    machine->service_mode = false;
    machine->cm4_seen = false;
    machine->shutdown_request_active = false;
    set_outputs_off(machine);
    return POWER_EVENT_POWERED_OFF;
}

static bool battery_is_critical(const struct power_inputs *in)
{
    if (!in->battery_present) {
        return false;
    }
    if (in->battery_percent >= 0 && in->battery_percent <= POWER_CRITICAL_BATTERY_PERCENT) {
        return true;
    }
    return in->battery_millivolts > 0 && in->battery_millivolts <= POWER_CRITICAL_BATTERY_MILLIVOLTS;
}

static uint32_t start_shutdown(struct power_machine *machine, const struct power_inputs *in)
{
    enter(machine, POWER_STATE_SHUTTING_DOWN, in->now_ms);
    if (!in->usb_host_mounted) {
        /* the HID power key cannot reach Linux: pulse the gpio-shutdown line instead */
        machine->shutdown_request_active = true;
        machine->shutdown_request_until_ms = in->now_ms + POWER_SHUTDOWN_REQUEST_PULSE_MS;
    }
    return POWER_EVENT_SEND_POWER_DOWN;
}

static bool running(uint8_t state)
{
    return state == POWER_STATE_BOOTING || state == POWER_STATE_ON;
}

uint32_t power_update(struct power_machine *machine, const struct power_inputs *in)
{
    uint32_t events = 0;
    const uint32_t now = in->now_ms;

    /* ---- power button ---- */
    if (in->button_down && !machine->button_was_down) {
        machine->button_down_since_ms = now;
        machine->button_consumed = false;
        machine->service_keys_at_press = in->function_key_down && in->back_key_down;
    }
    if (in->button_down) {
        const uint32_t held = elapsed(now, machine->button_down_since_ms);
        if (held >= POWER_HARD_CUT_MS && machine->state != POWER_STATE_OFF) {
            events |= cut_power(machine, now) | POWER_EVENT_HARD_CUT;
            machine->button_consumed = true;
        } else if (held >= POWER_LONG_PRESS_MS && !machine->button_consumed) {
            machine->button_consumed = true;
            if (running(machine->state)) {
                events |= POWER_EVENT_BUTTON_LONG | start_shutdown(machine, in);
            }
        }
    } else if (machine->button_was_down) {
        /* released */
        const uint32_t held = elapsed(now, machine->button_down_since_ms);
        if (!machine->button_consumed && held < POWER_LONG_PRESS_MS) {
            if (machine->state == POWER_STATE_OFF) {
                if (battery_is_critical(in) && !in->external_power) {
                    events |= POWER_EVENT_POWER_ON_REFUSED;
                } else {
                    machine->service_mode = machine->service_keys_at_press;
                    machine->critical_battery_reported = false;
                    enter(machine, POWER_STATE_STARTING, now);
                    events |= POWER_EVENT_POWERED_ON;
                }
            } else if (running(machine->state)) {
                events |= POWER_EVENT_BUTTON_SHORT;
            }
        }
    }
    machine->button_was_down = in->button_down;

    /* ---- battery ---- */
    if (in->battery_present && in->battery_percent >= 0) {
        if (in->external_power || in->battery_percent >= POWER_LOW_BATTERY_CLEAR_PERCENT) {
            machine->low_battery_reported = false;
        }
        if (running(machine->state) && !in->external_power) {
            if (battery_is_critical(in) && !machine->critical_battery_reported) {
                machine->critical_battery_reported = true;
                events |= POWER_EVENT_CRITICAL_BATTERY | start_shutdown(machine, in);
            } else if (in->battery_percent <= POWER_LOW_BATTERY_PERCENT && !machine->low_battery_reported) {
                machine->low_battery_reported = true;
                events |= POWER_EVENT_LOW_BATTERY;
            }
        }
    }

    /* ---- states ---- */
    switch (machine->state) {
    case POWER_STATE_STARTING:
        if (elapsed(now, machine->state_since_ms) >= POWER_START_DELAY_MS) {
            enter(machine, POWER_STATE_BOOTING, now);
        }
        break;
    case POWER_STATE_BOOTING:
        if (in->cm4_running || elapsed(now, machine->state_since_ms) >= POWER_BOOT_TIMEOUT_MS) {
            enter(machine, POWER_STATE_ON, now);
        }
        break;
    case POWER_STATE_ON:
        if (in->cm4_poweroff) {
            enter(machine, POWER_STATE_CUTTING, now); /* Linux halted by itself */
        }
        break;
    case POWER_STATE_SHUTTING_DOWN:
        if (in->cm4_poweroff) {
            enter(machine, POWER_STATE_CUTTING, now);
        } else if (elapsed(now, machine->state_since_ms) >= POWER_SHUTDOWN_TIMEOUT_MS) {
            events |= cut_power(machine, now);
        }
        break;
    case POWER_STATE_CUTTING:
        if (elapsed(now, machine->state_since_ms) >= POWER_POWEROFF_MARGIN_MS) {
            events |= cut_power(machine, now);
        }
        break;
    default:
        break;
    }

    /* ---- service mode: hold nRPIBOOT low until the CM4 has been running for a while ---- */
    if (machine->state != POWER_STATE_OFF && (in->cm4_running || in->cm4_3v3_present)) {
        if (!machine->cm4_seen) {
            machine->cm4_seen = true;
            machine->cm4_seen_since_ms = now;
        }
    }

    /* ---- outputs ---- */
    if (machine->state == POWER_STATE_OFF) {
        set_outputs_off(machine);
    } else {
        machine->outputs.boost_enable = true;
        machine->outputs.hold_cm4_off = machine->state == POWER_STATE_STARTING;
        machine->outputs.usb_to_usb_c = machine->service_mode;
        machine->outputs.rpiboot_low = machine->service_mode &&
                                       !(machine->cm4_seen && elapsed(now, machine->cm4_seen_since_ms) >= POWER_RPIBOOT_HOLD_MS);
        if (machine->shutdown_request_active && (int32_t)(now - machine->shutdown_request_until_ms) >= 0) {
            machine->shutdown_request_active = false;
        }
        machine->outputs.shutdown_request_low = machine->shutdown_request_active;
    }
    return events;
}

const char *power_state_name(uint8_t state)
{
    switch (state) {
    case POWER_STATE_OFF:
        return "off";
    case POWER_STATE_STARTING:
        return "starting";
    case POWER_STATE_BOOTING:
        return "booting";
    case POWER_STATE_ON:
        return "on";
    case POWER_STATE_SHUTTING_DOWN:
        return "shutting-down";
    case POWER_STATE_CUTTING:
        return "cutting";
    default:
        return "unknown";
    }
}
