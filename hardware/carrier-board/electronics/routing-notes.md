# Carrier board: routing the high-speed pairs by hand

The autorouter does not do coupled, length-matched differential pairs, so the DSI and USB pairs (16 unrouted connections in DRC) are left for
KiCad's interactive router. Rules come from [`circuit-notes.md`](circuit-notes.md) section 3; the net classes **DSI100** and
**USB90** in `carrier-board.kicad_pro` already hold the widths and gaps.

| Pairs | From → to | Net class | Width / gap (mm) |
|---|---|---|---|
| DSI1 clock + data lanes 0–3 (5 pairs) | CM4 J2 → 22-pin DSI FPC (top edge) | DSI100 | 0.20 / 0.18 |
| USB 2.0 (1 pair) + its run to the FFC | CM4 J2 → ESD part → 24-pin FFC (bottom edge) | USB90 | 0.25 / 0.18 |

DRC lists 16 unrouted connections: 10 on the DSI pairs, 6 on the USB pair (CM4 → ESD part → FFC). `carrier-board-drc.rpt` names each one.

## Steps in KiCad (about an hour)

1. Open `carrier-board.kicad_pcb` in KiCad 10's PCB editor. Pick layer **F.Cu** (the CM4 side, over the In1 ground plane).
2. **Route → Differential Pair** (shortcut `6`). Click a pad of a `_P` net; the router picks its `_N` partner and the class width/gap.
3. Route each pair on F.Cu only if you can; if a layer change is unavoidable, use a pair of vias with a ground via within 1 mm.
4. Inside the 0.4 mm DF40 pad field and the 0.5 mm FPC pads, neck down to 0.10–0.127 mm for under 2 mm (a project rule allows it).
5. **Route → Tune Skew of a Differential Pair** (`9`): match P and N to within 0.15 mm. Keep DSI lanes within about 1 mm of the clock pair.
6. Keep 0.5 mm from other copper; never cross a plane split (In1 is unbroken except the antenna keep-out).
7. **Inspect → Design Rules Checker**: 0 violations, 0 unconnected. Then commit the routed board.

## Keep the hand routing when regenerating

`generate_pcb.py` rebuilds the board from the schematic. After hand routing, run only `generate_pcb.py --finish` (imports the
autorouter session, DRC, renders, Gerbers) or teach the script to keep tracks on the pair nets. **Todo:** add a
`--keep-tracks` option that preserves existing tracks on `DSI*` and `USB*` nets (good first issue).

Once DRC is clean and the impedance widths are confirmed with JLCPCB's calculator, rename the Gerber zip (remove
`not-for-order`), and update `README.md`.
