/*
 * trackpad_logic.h: turns trackpad motion into arrow keys or mouse movement (pure logic, unit-tested on the host).
 *
 * Arrow mode (default): motion is accumulated per axis; each time an axis passes TRACKPAD_ARROW_THRESHOLD counts one
 * arrow key is sent and the other axis is cleared (so a slightly diagonal swipe gives clean arrows). Accumulated motion
 * is forgotten after TRACKPAD_IDLE_RESET_MS without motion.
 * Mouse mode: motion is scaled by TRACKPAD_MOUSE_NUMERATOR / TRACKPAD_MOUSE_DENOMINATOR and sent as mouse movement.
 * Tune the constants here (on hardware) and nowhere else.
 *
 * Signs: positive x = right, positive y = down (after the axis flip done by the trackpad driver, as in i2c_puppet).
 */
#ifndef TERMINAL_TRACKPAD_LOGIC_H
#define TERMINAL_TRACKPAD_LOGIC_H

#include <stdint.h>

#define TRACKPAD_ARROW_THRESHOLD 24  /* counts per arrow key (to tune; i2c_puppet used 15 per report for a swipe) */
#define TRACKPAD_IDLE_RESET_MS 150
#define TRACKPAD_MAX_ARROWS_PER_UPDATE 4
#define TRACKPAD_MOUSE_NUMERATOR 3
#define TRACKPAD_MOUSE_DENOMINATOR 2

enum trackpad_mode {
    TRACKPAD_MODE_ARROWS = 0,
    TRACKPAD_MODE_MOUSE,
};

enum trackpad_arrow {
    TRACKPAD_ARROW_UP = 0,
    TRACKPAD_ARROW_DOWN,
    TRACKPAD_ARROW_LEFT,
    TRACKPAD_ARROW_RIGHT,
};

struct trackpad_logic {
    int32_t accumulated_x;
    int32_t accumulated_y;
    uint32_t last_motion_ms;
};

void trackpad_logic_init(struct trackpad_logic *logic);

/* Arrow mode: add one motion report; writes up to `capacity` arrows to `arrows`, returns how many. */
int trackpad_logic_arrows(struct trackpad_logic *logic, int dx, int dy, uint32_t now_ms, uint8_t *arrows, int capacity);

/* Mouse mode: scale one motion report into a clamped mouse movement. */
void trackpad_logic_mouse(int dx, int dy, int8_t *mouse_x, int8_t *mouse_y);

/* HID usage of an arrow (for the keyboard report). */
uint8_t trackpad_arrow_usage(uint8_t arrow);

#endif
