/*
 * bq25895.h: driver for the TI BQ25895 charger with power path (I2C 0x6A).
 * Register numbers and bit fields from the TI datasheet SLUSC88C (March 2015, revised October 2022), section 8.4.
 */
#ifndef TERMINAL_BQ25895_H
#define TERMINAL_BQ25895_H

#include <stdbool.h>
#include <stdint.h>

struct bq25895_status {
    bool present;
    uint8_t vbus_status;    /* REG0B[7:5]: 0 no input, 1 SDP, 2 CDP, 3 DCP, 4 MaxCharge, 5 unknown, 6 non-standard, 7 OTG */
    uint8_t charge_status;  /* REG0B[4:3]: 0 not charging, 1 pre-charge, 2 fast charge, 3 done */
    bool power_good;        /* REG0B[2] */
    uint8_t faults;         /* REG0C (read twice: the second read is the present state) */
    int battery_millivolts; /* REG0E BATV */
    int system_millivolts;  /* REG0F SYSV */
    int vbus_millivolts;    /* REG11 VBUSV, 0 if no VBUS */
    int charge_milliamps;   /* REG12 ICHGR */
};

/* Configure the charger. Returns false if it does not answer. */
bool bq25895_init(void);
bool bq25895_read_status(struct bq25895_status *status);

#endif
