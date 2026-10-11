"""Procedural ink stick-figure rig + wobbly pen (OpenCV, monochrome).

Coordinates: 'world' pixels, y down. A Pen maps world -> screen with a camera
(cx, cy, zoom). Lines "boil": the wobble pattern is reseeded every boil tick
(e.g. floor(t*12)) so strokes shimmer like hand-redrawn animation on twos.

Joint angles are degrees measured from straight DOWN; positive = toward the
figure's facing direction (profile) or outward from the body (front view).
Elbow/knee angles are relative to the parent segment.
"""
import math, zlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

INK = (26, 22, 20)        # BGR
PAPER = (230, 238, 243)   # BGR of RGB(243,238,230)
FONTS = {
    'hand': '/usr/share/fonts/truetype/sand-box/google/Patrick Hand/PatrickHand-Regular.ttf',
    'marker': '/usr/share/fonts/truetype/sand-box/google/Permanent Marker/PermanentMarker-Regular.ttf',
    'arch': '/usr/share/fonts/truetype/sand-box/google/Architects Daughter/ArchitectsDaughter-Regular.ttf',
    'serif': '/usr/share/fonts/truetype/sand-box/google/Crimson Text/CrimsonText-Regular.ttf',   # cover lettering
}

def clamp01(x): return min(max(x, 0.0), 1.0)
def ease(x): x = clamp01(x); return x * x * (3 - 2 * x)
def ease_out(x): x = clamp01(x); return 1 - (1 - x) ** 3
def ease_out_back(x, s=2.2):
    x = clamp01(x) - 1; return 1 + x * x * ((s + 1) * x + s)
def lerp(a, b, k): return a + (b - a) * k

_TXT = {}
def _text_mask(s, font, px):
    key = (s, font, px)
    if key not in _TXT:
        f = ImageFont.truetype(FONTS[font], px)
        l, t, r, b = f.getbbox(s)
        im = Image.new('L', (r - l + 8, b - t + 8), 0)
        ImageDraw.Draw(im).text((4 - l, 4 - t), s, font=f, fill=255)
        _TXT[key] = np.asarray(im, np.float32) / 255.0
        if len(_TXT) > 400: _TXT.clear()
    return _TXT[key]


class Pen:
    def __init__(self, img, cam=(960, 540, 1.0), boil=0, wob=1.0):
        self.img = img; self.H, self.W = img.shape[:2]
        self.cam = cam; self.z = cam[2]; self.boil = boil; self.wob = wob

    def S(self, p):
        cx, cy, z = self.cam
        return ((p[0] - cx) * z + self.W / 2, (p[1] - cy) * z + self.H / 2)

    def rng(self, sid):
        return np.random.default_rng(zlib.crc32(f"{sid}|{self.boil}".encode()))

    def _wobble(self, P, sid, a, closed):
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); L = seg.sum()
        if L < 2 or a <= 0: return P
        s = np.concatenate([[0], np.cumsum(seg)])
        ss = np.unique(np.concatenate([np.linspace(0, L, max(int(L / 14), 2) + 1), s]))
        x = np.interp(ss, s, P[:, 0]); y = np.interp(ss, s, P[:, 1])
        r = self.rng(sid); ph = r.uniform(0, 6.283, 3)
        k1 = 6.283 / r.uniform(140, 300); k2 = 6.283 / r.uniform(40, 90)
        off = a * (1.5 * np.sin(ss * k1 + ph[0]) + 0.55 * np.sin(ss * k2 + ph[1]))
        if closed: off = off - (off[-1] - off[0]) * ss / L   # close the loop
        dx = np.gradient(x); dy = np.gradient(y); nn = np.hypot(dx, dy) + 1e-9
        sh = r.normal(0, a * 0.6, 2)                          # tiny whole-stroke shift
        return np.stack([x - dy / nn * off + sh[0], y + dx / nn * off + sh[1]], 1)

    def line(self, pts, w=5, col=INK, sid='l', wob=None, closed=False):
        if len(pts) < 2: return
        P = np.array([self.S(p) for p in pts], float)
        if closed: P = np.vstack([P, P[:1]])
        a = (self.wob if wob is None else wob) * min(self.z, 2.0) ** 0.5
        P = self._wobble(P, sid, a, closed)
        t = max(1, int(round(w * self.z)))
        cv2.polylines(self.img, [np.round(P * 16).astype(np.int32)], False, col, t, cv2.LINE_AA, shift=4)

    def arc(self, c, rx, ry, a0, a1, w=5, col=INK, sid='a', rot=0, wob=None, n=None):
        n = n or max(8, int(abs(a1 - a0) / 8))
        cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        pts = []
        for k in range(n + 1):
            a = math.radians(lerp(a0, a1, k / n)); x, y = rx * math.cos(a), ry * math.sin(a)
            pts.append((c[0] + x * cr - y * sr, c[1] + x * sr + y * cr))
        self.line(pts, w, col, sid, wob, closed=abs(a1 - a0) >= 359.9)

    def circle(self, c, r, w=5, col=INK, sid='c', fill=None, wob=None):
        if fill is not None: self.fill([(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in np.linspace(0, 6.283, 40)], fill)
        if w > 0: self.arc(c, r, r, 0, 360, w, col, sid, wob=wob)

    def rect(self, x0, y0, x1, y1, w=5, col=INK, sid='r', fill=None, wob=None):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        if fill is not None: self.fill(pts, fill)
        if w > 0: self.line(pts, w, col, sid, wob, closed=True)

    def fill(self, pts, col=INK):
        P = np.array([self.S(p) for p in pts], float)
        cv2.fillPoly(self.img, [np.round(P * 16).astype(np.int32)], col, cv2.LINE_AA, shift=4)

    def dot(self, c, r, col=INK):
        x, y = self.S(c)
        cv2.circle(self.img, (int(round(x * 16)), int(round(y * 16))), max(1, int(round(r * self.z * 16))), col, -1, cv2.LINE_AA, shift=4)

    def text(self, s, c, size, col=INK, font='hand', alpha=1.0, anchor='c'):
        px = max(6, int(round(size * self.z / 2)) * 2)
        m = _text_mask(s, font, px) * alpha
        x, y = self.S(c); h, w = m.shape
        x0 = int(x - w / 2) if anchor == 'c' else int(x); y0 = int(y - h / 2)
        X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x0 + w, self.W), min(y0 + h, self.H)
        if X1 <= X0 or Y1 <= Y0: return
        mm = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None]
        roi = self.img[Y0:Y1, X0:X1].astype(np.float32)
        self.img[Y0:Y1, X0:X1] = (roi * (1 - mm) + np.array(col, np.float32) * mm).astype(np.uint8)


# ---------------------------------------------------------------- rig
SEG = dict(r=23, neck=7, torso=92, ua=46, fa=44, th=56, sh=56)
BASE = dict(lean=0, tilt=0, lsh=-8, lel=12, rsh=12, rel=14, lhip=-8, lkn=-6, rhip=10, rkn=-4,
            look=0, mouth=0, front=0, thumb=0, wave=0, steer=0, clip=0, lookup=0, scrib=0, mic=0, talk=0, pface=0, padd=0)
POSES = {
    'stand':   {},
    'idle':    {'lsh': -4, 'lel': 22, 'rsh': 6, 'rel': 24, 'tilt': 4},
    'point':   {'rsh': 86, 'rel': 2, 'lean': 5, 'lsh': -12, 'lel': 20},
    'pointup': {'rsh': 128, 'rel': 4, 'lsh': 20, 'lel': 30},           # back-view point at a screen
    'pointupL': {'lsh': 128, 'lel': 4, 'rsh': 20, 'rel': 30},
    'tada':    {'lsh': -125, 'lel': -10, 'rsh': 125, 'rel': 10, 'mouth': 1},
    'wave':    {'rsh': 145, 'rel': 22, 'wave': 1, 'mouth': 1},
    'console': {'lsh': 50, 'lel': 40, 'rsh': 60, 'rel': 34, 'lean': 12},
    'steer':   {'lsh': 50, 'lel': 40, 'rsh': 60, 'rel': 34, 'lean': 12, 'steer': 1},
    'thumbs':  {'rsh': 38, 'rel': 92, 'thumb': 1, 'mouth': 1},
    'salute':  {'rsh': 100, 'rel': 122, 'lean': -2},
    'look_l':  {'look': -1, 'tilt': -6},
    'look_r':  {'look': 1, 'tilt': 6},
    'handear': {'rsh': 132, 'rel': 150, 'tilt': -8},
    'sit':     {'lhip': 90, 'lkn': -92, 'rhip': 84, 'rkn': -84, 'lsh': 28, 'lel': 42, 'rsh': 32, 'rel': 46, 'lean': -6},
    'front':   {'front': 1, 'lsh': 14, 'lel': 6, 'rsh': 14, 'rel': 6, 'lhip': 8, 'rhip': 8, 'lkn': 0, 'rkn': 0},
    'grin':    {'front': 1, 'mouth': 2, 'lsh': 42, 'lel': -66, 'rsh': 42, 'rel': -66, 'lhip': 10, 'rhip': 10, 'lkn': 0, 'rkn': 0},
    'plan':    {'front': 1, 'mouth': 2, 'rsh': 58, 'rel': 72, 'clip': 1, 'lsh': -96, 'lel': -24, 'lhip': 10, 'rhip': 10, 'lkn': 0, 'rkn': 0},
    'present': {'front': 1, 'mouth': 1, 'lsh': 118, 'lel': 14, 'rsh': 118, 'rel': 14},
    'surprise': {'front': 1, 'mouth': 3, 'lsh': 155, 'lel': 12, 'rsh': 155, 'rel': 12, 'lookup': 1, 'tilt': 0,
                 'lhip': 10, 'rhip': 10, 'lkn': 0, 'rkn': 0},
    'smile':   {'mouth': 1},
    # --- chorus additions
    'pull':    {'lean': -20, 'lsh': 80, 'lel': 4, 'rsh': 86, 'rel': 2, 'lhip': 24, 'lkn': -4, 'rhip': -16, 'rkn': -12, 'mouth': 3},
    'scribble': {'lean': 16, 'rsh': 55, 'rel': 72, 'scrib': 1, 'lsh': 42, 'lel': 52},
    'mic':     {'rsh': 60, 'rel': 115, 'mic': 1},
    'yawn':    {'lsh': 172, 'lel': 14, 'rsh': 150, 'rel': 18, 'mouth': 3, 'tilt': -12, 'lookup': .6},
    'cheer':   {'front': 1, 'mouth': 2, 'lsh': 152, 'lel': 14, 'rsh': 152, 'rel': 14, 'lhip': 10, 'rhip': 10, 'lkn': 0, 'rkn': 0},
    'trombone': {'rsh': 90, 'rel': 0, 'lsh': 62, 'lel': 70, 'tilt': -6},
    'cards':   {'rsh': 62, 'rel': 48, 'lsh': 55, 'lel': 52},
    'hips':    {'front': 1, 'lsh': 40, 'lel': -95, 'rsh': 40, 'rel': -95, 'lhip': 14, 'rhip': 14, 'lkn': 0, 'rkn': 0, 'mouth': 1, 'lookup': .3},
    # --- dialogue additions (talk = 0..1 mouth opening, driven per frame by voice RMS)
    'chinrub': {'rsh': 30, 'rel': 128, 'tilt': 6, 'lsh': -6, 'lel': 30},           # Riker strokes the beard
    'shrug':   {'front': 1, 'lsh': 48, 'lel': 78, 'rsh': 48, 'rel': 78, 'tilt': 8, 'mouth': 1, 'lhip': 10, 'rhip': 10, 'lkn': 0, 'rkn': 0},
    'palm':    {'rsh': 62, 'rel': 30, 'lsh': -6, 'lel': 22, 'lean': 4},           # open hand offered toward the other speaker
    'proud':   {'lean': -8, 'lsh': 20, 'lel': 110, 'rsh': 20, 'rel': 110, 'lookup': .4, 'mouth': 1},
    'facepalm': {'pface': 1, 'rsh': 100, 'rel': 128, 'tilt': 14, 'lookup': -.4, 'lsh': -6, 'lel': 20},       # profile
    'facepalmF': {'pface': 1, 'front': 1, 'rsh': 110, 'rel': 135, 'lsh': 14, 'lel': 6, 'tilt': -6, 'lookup': -.5,
                  'lhip': 8, 'rhip': 8, 'lkn': 0, 'rkn': 0},                                       # front view, one hand
    'facepalm2': {'pface': 1, 'front': 1, 'rsh': 110, 'rel': 135, 'lsh': 110, 'lel': 135, 'lookup': -.6,
                  'lhip': 8, 'rhip': 8, 'lkn': 0, 'rkn': 0},                                       # both hands
    'legover': {'rhip': 105, 'rkn': -40, 'lhip': -4, 'lsh': 40, 'lel': 30, 'rsh': 50, 'rel': 30, 'lean': -6},   # swing a leg over a chair
    'straddle': {'lhip': 90, 'lkn': -92, 'rhip': 84, 'rkn': -84, 'lsh': 62, 'lel': 30, 'rsh': 66, 'rel': 26, 'lean': 4},  # sat backwards, arms on the chair back
    # --- Barclay (hunched, nervous; padd = PADD in the right hand + stylus in the left)
    'hunch':   {'lean': 9, 'tilt': 10, 'lookup': -.25, 'lsh': 30, 'lel': 70, 'rsh': 36, 'rel': 74, 'padd': 1},
    'present_padd': {'lean': 4, 'tilt': 4, 'rsh': 78, 'rel': 10, 'lsh': 30, 'lel': 60, 'padd': 1, 'mouth': 1},
    'nervous': {'lean': 12, 'tilt': 14, 'lookup': -.4, 'lsh': 48, 'lel': 100, 'rsh': 44, 'rel': 104, 'padd': 1},
    'faint':   {'lean': -88, 'tilt': -8, 'lsh': 150, 'lel': 10, 'rsh': 170, 'rel': 10, 'lhip': 96, 'lkn': 0, 'rhip': 80, 'rkn': -6, 'mouth': 2, 'lookup': .4},
    # --- 'Thinking with AI' cover characters (opt-in)
    'think':   {'rsh': 20, 'rel': 150, 'lsh': -62, 'lel': 112, 'tilt': -6, 'mouth': 1},      # near hand at the chin, far hand on hip
    'kneeup':  {'rhip': 92, 'rkn': -70, 'lhip': -4, 'lkn': -2},                            # near knee lifted mid-step
    'armlink': {'front': 1, 'mouth': 2, 'lsh': 88, 'lel': 4, 'rsh': 88, 'rel': 4, 'lhip': 8, 'rhip': 8, 'lkn': 0, 'rkn': 0},
}

def pose(spec):
    """'sit+thumbs' -> merged dict; dicts pass through (merged over BASE)."""
    d = dict(BASE)
    if isinstance(spec, dict): d.update(spec); return d
    for part in spec.split('+'):
        if '=' in part: k, v = part.split('='); d[k] = float(v)     # inline param, e.g. 'sit+scribble+scrib=1.8'
        else: d.update(POSES[part])
    return d


class Figure:
    """keys: list of (t, pose_spec, transition_seconds). Positions: list of (t, x, y, dur).
    props: set of 'cap', 'beard', 'shine', 'badge', 'ponytail'. facing: +1 right / -1 left."""
    def __init__(self, name, x, y, facing=1, props=(), back=False, col=INK, scale=1.0, seg=None):
        self.seg = dict(SEG, **seg) if seg else SEG
        self.name = name; self.keys = [(-1e9, 'stand', 0.0)]; self.moves = [(-1e9, x, y, 0.0)]
        self.mod = None   # optional callable(t, posedict) -> posedict, for beat-synced overrides (kicks, pulls)
        self.facing = facing; self.props = set(props); self.back = back; self.col = col; self.scale = scale

    def key(self, t, spec, dur=0.25): self.keys.append((t, spec, dur)); self.keys.sort(key=lambda k: k[0]); return self
    def move(self, t, x, y, dur=0.4): self.moves.append((t, x, y, dur)); self.moves.sort(key=lambda k: k[0]); return self

    def pose_at(self, t, i=None):
        if i is None: i = max(j for j, k in enumerate(self.keys) if k[0] <= t)
        t0, spec, dur = self.keys[i]; cur = pose(spec)
        if i == 0 or dur <= 0: return cur
        k = ease((t - t0) / dur)
        if k >= 1: return cur
        prev = self.pose_at(t0, i - 1)
        return {n: lerp(prev[n], cur[n], k) for n in cur}

    def pos_at(self, t):
        i = max(j for j, m in enumerate(self.moves) if m[0] <= t)
        t0, x, y, dur = self.moves[i]
        if i == 0 or dur <= 0: return x, y
        px, py = self.pos_at(t0 - 1e-6)
        k = ease((t - t0) / dur); return lerp(px, x, k), lerp(py, y, k)

    def draw(self, pen, t, bob=0.0, w=5.5, halo=0):
        """halo>0 first strokes the whole figure in the opposite colour, w+halo wide,
        so it reads over busy/dark backgrounds."""
        if halo:
            c0 = self.col; self.col = PAPER if c0 == INK else INK
            self._halo = True; self.draw(pen, t, bob, w + halo); self._halo = False; self.col = c0
        return self._draw(pen, t, bob, w)

    _halo = False
    def _draw(self, pen, t, bob=0.0, w=5.5):
        P = self.pose_at(t); x, y = self.pos_at(t); S = self.scale; f = self.facing
        if self.mod: P = self.mod(t, dict(P))
        sid = f"{self.name}"; col = self.col
        fr = P['front']; ss = -1 if self.back else 1
        lean = P['lean'] + 1.3 * math.sin(t * 2 * math.pi / 3.1 + len(self.name))      # breathing
        y = y + bob * S
        def dirv(a, side, leg=False):       # unit vector for angle a (deg from down)
            sa, ca = math.sin(math.radians(a)), math.cos(math.radians(a))
            fx = f * sa * (1 - fr) + (side * ss * (abs(sa) if leg else sa)) * fr
            return fx, ca
        hip = (x, y)
        ul = math.radians(lean)
        up = (f * math.sin(ul) * (1 - fr), -math.cos(ul))
        sho = (hip[0] + up[0] * self.seg['torso'] * S, hip[1] + up[1] * self.seg['torso'] * S)
        neck = (sho[0] + up[0] * self.seg['neck'] * S, sho[1] + up[1] * self.seg['neck'] * S)
        ht = math.radians(lean + P['tilt'] - 14 * P['lookup'])
        hd = (f * math.sin(ht) * (1 - fr) + math.sin(math.radians(P['tilt'])) * fr * 0.5, -math.cos(ht))
        R = self.seg['r'] * S * P.get('hs', 1.0)          # hs: head scale (CONTEXT WINDOW gag)
        head = (neck[0] + hd[0] * R, neck[1] + hd[1] * R)
        # limbs
        wave = P['wave'] * 24 * math.sin(t * 2 * math.pi * 2.6)
        st = P['steer'] * 9 * math.sin(t * 2 * math.pi * 1.1)
        sc = P['scrib'] * math.sin(t * 2 * math.pi * 7.0)       # furious scribbling
        P['rsh'] += sc * 7; P['rel'] += P['scrib'] * 10 * math.sin(t * 2 * math.pi * 9.3 + 1)
        limbs = {}
        cust = ('boxbot' in self.props) or ('bean' in self.props)        # opt-in cover-character bodies
        CG = self._cust_geom(hip, sho, neck, up, P, f, S) if cust else None
        rs = 'redshirt' in self.props and not self._halo
        if rs:      # "red" shirt: ink can't do colour, so a solid ink tunic (arms get a paper halo to read over it)
            px, py = -up[1], up[0]; ws, wh = (12 + 8 * fr) * S, (10 + 6 * fr) * S
            top = (sho[0] - up[0] * 4 * S, sho[1] - up[1] * 4 * S); bot = (hip[0] - up[0] * 8 * S, hip[1] - up[1] * 8 * S)
            tun = [(top[0] - px * ws * .55, top[1] - py * ws * .55), (top[0] + px * ws * .55, top[1] + py * ws * .55),
                   (sho[0] + px * ws + up[0] * -10 * S, sho[1] + py * ws + up[1] * -10 * S), (bot[0] + px * wh, bot[1] + py * wh),
                   (bot[0] - px * wh, bot[1] - py * wh), (sho[0] - px * ws + up[0] * -10 * S, sho[1] - py * ws + up[1] * -10 * S)]
            pen.fill(tun, col); pen.line(tun, w * .8, col, sid + 'tunic', closed=True)
            ox = f * (1 - fr) * 3 * S; bx, by = sho[0] + ox + (5 * S if fr > .5 else 0), sho[1] + 20 * S   # paper delta badge
            pen.fill([(bx, by - 8 * S), (bx + 5.5 * S, by + 7 * S), (bx, by + 2 * S), (bx - 5.5 * S, by + 7 * S)], PAPER)
        for side, a1, a2, L1, L2, root, leg in (
                (-1, P['lsh'] + st, P['lel'], self.seg['ua'], self.seg['fa'], sho, False),
                (+1, P['rsh'] - st, P['rel'] + wave, self.seg['ua'], self.seg['fa'], sho, False),
                (-1, P['lhip'], P['lkn'], self.seg['th'], self.seg['sh'], hip, True),
                (+1, P['rhip'], P['rkn'], self.seg['th'], self.seg['sh'], hip, True)):
            if cust: root = CG['roots'][(side, leg)]
            v1 = dirv(a1, side, leg); j = (root[0] + v1[0] * L1 * S, root[1] + v1[1] * L1 * S)
            v2 = dirv(a1 + a2, side, leg); e = (j[0] + v2[0] * L2 * S, j[1] + v2[1] * L2 * S)
            limbs[(side, leg)] = (root, j, e)
            if rs and not leg: pen.line([root, j, e], w + 5 * S ** .5, PAPER, f"{sid}{side}{leg}")
            if not cust: pen.line([root, j, e], w, col, f"{sid}{side}{leg}")
        if rs:      # re-ink the sleeves over the halo so the shirt keeps its shoulders
            for sd in (-1, 1):
                r0, j, _ = limbs[(sd, False)]; m = (lerp(r0[0], j[0], .38), lerp(r0[1], j[1], .38))
                pen.line([r0, m], w + 6 * S ** .5, col, f"{sid}{sd}slv")
        if not cust: pen.line([hip, sho, neck], w, col, sid + 'torso')
        # head
        hfill = PAPER if (col == INK) != self._halo else INK
        if cust:
            head, R = self._cust_draw(pen, t, CG, limbs, head, R, P, f, S, w, col, hfill, sid)
        elif 'robot' in self.props:       # Grok Bot: boxy head + antenna
            pen.line([(head[0], head[1] - R), (head[0] + 4 * S, head[1] - R * 1.7)], w * .8, col, sid + 'ant')
            pen.circle((head[0] + 4 * S, head[1] - R * 1.8), 5 * S, 0, fill=col)
            pen.rect(head[0] - R, head[1] - R * .95, head[0] + R, head[1] + R * .95, w, col, sid + 'head', fill=hfill)
        else:
            pen.circle(head, R, w, col, sid + 'head', fill=hfill)
        if not self.back and not self._halo and 'boxbot' not in self.props:
            self._face(pen, head, R, P, f, fr, col, sid)
        self._props(pen, head, R, sho, up, P, f, fr, col, sid, w)
        for sd in (-1, 1):       # a hand on the face (facepalm) would hide under the head fill: redraw it on top
            r0, el, hd_ = limbs[(sd, False)]
            if P['pface'] > 0.5 and math.hypot(hd_[0] - head[0], hd_[1] - head[1]) < R * 0.95:
                pen.line([el, hd_], w, col, f"{sid}{sd}fp")
                pen.circle(hd_, R * 0.4, w * .6, col, f"{sid}{sd}palm", fill=PAPER if (col == INK) != self._halo else INK)
        hand = limbs[(1, False)][2]
        if P['thumb'] > 0.5:
            pen.circle(hand, 5 * S, 0, fill=col)
            pen.line([hand, (hand[0] + 2 * f * S, hand[1] - 15 * S)], w * 0.9, col, sid + 'thumb')
        if P['padd'] > 0.5:       # PADD (right hand) + stylus (left hand)
            pw, ph = 22 * S, 32 * S
            pts = [(hand[0] - pw / 2, hand[1] - ph), (hand[0] + pw / 2, hand[1] - ph), (hand[0] + pw / 2, hand[1] + 4 * S), (hand[0] - pw / 2, hand[1] + 4 * S)]
            pen.fill(pts, PAPER if col == INK else INK); pen.line(pts, w * .7, col, sid + 'padd', closed=True)
            pen.rect(hand[0] - pw / 2 + 4 * S, hand[1] - ph + 5 * S, hand[0] + pw / 2 - 4 * S, hand[1] - ph * .35, 0, fill=col)
            hl = limbs[(-1, False)][2]
            pen.line([hl, (hl[0] + 4 * f * S, hl[1] - 16 * S)], w * .5, col, sid + 'styl')
        if P['mic'] > 0.5:        # handheld log recorder
            pen.rect(hand[0] - 6 * S, hand[1] - 16 * S, hand[0] + 6 * S, hand[1] + 6 * S, w * .7, col, sid + 'mic', fill=col)
        if P['clip'] > 0.3:
            k = clamp01((P['clip'] - 0.3) / 0.7)
            cx, cy = hand[0] + 30 * S * ss, hand[1] - 50 * S * k
            bw, bh = 64 * S * k + 1, 84 * S * k + 1
            pen.rect(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2, w * 0.8, col, sid + 'clip', fill=PAPER if col == INK else INK)
            if k > 0.8:
                pen.rect(cx - 12 * S, cy - bh / 2 - 5 * S, cx + 12 * S, cy - bh / 2 + 5 * S, 0, fill=col)
                # doodled plan: start dot, dashed path, X marks the spot
                path = [(cx - 22 * S, cy + 26 * S), (cx - 8 * S, cy + 8 * S), (cx + 6 * S, cy + 18 * S), (cx + 14 * S, cy - 8 * S)]
                pen.line(path, 3, col, sid + 'plan')
                pen.dot(path[0], 4 * S, col)
                X = (cx + 16 * S, cy - 20 * S)
                pen.line([(X[0] - 8 * S, X[1] - 8 * S), (X[0] + 8 * S, X[1] + 8 * S)], 3.5, col, sid + 'x1')
                pen.line([(X[0] + 8 * S, X[1] - 8 * S), (X[0] - 8 * S, X[1] + 8 * S)], 3.5, col, sid + 'x2')
        return dict(head=head, sho=sho, hip=hip, hand_r=hand, hand_l=limbs[(-1, False)][2], R=R)

    # ------------------------------------------------ opt-in cover-character bodies ('boxbot', 'bean')
    BOX = dict(bw=66, bh=110, dx=48, dy=15, hw=50, hh=60, hdx=42, hdy=18, neck=9)     # boxbot proportions (x scale)
    def _cust_geom(self, hip, sho, neck, up, P, f, S):
        px = (-up[1], up[0])                                     # screen-right when upright
        A = lambda p, u, v: (p[0] + up[0] * u * S + px[0] * v * S, p[1] + up[1] * u * S + px[1] * v * S)
        if 'boxbot' in self.props:
            B = self.BOX; bw, bh = B['bw'], B['bh']; d = (-f * B['dx'] * S, -B['dy'] * S)
            fl, fr_ = A(hip, 0, -bw / 2), A(hip, 0, bw / 2)                      # front face (toward facing)
            tl, tr = A(hip, bh, -bw / 2), A(hip, bh, bw / 2)
            front = [fl, fr_, tr, tl]
            back_e = (fl, tl) if f > 0 else (fr_, tr)                            # edge the depth hangs off
            side = [back_e[0], back_e[1], (back_e[1][0] + d[0], back_e[1][1] + d[1]), (back_e[0][0] + d[0], back_e[0][1] + d[1])]
            top = [tl, tr, (tr[0] + d[0], tr[1] + d[1]), (tl[0] + d[0], tl[1] + d[1])]
            topc = A(hip, bh, 0); topc = (topc[0] + d[0] * .45, topc[1] + d[1] * .45)
            roots = {(-1, False): A(hip, bh - 10, -f * bw * .05), (1, False): A(hip, bh - 22, f * bw * .5),
                     (-1, True): A(hip, 0, -f * bw * .48), (1, True): A(hip, 0, f * bw * .02)}
            roots[(-1, True)] = (roots[(-1, True)][0] + d[0] * .25, roots[(-1, True)][1] + d[1] * .25)
            return dict(kind='box', front=front, side=side, top=top, topc=topc, roots=roots, px=px, A=A)
        L = math.hypot(sho[0] - hip[0], sho[1] - hip[1]) / S                     # bean: puffy torso outline
        roots = {(-1, False): A(sho, -22, -f * 30), (1, False): A(sho, -18, f * 10),
                 (-1, True): A(hip, 4, -f * 9), (1, True): A(hip, 4, f * 7)}
        return dict(kind='bean', L=L, roots=roots, px=px, A=A)

    def _cust_draw(self, pen, t, CG, limbs, head, R, P, f, S, w, col, hfill, sid):
        """Draw order: legs + far arm, body, near arm, head (+ accessories). Thin single-weight ink, paper fills."""
        A = CG['A']; px = CG['px']; up = (-px[1] * -1, px[0] * -1) if False else None
        def limb(k):
            r0, j, e = limbs[k]; pen.line([r0, j, e], w, col, f"{sid}{k[0]}{k[1]}")
            if k[1] and 'shoes' in self.props:          # oval shoe, toe forward
                c = (e[0] + self.facing * 7 * S, e[1] + 2 * S)
                pen.fill([(c[0] + 12 * S * math.cos(a), c[1] + 6 * S * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 20)], hfill)
                pen.arc(c, 12 * S, 6 * S, 0, 360, w, col, f"{sid}shoe{k[0]}")
            if k[1] and 'feet' in self.props:           # short stick feet, splayed
                pen.line([e, (e[0] + k[0] * self.facing * 11 * S, e[1])], w, col, f"{sid}foot{k[0]}")
        for k in ((-1, True), (1, True)): limb(k)
        if CG['kind'] == 'box':
            for nm in ('side', 'top', 'front'):
                pen.fill(CG[nm], hfill); pen.line(CG[nm], w, col, sid + 'box' + nm, closed=True)
            limb((-1, False)); limb((1, False))
            B = self.BOX; tc = CG['topc']
            n0 = tc; n1 = A(tc, B['neck'], 0)                                       # neck: two short strokes
            for o in (-5, 5): pen.line([A(n0, 0, o), A(n1, 0, o)], w * .8, col, sid + f'nk{o}')
            ht = math.radians(P['tilt'] * .6)
            ca, sa = math.cos(ht), math.sin(ht)
            hc = A(n1, B['hh'] / 2, f * 6)
            def H(u, v):                                                           # head-local (u up, v right) -> screen
                uu, vv = u * ca - v * sa * f, v * ca + u * sa * f
                return A(hc, uu, vv)
            hw, hh = B['hw'] / 2, B['hh'] / 2; d = (-f * B['hdx'], B['hdy'])
            fl, fr_, tr, tl = H(-hh, -hw), H(-hh, hw), H(hh, hw), H(hh, -hw)
            be = (fl, tl, -hh, -hw) if f > 0 else (fr_, tr, -hh, hw)
            side = [be[0], be[1], H(hh + d[1], be[3] + d[0]), H(-hh + d[1], be[3] + d[0])]
            top = [tl, tr, H(hh + d[1], hw + d[0]), H(hh + d[1], -hw + d[0])]
            for nm, Q in (('hs', side), ('ht', top), ('hf', [fl, fr_, tr, tl])):
                pen.fill(Q, hfill); pen.line(Q, w, col, sid + nm, closed=True)
            # face on the front face: dot eyes + smile
            lk = P['look'] * hw * .15
            for k, ev in enumerate((-.1, .42)):
                pen.dot(H(hh * .28, f * hw * ev + lk), 2.4 * S, col)
            tk = P.get('talk', 0)
            if tk > 0.06:                                                         # talking: open oval mouth (outline)
                mc = H(-hh * .3, f * hw * .19 + lk); mw_, mh_ = hw * .32 * S, hh * (.06 + .2 * tk) * S
                pen.fill([(mc[0] + mw_ * math.cos(q), mc[1] + mh_ * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 16)], col)
            else:
                sm = [H(-hh * .2 - hh * .14 * math.sin(math.pi * q), f * hw * (-.12 + .62 * q) + lk) for q in np.linspace(0, 1, 9)]
                pen.line(sm, w * .8, col, sid + 'smile')
            if 'antenna' in self.props:                                             # antenna + wiggling outlined ball
                base = H(hh + d[1] * .5, d[0] * .5)
                wg = math.radians(P.get('antw', 0.0) + P.get('antamp', 7.0) * math.sin(t * 2 * math.pi * 1.3))
                tip = (base[0] + 26 * S * math.sin(wg), base[1] - 26 * S * math.cos(wg))
                pen.line([base, tip], w * .85, col, sid + 'ant')
                c = (tip[0] + 6 * S * math.sin(wg), tip[1] - 6 * S * math.cos(wg))
                pen.circle(c, 6 * S, w * .85, col, sid + 'antb', fill=hfill)
            return hc, hh * S
        # bean torso: puffy kidney outline around the spine, slightly hollow on the front side
        hip_ = limbs[(-1, True)][0]; L = CG['L']; a = L * .62; b = L * .3
        mid = A(self.pos_at(t) if False else hip_, L * .5, -f * 6)
        pts = []
        for q in np.linspace(0, 2 * math.pi, 40, endpoint=False):
            u = a * math.cos(q); v = b * math.sin(q)
            if v * f > 0: v *= .72 + .28 * abs(math.cos(q)) ** .6                   # front: flatter (kidney)
            else: v *= 1.12                                                         # back: puffy
            pts.append(A(mid, u, v))
        pen.fill(pts, hfill); pen.line(pts, w, col, sid + 'bean', closed=True)
        limb((-1, False)); limb((1, False))
        pen.circle(head, R, w, col, sid + 'head', fill=hfill)
        if 'tuft' in self.props:                                                    # little hair curl on top
            top = (head[0], head[1] - R)
            pen.line([(top[0] - 2 * S, top[1] + 1 * S), (top[0] - 5 * S, top[1] - 6 * S), (top[0] + 1 * S, top[1] - 10 * S),
                      (top[0] + 4 * S, top[1] - 5 * S)], w * .8, col, sid + 'tuft')
        if 'bowtie' in self.props:                                                  # bow tie under the chin
            nk = A(limbs[(1, False)][0], 16, -f * 6)
            bs = 8 * S
            for sd in (-1, 1):
                pen.line([nk, (nk[0] + sd * bs, nk[1] - bs * .6), (nk[0] + sd * bs, nk[1] + bs * .6), nk], w * .75, col, sid + f'bow{sd}')
        return head, R

    def _face(self, pen, head, R, P, f, fr, col, sid):
        ex = head[0] + R * 0.42 * f * (1 - fr) + P['look'] * R * 0.28
        ey = head[1] - R * 0.12 - P['lookup'] * R * 0.25
        sep = R * (0.18 + 0.2 * fr)
        for dx in (-sep, sep):
            pen.dot((ex + dx, ey), 2.6 * self.scale, col)
        tk = P.get('talk', 0)
        if 'robot' in self.props:
            for dx in (-R * .38, R * .38):
                es = self.scale * P.get('hs', 1.0) ** .75
                pen.rect(ex + dx - 4 * es, ey - 5 * es, ex + dx + 4 * es, ey + 5 * es, 0, fill=col)
            gy = head[1] + R * .42
            if tk > 0.06:      # LED mouth: grill opens and its bars jump like a level meter
                gy = head[1] + R * .5; hh = R * (.1 + .17 * tk)
                pen.rect(ex - R * .5, gy - hh, ex + R * .5, gy + hh, 2.5, col, sid + 'grill')
                for k in range(4):
                    lv = hh * (.35 + .65 * abs(math.sin(pen.boil * 1.7 + k * 2.1)))
                    xk = ex - R * .33 + k * R * .22
                    pen.rect(xk - R * .06, gy + hh - 2 * lv * tk - R * .04, xk + R * .06, gy + hh - R * .04, 0, fill=col)
                return
            pen.rect(ex - R * .45, gy - R * .12, ex + R * .45, gy + R * .12, 2.5, col, sid + 'grill')
            for k in range(3): pen.line([(ex - R * .22 + k * R * .22, gy - R * .12), (ex - R * .22 + k * R * .22, gy + R * .12)], 2, col, sid + f'g{k}', wob=0)
            return
        m = P['mouth']; my = head[1] + R * 0.38; mx = ex
        if tk > 0.06:          # talking: open mouth, height follows the voice envelope
            mw = R * (.2 + .1 * fr); mh = R * (.05 + .24 * tk)
            pen.fill([(mx + mw * math.cos(a), my + R * .02 + mh * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 18)], col)
            return
        if m > 2.5:
            pen.circle((mx, my), R * 0.17, 3, col, sid + 'mO')
        elif m > 1.5:      # big grin: D shape with teeth line
            wdt = R * 0.62
            pen.fill([(mx - wdt / 2 + wdt * k, my - R * 0.06 + R * 0.34 * math.sin(math.pi * k)) for k in np.linspace(0, 1, 16)], col)
            pen.line([(mx - wdt * 0.35, my + R * 0.08), (mx + wdt * 0.35, my + R * 0.08)], 2, PAPER if col == INK else INK, sid + 'teeth', wob=0)
        elif m > 0.5:
            pen.arc((mx, my - R * 0.12), R * 0.3, R * 0.22, 30, 150, 3, col, sid + 'smile')

    def _props(self, pen, head, R, sho, up, P, f, fr, col, sid, w):
        S = self.scale; bg = PAPER if col == INK else INK
        if 'cap' in self.props:       # peaked captain's cap
            cy = head[1] - R * 0.45; cx = head[0]
            crown = [(cx - R * 1.0, cy), (cx - R * 0.92, cy - R * 0.75), (cx + R * 1.05, cy - R * 0.9), (cx + R * 1.0, cy)]
            if f < 0 and fr < 0.5: crown = [(2 * cx - p[0], p[1]) for p in crown]
            pen.fill(crown, col)
            pen.line(crown, w * 0.7, col, sid + 'cap', closed=True)
            if not self.back: pen.dot((cx, cy - R * 0.42), 3.5 * S, bg)
            bx = f * (1 - fr)
            if abs(bx) > 0.3:
                pen.line([(cx + R * 0.8 * f, cy + R * 0.05), (cx + R * 1.6 * f, cy + R * 0.25)], w, col, sid + 'brim')
            else:
                pen.arc((cx, cy), R * 1.05, R * 0.25, 0, 180, w * 0.8, col, sid + 'brimf')
        if 'beard' in self.props and not self.back:
            c = 90 - f * (1 - fr) * 32
            pen.arc(head, R * 1.02, R * 1.02, c - 68, c + 68, w * 1.5, col, sid + 'beard')
            for k in range(5):
                a = math.radians(c - 50 + k * 25)
                p0 = (head[0] + R * 0.82 * math.cos(a), head[1] + R * 0.82 * math.sin(a))
                pen.line([p0, (head[0] + R * 1.2 * math.cos(a), head[1] + R * 1.2 * math.sin(a))], 2.5, col, sid + f'bh{k}')
        if 'beard' in self.props and self.back:     # beard edge peeking out around the jaw from behind
            for sd in (-1, 1):
                a0 = 90 + sd * 62
                pen.arc(head, R * 1.12, R * 1.12, min(a0, a0 - sd * 34), max(a0, a0 - sd * 34), w * 1.6, col, sid + f'bb{sd}')
                for k in range(3):
                    a = math.radians(a0 - sd * k * 14)
                    pen.line([(head[0] + R * 1.05 * math.cos(a), head[1] + R * 1.05 * math.sin(a)),
                              (head[0] + R * 1.38 * math.cos(a), head[1] + R * 1.38 * math.sin(a))], 2.5 * S ** .5, col, sid + f'bbh{sd}{k}')
        if 'collar' in self.props and not self.back:   # uniform collar: V at the neck + shoulder seam
            nx, ny = sho
            pen.line([(nx - 16 * S, ny - 4 * S), (nx, ny + 12 * S), (nx + 16 * S, ny - 4 * S)], w * .7, col, sid + 'col')
            pen.line([(nx - 30 * S, ny + 6 * S), (nx + 30 * S, ny + 6 * S)], w * .5, col, sid + 'seam')
        if 'curly' in self.props:     # tousled curly hair: a scribble of loops over the crown
            for k in range(7):
                a = math.radians(-160 + k * 23); cx_ = head[0] + R * 1.02 * math.cos(a); cy_ = head[1] + R * 1.02 * math.sin(a)
                pen.arc((cx_, cy_), R * .26, R * .22, 0, 330, w * .55, col, sid + f'curl{k}', rot=k * 40)
        if 'shine' in self.props:
            pen.arc(head, R * 0.68, R * 0.68, -75 + 45 * (f < 0), -30 + 45 * (f < 0), 4, col, sid + 'sh1')
            pen.dot((head[0] + R * 0.25 * f, head[1] - R * 0.66), 2.2 * S, col)
            pen.line([(head[0] - R * 0.9, head[1] + R * 0.15), (head[0] - R * 1.08, head[1] + R * 0.05)], 3, col, sid + 'ear')
        if 'ferengi' in self.props:   # big fan ears + forehead ridges (bald)
            hx, hy = head; bg = PAPER if col == INK else INK
            sides = (-1, 1) if fr > 0.5 else (-f,)
            for sd in sides:
                X = lambda a, b: (hx + sd * a * R, hy + b * R)
                ear = [X(.8, -.55), X(1.5, -1.15), X(2.15, -.75), X(2.3, .05), X(1.9, .65), X(1.25, .8), X(.85, .4)]
                for _ in range(3):     # chaikin smoothing
                    E = np.array(ear + ear[:1]); ear = [tuple(q) for a_, b_ in zip(E[:-1], E[1:]) for q in (.75 * a_ + .25 * b_, .25 * a_ + .75 * b_)]
                pen.fill(ear, bg); pen.line(ear, w * .8, col, sid + f'ear{sd}', closed=True)
                pen.line([X(1.05, -.35), X(1.6, -.7), X(1.95, -.3), X(1.75, .25)], w * .5, col, sid + f'eri{sd}')
            for k in range(3):
                yy = hy - R * (.5 + .14 * k); hw = R * (.34 - .07 * k)
                pen.line([(hx + x_, yy - .1 * R * (1 - (x_ / hw) ** 2)) for x_ in np.linspace(-hw, hw, 7)], w * .45, col, sid + f'rdg{k}')
        if 'ponytail' in self.props and fr < 0.5:
            b = (head[0] - f * R * (1 - fr) * 0.95, head[1] - R * 0.3)
            pen.line([b, (b[0] - f * 14 * S, b[1] + 10 * S), (b[0] - f * 16 * S, b[1] + 30 * S)], w * 0.9, col, sid + 'pony')
        if 'badge' in self.props and not self.back:
            bx = sho[0] + 14 * S * (f * (1 - fr) * 0.35 + fr * 0.6); by = sho[1] + 22 * S
            pen.fill([(bx, by - 8 * S), (bx + 5 * S, by + 6 * S), (bx, by + 2 * S), (bx - 5 * S, by + 6 * S)], col)
