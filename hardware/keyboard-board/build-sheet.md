# Keyboard and power board: build sheet (Rev A)

**Status (2026-11-17):** schematic generated, KiCad ERC **0 errors, 0 warnings**. Layout generated and autorouted; DRC result
in "Checks" below. **Not built, not tested. Not ready to order** (see "Before ordering").

## What it is

The 2-layer board behind the BlackBerry Q20 keyboard. An RP2040 scans the keyboard and trackpad, presents them to Linux as a
composite USB device (keyboard, mouse, power key, status serial port), and owns the device's power: USB-C charging (BQ25895
with power path), the 5.08 V boost for the CM4 (TPS61089), the always-on 3.3 V rail, the fuel gauge (MAX17048) and the USB
switch for service mode (TS3USB221). Decisions: `docs/decisions/0004`, `0005`, `0006`.

## Inputs

| Input | Where |
|---|---|
| Board outline, position, stack-up height, cable pinout, power architecture, USB protocol | `system/plan/interfaces.md` v0.3, sections 1, 3, 4, 6, 7, 8 |
| Keyboard connector pinout, trackpad circuit, matrix GPIOs | Solder Party BBQ20KBD (`github.com/solderparty/bbq20kbd_hw`, CERN-OHL-1.2) and its firmware i2c_puppet (MIT): nets read from its KiCad files 2026-11-16 |
| Keyboard and nav-row position | `hardware/enclosure/build-sheet.md` (keyboard Y 8–44, nav row Y 47–60) |
| Charger, boost, switch | TI datasheets SLUSC88C (BQ25895), SLVSD38C (TPS61089), SCDS220M (TS3USB221) |
| RP2040 core circuit | Raspberry Pi Pico / "Hardware design with RP2040" (from memory: crystal, flash, decoupling as the Pico) |

## Files (all generated; edit the scripts)

| File | Made by |
|---|---|
| `electronics/keyboard-board.kicad_sch`, `.kicad_pro`, `terminal-1.kicad_sym`, `netlist.md`, `pin-map.md`, `preview/keyboard-board.svg`, `keyboard-board.pdf` | `electronics/generate_schematic.py --erc` (plain Python 3 + KiCad 10 for ERC/PDF) |
| `electronics/terminal-1.pretty/Hirose_BM20B-0.8-40DS-0.4V.kicad_mod` | `electronics/keyboard_connector_footprint.py` (called by the schematic script) |
| `electronics/keyboard-board.kicad_pcb`, `-drc.rpt`, `renders/`, `fabrication/` | `electronics/generate_pcb.py --all` (KiCad's Python; Freerouting 2.0.1 via `tools/fetch_tools.sh`) |
| `electronics/fabrication/keyboard-board-jlc-bom.csv`, `-jlc-cpl.csv` | `generate_pcb.py --all` (through `tools/build_jlc_files.py`, pointed at this board) |
| `electronics/parts.py` | by hand: LCSC numbers and footprints |
| `electronics/circuit-notes.md`, `harness.md` | by hand |

## Outline and placement

74 × 60 mm, 2 layers, 1.6 mm FR-4, 1 oz. Device frame position: lower-left corner at X −37, Y 4 (top edge Y 64). 4 × M2
(2.2 mm) holes 3.5 mm in from each corner. Board coordinates below: mm from the top-left corner seen from the front.

| Part | Side | Board position | Device frame | Note |
|---|---|---|---|---|
| J3 Q20 keyboard connector (BM20B, 0.8 mm mated) | **front** | (12.0, 19.3), turned 90° | X −25, Y 44.7 | The only front part. Position copied from the BBQ20KBD relative to the nav row: **CHECK with a keyboard** |
| Two slots beside J3 | through | (5.8–17.0, 4.6–8.6) and (5.5–9.2, 11.8–26.5) | | Copied from the BBQ20KBD (purpose assumed: keyboard locating features). **CHECK** |
| J4 FFC to the carrier (FH12-24S, 2.0 mm tall) | back | (37.0, 5.0), cable enters from the top edge | X 0, Y 56–64 | |
| J1 USB-C (top mount, **3.2 mm tall**) | back | (37.0, 56.4), mouth at the bottom edge | X 0, Y 3.4–12.9 | **Mid-frame cut-out needed** |
| L2 boost inductor (**3.0 mm tall**) | back | (65.0, 46.0) | X 24.4–31.6, Y 13.5–22.5 | **Mid-frame cut-out needed** |
| SW2 power button (side push) | back | (72.2, 14.0), plunger out of the right edge | X 35, Y 50 | Height and plunger reach **CHECK** against the Alps drawing and the enclosure's button |
| J2 battery wire pads | back (through-hole) | x 3.4, y 28.4–37.6 | X −33.6, Y 26.4–35.6 | Trim wire ends flush on the front |
| RP2040, charger, boost, LDOs, switch, everything else | back | see `generate_pcb.py` | | All ≤ 2.0 mm except the three marked |

Back-side heights over the 2.0 mm budget (interfaces.md stack-up): USB-C 3.2 mm, boost inductor 3.0 mm, power button (about
3.5 mm, CHECK). Everything else: QFN/SON/SOT-23 ≤ 1.1 mm, 1206 22 µF ≤ 1.8 mm (CHECK the chosen capacitor), FXL0420 2.0 mm,
FH12 2.0 mm, crystal 0.8 mm, BOOTSEL button TS-1187A about 1.5 mm (CHECK).

## Parts

The full list with descriptions is in `electronics/netlist.md`; LCSC numbers and footprints in `electronics/parts.py`.
How sure each LCSC number is:

| Part | LCSC | Source |
|---|---|---|
| RP2040 | C2040 | memory |
| W25Q128JVPIQ | C190862 | search |
| X322512MSB4SI | C9002 | search |
| BQ25895RTWR | C80200 | search |
| TPS61089RNRR | C165129 | search |
| MAX17048G+T10 | C2682616 | search |
| ME6211C28M5G-N | C53099 | search |
| ME6211C18M5G-N | C236671 | search |
| FXL0420-1R0-M | C167203 | search |
| FXL0630-2R2-M | C167218 | search |
| TS3USB221DRCR | C324071 | search |
| BM20B(0.8)-40DS-0.4V(51) | C424543 | search |
| FH12-24S-0.5SH(55) | C202112 | search |
| SKRTLAE010 | C110293 | search |
| BSS138 | C78284 | search |
| 2N7002 | C8545 | memory |
| AO3400A | C20917 | memory |
| resistor 10k | C25804 | reference |
| resistor 100k | C25803 | reference |
| resistor 4k7 | C23162 | reference |
| resistor 1k | C21190 | reference |
| resistor 5k1 | C23186 | reference |
| resistor 100R | C22775 | reference |
| resistor 27R | CHECK | CHECK |
| resistor 120R | CHECK | CHECK |
| resistor 30k | CHECK | CHECK |
| resistor 47k | CHECK | CHECK |
| resistor 150k | CHECK | CHECK |
| resistor 127k | CHECK | CHECK |
| resistor 301k | CHECK | CHECK |
| resistor 6k8 | CHECK | CHECK |
| capacitor 100nF | C14663 | reference |
| capacitor 1uF | C15849 | reference |
| capacitor 10uF 25V | C15850 | reference |
| capacitor 22uF 25V | C12891 | reference |
| capacitor 1nF | C1588 | reference |
| capacitor 4.7uF 10V | CHECK | CHECK |
| capacitor 2.2uF | CHECK | CHECK |
| capacitor 47nF | CHECK | CHECK |
| capacitor 4.7nF | CHECK | CHECK |
| capacitor 33pF | CHECK | CHECK |

"search": found in a web search on 2026-11-16, stock not checked. "memory": recalled, not looked up. "reference": used on the
reference project's boards. "CHECK": not looked up; JLCPCB will match by value and footprint at upload.

## Checks

CHECKS_TABLE

## Before ordering (open items)

1. **DRC must be clean** (see Checks) and a person must review the routing of the charger and boost power loops: the
   autorouter does not know about switching loops. Short, wide `CHARGER_SW`, `BOOST_SW`, VSYS and PGND connections matter
   more than anything else on this board. Hand-route or at least hand-check them.
2. Confirm every LCSC number, stock and Basic/Extended status; fill in the CHECK lines (`parts.py`).
3. Verify footprints against the makers' drawings: BM20B (project footprint), MAX17048 TDFN exposed pad, TS3USB221 VSON
   exposed pad, SKRTLAE010 orientation.
4. Pinouts from memory: **MAX17048** (1 CTG, 2 CELL, 3 VDD, 4 GND, 5 ALRT, 6 QSTRT, 7 SCL, 8 SDA). Verified from datasheets
   or KiCad's library: BQ25895, TPS61089, TS3USB221, W25Q128JVP, ME6211, USBLC6, RP2040 (KiCad + BBQ20KBD netlist).
5. Keyboard: the connector position and slots (copied from the BBQ20KBD), the nav-key identities (Call / BlackBerry / Back /
   End), and the backlight current: measure with a real Q20 keyboard and the Phase 0 bench build.
6. Cell: must allow about 6.5 A discharge (circuit-notes.md section 2); a ≤ 2.0 mm battery connector rated for it would
   replace the solder pads.
7. Mid-frame cut-outs for USB-C, boost inductor and power button (enclosure).
8. Boost compensation and thermal behaviour at 3 A: bench test (circuit-notes.md section 1).
9. Off-state drain with the CM4 fitted (no boost output disconnect).
10. USB-C mid-mount socket (interfaces.md asks for one; Rev A uses a top-mount socket).
