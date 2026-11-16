/*
 * bq25895.c: BQ25895 charger driver. Register values from TI datasheet SLUSC88C section 8.4 (register map).
 *
 * Settings written at start-up (every one survives only until a register reset, so they are re-applied whenever the
 * charger reports a watchdog fault):
 *   REG07 = 0x8D  EN_TERM=1, STAT_DIS=0, WATCHDOG=00 (I2C watchdog off: settings are not lost if the RP2040 is busy),
 *                 EN_TIMER=1, CHG_TIMER=10 (12 h), reserved bit 0 = 1
 *   REG02 = 0x71  CONV_START=0, CONV_RATE=1 (ADC every 1 s), BOOST_FREQ=1 (500 kHz, unused), ICO_EN=1,
 *                 HVDCP_EN=0 and MAXC_EN=0 (never ask a charger for 9 / 12 V: the USB-C input is rated for 5 V),
 *                 FORCE_DPDM=0, AUTO_DPDM_EN=1 (BC1.2 detection of the input current limit)
 *   REG03 = 0x1A  BAT_LOADEN=0, WD_RST=0, OTG_CONFIG=0 (the BQ25895 boost is not used: the CM4 has its own boost),
 *                 CHG_CONFIG=1, SYS_MIN=101 (3.5 V)
 *   REG04 = 0x20  EN_PUMPX=0, ICHG=0100000 = 2048 mA (about 0.5 C for a 4,000 mAh cell: an estimate, see circuit notes)
 *   REG06 = 0x5E  VREG=010111 (4.208 V), BATLOWV=1 (3.0 V), VRECHG=0 (100 mV)
 * The input current limit is left to BC1.2 detection (REG00 IINLIM) and the ILIM pin resistor, whichever is lower.
 */
#include "bq25895.h"

#include "board.h"
#include "i2c_bus.h"

#define REG00 0x00
#define REG02 0x02
#define REG03 0x03
#define REG04 0x04
#define REG06 0x06
#define REG07 0x07
#define REG0B 0x0B
#define REG0C 0x0C
#define REG0E 0x0E
#define REG0F 0x0F
#define REG11 0x11
#define REG12 0x12
#define REG14 0x14

#define REG0C_WATCHDOG_FAULT 0x80

static bool configure(void)
{
    static const struct {
        uint8_t reg;
        uint8_t value;
    } settings[] = {
        {REG07, 0x8D},
        {REG02, 0x71},
        {REG03, 0x1A},
        {REG04, 0x20},
        {REG06, 0x5E},
    };
    for (unsigned i = 0; i < sizeof(settings) / sizeof(settings[0]); i++) {
        if (!i2c_bus_write_byte(I2C_ADDRESS_CHARGER, settings[i].reg, settings[i].value)) {
            return false;
        }
    }
    return true;
}

bool bq25895_init(void)
{
    uint8_t part;
    /* REG14[5:3] PN = 111 for the BQ25895 */
    if (!i2c_bus_read_byte(I2C_ADDRESS_CHARGER, REG14, &part)) {
        return false;
    }
    return configure();
}

bool bq25895_read_status(struct bq25895_status *status)
{
    uint8_t reg0b, fault, adc[5];
    status->present = false;
    if (!i2c_bus_read_byte(I2C_ADDRESS_CHARGER, REG0B, &reg0b)) {
        return false;
    }
    /* REG0C latches faults: the first read returns and clears the old ones, the second the present state */
    i2c_bus_read_byte(I2C_ADDRESS_CHARGER, REG0C, &fault);
    if (fault & REG0C_WATCHDOG_FAULT) {
        configure(); /* the charger reset its registers to defaults */
    }
    i2c_bus_read_byte(I2C_ADDRESS_CHARGER, REG0C, &fault);
    /* REG0E..REG12 in one multi-byte read (allowed for every register except REG0C) */
    if (!i2c_bus_read(I2C_ADDRESS_CHARGER, REG0E, adc, sizeof(adc))) {
        return false;
    }
    status->present = true;
    status->vbus_status = (uint8_t)(reg0b >> 5);
    status->charge_status = (uint8_t)((reg0b >> 3) & 3u);
    status->power_good = (reg0b & 0x04) != 0;
    status->faults = fault;
    status->battery_millivolts = 2304 + (adc[0] & 0x7F) * 20; /* REG0E: offset 2.304 V, 20 mV/bit */
    status->system_millivolts = 2304 + (adc[1] & 0x7F) * 20;  /* REG0F: offset 2.304 V, 20 mV/bit */
    /* adc[2] = REG10 TS percentage, not used */
    status->vbus_millivolts = (adc[3] & 0x80) ? 2600 + (adc[3] & 0x7F) * 100 : 0; /* REG11: VBUS_GD, 2.6 V + 100 mV/bit */
    status->charge_milliamps = (adc[4] & 0x7F) * 50;                               /* REG12: 50 mA/bit */
    return true;
}
