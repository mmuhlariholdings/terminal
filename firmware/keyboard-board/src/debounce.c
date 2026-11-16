/* debounce.c: per-key integrating debounce (see debounce.h). Pure logic, no hardware access. */
#include "debounce.h"

#include <string.h>

void debounce_init(struct debounce *debounce, uint8_t count)
{
    memset(debounce, 0, sizeof(*debounce));
    debounce->count = count > DEBOUNCE_MAX_INPUTS ? DEBOUNCE_MAX_INPUTS : count;
}

uint64_t debounce_update(struct debounce *debounce, uint64_t raw)
{
    uint64_t changed = 0;
    for (uint8_t input = 0; input < debounce->count; input++) {
        const uint64_t bit = (uint64_t)1 << input;
        uint8_t *counter = &debounce->integrator[input];
        if (raw & bit) {
            if (*counter < DEBOUNCE_STEPS) {
                (*counter)++;
            }
            if (*counter == DEBOUNCE_STEPS && !(debounce->stable & bit)) {
                debounce->stable |= bit;
                changed |= bit;
            }
        } else {
            if (*counter > 0) {
                (*counter)--;
            }
            if (*counter == 0 && (debounce->stable & bit)) {
                debounce->stable &= ~bit;
                changed |= bit;
            }
        }
    }
    return changed;
}
