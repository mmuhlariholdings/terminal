/*
 * debounce.h: per-key integrating debounce for up to 64 inputs (pure logic, unit-tested on the host).
 *
 * Call debounce_update() once per scan (every 1 ms) with the raw state (bit n set = input n reads pressed). Each input has
 * a counter that moves one step towards the raw reading per scan; the stable state changes only when the counter reaches
 * 0 or DEBOUNCE_STEPS. So a change must persist for DEBOUNCE_STEPS consecutive scans (5 ms at 1 ms) to be accepted, and
 * single-scan glitches are ignored.
 */
#ifndef TERMINAL_DEBOUNCE_H
#define TERMINAL_DEBOUNCE_H

#include <stdint.h>

#define DEBOUNCE_STEPS 5
#define DEBOUNCE_MAX_INPUTS 64

struct debounce {
    uint8_t count;                          /* number of inputs in use */
    uint8_t integrator[DEBOUNCE_MAX_INPUTS];
    uint64_t stable;                        /* debounced state, bit n = input n pressed */
};

void debounce_init(struct debounce *debounce, uint8_t count);

/* Feed one scan. Returns the mask of inputs whose stable state changed in this scan. */
uint64_t debounce_update(struct debounce *debounce, uint64_t raw);

static inline int debounce_is_pressed(const struct debounce *debounce, uint8_t input)
{
    return (int)((debounce->stable >> input) & 1u);
}

#endif
