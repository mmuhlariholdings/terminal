# Project conventions

The rules every part of Terminal 1 follows. Adapted from the owner's Finish Line project. If a rule gets in your way, propose a
change in a pull request; don't silently break it.

## File and folder names

- **Lowercase words joined by hyphens** for every file and folder: `build-sheet.md`, `keyboard-board.kicad_pcb`. No spaces, no capitals.
- **Exceptions:** Python scripts use underscores (`generate_pcb.py`) because Python imports need them. `README.md`, `CLAUDE.md`,
  `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` and `SECURITY.md` keep their conventional capitals. Names fixed by a tool stay
  as the tool wants them (`fp-lib-table`, `CMakeLists.txt`, KiCad footprint names).
- **Full words, no abbreviations** in file, branch and tag names: `firmware`, not `fw`; `revision`, not `rev`.
- **Say what's inside.** A file sent outside the project carries its board's name: `carrier-board-gerbers.zip`.
- **No version numbers in names.** Git and each document's revision field carry the version (third-party programs excepted:
  `freerouting-2.0.1.jar`).

## Repository layout

```
system/      plan/ (product-plan.md, interfaces.md, the original PDF), releases/ (later)
hardware/    enclosure/ (Onshape FeatureScript model, build sheet, .glb), keyboard-board/, carrier-board/
             each board: build-sheet.md, README.md, electronics/ (generators, KiCad project, netlist, renders, fabrication/)
firmware/    keyboard-board/ (RP2040, Pico SDK + TinyUSB)
linux/       install script, configs, status daemon, image build (pi-gen stage)
docs/        conventions.md (this file), decisions/ (decision records), media/ (renders)
tools/       shared generators and checks (Python)
website/     the public website (static, GitHub Pages)
```

## Units and coordinates

- **Millimetres** everywhere.
- **Device frame:** origin at the centre of the bottom (USB-C) edge on the back face; X across the width, Y up the device, Z through
  the thickness towards the screen. Board-local coordinates are stated in each board's build sheet.
- **Shared numbers** (sizes, positions, pin maps, the inter-board cable, the USB protocol) live in
  [`system/plan/interfaces.md`](../system/plan/interfaces.md). Change them there first.

## Generated files: edit the script, never the output

| What | Source | Output | Check |
|---|---|---|---|
| Schematic | `hardware/<board>/electronics/generate_schematic.py` (uses `tools/kicadgen.py`) | `.kicad_sch`, `.kicad_pro`, `netlist.md`, PDF, SVG | `--erc`: **0 errors, 0 warnings** |
| Circuit board | `generate_pcb.py` in KiCad's Python (uses `tools/pcbgen.py`) | `.kicad_pcb`, renders, Gerbers, JLCPCB BOM/CPL | DRC: **0 violations, 0 unconnected** before ordering |
| 3D model | `hardware/enclosure/terminal-1.fs` | Onshape Feature Studio, `.glb` exports | Real regeneration + `terminal-1-check.fs` (0 clashes) |
| Firmware | `firmware/keyboard-board/` | `.uf2` | Builds in CI; host tests pass |

Every generated file says which script made it. Keep Mermaid block diagrams in the plan consistent with the schematics; when one
changes, update the other in the same pull request.

## Marking what is not verified

This project is designed with an AI assistant (record 0010). Anything not confirmed from a datasheet, a measurement or a test is
marked: `CHECK` in parts tables (for example an LCSC number), *verify* in prose. Removing a mark is a contribution in itself: say
in the pull request what you checked it against.

## Versions

| What | Scheme | Where shown | Git tag |
|---|---|---|---|
| Circuit board | Revision letters A, B, C… (silkscreen and schematic title block). A new letter whenever Gerbers change | Board, schematic, build sheet | `hardware/<board>/revision-<letter>` |
| Mechanical design | Whole numbers: mechanical 1, 2… (a change that alters a fabricated part) | Build sheet | `hardware/enclosure/mechanical-<n>` |
| Firmware | Semantic versioning `MAJOR.MINOR.PATCH` | `VER` reply, USB device string | `firmware/keyboard-board/<version>` |
| Linux image | Date-based `YYYY.MM.DD` | `/etc/terminal-1-release` | `linux/<version>` |
| Plan | `1.1`, … (changelog at its end) | Plan's version line | not tagged |

## Git workflow

- `main` is always buildable. Work on a branch (any name), open a pull request, and let the checks run
  (`.github/workflows/checks.yml` and the per-area workflows).
- One topic per pull request. Commit generated files together with the script change that made them.
- Sign off your commits (`git commit -s`) to certify the [Developer Certificate of Origin](https://developercertificate.org/).

## Decision records

Every decision that shapes the device gets a record in `docs/decisions/` (context, decision, consequences, alternatives, how we
check it). Copy `template.md` to the next number, status **Proposed**, add it to the index, open a pull request; the owner accepts
it. Never rewrite an accepted record: supersede it. Checked by `python3 tools/check_decisions.py`.

## Shared design rules

- One 1S LiPo, protected, in its own bay with swell room; never charge above 45 °C (the charger's TS input watches the cell).
- The RP2040 owns power: nothing cuts the CM4's 5 V without first asking Linux to halt (except the 10 s hard-off hold).
- Outdoor-safe plastics are not needed; printed parts in PETG or ASA.
- Carbon conducts and blocks radio: keep antennas behind the radio window.

## Materials and densities used for mass estimates

| Material | g/cm³ |
|---|---|
| Aluminium 6061 | 2.70 |
| Carbon fibre / epoxy | 1.55 |
| Fibreglass / epoxy | 1.85 |
| Cover glass | 2.50 |
| Populated FR-4 board (estimate) | 2.10 |
| LiPo cell (estimate) | 2.10 |
| PETG / ASA | 1.27 / 1.07 |
| Stainless steel | 7.90 |
