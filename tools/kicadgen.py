"""Minimal KiCad 8 schematic writer for the Terminal 1 boards.

Each unit's `<component>/electronics/generate_schematic.py` describes its parts and nets with this module and writes
`<unit>.kicad_sch` + `<unit>.kicad_pro`. Connections are made with NET LABELS on a short wire stub at every pin (a standard
KiCad practice), so the drawing is the net list: no long wires to route by hand.

Also writes:
  - an SVG preview (to check the layout without KiCad),
  - a net report (every net and the pins on it), used by `check()` to catch typos (a net with only one pin).

Conventions: mm, A3 sheet, everything on the 1.27 mm grid. Symbol-local Y is up; schematic Y is down (KiCad's rule).
UUIDs are derived from names (uuid5), so regenerating gives identical files and clean git diffs.
"""
import json
import os
import uuid
from collections import defaultdict

G = 2.54
NS = uuid.UUID("6f1c2a52-0b7e-4c84-9b0e-3f2d1a7c5e11")


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def fnum(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") if abs(v) > 1e-9 else "0"


FONT = "(effects (font (size 1.27 1.27)))"
FONT_HIDE = "(effects (font (size 1.27 1.27)) hide)"


class Part:
    """A schematic part. kind: 'box' (module/IC, pins left and right), 'R', 'C', 'LED', 'D2' (2-pin box),
    'flag' (power flag: one power_out pin, not in the BOM; tells ERC a net is supplied, e.g. through a switch)."""

    def __init__(self, ref, value, kind="box", left=(), right=(), width=None, desc="", footprint="", on_board=None, lcsc=""):
        self.ref, self.value, self.kind, self.desc, self.footprint = ref, value, kind, desc, footprint
        self.lcsc = lcsc          # JLCPCB / LCSC part number (C123456) for machine assembly; "" = not machine-placed
        self.in_bom = kind != "flag"
        # parts without a footprint (battery, fuse, lid items...) are wired to the board but not on it
        self.on_board = (bool(footprint) and kind != "flag") if on_board is None else on_board
        self.left = list(left)    # [(num, name, net, type)] net None = no-connect
        self.right = list(right)
        self.width = width
        self.at = (0.0, 0.0)

    # ---- symbol geometry (symbol-local, Y up) ----
    def geom(self):
        if self.kind == "flag":
            return {"w": 2.54, "h": 2.54, "pins": [(self.left[0], -2.54, 0.0, 0)], "plen": 1.27}
        if self.kind in ("R", "C", "LED", "D2"):
            return {"w": 5.08, "pins": [(self.left[0], -5.08, 0.0, 0), (self.right[0], 5.08, 0.0, 180)], "plen": 2.54}
        n = max(len(self.left), len(self.right), 1)
        h = (n + 1) * G
        w = self.width or 20.32
        pins = []
        for i, p in enumerate(self.left):
            pins.append((p, -w / 2 - G, ((n - 1) / 2 - i) * G, 0))
        for i, p in enumerate(self.right):
            pins.append((p, w / 2 + G, ((n - 1) / 2 - i) * G, 180))
        return {"w": w, "h": h, "pins": pins, "plen": G}

    def lib_name(self):
        import re
        return "terminal-1:" + re.sub(r"[^A-Za-z0-9_.-]", "_", f"{self.ref}_{self.value}".replace("#", ""))

    def lib_symbol(self, prefixed=True):
        """Symbol definition: prefixed=True for the schematic's embedded lib_symbols, False for the terminal-1.kicad_sym library."""
        g = self.geom()
        name = self.lib_name()
        base = name.split(":", 1)[1]
        yn = "yes" if self.in_bom else "no"
        ob = "yes" if self.on_board else "no"
        hide_nums = " (pin_numbers hide)" if any(not p[0][0].isdigit() for p in g["pins"]) and self.kind == "box" else ""
        out = [f"(symbol {q(name if prefixed else base)}{hide_nums} (pin_names (offset 0.508)) (exclude_from_sim no) (in_bom {yn}) (on_board {ob})",
               f"(property \"Reference\" {q(self.ref.rstrip('0123456789'))} (at 0 0 0) {FONT})",
               f"(property \"Value\" {q(self.value)} (at 0 0 0) {FONT})",
               f"(property \"Footprint\" \"\" (at 0 0 0) {FONT_HIDE})",
               f"(property \"Datasheet\" \"\" (at 0 0 0) {FONT_HIDE})",
               f"(property \"Description\" {q(self.desc)} (at 0 0 0) {FONT_HIDE})",
               f"(symbol {q(base + '_0_1')}"]
        st = "(stroke (width 0.254) (type default))"
        if self.kind == "box":
            w, h = g["w"], g["h"]
            out.append(f"(rectangle (start {fnum(-w / 2)} {fnum(h / 2)}) (end {fnum(w / 2)} {fnum(-h / 2)}) {st} (fill (type background)))")
        elif self.kind == "flag":
            out.append(f"(polyline (pts (xy -1.27 0) (xy 0 1.27) (xy 1.27 0) (xy 0 -1.27) (xy -1.27 0)) {st} (fill (type none)))")
        elif self.kind == "R" or self.kind == "D2":
            out.append(f"(rectangle (start -2.54 1.016) (end 2.54 -1.016) {st} (fill (type none)))")
        elif self.kind == "C":
            out.append(f"(polyline (pts (xy -0.762 2.032) (xy -0.762 -2.032)) {st} (fill (type none)))")
            out.append(f"(polyline (pts (xy 0.762 2.032) (xy 0.762 -2.032)) {st} (fill (type none)))")
            out.append(f"(polyline (pts (xy -2.54 0) (xy -0.762 0)) {st} (fill (type none)))")
            out.append(f"(polyline (pts (xy 0.762 0) (xy 2.54 0)) {st} (fill (type none)))")
        elif self.kind == "LED":
            out.append(f"(polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27)) {st} (fill (type none)))")
            out.append(f"(polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27)) {st} (fill (type none)))")
            out.append(f"(polyline (pts (xy -2.54 0) (xy -1.27 0)) {st} (fill (type none)))")
            out.append(f"(polyline (pts (xy 1.27 0) (xy 2.54 0)) {st} (fill (type none)))")
        out.append(")")
        out.append(f"(symbol {q(base + '_1_1')}")
        for (num, pname, net, ptype), x, y, ang in g["pins"]:
            out.append(f"(pin {ptype} line (at {fnum(x)} {fnum(y)} {ang}) (length {fnum(g['plen'])}) "
                       f"(name {q(pname)} {FONT}) (number {q(num)} {FONT}))")
        out.append(")")
        out.append(")")
        return "\n".join(out)

    def pin_points(self):
        """[(pin tuple, schematic x, y, side)] side -1 = left (stub goes left), +1 = right."""
        X, Y = self.at
        res = []
        for p, x, y, ang in self.geom()["pins"]:
            res.append((p, X + x, Y - y, -1 if ang == 0 else 1))
        return res


class Schematic:
    def __init__(self, project, title, rev, comments=()):
        self.project, self.title, self.rev, self.comments = project, title, rev, list(comments)
        self.parts = []
        self.texts = []   # (x, y, text, size)
        self.root = uid(project, "root")

    def add(self, part, x, y):
        part.at = (round(x / 1.27) * 1.27, round(y / 1.27) * 1.27)
        self.parts.append(part)
        return part

    def note(self, x, y, text, size=1.27):
        self.texts.append((x, y, text, size))

    # ---- nets ----
    def nets(self):
        nets = defaultdict(list)
        for pt in self.parts:
            for (num, pname, net, ptype), *_ in pt.pin_points():
                if net:
                    nets[net].append(f"{pt.ref}.{num}({pname})")
        return dict(sorted(nets.items()))

    def check(self):
        problems = []
        refs = [p.ref for p in self.parts]
        dup = {r for r in refs if refs.count(r) > 1}
        if dup:
            problems.append(f"duplicate references {sorted(dup)}")
        for net, pins in self.nets().items():
            if len(pins) < 2:
                problems.append(f"net {net} has only one pin: {pins}")
        return problems

    # ---- writers ----
    def write(self, folder):
        os.makedirs(folder, exist_ok=True)
        sch = os.path.join(folder, f"{self.project}.kicad_sch")
        o = [f"(kicad_sch (version 20231120) (generator \"terminal1_kicadgen\") (generator_version \"8.0\")",
             f"(uuid {q(self.root)})", "(paper \"A3\")",
             f"(title_block (title {q(self.title)}) (date \"2026-11-16\") (rev {q(self.rev)}) (company \"Terminal 1 open hardware\")"]
        for i, c in enumerate(self.comments[:4], 1):
            o.append(f"(comment {i} {q(c)})")
        o.append(")")
        o.append("(lib_symbols")
        for pt in self.parts:
            o.append(pt.lib_symbol())
        o.append(")")
        for pt in self.parts:
            X, Y = pt.at
            g = pt.geom()
            top = Y - (g.get("h", 2.54) / 2) - 1.27
            bot = Y + (g.get("h", 2.54) / 2) + 1.27
            o.append(f"(symbol (lib_id {q(pt.lib_name())}) (at {fnum(X)} {fnum(Y)} 0) (unit 1) (exclude_from_sim no) "
                     f"(in_bom {'yes' if pt.in_bom else 'no'}) (on_board {'yes' if pt.on_board else 'no'}) (dnp no) (uuid {q(uid(self.project, pt.ref))})")
            o.append(f"(property \"Reference\" {q(pt.ref)} (at {fnum(X)} {fnum(top)} 0) {FONT})")
            o.append(f"(property \"Value\" {q(pt.value)} (at {fnum(X)} {fnum(bot)} 0) {FONT})")
            o.append(f"(property \"Footprint\" {q(pt.footprint)} (at {fnum(X)} {fnum(Y)} 0) {FONT_HIDE})")
            o.append(f"(property \"Datasheet\" \"\" (at {fnum(X)} {fnum(Y)} 0) {FONT_HIDE})")
            o.append(f"(property \"Description\" {q(pt.desc)} (at {fnum(X)} {fnum(Y)} 0) {FONT_HIDE})")
            if pt.lcsc:
                o.append(f"(property \"LCSC\" {q(pt.lcsc)} (at {fnum(X)} {fnum(Y)} 0) {FONT_HIDE})")
            for (num, *_), *_ in pt.pin_points():
                o.append(f"(pin {q(num)} (uuid {q(uid(self.project, pt.ref, 'pin', num))}))")
            o.append(f"(instances (project {q(self.project)} (path {q('/' + self.root)} (reference {q(pt.ref)}) (unit 1))))")
            o.append(")")
        for pt in self.parts:
            for (num, pname, net, ptype), x, y, side in pt.pin_points():
                if net is None:
                    o.append(f"(no_connect (at {fnum(x)} {fnum(y)}) (uuid {q(uid(self.project, pt.ref, num, 'nc'))}))")
                    continue
                x2 = x + side * G
                o.append(f"(wire (pts (xy {fnum(x)} {fnum(y)}) (xy {fnum(x2)} {fnum(y)})) (stroke (width 0) (type default)) "
                         f"(uuid {q(uid(self.project, pt.ref, num, 'w'))}))")
                ang, just = (180, "right bottom") if side < 0 else (0, "left bottom")
                o.append(f"(label {q(net)} (at {fnum(x2)} {fnum(y)} {ang}) (fields_autoplaced yes) "
                         f"(effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(uid(self.project, pt.ref, num, 'l'))}))")
        for i, (x, y, t, s) in enumerate(self.texts):
            o.append(f"(text {q(t)} (exclude_from_sim no) (at {fnum(x)} {fnum(y)} 0) "
                     f"(effects (font (size {s} {s})) (justify left top)) (uuid {q(uid(self.project, 'text', i))}))")
        o.append("(sheet_instances (path \"/\" (page \"1\")))")
        o.append(")")
        with open(sch, "w") as fh:
            fh.write("\n".join(o) + "\n")
        # symbol library + project library table, so KiCad finds the "terminal-1" library (and the symbols can be edited)
        with open(os.path.join(folder, "terminal-1.kicad_sym"), "w") as fh:
            fh.write("(kicad_symbol_lib (version 20231120) (generator \"terminal1_kicadgen\") (generator_version \"8.0\")\n")
            fh.write("\n".join(pt.lib_symbol(prefixed=False) for pt in self.parts) + "\n)\n")
        with open(os.path.join(folder, "sym-lib-table"), "w") as fh:
            fh.write('(sym_lib_table\n  (version 7)\n  (lib (name "terminal-1")(type "KiCad")(uri "${KIPRJMOD}/terminal-1.kicad_sym")(options "")'
                     '(descr "Terminal 1 generated symbols"))\n)\n')
        pro = os.path.join(folder, f"{self.project}.kicad_pro")
        data = {}
        if os.path.exists(pro):                      # keep settings written by KiCad or the board script (net classes)
            try:
                data = json.load(open(pro))
            except ValueError:
                data = {}
        data.setdefault("meta", {})["filename"] = f"{self.project}.kicad_pro"
        data["meta"].setdefault("version", 1)
        data["sheets"] = [[self.root, "Root"]]
        with open(pro, "w") as fh:
            json.dump(data, fh, indent=2)
        return sch

    def write_netlist_md(self, path):
        lines = [f"# {self.title}: net list", "", f"Generated from `{self.project}.kicad_sch` by its generator. Do not edit by hand.", "",
                 "| Net | Pins |", "|---|---|"]
        for net, pins in self.nets().items():
            lines.append(f"| `{net}` | {', '.join(pins)} |")
        lines += ["", "## Parts", "", "| Ref | Value | LCSC | Description |", "|---|---|---|---|"]
        for pt in sorted([p for p in self.parts if p.in_bom], key=lambda p: (p.ref.rstrip('0123456789'), int(''.join(c for c in p.ref if c.isdigit()) or 0))):
            lines.append(f"| {pt.ref} | {pt.value} | {pt.lcsc or ('not on board' if not pt.on_board else '')} | {pt.desc} |")
        with open(path, "w") as fh:
            fh.write("\n".join(lines) + "\n")

    def write_svg(self, path):
        W, H = 420, 297
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * 4}" height="{W * 4}" viewBox="0 0 {W} {W}">',
             f'<rect width="{W}" height="{W}" fill="white"/>', '<g font-family="Helvetica" fill="black">']
        for pt in self.parts:
            X, Y = pt.at
            g = pt.geom()
            if pt.kind == "box":
                s.append(f'<rect x="{X - g["w"] / 2}" y="{Y - g["h"] / 2}" width="{g["w"]}" height="{g["h"]}" fill="#ffffe0" stroke="#800" stroke-width="0.25"/>')
                s.append(f'<text x="{X}" y="{Y - g["h"] / 2 - 1.2}" font-size="1.6" text-anchor="middle">{pt.ref} {pt.value}</text>')
            else:
                s.append(f'<rect x="{X - 2.54}" y="{Y - 1.0}" width="5.08" height="2.0" fill="none" stroke="#800" stroke-width="0.25"/>')
                s.append(f'<text x="{X}" y="{Y - 1.6}" font-size="1.3" text-anchor="middle">{pt.ref} {pt.value}</text>')
            for (num, pname, net, _), x, y, side in pt.pin_points():
                xb = x - side * G
                s.append(f'<line x1="{x}" y1="{y}" x2="{xb}" y2="{y}" stroke="#800" stroke-width="0.2"/>')
                if pt.kind == "box":
                    s.append(f'<text x="{xb - side * 0.6}" y="{y + 0.45}" font-size="1.2" text-anchor="{"start" if side < 0 else "end"}">{pname}</text>')
                if net is None:
                    s.append(f'<text x="{x}" y="{y + 0.5}" font-size="1.5" fill="blue" text-anchor="middle">x</text>')
                else:
                    x2 = x + side * G
                    s.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y}" stroke="green" stroke-width="0.2"/>')
                    s.append(f'<text x="{x2 + side * 0.4}" y="{y - 0.3}" font-size="1.2" fill="green" text-anchor="{"end" if side < 0 else "start"}">{net}</text>')
        for x, y, t, sz in self.texts:
            for i, line in enumerate(t.split("\n")):
                s.append(f'<text x="{x}" y="{y + (i + 1) * sz * 1.25}" font-size="{sz}">{line.replace("&", "&amp;").replace("<", "&lt;")}</text>')
        s.append("</g></svg>")
        with open(path, "w") as fh:
            fh.write("\n".join(s))


def run_erc(sch_path):
    """Run KiCad's electrical rules check (kicad-cli) and export the schematic PDF next to it. Returns (errors, warnings, report text) or None if KiCad isn't installed."""
    import glob
    import re
    import subprocess
    import tempfile
    cands = glob.glob("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli") + glob.glob("/usr/bin/kicad-cli") + glob.glob("/usr/local/bin/kicad-cli")
    if not cands:
        return None
    rpt = os.path.join(tempfile.gettempdir(), os.path.basename(sch_path) + ".erc.rpt")
    subprocess.run([cands[0], "sch", "erc", "--severity-all", "-o", rpt, sch_path], capture_output=True, text=True)
    if not os.path.exists(rpt):
        return (-1, -1, "KiCad could not load the schematic")
    text = open(rpt).read()
    subprocess.run([cands[0], "sch", "export", "pdf", "-o", sch_path[:-len(".kicad_sch")] + ".pdf", sch_path], capture_output=True, text=True)
    m = re.search(r"Errors (\d+)\s+Warnings (\d+)", text)
    return (int(m.group(1)), int(m.group(2)), text) if m else (-1, -1, text)


# ---- small helpers for the unit scripts ----
def P(num, name, net, ptype="passive"):
    """Pin: number, name, net (None = no-connect), KiCad electrical type."""
    return (num, name, net, ptype)


def two(ref, value, kind, net1, net2, desc, name1="~", name2="~", footprint="", lcsc=""):
    """Two-pin part (kind R, C, LED, D2): pin 1 on net1 (left), pin 2 on net2 (right)."""
    return Part(ref, value, kind, left=[P("1", name1, net1)], right=[P("2", name2, net2)], desc=desc, footprint=footprint, lcsc=lcsc)


TP_FOOTPRINT = "TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm"


def testpoints(sch, nets, x, y, first=1, per_row=4):
    """Test points: one 2 mm through-hole pad per net, for multimeter checks during bring-up and fault finding.
    Each is a one-pin part TP<n> whose value is the net name, printed beside the pad on the board."""
    for i, net in enumerate(nets):
        tp = Part(f"TP{first + i}", net, left=[P("1", "TP", net)], width=7.62, desc=f"Test point: {net}", footprint=TP_FOOTPRINT)
        tp.in_bom = False          # a bare copper pad, nothing to buy (matches KiCad's test-point footprint)
        sch.add(tp, x + (i % per_row) * 25.4, y + (i // per_row) * 10.16)


def flag(ref, net, desc):
    """Power flag on a net that is supplied through a switch or fuse (keeps KiCad's ERC honest)."""
    return Part(ref, "PWR_FLAG", "flag", left=[P("1", "pwr", net, "power_out")], desc=desc)


def write_fp_lib_table(here, sch_path):
    """Project footprint library table: our own library (if the folder has one) plus every KiCad standard library the schematic
    uses, from KiCad's built-in folder. So the project needs no global KiCad set-up: it checks the same on a Mac and in CI."""
    import re as _re
    used = sorted(set(_re.findall(r'\(property "Footprint" "([A-Za-z0-9_.-]+):', open(sch_path, encoding="utf-8").read())) - {"terminal-1"})
    rows = []
    if os.path.isdir(os.path.join(here, "terminal-1.pretty")):
        rows.append('  (lib (name "terminal-1")(type "KiCad")(uri "${KIPRJMOD}/terminal-1.pretty")(options "")(descr "Terminal 1 project footprints"))')
    for lib in used:
        rows.append(f'  (lib (name "{lib}")(type "KiCad")(uri "${{KICAD10_FOOTPRINT_DIR}}/{lib}.pretty")(options "")(descr "KiCad standard library"))')
    with open(os.path.join(here, "fp-lib-table"), "w") as fh:
        fh.write("(fp_lib_table\n  (version 7)\n" + "\n".join(rows) + "\n)\n")


def finish(sch, here, argv):
    """Write all outputs; run the net check and (with --erc) KiCad's ERC + PDF. Exits non-zero on any problem."""
    import sys as _sys
    problems = sch.check()
    out = sch.write(here)
    write_fp_lib_table(here, out)
    sch.write_netlist_md(os.path.join(here, "netlist.md"))
    os.makedirs(os.path.join(here, "preview"), exist_ok=True)
    sch.write_svg(os.path.join(here, "preview", sch.project + ".svg"))
    print("wrote", out)
    print(f"{len([p for p in sch.parts if p.in_bom])} parts, {len(sch.nets())} nets")
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))
        _sys.exit(1)
    print("net check: every net joins at least two pins")
    if "--erc" in argv:
        res = run_erc(out)
        if res is None:
            print("ERC skipped: KiCad (kicad-cli) not installed")
        else:
            print(f"KiCad ERC: {res[0]} errors, {res[1]} warnings")
            if res[0] or res[1]:
                print(res[2])
                _sys.exit(1)
