# CM4 carrier board: circuit notes (Rev A)

Hand-written by the design session that wrote `generate_schematic.py`; the impedance table is the output of
`estimate_impedance.py`. Every number here is an **estimate** unless it says "datasheet". Bench tests that confirm them are listed
at the end.

## 1. Power budget

All power arrives as **+5V_CM4** (5.1 V from the keyboard board's boost converter) on FFC pins 2-7 (6 contacts, about 0.5 A each,
so about 3 A for the cable; interfaces.md section 4).

| Load | Rail | Typical | Peak | Source of the number |
|---|---|---|---|---|
| CM4 4 GB, idle | 5 V | 400 mA | | CM4 datasheet table 5 |
| CM4, working (compile, browser) | 5 V | 1400 mA | about 2000 mA (all cores, Wi-Fi transmitting) | datasheet table 5; peak is our estimate |
| Display logic (ST7701S-class panel) | CM4 3.3 V | 30-80 mA | | estimate, panel not chosen |
| Display backlight, if run from the 22-way connector's 3.3 V (boost on the panel adapter) | CM4 3.3 V | 100-200 mA | 250 mA | estimate: 4-inch panel backlight about 0.4-0.6 W at full brightness |
| Status LEDs (2 x 1.3 mA), pull-ups, 3V3_SENSE | CM4 3.3 V | 5 mA | | (3.3 V - 2.0 V) / 1 k per LED |
| RTC | 3.3 V or cell | < 1 uA | | PCF85063A datasheet: about 0.25 uA |

- **5 V total**: about 0.6 A idle, 1.7 A working, 2.5 A peak. Inside the 3 A the cable carries and the keyboard board's boost
  (TPS61088, 3 A at 5.1 V per interfaces.md section 6); check the boost's real current limit at low battery voltage (3.4 V),
  where its input current is about 4 A.
- **CM4 3.3 V output**: datasheet limit 600 mA total (300 mA per pin, pins 84 and 86). Our estimate is up to about 330 mA with the
  backlight on that rail, so there is margin, but **if the chosen panel's backlight needs more than about 300 mA, feed it from
  +5V_CM4 instead** (that needs a different display connector or a spare FFC contact; open item in `build-sheet.md`).
- The CM4 has its own input capacitors; the carrier adds 2 x 22 uF + 100 nF at the +5V pins and 10 uF at the FFC (the IO board
  fits 100 nF at the CM4 plus the bulk of its own regulators). The In2 plane is +5V_CM4, so the 5 V path from the FFC to the
  CM4 is a plane, not a track.
- Supply voltage at the CM4 must stay within **4.75-5.25 V** (datasheet). With 5.1 V at the boost, the drop across the cable,
  connectors and planes must stay below 0.35 V at 2.5 A, i.e. below 0.14 ohm in total. The 20 mm FFC with six 0.3 mm contacts
  in parallel is estimated at under 0.03 ohm; connector contact resistance is about 0.05 ohm per contact (Hirose FH12 datasheet
  figure, max) or under 0.01 ohm for six in parallel. **Measure it** (test 2 below).

## 2. Real-time clock backup

Circuit as the CM4 IO board: PCF85063AT, 32.768 kHz crystal, BAT54C common-cathode Schottky pair (one anode on the CR2032,
the other on the CM4's 3.3 V), 100 nF at the clock's VDD. While the CM4 runs, the clock runs from 3.3 V and the cell supplies
nothing; while it is off, the cell supplies the clock through one diode (about 0.2-0.3 V drop at microamps, so the clock sees
about 2.7-2.9 V; the PCF85063A keeps time down to 0.9 V, datasheet).

Drain on the cell while the CM4 is off (estimates at 25 C):

| Item | Current |
|---|---|
| PCF85063A timekeeping, CLKOUT off | about 0.25 uA (datasheet typical) |
| CLKOUT running at 32 kHz into an open pin (on by default after the cell is first fitted; Linux's driver turns unused clocks off) | up to about 1 uA more |
| Reverse leakage of the BAT54C diode towards the unpowered 3.3 V rail | about 0.1-0.5 uA (rises steeply with temperature) |
| **Total** | **about 0.5-2 uA** |

A CR2032 holds about 220 mAh: 220 mAh / 2 uA is about 12 years; at 0.5 uA it is decades. **The cell's own shelf life (about
8-10 years) sets the backup life, not the circuit.** The device is also powered for much of its life, when the cell is not used.

## 3. Controlled impedance (estimate)

Pairs run on F.Cu (the CM4 side) over the solid In1 ground plane: edge-coupled microstrip. JLCPCB stack-up **JLC04161H-7628**:
outer copper 35 um, 7628 prepreg 0.2104 mm to In1, relative permittivity 4.4. The IO board (a thinner 0.09 mm prepreg)
uses 0.127 / 0.253 mm for 100 ohm and 0.147 / 0.253 mm for 90 ohm; on our thicker prepreg the tracks must be wider.

| Pair | Width (mm) | Gap (mm) | Single-ended Z0, bare (ohm) | Zdiff bare (ohm) | Zdiff with mask, est. (ohm) |
|---|---|---|---|---|---|
| DSI1 (target 100 ohm) | 0.20 | 0.18 | 67.3 | 106.2 | 102.5 |
| USB 2.0 (target 90 ohm) | 0.25 | 0.18 | 60.6 | 95.5 | 92.2 |

Sensitivity (bare, gap 0.18 mm): W 0.18 -> 111, W 0.20 -> 106, W 0.22 -> 102, W 0.25 -> 96, W 0.28 -> 90.

- Formulas: IPC-2141 microstrip with the usual edge-coupling correction, about +/-10 %. **This is an estimate to check with
  JLCPCB's impedance calculator** (stack-up JLC04161H-7628, "coplanar/differential on L1 referenced to L2") before ordering;
  then put the calculator's widths into the net classes in `generate_pcb.py` (`CLASSES`) and re-run it.
- The values set in the project (`carrier-board.kicad_pro` net classes DSI100 and USB90) are the table's widths and gaps.
- Inside the 0.4 mm pitch DF40 pad fields and the 0.5 mm FPC pads the pairs must neck down (0.1-0.127 mm) for a short length;
  a project rule allows this. Keep each neck-down under about 2 mm.
- Matching: within each pair to 0.15 mm (CM4 datasheet 2.4 and 2.8). Lane-to-lane matching for DSI is not required by the
  datasheet; keep lanes within about 1 mm of the clock pair as good practice.
- Keep pairs at least 3 x the gap (0.5 mm) from other copper, no pairs over plane splits (In1 is unbroken except the antenna
  keep-out, which no pair crosses), and a ground via within about 1 mm of every pair via.

## 4. Protection and signal choices

- **USB**: USBLC6-2SC6 at the FFC (the pair leaves the board on a cable). The keyboard board has its own protection at the USB-C
  port. Capacitance about 3.5 pF per line (ST datasheet typical), acceptable at 480 Mbit/s.
- **DSI**: no ESD parts, as on the CM4 IO board: the display cable stays inside the case, and diodes on 1 Gbit/s lanes cost signal
  quality. Handle the panel with ESD care during assembly.
- **Cable signals between power domains** (POWEROFF, SHUTDOWN_REQ, UART TX/RX): 1 k series resistors, because the keyboard
  board's RP2040 is always powered and the CM4 is not. They limit back-feeding through pin protection diodes to under 3 mA. The
  keyboard board firmware should still keep its UART TX and SHUTDOWN_REQ released (input) while the CM4 is off.
- **GLOBAL_EN** is pulled up to +5V by 100 k **inside the CM4** (datasheet pin 99). The keyboard board must pull it low with an
  open-drain part that tolerates 5 V (an N-MOSFET, not an RP2040 pin directly). Noted in interfaces.md section 4.
- **RUN_PG**: datasheet: driving it low resets the CM4. The keyboard board must only read it.
- **I2C (SDA0/SCL0)**: 1.8 k pull-ups to 3.3 V inside the CM4; no pull-ups on the carrier. The display adapter must not add strong
  pull-ups to another voltage.

## 5. Bench tests that confirm these numbers

1. Current from +5V_CM4 (TP7) idle and under `stress-ng --cpu 4` with Wi-Fi transfer: expect about 0.4 A and 1.4-2 A.
2. Voltage at TP7 under that load: must stay above 4.85 V (leaves margin to the CM4's 4.75 V minimum).
3. CM4 3.3 V (TP8) with the display at full brightness: above 3.2 V.
4. RTC (TP9): about 3.3 V with the CM4 on, about 2.8-3.0 V on the cell. Set the clock, power off for 24 h, check drift
   (expect a few seconds at most) and that `hwclock -r` works.
5. Current from the cell with the CM4 off: measure in series with the holder; expect under 2 uA.
6. USB enumerates at high speed (`lsusb -t` shows 480M) with the keyboard board; DSI panel runs at its full mode without errors.
