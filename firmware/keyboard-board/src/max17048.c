/*
 * max17048.c: MAX17048 fuel gauge driver.
 *
 * Registers (16-bit, most significant byte first) *verify* against the MAX17048/MAX17049 datasheet:
 *   0x02 VCELL    78.125 uV per bit
 *   0x04 SOC      high byte = percent, low byte = 1/256 percent
 *   0x08 VERSION  production version (any answer means the gauge is there)
 *   0x0C CONFIG   high byte RCOMP; low byte: bit 7 SLEEP, bit 6 ALSC, bit 5 ALRT (alert flag, write 0 to clear),
 *                 bits 4:0 ATHD (empty alert at 32 - ATHD percent)
 *   0x1A STATUS   alert causes (not used yet)
 * The cell model (RCOMP and the default ModelGauge model) is the chip's default: fine for a typical LiPo, to be checked
 * against the real cell by a discharge test.
 */
#include "max17048.h"

#include "board.h"
#include "i2c_bus.h"

#define REGISTER_VCELL 0x02
#define REGISTER_SOC 0x04
#define REGISTER_VERSION 0x08
#define REGISTER_CONFIG 0x0C

#define CONFIG_ALERT_FLAG 0x20

static bool read_word(uint8_t reg, uint16_t *value)
{
    uint8_t data[2];
    if (!i2c_bus_read(I2C_ADDRESS_GAUGE, reg, data, 2)) {
        return false;
    }
    *value = (uint16_t)((data[0] << 8) | data[1]);
    return true;
}

static bool write_word(uint8_t reg, uint16_t value)
{
    const uint8_t data[2] = {(uint8_t)(value >> 8), (uint8_t)value};
    return i2c_bus_write(I2C_ADDRESS_GAUGE, reg, data, 2);
}

bool max17048_init(uint8_t empty_alert_percent)
{
    uint16_t version, config;
    if (!read_word(REGISTER_VERSION, &version) || !read_word(REGISTER_CONFIG, &config)) {
        return false;
    }
    if (empty_alert_percent < 1) {
        empty_alert_percent = 1;
    }
    if (empty_alert_percent > 32) {
        empty_alert_percent = 32;
    }
    const uint8_t athd = (uint8_t)(32 - empty_alert_percent);
    config = (uint16_t)((config & 0xFF00) | (config & 0x00C0) | athd); /* keep RCOMP, SLEEP, ALSC; clear ALRT */
    return write_word(REGISTER_CONFIG, config);
}

bool max17048_read(struct max17048_reading *reading)
{
    uint16_t vcell, soc;
    reading->present = false;
    if (!read_word(REGISTER_VCELL, &vcell) || !read_word(REGISTER_SOC, &soc)) {
        return false;
    }
    reading->present = true;
    reading->cell_millivolts = (int)(((uint32_t)vcell * 78125u) / 1000000u);
    int percent = (soc + 128) >> 8; /* round */
    reading->percent = percent > 100 ? 100 : percent;
    return true;
}

void max17048_clear_alert(void)
{
    uint16_t config;
    if (read_word(REGISTER_CONFIG, &config) && (config & CONFIG_ALERT_FLAG)) {
        write_word(REGISTER_CONFIG, (uint16_t)(config & ~CONFIG_ALERT_FLAG));
    }
}
