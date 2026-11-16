#!/usr/bin/env python3
"""Project footprint library terminal-1.pretty: sockets for the plug-in controller boards.

Each footprint is two rows of 2.54 mm female sockets. Pad "numbers" are the signal names on those header positions,
so a schematic pin named "IO4" lands on the right socket hole. Unused positions keep their header name (no net).

Sources (checked 2026-11-14):
  ESP32-S3-DevKitC-1: Espressif dimension drawing PCB_ESP32-S3-DevKitC-1_V1 (25.40 mm wide, pins 1.27 mm from each
      edge -> rows 22.86 mm apart, 2 x 22 pins, pin 1 1.40 mm from the antenna end, 62.74 mm long) and the J1 / J3 tables
      in the ESP32-S3-DevKitC-1 v1.1 user guide.
  ESP32-DevKitC V4: Espressif esp32-devkitc-v4-dimensions.dxf (27.94 x 48.26 mm, rows 25.4 mm apart, 2 x 19 pins)
      and the J2 / J3 tables in the ESP32-DevKitC V4 user guide.
  Seeed XIAO (ESP32-S3 / ESP32-C3): Seeed OPL_Kicad_Library XIAO-ESP32-S3-DIP footprint and symbol (CC-BY-SA-4.0):
      2 x 7 pins, rows 15.24 mm apart; pads 1-7 = D0-D6, 8-11 = D7-D10, 12 = 3V3, 13 = GND, 14 = 5V (VBUS).
Usage: python3 tools/footprints.py <folder>   -> writes <folder>/terminal-1.pretty/*.kicad_mod and <folder>/fp-lib-table
"""
import os
import sys
import uuid

NS = uuid.UUID("2b6f9a10-7c3e-4c55-9f0e-5a1b2c3d4e5f")
P = 2.54

S3_J1 = ["3V3", "3V3", "RST", "IO4", "IO5", "IO6", "IO7", "IO15", "IO16", "IO17", "IO18", "IO8", "IO3", "IO46",
         "IO9", "IO10", "IO11", "IO12", "IO13", "IO14", "5V", "GND"]
S3_J3 = ["GND", "TX", "RX", "IO1", "IO2", "IO42", "IO41", "IO40", "IO39", "IO38", "IO37", "IO36", "IO35", "IO0",
         "IO45", "IO48", "IO47", "IO21", "IO20", "IO19", "GND", "GND"]
V4_J2 = ["3V3", "EN", "VP", "VN", "IO34", "IO35", "IO32", "IO33", "IO25", "IO26", "IO27", "IO14", "IO12", "GND",
         "IO13", "SD2", "SD3", "CMD", "5V"]
V4_J3 = ["GND", "IO23", "IO22", "TX", "RX", "IO21", "GND", "IO19", "IO18", "IO5", "IO17", "IO16", "IO4", "IO0",
         "IO2", "IO15", "SD1", "SD0", "CLK"]
XIAO_A = ["D0", "D1", "D2", "D3", "D4", "D5", "D6"]          # pads 1-7
XIAO_B = ["D7", "D8", "D9", "D10", "3V3", "GND", "5V"]       # pads 8-14


def u(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))


def f(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def line(x1, y1, x2, y2, layer, w, key):
    return (f'\t(fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {w}) (type solid)) '
            f'(layer "{layer}") (uuid "{u(key, x1, y1, x2, y2, layer)}"))')


def rect(x1, y1, x2, y2, layer, w, key):
    return "\n".join([line(x1, y1, x2, y1, layer, w, key), line(x2, y1, x2, y2, layer, w, key),
                      line(x2, y2, x1, y2, layer, w, key), line(x1, y2, x1, y1, layer, w, key)])


def text(kind, s, x, y, layer, key, size=1.0):
    head = f'\t(property "{kind}" "{s}"' if kind in ("Reference", "Value") else f'\t(fp_text user "{s}"'
    return (f'{head} (at {f(x)} {f(y)} 0) (layer "{layer}") (uuid "{u(key, kind, s)}") '
            f'(effects (font (size {size} {size}) (thickness 0.15))))')


def pad(name, x, y, first, key, idx):
    shape = "rect" if first else "circle"
    return (f'\t(pad "{name}" thru_hole {shape} (at {f(x)} {f(y)}) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") '
            f'(remove_unused_layers no) (uuid "{u(key, "pad", idx)}"))')


def model(rows, x, y, rot=0):
    return (f'\t(model "${{KICAD10_3DMODEL_DIR}}/Connector_PinSocket_2.54mm.3dshapes/PinSocket_1x{rows:02d}_P2.54mm_Vertical.step" '
            f'(offset (xyz {f(x)} {f(-y)} 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 {rot})))')


def dual_row(name, desc, colA, colB, spacing, outline, label):
    """Two vertical columns: A at x=0, B at x=spacing; pin 1 of each at y=0, running down (+y)."""
    key = name
    n = len(colA)
    out = [f'(footprint "{name}" (version 20240108) (generator "terminal1_footprints") (generator_version "1.0") (layer "F.Cu")',
           f'\t(descr "{desc}")', '\t(attr through_hole)',
           text("Reference", "REF**", spacing / 2, outline[1] - 1.5, "F.SilkS", key),
           text("Value", name, spacing / 2, (outline[1] + outline[3]) / 2, "F.Fab", key)]
    x0, y0, x1, y1 = outline
    out.append(rect(x0, y0, x1, y1, "F.SilkS", 0.15, key + "silk"))
    out.append(rect(x0 - 0.25, y0 - 0.25, x1 + 0.25, y1 + 0.25, "F.CrtYd", 0.05, key + "crt"))
    out.append(rect(x0, y0, x1, y1, "F.Fab", 0.1, key + "fab"))
    for i, ln in enumerate(label.split("|")):
        out.append(text("user", ln, spacing / 2, y0 + 3.0 + i * 1.5, "F.SilkS", key + str(i), size=0.9))
    for i in range(n):
        out.append(pad(colA[i], 0, i * P, i == 0, key + "A", i))
        out.append(pad(colB[i], spacing, i * P, i == 0, key + "B", i))
    # pin-1 marker
    out.append(line(-1.6, -1.2, -1.6, 1.2, "F.SilkS", 0.2, key + "p1"))
    out.append(model(n, 0, 0))
    out.append(model(n, spacing, 0))
    out.append(")")
    return "\n".join(out)


def xiao(name, desc):
    key = name
    out = [f'(footprint "{name}" (version 20240108) (generator "terminal1_footprints") (generator_version "1.0") (layer "F.Cu")',
           f'\t(descr "{desc}")', '\t(attr through_hole)',
           text("Reference", "REF**", 0, -10.8, "F.SilkS", key), text("Value", name, 0, 0, "F.Fab", key)]
    out.append(rect(-10.5, -8.9, 10.5, 8.9, "F.SilkS", 0.15, key + "silk"))
    out.append(rect(-10.75, -9.15, 10.75, 9.15, "F.CrtYd", 0.05, key + "crt"))
    out.append(text("user", "XIAO (USB end)", 0, -4.5, "F.SilkS", key, size=0.8))
    for i, nm in enumerate(XIAO_A):            # pads 1-7: y = -7.62, x from +7.62 to -7.62 (Seeed geometry)
        out.append(pad(nm, 7.62 - i * P, -7.62, i == 0, key + "A", i))
    for i, nm in enumerate(XIAO_B):            # pads 8-14: y = +7.62, x from -7.62 to +7.62
        out.append(pad(nm, -7.62 + i * P, 7.62, False, key + "B", i))
    out.append(model(7, 7.62, -7.62, 90))
    out.append(model(7, -7.62, 7.62, -90))
    out.append(")")
    return "\n".join(out)


FOOTPRINTS = {
    "ESP32-S3-DevKitC-1_Socket": dual_row(
        "ESP32-S3-DevKitC-1_Socket", "Sockets for Espressif ESP32-S3-DevKitC-1(U): 2 x 22, rows 22.86 mm apart. J1 left, J3 right, antenna end at pin 1",
        S3_J1, S3_J3, 22.86, (-1.27, -1.40, 22.86 + 1.27, -1.40 + 62.74), "ESP32-S3-DevKitC-1|antenna end"),
    "ESP32-DevKitC-V4_Socket": dual_row(
        "ESP32-DevKitC-V4_Socket", "Sockets for Espressif ESP32-DevKitC V4 (32U): 2 x 19, rows 25.4 mm apart. J2 left, J3 right, antenna end at pin 1",
        V4_J2, V4_J3, 25.4, (-1.27, -1.27, 25.4 + 1.27, -1.27 + 48.26), "ESP32-DevKitC V4|antenna end"),
    "Seeed_XIAO_Socket": xiao("Seeed_XIAO_Socket", "Sockets for a Seeed XIAO (ESP32-S3 / ESP32-C3): 2 x 7, rows 15.24 mm apart (Seeed geometry)"),
}


def write(folder):
    lib = os.path.join(folder, "terminal-1.pretty")
    os.makedirs(lib, exist_ok=True)
    for name, body in FOOTPRINTS.items():
        with open(os.path.join(lib, name + ".kicad_mod"), "w") as fh:
            fh.write(body + "\n")
    with open(os.path.join(folder, "fp-lib-table"), "w") as fh:
        fh.write('(fp_lib_table\n  (version 7)\n  (lib (name "terminal-1")(type "KiCad")(uri "${KIPRJMOD}/terminal-1.pretty")(options "")'
                 '(descr "Terminal 1 project footprints"))\n)\n')
    return lib


if __name__ == "__main__":
    print("wrote", write(sys.argv[1] if len(sys.argv) > 1 else "."))
