# Terminal 1 enclosure: build sheet

**Mechanical design 1 (draft)** · 2026-11-16 · Model: [`terminal-1.fs`](terminal-1.fs) (Onshape Feature Studio "Terminal 1 FS")
· Numbers from [`system/plan/interfaces.md`](../../system/plan/interfaces.md) v0.2. Nothing here has been fabricated or test-fitted.

## Inputs (parts that set the size; all *verify* against parts in hand)

| Part | Envelope used (mm) | Status |
|---|---|---|
| 4-inch 720 × 720 IPS DSI panel | 76.0 × 80.6 × 2.6 | Typical; exact panel not chosen (record 0003) |
| Raspberry Pi CM4 | 55 × 40 × 3.2 (+1.5 connector stack) | Datasheet outline; connector positions approximate |
| BlackBerry Q20 keyboard | 66 × 36 × 4.0 (keys 1.0 proud of the front) + nav row 66 × 13 | Estimated; measure a real keyboard |
| LiPo cell 855570 | 8.5 × 55 × 70 | Common size; 1.0 mm swell allowance in the bay |

## Coordinates

Millimetres. Origin at the centre of the **bottom (USB-C) edge on the back face**. X across the width, Y up the device, Z through
the thickness (+Z towards the screen and keys). Overall **84 × 150 × 19**, plan corners R9, front/back edge round R1.2.

## Parts

| # | Part | Material | Position / size (mm) | Qty | Mass (g, est.) | Made by |
|---|---|---|---|---|---|---|
| 1 | Mid-frame: 2 mm side band, plate behind the screen (Z 14.2–15.4, Y 70–148), plate over the battery (Z 11.2–12.4, Y 2–70), step at Y 69–70; slots for the inter-board cable, USB-C and power button | Aluminium 6061, black anodised | 84 × 150 × 19 | 1 | 83 | Phase 3a: printed PETG/ASA; 3b: machined |
| 2 | Carbon back | Carbon fibre / epoxy, 1.2 thick | Inside the band, Z 0–1.2, Y 2–134 | 1 | 20 | In-house, printed mould |
| 3 | Radio window | Fibreglass / epoxy (or printed) | Y 134–148, Z 0–1.2 | 1 | 2 | In-house |
| 4 | Cover glass | Glass 0.7 (black print border) | Y 63–148, Z 18.3–19.0 | 1 | 12 | Bought, cut to size |
| 5 | Display module | | Y 64.4–145, Z 15.7–18.3 | 1 | 32 | Bought |
| 6 | Keyboard deck (front plate, keyboard and nav openings) | Aluminium (printed in 3a) | Y 2–63, Z 17.4–19.0 | 1 | 7 | With the mid-frame |
| 7 | Q20 keyboard | Bought | Y 8–44, Z 16.0–20.0 | 1 | 14 | Bought |
| 8 | Keyboard frets (model only, part of 7) | Steel | 3 bars | – | 1 | |
| 9 | Navigation keys (Ctrl, Esc, Tab, Fn) | Part of the Q20 set (*verify*) | Y 47–60 | 1 | 4 | Bought |
| 10 | Trackpad | Part of the Q20 set | 10 × 8, centre X 0, Y 53.5 | 1 | 1 | Bought |
| 11 | Keyboard board | FR-4, 2 layers | 74 × 60, Y 4–64, Z 14.4–16.0, 4 × M2 holes | 1 | 15 | JLCPCB |
| 12 | USB-C socket (mid-mount) | | Y 0.8–7.8, Z 13.6–16.8, in a board slot | 1 | 2 | On 11 |
| 13 | Carrier board | FR-4, 4 layers | 74 × 72, Y 74–146, Z 6.9–8.5, 4 × M2 holes | 1 | 18 | JLCPCB / PCBWay |
| 14 | CM4 | Bought | Centre X 0, Y 112, Z 10.0–13.2 | 1 | 11 | Bought |
| 15 | CM4 connectors (Hirose DF40, 1.5 mm stack) | | Approximate positions | 2 | 0 | On 13 |
| 16 | Thermal pad | Silicone, 1.0 | 24 × 24 over the CM4's SoC, to plate (1) | 1 | 2 | Bought |
| 17 | Battery 855570 | LiPo, protected | 70 × 55, Z 2.2–10.7 | 1 | 69 | Bought |
| 18 | Power button | Aluminium | Right side, Y 46.5–53.5 | 1 | 0 | With the mid-frame |
| | **Total** | | | | **≈ 292** (Onshape: 290.9) | |

Masses from volume × density (densities of the screen, CM4, keyboard and cell are estimates). Not modelled yet: screws and
heat-set inserts, gasket, inter-board FFC, flex antenna, coin cell, FPC tails, labels. Allow about +10 g.

## Checks done

- Real regeneration in Onshape (2026-11-16): all parts build; assembled and exploded (12 mm) views checked.
- Interference check (`terminal-1-check.fs`): one clash found (USB-C socket into the keyboard base by 0.5 mm) and fixed by
  shortening the socket to end at Y 7.8. The check has not been re-run since; expected 0.

## Open items

1. Measure a real Q20 keyboard and nav row; adjust the keyboard and deck openings.
2. Choose the panel; adjust the screen envelope and the FPC route to the carrier's top-edge connector.
3. Place the CM4 connectors at their true positions once the carrier board layout fixes them.
4. Fixings: M2 screws into heat-set inserts (printed shell) or tapped bosses (aluminium); not modelled.
5. Antenna position behind the radio window; FFC route through the plate slot (28 × 4 at Y 64.5–68.5).
6. Split the mid-frame for phase 3a printing (front and back halves) once the boards are fixed.
7. Thermal check: plate-to-CM4 pad pressure and outside temperature after an hour (Phase 3 gate).
