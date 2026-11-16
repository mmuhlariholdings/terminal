# Keyboard board: circuit notes and hand calculations (Rev A)

Written by hand alongside `generate_schematic.py`. **Every number here is a hand estimate** from datasheet equations and
assumed efficiencies, not a measurement or a simulation. Each section ends with how the bench must check it.

## Power path in one paragraph

USB-C (5.1 k on CC1 and CC2: a sink, so a Type-C charger gives 5 V only) feeds the **BQ25895** charger (I2C 0x6A). Its power
path keeps **VSYS** at or above SYSMIN (3.5 V by default) from USB, and connects the cell to VSYS through its 11 mΩ BATFET
when there is no USB. VSYS feeds the **TPS61089** boost (5.08 V for the CM4, enabled by the RP2040), the always-on
**ME6211 3.3 V LDO** (RP2040, gauge, USB switch, keyboard backlight, trackpad LDOs) and nothing else. The **MAX17048**
gauge sits straight on the cell.

## Part changes against the plan and interfaces.md (also in the changelog of `system/plan/interfaces.md`)

- **TPS61089 instead of TPS61088.** TI's TPS61088 datasheet link returned "not found" on 2026-11-16, so its pinout could not be
  verified; the TPS61089 (same family, 7 A continuous switch current, peak limit settable to 10 A, VQFN-11 2 × 2.5 mm) has a
  datasheet (SLVSD38C), a KiCad symbol and footprint, and an LCSC listing (C165129). All numbers below use the TPS61089.
- **Battery on three wire pads (BAT+, NTC, BAT−) instead of a 2-pin JST-SH.** JST-SH contacts are rated about 1 A; the boost
  draws up to about 6 A from the cell at full load and low charge. The cell's thermistor needs a third wire for the BQ25895's
  TS input. A connector rated for 6 A that fits under 2.0 mm is an open item.
- **USB-C is top-mount** (HRO TYPE-C-31-M-12, 3.2 mm tall) on the back, not mid-mount: KiCad has no mid-mount footprint we
  could verify. It needs a cut-out in the mid-frame (the enclosure model assumed a mid-mount socket in a board slot).
- **Keyboard backlight runs from +3V3** (LED anodes straight to 3.3 V, N-MOSFET on the cathodes), exactly as the BBQ20KBD,
  not from VSYS as drawn in interfaces.md section 6. The LED current is unknown (the resistors are inside the keyboard flex).

## 1. Boost: TPS61089, VSYS → 5.08 V

| Item | Value | Source |
|---|---|---|
| Output | 1.212 V × (1 + 150 k / 47 k) = **5.08 V** | datasheet VREF 1.212 V (1.188–1.236 V → 4.98–5.18 V) |
| Switching frequency | 500 kHz, R_FSW = 301 k | datasheet table |
| Inductor | 2.2 µH FXL0630-2R2-M, Isat 10 A, heat 9.5 A, DCR 15 mΩ | LCSC datasheet table |
| Peak current limit | 1.03 × 10⁶ / 127 k = **8.1 A typical, 7.3 A minimum**, 8.9 A maximum | datasheet eq. 4 and table |
| Design load | 3 A at 5.08 V (15.2 W): the interfaces.md figure for CM4 + screen peaks | interfaces.md section 4 |

Inductor current (datasheet eq. 6–8, L taken 30 % low = 1.54 µH, efficiency assumed):

| VSYS | Efficiency (assumed) | Average inductor current | Ripple (peak to peak) | **Peak** |
|---|---|---|---|---|
| 3.7 V (cell half full) | 90 % | 4.58 A | 1.55 A | 5.36 A |
| 3.3 V (firmware's critical-battery shutdown) | 88 % | 5.25 A | 1.50 A | **6.00 A** |
| 3.0 V (cell nearly empty, worst case) | 85 % | 5.98 A | 1.60 A | **6.78 A** |

- The minimum current limit (7.3 A) sits above the 6.78 A worst case: about 7 % margin. Little margin: if the CM4 really pulls
  3 A continuously the firmware must shut down at 3.3 V (it does: critical battery).
- Inductor: Isat 10 A > the 8.9 A maximum current limit, so it does not saturate even in a short circuit. Heating 9.5 A > 6 A.
  Copper loss at 5.25 A: 5.25² × 0.015 = **0.41 W** (worst); at a typical 1.2 A input: 0.02 W.
- Converter losses at 3 A out and 3.3 V in: 15.2 W × (1/0.88 − 1) ≈ **2.1 W**, of which about 1.5 W in the IC. In a 2 × 2.5 mm
  package that is a large temperature rise (tens of °C): 3 A is a peak figure, not a continuous one. Typical terminal use is
  about 0.8 A (below). **Bench check:** 3 A electronic load at 3.3 V input for 60 s, measure the IC temperature.
- Output capacitors 4 × 22 µF 25 V 1206: about 35 µF left at 5 V after DC-bias derating (estimate, typical X5R curves).
- Compensation (datasheet eq. 17–18, read from a poorly extracted PDF, so treat as a starting point): crossover at the lower
  of f_SW / 10 = 50 kHz and f_RHPZ / 5; f_RHPZ = R_O (1 − D)² / (2π L) ≈ 40 kHz at 3.3 V / 3 A, so f_C ≈ 8 kHz.
  R_C = 2π V_OUT R_sense f_C C_O / ((1 − D) V_REF G_EA) ≈ 5.4 k → **6.8 k** fitted; C_C = R_O C_O / (2 R_C) ≈ 4.4 nF → **4.7 nF**.
  **Bench check:** load step 0.2 A → 2 A, overshoot under 5 %, no ringing; re-run with TI WEBENCH if it rings.
- **No output disconnect.** A synchronous boost conducts from VSYS to VOUT through the high-side switch's body diode when it is
  disabled, so +5V_CM4 sits at about VSYS − 0.5 V while the device is "off". The CM4 is held off by GLOBAL_EN (pulled low by
  Q7 from RP2040 reset), and its PMIC stays disabled. The leakage (feedback divider about 20 µA, plus the CM4's GLOBAL_EN-low
  current, unknown) counts in the off-state drain below. **Bench check:** measure the cell current with the device off and the
  CM4 fitted. Rev B option: a load switch on +5V_CM4.

## 2. Battery current and the cell

- Cell discharge at the worst case above: about **6 A** through the BQ25895's BATFET (rated to 9 A discharge, datasheet front page)
  and the cell's own protection circuit. Many 4,000 mAh pouch cells trip at 3–5 A. **Open item: the cell must be specified for
  at least 6.5 A continuous discharge**, or the CM4 + screen peak must be measured lower than 3 A.
- Wiring: 0.5 mm² (20 AWG) wires, 3 pads at 4.6 mm pitch (`Connector_Wire:SolderWire-0.5sqmm`), soldered from the back.

## 3. Charger: BQ25895

| Item | Value | Note |
|---|---|---|
| Input current ceiling (ILIM pin) | K_ILIM / R = 355 / 120 Ω = **2.96 A** (320–390 → 2.67–3.25 A) | datasheet K_ILIM; firmware sets IINLIM lower when BC1.2 detection finds a weaker source, and the input-voltage loop (VINDPM) backs off on a sagging supply |
| Charge current | **2.048 A** (register default, set again by firmware) = 0.5 C for 4,000 mAh | check the cell's datasheet: some cells allow only 0.5 C |
| Charge voltage | 4.208 V (register) | |
| Inductor | 1 µH FXL0420-1R0-M (datasheet recommends 1 µH with ≥ 20 µF on SYS) | about 6 A rating (CHECK the rating's definition) |
| Inductor ripple | V_BUS D (1 − D) / (f L) = 5 × 0.74 × 0.26 / (1.5 MHz × 1 µH) = **0.64 A** | |
| Inductor peak | (charge 2.05 A + system about 1.2 A) + 0.32 A ≈ **3.6 A** < 6 A | while the device runs and charges |
| TS divider | 5.1 k / 30 k (datasheet 5.23 k / 30.1 k for 0–45 °C with a 103AT NTC) | with 5.1 k / 30 k: charging stops at about 0 °C and 43 °C (estimate) |
| Charge time (device off) | about 2 h constant current + 0.5–1 h constant voltage ≈ **2.5–3 h** for 4,000 mAh | |

Cells without a thermistor: bridge **JP1** (a 10 k resistor stands in for the NTC at 25 °C). Charging then has no temperature
protection; do this only on the bench.

The power button also pulls the BQ25895's `/QON` low through D1 (B5819W). With no USB plugged in, a 12–18 s hold makes the
charger turn VSYS off and on again: a hardware reset of the RP2040 if its firmware ever hangs. The firmware's own hard cut-off is
at 10 s, so a working RP2040 acts first. `/QON` sits at about 3.5 V through its internal 200 k pull-up and D1 (a few µA flow
into the 3.3 V rail), above the 1.3 V logic-high threshold.

## 4. 3.3 V LDO (ME6211C33), always on

| Load (estimates) | Current |
|---|---|
| RP2040 running USB at 125 MHz | 25 mA |
| Keyboard backlight (unknown: BBQ20KBD drives it the same way) | up to 60 mA (assumed) |
| Trackpad (2.8 V + 1.8 V LDOs) | 5 mA (assumed) |
| MAX17048, TS3USB221, pull-ups | under 1 mA |
| **Total** | **about 90 mA** |

- Dissipation at the highest VSYS (4.4 V while charging): (4.4 − 3.3) × 0.09 = **0.10 W**; SOT-23-5 at about 250 °C/W: +25 °C.
- Dropout about 0.1 V at 100 mA: 3.3 V holds down to VSYS ≈ 3.4 V; below that the rail follows VSYS, which the RP2040
  tolerates (IOVDD 1.62–3.63 V).

## 5. Battery life (estimates; plan target "about 4 hours or more")

| Case | Power at the cell | 4,000 mAh × 3.7 V = 14.8 Wh, 90 % usable |
|---|---|---|
| Terminal work, screen on: CM4 2.5 W + screen 1.0 W + keyboard board 0.3 W, boost 90 % | about **4.2 W** | **3.2 h** |
| Light use, screen dimmed: CM4 1.8 W + screen 0.5 W + 0.2 W | about **2.8 W** | **4.8 h** |
| Off (RP2040 asleep, gauge, LDO, boost leakage, CM4 held off) | about 2–5 mA (estimate; the RP2040's sleep current dominates) | **1–3 months** |

CM4 and screen powers are not measured (no hardware yet). **Bench check:** run `stress-ng`-free terminal work for an hour on a
full cell and log the `BAT` lines from the status interface.

## 6. Signals

- **USB:** RP2040 D+/D− through 27 Ω (as the Raspberry Pi Pico) to switch port 1; USB-C through the USBLC6 to port 2 and to
  the BQ25895's D+/D− (BC1.2 detection: the charger drives the lines only for a moment after plug-in; a short stub). The CM4
  side is the switch's common port, out on FFC pins 12/13. Lengths are short; no impedance control on this 2-layer board.
- **I2C:** one bus at 3.3 V (4.7 k pull-ups) for the charger and gauge, extended to the trackpad's 1.8 V side through BSS138
  shifters (10 k pull-ups to 1.8 V), as the BBQ20KBD does for its trackpad bus.
- **CM4 control lines** are open drain through 2N7002s, so the RP2040 never back-powers an unpowered CM4. Q7's gate is pulled
  **up**, so the CM4 is held off whenever the RP2040 is in reset or unprogrammed. The CM4's status lines come in through 1 k
  with 100 k pull-downs.
- **GPIO budget:** all 30 RP2040 GPIOs are used (pin-map.md). The CM4 console (`UART_CM4_TX/RX`) therefore goes to test pads only.
