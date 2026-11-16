/*
 * keymap_table.c: THE key map. Edit this table to change what a key sends; keep the cheat sheet in README.md in step.
 *
 * Matrix positions (row, column) and the symbols printed on the keys come from the Solder Party i2c_puppet firmware
 * (https://github.com/solderparty/i2c_puppet, app/keyboard.c, MIT licence, Copyright (c) 2022 Solder Party AB).
 *
 * Each key: { name, role, plain, alt (printed symbol), fn }.
 *   CHARACTER('x')  an ASCII character, typed through the Linux "us" layout
 *   USAGE(HID_...)  a raw HID key (Enter, Esc, F1...): Shift, Ctrl and Meta are added to it
 *   FUNCTION(n)     F1..F12
 *   NOTHING         fall back to the next lower layer (fn -> alt -> plain)
 * Terminal layer (Fn): Fn + the number keys = F1-F10, Fn + letters = the shell symbols a Q20 lacks.
 */
#include "hid_usage.h"
#include "keymap.h"

#define CHARACTER(c) {KEY_OUTPUT_CHARACTER, (uint8_t)(c)}
#define USAGE(u) {KEY_OUTPUT_USAGE, (u)}
#define FUNCTION(n) {KEY_OUTPUT_USAGE, (uint8_t)(HID_USAGE_F1 + (n) - 1)}
#define NOTHING {KEY_OUTPUT_NONE, 0}

#define LETTER(name, letter, printed, fn) {name, KEY_ROLE_NORMAL, CHARACTER(letter), CHARACTER(printed), fn}

const struct key_definition keymap_table[KEY_COUNT] = {
    /* row 1 */
    [KEY_INDEX(0, 0)] = {"trackpad click", KEY_ROLE_TRACKPAD_CLICK, NOTHING, NOTHING, NOTHING},
    [KEY_INDEX(0, 1)] = LETTER("W", 'w', '1', FUNCTION(1)),
    [KEY_INDEX(0, 2)] = LETTER("G", 'g', '/', CHARACTER('`')),
    [KEY_INDEX(0, 3)] = LETTER("S", 's', '4', FUNCTION(4)),
    [KEY_INDEX(0, 4)] = LETTER("L", 'l', '"', NOTHING),
    [KEY_INDEX(0, 5)] = LETTER("H", 'h', ':', CHARACTER('^')),
    /* row 2 */
    [KEY_INDEX(1, 0)] = {"(none)", KEY_ROLE_NONE, NOTHING, NOTHING, NOTHING},
    [KEY_INDEX(1, 1)] = LETTER("Q", 'q', '#', CHARACTER('%')),
    [KEY_INDEX(1, 2)] = LETTER("R", 'r', '3', FUNCTION(3)),
    [KEY_INDEX(1, 3)] = LETTER("E", 'e', '2', FUNCTION(2)),
    [KEY_INDEX(1, 4)] = LETTER("O", 'o', '+', NOTHING),
    [KEY_INDEX(1, 5)] = LETTER("U", 'u', '_', CHARACTER('{')),
    /* row 3 */
    [KEY_INDEX(2, 0)] = {"Call (Ctrl)", KEY_ROLE_CONTROL, NOTHING, NOTHING, NOTHING},
    [KEY_INDEX(2, 1)] = {"microphone / 0", KEY_ROLE_NORMAL, CHARACTER('0'), CHARACTER('0'), FUNCTION(10)},
    [KEY_INDEX(2, 2)] = LETTER("F", 'f', '6', FUNCTION(6)),
    [KEY_INDEX(2, 3)] = {"left shift", KEY_ROLE_SHIFT, NOTHING, NOTHING, NOTHING},
    [KEY_INDEX(2, 4)] = LETTER("K", 'k', '\'', CHARACTER(']')),
    [KEY_INDEX(2, 5)] = LETTER("J", 'j', ';', CHARACTER('[')),
    /* row 4 */
    [KEY_INDEX(3, 0)] = {"(none)", KEY_ROLE_NONE, NOTHING, NOTHING, NOTHING},
    [KEY_INDEX(3, 1)] = {"space", KEY_ROLE_NORMAL, CHARACTER(' '), CHARACTER(' '), NOTHING},
    [KEY_INDEX(3, 2)] = LETTER("C", 'c', '9', FUNCTION(9)),
    [KEY_INDEX(3, 3)] = LETTER("Z", 'z', '7', FUNCTION(7)),
    [KEY_INDEX(3, 4)] = LETTER("M", 'm', '.', CHARACTER('>')),
    [KEY_INDEX(3, 5)] = LETTER("N", 'n', ',', CHARACTER('<')),
    /* row 5 */
    [KEY_INDEX(4, 0)] = {"BlackBerry menu (Esc)", KEY_ROLE_NORMAL, USAGE(HID_USAGE_ESCAPE), NOTHING, NOTHING},
    [KEY_INDEX(4, 1)] = {"sym (Linux Alt / Meta)", KEY_ROLE_META, NOTHING, NOTHING, NOTHING},
    [KEY_INDEX(4, 2)] = LETTER("T", 't', '(', CHARACTER('~')),
    [KEY_INDEX(4, 3)] = LETTER("D", 'd', '5', FUNCTION(5)),
    [KEY_INDEX(4, 4)] = LETTER("I", 'i', '-', CHARACTER('}')),
    [KEY_INDEX(4, 5)] = LETTER("Y", 'y', ')', CHARACTER('=')),
    /* row 6 */
    [KEY_INDEX(5, 0)] = {"Back (Tab)", KEY_ROLE_NORMAL, USAGE(HID_USAGE_TAB), NOTHING, NOTHING},
    [KEY_INDEX(5, 1)] = {"alt (printed symbols)", KEY_ROLE_SYMBOL, NOTHING, NOTHING, NOTHING},
    [KEY_INDEX(5, 2)] = LETTER("V", 'v', '?', NOTHING),
    [KEY_INDEX(5, 3)] = LETTER("X", 'x', '8', FUNCTION(8)),
    [KEY_INDEX(5, 4)] = {"speaker / $", KEY_ROLE_NORMAL, CHARACTER('$'), CHARACTER('$'), NOTHING},
    [KEY_INDEX(5, 5)] = LETTER("B", 'b', '!', CHARACTER('\\')),
    /* row 7 */
    [KEY_INDEX(6, 0)] = {"(none)", KEY_ROLE_NONE, NOTHING, NOTHING, NOTHING},
    [KEY_INDEX(6, 1)] = LETTER("A", 'a', '*', CHARACTER('&')),
    [KEY_INDEX(6, 2)] = {"right shift", KEY_ROLE_SHIFT, NOTHING, NOTHING, NOTHING},
    [KEY_INDEX(6, 3)] = LETTER("P", 'p', '@', CHARACTER('|')),
    [KEY_INDEX(6, 4)] = {"backspace", KEY_ROLE_NORMAL, USAGE(HID_USAGE_BACKSPACE), USAGE(HID_USAGE_DELETE), USAGE(HID_USAGE_DELETE)},
    [KEY_INDEX(6, 5)] = {"enter", KEY_ROLE_NORMAL, USAGE(HID_USAGE_ENTER), NOTHING, NOTHING},
    /* nav key on its own pin */
    [KEY_INDEX_RIGHT2] = {"End (Fn)", KEY_ROLE_FUNCTION, NOTHING, NOTHING, NOTHING},
};
