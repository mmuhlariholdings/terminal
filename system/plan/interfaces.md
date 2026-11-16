# Terminal 1: interfaces and shared numbers

**Version:** 0.2 (2026-11-16) · **Status:** first draft, every number marked *verify* is a hand estimate or from memory.

This file is the **single source of truth** for numbers that more than one part of the project depends on: the device
envelope, board outlines, the cable between the two boards, the CM4 pins we use, the RP2040 pins and the USB protocol
between the keyboard board and Linux. The Onshape model, both KiCad boards, the firmware and the Linux image all read
from here. **Change it here first**, then in every place listed under "Used by".

---

## 1. Device frame and envelope

- Units: millimetres.
- Origin: centre of the **bottom edge** of the device, on the **back face**.
- **X** across the width (−42 … +42), **Y** up the device (0 at the bottom edge with the USB-C port, 150 at the top),
  **Z** through the thickness (0 = back face, +Z towards the screen and keys).

| Item | Value | Notes |
|---|---|---|
| Overall size | **84 × 150 × 19** (W × H × T) | Plan target was 84 × 150 × 20; the stack-up below fits 19 |
| Corner radius (plan view) | 9 | |
| Edge radius (front and back) | 2.5 | |
| Wall (printed shell, phase 3a) | 2.0 sides, 1.6 front | |
| Target mass | 250–300 g | to be weighed |

### Stack-up (front to back)

| Zone | Layer | Thickness | Z range (from back) |
|---|---|---|---|
| Screen half (Y 70–150) | Cover glass 0.7 + screen module 2.6 (*verify* panel) | 3.3 | 15.7–19.0 |
| | Gasket / air | 0.3 | 15.4–15.7 |
| | Aluminium mid-frame | 1.2 | 14.2–15.4 |
| | Thermal pad (CM4 to frame) | 1.0 | 13.2–14.2 |
| | CM4 (top components 2.0 + board 1.2), components facing the frame | 3.2 | 10.0–13.2 |
| | Hirose DF40 board-to-board, 1.5 mm mated height | 1.5 | 8.5–10.0 |
| | Carrier board, 4 layers | 1.6 | 6.9–8.5 |
| | Carrier back components (max 2.5; **exception:** the CR2032 holder, about 4–5 mm, uses the air gap below it: keep the antenna flex and back-cover ribs clear of a 24 × 20 mm area at device X −31 … −11, Y 100 … 124, see `hardware/carrier-board/build-sheet.md`) | 2.5 | 4.4–6.9 |
| | Air + antenna flex | 3.2 | 1.2–4.4 |
| | Carbon back with radio window | 1.2 | 0–1.2 |
| Keyboard half (Y 0–70) | Q20 keyboard + keycaps (keys stand 1.0 proud of the front) | 4.0 | 16.0–20.0 |
| | Keyboard board, 2 layers, front side clear under the keyboard | 1.6 | 14.4–16.0 |
| | Keyboard board back components (max 2.0; inductors in frame cut-outs) | 2.0 | 12.4–14.4 |
| | Aluminium mid-frame | 1.2 | 11.2–12.4 |
| | Battery bay (cell 8.5 + 1.0 swell allowance) | 9.5 | 1.7–11.2 |
| | Back clearance | 0.5 | 1.2–1.7 |
| | Carbon back | 1.2 | 0–1.2 |

## 2. Bought-in parts that set the size (all *verify* against the part in hand)

| Part | Envelope (W × H × T) | Source of the number |
|---|---|---|
| 4-inch 720 × 720 IPS, MIPI DSI | Module 76.0 × 80.6 × 2.6, active area 71.9 × 70.2; FPC leaves the bottom edge | Typical ST7701S 4-inch square panels (*verify*) |
| Raspberry Pi CM4, 4 GB, 32 GB eMMC, Wi-Fi | 55 × 40 × 4.7 (incl. DF40 on the underside) | Raspberry Pi CM4 datasheet |
| BlackBerry Q20 keyboard with trackpad | Keyboard 66 × 36 × 4; nav row (4 keys + trackpad) 66 × 13 | BBQ20KBD design files (*verify*) |
| LiPo cell, 1S, protected | **855570**: 8.5 × 55 × 70, about 4,000–4,500 mAh | Common cell size (*verify*) |
| CR2032 holder for the RTC | 20 dia | on carrier back |

## 3. Board outlines (device frame, XY plane)

| Board | Size | Position (lower-left corner) | Layers | Mounting |
|---|---|---|---|---|
| **Carrier board** (`hardware/carrier-board`) | **74 × 72** | X −37, Y 74 | 4, controlled impedance (90 Ω USB / 100 Ω DSI differential) | 4 × M2 at 3.5 from each corner |
| **Keyboard board** (`hardware/keyboard-board`) | **74 × 60** | X −37, Y 4 (top edge Y 64, clear of the screen module, which starts at Y 64.4) | 2 | 4 × M2 at 3.5 from each corner |

- Carrier board: CM4 centred at X 0, Y 112 on the **front** side (facing the screen), display FPC connector at the top edge,
  inter-board FFC connector at the bottom edge centre, CR2032 + RTC on the back, U.FL lead from the CM4 to the flex antenna at the top.
- Keyboard board: Q20 keyboard and nav row on the **front**, everything else on the **back**; USB-C receptacle (mid-mount) at the
  bottom edge centre (Y 4, port opening at Y 0); power button on the right side edge at Y 50; battery JST-SH 2-pin on the back.

## 4. Inter-board cable: keyboard board ↔ carrier board

24-way, 0.5 mm pitch FFC, same-side contacts, about 20 mm long. Connector both ends: 24-pin 0.5 mm bottom-contact FPC
(for example Hirose FH12-24S-0.5SH or the JLCPCB-stocked equivalent).

| Pin | Net | Direction (from keyboard board) | Notes |
|---|---|---|---|
| 1 | GND | | |
| 2–7 | +5V_CM4 | out | 5.1 V from the boost, up to 3 A; 6 contacts at 0.5 A each |
| 8–11 | GND | | |
| 12 | USB_CM4_D_P | bidirectional | CM4 USB 2.0, 90 Ω differential |
| 13 | USB_CM4_D_N | bidirectional | |
| 14 | GND | | |
| 15 | CM4_nRPIBOOT | out, open drain | low at CM4 power-up = boot from USB (eMMC flashing) |
| 16 | CM4_GLOBAL_EN | out, open drain | low = CM4 held off. Pulled up to **+5V** by 100 k inside the CM4: drive with a 5 V-tolerant open-drain part (N-MOSFET), not an RP2040 pin directly |
| 17 | CM4_RUN_PG | in | high = CM4 running (CM4's own power-good). Read only: driving it low resets the CM4 |
| 18 | CM4_3V3_SENSE | in | CM4's 3.3 V output through 1 k; high = CM4 powered |
| 19 | CM4_POWEROFF | in | CM4 GPIO26 (gpio-poweroff): high = Linux has halted, safe to cut power. 1 k in series on the carrier |
| 20 | CM4_SHUTDOWN_REQ | out, open drain | CM4 GPIO17 (gpio-shutdown): pulse low = shut down cleanly (backup to the HID power key). 1 k in series and 10 k pull-up to the CM4's 3.3 V on the carrier |
| 21 | UART_CM4_TX | in | CM4 GPIO14 (UART0 TX, serial console). 1 k in series on the carrier |
| 22 | UART_CM4_RX | out | CM4 GPIO15 (UART0 RX). 1 k in series on the carrier; keep it released (input) while the CM4 is off |
| 23 | GND | | |
| 24 | GND | | |

## 5. CM4 pins used (carrier board and Linux image)

| CM4 signal | Use | Linux setting (`/boot/firmware/config.txt`) |
|---|---|---|
| USB 2.0 (USB_P / USB_N, pins 105 / 103) | Keyboard board (RP2040, through the USB switch) | `dtoverlay=dwc2,dr_mode=host` (the CM4 datasheet section 2.4 names `otg_mode=1` on current Raspberry Pi OS: try both at bring-up). USB_OTG_ID (pin 101) floats (internal pull-up) with a solder jumper to ground on the carrier, to fix host mode by hardware if needed |
| DSI1, 4 lanes + clock | Display, Raspberry Pi standard 22-pin 0.5 mm FPC (as the CM4 IO board's DISP1) | panel overlay, *verify* for the chosen panel |
| SDA0 / SCL0 = BCM2711 GPIO 44 / 45 (pins 82 / 80, I2C `i2c_csi_dsi`, 1.8 k pull-ups inside the CM4) | RTC PCF85063A (address 0x51); display connector pins 21 / 20 | `dtoverlay=i2c-rtc,pcf85063a,i2c_csi_dsi` (as on the CM4 IO board; pin mapping checked in the CM4 datasheet section 2.9, overlay parameter *verify* at bring-up) |
| GPIO 14 / 15 | UART0 serial console: test pads + inter-board cable | `enable_uart=1` |
| GPIO 17 | CM4_SHUTDOWN_REQ (input, pull-up) | `dtoverlay=gpio-shutdown,gpio_pin=17,active_low=1,gpio_pull=up` |
| GPIO 26 | CM4_POWEROFF (output) | `dtoverlay=gpio-poweroff,gpiopin=26,active_low=0` |
| GPIO 18 | Display backlight PWM: display connector pin 18 through a 0 Ω link | `dtoverlay=pwm,pin=18,func=2` |
| GPIO 27 | Display enable / reset: display connector pin 17 through a 0 Ω link (pins 17 and 18 are unconnected on the CM4 IO board's DISP1; remove the links for a panel that needs them open) | panel overlay |
| GLOBAL_EN, RUN_PG, nRPIBOOT | Inter-board cable (section 4) | |
| Antenna | External U.FL, flex antenna behind the radio window | `dtparam=ant2` |
| nEXTRST, Ethernet, PCIe, HDMI, CAM, DSI0 | not used in v1 (left unconnected per the CM4 datasheet; every pin listed in `hardware/carrier-board/electronics/pin-map.md`) | |
| EEPROM_nWP (pin 20) | floats (EEPROM writable, so bootloader updates work); solder jumper to ground on the carrier to write-protect a finished unit | |

## 6. Keyboard board power architecture

```
USB-C (sink, 5.1 k CC pull-downs) → BQ25895 charger with power path → VSYS (3.5–4.4 V) ─┬→ TPS61088 boost → +5V_CM4 (5.1 V, 3 A) → cable
                                         ↕ BAT                                         ├→ 3.3 V LDO (always on) → RP2040, MAX17048, keyboard
                                     1S LiPo 855570 ← MAX17048 gauge                    └→ keyboard backlight driver
```

- The BQ25895 cannot charge and boost to 5 V at the same time (its boost drives VBUS), so the 5 V for the CM4 comes from a
  **separate boost converter fed from VSYS**. That is what lets the device run while it charges. See decision record 0004.
- The RP2040 is always powered (from VSYS through a low-quiescent LDO) and owns power: it enables the boost and releases
  `CM4_GLOBAL_EN` to turn the CM4 on, and turns it off after Linux has halted.
- **USB switch** (TS3USB221 or similar): the CM4's USB normally goes to the RP2040; in **service mode** (hold `Fn` + `Back`
  while pressing power) it goes to the USB-C port and the RP2040 pulls `CM4_nRPIBOOT` low, so a computer can flash the eMMC
  with `rpiboot`, or Linux can run as a USB gadget. See decision record 0006.
- I2C on the keyboard board (RP2040 master): BQ25895, MAX17048, trackpad.

## 7. USB interface: keyboard board → Linux

Composite USB device, **VID 0x1209 / PID 0x0001 placeholder** (pid.codes test ID: apply for a free open-hardware PID at
pid.codes before anything ships). Manufacturer `Terminal 1 project`, product `Terminal 1 Keyboard`.

| Interface | Class | What |
|---|---|---|
| 0 | HID keyboard (boot protocol) | keys after the terminal key map (`firmware/keyboard-board/README.md`) |
| 1 | HID mouse | trackpad in mouse mode |
| 2 | HID consumer + system control | `System Power Down` (power-button long press), volume-less media keys |
| 3–4 | CDC ACM serial "status" | line protocol below; Linux sees `/dev/serial/by-id/usb-Terminal_1_project_Terminal_1_Keyboard_*-if03` |

Status line protocol (ASCII, `\n` terminated, 115200 nominal):

| From keyboard board | Meaning |
|---|---|
| `BAT <percent> <millivolts> <state>` | every 10 s and on change; state = `charging`, `discharging`, `full`, `no-battery` |
| `PWR <event>` | `button-short`, `button-long`, `low-battery`, `critical-battery` (Linux should shut down) |
| `VER <firmware version> <board revision>` | reply to `VER` |
| `OK` / `ERR <text>` | reply to a command |

| From Linux | Meaning |
|---|---|
| `VER` | ask for the version |
| `BL <0-100>` | keyboard backlight percent |
| `MODE arrows` / `MODE mouse` | trackpad mode |
| `PING` | reply `OK` |

## 8. RP2040 pin map (keyboard board; the bench build on a Raspberry Pi Pico uses the same GPIO numbers)

Owned by `hardware/keyboard-board/electronics/generate_schematic.py`; `firmware/keyboard-board/src/board.h` must match.
The keyboard matrix size and FPC pinout come from the BBQ20KBD design and are recorded in
`hardware/keyboard-board/electronics/pin-map.md`.

## Used by

`hardware/enclosure/` (Onshape FeatureScript, build sheet) · `hardware/carrier-board/electronics/` ·
`hardware/keyboard-board/electronics/` · `firmware/keyboard-board/` · `linux/` · `website/` (specifications section)

## Changelog

- 0.1 (2026-11-16): first draft from the prototype plan.
- 0.2 (2026-11-16): carrier board Rev A (`hardware/carrier-board`): SDA0/SCL0 confirmed as GPIO 44/45 (CM4 datasheet 2.9); GPIO 27 added as display enable on DSI pin 17, GPIO 18 to DSI pin 18; USB_OTG_ID and EEPROM_nWP handling added; carrier-side series resistors and the GLOBAL_EN 5 V pull-up noted on the cable table; CR2032 holder height exception in the stack-up. Open: the panel FPC leaves the module's bottom edge but the carrier's display connector is at its top edge (section 3): rotate the panel 180° or re-plan, see the carrier build sheet.
- 0.2 (2026-11-16): keyboard board 74 × 66 → **74 × 60** (Y 4–64): the taller board overlapped the screen module in the CAD layout. Screen module Y 64.4–145.0, cover glass Y 63–148.
