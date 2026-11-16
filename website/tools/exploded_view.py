"""Generate the exploded technical drawing (inline SVG) for the HARDWARE section of website/public/index.html.
Usage: python3 website/tools/exploded_view.py > /tmp/x.svg, then replace the <svg class="xdraw"> element in index.html.
Styles live in site.css (.xdraw ...).
Device frame from system/plan/interfaces.md: x across (0..84), y along (0..150, USB-C at y=0), z through thickness.
Isometric projection; layers drawn back to front so nearer plates hide the ones behind."""
import math

C, S = math.cos(math.radians(30)), math.sin(math.radians(30))
K = 1.9           # px per mm
OX, OY = 24, 0    # shifted later

def P(x, y, z):
    return ((x + y) * C * K, ((x - y) * S - z) * K)

def rrect(x0, y0, x1, y1, r, n=5):
    pts = []
    corners = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]
    for cx, cy, a0 in corners:
        if r == 0:
            pts.append((cx, cy)); continue
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def hull(points):
    pts = sorted(set((round(a, 2), round(b, 2)) for a, b in points))
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

out = []
allpts = []

def poly(pts, cls):
    allpts.extend(pts)
    d = ' '.join('%.1f,%.1f' % p for p in pts)
    out.append('<polygon class="%s" points="%s"/>' % (cls, d))

def line(a, b, cls):
    allpts.extend([a, b])
    out.append('<line class="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (cls, a[0], a[1], b[0], b[1]))

def slab(plan, z, t, cls='f'):
    """Extruded plan shape: silhouette hull, then top face."""
    top = [P(x, y, z + t) for x, y in plan]
    bot = [P(x, y, z) for x, y in plan]
    poly(hull(top + bot), cls)
    poly(top, cls)

def face(plan, z, cls):
    poly([P(x, y, z) for x, y in plan], cls)

Z = {'back': 0, 'battery': 48, 'boards': 98, 'frame': 148, 'front': 200}
T = {'back': 2.4, 'battery': 9, 'boards': 2, 'frame': 2.4, 'front': 4}
outline = rrect(0, 0, 84, 150, 9)

# assembly axes (behind everything): dash-dot lines through two corners
for (x, y) in [(84, 0), (0, 0), (84, 150)]:
    line(P(x, y, 0), P(x, y, Z['front'] + T['front']), 'ax')

# 5 carbon back with radio window (hatched)
slab(outline, Z['back'], T['back'])
face(rrect(3, 126, 81, 146, 3), Z['back'] + T['back'], 'h')

# 4 battery 855570: 55 x 70 x 8.5, under the keyboard
slab(rrect(14.5, 2, 69.5, 68, 1.5), Z['battery'], T['battery'])
face(rrect(30, 60, 54, 66, 0.8), Z['battery'] + T['battery'], 'f')  # protection PCB strip

# 3 boards: carrier 74x72 (Y 74..146), keyboard board 74x60 (Y 4..64)
zb = Z['boards']
slab(rrect(5, 74, 79, 146, 1), zb, T['boards'])
slab(rrect(14.5, 92, 69.5, 132, 1), zb + T['boards'], 2.2)          # CM4
slab(rrect(24, 104, 38, 118, 0.5), zb + T['boards'] + 2.2, 0.8)      # SoC
slab(rrect(44, 106, 56, 116, 0.5), zb + T['boards'] + 2.2, 0.8)      # RAM
slab(rrect(30, 140, 54, 145, 0.5), zb + T['boards'], 1.4)            # display FPC connector
slab(rrect(5, 4, 79, 64, 1), zb, T['boards'])
slab(rrect(38, 30, 46, 38, 0.3), zb + T['boards'], 0.9)              # RP2040
slab(rrect(36, 4, 48, 10, 1), zb + T['boards'], 1.6)                 # USB-C
slab(rrect(30, 58, 54, 63, 0.5), zb + T['boards'], 1.2)              # FFC connector

# 2 aluminium mid-frame with screen pocket and keyboard cut-outs
zf = Z['frame']
slab(outline, zf, T['frame'])
face(rrect(5, 70, 79, 146, 2), zf + T['frame'], 'f')
face(rrect(9, 12, 75, 50, 2), zf + T['frame'], 'f')

# 1 front: cover glass, square display, nav row, Q20 keys
zt = Z['front']
slab(outline, zt, T['front'])
top = zt + T['front']
face(rrect(5, 66, 79, 146, 3), top, 'f')        # cover glass
face(rrect(7, 71, 77, 141, 0), top, 'd')        # 70 x 70 active area (black)
face(rrect(9, 52, 75, 62, 2), top, 'f')         # nav row
face(rrect(37.5, 53.5, 46.5, 60.5, 2), top, 'f')  # trackpad
for r, (y0, n, x0, w) in enumerate([(41, 10, 9, 6.6), (32, 10, 9, 6.6), (23, 10, 9, 6.6), (14, 5, 9, 13.2)]):
    for i in range(n):
        if r == 3 and i == 2:
            continue
        xa = x0 + i * w
        wid = w * (2 if (r == 3 and i == 1) else 1)
        face(rrect(xa + 0.6, y0 + 0.8, xa + wid - 0.6, y0 + 7.2, 0.8, 2), top, 'k')

# leaders and balloons: anchor on the near (x=84) side face of each layer
labels = [('front', 1, 100), ('frame', 2, 110), ('boards', 3, 120), ('battery', 4, 30), ('back', 5, 90)]
xs = [p[0] for p in allpts]; ys = [p[1] for p in allpts]
minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
bx = maxx + 70
for key, n, y in labels:
    x = {'battery': 69.5, 'boards': 79}.get(key, 84)
    z = Z[key] + T[key] * 0.5
    ax, ay = P(x, y, z)
    out.append('<circle class="dot" cx="%.1f" cy="%.1f" r="2.2"/>' % (ax, ay))
    out.append('<polyline class="ld" points="%.1f,%.1f %.1f,%.1f %.1f,%.1f"/>' % (ax, ay, ax + 18, ay - 18, bx - 13, ay - 18))
    out.append('<circle class="bl" cx="%.1f" cy="%.1f" r="13"/>' % (bx, ay - 18))
    out.append('<text class="bn" x="%.1f" y="%.1f">%d</text>' % (bx, ay - 18 + 4.5, n))

pad = 12
vb = (minx - pad, miny - pad - 20, (bx + 16) - (minx - pad), (maxy + pad) - (miny - pad - 20))
svg = ('<svg class="xdraw" viewBox="%.0f %.0f %.0f %.0f" role="img" aria-labelledby="xdraw-t">'
       '<title id="xdraw-t">Exploded technical drawing of Terminal 1: five layers, numbered 1 to 5 from the front to the back.</title>'
       '<defs><pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
       '<line x1="0" y1="0" x2="0" y2="5" class="hl"/></pattern></defs>' % vb) + ''.join(out) + '</svg>'
print(svg)
