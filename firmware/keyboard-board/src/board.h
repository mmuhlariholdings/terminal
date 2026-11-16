/*
 * board.h: RP2040 pin map of the Terminal 1 keyboard and power board (Rev A), and of the bench build on a Raspberry Pi Pico.
 *
 * Must match hardware/keyboard-board/electronics/pin-map.md, which is owned by
 * hardware/keyboard-board/electronics/generate_schematic.py. Change the schematic generator first, then this file.
 *
 * The bench build (CMake option TERMINAL_BOARD=bench) uses the same GPIO numbers on a plain Pico. GPIO 23, 24, 25 and 29
 * are not on the Pico's header (they are the SMPS mode pin, VBUS sense, the LED and VSYS/3), so the bench build never
 * drives GPIO 23 and never reads GPIO 24 or 29; GPIO 25 (the Pico LED) shows "the boost would be on".
 *
 * Keyboard matrix pins follow the Solder Party BBQ20KBD board (https://github.com/solderparty/bbq20kbd_hw, CERN-OHL-1.2)
 * and its firmware i2c_puppet (https://github.com/solderparty/i2c_puppet, MIT, boards/bbq20kbd_breakout.h).
 */
#ifndef TERMINAL_BOARD_H
#define TERMINAL_BOARD_H

#ifndef TERMINAL_BOARD_BENCH
#define TERMINAL_BOARD_BENCH 0
#endif

/* ---- power button (also wired to the BQ25895 /QON pin through a diode) ---- */
#define PIN_POWER_BUTTON 0 /* input, pull-up, low = pressed */

/* ---- keyboard matrix: rows are inputs with pull-ups, one column at a time is driven low ---- */
#define PIN_KEYBOARD_ROW1 1
#define PIN_KEYBOARD_ROW2 2
#define PIN_KEYBOARD_ROW3 3
#define PIN_KEYBOARD_ROW4 4
#define PIN_KEYBOARD_ROW5 5
#define PIN_KEYBOARD_ROW6 6
#define PIN_KEYBOARD_ROW7 7
#define PIN_KEYBOARD_COL1 8
#define PIN_KEYBOARD_COL2 9
#define PIN_KEYBOARD_COL3 14
#define PIN_KEYBOARD_COL4 13
#define PIN_KEYBOARD_COL5 12
#define PIN_KEYBOARD_COL6 11
#define PIN_KEYBOARD_COL7 10 /* the single nav key "RIGHT2", read directly: pull-up, low = pressed */

#define KEYBOARD_ROW_PINS {PIN_KEYBOARD_ROW1, PIN_KEYBOARD_ROW2, PIN_KEYBOARD_ROW3, PIN_KEYBOARD_ROW4, \
                           PIN_KEYBOARD_ROW5, PIN_KEYBOARD_ROW6, PIN_KEYBOARD_ROW7}
#define KEYBOARD_COLUMN_PINS {PIN_KEYBOARD_COL1, PIN_KEYBOARD_COL2, PIN_KEYBOARD_COL3, \
                              PIN_KEYBOARD_COL4, PIN_KEYBOARD_COL5, PIN_KEYBOARD_COL6}

/* ---- keyboard backlight: PWM7 B, low-side N-MOSFET, high = LEDs on ---- */
#define PIN_BACKLIGHT_PWM 15

/* ---- trackpad (1.8 V side behind BSS138 level shifters, all non-inverting) ---- */
#define PIN_TRACKPAD_RESET 16    /* output, low = reset */
#define PIN_TRACKPAD_SHUTDOWN 17 /* output, high = trackpad shut down */
#define PIN_TRACKPAD_MOTION 22   /* input, low = motion data waiting */

/* ---- I2C1: BQ25895 charger, MAX17048 gauge, trackpad ---- */
#define PIN_I2C_SDA 18
#define PIN_I2C_SCL 19
#define I2C_BUS i2c1
#define I2C_FREQUENCY_HZ 100000
#define I2C_ADDRESS_CHARGER 0x6A  /* BQ25895 (datasheet SLUSC88C, 8.2.16) */
#define I2C_ADDRESS_GAUGE 0x36    /* MAX17048 */
#define I2C_ADDRESS_TRACKPAD 0x3B /* Q20 optical trackpad (from i2c_puppet app/touchpad.c) */

/* ---- power management ---- */
#define PIN_POWER_INTERRUPT 20         /* input, low = BQ25895 /INT pulse or MAX17048 /ALRT (wired-OR, 10k pull-up) */
#define PIN_USB_SELECT 21              /* output: low = CM4 USB <-> RP2040 (normal), high = CM4 USB <-> USB-C (service) */
#define PIN_CM4_SHUTDOWN_REQUEST 23    /* output: high = N-MOSFET pulls CM4_SHUTDOWN_REQ (CM4 GPIO17) low */
#define PIN_CM4_RUN_POWER_GOOD 24      /* input: high = CM4 running (RUN_PG) */
#define PIN_BOOST_ENABLE 25            /* output: high = TPS61089 boost on (+5V_CM4) */
#define PIN_CM4_GLOBAL_ENABLE_HOLD 26  /* output: high = N-MOSFET holds CM4_GLOBAL_EN low (CM4 off); board pull-up holds it at reset */
#define PIN_CM4_RPIBOOT 27             /* output: high = N-MOSFET pulls CM4_nRPIBOOT low (CM4 boots from USB) */
#define PIN_CM4_POWEROFF 28            /* input: high = Linux has halted (gpio-poweroff on CM4 GPIO26) */
#define PIN_CM4_3V3_SENSE 29           /* input: high = CM4 3.3 V present */

#define BOARD_REVISION_LETTER "A"

#endif
