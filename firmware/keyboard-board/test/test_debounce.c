/* test_debounce.c: host tests for the per-key integrating debounce (src/debounce.c). */
#include "debounce.h"
#include "test_framework.h"

int main(void)
{
    struct debounce debounce;
    debounce_init(&debounce, 44);

    /* a press must last DEBOUNCE_STEPS scans */
    for (int scan = 1; scan < DEBOUNCE_STEPS; scan++) {
        CHECK_EQUAL(0, debounce_update(&debounce, 1u << 3));
    }
    CHECK_EQUAL(1u << 3, debounce_update(&debounce, 1u << 3));
    CHECK(debounce_is_pressed(&debounce, 3));
    CHECK_EQUAL(0, debounce_update(&debounce, 1u << 3)); /* no repeat change */

    /* a one-scan glitch while pressed is ignored */
    CHECK_EQUAL(0, debounce_update(&debounce, 0));
    CHECK_EQUAL(0, debounce_update(&debounce, 1u << 3));
    CHECK(debounce_is_pressed(&debounce, 3));

    /* a release must also last */
    uint64_t changed = 0;
    int scans = 0;
    while (!changed && scans < 20) {
        changed = debounce_update(&debounce, 0);
        scans++;
    }
    CHECK_EQUAL(1u << 3, changed);
    CHECK_EQUAL(DEBOUNCE_STEPS, scans);
    CHECK(!debounce_is_pressed(&debounce, 3));

    /* a one-scan glitch while released is ignored */
    debounce_update(&debounce, 1u << 7);
    for (int scan = 0; scan < 10; scan++) {
        CHECK_EQUAL(0, debounce_update(&debounce, 0));
    }

    /* the top input (43, the power button) works with a 64-bit mask */
    const uint64_t power = (uint64_t)1 << 43;
    for (int scan = 0; scan < DEBOUNCE_STEPS - 1; scan++) {
        debounce_update(&debounce, power);
    }
    CHECK_EQUAL(power, debounce_update(&debounce, power));

    /* inputs beyond count are ignored */
    struct debounce small;
    debounce_init(&small, 2);
    for (int scan = 0; scan < 10; scan++) {
        CHECK_EQUAL(0, debounce_update(&small, 1u << 5));
    }
    return test_summary("debounce");
}
