/*
 * sticky_modifiers.h: sticky modifier keys (pure logic, unit-tested on the host).
 *
 * Each sticky modifier (Ctrl, Shift, Alt symbol layer, Fn, Sym/Meta) works three ways:
 *   - held while another key is pressed: a normal modifier, released with the key;
 *   - tapped once (pressed and released with no other key): applies to the next key only ("one-shot");
 *   - tapped twice: locked on until it is tapped again.
 * A third tap while locked unlocks it.
 */
#ifndef TERMINAL_STICKY_MODIFIERS_H
#define TERMINAL_STICKY_MODIFIERS_H

#include <stdbool.h>
#include <stdint.h>

enum sticky_modifier {
    STICKY_CONTROL = 0,
    STICKY_SHIFT,
    STICKY_SYMBOL,   /* the BlackBerry "alt" key: the symbols printed on the keys */
    STICKY_FUNCTION, /* Fn: F1-F10 and the shell symbols */
    STICKY_META,     /* the "sym" key: sent to Linux as Left Alt (Meta) */
    STICKY_COUNT
};

enum sticky_state {
    STICKY_OFF = 0,
    STICKY_ONE_SHOT,
    STICKY_LOCKED,
};

struct sticky_modifiers {
    uint8_t state[STICKY_COUNT];  /* enum sticky_state */
    bool down[STICKY_COUNT];      /* key physically held */
    bool used[STICKY_COUNT];      /* another key was pressed while this one was held */
};

void sticky_init(struct sticky_modifiers *sticky);
void sticky_press(struct sticky_modifiers *sticky, enum sticky_modifier modifier);
void sticky_release(struct sticky_modifiers *sticky, enum sticky_modifier modifier);

/* True if the modifier applies to the next key (held, one-shot or locked). */
bool sticky_active(const struct sticky_modifiers *sticky, enum sticky_modifier modifier);

/* True if the modifier is held down or locked (not one-shot): used for modifiers that stay in the HID report. */
bool sticky_held_or_locked(const struct sticky_modifiers *sticky, enum sticky_modifier modifier);

/* Call after a non-modifier key has been pressed and its modifiers read: one-shot modifiers are used up, held ones
 * are marked as used (so releasing them does not count as a tap). */
void sticky_consume(struct sticky_modifiers *sticky);

#endif
