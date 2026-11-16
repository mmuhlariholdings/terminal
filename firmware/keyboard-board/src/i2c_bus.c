/* i2c_bus.c: register access on the keyboard board's I2C bus, with timeouts (see i2c_bus.h). */
#include "i2c_bus.h"

#include <string.h>

#include "board.h"
#include "hardware/gpio.h"
#include "hardware/i2c.h"

#define I2C_TIMEOUT_US 5000

void i2c_bus_init(void)
{
    i2c_init(I2C_BUS, I2C_FREQUENCY_HZ);
    gpio_set_function(PIN_I2C_SDA, GPIO_FUNC_I2C);
    gpio_set_function(PIN_I2C_SCL, GPIO_FUNC_I2C);
    /* the board has external pull-ups; the internal ones help the bench build when a breakout has none */
    gpio_pull_up(PIN_I2C_SDA);
    gpio_pull_up(PIN_I2C_SCL);
}

bool i2c_bus_read(uint8_t address, uint8_t reg, uint8_t *data, size_t length)
{
    if (i2c_write_timeout_us(I2C_BUS, address, &reg, 1, true, I2C_TIMEOUT_US) != 1) {
        return false;
    }
    return i2c_read_timeout_us(I2C_BUS, address, data, length, false, I2C_TIMEOUT_US) == (int)length;
}

bool i2c_bus_write(uint8_t address, uint8_t reg, const uint8_t *data, size_t length)
{
    uint8_t buffer[8];
    if (length + 1 > sizeof(buffer)) {
        return false;
    }
    buffer[0] = reg;
    memcpy(&buffer[1], data, length);
    return i2c_write_timeout_us(I2C_BUS, address, buffer, length + 1, false, I2C_TIMEOUT_US) == (int)(length + 1);
}

bool i2c_bus_read_byte(uint8_t address, uint8_t reg, uint8_t *value)
{
    return i2c_bus_read(address, reg, value, 1);
}

bool i2c_bus_write_byte(uint8_t address, uint8_t reg, uint8_t value)
{
    return i2c_bus_write(address, reg, &value, 1);
}
