/* trackpad_logic.c: trackpad motion -> arrow keys or mouse movement (see trackpad_logic.h). Pure logic. */
#include "trackpad_logic.h"

#include "hid_usage.h"

void trackpad_logic_init(struct trackpad_logic *logic)
{
    logic->accumulated_x = 0;
    logic->accumulated_y = 0;
    logic->last_motion_ms = 0;
}

int trackpad_logic_arrows(struct trackpad_logic *logic, int dx, int dy, uint32_t now_ms, uint8_t *arrows, int capacity)
{
    if ((uint32_t)(now_ms - logic->last_motion_ms) > TRACKPAD_IDLE_RESET_MS) {
        logic->accumulated_x = 0;
        logic->accumulated_y = 0;
    }
    logic->last_motion_ms = now_ms;
    logic->accumulated_x += dx;
    logic->accumulated_y += dy;

    int count = 0;
    if (capacity > TRACKPAD_MAX_ARROWS_PER_UPDATE) {
        capacity = TRACKPAD_MAX_ARROWS_PER_UPDATE;
    }
    while (count < capacity) {
        const int32_t ax = logic->accumulated_x < 0 ? -logic->accumulated_x : logic->accumulated_x;
        const int32_t ay = logic->accumulated_y < 0 ? -logic->accumulated_y : logic->accumulated_y;
        if (ax < TRACKPAD_ARROW_THRESHOLD && ay < TRACKPAD_ARROW_THRESHOLD) {
            break;
        }
        if (ax >= ay) {
            const int right = logic->accumulated_x > 0;
            arrows[count++] = right ? TRACKPAD_ARROW_RIGHT : TRACKPAD_ARROW_LEFT;
            logic->accumulated_x += right ? -TRACKPAD_ARROW_THRESHOLD : TRACKPAD_ARROW_THRESHOLD;
            logic->accumulated_y = 0; /* axis lock */
        } else {
            const int down = logic->accumulated_y > 0;
            arrows[count++] = down ? TRACKPAD_ARROW_DOWN : TRACKPAD_ARROW_UP;
            logic->accumulated_y += down ? -TRACKPAD_ARROW_THRESHOLD : TRACKPAD_ARROW_THRESHOLD;
            logic->accumulated_x = 0;
        }
    }
    if (count == capacity) {
        /* a very fast swipe: drop the rest rather than queue a long burst of arrows */
        logic->accumulated_x = 0;
        logic->accumulated_y = 0;
    }
    return count;
}

static int8_t clamp_to_int8(int value)
{
    if (value > 127) {
        return 127;
    }
    if (value < -127) {
        return -127;
    }
    return (int8_t)value;
}

void trackpad_logic_mouse(int dx, int dy, int8_t *mouse_x, int8_t *mouse_y)
{
    *mouse_x = clamp_to_int8(dx * TRACKPAD_MOUSE_NUMERATOR / TRACKPAD_MOUSE_DENOMINATOR);
    *mouse_y = clamp_to_int8(dy * TRACKPAD_MOUSE_NUMERATOR / TRACKPAD_MOUSE_DENOMINATOR);
}

uint8_t trackpad_arrow_usage(uint8_t arrow)
{
    switch (arrow) {
    case TRACKPAD_ARROW_UP:
        return HID_USAGE_ARROW_UP;
    case TRACKPAD_ARROW_DOWN:
        return HID_USAGE_ARROW_DOWN;
    case TRACKPAD_ARROW_LEFT:
        return HID_USAGE_ARROW_LEFT;
    default:
        return HID_USAGE_ARROW_RIGHT;
    }
}
