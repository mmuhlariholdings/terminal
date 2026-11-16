/* hid_report.c: held keys -> queued HID boot keyboard reports (see hid_report.h). Pure logic. */
#include "hid_report.h"

#include <string.h>

void hid_report_init(struct hid_report_state *state)
{
    memset(state, 0, sizeof(*state));
}

void hid_report_press(struct hid_report_state *state, uint8_t slot, uint8_t usage, uint8_t modifiers)
{
    hid_report_release(state, slot);
    if (state->held_count == HID_REPORT_MAX_KEYS) {
        /* more than six keys: drop the oldest (boot protocol limit) */
        memmove(&state->held[0], &state->held[1], sizeof(state->held[0]) * (HID_REPORT_MAX_KEYS - 1));
        state->held_count--;
    }
    state->held[state->held_count].slot = slot;
    state->held[state->held_count].usage = usage;
    state->held[state->held_count].modifiers = modifiers;
    state->held_count++;
}

void hid_report_release(struct hid_report_state *state, uint8_t slot)
{
    for (uint8_t i = 0; i < state->held_count; i++) {
        if (state->held[i].slot == slot) {
            memmove(&state->held[i], &state->held[i + 1], sizeof(state->held[0]) * (state->held_count - i - 1));
            state->held_count--;
            return;
        }
    }
}

void hid_report_release_all(struct hid_report_state *state)
{
    state->held_count = 0;
}

bool hid_report_queue_current(struct hid_report_state *state, uint8_t base_modifiers)
{
    struct hid_keyboard_report report;
    memset(&report, 0, sizeof(report));
    report.modifiers = base_modifiers;
    if (state->held_count > 0) {
        report.modifiers |= state->held[state->held_count - 1].modifiers;
    }
    for (uint8_t i = 0; i < state->held_count; i++) {
        report.keys[i] = state->held[i].usage;
    }
    if (state->queue_count == HID_REPORT_QUEUE_LENGTH) {
        const uint8_t last = (uint8_t)((state->queue_head + state->queue_count - 1) % HID_REPORT_QUEUE_LENGTH);
        state->queue[last] = report;
        return false;
    }
    const uint8_t tail = (uint8_t)((state->queue_head + state->queue_count) % HID_REPORT_QUEUE_LENGTH);
    state->queue[tail] = report;
    state->queue_count++;
    return true;
}

bool hid_report_peek(const struct hid_report_state *state, struct hid_keyboard_report *report)
{
    if (state->queue_count == 0) {
        return false;
    }
    *report = state->queue[state->queue_head];
    return true;
}

void hid_report_pop(struct hid_report_state *state)
{
    if (state->queue_count == 0) {
        return;
    }
    state->queue_head = (uint8_t)((state->queue_head + 1) % HID_REPORT_QUEUE_LENGTH);
    state->queue_count--;
}
