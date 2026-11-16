/* test_trackpad_logic.c: host tests for trackpad motion -> arrows / mouse (src/trackpad_logic.c). */
#include "hid_usage.h"
#include "test_framework.h"
#include "trackpad_logic.h"

int main(void)
{
    struct trackpad_logic logic;
    uint8_t arrows[8];
    trackpad_logic_init(&logic);

    /* small motions accumulate until the threshold */
    CHECK_EQUAL(0, trackpad_logic_arrows(&logic, 10, 0, 1000, arrows, 8));
    CHECK_EQUAL(0, trackpad_logic_arrows(&logic, 10, 2, 1010, arrows, 8));
    CHECK_EQUAL(1, trackpad_logic_arrows(&logic, 10, 0, 1020, arrows, 8));
    CHECK_EQUAL(TRACKPAD_ARROW_RIGHT, arrows[0]);
    CHECK_EQUAL(0, logic.accumulated_y); /* axis lock */

    /* motion is forgotten after a pause */
    trackpad_logic_arrows(&logic, 0, -20, 1030, arrows, 8);
    CHECK_EQUAL(0, trackpad_logic_arrows(&logic, 0, -20, 1030 + TRACKPAD_IDLE_RESET_MS + 1, arrows, 8));

    /* a long swipe up gives several arrows, capped per update */
    trackpad_logic_init(&logic);
    CHECK_EQUAL(2, trackpad_logic_arrows(&logic, 0, -2 * TRACKPAD_ARROW_THRESHOLD, 5000, arrows, 8));
    CHECK_EQUAL(TRACKPAD_ARROW_UP, arrows[0]);
    CHECK_EQUAL(TRACKPAD_ARROW_UP, arrows[1]);
    CHECK_EQUAL(TRACKPAD_MAX_ARROWS_PER_UPDATE,
                trackpad_logic_arrows(&logic, -100 * TRACKPAD_ARROW_THRESHOLD, 0, 5010, arrows, 8));
    CHECK_EQUAL(TRACKPAD_ARROW_LEFT, arrows[0]);
    CHECK_EQUAL(0, logic.accumulated_x); /* burst dropped */
    CHECK_EQUAL(1, trackpad_logic_arrows(&logic, 3, TRACKPAD_ARROW_THRESHOLD, 5020, arrows, 1));
    CHECK_EQUAL(TRACKPAD_ARROW_DOWN, arrows[0]);

    /* mouse scaling and clamping */
    int8_t x, y;
    trackpad_logic_mouse(10, -4, &x, &y);
    CHECK_EQUAL(15, x);
    CHECK_EQUAL(-6, y);
    trackpad_logic_mouse(1000, -1000, &x, &y);
    CHECK_EQUAL(127, x);
    CHECK_EQUAL(-127, y);

    CHECK_EQUAL(HID_USAGE_ARROW_UP, trackpad_arrow_usage(TRACKPAD_ARROW_UP));
    CHECK_EQUAL(HID_USAGE_ARROW_LEFT, trackpad_arrow_usage(TRACKPAD_ARROW_LEFT));
    return test_summary("trackpad_logic");
}
