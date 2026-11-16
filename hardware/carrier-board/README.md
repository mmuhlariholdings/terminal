# CM4 carrier board

The 4-layer board behind the screen: Raspberry Pi CM4 on two Hirose DF40 connectors, the 22-pin DSI display connector (Pi
standard, as the CM4 IO board's DISP1), a PCF85063A real-time clock with a CR2032, status LEDs, serial console pads, and the
24-way cable to the keyboard board. 74 × 72 mm, Rev A. Design spec: [`build-sheet.md`](build-sheet.md).

## Status (2026-11-17)

| Check | Result |
|---|---|
| Schematic | Generated; **KiCad ERC 0 errors, 0 warnings** (32 parts, 45 nets); all 200 CM4 pins accounted for in [`electronics/pin-map.md`](electronics/pin-map.md) |
| Layout | Placed and autorouted except the high-speed pairs; **DRC 0 violations, 16 unconnected pads** (DSI1: 10, USB: 6) |
| Ready to order? | **No.** The DSI and USB pairs must be routed by hand: [`electronics/routing-notes.md`](electronics/routing-notes.md). Gerbers are in `electronics/fabrication/` marked **not for order** |
| Impedance | Estimated widths for JLCPCB JLC04161H-7628 in [`electronics/circuit-notes.md`](electronics/circuit-notes.md); confirm with JLCPCB's calculator |

## Regenerate

```sh
cd hardware/carrier-board/electronics
python3 generate_schematic.py --erc                     # schematic, ERC, PDF, netlist.md, pin-map.md
tools/fetch_tools.sh                                    # once, from the repository root: Freerouting
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 generate_pcb.py --all
```

`generate_pcb.py` checks each of the CM4's 200 pads against the CM4 IO board footprint geometry and stops if any is off by more
than 0.01 mm. Its four-layer helpers are in `board_four_layer.py`; `estimate_impedance.py` reproduces the impedance table.

## Credits

Based on Raspberry Pi's CM4 IO board design (CM4IOv5): RTC circuit, status LEDs, DISP1 pinout and CM4 footprint geometry.
Raspberry Pi publishes those files for reuse in customers' designs; check their current terms before redistributing copies.
