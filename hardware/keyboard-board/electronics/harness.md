# Keyboard board: wiring harness (Rev A)

Written by hand from `generate_schematic.py` (pinouts: `pin-map.md`, generated). Lengths are estimates from the enclosure
layout; confirm them on the first printed shell.

| Wire / cable | From | To | Type | Length | Connector | Notes |
|---|---|---|---|---|---|---|
| W1 inter-board cable | J4 (keyboard board, back, top edge centre) | Carrier board inter-board connector (bottom edge centre) | 24-way FFC, 0.5 mm pitch, **same-side contacts** (type A) | about 20 mm (*verify*) | Hirose FH12-24S-0.5SH both ends | Pinout: `system/plan/interfaces.md` section 4. +5V_CM4 on pins 2–7 (6 × 0.5 A) |
| W2 cell positive | J2 pad 1 `VBAT` | Cell + (red) | 0.5 mm² (20 AWG) silicone wire | about 40 mm | soldered from the back | Insulate the pad after soldering; the cell sits behind the mid-frame |
| W3 cell thermistor | J2 pad 2 `CHARGER_TS` | Cell NTC lead (10 k 103AT type) | 0.1 mm² wire | about 40 mm | soldered | Cell without NTC: leave open and bridge JP1 (bench only) |
| W4 cell negative | J2 pad 3 `GND` | Cell − (black) | 0.5 mm² (20 AWG) silicone wire | about 40 mm | soldered | |
| Keyboard flex | J3 (front, Hirose BM20B(0.8)-40DS-0.4V) | BlackBerry Q20 keyboard + trackpad flex | the keyboard's own flex and board-to-board plug | – | – | Pinout from the BBQ20KBD (`pin-map.md`) |

Not cabled: USB-C (J1), power button (SW2) and BOOTSEL (SW1) are on the board.

Trim the battery wire ends flush on the front: the front of the board is under the keyboard.
