/*
 * keymap.h: the Terminal 1 key map (pure logic, unit-tested on the host).
 *
 * Physical keys are numbered by their place in the BlackBerry Q20 matrix (row * 6 + column, rows and columns as in the
 * Solder Party BBQ20KBD design), plus the "RIGHT2" nav key, which has its own pin. What each key sends is in ONE table,
 * keymap_table.c: edit that file to change the layout. The cheat sheet in README.md describes the same table.
 *
 * Layers, highest priority first: Fn, Alt (the symbols printed on the keys), plain. Shift makes letters capital; a symbol
 * is always sent as that symbol (Shift is ignored for it). Ctrl and Sym (sent as Linux Alt / Meta) are added to anything.
 * Characters are sent as the key presses a Linux "us" keyboard layout turns into that character.
 */
#ifndef TERMINAL_KEYMAP_H
#define TERMINAL_KEYMAP_H

#include <stdbool.h>
#include <stdint.h>

#include "sticky_modifiers.h"
#include "trackpad_logic.h"

#define KEYBOARD_ROWS 7
#define KEYBOARD_COLUMNS 6
#define KEY_INDEX(row, column) ((row) * KEYBOARD_COLUMNS + (column))
#define KEY_INDEX_RIGHT2 (KEYBOARD_ROWS * KEYBOARD_COLUMNS) /* 42: nav key on its own pin */
#define KEY_COUNT (KEY_INDEX_RIGHT2 + 1)                    /* 43 physical keys */

/* Physical keys that the power manager needs to see (service mode = Fn + Back held while pressing power). */
#define KEY_INDEX_NAV_LEFT1 KEY_INDEX(2, 0)  /* Call key (leftmost above the keyboard): Ctrl   (verify on hardware) */
#define KEY_INDEX_NAV_LEFT2 KEY_INDEX(4, 0)  /* BlackBerry menu key: Esc                      (verify on hardware) */
#define KEY_INDEX_NAV_RIGHT1 KEY_INDEX(5, 0) /* Back key: Tab                                 (verify on hardware) */
#define KEY_INDEX_FUNCTION KEY_INDEX_RIGHT2  /* End key (rightmost): Fn                       (verify on hardware) */
#define KEY_INDEX_BACK KEY_INDEX_NAV_RIGHT1
#define KEY_INDEX_TRACKPAD_CLICK KEY_INDEX(0, 0)

enum key_role {
    KEY_ROLE_NONE = 0,       /* no key at this matrix position */
    KEY_ROLE_NORMAL,         /* sends plain / alt / fn outputs */
    KEY_ROLE_CONTROL,        /* sticky modifiers */
    KEY_ROLE_SHIFT,
    KEY_ROLE_SYMBOL,
    KEY_ROLE_FUNCTION,
    KEY_ROLE_META,
    KEY_ROLE_TRACKPAD_CLICK, /* Enter in arrow mode, left button in mouse mode, Fn + click toggles the mode */
};

enum key_output_kind {
    KEY_OUTPUT_NONE = 0,
    KEY_OUTPUT_CHARACTER, /* an ASCII character, typed through the Linux "us" layout */
    KEY_OUTPUT_USAGE,     /* a raw HID usage (Enter, Esc, F1...): Shift, Ctrl and Meta are added to it */
};

struct key_output {
    uint8_t kind;  /* enum key_output_kind */
    uint8_t value; /* character or HID usage */
};

struct key_definition {
    const char *name;
    uint8_t role; /* enum key_role */
    struct key_output plain;
    struct key_output alt;
    struct key_output function;
};

extern const struct key_definition keymap_table[KEY_COUNT];

/* What the firmware must do for one key event. */
enum keymap_action_kind {
    KEYMAP_ACTION_NONE = 0,
    KEYMAP_ACTION_KEY_PRESS,        /* press usage with modifiers (slot = physical key index) */
    KEYMAP_ACTION_KEY_RELEASE,      /* release the usage pressed from this slot */
    KEYMAP_ACTION_MOUSE_PRESS,      /* left mouse button down */
    KEYMAP_ACTION_MOUSE_RELEASE,
    KEYMAP_ACTION_TOGGLE_TRACKPAD,  /* switch between arrow and mouse mode */
};

struct keymap_action {
    uint8_t kind;  /* enum keymap_action_kind */
    uint8_t slot;
    uint8_t usage;
    uint8_t modifiers;
};

struct keymap_state {
    struct sticky_modifiers sticky;
    uint8_t trackpad_mode;           /* enum trackpad_mode */
    uint8_t pressed_kind[KEY_COUNT]; /* action kind emitted at press, so the release matches it */
};

void keymap_init(struct keymap_state *state);

/* Handle one debounced key change. */
struct keymap_action keymap_handle_key(struct keymap_state *state, uint8_t key_index, bool pressed);

/* Modifiers that stay in the HID report on their own: Ctrl and Meta while held or locked. */
uint8_t keymap_base_modifiers(const struct keymap_state *state);

/* Modifiers for a synthetic key (a trackpad arrow): Ctrl, Shift, Meta; uses up one-shot modifiers. */
uint8_t keymap_take_modifiers_for_synthetic_key(struct keymap_state *state);

/* Character -> HID usage and modifiers on a Linux "us" layout. Returns false for characters it cannot type. */
bool keymap_character_to_usage(char character, uint8_t *usage, uint8_t *modifiers);

#endif
