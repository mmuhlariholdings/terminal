/*
 * keymap.c: applies the key map table (keymap_table.c) and the sticky modifiers to key events. Pure logic, no hardware.
 * Behaviour adapted from the Solder Party i2c_puppet firmware (app/keyboard.c, MIT licence), extended for a terminal.
 */
#include "keymap.h"

#include <string.h>

#include "hid_usage.h"

void keymap_init(struct keymap_state *state)
{
    memset(state, 0, sizeof(*state));
    sticky_init(&state->sticky);
    state->trackpad_mode = TRACKPAD_MODE_ARROWS;
}

bool keymap_character_to_usage(char character, uint8_t *usage, uint8_t *modifiers)
{
    *modifiers = 0;
    if (character >= 'a' && character <= 'z') {
        *usage = (uint8_t)(HID_USAGE_A + (character - 'a'));
        return true;
    }
    if (character >= 'A' && character <= 'Z') {
        *usage = (uint8_t)(HID_USAGE_A + (character - 'A'));
        *modifiers = HID_MODIFIER_LEFT_SHIFT;
        return true;
    }
    if (character >= '1' && character <= '9') {
        *usage = (uint8_t)(HID_USAGE_1 + (character - '1'));
        return true;
    }
    /* the rest of printable ASCII on a US layout: character, usage, needs Shift */
    static const struct {
        char character;
        uint8_t usage;
        uint8_t shift;
    } symbols[] = {
        {'0', HID_USAGE_0, 0},           {' ', HID_USAGE_SPACE, 0},          {'!', HID_USAGE_1, 1},
        {'@', HID_USAGE_1 + 1, 1},       {'#', HID_USAGE_1 + 2, 1},          {'$', HID_USAGE_1 + 3, 1},
        {'%', HID_USAGE_1 + 4, 1},       {'^', HID_USAGE_1 + 5, 1},          {'&', HID_USAGE_1 + 6, 1},
        {'*', HID_USAGE_1 + 7, 1},       {'(', HID_USAGE_1 + 8, 1},          {')', HID_USAGE_0, 1},
        {'-', HID_USAGE_MINUS, 0},       {'_', HID_USAGE_MINUS, 1},          {'=', HID_USAGE_EQUAL, 0},
        {'+', HID_USAGE_EQUAL, 1},       {'[', HID_USAGE_BRACKET_LEFT, 0},   {'{', HID_USAGE_BRACKET_LEFT, 1},
        {']', HID_USAGE_BRACKET_RIGHT, 0}, {'}', HID_USAGE_BRACKET_RIGHT, 1}, {'\\', HID_USAGE_BACKSLASH, 0},
        {'|', HID_USAGE_BACKSLASH, 1},   {';', HID_USAGE_SEMICOLON, 0},      {':', HID_USAGE_SEMICOLON, 1},
        {'\'', HID_USAGE_APOSTROPHE, 0}, {'"', HID_USAGE_APOSTROPHE, 1},     {'`', HID_USAGE_GRAVE, 0},
        {'~', HID_USAGE_GRAVE, 1},       {',', HID_USAGE_COMMA, 0},          {'<', HID_USAGE_COMMA, 1},
        {'.', HID_USAGE_PERIOD, 0},      {'>', HID_USAGE_PERIOD, 1},         {'/', HID_USAGE_SLASH, 0},
        {'?', HID_USAGE_SLASH, 1},
    };
    for (unsigned i = 0; i < sizeof(symbols) / sizeof(symbols[0]); i++) {
        if (symbols[i].character == character) {
            *usage = symbols[i].usage;
            *modifiers = symbols[i].shift ? HID_MODIFIER_LEFT_SHIFT : 0;
            return true;
        }
    }
    return false;
}

uint8_t keymap_base_modifiers(const struct keymap_state *state)
{
    uint8_t modifiers = 0;
    if (sticky_held_or_locked(&state->sticky, STICKY_CONTROL)) {
        modifiers |= HID_MODIFIER_LEFT_CONTROL;
    }
    if (sticky_held_or_locked(&state->sticky, STICKY_META)) {
        modifiers |= HID_MODIFIER_LEFT_ALT;
    }
    return modifiers;
}

static uint8_t control_and_meta(const struct keymap_state *state)
{
    uint8_t modifiers = 0;
    if (sticky_active(&state->sticky, STICKY_CONTROL)) {
        modifiers |= HID_MODIFIER_LEFT_CONTROL;
    }
    if (sticky_active(&state->sticky, STICKY_META)) {
        modifiers |= HID_MODIFIER_LEFT_ALT;
    }
    return modifiers;
}

uint8_t keymap_take_modifiers_for_synthetic_key(struct keymap_state *state)
{
    uint8_t modifiers = control_and_meta(state);
    if (sticky_active(&state->sticky, STICKY_SHIFT)) {
        modifiers |= HID_MODIFIER_LEFT_SHIFT;
    }
    sticky_consume(&state->sticky);
    return modifiers;
}

static int sticky_for_role(uint8_t role)
{
    switch (role) {
    case KEY_ROLE_CONTROL:
        return STICKY_CONTROL;
    case KEY_ROLE_SHIFT:
        return STICKY_SHIFT;
    case KEY_ROLE_SYMBOL:
        return STICKY_SYMBOL;
    case KEY_ROLE_FUNCTION:
        return STICKY_FUNCTION;
    case KEY_ROLE_META:
        return STICKY_META;
    default:
        return -1;
    }
}

/* Pick the output for a normal key from the active layer, falling back to lower layers. */
static struct key_output choose_output(const struct keymap_state *state, const struct key_definition *key)
{
    if (sticky_active(&state->sticky, STICKY_FUNCTION) && key->function.kind != KEY_OUTPUT_NONE) {
        return key->function;
    }
    if (sticky_active(&state->sticky, STICKY_SYMBOL) && key->alt.kind != KEY_OUTPUT_NONE) {
        return key->alt;
    }
    return key->plain;
}

static struct keymap_action press_normal_key(struct keymap_state *state, uint8_t key_index,
                                             const struct key_definition *key)
{
    struct keymap_action action = {KEYMAP_ACTION_NONE, key_index, 0, 0};
    const struct key_output output = choose_output(state, key);
    const bool shift = sticky_active(&state->sticky, STICKY_SHIFT);
    uint8_t usage = 0;
    uint8_t modifiers = 0;

    if (output.kind == KEY_OUTPUT_CHARACTER) {
        char character = (char)output.value;
        if (shift && character >= 'a' && character <= 'z') {
            character = (char)(character - 'a' + 'A'); /* Shift makes letters capital; symbols stay as they are */
        }
        if (!keymap_character_to_usage(character, &usage, &modifiers)) {
            sticky_consume(&state->sticky);
            return action;
        }
    } else if (output.kind == KEY_OUTPUT_USAGE) {
        usage = output.value;
        if (shift) {
            modifiers |= HID_MODIFIER_LEFT_SHIFT; /* Shift+Tab, Shift+Enter... */
        }
    } else {
        sticky_consume(&state->sticky);
        return action;
    }
    modifiers |= control_and_meta(state);
    sticky_consume(&state->sticky);

    action.kind = KEYMAP_ACTION_KEY_PRESS;
    action.usage = usage;
    action.modifiers = modifiers;
    return action;
}

struct keymap_action keymap_handle_key(struct keymap_state *state, uint8_t key_index, bool pressed)
{
    struct keymap_action action = {KEYMAP_ACTION_NONE, key_index, 0, 0};
    if (key_index >= KEY_COUNT) {
        return action;
    }
    const struct key_definition *key = &keymap_table[key_index];
    const int sticky = sticky_for_role(key->role);

    if (sticky >= 0) {
        if (pressed) {
            sticky_press(&state->sticky, (enum sticky_modifier)sticky);
        } else {
            sticky_release(&state->sticky, (enum sticky_modifier)sticky);
        }
        return action;
    }

    if (!pressed) {
        const uint8_t kind = state->pressed_kind[key_index];
        state->pressed_kind[key_index] = KEYMAP_ACTION_NONE;
        if (kind == KEYMAP_ACTION_KEY_PRESS) {
            action.kind = KEYMAP_ACTION_KEY_RELEASE;
        } else if (kind == KEYMAP_ACTION_MOUSE_PRESS) {
            action.kind = KEYMAP_ACTION_MOUSE_RELEASE;
        }
        return action;
    }

    switch (key->role) {
    case KEY_ROLE_NORMAL:
        action = press_normal_key(state, key_index, key);
        break;
    case KEY_ROLE_TRACKPAD_CLICK:
        if (sticky_active(&state->sticky, STICKY_FUNCTION)) {
            state->trackpad_mode = state->trackpad_mode == TRACKPAD_MODE_ARROWS ? TRACKPAD_MODE_MOUSE : TRACKPAD_MODE_ARROWS;
            sticky_consume(&state->sticky);
            action.kind = KEYMAP_ACTION_TOGGLE_TRACKPAD;
        } else if (state->trackpad_mode == TRACKPAD_MODE_MOUSE) {
            sticky_consume(&state->sticky);
            action.kind = KEYMAP_ACTION_MOUSE_PRESS;
        } else {
            static const struct key_definition enter = {"trackpad Enter", KEY_ROLE_NORMAL,
                                                         {KEY_OUTPUT_USAGE, HID_USAGE_ENTER},
                                                         {KEY_OUTPUT_NONE, 0}, {KEY_OUTPUT_NONE, 0}};
            action = press_normal_key(state, key_index, &enter);
        }
        break;
    default:
        break;
    }
    state->pressed_kind[key_index] = action.kind == KEYMAP_ACTION_TOGGLE_TRACKPAD ? KEYMAP_ACTION_NONE : action.kind;
    return action;
}
