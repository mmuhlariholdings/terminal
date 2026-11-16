"""Run ngspice from Python through the shared library that ships with KiCad (no install needed), and draw simple SVG plots.

    from spice import run, svg_plot
    vecs, log = run(netlist_text, ["v(out)", "i(vsrc)"])     # dict of name -> list of floats (and the sweep/time axis)

Uses the ngspice shared-library API (ngSpice_Init / ngSpice_Circ / ngSpice_Command / ngGet_Vec_Info).
"""
import ctypes
import html
import math
import os

LIB = "/Applications/KiCad/KiCad.app/Contents/PlugIns/sim/libngspice.0.dylib"

_SendChar = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
_SendStat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
_Exit = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
_SendData = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
_SendInit = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)
_BGRun = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)


class _VecInfo(ctypes.Structure):
    _fields_ = [("v_name", ctypes.c_char_p), ("v_type", ctypes.c_int), ("v_flags", ctypes.c_short),
                ("v_realdata", ctypes.POINTER(ctypes.c_double)), ("v_compdata", ctypes.POINTER(ctypes.c_double)),
                ("v_length", ctypes.c_int)]


_lib = None
_log = []
_keep = []


def _init():
    global _lib
    if _lib:
        return _lib
    _lib = ctypes.CDLL(LIB)
    cbs = [_SendChar(lambda s, i, u: (_log.append(s.decode(errors="replace")), 0)[1]),
           _SendStat(lambda s, i, u: 0), _Exit(lambda *a: 0), _SendData(lambda *a: 0), _SendInit(lambda *a: 0), _BGRun(lambda *a: 0)]
    _keep.extend(cbs)
    _lib.ngSpice_Init(*cbs, None)
    _lib.ngGet_Vec_Info.restype = ctypes.POINTER(_VecInfo)
    return _lib


def run(netlist, vectors, analysis_cmd="run"):
    """Load a netlist (text, with its analysis line), run it, return ({vector: [values]}, log text).
    For AC analyses each value is the magnitude; ask for "frequency" to get the axis."""
    lib = _init()
    _log.clear()
    lines = [ln for ln in netlist.strip().split("\n")] + [".end"]
    arr = (ctypes.c_char_p * (len(lines) + 1))(*[ln.encode() for ln in lines], None)
    lib.ngSpice_Circ(arr)
    lib.ngSpice_Command(analysis_cmd.encode())
    out = {}
    for v in vectors:
        p = lib.ngGet_Vec_Info(v.encode())
        if not p:
            raise RuntimeError(f"no vector {v}\n" + "".join(_log[-30:]))
        info = p.contents
        n = info.v_length
        if info.v_realdata:
            out[v] = [info.v_realdata[i] for i in range(n)]
        else:      # complex: magnitude
            out[v] = [math.hypot(info.v_compdata[2 * i], info.v_compdata[2 * i + 1]) for i in range(n)]
    lib.ngSpice_Command(b"destroy all")
    lib.ngSpice_Command(b"remcirc")
    return out, "\n".join(_log)


def svg_plot(path, series, xlabel, ylabel, title, logx=False, xfmt=None, yfmt=None, hlines=(), w=720, h=380):
    """Minimal line chart. series: [(label, xs, ys, colour)]. hlines: [(y, label)] dashed reference lines."""
    ml, mr, mt, mb = 70, 20, 36, 52
    xs_all = [x for _, xs, _, _ in series for x in xs]
    ys_all = [y for _, _, ys, _ in series for y in ys] + [y for y, _ in hlines]
    fx = (lambda x: math.log10(x)) if logx else (lambda x: x)
    x0, x1 = fx(min(xs_all)), fx(max(xs_all))
    y0, y1 = min(ys_all), max(ys_all)
    pad = (y1 - y0) * 0.06 or 1
    y0, y1 = y0 - pad, y1 + pad
    X = lambda x: ml + (fx(x) - x0) / ((x1 - x0) or 1) * (w - ml - mr)   # noqa: E731
    Y = lambda y: mt + (1 - (y - y0) / ((y1 - y0) or 1)) * (h - mt - mb)  # noqa: E731
    xfmt = xfmt or (lambda v: f"{v:.3g}")
    yfmt = yfmt or (lambda v: f"{v:.3g}")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="Barlow, Arial, sans-serif" font-size="12">',
         f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
         f'<text x="{ml}" y="20" font-size="14" font-weight="700">{html.escape(title)}</text>']
    for i in range(6):     # grid and ticks
        yv = y0 + (y1 - y0) * i / 5
        o.append(f'<line x1="{ml}" x2="{w - mr}" y1="{Y(yv):.1f}" y2="{Y(yv):.1f}" stroke="#e3e3e0"/>'
                 f'<text x="{ml - 6}" y="{Y(yv) + 4:.1f}" text-anchor="end" fill="#555">{html.escape(yfmt(yv))}</text>')
        if logx:
            xv = 10 ** (x0 + (x1 - x0) * i / 5)
        else:
            xv = x0 + (x1 - x0) * i / 5
        o.append(f'<line y1="{mt}" y2="{h - mb}" x1="{X(xv):.1f}" x2="{X(xv):.1f}" stroke="#eeeeec"/>'
                 f'<text x="{X(xv):.1f}" y="{h - mb + 16}" text-anchor="middle" fill="#555">{html.escape(xfmt(xv))}</text>')
    for yv, lab in hlines:
        o.append(f'<line x1="{ml}" x2="{w - mr}" y1="{Y(yv):.1f}" y2="{Y(yv):.1f}" stroke="#b3261e" stroke-dasharray="5 4"/>'
                 f'<text x="{w - mr - 4}" y="{Y(yv) - 4:.1f}" text-anchor="end" fill="#b3261e">{html.escape(lab)}</text>')
    for k, (lab, xs, ys, col) in enumerate(series):
        pts = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in zip(xs, ys))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"/>')
        o.append(f'<rect x="{ml + 8 + k * 170}" y="{h - 18}" width="14" height="4" fill="{col}"/>'
                 f'<text x="{ml + 26 + k * 170}" y="{h - 12}">{html.escape(lab)}</text>')
    o.append(f'<text x="{(ml + w - mr) / 2}" y="{h - 26}" text-anchor="middle" fill="#333">{html.escape(xlabel)}</text>')
    o.append(f'<text transform="translate(16 {(mt + h - mb) / 2}) rotate(-90)" text-anchor="middle" fill="#333">{html.escape(ylabel)}</text>')
    o.append(f'<rect x="{ml}" y="{mt}" width="{w - ml - mr}" height="{h - mt - mb}" fill="none" stroke="#999"/></svg>')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write("\n".join(o))
