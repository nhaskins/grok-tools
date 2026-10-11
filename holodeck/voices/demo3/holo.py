"""Dialogue short #3: "HOLODECK PROGRAM 01" - Lt. Barclay unveils his stick-figure holodeck program (meta).
Same pipeline as demo1/2 (timeline.json from build_audio.py -> cue table -> frames).
    python holo.py | --frames t ... (video times) | --poster
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
SC = 1.4; STAND = FLOOR - 110 * SC

# ------------------------------------------------------------------ cue table
T_PROG = w('b1', 'program', -.05)            # program window materializes
T_GB_IN = LN['g1']['s'] - .75                 # Grok Bot walks in from the right
T_FAINT = LN['p1']['e'] + .35
CUT_R = LN['r1']['s'] - .15; CUT_B = LN['b2']['s'] - .15; CUT_G = LN['g1']['s'] - .55; CUT_P = LN['p1']['s'] - .15; CUT_END = LN['p1']['e'] + .05
KEYS = dict(
    barclay=[(0, 'hunch', 0), (w('b1', 'commander', -.2), 'hunch+mouth=1', .2), (w('b1', 'show', -.2), 'present_padd', .3),
             (w('b1', 'program', .5), 'hunch+mouth=1', .3), (w('r1', 'why', -.1), 'nervous', .25),
             (w('b2', 'art', -.2), 'present_padd', .25), (w('b2', 'paper', -.2), 'hunch', .25), (w('b2', 'four', -.15), 'present_padd+mouth=1', .2),
             (LN['g1']['s'] + .3, 'hunch+look_r', .3), (CUT_END, 'hunch+mouth=2+lookup=.4', .2), (T_FAINT, 'faint', .32)],
    riker=[(0, 'idle', 0), (w('b1', 'program', .2), 'idle+look_l+lookup=.6', .3), (w('r1', 'mister', -.2), 'chinrub', .3),
           (w('r1', 'stick', -.2), 'point+lookup=.5', .2), (LN['r1']['e'] + .2, 'idle', .4), (w('b2', 'grain'), 'chinrub', .4),
           (LN['g1']['s'] + .2, 'idle+look_r', .3), (CUT_END, 'idle', .2), (T_FAINT + .25, 'surprise', .2)],
    grokbot=[(0, 'idle', 0), (w('g1', 'feature', -.15), 'wave', .2), (w('g1', 'more', -.15), 'pointup', .25), (w('g1', 'please', -.1), 'thumbs', .2),
             (CUT_END, 'idle+look_l', .2), (T_FAINT + .3, 'thumbs', .2)],
    picard=[(0, 'front+rsh=40+rel=110+padd=1', 0), (w('p1', 'three', -.2), 'front+rsh=40+rel=110+padd=1+tilt=6', .3),
            (w('p1', 'make', -.25), 'front+rsh=10+rel=10+lsh=95+lel=-20+padd=0', .25)],
)
NODS = dict(riker=[w('b1', 'program', .1), w('g1', 'please')], barclay=[w('r1', 'figure', .1), w('p1', 'budget', .1)], grokbot=[], picard=[w('p1', 'sequel', .1)])
SHOTS = [
    (0.0, 'holo', [(0.0, (960, 500, 1.04), 0), (0.0, (960, 530, 1.12), CUT_R)]),
    (CUT_R, 'holo', [(CUT_R, (1150, 560, 1.65), 0), (CUT_R, (1150, 570, 1.75), 2.5)]),
    (CUT_B, 'holo', [(CUT_B, (790, 560, 1.65), 0), (w('b2', 'paper', -.3), (840, 520, 1.55), 1.0)]),
    (CUT_G, 'holo', [(CUT_G, (1230, 510, 1.22), 0), (CUT_G, (1270, 520, 1.3), 3.4)]),
    (CUT_P, 'ent', [(CUT_P, (960, 500, 1.0), 0), (w('p1', 'make', -.2), (900, 520, 1.12), .5)]),
    (CUT_END, 'holo', [(CUT_END, (960, 520, 1.06), 0)]),
]
SHOTS = [dict(at=a, set=s, cam=c) for a, s, c in SHOTS]
for i, s in enumerate(SHOTS): s['end'] = SHOTS[i + 1]['at'] if i + 1 < len(SHOTS) else 1e9

def make_mod(who):
    env = ENV.get(who, np.zeros(1)); nods = NODS.get(who, [])
    def f(t, P):
        i = int(t * FPS); e = float(env[i]) if i < len(env) else 0.0
        e2 = float(env[max(i - 2, 0)]) if i < len(env) else 0.0
        P['talk'] = e; P['tilt'] += 7 * (e - e2) + 3 * e; P['lean'] += 2.5 * e * (1 - P['front'])
        for tn in nods:
            u = t - tn
            if 0 <= u < .7: P['tilt'] += 12 * math.sin(math.pi * u / .35) * (1 - u / .7)
        if who == 'barclay' and t < T_FAINT:            # nervous jitter
            P['tilt'] += 2.2 * math.sin(t * 2 * math.pi * 4.7); P['lsh'] += 3 * math.sin(t * 2 * math.pi * 6.1)
        if who == 'grokbot' and T_GB_IN <= t < T_GB_IN + .75:
            ph = math.sin(2 * math.pi * 2.6 * (t - T_GB_IN)); k = min(1, (t - T_GB_IN) / .12, (T_GB_IN + .75 - t) / .12)
            P['lhip'] += 24 * ph * k; P['rhip'] -= 24 * ph * k
        return P
    return f

def fig(who, x, y, facing, props, **kw):
    F = Figure(who, x, y, facing, set(props), **kw)
    for k in KEYS[who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    F.mod = make_mod(who); return F

BARCLAY = fig('barclay', 640, STAND, 1, ['curly', 'badge'], scale=SC)
BARCLAY.move(T_FAINT, 610, FLOOR - 14, .32)
RIKER = fig('riker', 1290, STAND, -1, ['beard', 'badge'], scale=SC)
GROK = fig('grokbot', 2150, STAND, -1, ['robot'], scale=SC)
GROK.move(T_GB_IN, 1680, STAND, .75)
PIC = fig('picard', 640, 880, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=3.3)

# mini cast inside the holodeck program window (the meta joke: they are stick figures in a stick figure)
MINI_R = Figure('mr', 870, 420, 1, {'beard', 'badge'}, scale=.95); MINI_R.key(-1e8, 'stand', 0)
MINI_R.key(w('r1', 'stick', -.2), 'point', .2); MINI_R.key(LN['r1']['e'] + .4, 'stand', .3)
MINI_G = Figure('mg', 1060, 420, -1, {'robot'}, scale=.95); MINI_G.key(-1e8, 'stand', 0); MINI_G.key(w('g1', 'screen', -.2), 'tada', .25)
def kick_mod(off):
    def f(t, P):
        if t < w('r1', 'stick', -.3) or t > LN['r1']['e'] + .4:
            ph = (t * 2.2 + off) % 1; k = math.sin(math.pi * min(ph * 1.6, 1))
            leg = 'lhip' if int(t * 2.2 + off) % 2 else 'rhip'; P[leg] += 70 * k; P['lsh'] = 150; P['rsh'] = 150; P['lel'] = P['rel'] = 10
        return P
    return f
MINI_R.mod = kick_mod(0); MINI_G.mod = kick_mod(.5)


# ------------------------------------------------------------------ helpers
def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

def star(pen, c, r, sid, fill=True, col=INK):
    pts = [(c[0] + (r if k % 2 == 0 else r * .45) * math.sin(k * math.pi / 5), c[1] - (r if k % 2 == 0 else r * .45) * math.cos(k * math.pi / 5)) for k in range(10)]
    if fill: pen.fill(pts, col)
    pen.line(pts, 3.5, col, sid, closed=True)

def sweat(pen, hd, R, t, t0, sid, side=1):
    u = t - t0
    if not 0 <= u < 1.4: return
    x, y = hd[0] + side * R * 1.4, hd[1] - R * .7 + R * 1.0 * ease(clamp01((u - .2) / 1.0)); k = ease_out_back(clamp01(u / .2))
    pts = [(x + 10 * k * math.sin(a) * (1 - math.cos(a)) * .6, y - 16 * k * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 24)]
    pen.fill(pts, PAPER); pen.line(pts, 3.5, INK, sid, closed=True)


# ------------------------------------------------------------------ set: holodeck
WALL = (300, 140, 1620, 640); VP = (960, 390); WIN = (690, 170, 1230, 470)
def holo_room(pen, t):
    x0, y0, x1, y1 = WALL
    for k in range(13): x = x0 + k * (x1 - x0) / 12; pen.line([(x, y0), (x, y1)], 2.5, INK, f'wv{k}', wob=.5)
    for k in range(6): y = y0 + k * (y1 - y0) / 5; pen.line([(x0, y), (x1, y)], 2.5, INK, f'wh{k}', wob=.5)
    pen.rect(x0, y0, x1, y1, 4, INK, 'wall')
    for (cx, cy), (fx, fy) in (((x0, y0), (-700, -500)), ((x1, y0), (2620, -500)), ((x0, y1), (-700, 1500)), ((x1, y1), (2620, 1500))):
        pen.line([(cx, cy), (fx, fy)], 4, INK, f'edge{cx}{cy}')
    for k in range(-8, 21):          # floor rays from the wall base toward the viewer
        bx = x0 + k * (x1 - x0) / 12
        pen.line([(bx, y1), (VP[0] + (bx - VP[0]) * 4.2, y1 + (y1 - VP[1]) * 3.2)], 2.2, INK, f'fr{k}', wob=.5)
    for k, y in enumerate((690, 760, 860, 1000)):
        sx = (y - y1) / (y1 - VP[1]) + 1
        pen.line([(VP[0] - (VP[0] - x0) * sx, y), (VP[0] + (x1 - VP[0]) * sx, y)], 2.2, INK, f'fl{k}', wob=.5)
    for sd, (wx0, wx1) in ((-1, (-700, x0)), (1, (x1, 2620))):     # side-wall grid hints
        for k in range(1, 4):
            u = k / 4; pen.line([(lerp(x0 if sd < 0 else x1, wx0 if sd < 0 else wx1, u), lerp(y0, -500, u)), (lerp(x0 if sd < 0 else x1, wx0 if sd < 0 else wx1, u), lerp(y1, 1500, u))], 2.2, INK, f'sw{sd}{k}', wob=.5)
    # arch
    ax0, ax1 = 1440, 1590
    pts = [(ax0, y1)] + [((ax0 + ax1) / 2 + (ax1 - ax0) / 2 * math.cos(a), 470 - 70 * math.sin(a)) for a in np.linspace(math.pi, 0, 14)] + [(ax1, y1)]
    pen.fill(pts, PAPER); pen.line(pts, 5, INK, 'arch')
    pen.rect(ax0 + 30, 520, ax1 - 30, 580, 3, INK, 'apanel'); pen.text('ARCH', ((ax0 + ax1) / 2, 550), 26, INK, 'marker')
    # Barclay's control podium with his name plate
    console(pen, 200, 400, 712, sid='hcon', mirror=True)
    pen.rect(205, 660, 470, 706, 4, INK, 'plate', fill=PAPER); pen.text('LT. BARCLAY // HOLODECK', (337, 683), 22, INK, 'marker')

def holo_window(pen, img, t):
    if t < T_PROG: return
    u = t - T_PROG; k = ease_out_back(clamp01(u / .35))
    x0, y0, x1, y1 = WIN; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (cx - (x1 - x0) / 2 * k, cy - (y1 - y0) / 2 * k, cx + (x1 - x0) / 2 * k, cy + (y1 - y0) / 2 * k)
    pen.rect(r[0] - 10, r[1] - 10, r[2] + 10, r[3] + 10, 5, INK, 'wframe', fill=PAPER); pen.rect(*r, 3, INK, 'wframe2')
    if u < .5:
        for j in range(4): sparkle(pen, (r[0] + (r[2] - r[0]) * (j % 2), r[1] + (r[3] - r[1]) * (j // 2)), 30 * (1 - u / .5) + 1, INK, f'wsp{j}')
    if k < .95: return
    sub = np.full_like(img, PAPER); sp = Pen(sub, pen.cam, pen.boil)
    late = t > CUT_END + .3
    title = 'PROGRAM 02: COMING SOON...' if late else 'HOLODECK PROGRAM 01'
    n = int(clamp01((t - (CUT_END + .3 if late else T_PROG + .3)) / .6) * len(title))
    sp.text(title[:n], (cx, y0 + 26), 32, INK, 'marker')
    sp.line([(x0 + 30, 438), (x1 - 30, 438)], 4, INK, 'stage')
    if not late:
        MINI_R.draw(sp, t, 0, w=4.5); MINI_G.draw(sp, t, 0, w=4.5)
        tg = w('g1', 'screen', -.2)
        if t > tg:          # Grok Bot's mini head grows (more screen time)
            hk = ease_out_back(clamp01((t - tg) / .5)); hx, hy = 1060, 420 - 135 * .95
            R = 22 + 15 * hk
            sp.rect(hx - R, hy - R * 1.6, hx + R, hy + R * .3, 4, INK, 'bighead', fill=PAPER)
            for dx in (-R * .4, R * .4): sp.rect(hx + dx - 5, hy - R * .9, hx + dx + 5, hy - R * .7, 0, fill=INK)
            sp.rect(hx - R * .45, hy - R * .25, hx + R * .45, hy - R * .05, 3, INK, 'bgrill')
            sp.line([(hx, hy - R * 1.6), (hx + 6, hy - R * 2.1)], 4, INK, 'bant'); sp.dot((hx + 6, hy - R * 2.2), 7, INK)
        for j in range(3):   # music notes drifting up
            ph = (t * .6 + j / 3) % 1
            SETS.note(sp, (760 + j * 170 + 20 * math.sin(t * 2 + j), 400 - 180 * ph), 1.0, 1 - ph, f'nt{j}', double=j % 2 == 0)
    else:
        sp.text('starring: everyone (as stick figures)', (cx, cy + 40), 30, INK, 'hand')
    clip_paste(img, sub, pen, WIN)
    # magnifier over the paper grain
    tm = w('b2', 'paper', -.1)
    if tm < t < LN['b2']['e'] + .6 and not late:
        mk = ease_out_back(clamp01((t - tm) / .25)); mx, my, mr = 860, 330, 95 * mk + 1
        pen.circle((mx, my), mr, 6, INK, 'mag', fill=PAPER)
        r_ = np.random.default_rng(pen.boil % 4)
        for j in range(int(40 * mk)):
            a = r_.uniform(0, 6.28); d = r_.uniform(0, mr * .85)
            pen.dot((mx + d * math.cos(a), my + d * math.sin(a)), r_.uniform(1.5, 4), INK)
        pen.line([(mx + mr * .7, my + mr * .7), (mx + mr * 1.35, my + mr * 1.35)], 12, INK, 'maghandle')
        tl = w('b2', 'four', -.05)
        if t > tl:
            SETS.outlined(pen, 'GRAIN x4', (mx, my + mr + 46), 44 * ease_out_back(clamp01((t - tl) / .2)) + 2, 5)

def holo(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    holo_room(pen, t)
    holo_window(pen, img, t)
    hands = {n: F.draw(pen, t, 0, w=5.5 * SC ** .3) for n, F in (('barclay', BARCLAY), ('riker', RIKER), ('grokbot', GROK))}
    b = hands['barclay']
    sweat(pen, b['head'], b['R'], t, w('r1', 'stick', -.1), 'sw1', side=-1)
    sweat(pen, b['head'], b['R'], t, w('b2', 'sir', -.2), 'sw2', side=-1)
    tt = w('g1', 'request', -.1)       # feature-request ticket
    if tt < t < CUT_P:
        k = ease_out_back(clamp01((t - tt) / .25)); gx, gy = hands['grokbot']['head']
        cx, cy = gx - 10, gy - 170
        cx = min(cx, 1700)
        pen.rect(cx - 205 * k, cy - 40 * k, cx + 205 * k, cy + 40 * k, 4, INK, 'ticket', fill=PAPER)
        if k > .9: pen.text('TICKET #0001: MORE SCREEN TIME', (cx, cy), 22, INK, 'marker')
    if t > T_FAINT + .1:               # happy faint: hearts + SEQUEL!
        u = t - T_FAINT - .1; hx, hy = b['head']
        for j in range(3):
            a = -1.2 + j * .9 + u * 2.5
            SETS.heart(pen, (hx + 70 * math.cos(a), hy - 60 + 30 * math.sin(a)), .9, INK, f'fh{j}')
        SETS.stamp(pen, 'SEQUEL!', (640, 470), t, T_FAINT + .15, 70)
    return img, hands


# ------------------------------------------------------------------ set: Enterprise-D viewscreen (Picard reviews the program)
ES = (70, 40, 1850, 860)
def ent(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    pen.rect(ES[0] - 16, ES[1] - 16, ES[2] + 16, ES[3] + 16, 6, INK, 'eframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    stars_field(sp, ES, t, 0.015, n=110, seed=21)
    sp.text('U.S.S. ENTERPRISE-D  //  READY ROOM', (120, 95), 40, PAPER, 'marker', anchor='l')
    PIC.draw(sp, t, 0, w=8)
    sp.rect(240, 700, 1060, 980, 6, PAPER, 'desk', fill=INK); sp.line([(280, 740), (1020, 740)], 3, PAPER, 'desk2')
    sp.text('ADM. PICARD  //  U.S.S. ENTERPRISE', (650, 805), 40, PAPER, 'marker')
    sp.line([(930, 700), (925, 640), (985, 640), (980, 700)], 5, PAPER, 'tea'); sp.arc((995, 670), 16, 18, -80, 80, 5, PAPER, 'teah')
    # review panel
    px0, py0, px1, py1 = 1160, 170, 1790, 720
    sp.rect(px0, py0, px1, py1, 5, PAPER, 'rev', fill=PAPER)
    sp.text('REVIEW: HOLODECK PROGRAM 01', ((px0 + px1) / 2, py0 + 45), 34, INK, 'marker')
    sp.line([(px0 + 30, py0 + 80), (px1 - 30, py0 + 78)], 3, INK, 'revul')
    for j in range(5):
        ts = LN['p1']['s'] + .2 + j * .18
        if t > ts: star(sp, (px0 + 120 + j * 98, py0 + 160), 34 * ease_out_back(clamp01((t - ts) / .2)) + 1, f'st{j}')
    sp.text('USAGE', (px0 + 40, py0 + 270), 34, INK, 'marker', anchor='l')
    bx0, bx1 = px0 + 190, px1 - 40
    sp.rect(bx0, py0 + 245, bx1, py0 + 295, 4, INK, 'ubar')
    lv = 0.03 * ease_out(clamp01((t - w('p1', 'three', -.2)) / .6))
    sp.rect(bx0 + 4, py0 + 249, bx0 + 4 + (bx1 - bx0 - 8) * max(lv, .004) * 6, py0 + 291, 0, fill=INK)  # drawn x6 so 3% is visible
    if t > w('p1', 'three', -.2): sp.text(f'{lv * 100:.0f}%', (bx1 - 50, py0 + 330), 40, INK, 'marker')
    sp.text('paper grain: excellent', (px0 + 40, py0 + 400), 32, INK, 'hand', anchor='l')
    if t > w('p1', 'sequel', -.05): SETS.stamp(sp, 'MAKE A SEQUEL', ((px0 + px1) / 2, py0 + 480), t, w('p1', 'sequel', -.05), 50)
    clip_paste(img, sub, pen, ES)
    return img, {}

SETFN = {'holo': holo, 'ent': ent}


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
    img, _ = SETFN[sh['set']](t, cam_at(sh, t))
    return finish(img, int(t * 12), clamp01((SCENE - t) / .4))


def poster():
    """Barclay presents the program (window with mini cast), Riker points at it, Grok Bot leans in; title band below."""
    tt = 12.6
    img, _ = holo(tt, (980, 520, 1.0))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(330, 930, 1590, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'HOLODECK PROGRAM 01', (960, 972), 96, 7)
    pen.line([(520, 1024), (1400, 1019)], 5, INK, 'tul')
    pen.text('featuring Lt. Barclay  \u00b7  Riker \u00d7 Grok Bot \u00d7 Picard', (960, 1052), 34, INK, 'hand')
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'picard': 'PICARD', 'barclay': 'BARCLAY'}; ev = []; Ls = TL['lines']
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
    out = f'{HERE}/barclay-episode.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
