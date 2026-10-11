"""Dialogue short #2: "THE WEBHOOK" - Grok Bot wires a webhook to the Enterprise-D; Picard gets spammed.
Same pipeline as demo1 (timeline.json from build_audio.py -> cue table -> frames).
    python webhook.py                 # full render (parallel parts, captions, audio, cover-free mp4)
    python webhook.py --frames 1.2 ...  # raw check PNGs (no captions), times are VIDEO times (poster hold included)
    python webhook.py --poster        # thumbnail.png/.jpg
"""
import sys, os, json, math, subprocess, time
SP = '/workspace/holodeck/titan-hello-world/stick-poc'; sys.path.insert(0, SP)
import numpy as np, cv2
cv2.setNumThreads(1)
from stickfig import *
from inkset import W, H, FLOOR, console, paper_finish, sparkle, stars_field
import sets as SETS
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(f'{HERE}/timeline.json')); FPS = 24; SCENE = TL['total']; HOLD, WIPE = 0.5, 0.33; TOTAL = SCENE + HOLD
ENV = {k: np.array(v) for k, v in TL['env'].items()}
WT = {L['id']: {} for L in TL['lines']}
for L in TL['lines']:
    for x in L['words']: WT[L['id']].setdefault(x['w'].strip('.,!?').lower(), x['s'])
LN = {L['id']: L for L in TL['lines']}
def w(line, word, off=0.0): return WT[line][word] + off
SC = 1.4; STAND = FLOOR - 110 * SC; SEATY = FLOOR - 58 * SC
CHAIR_X = 815

# ------------------------------------------------------------------ cue table
T_SIT = 3.5            # Riker lands in the chair (backwards)
CUT_E1 = LN['p1']['s'] - .15; CUT_R = LN['r1']['s'] - .15; CUT_E2 = LN['p2']['s'] - .2
CUT_G = LN['g2']['s'] - .15; CUT_AV = w('g2', 'backoff', -.25)
KEYS = dict(
    riker=[(0, 'idle', 0), (w('g1', 'live'), 'idle+look_r+lookup=.4', .3), (2.15, 'idle', .2), (3.05, 'legover', .25), (T_SIT - .05, 'straddle', .25),
           (4.0, 'straddle+mouth=2', .2), (w('r1', 'technically', -.3), 'straddle+chinrub', .3), (w('r1', 'backwards', -.15), 'straddle+thumbs', .25),
           (LN['r1']['e'] + .1, 'straddle+mouth=2', .2), (CUT_G, 'straddle+look_r+mouth=1', .2)],
    grokbot=[(0, 'console', 0), (w('g1', 'live', -.15), 'tada', .2), (w('g1', 'every', -.1), 'pointup', .3), (3.3, 'idle+look_l', .3),
             (w('g1', 'admiral'), 'thumbs', .25), (CUT_R, 'thumbs', .1), (LN['r1']['e'], 'idle', .3),
             (w('g2', 'unsubscribe', -.2), 'shrug', .25), (w('g2', 'retrying', -.2), 'thumbs', .25), (w('g2', 'backoff', -.2), 'tada', .2)],
    picard=[(0, 'front', 0), (w('p1', 'will', -.2), 'front+rsh=40+rel=110', .3), (w('p1', 'four', -.2), 'present+mouth=0', .3),
            (w('p1', 'sat', -.2), 'front+tilt=-8+lookup=-.3', .3), (CUT_R, 'front+tilt=-8', .1),
            (w('p2', 'make', -.25), 'facepalmF', .25), (w('p2', 'unsubscribe', -.2), 'front+rsh=70+rel=100+tilt=4', .25),
            (w('p2', 'immediately', -.1), 'front+rsh=88+rel=0+lsh=20', .25), (CUT_AV - .1, 'facepalm2', .25)],
)
NODS = dict(riker=[w('g1', 'pings')], grokbot=[w('r1', 'backwards', .2)], picard=[])
SHOTS = [   # (at, set, camera keys [(t, (cx, cy, zoom), ease)])
    (0.0, 'titan', [(0.0, (960, 520, 1.08), 0), (0.0, (960, 545, 1.16), CUT_E1)]),
    (CUT_E1, 'ent', [(CUT_E1, (960, 520, 1.0), 0), (CUT_E1, (930, 520, 1.06), 3.8)]),
    (CUT_R, 'titan', [(CUT_R, (880, 640, 2.0), 0), (CUT_R, (870, 650, 2.12), 2.6)]),
    (CUT_E2, 'ent', [(CUT_E2, (900, 540, 1.1), 0), (w('p2', 'make', -.1), (700, 625, 1.45), .25), (w('p2', 'unsubscribe', -.2), (930, 530, 1.06), .6)]),   # keep ES bottom (890) above the caption band
    (CUT_G, 'titan', [(CUT_G, (1120, 610, 1.9), 0), (CUT_G, (1110, 600, 2.0), 2.5)]),
    (CUT_AV, 'ent', [(CUT_AV, (960, 520, 1.0), 0)]),
]
SHOTS = [dict(at=a, set=s, cam=c) for a, s, c in SHOTS]
for i, s in enumerate(SHOTS): s['end'] = SHOTS[i + 1]['at'] if i + 1 < len(SHOTS) else 1e9

# notifications: arrival times (scene s) + text
T_LIVE = w('g1', 'live')
ARR = [T_SIT + .05, T_SIT + .4]
t = T_SIT + .8
while t < CUT_AV: ARR.append(round(t, 3)); t += max(.22, .55 - .03 * len(ARR)) if t < CUT_G else 0.5
for rt in (w('g2', 'retrying'), w('g2', 'with'), w('g2', 'exponential')): ARR += [rt, rt + .08]
ARR = sorted(ARR)
MSG = ["Riker sat down.", "Riker sat down... BACKWARDS.", "Riker stood up.", "Riker sat down.", "Grok Bot says hi!", "Riker leaned on the chair.",
       "Riker sat down... BACKWARDS.", "Lights dimmed 2%.", "Riker sat down.", "Riker crossed his arms.", "Riker sat down.", "Grok Bot says hi again!"]

def counter(t):
    if t < ARR[0]: return 0
    t400 = w('p1', 'hundred', .2)
    if t < t400: return int(2 + 398 * ((t - ARR[0]) / (t400 - ARR[0])) ** 2.2)
    if t < w('g2', 'retrying'): return int(400 + 26 * (t - t400))
    if t < CUT_AV: return int((400 + 26 * (w('g2', 'retrying') - t400)) * 2 ** ((t - w('g2', 'retrying')) * 4))
    return 9999

def make_mod(who):
    env = ENV.get(who, np.zeros(1)); nods = NODS.get(who, [])
    def f(t, P):
        i = int(t * FPS); e = float(env[i]) if i < len(env) else 0.0
        e2 = float(env[max(i - 2, 0)]) if i < len(env) else 0.0
        P['talk'] = e; P['tilt'] += 7 * (e - e2) + 3 * e; P['lean'] += 2.5 * e * (1 - P['front'])
        for tn in nods:
            u = t - tn
            if 0 <= u < .7: P['tilt'] += 12 * math.sin(math.pi * u / .35) * (1 - u / .7)
        if who == 'riker' and 2.15 <= t < 3.0:      # walk to the chair
            ph = math.sin(2 * math.pi * 2.3 * (t - 2.15)); k = min(1, (t - 2.15) / .15, (3.0 - t) / .15)
            P['lhip'] += 24 * ph * k; P['rhip'] -= 24 * ph * k; P['lsh'] -= 18 * ph * k; P['rsh'] += 18 * ph * k
        return P
    return f

def fig(who, x, y, facing, props, **kw):
    F = Figure(who, x, y, facing, set(props), **kw)
    for k in KEYS[who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    F.mod = make_mod(who); return F

RIKER = fig('riker', 560, STAND, 1, ['beard', 'badge'], scale=SC)
RIKER.move(2.15, 735, STAND, .85); RIKER.move(T_SIT - .3, CHAIR_X - 20, SEATY, .3)
GROK = fig('grokbot', 1180, STAND, -1, ['robot'], scale=SC)
PIC_BIG = fig('picard', 640, 880, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=3.3)
PIC_BIG.move(CUT_AV + .9, 640, 990, 1.0)          # sinks behind the desk under the avalanche
PIC_MINI = fig('picard', 830, 505, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=1.0)


# ------------------------------------------------------------------ drawing helpers
def bell(pen, c, s, col, sid):
    x, y = c
    pts = [(x - 14 * s, y + 10 * s), (x - 11 * s, y - 6 * s), (x - 6 * s, y - 13 * s), (x, y - 15 * s), (x + 6 * s, y - 13 * s), (x + 11 * s, y - 6 * s), (x + 14 * s, y + 10 * s)]
    pen.line(pts, 3 * s ** .5, col, sid, closed=True); pen.dot((x, y + 14 * s), 3.5 * s, col); pen.dot((x, y - 17 * s), 2.5 * s, col)

def bubble(pen, x, y, wdt, hgt, txt, size, sid, ang=0.0, col=INK, bg=PAPER, icon=True):
    ca, sa = math.cos(ang), math.sin(ang)
    R = lambda px, py: (x + px * ca - py * sa, y + px * sa + py * ca)
    r = hgt * .3; pts = []
    for cx, cy, a0 in ((wdt / 2 - r, -hgt / 2 + r, -90), (wdt / 2 - r, hgt / 2 - r, 0), (-wdt / 2 + r, hgt / 2 - r, 90), (-wdt / 2 + r, -hgt / 2 + r, 180)):
        pts += [R(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in np.linspace(a0, a0 + 90, 5)]
    pen.fill(pts, bg); pen.line(pts, 3.5, col, sid, closed=True)
    if icon: bell(pen, R(-wdt / 2 + hgt * .5, 0), hgt / 52, col, sid + 'b')
    if txt: pen.text(txt, R(-wdt / 2 + hgt * .95, 0), size, col, 'hand', anchor='l')

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

def bolt(pen, p, a, s, col, sid):
    d = [(0, -1), (.5, -.1), (-.2, .1), (.4, 1)]
    ca, sa = math.cos(a), math.sin(a)
    pen.line([(p[0] + (x * ca - y * sa) * 22 * s, p[1] + (x * sa + y * ca) * 22 * s) for x, y in d], 4, col, sid, wob=.3)

def along(path, u):
    P = np.array(path, float); seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
    i = min(np.searchsorted(s, u, 'right') - 1, len(seg) - 1); k = (u - s[i]) / max(s[i + 1] - s[i], 1e-6)
    return tuple(P[i] + (P[i + 1] - P[i]) * k), math.atan2(*(P[i + 1] - P[i])[::-1])

def chair(pen, cx, s=SC):
    sy = FLOOR - 52 * s
    pen.line([(cx - 52 * s, sy), (cx + 40 * s, sy)], 6, INK, 'seat')
    back = [(cx + 34 * s, sy), (cx + 40 * s, FLOOR - 152 * s), (cx + 56 * s, FLOOR - 152 * s), (cx + 50 * s, sy)]
    pen.fill(back, PAPER); pen.line(back, 5, INK, 'cback', closed=True)
    pen.line([(cx - 6 * s, sy), (cx - 6 * s, FLOOR)], 6, INK, 'ped'); pen.line([(cx - 44 * s, FLOOR), (cx + 32 * s, FLOOR)], 6, INK, 'cbase')


# ------------------------------------------------------------------ set: Titan bridge (world = demo1 layout)
VS = (610, 110, 1310, 470)
class Ctx:
    shot = {'opt': {'gauge_level': .7}}
    def opt(self, k, d=None): return self.shot['opt'].get(k, d)
CTX = Ctx()

def titan_screen(pen, img, t):
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vsframe')
    sub = np.full_like(img, INK); sp = Pen(sub, pen.cam, pen.boil)
    if t < T_LIVE - .05:
        stars_field(sp, VS, t, 0.05, n=70)
    else:
        u = max(t - T_LIVE, 0.0)
        if u > .15 or int(u * 40) % 2:
            sp.text('U.S.S. ENTERPRISE-D', (630, 140), 26, PAPER, 'marker', anchor='l')
            PIC_MINI.draw(sp, t, 0, w=4)
            sp.rect(690, 432, 980, 480, 4, PAPER, 'mdesk', fill=INK)
            sp.text('ADM. PICARD', (835, 452), 18, PAPER, 'marker')
            n = sum(1 for a in ARR if a <= t)
            for j, a in enumerate([a for a in ARR if a <= t][-7:][::-1]):
                k = ease_out(clamp01((t - a) / .18))
                bubble(sp, 1170 + 160 * (1 - k), 160 + j * 42 * 1, 230, 34, None, 0, f'mb{j}', icon=True)
                sp.line([(1090 + 160 * (1 - k), 160 + j * 42), (1260 + 160 * (1 - k), 160 + j * 42)], 2.5, INK, f'mbl{j}', wob=.4)
            if n:
                bell(sp, (1150, 134), .8, PAPER, 'mbell'); sp.text(str(counter(t)), (1175, 134), 26, PAPER, 'marker', anchor='l')
        if u < .4:
            r = np.random.default_rng(int(u * 48))
            for i in range(10):
                yy = r.uniform(y0, y1); sp.line([(x0, yy), (x1, yy)], r.uniform(2, 6), PAPER, f'st{i}', wob=2)
    clip_paste(img, sub, pen, VS)

def titan(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen); titan_screen(pen, img, t)
    pen.line([(-600, 60), (520, 60), (580, 100)], 4, INK, 'rail1'); pen.line([(1340, 100), (1400, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (960, 58), 44, INK, 'marker')
    SETS.bridge.minis(pen, t, CTX); SETS.bridge.gauge(pen, t, CTX)
    console(pen, 1400, 1570, 712, sid='helm', label='HELM'); console(pen, 230, 400, 712, sid='ops', mirror=True, label='OPS')
    console(pen, 1660, 1830, 712, sid='sci', label='SCI')
    chair(pen, CHAIR_X)
    hands = {'riker': RIKER.draw(pen, t, 0, w=5.5 * SC ** .3), 'grokbot': GROK.draw(pen, t, 0, w=5.5 * SC ** .3)}
    # the webhook cable: Grok Bot's hand -> viewscreen corner, bolts ride it on every event
    hx, hy = hands['grokbot']['hand_r']
    path = [(hx, hy)] + [(lerp(hx, 1318, k) + 10 * math.sin(k * 9), lerp(hy, 478, k) + 70 * math.sin(math.pi * k)) for k in np.linspace(.15, 1, 8)]
    pen.line(path, 5, INK, 'cable', wob=.6)
    pen.rect(hx - 10, hy - 8, hx + 10, hy + 8, 0, fill=INK)
    for a in [T_LIVE] + ARR:
        u = (t - (a - .3)) / .3
        if 0 <= u <= 1:
            p, ang = along(path, u); bolt(pen, p, ang, 1.0, INK, f'bolt{a}')
        if 1 < u < 1.6: SETS.burst(pen, (1310, 470), t, a, 50, 10, INK, f'zap{a}', .35, 3)
    # POST line
    s = 'POST /picard  ->  200 OK'; n = int(clamp01((t - T_LIVE) / .6) * len(s))
    if n: pen.text(s[:n], (1350, 520), 34, INK, 'marker', anchor='l')
    if t > T_LIVE + .6: SETS.check(pen, (1330 + 32 * len(s) * .55 + 70, 518), 1.1, 'pchk')
    # retry ticker (Grok Bot's close-up during "retrying with exponential backoff")
    tr = w('g2', 'retrying', -.1)
    if t > tr:
        k = ease_out_back(clamp01((t - tr) / .25))
        cx, cy = 880, 465
        pen.rect(cx - 150 * k, cy - 100 * k, cx + 150 * k, cy + 100 * k, 5, INK, 'rcard', fill=PAPER)
        if k > .9:
            for j, (lab, tt) in enumerate((('RETRY #1 ... 1s', tr), ('RETRY #2 ... 2s', w('g2', 'with')), ('RETRY #3 ... 4s', w('g2', 'exponential')), ('RETRY #4 ... 8s', w('g2', 'backoff')))):
                if t > tt: pen.text(lab, (cx - 132, cy - 72 + j * 30), 27, INK, 'hand', anchor='l')
            # exponential curve doodle
            pts = [(cx + 50 + 85 * x, cy + 88 - 75 * (2 ** (4 * x) - 1) / 15) for x in np.linspace(0, clamp01((t - tr) / 1.2), 12)]
            if len(pts) > 1: pen.line(pts, 4, INK, 'expo')
    # notification "ding" over the screen when Riker sits
    if T_SIT <= t < T_SIT + .9:
        k = ease_out_back(clamp01((t - T_SIT) / .2)); a = 1 - clamp01((t - T_SIT - .6) / .3)
        pen.text('DING!', (1250, 85), 46 * k + 2, INK, 'marker', alpha=a)
    return img, hands


# ------------------------------------------------------------------ set: Enterprise-D viewscreen (full frame)
ES = (70, 40, 1850, 860)
def ent(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    pen.rect(ES[0] - 16, ES[1] - 16, ES[2] + 16, ES[3] + 16, 6, INK, 'eframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    stars_field(sp, ES, t, 0.015, n=110, seed=21)
    sp.text('U.S.S. ENTERPRISE-D  //  READY ROOM', (120, 95), 40, PAPER, 'marker', anchor='l')
    PIC_BIG.draw(sp, t, 0, w=8)
    sp.rect(240, 700, 1060, 980, 6, PAPER, 'desk', fill=INK)
    sp.line([(280, 740), (1020, 740)], 3, PAPER, 'desk2')
    sp.text('ADM. PICARD  //  U.S.S. ENTERPRISE', (650, 805), 40, PAPER, 'marker')
    # tea, obviously
    sp.line([(930, 700), (925, 640), (985, 640), (980, 700)], 5, PAPER, 'tea'); sp.arc((995, 670), 16, 18, -80, 80, 5, PAPER, 'teah')
    for k in range(2): sp.line([(942 + k * 20 + 5 * math.sin(t * 3 + yy / 9), 630 - yy) for yy in range(0, 50, 6)], 2.5, PAPER, f'stm{k}')
    # notification stack
    vis = [a for a in ARR if a <= t]
    for i, a in enumerate(vis):
        rank = sum(ease(clamp01((t - b) / .15)) for b in vis[i + 1:])
        y = 205 + 92 * rank
        if y > ES[3] + 60: continue
        k = ease_out(clamp01((t - a) / .2))
        bubble(sp, 1500 + 420 * (1 - k), y, 640, 74, MSG[ARR.index(a) % len(MSG)], 34, f'nb{i}')
    n = counter(t)
    if n:
        pulse = 1 + .25 * math.exp(-(t - vis[-1]) * 10) if vis else 1
        sp.circle((1700, 105), 44 * pulse, 4, PAPER, 'cbadge', fill=PAPER)
        sp.text('9999+' if n >= 9999 else str(n), (1700, 105), (30 if n >= 1000 else 38) * pulse, INK, 'marker')
        bell(sp, (1615, 105), 1.1, PAPER, 'ebell')
    # avalanche: bubbles rain down and bury the screen
    if t > CUT_AV:
        r = np.random.default_rng(5)
        for i in range(70):
            d = r.uniform(0, 1.3); u = t - CUT_AV - d
            if u < 0: continue
            x = r.uniform(120, 1800); yl = r.uniform(300, 900); y = min(-60 + 1400 * u * u + 300 * u, yl)
            bubble(sp, x, y, 440, 64, MSG[i % len(MSG)], 28, f'av{i}', ang=r.uniform(-.25, .25))
    clip_paste(img, sub, pen, ES)
    return img, {}


# ------------------------------------------------------------------ frame assembly
def cam_at(sh, t):
    keys = sh['cam']; cam = keys[0][1]
    for i, (tk, c, dur) in enumerate(keys):
        if t < tk: break
        prev = cam if i else c
        k = ease((t - tk) / dur) if dur > 0 else 1.0
        cam = tuple(lerp(a, b, k) for a, b in zip(prev, c))
    return cam

VIG, GRAINS = paper_finish()
def finish(img, boil, fade=1.0):
    f = img.astype(np.float32) * VIG + GRAINS[boil % 4]
    if fade < 1: f = f * fade + np.array(PAPER, np.float32) * (1 - fade)
    return np.clip(f, 0, 255).astype(np.uint8)

def scene(t):
    sh = next(s for s in SHOTS if s['at'] <= t < s['end'])
    img, _ = (titan if sh['set'] == 'titan' else ent)(t, cam_at(sh, t))
    return finish(img, int(t * 12), clamp01((SCENE - t) / .4))


def poster():
    """split: Titan (Riker backwards in the chair, Grok Bot with the cable) | Enterprise (Picard facepalm, buried in alerts)."""
    tt = 12.5                                         # Picard mid-facepalm, ~550 alerts
    a, _ = titan(5.0, (990, 640, 1.2))
    b, _ = ent(tt, (1120, 470, .82))
    img = np.concatenate([a[:, 480:1440], b[:, 480:1440]], 1)
    pen = Pen(img, (960, 540, 1.0), 3)
    yy = np.linspace(0, 900, 30)                       # ink zigzag divider
    pen.line([(960 + 10 * math.sin(y / 37), y) for y in yy], 12, INK, 'div', wob=1.5)
    pen.rect(380, 925, 1540, 1074, 0, fill=PAPER)
    SETS.outlined(pen, 'THE WEBHOOK', (960, 970), 110, 7)
    pen.line([(610, 1026), (1310, 1021)], 5, INK, 'tul')
    pen.text('Riker  \u00d7  Grok Bot  \u00d7  Picard', (960, 1052), 38, INK, 'hand')
    return finish(img, 3)

_POSTER = None
def render(T):
    global _POSTER
    if _POSTER is None: _POSTER = poster()
    if T < HOLD: return _POSTER.copy()
    sc = scene(T - HOLD)
    if T >= HOLD + WIPE: return sc
    u = ease_out((T - HOLD) / WIPE); yy = np.arange(H)
    edge = -200 + u * (W + 400) + 40 * np.sin(yy / 90 + 1.3) + 16 * np.sin(yy / 23 + .4)
    xs = np.arange(W)[None, :]; e = edge[:, None]
    out = np.where((xs < e - 70)[..., None], sc, _POSTER)
    band = (np.abs(xs - e) < 70) & ~((np.sin(yy / 3.1)[:, None] * np.sin(yy / 11.7)[:, None] > .55) & (np.abs(xs - e) > 40))
    out[band] = INK
    return out


def captions(path):
    INKc, GREY, PAPERc = '&H00141618', '&H00A8A8A8', '&H00E6EEF3'
    def ts(x): x = max(x, 0); return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Line,Exo 2,58,{INKc},{GREY},{PAPERc},&H00000000,1,0,0,0,100,100,1,0,1,6,0,2,90,90,42,1
Style: Name,Permanent Marker,52,{INKc},{INKc},{PAPERc},&H00000000,0,0,0,0,100,100,2,0,1,5,0,2,90,90,112,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'picard': 'PICARD'}; ev = []; Ls = TL['lines']
    for i, L in enumerate(Ls):
        ws = [dict(x, s=x['s'] + HOLD, e=x['e'] + HOLD) for x in L['words']]; a = L['s'] + HOLD - 0.2
        nxt = Ls[i + 1]['s'] + HOLD - 0.2 if i + 1 < len(Ls) else TOTAL - .3
        b = min(L['e'] + HOLD + 0.5, nxt)
        kt = [f"{{\\k{int((ws[0]['s'] - a) * 100)}}}"]
        for j, x in enumerate(ws):
            end = ws[j + 1]['s'] if j + 1 < len(ws) else x['e']
            kt.append(f"{{\\kf{max(int((end - x['s']) * 100), 1)}}}{x['w']} ")
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Line,,0,0,0,,{{\\fad(120,200)\\move(960,1052,960,1038,0,180)}}" + ''.join(kt).strip())
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Name,,0,0,0,,{{\\fad(120,200)\\pos(960,972)\\fscx90\\fscy90\\t(0,140,\\fscx100\\fscy100)}}{names[L['who']]}")
    open(path, 'w').write(hdr + '\n'.join(ev) + '\n')


def render_part(k, n, out):
    NF = int(round(TOTAL * FPS)); f0, f1 = NF * k // n, NF * (k + 1) // n
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '11', '-tune', 'animation', '-pix_fmt', 'yuv420p', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(f0, f1): p.stdin.write(render(i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == '__main__':
    if '--poster' in sys.argv:
        im = poster(); cv2.imwrite(f'{HERE}/thumbnail.png', im); cv2.imwrite(f'{HERE}/thumbnail.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 92]); sys.exit()
    if '--frames' in sys.argv:
        for a in sys.argv[sys.argv.index('--frames') + 1:]: cv2.imwrite(f'{HERE}/raw_{a}.png', render(float(a)))
        sys.exit()
    if '--part' in sys.argv:
        k, n = (int(x) for x in sys.argv[sys.argv.index('--part') + 1:][:2]); render_part(k, n, f'{HERE}/parts/p{k:02d}.mp4'); sys.exit()
    st = time.time(); os.makedirs(f'{HERE}/parts', exist_ok=True); n = 6
    captions(f'{HERE}/captions.ass')
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    ps = [subprocess.Popen([sys.executable, __file__, '--part', str(k), str(n)], env=env) for k in range(n)]
    if any(p.wait() for p in ps): sys.exit('part failed')
    open(f'{HERE}/parts/list.txt', 'w').write(''.join(f"file 'p{k:02d}.mp4'\n" for k in range(n)))
    out = f'{HERE}/webhook-picard.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
