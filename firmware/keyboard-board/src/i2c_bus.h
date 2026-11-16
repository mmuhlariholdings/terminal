/*
 * i2c_bus.h: the keyboard board's single I2C bus (I2C1 on GPIO 18/19): BQ25895, MAX17048 and the trackpad.
 * Every transfer has a timeout, so a missing device (the bench build) never hangs the firmware.
 */
#ifndef TERMINAL_I2C_BUS_H
#define TERMINAL_I2C_BUS_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

void i2c_bus_init(void);
bool i2c_bus_read(uint8_t address, uint8_t reg, uint8_t *data, size_t length);
bool i2c_bus_write(uint8_t address, uint8_t reg, const uint8_t *data, size_t length);
bool i2c_bus_read_byte(uint8_t address, uint8_t reg, uint8_t *value);
bool i2c_bus_write_byte(uint8_t address, uint8_t reg, uint8_t value);

#endif
