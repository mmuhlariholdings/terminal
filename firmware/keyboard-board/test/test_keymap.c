/* test_keymap.c: host tests for the terminal key map, sticky modifiers and HID report building. */
#include "hid_report.h"
#include "hid_usage.h"
#include "keymap.h"
#include "test_framework.h"

#define KEY_W KEY_INDEX(0, 1)
#define KEY_G KEY_INDEX(0, 2)
#define KEY_Q KEY_INDEX(1, 1)
#define KEY_P KEY_INDEX(6, 3)
#define KEY_A KEY_INDEX(6, 1)
#define KEY_T KEY_INDEX(4, 2)
#define KEY_U KEY_INDEX(1, 5)
#define KEY_MICROPHONE KEY_INDEX(2, 1)
#define KEY_BACKSPACE KEY_INDEX(6, 4)
#define KEY_LEFT_SHIFT KEY_INDEX(2, 3)
#define KEY_ALT KEY_INDEX(5, 1)
#define KEY_SYM KEY_INDEX(4, 1)
#define KEY_CONTROL KEY_INDEX_NAV_LEFT1
#define KEY_ESCAPE KEY_INDEX_NAV_LEFT2
#define KEY_TAB KEY_INDEX_NAV_RIGHT1
#define KEY_FN KEY_INDEX_FUNCTION

static struct keymap_state state;

static struct keymap_action tap(uint8_t key)
{
    struct keymap_action action = keymap_handle_key(&state, key, true);
    struct keymap_action release = keymap_handle_key(&state, key, false);
    if (action.kind == KEYMAP_ACTION_KEY_PRESS) {
        CHECK_EQUAL(KEYMAP_ACTION_KEY_RELEASE, release.kind);
    }
    return action;
}

static void expect_key(struct keymap_action action, uint8_t usage, uint8_t modifiers)
{
    CHECK_EQUAL(KEYMAP_ACTION_KEY_PRESS, action.kind);
    CHECK_EQUAL(usage, action.usage);
    CHECK_EQUAL(modifiers, action.modifiers);
}

static void test_table(void)
{
    /* every printable character the table uses can be typed */
    for (int key = 0; key < KEY_COUNT; key++) {
        const struct key_output outputs[3] = {keymap_table[key].plain, keymap_table[key].alt, keymap_table[key].function};
        for (int layer = 0; layer < 3; layer++) {
            if (outputs[layer].kind == KEY_OUTPUT_CHARACTER) {
                uint8_t usage, modifiers;
                CHECK(keymap_character_to_usage((char)outputs[layer].value, &usage, &modifiers));
            }
        }
        CHECK(keymap_table[key].name != NULL);
    }
    /* the twelve shell symbols on Fn, plus the three additions */
    const char *wanted = "|~`{}[]<>\\^=&%";
    for (const char *c = wanted; *c; c++) {
        int found = 0;
        for (int key = 0; key < KEY_COUNT; key++) {
            if (keymap_table[key].function.kind == KEY_OUTPUT_CHARACTER && keymap_table[key].function.value == (uint8_t)*c) {
                found++;
            }
        }
        CHECK_EQUAL(1, found);
    }
    /* F1-F10 each exactly once */
    for (int n = 1; n <= 10; n++) {
        int found = 0;
        for (int key = 0; key < KEY_COUNT; key++) {
            if (keymap_table[key].function.kind == KEY_OUTPUT_USAGE && keymap_table[key].function.value == HID_USAGE_F1 + n - 1) {
                found++;
            }
        }
        CHECK_EQUAL(1, found);
    }
}

static void test_plain_shift_alt_fn(void)
{
    keymap_init(&state);
    expect_key(tap(KEY_W), HID_USAGE_A + ('w' - 'a'), 0);

    /* held Shift: capital letter */
    keymap_handle_key(&state, KEY_LEFT_SHIFT, true);
    expect_key(tap(KEY_W), HID_USAGE_A + ('w' - 'a'), HID_MODIFIER_LEFT_SHIFT);
    keymap_handle_key(&state, KEY_LEFT_SHIFT, false);
    expect_key(tap(KEY_W), HID_USAGE_A + ('w' - 'a'), 0); /* held shift ends with its release */

    /* held Alt: printed symbol; W -> 1, Q -> # (Shift+3) */
    keymap_handle_key(&state, KEY_ALT, true);
    expect_key(tap(KEY_W), HID_USAGE_1, 0);
    expect_key(tap(KEY_Q), HID_USAGE_1 + 2, HID_MODIFIER_LEFT_SHIFT);
    keymap_handle_key(&state, KEY_ALT, false);

    /* Shift + Alt symbol: still just the symbol */
    keymap_handle_key(&state, KEY_LEFT_SHIFT, true);
    keymap_handle_key(&state, KEY_ALT, true);
    expect_key(tap(KEY_W), HID_USAGE_1, 0);
    keymap_handle_key(&state, KEY_ALT, false);
    keymap_handle_key(&state, KEY_LEFT_SHIFT, false);

    /* held Fn: F1, F10, pipe, backslash */
    keymap_handle_key(&state, KEY_FN, true);
    expect_key(tap(KEY_W), HID_USAGE_F1, 0);
    expect_key(tap(KEY_MICROPHONE), HID_USAGE_F1 + 9, 0);
    expect_key(tap(KEY_P), HID_USAGE_BACKSLASH, HID_MODIFIER_LEFT_SHIFT);
    expect_key(tap(KEY_INDEX(5, 5)), HID_USAGE_BACKSLASH, 0);
    expect_key(tap(KEY_T), HID_USAGE_GRAVE, HID_MODIFIER_LEFT_SHIFT);  /* ~ */
    expect_key(tap(KEY_G), HID_USAGE_GRAVE, 0);                        /* ` */
    expect_key(tap(KEY_U), HID_USAGE_BRACKET_LEFT, HID_MODIFIER_LEFT_SHIFT); /* { */
    expect_key(tap(KEY_BACKSPACE), HID_USAGE_DELETE, 0);
    /* Fn on a key with no Fn output falls back to plain */
    expect_key(tap(KEY_INDEX(0, 4)), HID_USAGE_A + ('l' - 'a'), 0);
    keymap_handle_key(&state, KEY_FN, false);

    /* nav keys: Esc and Tab; Shift+Tab */
    expect_key(tap(KEY_ESCAPE), HID_USAGE_ESCAPE, 0);
    expect_key(tap(KEY_TAB), HID_USAGE_TAB, 0);
    keymap_handle_key(&state, KEY_LEFT_SHIFT, true);
    expect_key(tap(KEY_TAB), HID_USAGE_TAB, HID_MODIFIER_LEFT_SHIFT);
    keymap_handle_key(&state, KEY_LEFT_SHIFT, false);

    /* Ctrl held + c, Sym (Meta) held + b */
    keymap_handle_key(&state, KEY_CONTROL, true);
    CHECK_EQUAL(HID_MODIFIER_LEFT_CONTROL, keymap_base_modifiers(&state));
    expect_key(tap(KEY_INDEX(3, 2)), HID_USAGE_A + ('c' - 'a'), HID_MODIFIER_LEFT_CONTROL);
    keymap_handle_key(&state, KEY_CONTROL, false);
    CHECK_EQUAL(0, keymap_base_modifiers(&state));
    keymap_handle_key(&state, KEY_SYM, true);
    expect_key(tap(KEY_INDEX(5, 5)), HID_USAGE_A + ('b' - 'a'), HID_MODIFIER_LEFT_ALT);
    keymap_handle_key(&state, KEY_SYM, false);
}

static void test_sticky(void)
{
    keymap_init(&state);
    /* tap Ctrl once: applies to the next key only */
    tap(KEY_CONTROL);
    CHECK_EQUAL(STICKY_ONE_SHOT, state.sticky.state[STICKY_CONTROL]);
    CHECK_EQUAL(0, keymap_base_modifiers(&state)); /* one-shot is not sent on its own */
    expect_key(tap(KEY_INDEX(3, 2)), HID_USAGE_A + ('c' - 'a'), HID_MODIFIER_LEFT_CONTROL);
    expect_key(tap(KEY_INDEX(3, 2)), HID_USAGE_A + ('c' - 'a'), 0);

    /* tap Shift twice: locked (caps) until tapped again */
    tap(KEY_LEFT_SHIFT);
    tap(KEY_LEFT_SHIFT);
    CHECK_EQUAL(STICKY_LOCKED, state.sticky.state[STICKY_SHIFT]);
    expect_key(tap(KEY_A), HID_USAGE_A, HID_MODIFIER_LEFT_SHIFT);
    expect_key(tap(KEY_A), HID_USAGE_A, HID_MODIFIER_LEFT_SHIFT);
    tap(KEY_LEFT_SHIFT);
    CHECK_EQUAL(STICKY_OFF, state.sticky.state[STICKY_SHIFT]);
    expect_key(tap(KEY_A), HID_USAGE_A, 0);

    /* tap Fn once then W: F1, then W again is plain */
    tap(KEY_FN);
    expect_key(tap(KEY_W), HID_USAGE_F1, 0);
    expect_key(tap(KEY_W), HID_USAGE_A + ('w' - 'a'), 0);

    /* tap Alt once: one symbol */
    tap(KEY_ALT);
    expect_key(tap(KEY_INDEX(0, 3)), HID_USAGE_1 + 3, 0); /* S -> 4 */
    expect_key(tap(KEY_INDEX(0, 3)), HID_USAGE_A + ('s' - 'a'), 0);

    /* one-shot Ctrl plus held Shift: Ctrl+Shift+T */
    tap(KEY_CONTROL);
    keymap_handle_key(&state, KEY_LEFT_SHIFT, true);
    expect_key(tap(KEY_T), HID_USAGE_A + ('t' - 'a'), HID_MODIFIER_LEFT_CONTROL | HID_MODIFIER_LEFT_SHIFT);
    keymap_handle_key(&state, KEY_LEFT_SHIFT, false);
    CHECK_EQUAL(STICKY_OFF, state.sticky.state[STICKY_SHIFT]); /* used while held: not a tap */
    CHECK_EQUAL(STICKY_OFF, state.sticky.state[STICKY_CONTROL]);

    /* locked Ctrl stays in the report base */
    tap(KEY_CONTROL);
    tap(KEY_CONTROL);
    CHECK_EQUAL(HID_MODIFIER_LEFT_CONTROL, keymap_base_modifiers(&state));
    tap(KEY_CONTROL);
    CHECK_EQUAL(0, keymap_base_modifiers(&state));

    /* synthetic keys (trackpad arrows) take one-shot Shift */
    tap(KEY_LEFT_SHIFT);
    CHECK_EQUAL(HID_MODIFIER_LEFT_SHIFT, keymap_take_modifiers_for_synthetic_key(&state));
    CHECK_EQUAL(0, keymap_take_modifiers_for_synthetic_key(&state));
}

static void test_trackpad_click(void)
{
    keymap_init(&state);
    expect_key(tap(KEY_INDEX_TRACKPAD_CLICK), HID_USAGE_ENTER, 0);
    /* Fn + click toggles to mouse mode */
    keymap_handle_key(&state, KEY_FN, true);
    CHECK_EQUAL(KEYMAP_ACTION_TOGGLE_TRACKPAD, tap(KEY_INDEX_TRACKPAD_CLICK).kind);
    keymap_handle_key(&state, KEY_FN, false);
    CHECK_EQUAL(TRACKPAD_MODE_MOUSE, state.trackpad_mode);
    CHECK_EQUAL(KEYMAP_ACTION_MOUSE_PRESS, keymap_handle_key(&state, KEY_INDEX_TRACKPAD_CLICK, true).kind);
    CHECK_EQUAL(KEYMAP_ACTION_MOUSE_RELEASE, keymap_handle_key(&state, KEY_INDEX_TRACKPAD_CLICK, false).kind);
    /* the release matches the press even if the mode changes in between */
    CHECK_EQUAL(KEYMAP_ACTION_MOUSE_PRESS, keymap_handle_key(&state, KEY_INDEX_TRACKPAD_CLICK, true).kind);
    state.trackpad_mode = TRACKPAD_MODE_ARROWS;
    CHECK_EQUAL(KEYMAP_ACTION_MOUSE_RELEASE, keymap_handle_key(&state, KEY_INDEX_TRACKPAD_CLICK, false).kind);
    /* empty matrix positions and out-of-range keys do nothing */
    CHECK_EQUAL(KEYMAP_ACTION_NONE, tap(KEY_INDEX(1, 0)).kind);
    CHECK_EQUAL(KEYMAP_ACTION_NONE, keymap_handle_key(&state, 200, true).kind);
}

static void test_reports(void)
{
    struct hid_report_state reports;
    struct hid_keyboard_report report;
    hid_report_init(&reports);
    CHECK(!hid_report_peek(&reports, &report));

    /* "#" (Shift+3) held, then "q" pressed: the report uses q's modifiers only */
    hid_report_press(&reports, 1, HID_USAGE_1 + 2, HID_MODIFIER_LEFT_SHIFT);
    hid_report_queue_current(&reports, 0);
    hid_report_press(&reports, 2, HID_USAGE_A + ('q' - 'a'), 0);
    hid_report_queue_current(&reports, HID_MODIFIER_LEFT_CONTROL);
    CHECK(hid_report_peek(&reports, &report));
    CHECK_EQUAL(HID_MODIFIER_LEFT_SHIFT, report.modifiers);
    CHECK_EQUAL(HID_USAGE_1 + 2, report.keys[0]);
    hid_report_pop(&reports);
    CHECK(hid_report_peek(&reports, &report));
    CHECK_EQUAL(HID_MODIFIER_LEFT_CONTROL, report.modifiers);
    CHECK_EQUAL(HID_USAGE_A + ('q' - 'a'), report.keys[1]);
    hid_report_pop(&reports);

    hid_report_release(&reports, 1);
    hid_report_release(&reports, 2);
    hid_report_queue_current(&reports, 0);
    CHECK(hid_report_peek(&reports, &report));
    CHECK_EQUAL(0, report.keys[0]);
    hid_report_pop(&reports);
    CHECK(!hid_report_peek(&reports, &report));

    /* more than six keys: oldest dropped */
    for (uint8_t slot = 0; slot < 8; slot++) {
        hid_report_press(&reports, slot, (uint8_t)(HID_USAGE_A + slot), 0);
    }
    CHECK_EQUAL(HID_REPORT_MAX_KEYS, reports.held_count);
    CHECK_EQUAL(2, reports.held[0].slot);

    /* full queue: the newest report replaces the last one */
    hid_report_init(&reports);
    for (int i = 0; i < HID_REPORT_QUEUE_LENGTH; i++) {
        CHECK(hid_report_queue_current(&reports, 0));
    }
    hid_report_press(&reports, 3, HID_USAGE_ENTER, 0);
    CHECK(!hid_report_queue_current(&reports, 0));
    CHECK_EQUAL(HID_REPORT_QUEUE_LENGTH, reports.queue_count);
    for (int i = 0; i < HID_REPORT_QUEUE_LENGTH - 1; i++) {
        hid_report_pop(&reports);
    }
    CHECK(hid_report_peek(&reports, &report));
    CHECK_EQUAL(HID_USAGE_ENTER, report.keys[0]);
}

int main(void)
{
    test_table();
    test_plain_shift_alt_fn();
    test_sticky();
    test_trackpad_click();
    test_reports();
    return test_summary("keymap");
}
