/*
 * hid_report.h: builds HID boot-protocol keyboard reports from the keys currently held, and queues them so that quick
 * press-release pairs (trackpad arrows) are never lost between USB polls (pure logic, unit-tested on the host).
 *
 * The modifier byte is the base modifiers (Ctrl / Meta held or locked) plus the modifiers of the MOST RECENTLY pressed
 * key only, so typing "#" (Shift+3) then "q" with overlapping presses does not turn the q into a Q.
 */
#ifndef TERMINAL_HID_REPORT_H
#define TERMINAL_HID_REPORT_H

#include <stdbool.h>
#include <stdint.h>

#define HID_REPORT_MAX_KEYS 6
#define HID_REPORT_QUEUE_LENGTH 16
#define HID_REPORT_SYNTHETIC_SLOT 0xFF /* slot used for synthetic taps (trackpad arrows) */

struct hid_held_key {
    uint8_t slot; /* physical key index, or HID_REPORT_SYNTHETIC_SLOT */
    uint8_t usage;
    uint8_t modifiers;
};

struct hid_keyboard_report {
    uint8_t modifiers;
    uint8_t keys[HID_REPORT_MAX_KEYS];
};

struct hid_report_state {
    struct hid_held_key held[HID_REPORT_MAX_KEYS];
    uint8_t held_count;
    struct hid_keyboard_report queue[HID_REPORT_QUEUE_LENGTH];
    uint8_t queue_head;
    uint8_t queue_count;
};

void hid_report_init(struct hid_report_state *state);
void hid_report_press(struct hid_report_state *state, uint8_t slot, uint8_t usage, uint8_t modifiers);
void hid_report_release(struct hid_report_state *state, uint8_t slot);
void hid_report_release_all(struct hid_report_state *state);

/* Build the report for the current held keys and queue it (call after every change). Returns false if the queue is
 * full (the newest state still wins: the last queued report is replaced). */
bool hid_report_queue_current(struct hid_report_state *state, uint8_t base_modifiers);

bool hid_report_peek(const struct hid_report_state *state, struct hid_keyboard_report *report);
void hid_report_pop(struct hid_report_state *state);

#endif
