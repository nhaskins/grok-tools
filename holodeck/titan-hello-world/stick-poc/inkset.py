"""Shared ink set pieces + paper finish for the stick-figure videos (used by render.py and engine.py)."""
import math
import numpy as np, cv2
from stickfig import *

W, H = 1920, 1080
FLOOR = 880
def stars_field(pen, rect, t, speed, n=170, seed=7, col=PAPER, streak=0.0):
    x0, y0, x1, y1 = rect; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = np.random.default_rng(seed); X = r.uniform(-1, 1, n); Y = r.uniform(-1, 1, n); Z0 = r.uniform(0, 1, n)
    z = (Z0 - speed * t) % 1.0 + 0.05
    for i in range(n):
        sx, sy = cx + X[i] / z[i] * (x1 - x0) * 0.18, cy + Y[i] / z[i] * (y1 - y0) * 0.18
        if not (x0 < sx < x1 and y0 < sy < y1): continue
        rr = 1.2 + 2.2 * (1 - z[i])
        if streak > 0:
            z2 = z[i] + streak * speed
            pen.line([(cx + X[i] / z2 * (x1 - x0) * .18, cy + Y[i] / z2 * (y1 - y0) * .18), (sx, sy)], rr, col, f's{i}', wob=0)
        else:
            pen.dot((sx, sy), rr, col)

def sparkle(pen, c, s, col, sid):
    pen.line([(c[0] - s, c[1]), (c[0] + s, c[1])], 3, col, sid + 'h')
    pen.line([(c[0], c[1] - s * 1.3), (c[0], c[1] + s * 1.3)], 3, col, sid + 'v')
    pen.line([(c[0] - s * .4, c[1] - s * .4), (c[0] + s * .4, c[1] + s * .4)], 2, col, sid + 'd')
    pen.line([(c[0] + s * .4, c[1] - s * .4), (c[0] - s * .4, c[1] + s * .4)], 2, col, sid + 'e')

def webhook(pen, c, ang, s, col, sid):
    ca, sa = math.cos(ang), math.sin(ang)
    T = lambda x, y: (c[0] + (x * ca - y * sa) * s, c[1] + (x * sa + y * ca) * s)
    pen.line([T(-46, 0), T(18, 0)], 4.5, col, sid + 'sh')
    pen.line([T(18, 0)] + [T(18 + 13 * math.cos(a), 13 + 13 * math.sin(a)) for a in np.linspace(-math.pi / 2, math.pi * .62, 9)] + [T(4, 13)], 4.5, col, sid + 'cu')
    pen.line([T(4, 13), T(10, 4), T(14, 15)], 3.5, col, sid + 'ba')
    pen.line([T(-46, 0), T(-58, -9)], 3.5, col, sid + 'f1'); pen.line([T(-46, 0), T(-58, 9)], 3.5, col, sid + 'f2')
    for k in range(3):
        pen.line([T(-74 - k * 22, 0), T(-66 - k * 22, 0)], 3, col, sid + f'tr{k}', wob=0)

def ship(pen, c, s, col=INK, bg=PAPER, sid='ship', facing=-1):
    """Titan-ish starship, 3/4 side view; saucer forward (left when facing=-1)."""
    f = -facing
    P = lambda x, y: (c[0] + x * f * s, c[1] + y * s)
    def capsule(x0, x1, y, h, name):
        r = h / 2
        pts = [(x0 + r - r * math.sin(a), y + r * math.cos(a)) for a in np.linspace(0, math.pi, 10)]   # rounded front
        pts += [(x1 - 6, y - r), (x1, y - r * .5), (x1, y + r * .5), (x1 - 6, y + r)]
        pts = [P(*p) for p in pts]
        pen.fill(pts, bg); pen.line(pts, 4.5, col, sid + name, closed=True)
        pen.circle(P(x0 + r, y), r * .62 * s, 0, fill=col)                                          # bussard
        pen.line([P(x0 + h * 1.4, y), P(x1 - 20, y)], 2.5, col, sid + name + 'g', wob=.4)
    capsule(150, 420, -92, 34, 'nacF')                       # far nacelle
    pen.line([P(90, 30), P(200, -78)], 5, col, sid + 'pyF')
    # secondary hull + neck
    hull = [(110 + 155 * math.cos(a), 52 + 40 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 32)]
    pen.fill([P(*p) for p in hull], bg); pen.line([P(*p) for p in hull], 4.5, col, sid + 'hull', closed=True)
    pen.circle(P(-28, 52), 13 * s, 3, col, sid + 'defl', fill=col)
    neck = [(-30, 10), (40, 18), (80, 30), (20, 30)]
    pen.fill([P(*p) for p in neck], bg); pen.line([P(*p) for p in neck], 4.5, col, sid + 'neck', closed=True)
    pen.line([P(130, 34), P(230, -38)], 5, col, sid + 'pyN')
    capsule(170, 450, -48, 38, 'nacN')                       # near nacelle
    # saucer
    sau = [(-130 + 210 * math.cos(a), -6 + 50 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 44)]
    pen.fill([P(*p) for p in sau], bg); pen.line([P(*p) for p in sau], 5, col, sid + 'sau', closed=True)
    pen.line([P(-130 + 150 * math.cos(a), -6 + 34 * math.sin(a)) for a in np.linspace(0.15, math.pi - .15, 14)], 3, col, sid + 'ring')
    pen.arc(P(-130, -48), 34 * s, 14 * s, 180, 360, 4, col, sid + 'dome')
    for k in range(11):
        a = math.pi * (0.12 + k * 0.07)
        pen.dot(P(-130 + 196 * math.cos(a), -2 + 44 * math.sin(a)), 2.4 * s, col)
    for k in range(5):   # shading hatch under saucer
        x = -230 + k * 40; pen.line([P(x, 34), P(x + 18, 40)], 2.5, col, sid + f'hat{k}')

def console(pen, x0, x1, top, col=INK, sid='con', mirror=False, label=None):
    pts = [(x0, top + 30), (x1 - 10, top), (x1, top + 14), (x1 - 20, FLOOR), (x0 + 20, FLOOR)]
    if mirror: pts = [(x0 + x1 - p[0], p[1]) for p in pts]
    pen.fill(pts, PAPER); pen.line(pts, 5, col, sid, closed=True)
    for k in range(4):
        bx = x0 + 40 + k * (x1 - x0 - 80) / 3
        pen.rect(bx - 8, top + 60, bx + 8, top + 72, 3, col, sid + f'b{k}', fill=col if k % 2 else None)
    pen.line([(x0 + 35, top + 100), (x1 - 35, top + 100)], 3, col, sid + 'slot')
    if label: pen.text(label, ((x0 + x1) / 2, top + 135), 30, col, 'hand')

def chair(pen, x):
    pen.line([(x - 60, 826), (x + 42, 826)], 6, INK, 'seat')
    pen.line([(x - 55, 826), (x - 66, 690), (x - 46, 690), (x - 38, 826)], 5, INK, 'back', closed=True)
    pen.line([(x - 50, 778), (x + 38, 778)], 5, INK, 'arm')
    pen.line([(x - 10, 826), (x - 10, FLOOR)], 6, INK, 'ped'); pen.line([(x - 50, FLOOR), (x + 30, FLOOR)], 6, INK, 'base')


def paper_finish():
    r = np.random.default_rng(1)
    low = cv2.resize(r.normal(0, 1, (34, 60)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vig = (1 - 0.16 * np.clip(d - 0.35, 0, None) ** 1.6).astype(np.float32)
    grains = []
    for i in range(4):
        g = r.normal(0, 5.0, (H, W)).astype(np.float32)
        fib = cv2.GaussianBlur(r.normal(0, 7, (H, W)).astype(np.float32), (0, 0), sigmaX=6, sigmaY=0.6)
        grains.append((g + fib + low * 3)[..., None])
    return vig[..., None], grains


def thoughtcloud(pen, c, rx, ry, t=0.0, sid='cloud', n=12, w=3.0, col=INK, fill=PAPER, seed=4, puffs=(), dip=0.0, boil=0.0):
    """Hand-scribbled thought cloud (opt-in prop, 'Thinking with AI' cover): a bumpy outline of n outward lobes around
    an ellipse, paper-filled so it sits behind figures. puffs = ((x, y, r), ...) small outlined thought circles.
    dip pulls the bottom of the cloud up between the lobes (cover: the cloud's lower edge sags between the heads).
    boil adds a slow breathing wobble to the lobe radii."""
    import math as _m
    rng = np.random.default_rng(seed)
    ang = np.sort((np.arange(n) + rng.uniform(-.28, .28, n)) / n * 2 * _m.pi - _m.pi / 2)
    rad = 1 + rng.uniform(-.07, .07, n) + boil * .02 * np.sin(t * 2.1 + np.arange(n) * 1.7)
    anchors = []
    for a, r in zip(ang, rad):
        dy = -dip * max(0.0, _m.sin(a)) ** 3                    # lift the underside a little
        anchors.append((c[0] + rx * r * _m.cos(a), c[1] + ry * (r * _m.sin(a) + dy)))
    pts = []
    for k in range(n):
        p0 = anchors[k]; p1 = anchors[(k + 1) % n]
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        hl = _m.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 2
        nx, ny = mx - c[0], my - c[1]; nl = _m.hypot(nx, ny) or 1; nx, ny = nx / nl, ny / nl
        bul = hl * (.62 + .2 * rng.uniform())                   # bulge height of this lobe
        for q in np.linspace(0, 1, 12, endpoint=False):
            s_ = _m.sin(_m.pi * q)
            pts.append((p0[0] + (p1[0] - p0[0]) * q + nx * bul * s_, p0[1] + (p1[1] - p0[1]) * q + ny * bul * s_))
    if fill is not None: pen.fill(pts, fill)
    pen.line(pts, w, col, sid, closed=True)
    for j, (x, y, r) in enumerate(puffs):
        pen.circle((x, y), r, w, col, f'{sid}puff{j}', fill=fill)
    return pts
