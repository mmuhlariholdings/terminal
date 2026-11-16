# Keyboard and power board

The 2-layer board behind the keyboard: RP2040 (keyboard, trackpad, USB device, power manager), BlackBerry Q20 keyboard and
trackpad connector, BQ25895 charger with power path, TPS61089 5.08 V boost for the CM4, MAX17048 gauge, USB-C, a TS3USB221
USB switch for service mode, power button, and the 24-way cable to the carrier board. 74 × 60 mm, Rev A.
Interfaces: [`system/plan/interfaces.md`](../../system/plan/interfaces.md) sections 3, 4, 6–8. Why: decisions 0004–0006.

## Status (2026-11-17)

STATUS_LINES

**Not ready to order.** The list of what must happen first is in [`build-sheet.md`](build-sheet.md) ("Before ordering").

## Where things are

| File | What |
|---|---|
| [`build-sheet.md`](build-sheet.md) | Design spec: inputs, outline, placement, parts and how sure each LCSC number is, checks, open items |
| [`electronics/generate_schematic.py`](electronics/generate_schematic.py) | The schematic, as a script (owns the RP2040 pin map) |
| [`electronics/parts.py`](electronics/parts.py) | LCSC numbers and footprints |
| [`electronics/pin-map.md`](electronics/pin-map.md) | RP2040 GPIOs, keyboard matrix, connector pinouts (generated) |
| [`electronics/netlist.md`](electronics/netlist.md) | Every net and part (generated) |
| [`electronics/circuit-notes.md`](electronics/circuit-notes.md) | Hand calculations: boost peak current, inductors, charger, LDO, battery life (estimates) |
| [`electronics/harness.md`](electronics/harness.md) | Cable and wires |
| [`electronics/generate_pcb.py`](electronics/generate_pcb.py) | The layout, as a script (placement, autorouting, DRC, renders, Gerbers, JLCPCB files) |
| `electronics/renders/`, `electronics/fabrication/` | Generated renders, Gerbers and JLCPCB BOM / placement files |
| [`../../firmware/keyboard-board/`](../../firmware/keyboard-board/) | The RP2040 firmware (its `src/board.h` must match `pin-map.md`; the schematic script checks it) |

## Rebuild

```sh
cd hardware/keyboard-board/electronics
python3 generate_schematic.py --erc        # schematic, net list, pin map, PDF; KiCad ERC must say 0 errors, 0 warnings
tools/fetch_tools.sh                       # once, from the repository root: Freerouting 2.0.1 (needs Java 21)
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 generate_pcb.py --all
```

## Credits

The keyboard connector pinout, trackpad level shifting and matrix wiring follow Solder Party's
[BBQ20KBD](https://github.com/solderparty/bbq20kbd_hw) (CERN-OHL-1.2) and its firmware
[i2c_puppet](https://github.com/solderparty/i2c_puppet) (MIT). The RP2040 core circuit follows the Raspberry Pi Pico.
