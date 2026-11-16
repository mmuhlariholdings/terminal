/*
 * hid_usage.h: USB HID keyboard usage IDs and modifier bits (USB HID Usage Tables 1.3, Keyboard/Keypad page 0x07).
 * Own copy (same values as TinyUSB's hid.h) so the pure key-map logic builds and is tested on a computer without TinyUSB.
 */
#ifndef TERMINAL_HID_USAGE_H
#define TERMINAL_HID_USAGE_H

#define HID_MODIFIER_LEFT_CONTROL 0x01
#define HID_MODIFIER_LEFT_SHIFT 0x02
#define HID_MODIFIER_LEFT_ALT 0x04
#define HID_MODIFIER_LEFT_GUI 0x08

#define HID_USAGE_NONE 0x00
#define HID_USAGE_A 0x04 /* A..Z = 0x04..0x1D */
#define HID_USAGE_1 0x1E /* 1..9 = 0x1E..0x26 */
#define HID_USAGE_0 0x27
#define HID_USAGE_ENTER 0x28
#define HID_USAGE_ESCAPE 0x29
#define HID_USAGE_BACKSPACE 0x2A
#define HID_USAGE_TAB 0x2B
#define HID_USAGE_SPACE 0x2C
#define HID_USAGE_MINUS 0x2D
#define HID_USAGE_EQUAL 0x2E
#define HID_USAGE_BRACKET_LEFT 0x2F
#define HID_USAGE_BRACKET_RIGHT 0x30
#define HID_USAGE_BACKSLASH 0x31
#define HID_USAGE_SEMICOLON 0x33
#define HID_USAGE_APOSTROPHE 0x34
#define HID_USAGE_GRAVE 0x35
#define HID_USAGE_COMMA 0x36
#define HID_USAGE_PERIOD 0x37
#define HID_USAGE_SLASH 0x38
#define HID_USAGE_F1 0x3A /* F1..F12 = 0x3A..0x45 */
#define HID_USAGE_HOME 0x4A
#define HID_USAGE_PAGE_UP 0x4B
#define HID_USAGE_DELETE 0x4C
#define HID_USAGE_END 0x4D
#define HID_USAGE_PAGE_DOWN 0x4E
#define HID_USAGE_ARROW_RIGHT 0x4F
#define HID_USAGE_ARROW_LEFT 0x50
#define HID_USAGE_ARROW_DOWN 0x51
#define HID_USAGE_ARROW_UP 0x52

#endif
