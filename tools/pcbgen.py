"""Circuit board builder for the Terminal 1 boards. Runs inside KiCad's own Python (it uses the pcbnew module):

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 <component>/electronics/generate_pcb.py

It reads the parts, footprints and nets from the component's schematic generator (so the board can never disagree
with the schematic), places each footprint where the board script says, assigns every pad to its net, adds the board
outline, mounting holes, a label and ground planes, and saves <project>.kicad_pcb. Net classes (track widths) go in the
project file. Routing is a separate step (Specctra DSN out, routed session back in).
"""
import json
import os
import subprocess

import pcbnew

KICAD = "/Applications/KiCad/KiCad.app/Contents"
STD_FP = os.path.join(KICAD, "SharedSupport", "footprints")
KICAD_CLI = os.path.join(KICAD, "MacOS", "kicad-cli")
MM = pcbnew.FromMM


def v(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


# Project copies of standard footprints, adapted for JLCPCB's 2-layer process: name -> (standard library, standard name).
# The heat vias under these modules' ground pads are 0.2 mm, finer than JLCPCB's 0.3 mm minimum for 2-layer boards, so the
# copies drop them; the ground pad still connects through the module's ground pins and the pours.
JLC_VARIANTS = {"ESP32-S3-WROOM-1U_JLC": ("RF_Module", "ESP32-S3-WROOM-1U"), "ESP32-S2-MINI-1U_JLC": ("RF_Module", "ESP32-S2-MINI-1U")}


JLC_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jlc-footprints.pretty")
JLC_3D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jlc-footprints.3dshapes")
# 3D models for the copies (KiCad's library has none for these modules): Espressif's own, placed as in Espressif's footprints,
# corrected for any difference between their footprint origin and KiCad's (WROOM-1U: KiCad's pads sit 0.15 mm higher).
JLC_MODELS = {"ESP32-S3-WROOM-1U_JLC": ("ESP32-S3-WROOM-1U.STEP", (-9.0, -9.6, 0.0)),
              "ESP32-S2-MINI-1U_JLC": ("ESP32-S3-MINI-1U.STEP", (-7.7, -7.7, 0.0))}


# 3D models for standard KiCad footprints whose library has none: footprint name -> (file, offset mm, rotation degrees).
# Checked by measuring each model against its footprint's pads and body outline (KiCad 3D export), 2026-11-15.
EXTRA_MODELS = {
    "SW_Push_1P1T_XKB_TS-1187A": ("SW_Push_1P1T_XKB_TS-1187A.step", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),        # EasyEDA / LCSC C318884
    "microSD_HC_Molex_104031-0811": ("microSD_HC_Molex_104031-0811.step", (-0.07, -0.30, 0.0), (90.0, 0.0, 0.0)),  # Molex (Y-up model)
}


def attach_models(fp, folder):
    """Give a placed footprint the project's 3D model, if it has one (JLC module copies or EXTRA_MODELS)."""
    name = fp.GetFPID().GetLibItemName().wx_str()
    if name in JLC_MODELS:
        step, off = JLC_MODELS[name]; rot = (0.0, 0.0, 0.0)
    elif name in EXTRA_MODELS:
        step, off, rot = EXTRA_MODELS[name]
    else:
        return False
    fp.Models().clear()
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = model_path(folder, step)
    m.m_Offset.x, m.m_Offset.y, m.m_Offset.z = off
    m.m_Rotation.x, m.m_Rotation.y, m.m_Rotation.z = rot
    fp.Models().push_back(m)
    return True


def model_path(folder, step):
    """Path to a project 3D model as KiCad expects it in a project: relative to the project folder (${KIPRJMOD})."""
    return "${KIPRJMOD}/" + os.path.relpath(os.path.join(JLC_3D, step), folder).replace(os.sep, "/")


def ensure_jlc_variant(folder, fpname):
    """Make the JLCPCB copy once in tools/jlc-footprints.pretty, then copy it into the project's terminal-1.pretty."""
    import shutil
    lib = os.path.join(folder, "terminal-1.pretty")
    path = os.path.join(lib, fpname + ".kicad_mod")
    shared = os.path.join(JLC_LIB, fpname + ".kicad_mod")
    if not os.path.exists(shared):
        # text edit of the standard footprint file: drop through-hole pads finer than 0.3 mm (KiCad's own FootprintSave is
        # unreliable from a script). Pads are top-level "(pad ...)" blocks; matching brackets finds each block's end.
        import re
        stdlib, stdname = JLC_VARIANTS[fpname]
        text = open(os.path.join(STD_FP, stdlib + ".pretty", stdname + ".kicad_mod"), encoding="utf-8").read()
        out, i, removed = [], 0, 0
        for m in re.finditer(r"\(pad ", text):
            if m.start() < i:
                continue
            depth, k = 0, m.start()
            while True:
                if text[k] == "(":
                    depth += 1
                elif text[k] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            block = text[m.start():k + 1]
            d = re.search(r"\(drill ([\d.]+)", block)
            if " thru_hole " in block and d and float(d.group(1)) < 0.3:
                out.append(text[i:m.start()].rstrip(" \t"))
                i = k + 1
                removed += 1
        out.append(text[i:])
        text = "".join(out)
        text = re.sub(r'\(footprint "[^"]+"', f'(footprint "{fpname}"', text, count=1)
        # replace the standard library's 3D model (not installed for these parts) with Espressif's: a placeholder path, filled in
        # per project when the copy is made (the relative path differs by folder depth)
        text = re.sub(r'\s*\(model "[^"]*"(?:[^()]|\((?:[^()]|\([^()]*\))*\))*\)', "", text)
        if fpname in JLC_MODELS:
            step, (ox, oy, oz) = JLC_MODELS[fpname]
            block = (f'\n\t(model "@JLC3D@/{step}"\n\t\t(offset (xyz {ox} {oy} {oz}))\n\t\t(scale (xyz 1 1 1))\n'
                     f'\t\t(rotate (xyz 0 0 0))\n\t)\n')
            text = text.rstrip().rstrip(")") + block + ")\n"
        text = re.sub(r'\(descr "([^"]*)"', lambda mm: f'(descr "{mm.group(1)} (JLCPCB 2-layer copy: {removed} heat vias of 0.2 mm removed)"', text, count=1)
        os.makedirs(JLC_LIB, exist_ok=True)
        open(shared, "w", encoding="utf-8").write(text)
    os.makedirs(lib, exist_ok=True)
    text = open(shared, encoding="utf-8").read()
    step = JLC_MODELS.get(fpname, ("",))[0]
    if step:
        text = text.replace(f"@JLC3D@/{step}", model_path(folder, step))
    open(path, "w", encoding="utf-8").write(text)
    table = os.path.join(folder, "fp-lib-table")
    row = '  (lib (name "terminal-1")(type "KiCad")(uri "${KIPRJMOD}/terminal-1.pretty")(options "")(descr "Terminal 1 project footprints"))\n'
    if not os.path.exists(table):
        with open(table, "w") as fh:
            fh.write("(fp_lib_table\n  (version 7)\n" + row + ")\n")
    elif '(name "terminal-1")' not in open(table).read():
        # keep the standard-library rows written by tools/kicadgen.py; add ours after the header
        text = open(table).read().replace("(version 7)\n", "(version 7)\n" + row, 1)
        open(table, "w").write(text)


def load_fp(libname, fpname, folder):
    if libname == "terminal-1" and fpname in JLC_VARIANTS:
        ensure_jlc_variant(folder, fpname)
    path = os.path.join(folder, libname + ".pretty") if libname == "terminal-1" else os.path.join(STD_FP, libname + ".pretty")
    fp = pcbnew.FootprintLoad(path, fpname)
    if fp is None:
        raise RuntimeError(f"footprint not found: {libname}:{fpname}")
    fp.SetFPID(pcbnew.LIB_ID(libname, fpname))
    return fp


def write_net_classes(pro_path, power_nets, power_width=1.0, signal_width=0.35, high_nets=(), high_width=2.5):
    """Net classes in the project file: power nets get wide tracks; high-current nets (LED channels) wider still."""
    data = json.load(open(pro_path)) if os.path.exists(pro_path) else {}
    # 0.2 mm clearance everywhere: what Freerouting routes to, ample at 12 V (IPC-2221: about 0.1 mm below 15 V)
    base = {"clearance": 0.2, "via_diameter": 0.9, "via_drill": 0.45, "diff_pair_gap": 0.25, "diff_pair_width": 0.2,
            "diff_pair_via_gap": 0.25, "microvia_diameter": 0.3, "microvia_drill": 0.1, "wire_width": 6, "bus_width": 12,
            "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647}
    data["net_settings"] = {
        "classes": [dict(base, name="Default", track_width=signal_width),
                    dict(base, name="Power", track_width=power_width, via_diameter=1.2, via_drill=0.6, priority=1),
                    dict(base, name="HighCurrent", track_width=high_width, via_diameter=1.6, via_drill=0.8, priority=0)],
        "meta": {"version": 4},
        "netclass_patterns": [{"netclass": "Power", "pattern": "/" + n} for n in power_nets]
                             + [{"netclass": "HighCurrent", "pattern": "/" + n} for n in high_nets],
    }
    # Silkscreen checks waived on purpose: connectors (USB-C, microSD, terminals) overhang the board edge by design, and silkscreen
    # that runs over a pad is trimmed by the board house. Every other check stays an error.
    sev = data.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rule_severities", {})
    # Silkscreen touching silkscreen is cosmetic only (references on packed parts are hidden anyway).
    sev.update({"silk_edge_clearance": "ignore", "silk_over_copper": "ignore", "silk_overlap": "ignore"})
    with open(pro_path, "w") as fh:
        json.dump(data, fh, indent=2)


def apply_net_classes(board, pro_path):
    """Put the project file's net classes (track width, via size) and net patterns onto a loaded board, so the Specctra export
    tells the autorouter how wide each net's tracks must be. (A board loaded or built from a script doesn't pick them up by itself:
    Rev B boards were routed at the default width everywhere because of this.)"""
    data = json.load(open(pro_path))["net_settings"]
    ns = board.GetDesignSettings().m_NetSettings
    for c in data["classes"]:
        if c["name"] == "Default":
            nc = ns.GetDefaultNetclass()
        else:
            nc = pcbnew.NETCLASS(c["name"])
            nc.SetPriority(c.get("priority", 0))
        nc.SetTrackWidth(MM(c["track_width"])); nc.SetClearance(MM(c["clearance"]))
        nc.SetViaDiameter(MM(c["via_diameter"])); nc.SetViaDrill(MM(c["via_drill"]))
        if c["name"] != "Default":
            ns.SetNetclass(c["name"], nc)
    for a in data.get("netclass_patterns", []):
        ns.SetNetclassPatternAssignment(a["pattern"], a["netclass"])
    ns.ClearAllCaches()
    for net in board.GetNetInfo().NetsByName().values():
        net.SetNetClass(ns.GetEffectiveNetClass(net.GetNetname()))


class Board:
    def __init__(self, sch, folder, width, height, title, holes=(), hole_inset=5.0, hole_fp="MountingHole_3.2mm_M3", hole_value="M3"):
        self.sch, self.folder, self.w, self.h, self.title = sch, folder, width, height, title
        self.hole_fp, self.hole_value = hole_fp, hole_value
        self.board = pcbnew.BOARD()
        self.nets = {}
        self.fps = {}
        self.holes = list(holes) or [(hole_inset, hole_inset), (width - hole_inset, hole_inset),
                                     (hole_inset, height - hole_inset), (width - hole_inset, height - hole_inset)]
        self._parts = {p.ref: p for p in sch.parts}

    def net(self, name, raw=False):
        if not raw:
            name = "/" + name        # local labels on the root sheet are named "/<label>" by KiCad
        if name not in self.nets:
            ni = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(ni)
            self.nets[name] = ni
        return self.nets[name]

    def place(self, ref, x, y, rot=0, side="top"):
        """Place a schematic part's footprint with its origin at (x, y) mm, rotated rot degrees (counter-clockwise)."""
        import uuid as _uuid
        part = self._parts[ref]
        lib, name = part.footprint.split(":", 1)
        fp = load_fp(lib, name, self.folder)
        fp.SetReference(ref)
        fp.SetValue(part.value)
        fp.SetField("Description", part.desc)
        attach_models(fp, self.folder)
        if not part.in_bom:                         # bare pads (test points, wire pads): nothing to buy or fit
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
            fp.Models().clear()                     # and no 3D model: a pin-header footprint used for wire pads would render as a header
        if getattr(part, "lcsc", ""):
            fp.SetField("LCSC", part.lcsc)          # JLCPCB part number, carried into the assembly files
            f = fp.GetField("LCSC")
            f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
        self.board.Add(fp)
        fp.SetPosition(v(x, y))
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        if side == "bottom":
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        # link to the schematic symbol (root sheet path = "/<symbol uuid>") so KiCad can check board against schematic
        from kicadgen import uid
        fp.SetPath(pcbnew.KIID_PATH("/" + uid(self.sch.project, ref)))
        pinnet, unused = {}, {}
        for (num, pname, netname, ptype), *_ in part.pin_points():
            if netname:
                pinnet[num] = netname
            else:                    # KiCad gives each no-connect pin its own net: unconnected-(<ref>-<pin>-Pad<n>)
                unused[num] = (f"unconnected-({ref}-Pad{num})" if pname in (num, "~", "")
                               else f"unconnected-({ref}-{pname.replace(' ', '_')}-Pad{num})")
        for pad in fp.Pads():
            n = pad.GetNumber()
            if n in pinnet:
                pad.SetNet(self.net(pinnet[n]))
            elif n in unused:
                pad.SetNet(self.net(unused[n], raw=True))
        self.fps[ref] = fp
        return fp

    def place_testpoints(self, refs, edge=2.5, clearance=0.8):
        """Put the test points (TP...) in free space: scan rows from the bottom edge up, left to right, and take spots
        clear of every placed footprint's courtyard, the mounting holes, rule areas and board texts. The net name is
        printed on the silkscreen under each pad."""
        def box_of(fp):
            try:
                return fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            except Exception:
                return fp.GetBoundingBox(False, False)
        def grow(b, d):
            return (pcbnew.ToMM(b.GetLeft()) - d, pcbnew.ToMM(b.GetTop()) - d, pcbnew.ToMM(b.GetRight()) + d, pcbnew.ToMM(b.GetBottom()) + d)
        blocked = [grow(box_of(fp), clearance) for fp in self.board.GetFootprints()]
        blocked += [grow(z.GetBoundingBox(), clearance) for z in self.board.Zones() if z.GetIsRuleArea()]
        blocked += [grow(t.GetBoundingBox(), clearance) for t in self.board.GetDrawings() if isinstance(t, pcbnew.PCB_TEXT)]
        def need(ref):     # pad plus the net label under it, relative to the pad centre; labels are about 0.62 mm per character
            half = max(1.6, (0.62 * len(self._parts[ref].value) + 0.6) / 2)
            return (-half, -1.6, half, 3.4)
        def free(ref, x, y):
            n = need(ref)
            r = (x + n[0], y + n[1], x + n[2], y + n[3])
            if r[0] < edge or r[1] < edge or r[2] > self.w - edge or r[3] > self.h - edge:
                return False
            return all(r[2] < b[0] or r[0] > b[2] or r[3] < b[1] or r[1] > b[3] for b in blocked)
        todo = list(refs)
        y = self.h - edge - 3.4
        while todo and y > edge:
            x = edge + 1.6
            while todo and x < self.w:
                ref = todo[0]
                if free(ref, x, y):
                    todo.pop(0)
                    fp = self.place(ref, x, y)
                    fp.Reference().SetVisible(False)
                    val = fp.Value()
                    val.SetLayer(pcbnew.F_SilkS); val.SetVisible(True)
                    val.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8))); val.SetTextThickness(MM(0.12))
                    val.SetPosition(v(x, y + 2.4))
                    n = need(ref)
                    blocked.append((x + n[0] - clearance, y + n[1] - clearance, x + n[2] + clearance, y + n[3] + clearance))
                    x += n[2] + clearance + 0.5
                else:
                    x += 0.5
            y -= 0.5
        if todo:
            raise SystemExit(f"no free space for test points {todo}")

    def block(self, name):
        """References of the parts a shared block (tools/boardblocks.py) added, in schematic order."""
        return [p.ref for p in self.sch.parts if p.on_board and getattr(p, "block", None) == name]

    def place_group(self, refs, x0, y0, x1, y1, gap=1.0, rot=0):
        """Pack footprints into the rectangle (x0, y0)-(x1, y1) mm, left to right in rows, in the order given, keeping `gap` mm
        between their outlines (courtyards and pads, text ignored). Parts already placed are skipped. Fails loudly if they
        don't fit, so a crowded region is fixed in the board script rather than overlapping silently."""
        x, y, row = x0, y0, 0.0
        for ref in refs:
            if ref in self.fps:
                continue
            fp = self.place(ref, 0, 0, rot)
            fp.Reference().SetVisible(False)        # packed small parts: the reference is on the assembly drawing, not the silkscreen
            bb = fp.GetBoundingBox(False)
            w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
            if x + w > x1 + 1e-6 and x > x0:
                x, y, row = x0, y + row + gap, 0.0
            if y + h > y1 + 1e-6 or x + w > x1 + 1e-6:
                raise SystemExit(f"place_group: {ref} ({w:.1f} x {h:.1f} mm) doesn't fit in ({x0}, {y0})-({x1}, {y1})")
            ox, oy = pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY())
            fp.SetPosition(v(x - ox, y - oy))
            x += w + gap
            row = max(row, h)
        return y + row

    def copper_area(self, net, x0, y0, x1, y1, layer=None, priority=1):
        """Solid copper on one net over a rectangle (e.g. a MOSFET drain, to spread its heat), above the ground planes."""
        z = pcbnew.ZONE(self.board)
        z.SetLayer(layer if layer is not None else pcbnew.F_Cu); z.SetNet(self.net(net))
        z.SetAssignedPriority(priority)
        z.SetLocalClearance(MM(0.4)); z.SetMinThickness(MM(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        ol = z.Outline(); ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(MM(x), MM(y))
        self.board.Add(z)

    def unplaced(self):
        return sorted(p.ref for p in self.sch.parts if p.on_board and p.ref not in self.fps)

    def outline_and_holes(self, corner=3.0):
        w, h, r = self.w, self.h, corner
        segs = [((r, 0), (w - r, 0)), ((w, r), (w, h - r)), ((w - r, h), (r, h)), ((0, h - r), (0, r))]
        for a, b in segs:
            s = pcbnew.PCB_SHAPE(self.board)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
            s.SetStart(v(*a)); s.SetEnd(v(*b)); self.board.Add(s)
        k = r * (1 - 0.7071067811865476)
        for start, mid, end in (((0, r), (k, k), (r, 0)), ((w - r, 0), (w - k, k), (w, r)),
                                ((w, h - r), (w - k, h - k), (w - r, h)), ((r, h), (k, h - k), (0, h - r))):
            s = pcbnew.PCB_SHAPE(self.board)
            s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
            s.SetArcGeometry(v(*start), v(*mid), v(*end))
            self.board.Add(s)
        # keep tracks and vias 1 mm clear of the board edge (the autorouter doesn't see KiCad's edge clearance)
        band = 1.0
        for x0, y0, x1, y1 in ((0, 0, w, band), (0, h - band, w, h), (0, 0, band, h), (w - band, 0, w, h)):
            z = pcbnew.ZONE(self.board)
            z.SetIsRuleArea(True)
            z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowZoneFills(False)
            ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
            ol = z.Outline(); ol.NewOutline()
            for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
                ol.Append(MM(px), MM(py))
            self.board.Add(z)
        for i, (x, y) in enumerate(self.holes, 1):
            fp = load_fp("MountingHole", self.hole_fp, self.folder)
            fp.SetReference(f"H{i}"); fp.SetValue(self.hole_value)
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
            fp.Reference().SetVisible(False)
            self.board.Add(fp); fp.SetPosition(v(x, y))

    def cutout_circle(self, cx, cy, d, keepout=2.0):
        """Round hole cut through the board (e.g. the reflector opening in the alignment ring board), with a keep-out
        ring round it so the autorouter (which doesn't see KiCad's edge clearance on inner holes) stays clear."""
        import math
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
        s.SetCenter(v(cx, cy)); s.SetEnd(v(cx + d / 2, cy))
        self.board.Add(s)
        z = pcbnew.ZONE(self.board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowZoneFills(False)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
        ol = z.Outline(); ol.NewOutline()
        r = d / 2 + keepout
        for i in range(48):
            a = 2 * math.pi * i / 48
            ol.Append(MM(cx + r * math.cos(a)), MM(cy + r * math.sin(a)))
        self.board.Add(z)

    def label(self, text, x, y, size=1.6, layer=None):
        t = pcbnew.PCB_TEXT(self.board)
        t.SetText(text); t.SetPosition(v(x, y)); t.SetLayer(layer if layer is not None else pcbnew.F_SilkS)
        if layer == pcbnew.B_SilkS:
            t.SetMirrored(True)          # bottom-side text reads correctly when the board is turned over
        t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(size * 0.15))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        self.board.Add(t)

    def solid_to_plane(self, pads):
        """High-current pads join the ground plane solidly (no thermal spokes). pads: [(ref, pad number)]."""
        for ref, num in pads:
            for pad in self.fps[ref].Pads():
                if pad.GetNumber() == num:
                    pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    def ground_planes(self, net="GND", layers=(pcbnew.F_Cu, pcbnew.B_Cu), inset=0.5):
        for layer in layers:
            z = pcbnew.ZONE(self.board)
            z.SetLayer(layer); z.SetNet(self.net(net))
            z.SetLocalClearance(MM(0.4)); z.SetMinThickness(MM(0.3))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)   # no orphaned copper islands
            ol = z.Outline(); ol.NewOutline()
            for x, y in ((inset, inset), (self.w - inset, inset), (self.w - inset, self.h - inset), (inset, self.h - inset)):
                ol.Append(MM(x), MM(y))
            self.board.Add(z)

    def fill_zones(self):
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())

    def save(self):
        path = os.path.join(self.folder, self.sch.project + ".kicad_pcb")
        self.board.SetFileName(path)
        pcbnew.SaveBoard(path, self.board)
        return path


def drc(pcb_path, parity=True):
    rpt = pcb_path[:-len(".kicad_pcb")] + "-drc.rpt"
    args = [KICAD_CLI, "pcb", "drc", "--severity-all", "-o", rpt]
    if parity:
        args.append("--schematic-parity")
    subprocess.run(args + [pcb_path], capture_output=True, text=True)
    return open(rpt).read() if os.path.exists(rpt) else "DRC did not run"


def render(pcb_path, out_png, side="top", rotate=None, w=1600, h=1000, zoom=1.0):
    args = [KICAD_CLI, "pcb", "render", "-o", out_png, "--quality", "high", "--background", "opaque",
            "-w", str(w), "-h", str(h), "--zoom", str(zoom), "--side", side]
    if rotate:
        args += ["--rotate", rotate, "--perspective"]
    r = subprocess.run(args + [pcb_path], capture_output=True, text=True)
    return os.path.exists(out_png), r.stderr[-400:]


def import_routes(pcb_path, ses_path):
    """Bring the autorouter's tracks (Specctra session) into the board, refill the ground planes, save."""
    board = pcbnew.LoadBoard(pcb_path)
    ok = pcbnew.ImportSpecctraSES(board, ses_path)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(pcb_path, board)
    tracks = [t for t in board.GetTracks()]
    vias = [t for t in tracks if t.GetClass() == "PCB_VIA"]
    return ok, len(tracks) - len(vias), len(vias)


def write_rules(folder, project):
    """Project design rules (<project>.kicad_dru). Through-hole pads on a ground plane may be joined by a single
    thermal spoke on one layer, because the same pad is also joined to the plane on the other layer."""
    with open(os.path.join(folder, project + ".kicad_dru"), "w") as fh:
        fh.write('(version 1)\n'
                 '(rule "THT ground pads: one spoke is enough (joined on both layers)"\n'
                 '  (condition "A.Type == \'Pad\' && A.NetName == \'/GND\'")\n'
                 '  (constraint min_resolved_spokes 1))\n')


def export_fab(pcb_path, outdir):
    """Manufacturing files for a board house (JLCPCB, PCBWay...): Gerbers for every layer, Excellon drill, one zip."""
    import shutil
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        os.remove(os.path.join(outdir, f))
    layers = "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts"
    subprocess.run([KICAD_CLI, "pcb", "export", "gerbers", "-o", outdir + "/", "--layers", layers, "--subtract-soldermask", pcb_path],
                   capture_output=True, text=True)
    subprocess.run([KICAD_CLI, "pcb", "export", "drill", "-o", outdir + "/", "--format", "excellon", "--drill-origin", "absolute",
                    "--excellon-units", "mm", "--generate-map", "--map-format", "pdf", pcb_path], capture_output=True, text=True)
    files = sorted(os.listdir(outdir))
    zipbase = os.path.join(os.path.dirname(outdir), os.path.basename(pcb_path)[:-len(".kicad_pcb")] + "-gerbers")
    shutil.make_archive(zipbase, "zip", outdir)
    return files, zipbase + ".zip"


def finish(pcb_path, ses_path, render_dir):
    """After routing: import tracks, check, render and export manufacturing files. Returns a summary dict."""
    import re
    folder = os.path.dirname(pcb_path)
    ok, ntr, nvia = import_routes(pcb_path, ses_path)
    board = pcbnew.LoadBoard(pcb_path)               # bare pads have no 3D model (also for boards placed before this rule)
    for fp in board.GetFootprints():
        if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM and not (fp.GetAttributes() & pcbnew.FP_BOARD_ONLY):
            fp.Models().clear()
    pcbnew.SaveBoard(pcb_path, board)
    report = drc(pcb_path)
    found = dict((k, int(n)) for n, k in re.findall(r"\*\* Found (\d+) (DRC violations|unconnected pads|Footprint errors)", report))
    os.makedirs(render_dir, exist_ok=True)
    stem = os.path.basename(pcb_path)[:-len(".kicad_pcb")]
    shots = {}
    for name, kw in (("top", dict(side="top")), ("bottom", dict(side="bottom")), ("iso", dict(rotate="-50,0,-30", zoom=0.9))):
        out = os.path.join(render_dir, f"{stem}-{name}.png")
        render(pcb_path, out, **kw)
        shots[name] = os.path.exists(out)
    fab_files, zip_path = export_fab(pcb_path, os.path.join(folder, "fabrication", "gerbers"))
    return {"import_ok": ok, "tracks": ntr, "vias": nvia, "drc": found, "renders": shots, "fab_files": len(fab_files), "zip": zip_path}


FREEROUTING = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "freerouting-2.0.1.jar")


def route(dsn_path, ses_path, passes=50, timeout=900, tries=3):
    """Autoroute with Freerouting (no window, single thread: its multi-thread optimiser is known to break clearances).
    Its output goes to <project>-freerouting.log, not a pipe: with a pipe it sometimes exits before the session file is written
    (an empty .ses). An empty or missing session is retried."""
    log_path = dsn_path[:-len(".dsn")] + "-freerouting.log"
    for attempt in range(1, tries + 1):
        if os.path.exists(ses_path):
            os.remove(ses_path)
        with open(log_path, "w") as log:
            subprocess.run(["java", "-jar", FREEROUTING, "-de", dsn_path, "-do", ses_path, "-mp", str(passes), "-mt", "1",
                            "--gui.enabled=false"], stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        if os.path.exists(ses_path) and os.path.getsize(ses_path) > 0:
            return True, f"routed on attempt {attempt}"
    return False, open(log_path).read()[-1500:]


def main(build, sch, here, argv):
    """Board script entry point.
       (no option)  place parts, save the board, write <project>.dsn for routing
       --finish     import <project>.ses, DRC, renders, Gerbers
       --all        both, routing with Freerouting in between"""
    pcb = os.path.join(here, sch.project + ".kicad_pcb")
    dsn = os.path.join(here, sch.project + ".dsn")
    ses = os.path.join(here, sch.project + ".ses")
    if "--finish" not in argv:
        b = build()
        b.save()
        # Route every net, ground included: the autorouter treats a copper pour as one continuous plane and would skip its net,
        # but on a dense board the pour breaks into islands. So the routing copy has no pours; they are poured over the tracks after.
        rb = pcbnew.LoadBoard(pcb)
        for z in list(rb.Zones()):
            if not z.GetIsRuleArea():
                rb.Remove(z)
        apply_net_classes(rb, os.path.join(here, sch.project + ".kicad_pro"))
        pcbnew.ExportSpecctraDSN(rb, dsn)
        print("placed:", pcb)
    if "--all" in argv:
        ok, log = route(dsn, ses)
        print("routed:", ok)
        if not ok:
            print(log)
            raise SystemExit(1)
    if "--finish" in argv or "--all" in argv:
        print(finish(pcb, ses, os.path.join(here, "renders")))
