/* backlight.h: keyboard backlight, PWM on GPIO 15 into a low-side N-MOSFET (0-100 percent). */
#ifndef TERMINAL_BACKLIGHT_H
#define TERMINAL_BACKLIGHT_H

#include <stdint.h>

void backlight_init(void);
void backlight_set_percent(uint8_t percent);

#endif
