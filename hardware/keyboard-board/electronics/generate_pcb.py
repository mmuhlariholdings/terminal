#!/usr/bin/env python3
"""Keyboard and power board layout, Rev A, built from the schematic generator with KiCad's own Python:

  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 generate_pcb.py --all

  (no option)  place parts, pours and keep-outs, save keyboard-board.kicad_pcb, write keyboard-board.dsn for the autorouter
  --all        also autoroute (Freerouting 2.0.1, tools/bin/; fetch it with tools/fetch_tools.sh), import the tracks, DRC,
               renders, Gerbers, JLCPCB BOM / placement files
  --finish     only import keyboard-board.ses, DRC, renders, Gerbers, JLCPCB files

Board 74 x 60 mm, 2 layers, 1.6 mm, 4 x M2 holes 3.5 mm in from the corners (system/plan/interfaces.md section 3, v0.2).
Coordinates: mm from the board's top-left corner as seen from the FRONT (keyboard side), X right, Y down. Device frame
(interfaces.md section 1): device X = x - 37, device Y = 64 - y. The top edge (y = 0) faces the screen.

  Front (F.Cu): only the Q20 keyboard connector; the keyboard and nav row sit over the whole front (device Y 8-60).
  Back (B.Cu): everything else. Parts over 2.0 mm tall (USB-C 3.2, boost inductor 3.0, power button) need frame cut-outs:
  listed in build-sheet.md.
  USB-C at the bottom edge centre, FFC to the carrier at the top edge centre, power button on the right edge at device Y 50.

The keyboard connector position and the two slots beside it copy the BBQ20KBD board (Solder Party, CERN-OHL-1.2): both boards
are 74 mm wide with the keyboard centred, and the connector sits 15.3 mm below the top of the nav row (BBQ20KBD: connector
at 12.0, 22.2 with the nav row about 6.9 mm below its top edge, measured from its photo, so an estimate). Our nav row top is at
device Y 60 (hardware/enclosure/build-sheet.md), 4 mm below the board's top edge. CHECK with a keyboard in hand.

Uses tools/pcbgen.py (shared, not edited). Board-specific behaviour lives here: net classes with JLCPCB-friendly 0.15 mm
clearance (the shared default of 0.2 mm cannot reach the RP2040's 0.4 mm-pitch pads), a design rule for the 0.4 mm-pitch
keyboard connector, the slots, power pours and a test-pad placer for the back side.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import pcbgen  # noqa: E402
import pcbnew  # noqa: E402
from generate_schematic import REVISION, sch  # noqa: E402

W, H = 74.0, 60.0
MM = pcbnew.FromMM

# Slots copied from the BBQ20KBD board, shifted 2.9 mm up (our nav row is 4 mm below the top edge, theirs about 6.9 mm).
SLOTS = [(5.8, 4.6, 17.0, 8.6), (5.5, 11.8, 9.2, 26.5)]
KEYBOARD_CONNECTOR_AT = (12.0, 19.3)

POWER_NETS = ["VBUS", "VSYS", "VBAT", "+5V_CM4", "CHARGER_SW", "CHARGER_PMID", "BOOST_SW"]
CLASSES = {  # JLCPCB 2-layer: 0.127 mm minimum track and gap; we use 0.15 / 0.2 with margin
    "Default": dict(track_width=0.2, clearance=0.15, via_diameter=0.6, via_drill=0.3),
    "Power": dict(track_width=0.3, clearance=0.15, via_diameter=0.8, via_drill=0.4),   # 0.3: still fits the 0.5 mm-pitch charger pads; current goes through the pours
}

# fixed positions: ref -> (x, y, rotation, side)
FIXED = {
    "J3": (KEYBOARD_CONNECTOR_AT[0], KEYBOARD_CONNECTOR_AT[1], 90, "top"),   # Q20 keyboard connector, front
    "J4": (37.0, 5.0, 0, "bottom"),      # FFC to the carrier, top edge centre; latch side faces the top edge (checked below)
    "J1": (37.0, 56.4, 180, "bottom"),   # USB-C, mouth at the bottom edge (checked below)
    "SW2": (72.2, 14.0, 90, "bottom"),   # power button, plunger out of the right edge (checked below)
    "U8": (37.0, 27.0, 45, "bottom"),    # RP2040, turned 45 degrees for even fan-out
    "U2": (20.0, 47.0, 0, "bottom"),     # BQ25895 near the USB-C
    "L1": (11.5, 47.5, 0, "bottom"),     # charger inductor
    "U4": (58.0, 40.5, 0, "bottom"),     # TPS61089
    "L2": (65.0, 46.0, 90, "bottom"),    # boost inductor
    "J2": (3.4, 28.4, 90, "bottom"),     # battery wire pads, a column along the left edge (the cell is behind the frame)
}


def write_net_classes(pro_path):
    data = json.load(open(pro_path)) if os.path.exists(pro_path) else {}
    base = {"clearance": 0.15, "via_diameter": 0.6, "via_drill": 0.3, "diff_pair_gap": 0.25, "diff_pair_width": 0.2,
            "diff_pair_via_gap": 0.25, "microvia_diameter": 0.3, "microvia_drill": 0.1, "wire_width": 6, "bus_width": 12,
            "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647}
    classes = []
    for name, c in CLASSES.items():
        d = dict(base, name=name, **c)
        if name != "Default":
            d["priority"] = 1
        classes.append(d)
    data["net_settings"] = {"classes": classes, "meta": {"version": 4},
                            "netclass_patterns": [{"netclass": "Power", "pattern": "/" + n} for n in POWER_NETS]}
    ds = data.setdefault("board", {}).setdefault("design_settings", {})
    sev = ds.setdefault("rule_severities", {})
    # silkscreen-only checks waived (cosmetic; the board house clips silk over pads); every copper check stays an error
    sev.update({"silk_edge_clearance": "ignore", "silk_over_copper": "ignore", "silk_overlap": "ignore"})
    rules = ds.setdefault("rules", {})
    rules.update({"min_clearance": 0.127, "min_track_width": 0.127, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3,
                  "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.2})
    with open(pro_path, "w") as fh:
        json.dump(data, fh, indent=2)


def write_rules():
    pcbgen.write_rules(HERE, sch.project)
    with open(os.path.join(HERE, sch.project + ".kicad_dru"), "a") as fh:
        fh.write('(rule "Keyboard connector: 0.4 mm pitch pads are 0.17 mm apart (Hirose land pattern)"\n'
                 '  (condition "A.Type == \'Pad\' && B.Type == \'Pad\' && A.Parent == \'J3\' && B.Parent == \'J3\'")\n'
                 '  (constraint clearance (min 0.12)))\n')


def slot(b, x0, y0, x1, y1, keepout=0.5):
    """Rectangular cut-out (Edge.Cuts) with a copper keep-out ring, so the autorouter stays clear."""
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    for a, c in zip(pts, pts[1:]):
        s = pcbnew.PCB_SHAPE(b.board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
        s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); s.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
        b.board.Add(s)
    keep_out(b, x0 - keepout, y0 - keepout, x1 + keepout, y1 + keepout)


def keep_out(b, x0, y0, x1, y1, tracks=True):
    z = pcbnew.ZONE(b.board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowZoneFills(True)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    ol = z.Outline(); ol.NewOutline()
    for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(MM(px), MM(py))
    b.board.Add(z)


def centre(fp, pads):
    xs = [pcbnew.ToMM(p.GetPosition().x) for p in fp.Pads() if p.GetNumber() in pads]
    ys = [pcbnew.ToMM(p.GetPosition().y) for p in fp.Pads() if p.GetNumber() in pads]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def check_orientation(b):
    """Stop if a connector faces the wrong way: USB-C signal pads must be further from the bottom edge than its shell pads'
    centre, the FFC's contacts further from the top edge than its latch (fab outline), the button's contacts left of its plunger."""
    problems = []
    usb = b.fps["J1"]
    if not centre(usb, ["A1", "B1"])[1] < centre(usb, ["SH"])[1]:
        problems.append("J1 USB-C: mouth does not face the bottom edge")
    ffc = b.fps["J4"]
    bbox = ffc.GetBoundingBox(False)
    body = (pcbnew.ToMM(bbox.GetTop()) + pcbnew.ToMM(bbox.GetBottom())) / 2
    if not centre(ffc, ["1", "24"])[1] > body:
        problems.append("J4 FFC: cable entry does not face the top edge")
    sw = b.fps["SW2"]
    if not centre(sw, ["1", "2"])[0] < centre(sw, ["MP"])[0]:
        problems.append("SW2 power button: plunger does not face the right edge")
    if problems:
        raise SystemExit("orientation: " + "; ".join(problems))


def exposed_pad_vias(b, ref, pad_number, columns, rows, diameter=0.6, drill=0.3):
    """Ground vias inside an exposed pad: the pad is ringed by pins, so the autorouter cannot leave it by a track."""
    fp = b.fps[ref]
    pad = [p for p in fp.Pads() if p.GetNumber() == pad_number][0]
    bb = pad.GetBoundingBox()
    x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
    for i in range(columns):
        for j in range(rows):
            x = x0 + (x1 - x0) * (i + 1) / (columns + 1)
            y = y0 + (y1 - y0) * (j + 1) / (rows + 1)
            via = pcbnew.PCB_VIA(b.board)
            via.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
            via.SetWidth(MM(diameter)); via.SetDrill(MM(drill))
            via.SetNet(pad.GetNet())
            b.board.Add(via)


def place_test_pads(b, refs, clearance=0.6):
    """Test pads on the BACK, in free space (the front is under the keyboard). Scans rows from the bottom edge up."""
    def box(fp):
        bb = fp.GetBoundingBox(False)
        return (pcbnew.ToMM(bb.GetLeft()) - clearance, pcbnew.ToMM(bb.GetTop()) - clearance,
                pcbnew.ToMM(bb.GetRight()) + clearance, pcbnew.ToMM(bb.GetBottom()) + clearance)
    blocked = [box(fp) for fp in b.board.GetFootprints() if fp.GetLayer() == pcbnew.B_Cu or fp.GetReference().startswith("H")]
    blocked += [(x0 - 0.8, y0 - 0.8, x1 + 0.8, y1 + 0.8) for x0, y0, x1, y1 in SLOTS]
    todo = list(refs)
    y = H - 2.6
    while todo and y > 2.5:
        x = 2.6
        while todo and x < W - 2.6:
            label = len(b._parts[todo[0]].value) * 0.55 + 0.4
            half = max(1.3, label / 2)
            r = (x - half, y - 1.3, x + half, y + 2.7)
            if all(r[2] < q[0] or r[0] > q[2] or r[3] < q[1] or r[1] > q[3] for q in blocked):
                ref = todo.pop(0)
                fp = b.place(ref, x, y, 0, side="bottom")
                fp.Reference().SetVisible(False)
                val = fp.Value()
                val.SetLayer(pcbnew.B_SilkS); val.SetVisible(True); val.SetMirrored(True)
                val.SetTextSize(pcbnew.VECTOR2I(MM(0.7), MM(0.7))); val.SetTextThickness(MM(0.1))
                val.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y + 1.9)))
                blocked.append((r[0] - 0.3, r[1] - 0.3, r[2] + 0.3, r[3] + 0.3))
                x = r[2] + half + 0.4
            else:
                x += 0.5
        y -= 0.5
    if todo:
        raise SystemExit(f"no free space on the back for test pads {todo}")


def build():
    write_rules()
    write_net_classes(os.path.join(HERE, sch.project + ".kicad_pro"))
    b = pcbgen.Board(sch, HERE, W, H, "Terminal 1 keyboard board", hole_inset=3.5, hole_fp="MountingHole_2.2mm_M2", hole_value="M2")
    for ref, (x, y, r, side) in FIXED.items():
        b.place(ref, x, y, r, side=side)
    check_orientation(b)
    for x0, y0, x1, y1 in SLOTS:
        slot(b, x0, y0, x1, y1)
    by_desc = {p.ref: p for p in sch.parts}
    overflow = []

    def group(names, x0, y0, x1, y1, gap=0.5, rot=0):
        # like pcbgen.Board.place_group, but on the back: pack left to right in rows, keeping `gap` mm between outlines
        x, y, row = x0, y0, 0.0
        for ref in names:
            if ref in b.fps:
                continue
            fp = b.place(ref, 0, 0, rot, side="bottom")
            fp.Reference().SetVisible(False)
            bb = fp.GetBoundingBox(False)
            w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
            if x + w > x1 + 1e-6 and x > x0:
                x, y, row = x0, y + row + gap, 0.0
            if y + h > y1 + 1e-6 or x + w > x1 + 1e-6:
                b.fps.pop(ref)
                b.board.Remove(fp)
                overflow.append(f"{ref} ({by_desc[ref].value}, {w:.1f} x {h:.1f}) in ({x0}, {y0})-({x1}, {y1})")
                continue
            ox, oy = pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY())
            pos = fp.GetPosition()
            fp.SetPosition(pcbnew.VECTOR2I(pos.x + MM(x - ox), pos.y + MM(y - oy)))
            x += w + gap
            row = max(row, h)

    def net_parts(*nets, prefixes=("R", "C", "D", "Q", "Y", "SW", "JP", "U")):
        out = []
        for p in sch.parts:
            if not p.on_board or p.ref in b.fps or p.ref.startswith("TP") or not p.ref.startswith(prefixes):
                continue
            if any(pin[2] in nets for pin in p.left + p.right):
                out.append(p.ref)
        return out

    # Groups: references from the schematic generator (stable while its part order is unchanged).
    # ---- top band: CM4 interface drivers, USB switch ----
    group(["Q7", "Q8", "Q9", "R32", "R33", "R34", "R35", "R36", "R37", "R38", "R39", "R40", "C42"], 47.5, 1.8, 66.5, 10.5)
    group(["U10", "C38", "R18", "R16", "R17"], 26.0, 9.0, 36.5, 16.5)
    # ---- left: trackpad LDOs and level shifters (behind the keyboard connector), 3.3 V LDO, gauge ----
    group(["U6", "U7", "C21", "C22", "C23", "C40", "C41", "Q2", "Q3", "Q4", "Q5", "Q6",
           "R24", "R25", "R26", "R27", "R28", "R29", "R30", "R31"], 10.0, 9.6, 25.5, 28.0)
    group(["U5", "C19", "C20"], 10.0, 28.5, 22.0, 32.5)
    group(["U3", "C9", "C8"], 8.0, 34.0, 22.0, 38.5)
    # ---- RP2040 core ----
    group(["C24", "C25", "C26", "C27", "C28", "C29", "C30", "C31"], 43.8, 19.5, 50.6, 34.5)
    group(["C32", "C33", "C34", "R13"], 25.5, 19.5, 30.5, 30.0)
    group(["Y1", "R15", "C36", "C37"], 25.5, 34.0, 37.0, 40.0)
    group(["U9", "C35", "R14"], 37.5, 33.5, 50.5, 43.5)
    group(["SW1"], 34.0, 43.6, 42.5, 49.8)
    # ---- I2C pull-ups, power button parts, backlight switch (right, near the button) ----
    group(["R19", "R20", "R21", "R22", "C39", "Q1", "R23"], 51.5, 12.0, 69.5, 19.5)
    # ---- boost (right) ----
    group(["R7", "C10", "C11", "R8", "R9", "R10", "R11", "C12", "R12"], 51.0, 20.5, 65.5, 36.0)
    group(["C15", "C16", "C17", "C18"], 66.0, 21.5, 71.8, 40.0, rot=90)
    group(["C13", "C14"], 52.0, 50.0, 61.0, 58.0)
    # ---- charger (bottom left, next to the USB-C) ----
    group(["C6", "C7"], 23.5, 43.5, 33.5, 49.5)
    group(["C1", "C2", "C3", "C4", "C5", "R3", "R4", "R5", "R6", "JP1", "D1"], 7.0, 51.0, 31.5, 59.0)
    group(["U1", "R1", "R2"], 42.5, 50.0, 51.5, 58.5)
    group([p.ref for p in sch.parts if p.on_board and p.ref not in b.fps and not p.ref.startswith("TP")], 26.0, 45.5, 50.0, 49.5)
    if overflow:
        raise SystemExit("parts that did not fit their area:\n  " + "\n  ".join(overflow))

    b.outline_and_holes(corner=2.0)
    # keep tracks out from under the side-entry parts' overhangs and the inductors' centres (copper under L is allowed)
    b.label(f"TERMINAL 1 KEYBOARD BOARD REV {REVISION}", 26.0, 50.6, 0.9, layer=pcbnew.B_SilkS)
    b.label("github.com terminal-1 (CERN-OHL-S-2.0)", 26.0, 52.0, 0.7, layer=pcbnew.B_SilkS)
    place_test_pads(b, [p.ref for p in sch.parts if p.ref.startswith("TP")])
    missing = b.unplaced()
    if missing:
        raise SystemExit(f"parts with a footprint but no position: {missing}")
    for ref, pad, columns, rows in (("U8", "57", 3, 3), ("U2", "25", 2, 2), ("U10", "11", 1, 2), ("U3", "9", 1, 1)):
        exposed_pad_vias(b, ref, pad, columns, rows)
    # power pours on the back (component side), above the ground pour: VSYS across the bottom, +5V_CM4 up the right side
    b.copper_area("VSYS", 9.0, 44.8, 66.0, 49.0, layer=pcbnew.B_Cu, priority=2)
    b.copper_area("+5V_CM4", 62.0, 6.0, 71.5, 41.0, layer=pcbnew.B_Cu, priority=2)
    # the cell current (up to about 6 A) from the wire pads to the charger's BAT pins: a pour on the front (only J3 is there)
    b.copper_area("VBAT", 1.5, 27.5, 24.0, 50.5, layer=pcbnew.F_Cu, priority=2)
    b.ground_planes()
    return b


def jlc_files():
    """JLCPCB BOM and placement (CPL) files with the shared tools/build_jlc_files.py, pointed at this board only."""
    import build_jlc_files
    build_jlc_files.BOARDS = {"keyboard-board": os.path.relpath(os.path.join(HERE, sch.project + ".kicad_pcb"), ROOT)}
    build_jlc_files.ROOT = ROOT
    return build_jlc_files.main()


ROUTER_PASSES = 20          # Freerouting gives up after this many passes and writes its best (possibly incomplete) result
ROUTER_TIMEOUT = 3600       # seconds; one pass takes about 50 s on this board


def route(dsn_path, ses_path):
    """Freerouting 2.0.1 with a pass limit. Its "-mp" option does not stop the batch router in 2.0.1 (seen on this board:
    45 passes with -mp 12); the limit that works is "router.max_passes" in its settings file, which lives in its user-data
    folder under the Java temporary directory. This run gets a private temporary directory with its own settings file, so the
    shared tools/pcbgen.py and the user's own Freerouting settings are left alone."""
    import subprocess
    import tempfile
    data = os.path.join(tempfile.gettempdir(), "terminal-1-keyboard-board-freerouting")
    os.makedirs(os.path.join(data, "freerouting"), exist_ok=True)
    with open(os.path.join(data, "freerouting", "freerouting.json"), "w") as fh:
        json.dump({"gui": {"enabled": False}, "router": {"max_passes": ROUTER_PASSES, "max_threads": 1},
                   "usage_and_diagnostic_data": {"disable_analytics": True}, "version": "2.0.1"}, fh)
    if os.path.exists(ses_path):
        os.remove(ses_path)
    log_path = dsn_path[:-len(".dsn")] + "-freerouting.log"
    with open(log_path, "w") as log:
        subprocess.run(["java", f"-Djava.io.tmpdir={data}", "-jar", pcbgen.FREEROUTING, "-de", dsn_path, "-do", ses_path,
                        "-mp", str(ROUTER_PASSES), "-mt", "1", "--gui.enabled=false"],
                       stdout=log, stderr=subprocess.STDOUT, timeout=ROUTER_TIMEOUT)
    ok = os.path.exists(ses_path) and os.path.getsize(ses_path) > 0
    return ok, open(log_path).read()[-1500:]


if __name__ == "__main__":
    if "--all" in sys.argv:
        pcbgen.main(build, sch, HERE, [])                       # place, save, write the DSN
        project = os.path.join(HERE, sch.project)
        ok, log = route(project + ".dsn", project + ".ses")
        print("routed:", ok)
        if not ok:
            print(log)
            raise SystemExit(1)
        pcbgen.main(build, sch, HERE, ["--finish"])
        jlc_files()
    else:
        pcbgen.main(build, sch, HERE, sys.argv)
        if "--finish" in sys.argv:
            jlc_files()
