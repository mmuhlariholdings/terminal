/*
 * trackpad.h: driver for the BlackBerry Q20 optical trackpad (I2C 0x3B, 1.8 V, behind level shifters).
 * Ported from the Solder Party i2c_puppet firmware (app/touchpad.c, MIT licence, Copyright (c) 2022 Solder Party AB).
 */
#ifndef TERMINAL_TRACKPAD_H
#define TERMINAL_TRACKPAD_H

#include <stdbool.h>

/* Reset and wake the trackpad. Returns false if it does not answer on I2C. */
bool trackpad_init(void);

/* Shut the trackpad down (device off) or wake it. */
void trackpad_set_shutdown(bool shutdown);

/* If the trackpad has motion waiting (MOTION pin low), read it: dx positive = right, dy positive = down. */
bool trackpad_read_motion(int *dx, int *dy);

#endif
