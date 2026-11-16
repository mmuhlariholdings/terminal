/*
 * max17048.h: driver for the Analog Devices (Maxim) MAX17048 fuel gauge (I2C 0x36).
 * Register map from memory of the MAX17048/MAX17049 datasheet: *verify* against the datasheet before relying on it.
 */
#ifndef TERMINAL_MAX17048_H
#define TERMINAL_MAX17048_H

#include <stdbool.h>
#include <stdint.h>

struct max17048_reading {
    bool present;
    int cell_millivolts; /* VCELL */
    int percent;         /* SOC, rounded, 0-100 */
};

/* Detect the gauge and set its empty-alert threshold. Returns false if it does not answer. */
bool max17048_init(uint8_t empty_alert_percent);
bool max17048_read(struct max17048_reading *reading);

/* Clear the alert flag (and so release the /ALRT line). */
void max17048_clear_alert(void);

#endif
