# Terminal 1 keyboard and power board: net list

Generated from `keyboard-board.kicad_sch` by its generator. Do not edit by hand.

| Net | Pins |
|---|---|
| `+1V8` | U7.5(VOUT), C22.1(~), J3.10(1V8), C40.1(~), Q2.1(G), R24.1(~), Q3.1(G), R26.1(~), Q4.1(G), R27.1(~), Q5.1(G), R29.1(~), Q6.1(G), R30.1(~), TP7.1(TP) |
| `+2V8` | U6.5(VOUT), C21.1(~), J3.8(2V8), C41.1(~), TP6.1(TP) |
| `+3V3` | U5.5(VOUT), C20.1(~), U6.1(VIN), U6.3(CE), U7.1(VIN), U7.3(CE), C23.1(~), U8.1(IOVDD), U8.10(IOVDD), U8.22(IOVDD), U8.33(IOVDD), U8.42(IOVDD), U8.49(IOVDD), U8.43(ADC_AVDD), U8.44(VREG_VIN), U8.48(USB_VDD), C24.1(~), C25.1(~), C26.1(~), C27.1(~), C28.1(~), C29.1(~), C30.1(~), C31.1(~), R13.1(~), U9.8(VCC), C35.1(~), U10.10(VCC), C38.1(~), R19.1(~), R20.1(~), R21.1(~), R22.1(~), J3.34(LEDA), J3.36(LEDA), R25.1(~), R28.1(~), R31.1(~), R32.1(~), TP5.1(TP) |
| `+5V_CM4` | U4.6(VOUT), R9.1(~), C15.1(~), C16.1(~), C17.1(~), C18.1(~), J4.2(+5V), J4.3(+5V), J4.4(+5V), J4.5(+5V), J4.6(+5V), J4.7(+5V), C42.1(~), TP4.1(TP) |
| `BACKLIGHT_CATHODE` | J3.33(LEDK), J3.35(LEDK), J3.37(LEDK), Q1.3(D) |
| `BACKLIGHT_PWM` | U8.18(GPIO15), Q1.1(G), R23.1(~), TP27.1(TP) |
| `BATTERY_NTC_DUMMY` | R6.2(~), JP1.1(1) |
| `BOOST_BOOT` | U4.10(BOOT), C10.1(~) |
| `BOOST_COMP` | U4.4(COMP), R11.1(~) |
| `BOOST_COMP_RC` | R11.2(~), C12.1(~) |
| `BOOST_ENABLE` | U4.7(EN), R12.1(~), U8.37(GPIO25), TP15.1(TP) |
| `BOOST_FB` | U4.3(FB), R9.2(~), R10.1(~) |
| `BOOST_FSW` | U4.1(FSW), R7.1(~) |
| `BOOST_ILIM` | U4.8(ILIM), R8.1(~) |
| `BOOST_SW` | U4.11(SW), L2.2(~), R7.2(~), C10.2(~) |
| `BOOST_VCC` | U4.2(VCC), C11.1(~) |
| `BOOTSEL` | R14.2(~), SW1.1(1), TP26.1(TP) |
| `CHARGER_BOOTSTRAP` | U2.21(BTST), C4.1(~) |
| `CHARGER_ILIM` | U2.10(ILIM), R3.1(~) |
| `CHARGER_PMID` | U2.23(PMID), C2.1(~), C3.1(~) |
| `CHARGER_QON` | U2.12(~{QON}), D1.2(A) |
| `CHARGER_REGN` | U2.22(REGN), C5.1(~), R4.1(~) |
| `CHARGER_SW` | U2.19(SW), U2.20(SW), C4.2(~), L1.1(~) |
| `CHARGER_TS` | U2.11(TS), R4.2(~), R5.1(~), R6.1(~), J2.2(NTC), TP29.1(TP) |
| `CM4_3V3_SENSE` | J4.18(3V3_SENSE), R39.1(~) |
| `CM4_3V3_SENSE_IN` | U8.41(GPIO29), R39.2(~), R40.1(~) |
| `CM4_GLOBAL_EN` | J4.16(GLOBAL_EN), Q7.3(D), TP17.1(TP) |
| `CM4_GLOBAL_EN_HOLD` | U8.38(GPIO26), Q7.1(G), R32.2(~) |
| `CM4_POWEROFF` | J4.19(POWEROFF), R37.1(~), TP20.1(TP) |
| `CM4_POWEROFF_SENSE` | U8.40(GPIO28), R37.2(~), R38.1(~) |
| `CM4_RPIBOOT_DRIVE` | U8.39(GPIO27), Q8.1(G), R33.1(~) |
| `CM4_RUN_PG` | J4.17(RUN_PG), R35.1(~), TP18.1(TP) |
| `CM4_RUN_PG_SENSE` | U8.36(GPIO24), R35.2(~), R36.1(~) |
| `CM4_SHUTDOWN_REQ` | J4.20(SHUTDOWN_REQ), Q9.3(D) |
| `CM4_SHUTDOWN_REQUEST_DRIVE` | U8.35(GPIO23), Q9.1(G), R34.1(~) |
| `CM4_nRPIBOOT` | J4.15(nRPIBOOT), Q8.3(D), TP19.1(TP) |
| `GND` | J1.A1(GND), J1.A12(GND), J1.SH(SHIELD), J1.B1(GND), J1.B12(GND), R1.2(~), R2.2(~), U1.2(GND), #FLG02.1(pwr), U2.8(OTG), U2.9(~{CE}), U2.17(PGND), U2.18(PGND), U2.25(EP), C1.2(~), C2.2(~), C3.2(~), C5.2(~), C6.2(~), C7.2(~), C8.2(~), R3.2(~), R5.2(~), JP1.2(2), J2.3(BAT-), U3.4(GND), U3.9(EP), U3.6(QSTRT), U3.1(CTG), C9.2(~), U4.5(GND), C11.2(~), R8.2(~), R10.2(~), C12.2(~), R12.2(~), C13.2(~), C14.2(~), C15.2(~), C16.2(~), C17.2(~), C18.2(~), U5.2(GND), C19.2(~), C20.2(~), U6.2(GND), C21.2(~), U7.2(GND), C22.2(~), C23.2(~), U8.19(TESTEN), U8.57(GND), C24.2(~), C25.2(~), C26.2(~), C27.2(~), C28.2(~), C29.2(~), C30.2(~), C31.2(~), C32.2(~), C33.2(~), C34.2(~), U9.4(GND), C35.2(~), SW1.2(2), Y1.2(GND), Y1.4(GND), C36.2(~), C37.2(~), U10.6(~{OE}), U10.5(GND), U10.11(EP), C38.2(~), R18.2(~), SW2.2(2), C39.2(~), J3.1(GND), J3.7(GND), J3.9(GND), J3.11(GND), J3.19(GND), J3.20(GND), J3.21(GND), J3.22(AGND), J3.25(GND), J3.40(GND), J3.MP1(MP1), J3.MP2(MP2), J3.MP3(MP3), J3.MP4(MP4), Q1.2(S), R23.2(~), C40.2(~), C41.2(~), J4.1(GND), J4.8(GND), J4.9(GND), J4.10(GND), J4.11(GND), J4.14(GND), J4.23(GND), J4.24(GND), J4.MP(MP), Q7.2(S), Q8.2(S), R33.2(~), Q9.2(S), R34.2(~), R36.2(~), R38.2(~), R40.2(~), C42.2(~), TP8.1(TP), TP9.1(TP) |
| `I2C_SCL` | U2.5(SCL), U3.7(SCL), U8.30(GPIO19), R20.2(~), Q3.3(D), TP12.1(TP) |
| `I2C_SDA` | U2.6(SDA), U3.8(SDA), U8.29(GPIO18), R19.2(~), Q5.3(D), TP11.1(TP) |
| `KEYBOARD_COL1` | U8.11(GPIO8), J3.12(COL1) |
| `KEYBOARD_COL2` | U8.12(GPIO9), J3.13(COL2) |
| `KEYBOARD_COL3` | U8.17(GPIO14), J3.14(COL3) |
| `KEYBOARD_COL4` | U8.16(GPIO13), J3.15(COL4) |
| `KEYBOARD_COL5` | U8.15(GPIO12), J3.16(COL5) |
| `KEYBOARD_COL6` | U8.14(GPIO11), J3.17(COL6) |
| `KEYBOARD_COL7` | U8.13(GPIO10), J3.18(COL7) |
| `KEYBOARD_ROW1` | U8.3(GPIO1), J3.32(ROW1) |
| `KEYBOARD_ROW2` | U8.4(GPIO2), J3.31(ROW2) |
| `KEYBOARD_ROW3` | U8.5(GPIO3), J3.30(ROW3) |
| `KEYBOARD_ROW4` | U8.6(GPIO4), J3.29(ROW4) |
| `KEYBOARD_ROW5` | U8.7(GPIO5), J3.28(ROW5) |
| `KEYBOARD_ROW6` | U8.8(GPIO6), J3.27(ROW6) |
| `KEYBOARD_ROW7` | U8.9(GPIO7), J3.26(ROW7) |
| `POWER_BUTTON` | D1.1(K), U8.2(GPIO0), SW2.1(1), R22.2(~), C39.1(~), TP14.1(TP) |
| `POWER_INTERRUPT` | U2.7(~{INT}), U3.5(~{ALRT}), U8.31(GPIO20), R21.2(~), TP13.1(TP) |
| `QSPI_SCLK` | U8.52(QSPI_SCLK), U9.6(CLK) |
| `QSPI_SD0` | U8.53(QSPI_SD0), U9.5(DI/IO0) |
| `QSPI_SD1` | U8.55(QSPI_SD1), U9.2(DO/IO1) |
| `QSPI_SD2` | U8.54(QSPI_SD2), U9.3(~{WP}/IO2) |
| `QSPI_SD3` | U8.51(QSPI_SD3), U9.7(~{HOLD}/IO3) |
| `QSPI_SS` | U8.56(QSPI_SS), U9.1(~{CS}), R14.1(~) |
| `RP2040_DVDD` | U8.45(VREG_VOUT), U8.23(DVDD), U8.50(DVDD), C32.1(~), C33.1(~), C34.1(~), TP10.1(TP) |
| `RP2040_RUN` | U8.26(RUN), R13.2(~), TP25.1(TP) |
| `RP2040_SWCLK` | U8.24(SWCLK), TP23.1(TP) |
| `RP2040_SWDIO` | U8.25(SWDIO), TP24.1(TP) |
| `RP2040_USB_D_N` | U8.46(USB_DM), R17.1(~) |
| `RP2040_USB_D_P` | U8.47(USB_DP), R16.1(~) |
| `RP2040_XIN` | U8.20(XIN), Y1.1(1), C36.1(~) |
| `RP2040_XOUT` | U8.21(XOUT), R15.1(~) |
| `RP2040_XOUT_CRYSTAL` | Y1.3(3), R15.2(~), C37.1(~) |
| `TRACKPAD_MOTION` | U8.34(GPIO22), Q4.3(D), R28.2(~), TP28.1(TP) |
| `TRACKPAD_MOTION_1V8` | J3.4(TP_MOTION), Q4.2(S), R27.2(~) |
| `TRACKPAD_RESET` | U8.27(GPIO16), Q6.3(D), R31.2(~) |
| `TRACKPAD_RESET_1V8` | J3.6(TP_RESET), Q6.2(S), R30.2(~) |
| `TRACKPAD_SCL_1V8` | J3.3(TP_SCL), Q3.2(S), R26.2(~) |
| `TRACKPAD_SDA_1V8` | J3.5(TP_SDA), Q5.2(S), R29.2(~) |
| `TRACKPAD_SHUTDOWN` | U8.28(GPIO17), Q2.3(D), R25.2(~) |
| `TRACKPAD_SHUTDOWN_1V8` | J3.2(TP_SHDN), Q2.2(S), R24.2(~) |
| `UART_CM4_RX` | J4.22(UART_RX), TP22.1(TP) |
| `UART_CM4_TX` | J4.21(UART_TX), TP21.1(TP) |
| `USB_CM4_D_N` | U10.7(D-), J4.13(USB_D-) |
| `USB_CM4_D_P` | U10.8(D+), J4.12(USB_D+) |
| `USB_C_CC1` | J1.A5(CC1), R1.1(~) |
| `USB_C_CC2` | J1.B5(CC2), R2.1(~) |
| `USB_C_D_N` | J1.A7(D-), J1.B7(D-), U1.3(IO2), U1.4(IO2), U2.3(D-), U10.4(2D-) |
| `USB_C_D_P` | J1.A6(D+), J1.B6(D+), U1.1(IO1), U1.6(IO1), U2.2(D+), U10.3(2D+) |
| `USB_RP2040_D_N` | R17.2(~), U10.2(1D-) |
| `USB_RP2040_D_P` | R16.2(~), U10.1(1D+) |
| `USB_SELECT` | U8.32(GPIO21), U10.9(S), R18.1(~), TP16.1(TP) |
| `VBAT` | U2.13(BAT), U2.14(BAT), C8.1(~), #FLG04.1(pwr), J2.1(BAT+), U3.3(VDD), U3.2(CELL), C9.1(~), TP3.1(TP) |
| `VBUS` | J1.A4(VBUS), J1.A9(VBUS), J1.B4(VBUS), J1.B9(VBUS), U1.5(VBUS), #FLG01.1(pwr), U2.1(VBUS), C1.1(~), TP1.1(TP) |
| `VSYS` | U2.15(SYS), U2.16(SYS), L1.2(~), C6.1(~), C7.1(~), #FLG03.1(pwr), U4.9(VIN), L2.1(~), C13.1(~), C14.1(~), U5.1(VIN), U5.3(CE), C19.1(~), TP2.1(TP) |

## Parts

| Ref | Value | LCSC | Description |
|---|---|---|---|
| C1 | 1uF | C15849 | VBUS input (datasheet: 1 uF at VBUS) |
| C2 | 10uF 25V | C15850 | PMID (datasheet: at least 8.2 uF without OTG) |
| C3 | 10uF 25V | C15850 | PMID, second (DC bias derating) |
| C4 | 47nF |  | Bootstrap capacitor (datasheet: 47 nF) |
| C5 | 4.7uF 10V |  | REGN (datasheet: 4.7 uF, 10 V) |
| C6 | 22uF 25V | C12891 | SYS output (datasheet: at least 20 uF) |
| C7 | 22uF 25V | C12891 | SYS output |
| C8 | 10uF 25V | C15850 | BAT (datasheet: 10 uF close to BAT) |
| C9 | 1uF | C15849 | Gauge supply |
| C10 | 100nF | C14663 | Bootstrap capacitor (datasheet 0.1 uF) |
| C11 | 2.2uF |  | Internal regulator (datasheet: more than 1 uF) |
| C12 | 4.7nF |  | Compensation C (estimate) |
| C13 | 100nF | C14663 | Boost VIN pin, close to U pin 9 |
| C14 | 22uF 25V | C12891 | Boost input bulk |
| C15 | 22uF 25V | C12891 | Boost output (4 x 22 uF: about 35 uF left at 5 V after DC-bias derating, estimate) |
| C16 | 22uF 25V | C12891 | Boost output (4 x 22 uF: about 35 uF left at 5 V after DC-bias derating, estimate) |
| C17 | 22uF 25V | C12891 | Boost output (4 x 22 uF: about 35 uF left at 5 V after DC-bias derating, estimate) |
| C18 | 22uF 25V | C12891 | Boost output (4 x 22 uF: about 35 uF left at 5 V after DC-bias derating, estimate) |
| C19 | 1uF | C15849 | 3.3 V LDO input |
| C20 | 10uF 25V | C15850 | 3.3 V output |
| C21 | 1uF | C15849 | 2.8 V output |
| C22 | 1uF | C15849 | 1.8 V output |
| C23 | 1uF | C15849 | Trackpad LDO inputs |
| C24 | 100nF | C14663 | IOVDD decoupling, one per IOVDD pin |
| C25 | 100nF | C14663 | IOVDD decoupling, one per IOVDD pin |
| C26 | 100nF | C14663 | IOVDD decoupling, one per IOVDD pin |
| C27 | 100nF | C14663 | IOVDD decoupling, one per IOVDD pin |
| C28 | 100nF | C14663 | IOVDD decoupling, one per IOVDD pin |
| C29 | 100nF | C14663 | IOVDD decoupling, one per IOVDD pin |
| C30 | 100nF | C14663 | ADC_AVDD / USB_VDD decoupling |
| C31 | 1uF | C15849 | VREG_VIN |
| C32 | 1uF | C15849 | VREG_VOUT (1.1 V core) |
| C33 | 100nF | C14663 | DVDD pin 23 |
| C34 | 100nF | C14663 | DVDD pin 50 |
| C35 | 100nF | C14663 | Flash decoupling |
| C36 | 33pF |  | Crystal load: 2 x (20 pF - 3 pF stray) = 34 pF |
| C37 | 33pF |  | Crystal load |
| C38 | 100nF | C14663 | USB switch decoupling |
| C39 | 100nF | C14663 | Power button filter |
| C40 | 1uF | C15849 | Trackpad 1.8 V at the connector |
| C41 | 1uF | C15849 | Trackpad 2.8 V at the connector |
| C42 | 100nF | C14663 | FFC +5V pins, high frequency |
| D1 | B5819W | C8598 | Power button also pulls /QON low: 12-18 s hold with no USB = charger resets VSYS (pin 1 cathode) |
| J1 | USB-C | C165948 | USB-C receptacle at the bottom edge centre: charging, and the CM4's USB in service mode |
| J3 | Q20 keyboard | C424543 | Hirose BM20B(0.8)-40DS-0.4V receptacle for the Q20 keyboard flex, on the FRONT (pinout from BBQ20KBD U4) |
| J4 | To carrier | C202112 | Hirose FH12-24S-0.5SH 24-way 0.5 mm FFC, top edge centre, back side |
| L1 | 1uH | C167203 | Charger inductor 1 uH (datasheet recommends 1 uH), about 6 A |
| L2 | 2.2uH | C167218 | Boost inductor 2.2 uH, Isat 10 A (frame cut-out: 3.0 mm tall) |
| Q1 | AO3400A | C20917 | Keyboard backlight low-side switch (LED anodes on +3V3, as BBQ20KBD) (SOT-23: 1 G, 2 S, 3 D) |
| Q2 | BSS138 | C78284 | Level shifter, trackpad shutdown (1.8 V <-> 3.3 V) (SOT-23: 1 G, 2 S, 3 D) |
| Q3 | BSS138 | C78284 | Level shifter, trackpad I2C SCL (1.8 V <-> 3.3 V) (SOT-23: 1 G, 2 S, 3 D) |
| Q4 | BSS138 | C78284 | Level shifter, trackpad motion (1.8 V <-> 3.3 V) (SOT-23: 1 G, 2 S, 3 D) |
| Q5 | BSS138 | C78284 | Level shifter, trackpad I2C SDA (1.8 V <-> 3.3 V) (SOT-23: 1 G, 2 S, 3 D) |
| Q6 | BSS138 | C78284 | Level shifter, trackpad reset (1.8 V <-> 3.3 V) (SOT-23: 1 G, 2 S, 3 D) |
| Q7 | 2N7002 | C8545 | Holds the CM4 off (GLOBAL_EN low) when the gate is high (SOT-23: 1 G, 2 S, 3 D) |
| Q8 | 2N7002 | C8545 | Pulls nRPIBOOT low (service mode) (SOT-23: 1 G, 2 S, 3 D) |
| Q9 | 2N7002 | C8545 | Pulses CM4 GPIO17 low: clean shutdown request (SOT-23: 1 G, 2 S, 3 D) |
| R1 | 5k1 | C23186 | CC1 pull-down: sink, asks the charger for 5 V |
| R2 | 5k1 | C23186 | CC2 pull-down |
| R3 | 120R |  | ILIM: input current ceiling 355 / 120 = 3.0 A (firmware sets lower via I2C) |
| R4 | 5k1 | C23186 | TS divider top (datasheet RT1 5.23 k for 0-45 C with a 103AT NTC) |
| R5 | 30k |  | TS divider bottom (datasheet RT2 30.1 k) |
| R6 | 10k | C25804 | Stands in for the cell NTC (10 k = 25 C) when JP1 is bridged |
| R7 | 301k |  | FSW to SW: 500 kHz (datasheet table) |
| R8 | 127k |  | Peak current limit 1.03e6 / 127k = 8.1 A typical, 7.3 A minimum |
| R9 | 150k |  | Feedback top: 1.212 V x (1 + 150 / 47) = 5.08 V |
| R10 | 47k |  | Feedback bottom |
| R11 | 6k8 |  | Compensation R (estimate: circuit-notes.md, tune on the bench) |
| R12 | 100k | C25803 | Boost off while the RP2040 starts |
| R13 | 10k | C25804 | RUN pull-up (reset pad TP) |
| R14 | 1k | C21190 | BOOTSEL: holding the button at reset pulls flash CS low -> USB bootloader |
| R15 | 1k | C21190 | XOUT series resistor (as the Pico) |
| R16 | 27R |  | USB D+ series resistor (as the Pico) |
| R17 | 27R |  | USB D- series resistor |
| R18 | 100k | C25803 | Normal mode while the RP2040 starts |
| R19 | 4k7 | C23162 | I2C pull-up |
| R20 | 4k7 | C23162 | I2C pull-up |
| R21 | 10k | C25804 | Pull-up: BQ25895 /INT and MAX17048 /ALRT are open drain |
| R22 | 100k | C25803 | Power button pull-up (works with the RP2040 asleep) |
| R23 | 100k | C25803 | Backlight off while the RP2040 starts |
| R24 | 10k | C25804 | 1.8 V side pull-up, trackpad shutdown |
| R25 | 10k | C25804 | 3.3 V side pull-up, trackpad shutdown |
| R26 | 10k | C25804 | 1.8 V side pull-up, trackpad I2C SCL |
| R27 | 10k | C25804 | 1.8 V side pull-up, trackpad motion |
| R28 | 10k | C25804 | 3.3 V side pull-up, trackpad motion |
| R29 | 10k | C25804 | 1.8 V side pull-up, trackpad I2C SDA |
| R30 | 10k | C25804 | 1.8 V side pull-up, trackpad reset |
| R31 | 10k | C25804 | 3.3 V side pull-up, trackpad reset |
| R32 | 100k | C25803 | Gate pull-UP: the CM4 is held off while the RP2040 resets |
| R33 | 100k | C25803 | Gate pull-down: normal eMMC boot |
| R34 | 100k | C25803 | Gate pull-down |
| R35 | 1k | C21190 | Series resistor: CM4_RUN_PG into the RP2040 (limits current if the CM4 is powered and the RP2040 is not) |
| R36 | 100k | C25803 | Pull-down: reads low while the CM4 is off (CM4_RUN_PG) |
| R37 | 1k | C21190 | Series resistor: CM4_POWEROFF into the RP2040 (limits current if the CM4 is powered and the RP2040 is not) |
| R38 | 100k | C25803 | Pull-down: reads low while the CM4 is off (CM4_POWEROFF) |
| R39 | 1k | C21190 | Series resistor: CM4_3V3_SENSE into the RP2040 (limits current if the CM4 is powered and the RP2040 is not) |
| R40 | 100k | C25803 | Pull-down: reads low while the CM4 is off (CM4_3V3_SENSE) |
| SW1 | BOOTSEL | C318884 | BOOTSEL button (firmware can also be loaded from the CM4 with picotool) |
| SW2 | Power | C110293 | Side-push power button on the right edge, 46 mm up from the board's bottom edge |
| U1 | USBLC6-2SC6 | C7519 | ESD protection on the USB-C data lines and VBUS |
| U2 | BQ25895 | C80200 | BQ25895RTW: 1-cell charger with power path, 1.5 MHz buck, I2C 0x6A, BC1.2 detection on D+/D- |
| U3 | MAX17048 | C2682616 | MAX17048 fuel gauge, I2C 0x36 (pinout from memory: 1 CTG, 2 CELL, 3 VDD, 4 GND, 5 ALRT, 6 QSTRT, 7 SCL, 8 SDA: CHECK) |
| U4 | TPS61089 | C165129 | TPS61089 7 A synchronous boost (VQFN-11 RNR), from VSYS, 500 kHz, PFM at light load |
| U5 | ME6211C33 | C82942 | 3.3 V LDO 500 mA, always on from VSYS (dropout about 0.1 V at 100 mA) |
| U6 | ME6211C28 | C53099 | 2.8 V for the trackpad (as BBQ20KBD) |
| U7 | ME6211C18 | C236671 | 1.8 V for the trackpad I/O (as BBQ20KBD) |
| U8 | RP2040 | C2040 | Raspberry Pi RP2040 (QFN-56): keyboard, trackpad, USB device, power manager |
| U9 | W25Q128JV | C190862 | 16 MB QSPI flash (WSON-8 6 x 5); exposed pad left unconnected (Winbond: may float or go to GND) |
| U10 | TS3USB221 | C324071 | TS3USB221 (DRC): S low = CM4 to RP2040 (port 1), S high = CM4 to USB-C (port 2); datasheet SCDS220M |
| Y1 | 12MHz | C9002 | 12 MHz crystal, 20 pF load |
