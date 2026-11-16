#!/usr/bin/env python3
"""JLCPCB assembly files for every board, read from the routed KiCad boards (Rev C onwards). Runs in KiCad's own Python:

  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 tools/build_jlc_files.py

Writes, next to each board's Gerber zip in <unit>/electronics[/ring]/fabrication/:
  <board>-jlc-bom.csv   parts list: Comment, Designator, Footprint, LCSC Part #   (one line per part type)
  <board>-jlc-cpl.csv   placement:  Designator, Mid X, Mid Y, Layer, Rotation     (every machine-placed part)
and prints a summary: parts per board, unique part types, lines without an LCSC number (JLCPCB matches those by value and
footprint at upload: check the match it offers).

Left out of both files: parts marked "exclude from BOM" on the board (test pads, wire pads, mounting holes). Rotations are KiCad's;
JLCPCB's upload shows every part on the board picture: check the orientation of polarised parts (chips, diodes, the electrolytic
capacitor, connectors) there, and use its rotate tool if one is wrong. Stock is checked live by the same upload.
"""
import csv
import os
import sys
from collections import OrderedDict

import pcbnew

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BOARDS = {
    "centre-pod": "hardware/centre-pod/electronics/centre-pod.kicad_pcb",
    "light-head": "hardware/light-head/electronics/light-head.kicad_pcb",
    "reflector-pod": "hardware/reflector-pod/electronics/reflector-pod.kicad_pcb",
    "reflector-ring": "hardware/reflector-pod/electronics/ring/reflector-ring.kicad_pcb",
    "remote": "hardware/remote/electronics/remote.kicad_pcb",
}


def field(fp, name):
    return fp.GetFieldText(name) if fp.HasField(name) else ""


def main():
    origin_note = "coordinates in mm from the board's top-left corner, Y measured upwards (negative), as KiCad's own position files"
    totals = []
    for name, rel in BOARDS.items():
        pcb = os.path.join(ROOT, rel)
        board = pcbnew.LoadBoard(pcb)
        out_dir = os.path.join(os.path.dirname(pcb), "fabrication")
        os.makedirs(out_dir, exist_ok=True)
        groups, rows, blank = OrderedDict(), [], []
        for fp in sorted(board.GetFootprints(), key=lambda f: (f.GetReference().rstrip("0123456789"), int("0" + "".join(c for c in f.GetReference() if c.isdigit())))):
            attrs = fp.GetAttributes()
            if attrs & pcbnew.FP_EXCLUDE_FROM_BOM or attrs & pcbnew.FP_BOARD_ONLY:
                continue
            ref, val, lcsc = fp.GetReference(), fp.GetValue(), field(fp, "LCSC")
            if lcsc == "CHECK":
                lcsc = ""
            fpname = fp.GetFPID().GetLibItemName().wx_str()
            key = (val, fpname, lcsc)
            groups.setdefault(key, []).append(ref)
            pos = fp.GetPosition()
            rows.append([ref, f"{pcbnew.ToMM(pos.x):.3f}mm", f"{-pcbnew.ToMM(pos.y):.3f}mm",
                         "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom", f"{fp.GetOrientationDegrees() % 360:.1f}"])
            if not lcsc:
                blank.append(f"{val} ({', '.join([ref])})")
        bom = os.path.join(out_dir, f"{name}-jlc-bom.csv")
        with open(bom, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
            for (val, fpname, lcsc), refs in groups.items():
                w.writerow([val, ",".join(refs), fpname, lcsc])
        cpl = os.path.join(out_dir, f"{name}-jlc-cpl.csv")
        with open(cpl, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            w.writerows(rows)
        missing = sorted({(v, ", ".join(r)) for (v, f, l), r in groups.items() if not l})
        totals.append((name, len(rows), len(groups), missing))
        print(f"{name:15} {len(rows):3} parts, {len(groups):2} part types -> {os.path.relpath(bom, ROOT)}, {os.path.basename(cpl)}")
        for v, r in missing:
            print(f"{'':15} no LCSC number (JLCPCB matches it at upload): {v} [{r}]")
    print(f"({origin_note})")
    return totals


if __name__ == "__main__":
    main()
    sys.exit(0)
