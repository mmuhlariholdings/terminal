/* sticky_modifiers.c: sticky modifier state machine (see sticky_modifiers.h). Pure logic, no hardware access. */
#include "sticky_modifiers.h"

#include <string.h>

void sticky_init(struct sticky_modifiers *sticky)
{
    memset(sticky, 0, sizeof(*sticky));
}

void sticky_press(struct sticky_modifiers *sticky, enum sticky_modifier modifier)
{
    sticky->down[modifier] = true;
    sticky->used[modifier] = false;
}

void sticky_release(struct sticky_modifiers *sticky, enum sticky_modifier modifier)
{
    if (!sticky->down[modifier]) {
        return;
    }
    sticky->down[modifier] = false;
    if (sticky->used[modifier]) {
        /* it was held as a normal modifier: it ends with the release */
        sticky->state[modifier] = STICKY_OFF;
        return;
    }
    /* a tap: off -> one-shot -> locked -> off */
    switch (sticky->state[modifier]) {
    case STICKY_OFF:
        sticky->state[modifier] = STICKY_ONE_SHOT;
        break;
    case STICKY_ONE_SHOT:
        sticky->state[modifier] = STICKY_LOCKED;
        break;
    default:
        sticky->state[modifier] = STICKY_OFF;
        break;
    }
}

bool sticky_active(const struct sticky_modifiers *sticky, enum sticky_modifier modifier)
{
    return sticky->down[modifier] || sticky->state[modifier] != STICKY_OFF;
}

bool sticky_held_or_locked(const struct sticky_modifiers *sticky, enum sticky_modifier modifier)
{
    return sticky->down[modifier] || sticky->state[modifier] == STICKY_LOCKED;
}

void sticky_consume(struct sticky_modifiers *sticky)
{
    for (int modifier = 0; modifier < STICKY_COUNT; modifier++) {
        if (sticky->down[modifier]) {
            sticky->used[modifier] = true;
        } else if (sticky->state[modifier] == STICKY_ONE_SHOT) {
            sticky->state[modifier] = STICKY_OFF;
        }
    }
}
