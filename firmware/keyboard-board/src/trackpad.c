/*
 * trackpad.c: Q20 optical trackpad driver, ported from the Solder Party i2c_puppet firmware
 * (https://github.com/solderparty/i2c_puppet, app/touchpad.c, MIT licence, Copyright (c) 2022 Solder Party AB).
 * Registers as used there: 0x00 product ID, 0x02 MOTION (bit 7 = motion), 0x03 DELTA_X, 0x04 DELTA_Y (signed 8-bit).
 * Differences: polled from the main loop instead of read inside the GPIO interrupt, and the bus is shared with the
 * charger and gauge (one I2C bus through BSS138 level shifters).
 */
#include "trackpad.h"

#include <stdint.h>

#include "board.h"
#include "hardware/gpio.h"
#include "i2c_bus.h"
#include "pico/stdlib.h"

#define REGISTER_PRODUCT_ID 0x00
#define REGISTER_MOTION 0x02
#define REGISTER_DELTA_X 0x03
#define REGISTER_DELTA_Y 0x04
#define MOTION_BIT 0x80

bool trackpad_init(void)
{
    gpio_init(PIN_TRACKPAD_SHUTDOWN);
    gpio_set_dir(PIN_TRACKPAD_SHUTDOWN, GPIO_OUT);
    gpio_put(PIN_TRACKPAD_SHUTDOWN, 0);

    gpio_init(PIN_TRACKPAD_MOTION);
    gpio_set_dir(PIN_TRACKPAD_MOTION, GPIO_IN);
    gpio_pull_up(PIN_TRACKPAD_MOTION);

    gpio_init(PIN_TRACKPAD_RESET);
    gpio_set_dir(PIN_TRACKPAD_RESET, GPIO_OUT);
    gpio_put(PIN_TRACKPAD_RESET, 0);
    sleep_ms(100); /* reset pulse length as in i2c_puppet */
    gpio_put(PIN_TRACKPAD_RESET, 1);
    sleep_ms(10);

    uint8_t product;
    return i2c_bus_read_byte(I2C_ADDRESS_TRACKPAD, REGISTER_PRODUCT_ID, &product);
}

void trackpad_set_shutdown(bool shutdown)
{
    gpio_put(PIN_TRACKPAD_SHUTDOWN, shutdown ? 1 : 0);
}

bool trackpad_read_motion(int *dx, int *dy)
{
    if (gpio_get(PIN_TRACKPAD_MOTION)) {
        return false; /* no motion waiting */
    }
    uint8_t motion, x, y;
    if (!i2c_bus_read_byte(I2C_ADDRESS_TRACKPAD, REGISTER_MOTION, &motion) || !(motion & MOTION_BIT)) {
        return false;
    }
    if (!i2c_bus_read_byte(I2C_ADDRESS_TRACKPAD, REGISTER_DELTA_X, &x) ||
        !i2c_bus_read_byte(I2C_ADDRESS_TRACKPAD, REGISTER_DELTA_Y, &y)) {
        return false;
    }
    /* same axis convention as i2c_puppet: x is flipped */
    *dx = -(int)(int8_t)x;
    *dy = (int)(int8_t)y;
    return true;
}
