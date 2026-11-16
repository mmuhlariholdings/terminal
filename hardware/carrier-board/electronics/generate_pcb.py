#!/usr/bin/env python3
"""Terminal 1 CM4 carrier board layout, Rev A, built from the schematic generator with KiCad's own Python:

  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 generate_pcb.py --all

  (no option)  place parts, planes and keep-outs, save carrier-board.kicad_pcb, write carrier-board.dsn for the autorouter
  --all        also autoroute (Freerouting 2.0.1, tools/bin/), import the tracks, run DRC, render, write Gerbers
  --finish     only import carrier-board.ses, DRC, render, Gerbers

Board 74 x 72 mm, 4 layers, 1.6 mm (JLCPCB JLC04161H-7628): F.Cu signals (CM4 side), In1.Cu ground plane, In2.Cu +5V_CM4
plane, B.Cu signals + ground pour. 4 x M2 holes 3.5 mm in from the corners (system/plan/interfaces.md section 3).
Coordinates: mm from the board's top-left corner (KiCad), X right, Y down. Device frame (interfaces.md): device X = x - 37,
device Y = 146 - y. The CM4 centre (device X 0, Y 112) is at (37, 34).

CM4 position: the two DF40 receptacles are placed from the pad coordinates of the CM4 footprint in Raspberry Pi's CM4 IO board
design (CM4IOv5, footprint "Raspberry-Pi-4-Compute-Module": rows 3.08 mm apart, pins 1/2 at (-2, -31.3)/(1.08, -31.3),
pins 101/102 at (31.92, -31.3)/(35, -31.3), mounting holes at (0, 0), (33, 0), (0, -48), (33, -48), all relative to one CM4
mounting hole), turned 90 degrees so the CM4's 55 mm side runs across the board, with connector J1 (pins 1-100) towards the
FFC at the bottom and J2 (pins 101-200, with DSI1 and USB) towards the display connector at the top. The script checks every
one of the 200 pads against those coordinates and stops if any is off by more than 0.01 mm.

High-speed nets (DSI1 and USB) are NOT autorouted: see routing-notes.md. The autorouter is kept out of their corridors.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
sys.path.insert(0, HERE)
import pcbgen  # noqa: E402
import pcbnew  # noqa: E402
import board_four_layer as four  # noqa: E402
from generate_schematic import REVISION, sch  # noqa: E402
from parts import FP_CM4_HOLE  # noqa: E402

W, H = 74.0, 72.0
CM4_CENTRE = (37.0, 34.0)
DSI_NETS = [f"DSI1_{l}_{s}" for l in ("D0", "D1", "C", "D2", "D3") for s in ("P", "N")]
USB_NETS = ["USB_CM4_D_P", "USB_CM4_D_N"]
HIGH_SPEED = DSI_NETS + USB_NETS

# Net classes (estimates for JLC04161H-7628, outer layer over the In1 ground plane: see circuit-notes.md and
# estimate_impedance.py; check with JLCPCB's impedance calculator before ordering an impedance-controlled build).
CLASSES = {
    "Default": dict(track_width=0.15, clearance=0.127, via_diameter=0.5, via_drill=0.3),
    "Power": dict(track_width=0.2, clearance=0.127, via_diameter=0.6, via_drill=0.3),
    "DSI100": dict(track_width=0.2, clearance=0.2, via_diameter=0.5, via_drill=0.3, diff_pair_width=0.2, diff_pair_gap=0.18),
    "USB90": dict(track_width=0.25, clearance=0.2, via_diameter=0.5, via_drill=0.3, diff_pair_width=0.25, diff_pair_gap=0.18),
}
PATTERNS = [("+5V_CM4", "Power"), ("+3V3", "Power"), ("GND", "Power"), ("RTC_VDD", "Power")] + \
           [("DSI1_*", "DSI100"), ("USB_CM4_D_*", "USB90")]
RULES = """
(rule "DSI1 pairs: matched within a pair to 0.15 mm (CM4 datasheet 2.8)"
  (condition "A.hasNetclass('DSI100')")
  (constraint diff_pair_uncoupled (max 3mm))
  (constraint skew (max 0.15mm)))
(rule "USB pair: matched to 0.15 mm (CM4 datasheet 2.4)"
  (condition "A.hasNetclass('USB90')")
  (constraint diff_pair_uncoupled (max 3mm))
  (constraint skew (max 0.15mm)))
(rule "Neck-down allowed inside the 0.4 mm pitch CM4 connector fields"
  (condition "A.hasNetclass('DSI100') || A.hasNetclass('USB90') || A.hasNetclass('Power')")
  (constraint track_width (min 0.1mm) (opt 0.2mm))
  (constraint clearance (min 0.1mm)))
"""


def cm4_point(lx, ly):
    """IO-board CM4 footprint coordinates (relative to one CM4 mounting hole) -> our board, turned 90 degrees."""
    dx, dy = lx - 16.5, ly + 24.0            # relative to the CM4 centre (holes span 33 x 48)
    return (round(CM4_CENTRE[0] + dy, 4), round(CM4_CENTRE[1] - dx, 4))


def cm4_pad(n):
    """Target position of CM4 connector pin n (1-200)."""
    base = 0.0 if n <= 100 else 33.92
    k = (n - 1) if n <= 100 else (n - 101)
    lx = base + (-2.0 if k % 2 == 0 else 1.08)
    ly = -31.3 + 0.4 * (k // 2)
    return cm4_point(lx, ly)


CM4_HOLES = [cm4_point(x, y) for x, y in ((0, 0), (33, 0), (0, -48), (33, -48))]
CM4_OUTLINE = (CM4_CENTRE[0] - 27.5, CM4_CENTRE[1] - 20, CM4_CENTRE[0] + 27.5, CM4_CENTRE[1] + 20)
# Where we believe the CM4's own PCB antenna sits (from the copper cut-out under it on the IO board, 16 x 6 mm at the module
# edge): the corner of the CM4 at the pin-200 end, J1 side. Kept free of copper on every layer so the internal antenna
# (dtparam=ant1) still works as a fallback. VERIFY against the CM4 STEP model.
ANTENNA_KEEPOUT = (58.0, 31.0, W - 0.5, 47.0)

# High-speed corridors kept free of autorouted copper (routing copy only; the saved board has no such keep-outs)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
CORRIDORS = [
    ("DSI corridor (J2 pins 171-200 to J4 pins 1-16)", (45.4, 1.0, 56.5, 20.2), [F, B]),
    ("USB corridor 1 (J2 pins 103/105 down under the CM4)", (29.3, 19.6, 31.6, 45.5), [F]),
    ("USB corridor 2", (25.5, 43.5, 31.6, 45.5), [F]),
    ("USB corridor 3 (left of J1)", (25.5, 43.5, 27.5, 58.5), [F]),
    ("USB corridor 4 (to the ESD part and the FFC)", (25.5, 56.5, 38.6, 58.5), [F]),
    ("USB corridor 5", (35.6, 56.5, 38.6, 63.6), [F]),
]

# Test pads on the back: (ref, short label). Order as in the schematic (TP1-TP12).
NOT_FOR_ORDER = ("NOT FOR ORDER. Written by hardware/carrier-board/electronics/generate_pcb.py (Terminal 1 CM4 carrier, Rev A).\n"
                 "The DSI1 and USB differential pairs are not routed and DRC is not clean. See routing-notes.md.\n")
TP_LABELS = ["TX", "RX", "GND", "BOOT", "EN", "PG", "5V", "3V3", "RTC", "INT", "SDA", "SCL"]

FRONT = {   # ref: (x, y, rotation)
    "J3": (37.0, 67.0, 0),          # FFC to the keyboard board, cable entry at the bottom edge (pads face the CM4)
    "J4": (47.75, 4.9, 180),        # DSI 22-way, cable entry at the top edge; pin 1 at the right (x 53), pin 22 at x 42.5
    "U1": (37.0, 60.6, 90),         # USB ESD, in line with the pair just above the FFC
}
BACK = {    # ref: (x, y, rotation) seen from the front (KiCad flips them onto B.Cu)
    "C1": (43.0, 57.0, 0), "C2": (48.0, 57.0, 0), "C3": (52.0, 57.0, 0), "C4": (32.0, 61.0, 0),
    "C5": (38.5, 57.0, 0), "C6": (35.0, 57.0, 0),
    "R1": (39.0, 61.5, 90), "R2": (41.0, 61.5, 90), "R3": (43.0, 61.5, 90), "R4": (45.0, 61.5, 90), "R5": (47.0, 61.5, 90),
    "R6": (49.0, 61.5, 90),
    "R7": (40.0, 10.5, 90), "R8": (38.0, 10.5, 90), "C7": (35.5, 10.5, 90), "C8": (33.5, 10.5, 90),
    "BT1": (16.0, 34.0, 90),
    "U2": (37.0, 38.0, 0), "Y1": (31.5, 38.0, 90), "D1": (37.0, 31.5, 0), "C9": (41.5, 31.5, 90), "R9": (41.5, 44.0, 90),
    "U3": (62.0, 22.0, 0), "R10": (65.5, 22.0, 90), "D3": (67.5, 22.0, 90), "R11": (65.5, 26.5, 90), "D2": (67.5, 26.5, 90),
    "JP1": (28.0, 56.0, 0), "JP2": (28.0, 60.5, 0),
}


def build():
    pro = os.path.join(HERE, sch.project + ".kicad_pro")
    four.write_net_classes(pro, CLASSES, PATTERNS)
    four.write_rules(HERE, sch.project, RULES)
    b = pcbgen.Board(sch, HERE, W, H, "Terminal 1 CM4 carrier", hole_inset=3.5, hole_fp="MountingHole_2.2mm_M2", hole_value="M2")
    four.make_four_layer(b.board)

    # CM4 connectors: every pad checked against the IO board's CM4 footprint geometry
    for ref, first in (("J1", 1), ("J2", 101)):
        fp, rot, err = four.place_to_match(b, ref, {n - first + 1: cm4_pad(n) for n in range(first, first + 100)})
        print(f"{ref}: CM4 pins {first}-{first + 99} placed, rotation {rot}, worst pad error {err:.4f} mm")
    for ref, (x, y, r) in FRONT.items():
        b.place(ref, x, y, r)
    for ref, (x, y, r) in BACK.items():
        fp = b.place(ref, x, y, r, side="bottom")
        fp.Reference().SetVisible(False)
    for ref in ("U1", "J3", "J4"):
        b.fps[ref].Reference().SetVisible(False)
    # test pads on the back in a 4 x 3 grid at the lower left, short labels on the back silkscreen
    for i, label in enumerate(TP_LABELS):
        x, y = 8.0 + (i % 4) * 5.0, 54.5 + (i // 4) * 5.0
        fp = b.place(f"TP{i + 1}", x, y, 0, side="bottom")
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        b.label(label, x + 1.4, y + 2.4, 0.8, layer=pcbnew.B_SilkS)
    missing = b.unplaced()
    if missing:
        raise SystemExit(f"parts with a footprint but no position: {missing}")

    tb = b.board.GetTitleBlock()
    tb.SetTitle("Terminal 1 CM4 carrier board"); tb.SetRevision(REVISION); tb.SetDate("2026-11-16")
    tb.SetComment(0, "Generated by hardware/carrier-board/electronics/generate_pcb.py - edit the script, not this file")
    tb.SetComment(1, "Rev A: high-speed pairs (DSI1, USB) not routed yet: see routing-notes.md. NOT FOR ORDER")
    b.outline_and_holes(corner=3.0)
    for i, (x, y) in enumerate(CM4_HOLES, 1):            # CM4 fixing holes (M2.5 standoffs, 1.5 mm stacking)
        fp = pcbgen.load_fp("MountingHole", FP_CM4_HOLE, HERE)
        fp.SetReference(f"H{4 + i}"); fp.SetValue("CM4 M2.5")
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        fp.Reference().SetVisible(False)
        b.board.Add(fp); fp.SetPosition(pcbgen.v(x, y))
    four.keepout(b.board, ANTENNA_KEEPOUT, [F, pcbnew.In1_Cu, pcbnew.In2_Cu, B], "CM4 PCB antenna: no copper (verify position)",
                 zones=True)

    # planes and pours
    four.plane(b, "GND", pcbnew.In1_Cu)
    four.plane(b, "+5V_CM4", pcbnew.In2_Cu)
    four.plane(b, "GND", F)
    four.plane(b, "GND", B)

    # plane fan-out: a via beside every ground and +5V pad (not inside the high-speed corridors: those are placed by hand
    # together with the pairs)
    added, missed = four.plane_fanout(b, {"/GND", "/+5V_CM4"}, [r for name, r, _ in CORRIDORS if not name.startswith(("USB corridor 4", "USB corridor 5"))] + [ANTENNA_KEEPOUT])
    print(f"plane fan-out: {added} vias; pads left for hand routing: {', '.join(missed) or 'none'}")

    # silkscreen
    four.silk_rect(b.board, CM4_OUTLINE, pcbnew.F_SilkS)
    b.label("CM4 (components face the screen)", CM4_OUTLINE[0] + 2, CM4_OUTLINE[1] + 19, 1.0)
    b.label("CM4 U.FL lead: up and over the top edge to the flex antenna", 6.0, 9.5, 0.8)
    b.label("DISPLAY", 35.5, 1.6, 0.8)
    b.label("TO KEYBOARD BOARD", 17.0, 70.0, 0.8)
    b.label(f"TERMINAL 1 CM4 CARRIER REV {REVISION}", 68.0, 66.5, 1.0, layer=pcbnew.B_SilkS)
    b.label("RTC CELL CR2032 +UP", 24.0, 46.5, 0.8, layer=pcbnew.B_SilkS)
    b.label("JP1 EEPROM WP  JP2 USB HOST", 34.5, 53.0, 0.8, layer=pcbnew.B_SilkS)
    b.label("PWR ACT", 69.5, 29.5, 0.8, layer=pcbnew.B_SilkS)
    return b


def drc_counts(report):
    found = dict((k, int(n)) for n, k in re.findall(r"\*\* Found (\d+) (DRC violations|unconnected pads|Footprint errors)", report))
    kinds = {}
    for m in re.finditer(r"^\[(\w+)\]:", report, re.M):
        kinds[m.group(1)] = kinds.get(m.group(1), 0) + 1
    unrouted = re.findall(r"\[unconnected_items\].*?\n(?:.*\n){0,4}?.*?Net (/?[^\]\)\s]+)", report)
    return found, kinds


def main(argv):
    pcb = os.path.join(HERE, sch.project + ".kicad_pcb")
    dsn = os.path.join(HERE, sch.project + ".dsn")
    ses = os.path.join(HERE, sch.project + ".ses")
    pro = os.path.join(HERE, sch.project + ".kicad_pro")
    if "--finish" not in argv:
        b = build()
        b.save()
        four.write_stackup(pcb)
        four.routing_copy(pcb, dsn, pro, HIGH_SPEED, CORRIDORS)
        print("placed:", pcb)
    if "--all" in argv:
        ok, log = pcbgen.route(dsn, ses, passes=40, timeout=1500)
        print("routed:", ok, log if not ok else "")
        if not ok:
            raise SystemExit(1)
    if "--finish" in argv or "--all" in argv:
        ok, ntr, nvia = pcbgen.import_routes(pcb, ses)
        board = pcbnew.LoadBoard(pcb)
        four.apply_net_classes(board, pro)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(pcb, board)
        report = pcbgen.drc(pcb)
        found, kinds = drc_counts(report)
        print("tracks", ntr, "vias", nvia, "DRC", found, kinds)
        rd = os.path.join(HERE, "renders")
        os.makedirs(rd, exist_ok=True)
        for name, kw in (("top", dict(side="top")), ("bottom", dict(side="bottom")), ("iso", dict(rotate="-50,0,-30", zoom=0.9))):
            pcbgen.render(pcb, os.path.join(rd, f"carrier-board-{name}.png"), **kw)
        gerber_dir = os.path.join(HERE, "fabrication", "gerbers")
        files, z = four.export_fab(pcb, gerber_dir, "carrier-board-gerbers-not-for-order", NOT_FOR_ORDER)
        print("gerbers:", len(files), "files ->", z)


if __name__ == "__main__":
    main(sys.argv)
