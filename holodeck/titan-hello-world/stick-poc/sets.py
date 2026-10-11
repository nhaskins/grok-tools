"""Set pieces for engine.py. Each set is a class with optional bg(pen, t, ctx) and fg(pen, t, ctx).
bg draws behind the cast, fg on top. Gag timings come from ctx.ev('<event name>') (CUES['events'])."""
import math
import numpy as np, cv2
from stickfig import *
from inkset import W, H, FLOOR, stars_field, sparkle, ship
import os
_P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEATS = np.load(f'{_P}/beats.npy'); BARS = np.load(f'{_P}/bars.npy')
def since(arr, t):
    p = arr[arr <= t]; return t - p[-1] if len(p) else 9.0


def floor(pen, y=FLOOR, x0=-700, x1=2600):
    pen.line([(x0, y), (x1, y)], 6, INK, 'floor')
    for k in range(int(x0 / 90), int(x1 / 90)):
        x = k * 90; pen.line([(x, y + 4), (x - 28, y + 40)], 2.5, INK, f'fh{k}', wob=0.6)

def beats_between(a, b): return BEATS[(BEATS >= a) & (BEATS <= b)]

def heart(pen, c, s, col=INK, sid='heart'):
    pts = [(c[0] + s * 16 * math.sin(a) ** 3, c[1] - s * (13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)))
           for a in np.linspace(0, 2 * math.pi, 40)]
    pen.fill(pts, col); pen.line(pts, 4, col, sid, closed=True)

def check(pen, c, s, sid):
    pen.line([(c[0] - 14 * s, c[1]), (c[0] - 4 * s, c[1] + 12 * s), (c[0] + 18 * s, c[1] - 16 * s)], 6 * s ** .5, INK, sid)

def burst(pen, c, t, t0, R, n=18, col=INK, sid='bu', dur=0.9, w=4):
    u = (t - t0) / dur
    if not 0 <= u < 1: return
    k = ease_out(min(u * 1.6, 1)); fade = 1 - clamp01((u - 0.55) / 0.45)
    r = np.random.default_rng(abs(hash(sid)) % 999)
    for i in range(n):
        a = i * 2 * math.pi / n + r.uniform(-.1, .1); L = R * r.uniform(.7, 1.1)
        r0, r1 = L * (0.25 + 0.6 * k), L * k
        p0 = (c[0] + r0 * math.cos(a), c[1] + r0 * math.sin(a)); p1 = (c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a))
        if r1 - r0 > 2: pen.line([p0, p1], w * fade + .5, col, f'{sid}{i}')
        if fade > .1: pen.dot(p1, (3 + 3 * (i % 2)) * fade, col)

def paper_sheet(pen, c, ang, s, sid, label=None):
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda x, y: (c[0] + (x * ca - y * sa) * s, c[1] + (x * sa + y * ca) * s)
    pts = [P(-26, -34), P(26, -34), P(26, 34), P(-26, 34)]
    pen.fill(pts, PAPER); pen.line(pts, 3.5, INK, sid, closed=True)
    if label: pen.text(label, P(0, -8), 20 * s, INK, 'marker')
    for k in range(3): pen.line([P(-16, 8 + k * 9), P(16 - 8 * (k == 2), 8 + k * 9)], 2, INK, sid + f'l{k}', wob=.4)


# ------------------------------------------------------------------ "We pull the code and we keep it in sync"
class tug:
    @staticmethod
    def crate_x(t, ctx):
        tp = ctx.ev('pull'); x = 1300
        for b in beats_between(tp - 0.05, t): x -= 34 * ease_out((t - b) / 0.22)
        return x

    @staticmethod
    def bg(pen, t, ctx):
        floor(pen)
        pen.text(ctx.opt('sign', 'git pull origin titan'), (960, 270), 50, INK, 'marker')
        pen.line([(700, 307), (1220, 303)], 3, INK, 'ul')
        x0c = tug.crate_x(t, ctx); y1 = FLOOR - 4
        for ci in reversed(range(ctx.opt('crates', 1))):
            x = x0c + ci * 300
            if ci: pen.line([(x - 30, y1 - 115), (x, y1 - 115)], 6, INK, f'rc{ci}')
            tug.crate(pen, x, y1, ci)

    @staticmethod
    def crate(pen, x, y1, ci):
        if True:
            sid = f'crate{ci}'
            pen.rect(x, y1 - 230, x + 270, y1, 6, INK, sid, fill=PAPER)
            pen.line([(x, y1 - 230), (x + 270, y1)], 3, INK, sid + 'c1'); pen.line([(x + 270, y1 - 230), (x, y1)], 3, INK, sid + 'c2')
            pen.rect(x + 40, y1 - 175, x + 230, y1 - 60, 0, fill=PAPER)
            pen.text(['{ CODE }', '{ API }', '{ DOCS }', '{ TESTS }'][ci % 4], (x + 135, y1 - 118), 52, INK, 'marker')
            for k in range(3):   # drag marks behind the crate
                pen.line([(x + 280 + k * 30, y1 - 2), (x + 300 + k * 30, y1 - 2)], 3, INK, f'{sid}dm{k}')

    @staticmethod
    def fg(pen, t, ctx):
        hands = sorted([h['hand_r'] for h in ctx.hands.values()], key=lambda p: p[0])
        if not hands: return
        x = tug.crate_x(t, ctx); ry = FLOOR - 4 - 115
        tail = [(hands[0][0] - 140, FLOOR - 12), (hands[0][0] - 300, FLOOR - 4)]
        pen.line(list(reversed(tail)) + hands + [(x, ry)], 6, INK, 'rope')
        ts = ctx.ev('sync_checks')
        heads = sorted([h['head'] for h in ctx.hands.values()], key=lambda p: p[0])
        for i, hd in enumerate(heads):
            k = ease_out_back((t - ts - i * 0.12) / 0.25)
            if k > 0.02: check(pen, (hd[0], hd[1] - 70), k, f'ck{i}')
        k = ease_out_back((t - ctx.ev('sync')) / 0.3)
        if k > 0.02:
            pen.text('IN SYNC!', (1010, 430), 80 * k, INK, 'marker')
            pen.rect(1010 - 230 * k, 430 - 70 * k, 1010 + 230 * k, 430 + 70 * k, 5, INK, 'stamp')


# ------------------------------------------------------------------ "We draft the deals faster than you can think"
class draft:
    DESK = (720, 1200, 768)

    @staticmethod
    def bg(pen, t, ctx):
        floor(pen)
        x0, x1, ty = draft.DESK
        if t > ctx.ev('faster'):   # speed lines streaming past
            for i in range(14):
                y = 260 + i * 38; x = 1900 - ((t * 1500 + i * 377) % 2600)
                pen.line([(x, y), (x + 160 + 60 * (i % 3), y)], 3, INK, f'sp{i}', wob=.3)
        pen.line([(x0, ty), (x1, ty)], 7, INK, 'desk')
        pen.line([(x0 + 30, ty), (x0 + 30, FLOOR)], 6, INK, 'dl1'); pen.line([(x1 - 30, ty), (x1 - 30, FLOOR)], 6, INK, 'dl2')
        for sx in (650, 1270):   # stools
            pen.line([(sx - 45, 826), (sx + 45, 826)], 6, INK, f'st{sx}'); pen.line([(sx, 826), (sx, FLOOR)], 6, INK, f'sp{sx}')
        # pads with growing scribbles
        n = int(clamp01((t - ctx.ev('draft')) / 2.5) * 60)
        for side, px in ((0, 800), (1, 1120)):
            pen.rect(px - 50, ty - 8, px + 50, ty - 2, 3, INK, f'pad{side}', fill=PAPER)
        # stack of finished deals
        k = int(clamp01((t - ctx.ev('deals')) / 2) * 9)
        for i in range(k): pen.rect(940, ty - 10 - i * 9, 1000, ty - 3 - i * 9, 2.5, INK, f'dk{i}', fill=PAPER)

    @staticmethod
    def fg(pen, t, ctx):
        x0, x1, ty = draft.DESK
        t0 = ctx.ev('draft')
        r = np.random.default_rng(12)
        nps = ctx.opt('sheets', 1)
        for i0, b0 in enumerate(beats_between(t0 - 0.05, ctx.shot['end'])):   # sheet(s) fly off on every beat
          for j in range(nps):
            i = i0 * nps + j; b = b0 + j * 0.12
            u = t - b
            if u < 0 or u > 1.6: continue
            r = np.random.default_rng(100 + i)     # per-sheet seed (stable while other sheets come and go)
            side = i % 2; sx = 820 if side == 0 else 1100
            vx = r.uniform(250, 520) * (1 if side else -1) * (0.6 if i % 3 == 0 else 1); vy = -r.uniform(650, 900)
            c = (sx + vx * u, ty - 20 + vy * u + 700 * u * u)
            paper_sheet(pen, c, u * r.uniform(3, 7) * (1 if side else -1), 1.15, f'fs{i}', 'DEAL' if i % 2 == 0 else None)
        # thought bubble that can't keep up: chases from the left, arrives on "think"
        hd = ctx.hands.get('riker', {}).get('head', (650, 610))
        ta, tb = t0, ctx.ev('think')
        u = clamp01((t - ta) / (tb - ta))
        target = (hd[0] - 150, hd[1] - 190)
        bx = lerp(-260, target[0], ease(u) ** 1.3); by = target[1] - 40 * abs(math.sin(t * 9)) * (1 - u)
        R = 80 + 28 * ease_out_back((t - tb) / 0.25) if t > tb else 80
        pts = []
        for k in range(14):        # scalloped cloud outline
            a0 = k * 2 * math.pi / 14
            pts += [(bx + R * 1.35 * math.cos(a) + 12 * math.cos(a0 * 7), by + R * 0.85 * math.sin(a)) for a in np.linspace(a0, a0 + 2 * math.pi / 14, 4)]
        pen.fill(pts, PAPER); pen.line(pts, 5, INK, 'bub', closed=True)
        if t > tb:
            pen.text('!!', (bx, by), 70, INK, 'marker')
            for k, (dx, dy, rr) in enumerate(((60, 95, 16), (100, 140, 10))):
                pen.circle((bx + dx, by + dy), rr, 4, INK, f'bd{k}', fill=PAPER)
        else:
            pen.text('wait up...', (bx, by), 34, INK, 'hand')
            for k in range(2):   # sweat drops flying off
                ph = (t * 3 + k * .5) % 1
                pen.circle((bx - R * 1.4 - 30 * ph, by - 50 + 40 * ph * ph + k * 40), 6, 3, INK, f'sw{k}', fill=PAPER)


# ------------------------------------------------------------------ "Captain's log at a quarter to five"
class log:
    CLOCK = (1420, 420, 120)

    @staticmethod
    def bg(pen, t, ctx):
        floor(pen)
        pen.line([(900, 768), (1260, 768)], 7, INK, 'desk')
        pen.line([(930, 768), (930, FLOOR)], 6, INK, 'dl1'); pen.line([(1230, 768), (1230, FLOOR)], 6, INK, 'dl2')
        pen.line([(780, 826), (870, 826)], 6, INK, 'seat'); pen.line([(785, 826), (775, 690)], 5, INK, 'back'); pen.line([(825, 826), (825, FLOOR)], 6, INK, 'ped')
        pen.line([(1120, 768), (1116, 718), (1160, 718), (1156, 768)], 4, INK, 'mug')
        pen.arc((1168, 742), 14, 16, -80, 80, 4, INK, 'mugh')
        for k in range(2):   # steam
            pen.line([(1128 + k * 18 + 6 * math.sin(t * 3 + yy / 9), 708 - yy) for yy in range(0, 60, 6)], 2.5, INK, f'stm{k}')
        cx, cy, R = log.CLOCK
        pen.circle((cx, cy), R, 6, INK, 'clk', fill=PAPER); pen.circle((cx, cy), R + 12, 3, INK, 'clk2')
        for k in range(12):
            a = k * math.pi / 6; L = 22 if k % 3 == 0 else 10
            pen.line([(cx + (R - 8) * math.sin(a), cy - (R - 8) * math.cos(a)), (cx + (R - 8 - L) * math.sin(a), cy - (R - 8 - L) * math.cos(a))], 4, INK, f'tk{k}')
        for k, lab in ((0, '12'), (3, '3'), (6, '6'), (9, '9')):
            a = k * math.pi / 6; pen.text(lab, (cx + (R - 52) * math.sin(a), cy - (R - 52) * math.cos(a)), 30, INK, 'hand')
        ts, te = ctx.ev('clock_spin'), ctx.ev('clock_land')
        wild = ctx.opt('wild', 0)
        if wild and t < ts: h = 3.0 + wild * (t - ctx.shot['t']) * (1 + 0.6 * math.sin(t * 3))   # clock spinning out of control
        elif wild: h = 3.0 + wild * (ts - ctx.shot['t']) * 1.0 + 0
        else: h = 3.0 + 1.75 * ease_out_back((t - ts) / (te - ts), 1.2) if t > ts else 3.0 + 0.01 * math.sin(t * 20) * (t > ts - 1)
        if wild and t >= ts:
            h0 = 3.0 + wild * (ts - ctx.shot['t']) * (1 + 0.6 * math.sin(ts * 3)); h1 = math.ceil(h0) + 4.75
            h = lerp(h0, h1, ease_out_back((t - ts) / (te - ts), 1.2))
        am = h % 1 * 2 * math.pi; ah = h / 12 * 2 * math.pi
        pen.line([(cx, cy), (cx + R * .78 * math.sin(am), cy - R * .78 * math.cos(am))], 6, INK, 'mh')
        pen.line([(cx, cy), (cx + R * .5 * math.sin(ah), cy - R * .5 * math.cos(ah))], 9, INK, 'hh')
        pen.dot((cx, cy), 9, INK)
        if t > te: sparkle(pen, (cx + R + 30, cy - R), 22 * ease_out_back((t - te) / .2) * (1 - clamp01((t - te - .6) / .3)) + .1, INK, 'ding')
        # typewriter header
        s = "CAPTAIN'S LOG  04:45"; tl = ctx.ev('log')
        n = int(clamp01((t - tl) / 0.9) * len(s))
        if n: pen.text(s[:n], (560, 300), 44, INK, 'marker', anchor='l')

    @staticmethod
    def fg(pen, t, ctx):
        hd = ctx.hands.get('captain', {}).get('head')
        if not hd: return
        if ctx.ev('log') - .1 < t < ctx.ev('clock_land'):     # sound waves from the recorder
            for k in range(3):
                ph = (t * 2.4 + k / 3) % 1
                pen.arc((hd[0] + 40, hd[1] + 5), 30 + 70 * ph, 40 + 70 * ph, -40, 40, 4 * (1 - ph) + .5, INK, f'sw{k}')
        ty = ctx.ev('yawn')
        if t > ty + .2:
            for k, ch in enumerate('zzZ'):
                u = (t - ty - .2 - k * .25)
                if u > 0: pen.text(ch, (hd[0] + 60 + 30 * k + 10 * math.sin(u * 4), hd[1] - 80 - 55 * k - 30 * u), 36 + 14 * k, INK, 'marker', alpha=clamp01(u * 4))


# ------------------------------------------------------------------ "Grok Bot crew, keeping the mission alive"
class chorusline:
    @staticmethod
    def bg(pen, t, ctx):
        floor(pen)
        for k in range(9):   # footlights
            x = 280 + k * 170; pen.arc((x, FLOOR + 2), 26, 18, 180, 360, 4, INK, f'fl{k}')
            if since(BEATS, t) < 0.12:
                for j in (-1, 0, 1): pen.line([(x + j * 14, FLOOR - 26), (x + j * 26, FLOOR - 46)], 2.5, INK, f'fr{k}{j}')
        alive = t > ctx.ev('alive')
        # banner + ECG line
        pen.rect(330, 160, 1590, 400, 5, INK, 'ban', fill=PAPER)
        pen.line([(330, 160), (300, 120)], 4, INK, 'bs1'); pen.line([(1590, 160), (1620, 120)], 4, INK, 'bs2')
        pen.text('MISSION: ALIVE!' if alive else 'MISSION', (900 if alive else 960, 222), 66, INK, 'marker')
        xs = np.arange(360, 1561, 6.0); ys = np.zeros_like(xs)
        for b in beats_between(t - 3.5, t):
            x = 1560 - (t - b) * 360
            big = 1.8 if abs(b - ctx.ev('alive')) < 0.25 else 1.0
            d = xs - x
            ys += big * (np.interp(d, [-16, -8, 0, 8, 18], [0, 10, -70, 34, 0], left=0, right=0))
        pen.line(list(zip(xs, 335 + ys * .75)), 4, INK, 'ecg', wob=0.3)
        if alive:
            k = 1 + 0.25 * math.exp(-since(BEATS, t) * 8)
            heart(pen, (1360, 225), 2.4 * k)

    @staticmethod
    def fg(pen, t, ctx):
        g = ctx.hands.get('grokbot')
        k = ease_out_back((t - ctx.ev('grok')) / .3)
        if g and k > 0.02 and t < ctx.ev('grok') + 2.4:
            hx, hy = g['head']
            pen.text('GROK BOT', (hx + 230, hy - 120), 50 * k, INK, 'marker')
            pen.line([(hx + 150, hy - 100), (hx + 80, hy - 60), (hx + 45, hy - 40)], 4, INK, 'ga')
            pen.line([(hx + 45, hy - 40), (hx + 66, hy - 40)], 4, INK, 'ga1'); pen.line([(hx + 45, hy - 40), (hx + 54, hy - 58)], 4, INK, 'ga2')


# ------------------------------------------------------------------ "Warp the signal, light the sky"
class warpsky:
    SHIP = (640, 470, 0.95)

    @staticmethod
    def bg(pen, t, ctx):
        pen.img[:] = INK
        tw = ctx.ev('warp'); w = clamp01((t - tw) / 1.2) * (1 - 0.9 * clamp01((t - ctx.ev('light') + .15) / .3))
        stars_field(pen, (-400, -300, 2300, 1300), t, 0.04 + 0.2 * w, n=260, seed=31, col=PAPER, streak=0.02 + 0.45 * w)

    @staticmethod
    def fg(pen, t, ctx):
        cx, cy, s = warpsky.SHIP
        ship(pen, (cx, cy + 8 * math.sin(t * 2)), s, PAPER, INK, 'titanw', facing=1)
        x0 = cx + 340 * s; ts = ctx.ev('signal')
        a = clamp01((t - ctx.ev('warp') + .3) / 1.0)
        if a > 0:   # the signal: a sine that warps and bends harder after "signal"
            bend = 1 + 2.5 * ease_out_back((t - ts) / .4) if t > ts else 1
            xs = np.linspace(x0, x0 + 1500 * a, 160); u = (xs - x0) / 1500
            ys = cy + (14 + 60 * u) * bend * np.sin(u * 30 - t * 14) + 140 * bend * u * u * math.sin(t * 2.3)
            pen.line(list(zip(xs, ys)), 4, PAPER, 'sig', wob=.4)
            for k in range(3):
                ph = (t * 1.5 + k / 3) % 1
                pen.arc((x0, cy), 40 + 300 * ph, 60 + 380 * ph, -40, 40, 4 * (1 - ph) + .4, PAPER, f'ring{k}')
        tl = ctx.ev('light')
        r = np.random.default_rng(8)
        for i, b in enumerate(beats_between(ctx.ev('signal') - .05, tl - .1)):   # small bursts on each beat
            burst(pen, (r.uniform(950, 1700), r.uniform(120, 380)), t, b, r.uniform(140, 210), 16, PAPER, f'fw{i}', 1.0, 6)
        burst(pen, (1250, 280), t, tl, 460, 28, PAPER, 'fwbig', 1.4, 9)
        burst(pen, (1600, 180), t, tl + .22, 220, 18, PAPER, 'fwbig2', 1.2, 6)
        burst(pen, (900, 160), t, tl + .38, 200, 18, PAPER, 'fwbig3', 1.2, 6)   # big one on "light"
        # paper horizon band (screen space) keeps the captions on paper
        rp = Pen(pen.img, (W / 2, H / 2, 1.0), pen.boil)
        hill = [(-20, 925)] + [(x, 905 - 18 * math.sin(x / 260) - 10 * math.sin(x / 97)) for x in range(0, W + 41, 40)] + [(W + 20, 925)]
        rp.fill(hill + [(W + 20, H + 20), (-20, H + 20)], PAPER); rp.line(hill, 6, INK, 'hz')
        for k in range(3):   # tiny watchers on the horizon
            x = 1500 + k * 55; y = 905 - 18 * math.sin(x / 260) - 10 * math.sin(x / 97)
            F = Figure(f'wt{k}', x, y - 33, 1, back=True, scale=0.3); F.key(0, 'front+cheer' if t > ctx.ev('light') else 'front', 0)
            F.draw(rp, t, 0, w=4)


# ------------------------------------------------------------------ "Titan rising, Titan high"
class rise:
    @staticmethod
    def ship_pos(t, ctx):
        a, b = ctx.ev('rise_start'), ctx.ev('rise_top')
        u = ease(clamp01((t - a) / (b - a)))
        return (960, lerp(990, -230, u)), lerp(0.9, 1.75, u)

    @staticmethod
    def bg(pen, t, ctx):
        r = np.random.default_rng(17)
        for i in range(16):   # clouds pinned in world space -> tilt reads as motion
            cx, cy = r.uniform(-100, 2000), r.uniform(-900, 560); sc = r.uniform(.7, 1.4)
            pts = []
            for k in range(5): pts += [(cx - 120 * sc + k * 60 * sc + 30 * sc - 30 * sc * math.cos(a), cy - 28 * sc * math.sin(a) * (1.2 if k in (1, 2) else 0.8)) for a in np.linspace(0, math.pi, 7)]
            pen.line(pts + [(cx + 180 * sc, cy), (cx - 120 * sc, cy)], 4, INK, f'cl{i}', closed=True)
        c, s = rise.ship_pos(t, ctx)
        burst(pen, c, t, ctx.ev('high'), 640, 30, INK, 'hb', 1.6, 6)
        for i in range(9):   # exhaust / speed lines below the ship
            x = c[0] - 260 * s + i * 65 * s; y = c[1] + 90 * s + ((t * 900 + i * 137) % 340)
            pen.line([(x, y), (x, y + 90 + 40 * (i % 2))], 3, INK, f'ex{i}', wob=.4)
        ship(pen, c, s, sid='titanr', facing=-1)
        hill = [(-400, 1500), (-400, 880)] + [(x, 880 - 70 * math.exp(-((x - 960) / 520) ** 2)) for x in range(-400, 2401, 50)] + [(2400, 880), (2400, 1500)]
        pen.fill(hill, PAPER); pen.line(hill[1:-1], 6, INK, 'hill')
        for k in range(14):
            x = -200 + k * 170; y = 880 - 70 * math.exp(-((x - 960) / 520) ** 2)
            pen.line([(x, y + 14), (x - 20, y + 40)], 2.5, INK, f'gh{k}', wob=.6)

    @staticmethod
    def fg(pen, t, ctx):
        if t > ctx.ev('high'):
            c, s = rise.ship_pos(t, ctx)
            k = ease_out_back((t - ctx.ev('high')) / .3); lx, ly = c[0] - 330 * s, c[1] - 105 * s
            if k > .05: pen.rect(lx - 125 * k, ly - 45 * k, lx + 125 * k, ly + 45 * k, 4, INK, 'tsign', fill=PAPER)
            pen.text('TITAN', (lx, ly), 64 * k + 1, INK, 'marker')


# ================================================================== full-song set pieces
from inkset import console, chair


class RevealPen:
    """Wraps a Pen and only draws the first `k` strokes (fractional k draws the k-th stroke partially),
    so any set piece (e.g. ship()) can be drawn on line by line."""
    def __init__(self, pen, k): self.p = pen; self.k = k; self.i = 0; self.tip = None

    def _frac(self):
        f = self.k - self.i; self.i += 1; return f

    def line(self, pts, w=5, col=INK, sid='l', wob=None, closed=False):
        f = self._frac()
        if f <= 0 or len(pts) < 2: return
        pts = list(pts) + ([pts[0]] if closed else [])
        if f < 1:
            P = np.array(pts, float); seg = np.linalg.norm(np.diff(P, axis=0), axis=1); L = seg.sum() * f
            out = [tuple(P[0])]; acc = 0
            for j, sl in enumerate(seg):
                if acc + sl >= L:
                    u = (L - acc) / max(sl, 1e-6); out.append(tuple(P[j] + (P[j + 1] - P[j]) * u)); break
                out.append(tuple(P[j + 1])); acc += sl
            pts = out; self.tip = pts[-1]; closed = False
        self.p.line(pts, w, col, sid, wob)

    def arc(self, c, rx, ry, a0, a1, w=5, col=INK, sid='a', rot=0, wob=None, n=None):
        n = n or max(8, int(abs(a1 - a0) / 8)); pts = []
        for k in range(n + 1):
            a = math.radians(lerp(a0, a1, k / n)); pts.append((c[0] + rx * math.cos(a), c[1] + ry * math.sin(a)))
        self.line(pts, w, col, sid, wob)

    def circle(self, c, r, w=5, col=INK, sid='c', fill=None, wob=None):
        if fill is not None and self.k - self.i >= 1: self.p.circle(c, r, 0, fill=fill)
        if w > 0: self.arc(c, r, r, 0, 360, w, col, sid, wob=wob)
        elif fill is not None: self.i += 1

    def rect(self, x0, y0, x1, y1, w=5, col=INK, sid='r', fill=None, wob=None):
        if fill is not None and self.k - self.i >= 1: self.p.fill([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill)
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], w, col, sid, wob, closed=True)

    def fill(self, pts, col=INK):
        if self.k - self.i >= 1.0: self.p.fill(pts, col)   # fills don't count as strokes

    def dot(self, c, r, col=INK):
        if self.k - self.i >= 1: self.p.dot(c, r, col)

    def text(self, *a, **kw):
        if self.k - self.i >= 1: self.p.text(*a, **kw)
        self.i += 1


def count_strokes(fn):
    rp = RevealPen(None, -1); fn(rp); return rp.i


def twinkle_stars(pen, t, n=120, seed=3, rect=(-200, -150, 2120, 1000), col=INK, drift=0.0):
    r = np.random.default_rng(seed); db = since(BEATS, t)
    for i in range(n):
        x = r.uniform(rect[0], rect[2]) - drift * t * r.uniform(.4, 1.2); y = r.uniform(rect[1], rect[3])
        x = (x - rect[0]) % (rect[2] - rect[0]) + rect[0]
        if i % 11 == 0:
            pulse = 1 + 0.7 * math.exp(-db * 6) * ((i // 11) % 2)
            sparkle(pen, (x, y), 8 * pulse, col, f'tw{i}')
        else:
            pen.dot((x, y), r.uniform(1.4, 3.4) * (1 + 0.5 * math.exp(-db * 8) * (i % 3 == 0)), col)


def outlined(pen, txt, c, size, ow, font='marker'):
    """ink lettering with a thick paper outline, readable over ink or busy backgrounds"""
    for k in range(12):
        a = k * math.pi / 6; pen.text(txt, (c[0] + ow * math.cos(a), c[1] + ow * math.sin(a)), size, PAPER, font)
    pen.text(txt, c, size, INK, font)


def stamp(pen, txt, c, t, t0, size=80, w=5, sid='stamp'):
    k = ease_out_back((t - t0) / 0.3)
    if k <= 0.02: return
    L = len(txt) * size * 0.33
    pen.rect(c[0] - L * k, c[1] - size * .85 * k, c[0] + L * k, c[1] + size * .85 * k, w, INK, sid, fill=PAPER)
    pen.text(txt, c, size * k, INK, 'marker')


# ------------------------------------------------------------------ intro: ship drawn on, title card
class title:
    @staticmethod
    def bg(pen, t, ctx):
        twinkle_stars(pen, t, 140, seed=5, drift=4)
        a, b = ctx.ev('draw_a'), ctx.ev('draw_b')
        c = (960 + 12 * math.sin(t * .5), 420 + 6 * math.sin(t * .8)); sc = 1.35
        N = title.N if hasattr(title, 'N') else count_strokes(lambda p: ship(p, c, sc, sid='tt'))
        title.N = N
        k = clamp01((t - a) / (b - a)) * N
        rp = RevealPen(pen, k); ship(rp, c, sc, sid='tt')
        if 0 < k < N and rp.tip is not None:     # pen nib at the end of the stroke being drawn
            pen.dot(rp.tip, 7, INK)
        for j, (key, txt, y, size, font) in enumerate((('title', 'U.S.S. TITAN', 735, 130, 'marker'), ('sub', 'BRIDGE THEME', 860, 60, 'hand'))):
            t0 = ctx.ev(key)
            n = int(clamp01((t - t0) / 1.2) * len(txt))
            if n: pen.text(txt[:n], (960 - (len(txt) - n) * size * 0.27, y), size, INK, font)
            u = clamp01((t - t0 - 1.0) / .8)
            if u > 0 and j == 0:
                pen.line([(560, 815), (560 + 800 * u, 808)], 5, INK, 'tul')


# ------------------------------------------------------------------ generic bridge
class bridge:
    VS = (610, 110, 1310, 470)
    MINI = {'OPS': (300, 200, 410, 290), 'HELM': (1340, 200, 1450, 290), 'SCI': (1640, 200, 1750, 290)}

    @staticmethod
    def screen(pen, t, ctx):
        vx0, vy0, vx1, vy1 = bridge.VS
        mode = ctx.opt('screen', 'stars')
        pen.rect(vx0 - 14, vy0 - 14, vx1 + 14, vy1 + 14, 5, INK, 'vsframe')
        if mode == 'off':
            pen.rect(vx0, vy0, vx1, vy1, 0, fill=INK)
            pen.text('zzz', (960, 290), 40, PAPER, 'hand', alpha=.6); return
        pen.rect(vx0, vy0, vx1, vy1, 0, fill=INK)
        if mode == 'boot':
            tb = ctx.ev(ctx.opt('boot_ev', 'boot'))
            u = clamp01((t - tb) / ctx.opt('boot_len', 6.0))
            pen.text('TITAN OS v2.6', (960, 230), 44, PAPER, 'marker')
            pen.rect(720, 300, 1200, 340, 3, PAPER, 'pbar'); pen.rect(726, 306, 726 + 468 * u, 334, 0, fill=PAPER)
            pen.text(f'{int(u * 100)}%', (960, 400), 34, PAPER, 'hand'); return
        warp = mode in ('warp', 'fireworks')
        stars_field(pen, (vx0, vy0, vx1, vy1), t, 0.25 if warp else 0.07, n=90, streak=0.35 if warp else 0.0)
        if mode == 'countdown':
            for key, txt in ctx.opt('countdown', []):
                tk = ctx.ev(key) if isinstance(key, str) else key
                u = t - tk
                if 0 <= u < 0.44:
                    k = ease_out_back(min(u / .15, 1)); pen.text(txt, (960, 290), 190 * k + 1, PAPER, 'marker')
        if mode == 'fireworks':
            r = np.random.default_rng(4)
            for i, b in enumerate(BEATS[(BEATS > t - 1) & (BEATS <= t)]):
                rr = np.random.default_rng(int(b * 100))
                burst(pen, (rr.uniform(720, 1200), rr.uniform(190, 360)), t, b, rr.uniform(70, 110), 14, PAPER, f'vf{int(b*100)}', .9, 4)

    @staticmethod
    def minis(pen, t, ctx):
        boot = ctx.opt('boot', None); chk = ctx.opt('checks', None)
        icons = {'OPS': 'wave', 'HELM': 'radar', 'SCI': 'bars'}
        for j, (nm, (x0, y0, x1, y1)) in enumerate(bridge.MINI.items()):
            on = True if boot is None or nm not in boot else t >= ctx.ev(boot[nm])
            pen.rect(x0, y0, x1, y1, 4, INK, f'mini{nm}', fill=PAPER if on else INK)
            pen.text(nm, ((x0 + x1) / 2, y1 + 22), 24, INK, 'hand')
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if not on: continue
            if boot is not None and nm in boot and t - ctx.ev(boot[nm]) < .5:
                sparkle(pen, (x1 + 6, y0 - 6), 14 * ease_out_back((t - ctx.ev(boot[nm])) / .2), INK, f'ms{nm}')
            if chk is not None and t > ctx.ev(chk) + j * 0.22:
                check(pen, (cx, cy), 1.4 * ease_out_back((t - ctx.ev(chk) - j * .22) / .25) + .01, f'mck{nm}'); continue
            ic = icons[nm]
            if ic == 'wave':
                pen.line([(x0 + 8 + k * 4, cy + 18 * math.sin(k * .5 - t * 6)) for k in range(24)], 3, INK, f'iw{nm}', wob=.3)
            elif ic == 'radar':
                pen.circle((cx, cy), 34, 3, INK, f'ir{nm}'); a = t * 3
                pen.line([(cx, cy), (cx + 34 * math.cos(a), cy + 34 * math.sin(a))], 3, INK, f'ira{nm}')
            else:
                for k in range(4):
                    hgt = 14 + 40 * abs(math.sin(t * 2 + k * 1.3)) * (0.5 + 0.5 * math.exp(-since(BEATS, t) * 5))
                    pen.rect(x0 + 14 + k * 22, y1 - 10 - hgt, x0 + 28 + k * 22, y1 - 10, 0, fill=INK)

    @staticmethod
    def gauge(pen, t, ctx):
        g = ctx.opt('gauge', None)
        lvl = ctx.opt('gauge_level', 1.0) if g is None else lerp(g[2] if len(g) > 2 else 0.1, 1.0, clamp01((t - ctx.ev(g[0])) / (ctx.ev(g[1]) - ctx.ev(g[0]))) ** 1.3)
        x0, y0, x1, y1 = 470, 140, 535, 580
        pen.rect(x0, y0, x1, y1, 5, INK, 'gauge', fill=PAPER)
        yy = y1 - 6 - (y1 - y0 - 12) * lvl
        pen.line([(x0 + 8, yy), (x1 - 8, yy)], 4, INK, 'glvl')
        for k in range(int((y1 - 8 - yy) / 16)):      # hatched fill instead of a solid black bar
            y = y1 - 12 - k * 16; pen.line([(x0 + 10, y), (x1 - 10, y - 12)], 3, INK, f'gh{k}', wob=.3)
        for k in range(1, 5): pen.line([(x0 - 14, y0 + k * 88), (x0, y0 + k * 88)], 3, INK, f'gt{k}')
        pen.text('PWR', ((x0 + x1) / 2, y1 + 26), 26, INK, 'marker')
        if g is not None and lvl > 0.97 and int(t * 6) % 2: pen.text('WARP READY', ((x0 + x1) / 2, y0 - 30), 28, INK, 'marker')

    @staticmethod
    def bg(pen, t, ctx):
        floor(pen)
        bridge.screen(pen, t, ctx)
        pen.line([(-600, 60), (520, 60), (580, 100)], 4, INK, 'rail1'); pen.line([(1340, 100), (1400, 60), (2500, 60)], 4, INK, 'rail2')
        pen.text('U.S.S. TITAN', (960, 58), 44, INK, 'marker')
        bridge.minis(pen, t, ctx); bridge.gauge(pen, t, ctx)
        console(pen, 1300, 1470, 712, sid='helm', label='HELM')
        console(pen, 270, 440, 712, sid='ops', mirror=True, label='OPS')
        console(pen, 1600, 1770, 712, sid='sci', label='SCI')
        if ctx.opt('chair', True): chair(pen, 720)

    @staticmethod
    def fg(pen, t, ctx):
        st = ctx.opt('stamp', None)
        if st: stamp(pen, st[1], (960, 300), t, ctx.ev(st[0]), 70)
        fl = ctx.opt('flicker', None)
        if fl and ctx.ev(fl[0]) <= t < ctx.ev(fl[1]):
            r = np.random.default_rng(int(t * 24))
            for k, x in enumerate((140, 1780)):       # rotating alarm beacons
                a = t * 9 + k; pen.circle((x, 130), 26, 5, INK, f'bea{k}', fill=INK)
                for j in range(2):
                    aa = a + j * math.pi
                    pen.line([(x + 34 * math.cos(aa), 130 + 34 * math.sin(aa) * .4), (x + 120 * math.cos(aa), 130 + 120 * math.sin(aa) * .4)], 4, INK, f'bb{k}{j}')
            if r.uniform() < 0.3 * clamp01((t - ctx.ev(fl[0])) / 1.0) + 0.05:
                pen.img[:] = (pen.img.astype(np.uint16) * 3 // 5).astype(np.uint8)   # lights dip
        if ctx.opt('confetti'):
            r = np.random.default_rng(6)
            for i in range(70):
                x = r.uniform(-100, 2000) + 40 * math.sin(t * 2 + i); y = (r.uniform(-300, 1000) + t * r.uniform(160, 300)) % 1300 - 200
                a = t * r.uniform(2, 6) + i; L = 12
                pen.line([(x - L * math.cos(a), y - L * math.sin(a)), (x + L * math.cos(a), y + L * math.sin(a))], 5, INK, f'cf{i}', wob=0)


# ------------------------------------------------------------------ "Titan, engage" / ENGAGE! punch
class engage(bridge):
    @staticmethod
    def fg(pen, t, ctx):
        bridge.fg(pen, t, ctx)
        te = ctx.ev('engage')
        if t >= te - 0.05:
            u = (t - te + .05)
            k = 1 + 1.6 * (1 - ease_out(min(u / .18, 1)))
            rp = Pen(pen.img, (960, 540, 1.0), pen.boil)
            for i in range(28):    # radial speed lines behind the word
                a = i * 2 * math.pi / 28 + (pen.boil % 2) * .05
                r0 = 420 + 40 * (i % 3)
                rp.line([(960 + r0 * math.cos(a), 470 + r0 * .55 * math.sin(a)), (960 + 1300 * math.cos(a), 470 + 1300 * .55 * math.sin(a))], 6, INK, f'el{i}', wob=.5)
            size = ctx.opt('word_size', 230)
            outlined(rp, ctx.opt('word', 'ENGAGE!'), (960, 470), size * k, 0.06 * size)


# ------------------------------------------------------------------ exterior: ship jumps to / flies at warp
class fullwarp:
    @staticmethod
    def bg(pen, t, ctx):
        tj = ctx.ev('jump'); w = clamp01((t - tj) / .25) if ctx.opt('jumping', True) else 1.0
        stars_field(pen, (-300, -200, 2220, 1280), t, 0.05 + 0.5 * w, n=220, seed=13, col=INK, streak=0.03 + 0.6 * w)
        f = ctx.opt('facing', -1)
        c = list(ctx.opt('c', (960, 520))); sc = ctx.opt('scale', 1.5)
        if ctx.opt('jumping', True) and t > tj:
            u = t - tj; c[0] += f * (u ** 2) * 2400; sc *= 1 - min(u, .8) * .4
        c[1] += 8 * math.sin(t * 7) * w
        for i in range(10):   # speed lines trailing the ship
            y = c[1] - 100 + i * 24; x0 = c[0] - f * (320 + (i % 3) * 60) * sc
            L = (200 + 900 * w) * (0.6 + 0.4 * ((i * 7) % 3))
            pen.line([(x0, y), (x0 - f * L, y)], 3 + 2 * w, INK, f'fs{i}', wob=.4)
        ship(pen, c, sc, sid='fw', facing=f)
        if ctx.opt('jumping', True) and 0 < t - tj < .5:
            burst(pen, (c[0], c[1]), t, tj, 700, 30, INK, 'fwj', .5, 8)
        if ctx.opt('label'): pen.text('U.S.S. TITAN', (c[0], c[1] + 190 * sc / 1.5), 46, INK, 'marker')


# ------------------------------------------------------------------ "The boldest crew the stars have seen": heroic lineup
class heroic:
    @staticmethod
    def bg(pen, t, ctx):
        twinkle_stars(pen, t, 90, seed=8, rect=(-200, -150, 2120, 560))
        c = (960, 870); R = 470
        pen.circle(c, R, 6, INK, 'sun')
        for i in range(36):
            a = math.pi + i * math.pi / 35 + t * 0.02
            pen.line([(c[0] + (R + 30) * math.cos(a), c[1] + (R + 30) * math.sin(a)), (c[0] + (R + 140 + 40 * (i % 2)) * math.cos(a), c[1] + (R + 140 + 40 * (i % 2)) * math.sin(a))], 3, INK, f'sr{i}')
        for k in range(6):
            y = c[1] - 80 - k * 70; half = math.sqrt(max(R * R - (y - c[1]) ** 2, 0))
            pen.line([(c[0] - half + 20, y), (c[0] + half - 20, y)], 2.5, INK, f'sh{k}', wob=.5)
        ridge = [(-300, 900)] + [(x, 880 - 10 * math.sin(x / 140)) for x in range(-300, 2300, 60)] + [(2300, 900), (2300, 1300), (-300, 1300)]
        pen.fill(ridge, PAPER); pen.line(ridge[1:-2], 6, INK, 'ridge')
        ts = ctx.ev('stars')
        for i in range(5):
            u = t - ts - i * .12
            if u > 0: sparkle(pen, (300 + i * 330, 160 + 60 * (i % 2)), 26 * ease_out_back(u / .3), INK, f'hs{i}')


# ------------------------------------------------------------------ mid section: disco / trombone / poker / away mission
class disco:
    @staticmethod
    def bg(pen, t, ctx):
        floor(pen)
        for k in range(-8, 9):   # dance floor perspective
            pen.line([(960 + k * 60, FLOOR), (960 + k * 160, 1120)], 2.5, INK, f'df{k}', wob=.4)
        bx, by = 960, 170
        pen.line([(bx, -60), (bx, by - 60)], 3, INK, 'dbw')
        pen.circle((bx, by), 60, 5, INK, 'db', fill=PAPER)
        for k in range(-2, 3):
            pen.line([(bx - math.sqrt(3600 - (k * 22) ** 2), by + k * 22), (bx + math.sqrt(3600 - (k * 22) ** 2), by + k * 22)], 2, INK, f'dbh{k}', wob=0)
            xx = bx + 52 * math.sin(t * 2 + k * .7)
            pen.line([(xx, by - 55), (xx, by + 55)], 2, INK, f'dbv{k}', wob=0)
        for j, side in enumerate((-1, 1)):    # swinging spotlight cones
            a = side * (0.35 + 0.25 * math.sin(t * 1.7 + j))
            fx = bx + math.tan(a) * (FLOOR - by)
            pen.line([(bx, by + 55), (fx - 120, FLOOR)], 2.5, INK, f'sp{j}a'); pen.line([(bx, by + 55), (fx + 120, FLOOR)], 2.5, INK, f'sp{j}b')
            pen.arc((fx, FLOOR), 120, 18, 0, 360, 2.5, INK, f'spf{j}')
        r = np.random.default_rng(2)
        for i in range(16):   # mirror-ball glints
            a = r.uniform(0, 6.28) + t * .8; d = r.uniform(250, 900)
            p = (bx + d * math.cos(a) * 1.4, by + 200 + d * .5 * math.sin(a))
            if -50 < p[1] < 820: sparkle(pen, p, 7 + 6 * math.exp(-since(BEATS, t) * 8), INK, f'gl{i}')
        if ctx.opt('sign'): pen.text(ctx.opt('sign'), (960, 330), 54, INK, 'marker')

    @staticmethod
    def fg(pen, t, ctx):
        for fid in ctx.opt('notes_from', []):
            h = ctx.hands.get(fid)
            if not h: continue
            for k in range(4):
                u = (t * .8 + k / 4) % 1
                p = (h['head'][0] + 60 + 160 * u, h['head'][1] - 40 - 220 * u + 20 * math.sin(u * 12))
                note(pen, p, 40, 1 - u, f'n{fid}{k}', k % 2 == 0)


class stage:
    @staticmethod
    def bg(pen, t, ctx):
        floor(pen)
        pen.arc((960, FLOOR), 420, 60, 0, 360, 3, INK, 'spot')
        for k in range(14):   # curtain scallops + drapes
            pen.arc((-40 + k * 150, 40), 75, 45, 0, 180, 5, INK, f'cs{k}')
        for side in (-1, 1):
            x0 = 960 + side * 960
            for k in range(4):
                xx = x0 - side * (40 + k * 45)
                pen.line([(xx, 40), (xx - side * 30 * math.sin(t + k), 500), (xx + side * 20, FLOOR)], 4, INK, f'dr{side}{k}')
        if ctx.opt('sign'): pen.text(ctx.opt('sign'), (960, 170), 56, INK, 'marker')

    @staticmethod
    def fg(pen, t, ctx):
        tb = ctx.opt('trombone')
        h = ctx.hands.get(tb) if tb else None
        if h:
            f = 1; mx, my = h['head'][0] + 26, h['head'][1] + 10
            hx = h['hand_r'][0]
            bell = mx + 170
            pen.line([(mx, my), (bell - 40, my)], 5, INK, 'tb1')
            pen.line([(bell - 40, my), (bell, my - 24)], 5, INK, 'tb2'); pen.line([(bell - 40, my), (bell, my + 24)], 5, INK, 'tb3')
            pen.line([(bell, my - 24), (bell, my + 24)], 4, INK, 'tb4')
            pen.line([(mx + 10, my), (mx + 10, my + 26), (hx, my + 26)], 5, INK, 'tbs')   # slide follows the hand
            pen.line([(hx, my + 18), (hx, my + 34)], 5, INK, 'tbh')
            for k in range(5):
                u = (t * .9 + k / 5) % 1
                p = (bell + 40 + 380 * u, my - 30 - 160 * u + 30 * math.sin(u * 14))
                note(pen, p, 46 + 20 * u, 1 - u * u, f'tn{k}', k % 2 == 0)
            tw = ctx.ev('wah')
            if t > tw: pen.text('WAH-WAH!', (bell + 300, my - 210), 60 * ease_out_back((t - tw) / .3) + 1, INK, 'marker')


class poker:
    @staticmethod
    def bg(pen, t, ctx):
        floor(pen)
        pen.line([(960, -50), (960, 180)], 3, INK, 'lw')
        pen.arc((960, 200), 120, 40, 180, 360, 5, INK, 'lamp'); pen.line([(840, 200), (1080, 200)], 5, INK, 'lamp2')
        pen.line([(860, 205), (640, 760)], 2, INK, 'lc1', wob=.6); pen.line([(1060, 205), (1280, 760)], 2, INK, 'lc2', wob=.6)

    @staticmethod
    def fg(pen, t, ctx):
        pen.fill([(960 + 360 * math.cos(a), 780 + 70 * math.sin(a)) for a in np.linspace(0, 6.283, 50)], PAPER)
        pen.arc((960, 780), 360, 70, 0, 360, 6, INK, 'tbl')
        pen.line([(940, 850), (920, FLOOR)], 6, INK, 'tl1'); pen.line([(980, 850), (1000, FLOOR)], 6, INK, 'tl2')
        for k in range(3):   # chip stacks
            x = 860 + k * 90
            for j in range(3 + k): pen.arc((x, 770 - j * 8), 18, 6, 0, 360, 3, INK, f'ch{k}{j}')
        for fid, h in ctx.hands.items():
            if fid in ('grokbot',): continue
            hx, hy = h['hand_r']
            for c in range(3):
                a = -0.4 + c * .35
                pts = [(hx + dx * math.cos(a) - dy * math.sin(a), hy + dx * math.sin(a) + dy * math.cos(a)) for dx, dy in ((-10, -40), (10, -40), (10, 0), (-10, 0))]
                pen.fill(pts, PAPER); pen.line(pts, 2.5, INK, f'cd{fid}{c}', closed=True)
        tr = ctx.ev('reveal')
        if t > tr:
            k = ease_out_back((t - tr) / .3)
            for c in range(4):
                x = 840 + c * 80; y = 735 - 20 * k
                pen.rect(x - 30 * k, y - 44 * k, x + 30 * k, y + 44 * k, 4, INK, f'rv{c}', fill=PAPER)
                pen.text('A', (x, y), 50 * k + 1, INK, 'marker')
            stamp(pen, 'FOUR ACES?!', (960, 420), t, tr + .35, 70)


class planet:
    @staticmethod
    def bg(pen, t, ctx):
        twinkle_stars(pen, t, 60, seed=12, rect=(-200, -150, 2120, 600))
        pen.circle((1500, 230), 120, 5, INK, 'pl', fill=PAPER)
        pen.arc((1500, 230), 230, 40, 190, 350, 5, INK, 'ring1'); pen.arc((1500, 230), 230, 40, -10, 190, 5, INK, 'ring2')
        for k in range(3): pen.line([(1420 + k * 50, 160 + k * 25), (1470 + k * 50, 160 + k * 25)], 2.5, INK, f'plh{k}')
        pen.circle((380, 160), 40, 4, INK, 'm1'); pen.circle((520, 110), 22, 4, INK, 'm2')
        gr = [(-300, 1300), (-300, 880)] + [(x, 870 - 30 * math.sin(x / 300) - 12 * math.sin(x / 90)) for x in range(-300, 2400, 50)] + [(2400, 880), (2400, 1300)]
        pen.fill(gr, PAPER); pen.line(gr[1:-1], 6, INK, 'gr')
        for i, x in enumerate((180, 640, 1350, 1760)):   # alien plants, swaying on beats
            y = 870 - 30 * math.sin(x / 300) - 12 * math.sin(x / 90); sw = 14 * math.sin(t * 2 + i) + 10 * math.exp(-since(BEATS, t) * 6)
            top = (x + sw, y - 170 - 30 * (i % 2))
            pen.line([(x, y), ((x + top[0]) / 2 - 10, y - 90), top], 5, INK, f'pst{i}')
            pen.circle(top, 26, 5, INK, f'pbl{i}', fill=PAPER)
            for k in range(5):
                a = k * 2 * math.pi / 5 + t; pen.line([(top[0] + 26 * math.cos(a), top[1] + 26 * math.sin(a)), (top[0] + 42 * math.cos(a), top[1] + 42 * math.sin(a))], 3, INK, f'psp{i}{k}')
        for fid, tb in ctx.opt('beam', {}).items():   # beam-in sparkle columns
            tb = ctx.ev(tb); x = ctx.shot['figs'][fid].pos_at(tb + .01)[0]
            u = t - tb + .6
            if 0 < u < 1.0:
                a = math.sin(math.pi * u)
                for k in range(8):
                    yy = 560 + ((k * 47 + t * 400) % 330)
                    sparkle(pen, (x + 22 * math.sin(k * 2.1 + t * 9), yy), 10 * a, INK, f'bm{fid}{k}')
                pen.line([(x - 50, 520), (x - 50, 880)], 3 * a + .5, INK, f'bml{fid}'); pen.line([(x + 50, 520), (x + 50, 880)], 3 * a + .5, INK, f'bmr{fid}')

    @staticmethod
    def fg(pen, t, ctx):
        bl = ctx.opt('blob')
        if bl:
            x = lerp(bl[0], bl[1], ease(clamp01((t - ctx.shot['t']) / (ctx.shot['end'] - ctx.shot['t']))))
            hop = 40 * abs(math.sin(math.pi * beat_ph(t)))
            y = 862 - hop; sq = 1 + .25 * math.exp(-since(BEATS, t) * 10)
            pts = [(x + 46 * sq * math.cos(a), y - 34 / sq - 34 / sq * math.sin(a) + 4 * math.sin(a * 5 + t * 8)) for a in np.linspace(0, 2 * math.pi, 30)]
            pen.fill(pts, PAPER); pen.line(pts, 5, INK, 'blob', closed=True)
            for dx in (-14, 14): pen.circle((x + dx, y - 44 / sq), 8, 3, INK, f'be{dx}', fill=PAPER); pen.dot((x + dx + 2, y - 44 / sq), 3.5, INK)
            pen.arc((x, y - 24 / sq), 12, 7, 20, 160, 3, INK, 'bsm')
            pen.line([(x - 6, y - 66 / sq), (x - 16, y - 92 / sq)], 3, INK, 'ba1'); pen.dot((x - 16, y - 92 / sq), 5, INK)


def note(pen, p, size, alpha, sid, double=False):
    if alpha <= 0.05: return
    s = size / 40; w = 4 * s
    xs = (0, 26 * s) if double else (0,)
    for x in xs:
        pen.circle((p[0] + x - 9 * s, p[1] + 14 * s), 9 * s, 0, fill=INK)
        pen.line([(p[0] + x, p[1] + 14 * s), (p[0] + x, p[1] - 22 * s)], w, INK, sid + f's{x:.0f}')
    if double: pen.line([(p[0], p[1] - 22 * s), (p[0] + 26 * s, p[1] - 26 * s)], w * 1.4, INK, sid + 'bm')
    else: pen.line([(p[0], p[1] - 22 * s), (p[0] + 12 * s, p[1] - 8 * s)], w, INK, sid + 'fl')


def beat_ph(t):
    i = np.searchsorted(BEATS, t, side='right') - 1
    if i < 0 or i + 1 >= len(BEATS): return 0.0
    return (t - BEATS[i]) / (BEATS[i + 1] - BEATS[i])


# ------------------------------------------------------------------ verse 1 (legacy render.py, wrapped unchanged)
class legacy_verse:
    @staticmethod
    def bg(pen, t, ctx):
        import render
        pen.img[:] = render.render_frame(t)


# ------------------------------------------------------------------ finale: Titan flies off, end card, ink fades to paper
class finale:
    @staticmethod
    def bg(pen, t, ctx):
        t0 = ctx.shot['t']; u = clamp01((t - t0) / (ctx.ev('gone') - t0))
        twinkle_stars(pen, t, 160, seed=21, drift=10)
        c = (lerp(820, 1380, ease(u)), lerp(560, 380, ease(u))); sc = lerp(1.25, 0.12, ease(u) ** .8)
        if sc > 0.15:
            for i in range(5):
                y = c[1] - 40 * sc + i * 22 * sc
                pen.line([(c[0] + 330 * sc, y), (c[0] + (330 + 500) * sc, y)], 3, INK, f'tr{i}', wob=.4)
            ship(pen, c, sc, sid='fin')
        else:
            sparkle(pen, c, 14, INK, 'fin_spark')
        for key, txt, y, size, font in (('card1', 'U.S.S. TITAN', 700, 120, 'marker'), ('card2', '- Bridge Theme -', 820, 60, 'hand'),
                                        ('card3', 'music by PinkSprinkleMagic', 905, 46, 'hand')):
            tk = ctx.ev(key); n = int(clamp01((t - tk) / .9) * len(txt))
            if n: pen.text(txt[:n], (960 - (len(txt) - n) * size * 0.27, y), size, INK, font)

    @staticmethod
    def fg(pen, t, ctx):
        a = clamp01((t - ctx.ev('fade')) / 1.2)
        if a > 0:
            pen.img[:] = (pen.img.astype(np.float32) * (1 - a) + np.array(PAPER, np.float32) * a).astype(np.uint8)
