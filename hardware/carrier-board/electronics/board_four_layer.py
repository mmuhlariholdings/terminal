"""Four-layer additions to the shared board builder tools/pcbgen.py, for the CM4 carrier board only.

tools/pcbgen.py is shared with the keyboard board and written for 2-layer boards (net classes without differential pairs,
Gerbers for F/B copper only, ground pours on the outer layers). This module wraps it rather than editing it:

  - four copper layers with JLCPCB's JLC04161H-7628 stack-up written into the board file,
  - net classes with differential-pair width and gap (DSI 100 ohm, USB 90 ohm) and design rules for JLCPCB's 4-layer process,
  - planes on the inner layers (In1.Cu ground, In2.Cu +5V_CM4),
  - rule areas (copper keep-outs) and a routing copy that keeps the autorouter out of the high-speed corridors,
  - Gerbers for all four copper layers.

Runs inside KiCad's own Python (pcbnew). Used by generate_pcb.py.
"""
import json
import os
import re
import shutil
import subprocess

import pcbnew

import pcbgen

MM = pcbnew.FromMM

# JLCPCB JLC04161H-7628, 1.6 mm (JLCPCB's published stack-up; check the current figures on jlcpcb.com before ordering)
STACKUP = [  # (KiCad layer name, type, thickness mm, material, relative permittivity)
    ("F.Cu", "copper", 0.035, None, None),
    ("dielectric 1", "prepreg", 0.2104, "7628", 4.4),
    ("In1.Cu", "copper", 0.0152, None, None),
    ("dielectric 2", "core", 1.065, "FR4", 4.6),
    ("In2.Cu", "copper", 0.0152, None, None),
    ("dielectric 3", "prepreg", 0.2104, "7628", 4.4),
    ("B.Cu", "copper", 0.035, None, None),
]


def make_four_layer(board):
    """Switch a fresh pcbnew BOARD to four copper layers; the inner layers are planes."""
    board.SetCopperLayerCount(4)
    ls = board.GetEnabledLayers()
    ls.AddLayer(pcbnew.In1_Cu); ls.AddLayer(pcbnew.In2_Cu)
    board.SetEnabledLayers(ls)
    for layer in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        board.SetLayerType(layer, pcbnew.LT_POWER)
    board.SetLayerName(pcbnew.In1_Cu, "In1.Cu")
    board.SetLayerName(pcbnew.In2_Cu, "In2.Cu")
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))


def write_stackup(pcb_path):
    """Put the physical stack-up (thicknesses, permittivity) into the saved board file, so KiCad's impedance tools and the
    fabrication notes see it. Text edit: the stack-up isn't reachable from pcbnew's Python API in a stable way."""
    text = open(pcb_path, encoding="utf-8").read()
    text = re.sub(r"\n\s*\(stackup(?:[^()]|\((?:[^()]|\((?:[^()]|\([^()]*\))*\))*\))*\)", "", text)
    rows = ['\t\t(stackup', '\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))', '\t\t\t(layer "F.Paste" (type "Top Solder Paste"))',
            '\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))']
    for name, kind, t, mat, er in STACKUP:
        if kind == "copper":
            rows.append(f'\t\t\t(layer "{name}" (type "copper") (thickness {t}))')
        else:
            rows.append(f'\t\t\t(layer "{name}" (type "{kind}") (thickness {t}) (material "{mat}") (epsilon_r {er}) (loss_tangent 0.02))')
    rows += ['\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))', '\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))',
             '\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))', '\t\t\t(copper_finish "ENIG")', '\t\t\t(dielectric_constraints no)', '\t\t)']
    text = text.replace("(setup", "(setup\n" + "\n".join(rows), 1)
    open(pcb_path, "w", encoding="utf-8").write(text)


def write_net_classes(pro_path, classes, patterns):
    """Net classes in the project file. classes: {name: dict(track_width, clearance, via_diameter, via_drill,
    diff_pair_width, diff_pair_gap)}; patterns: [(net-name pattern, class)]. Default must be in classes."""
    data = json.load(open(pro_path)) if os.path.exists(pro_path) else {}
    base = {"clearance": 0.127, "via_diameter": 0.5, "via_drill": 0.3, "diff_pair_gap": 0.18, "diff_pair_width": 0.2,
            "diff_pair_via_gap": 0.25, "microvia_diameter": 0.3, "microvia_drill": 0.1, "wire_width": 6, "bus_width": 12,
            "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647}
    out = []
    for i, (name, c) in enumerate(classes.items()):
        d = dict(base, name=name, **c)
        if name != "Default":
            d["priority"] = i
        out.append(d)
    data["net_settings"] = {"classes": out, "meta": {"version": 4},
                            "netclass_patterns": [{"netclass": c, "pattern": "/" + p} for p, c in patterns]}
    sev = data.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rule_severities", {})
    # cosmetic silkscreen checks only (references on packed parts are hidden; the board house trims silk off pads)
    sev.update({"silk_edge_clearance": "ignore", "silk_over_copper": "ignore", "silk_overlap": "ignore"})
    rules = data["board"]["design_settings"].setdefault("rules", {})
    rules.update({"min_track_width": 0.09, "min_clearance": 0.09, "min_via_diameter": 0.45, "min_through_hole_diameter": 0.2,
                  "min_via_annular_width": 0.1, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.2, "min_hole_to_hole": 0.25,
                  "min_microvia_diameter": 0.3, "min_microvia_drill": 0.1})
    with open(pro_path, "w") as fh:
        json.dump(data, fh, indent=2)


def apply_net_classes(board, pro_path):
    """As pcbgen.apply_net_classes, plus the differential-pair width and gap (used by KiCad's diff-pair router)."""
    data = json.load(open(pro_path))["net_settings"]
    ns = board.GetDesignSettings().m_NetSettings
    for c in data["classes"]:
        nc = ns.GetDefaultNetclass() if c["name"] == "Default" else pcbnew.NETCLASS(c["name"])
        if c["name"] != "Default":
            nc.SetPriority(c.get("priority", 0))
        nc.SetTrackWidth(MM(c["track_width"])); nc.SetClearance(MM(c["clearance"]))
        nc.SetViaDiameter(MM(c["via_diameter"])); nc.SetViaDrill(MM(c["via_drill"]))
        nc.SetDiffPairWidth(MM(c["diff_pair_width"])); nc.SetDiffPairGap(MM(c["diff_pair_gap"]))
        if c["name"] != "Default":
            ns.SetNetclass(c["name"], nc)
    for a in data.get("netclass_patterns", []):
        ns.SetNetclassPatternAssignment(a["pattern"], a["netclass"])
    ns.ClearAllCaches()
    for net in board.GetNetInfo().NetsByName().values():
        net.SetNetClass(ns.GetEffectiveNetClass(net.GetNetname()))


def write_rules(folder, project, rules=""):
    """Project design rules: pcbgen's thermal-spoke rule plus our own."""
    pcbgen.write_rules(folder, project)
    with open(os.path.join(folder, project + ".kicad_dru"), "a") as fh:
        fh.write(rules)


def plane(b, net, layer, inset=0.5, priority=0, thermal=True):
    """Copper zone over the whole board on one layer (b = pcbgen.Board)."""
    z = pcbnew.ZONE(b.board)
    z.SetLayer(layer); z.SetNet(b.net(net))
    z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2))
    z.SetAssignedPriority(priority)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(MM(0.25)); z.SetThermalReliefSpokeWidth(MM(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline(); ol.NewOutline()
    for x, y in ((inset, inset), (b.w - inset, inset), (b.w - inset, b.h - inset), (inset, b.h - inset)):
        ol.Append(MM(x), MM(y))
    b.board.Add(z)
    return z


def keepout(board, rect, layers, name, tracks=True, vias=True, zones=False, footprints=False):
    """Rule area (KiCad keep-out) over rect = (x0, y0, x1, y1) mm on the given copper layers."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowPads(False)
    z.SetDoNotAllowZoneFills(zones); z.SetDoNotAllowFootprints(footprints)
    ls = pcbnew.LSET()
    for layer in layers:
        ls.AddLayer(layer)
    z.SetLayerSet(ls)
    ol = z.Outline(); ol.NewOutline()
    x0, y0, x1, y1 = rect
    for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(MM(px), MM(py))
    board.Add(z)
    return z


def silk_rect(board, rect, layer, width=0.15):
    x0, y0, x1, y1 = rect
    for a, c in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer); s.SetWidth(MM(width))
        s.SetStart(pcbgen.v(*a)); s.SetEnd(pcbgen.v(*c)); board.Add(s)


def place_to_match(b, ref, targets, side="top", tolerance=0.01):
    """Place a footprint so that its pads land on given board positions: targets = {pad number: (x, y) mm}.
    Tries the four rotations, moves the footprint so the first target pad matches, and checks every target pad.
    Raises if no rotation matches: the footprint's pad numbering does not agree with the targets."""
    first = next(iter(targets))
    for rot in (0, 90, 180, 270):
        fp = b.place(ref, 0, 0, rot, side=side) if ref not in b.fps else b.fps[ref]
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        pads = {p.GetNumber(): p for p in fp.Pads()}
        p = pads[str(first)].GetPosition()
        tx, ty = targets[first]
        pos = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(pos.x + MM(tx) - p.x, pos.y + MM(ty) - p.y))
        worst = 0.0
        for num, (x, y) in targets.items():
            q = pads[str(num)].GetPosition()
            worst = max(worst, abs(pcbnew.ToMM(q.x) - x), abs(pcbnew.ToMM(q.y) - y))
        if worst <= tolerance:
            return fp, rot, worst
    raise SystemExit(f"{ref}: no rotation puts its pads on the target positions (worst error {worst:.3f} mm)")


def routing_copy(pcb_path, dsn_path, pro_path, skip_nets, corridors):
    """Write the Specctra DSN the autorouter works on: the saved board without outer-layer pours, with the high-speed nets
    taken off their pads (the autorouter then treats those pads as obstacles and leaves the nets for hand routing) and
    with rule areas over the corridors reserved for them. The inner planes stay, so ground and +5V pads get vias to them."""
    rb = pcbnew.LoadBoard(pcb_path)
    for z in list(rb.Zones()):
        if not z.GetIsRuleArea() and z.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
            rb.Remove(z)
    skip = {"/" + n for n in skip_nets}
    for fp in rb.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() in skip:
                pad.SetNetCode(0)
    for name, rect, layers in corridors:
        keepout(rb, rect, layers, name)
    apply_net_classes(rb, pro_path)
    pcbnew.ExportSpecctraDSN(rb, dsn_path)
    return rb


def export_fab(pcb_path, outdir, zip_name, note=""):
    """Gerbers for all four copper layers, masks, silkscreens, paste and outline; Excellon drill; one zip."""
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        os.remove(os.path.join(outdir, f))
    layers = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts"
    subprocess.run([pcbgen.KICAD_CLI, "pcb", "export", "gerbers", "-o", outdir + "/", "--layers", layers, "--subtract-soldermask",
                    pcb_path], capture_output=True, text=True)
    subprocess.run([pcbgen.KICAD_CLI, "pcb", "export", "drill", "-o", outdir + "/", "--format", "excellon", "--drill-origin",
                    "absolute", "--excellon-units", "mm", "--generate-map", "--map-format", "pdf", pcb_path],
                   capture_output=True, text=True)
    if note:
        with open(os.path.join(outdir, "NOT-FOR-ORDER.txt"), "w") as fh:
            fh.write(note)
    files = sorted(os.listdir(outdir))
    zipbase = os.path.join(os.path.dirname(outdir), zip_name)
    shutil.make_archive(zipbase, "zip", outdir)
    return files, zipbase + ".zip"


def _pad_distance(pad, x, y):
    """Distance (mm) from point (x, y) to the edge of a pad, treating the pad as its (rotated) rectangle; 0 inside."""
    import math
    c = pad.GetPosition()
    sx, sy = pcbnew.ToMM(pad.GetSize().x) / 2, pcbnew.ToMM(pad.GetSize().y) / 2
    a = -math.radians(pad.GetOrientation().AsDegrees())
    dx, dy = x - pcbnew.ToMM(c.x), y - pcbnew.ToMM(c.y)
    lx = dx * math.cos(a) - dy * math.sin(a)
    ly = dx * math.sin(a) + dy * math.cos(a)
    return math.hypot(max(abs(lx) - sx, 0.0), max(abs(ly) - sy, 0.0))


def plane_fanout(b, nets, avoid_rects, via=(0.45, 0.25), track=0.2, clearance=0.15, edge=0.8, skip_refs=()):
    """Give every surface pad on `nets` its own via to the inner planes, with a short track: the autorouter knows the planes
    but does not drop vias onto them by itself. For each pad, positions are tried along the pad's long axis (outwards first),
    then across it, at growing distances; the first one clear of every other-net pad, every earlier fan-out via and track,
    the holes, the board edge and the rectangles in avoid_rects is used. Returns (vias added, pads left without one)."""
    import math
    board = b.board
    vd, vdr = via
    pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
    holes = [(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y), pcbnew.ToMM(p.GetDrillSize().x) / 2)
             for p in pads if p.GetDrillSize().x > 0]
    placed_vias, placed_tracks = [], []          # (x, y, net), (x0, y0, x1, y1, layer, net)
    added, missed = 0, []

    def clear_point(x, y, r, net, layers):
        if x < edge or y < edge or x > b.w - edge or y > b.h - edge:
            return False
        for x0, y0, x1, y1 in avoid_rects:
            if x0 - r <= x <= x1 + r and y0 - r <= y <= y1 + r:
                return False
        for hx, hy, hr in holes:
            if math.hypot(x - hx, y - hy) < hr + r + 0.3:
                return False
        for p in pads:
            if p.GetNetname() == net or not any(p.IsOnLayer(l) for l in layers):
                continue
            if _pad_distance(p, x, y) < r + clearance:
                return False
        for vx, vy, vn in placed_vias:
            need = (vd / 2 + r + clearance) if vn != net else (vdr + 0.3)
            if math.hypot(x - vx, y - vy) < need:
                return False
        for x0, y0, x1, y1, layer, tn in placed_tracks:
            if tn == net or layer not in layers:
                continue
            L = math.hypot(x1 - x0, y1 - y0) or 1e-9
            t = max(0.0, min(1.0, ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / L ** 2))
            if math.hypot(x - (x0 + t * (x1 - x0)), y - (y0 + t * (y1 - y0))) < r + track / 2 + clearance:
                return False
        return True

    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        if fp.GetReference() in skip_refs:
            continue
        for pad in fp.Pads():
            net = pad.GetNetname()
            if net not in nets or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            layer = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            px, py = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
            sx, sy = pcbnew.ToMM(pad.GetSize().x), pcbnew.ToMM(pad.GetSize().y)
            ang = math.radians(pad.GetOrientation().AsDegrees())
            long_axis = (0.0, 1.0) if sy >= sx else (1.0, 0.0)
            ax = (long_axis[0] * math.cos(ang) + long_axis[1] * math.sin(ang), -long_axis[0] * math.sin(ang) + long_axis[1] * math.cos(ang))
            # outwards = away from the footprint centre along the long axis
            fc = fp.GetPosition()
            out = 1.0 if (px - pcbnew.ToMM(fc.x)) * ax[0] + (py - pcbnew.ToMM(fc.y)) * ax[1] >= 0 else -1.0
            half_long, half_short = max(sx, sy) / 2, min(sx, sy) / 2
            dirs = [(out * ax[0], out * ax[1], half_long), (-out * ax[0], -out * ax[1], half_long),
                    (ax[1], -ax[0], half_short), (-ax[1], ax[0], half_short)]
            done = False
            for step in range(0, 12):
                for dx, dy, h in dirs:
                    d = h + vd / 2 + 0.12 + 0.15 * step
                    x, y = px + dx * d, py + dy * d
                    if not clear_point(x, y, vd / 2, net, (pcbnew.F_Cu, pcbnew.B_Cu)):
                        continue
                    # the track from the pad edge to the via must also be clear
                    ok = True
                    for k in range(1, 9):
                        tx, ty = px + dx * (h + (d - h) * k / 8), py + dy * (h + (d - h) * k / 8)
                        if not clear_point(tx, ty, track / 2, net, (layer,)):
                            ok = False
                            break
                    if not ok:
                        continue
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pcbgen.v(x, y)); v.SetWidth(MM(vd)); v.SetDrill(MM(vdr))
                    v.SetNet(pad.GetNet()); board.Add(v)
                    t = pcbnew.PCB_TRACK(board)
                    t.SetStart(pad.GetPosition()); t.SetEnd(pcbgen.v(x, y)); t.SetWidth(MM(min(track, 2 * half_short)))
                    t.SetLayer(layer); t.SetNet(pad.GetNet()); board.Add(t)
                    placed_vias.append((x, y, net)); placed_tracks.append((px, py, x, y, layer, net))
                    added += 1
                    done = True
                    break
                if done:
                    break
            if not done:
                missed.append(f"{fp.GetReference()}.{pad.GetNumber()}")
    return added, missed
