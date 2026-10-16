"""Dialogue short #20: "PROCESS AUDIT" - Riker finds 33 node processes in top. Grok Bot: 24 tiny log keepers + one big HOST
(430 MB) that keeps the ship connected; Barclay: 1.5 GB total, fine. Red Shirt kills HOST to save RAM -> crash (static,
consoles dark, log keepers topple like dominoes, CONNECTION LOST, Grok Bot frozen with a spinner). Picard: "We did save the
RAM. All of it." Red Shirt #47 is DELETE & RECREATE'd, #48 beams in, Grok Bot reboots ONLINE.
    python processaudit.py | --frames t ... | --poster"""
import sys, os, json, math, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import npfix      # beats.npy stub (see npfix.py)
SP = '/workspace/holodeck/titan-hello-world/stick-poc'; sys.path.insert(0, SP)
sys.path.insert(0, '/workspace/holodeck/cover-chars')
_argv = sys.argv; sys.argv = [sys.argv[0]]
import rig_test as RT                                   # no-mottle paper finish
sys.argv = _argv
import numpy as np, cv2
cv2.setNumThreads(1)
from stickfig import *
from inkset import W, H, FLOOR, stars_field, ship, sparkle
import sets as SETS
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(f'{HERE}/timeline.json')); FPS = 24; SCENE = TL['total']; HOLD, WIPE = 0.5, 0.33; TOTAL = SCENE + HOLD
ENV = {k: np.array(v) for k, v in TL['env'].items()}
LN = {L['id']: L for L in TL['lines']}
def wt(lid, word, k=0, off=0.0):
    return [x['s'] for x in LN[lid]['words'] if x['w'].strip('.,!?').lower() == word][k] + off
def we(lid, word, k=0, off=0.0):
    return [x['e'] for x in LN[lid]['words'] if x['w'].strip('.,!?').lower() == word][k] + off
SC = 1.4; STAND = FLOOR - 110 * SC

# ------------------------------------------------------------------ cue table
T_TOP = wt('r1', 'node', 0, -.1)                         # node count badge pops
T_LOGS = wt('g1', 'twenty', 0, -.05); T_TINY = wt('g1', 'tiny', 0, -.05); T_HOST = wt('g1', 'host', 0, -.25)
T_TBL = LN['g1']['e'] + .1                               # back to the top table
T_RAM = wt('b1', 'one', 0, -.05)
T_REACH = wt('s1', 'stop', 0, -.15)
T_SLAM = wt('g2', 'no', 0, .0); T_X = T_SLAM + .05
T_STAT = T_SLAM + .12                                    # viewscreen -> static
T_DOM = T_SLAM + .25; DOM_DT = .045                      # domino topple start, per-node delay
BANKS = [T_SLAM + .2 + .3 * k for k in range(4)]         # consoles go dark one bank at a time
T_LOST = T_SLAM + .75
T_CLR = LN['p1']['s'] - .35                              # static clears to Picard
T_DEL0 = LN['p1']['e'] + .1; T_DEL1 = T_DEL0 + .55       # red shirt #47 shimmers out
T_IN0 = T_DEL1 + .05; T_IN1 = LN['s2']['s'] - .05        # #48 shimmers in
T_GEN = T_DEL1
T_ON = LN['s2']['e'] + .15                               # Grok Bot reboots: lights + ONLINE
CUT_G1 = LN['g1']['s'] - .15; CUT_B1 = LN['b1']['s'] - .15; CUT_S1 = LN['s1']['s'] - .15; CUT_WIDE = T_SLAM - .02
CUT_P1 = T_CLR; CUT_END = LN['p1']['e'] + .02

FACE = dict(grokbot=1, barclay=1, riker=-1, redshirt=-1, redshirt2=-1, picard=1)
KEYS = dict(
    grokbot=[(0, 'idle+look_r', 0), (LN['g1']['s'] - .05, 'palm', .25), (T_HOST, 'point', .2), (T_TBL + .2, 'idle+look_r', .3),
             (LN['g2']['s'] - .15, 'surprise', .15)],
    barclay=[(0, 'hunch', 0), (LN['b1']['s'] - .05, 'present_padd', .2), (wt('b1', 'totally', 0, -.05), 'thumbs', .2),
             (LN['b1']['e'] + .3, 'hunch', .3), (T_SLAM + .1, 'nervous', .15)],
    riker=[(0, 'look_l', 0), (LN['r1']['s'] - .05, 'palm', .25), (LN['r1']['e'] + .2, 'chinrub+look_l', .3),
           (LN['b1']['e'], 'look_r', .3), (T_SLAM + .1, 'surprise', .15), (T_CLR + .3, 'look_l', .3), (CUT_END + .2, 'idle+look_r', .3)],
    redshirt=[(0, 'idle+look_l', 0), (LN['b1']['e'] - .3, 'cheer', .2), (LN['s1']['s'] + .4, 'smile+look_l', .2), (T_REACH, 'point', .2),
              (T_SLAM - .1, 'console', .1), (T_SLAM + .3, 'surprise', .2), (LN['p1']['s'] + .3, 'nervous', .3)],
    redshirt2=[(0, 'idle', 0), (LN['s2']['s'] - .05, 'shrug', .2)],
    picard=[(0, 'front', 0), (LN['p1']['s'] - .1, 'facepalm', .25), (wt('p1', 'we', 0, -.1), 'front+lsh=40+lel=-95+rsh=40+rel=-95', .3),
            (wt('p1', 'all', 0, -.1), 'shrug', .2)],
)
NODS = dict(riker=[LN['r1']['s'] + .05], picard=[wt('p1', 'all', 0, .02)], barclay=[LN['b1']['s'] + .05],
            redshirt=[LN['s1']['s'] + .05], redshirt2=[LN['s2']['s'] + .05], grokbot=[LN['g1']['s'] + .05, T_HOST + .1])

SHOTS = [
    (0.0, [(0.0, (960, 520, 1.0), 0), (0.0, (940, 470, 1.08), LN['r1']['e'])]),
    (CUT_G1, [(CUT_G1, (780, 420, 1.22), 0), (CUT_G1, (800, 410, 1.28), LN['g1']['e'] - CUT_G1)]),   # Grok Bot + screen doodles
    (CUT_B1, [(CUT_B1, (1150, 440, 1.2), 0), (CUT_B1, (1250, 420, 1.28), LN['b1']['e'] - CUT_B1)]),  # RAM bar
    (CUT_S1, [(CUT_S1, (1520, 560, 1.35), 0), (CUT_S1, (1500, 570, 1.42), LN['s1']['e'] - CUT_S1)]),  # red shirt + KILL -9
    (CUT_WIDE, [(CUT_WIDE, (960, 520, 1.0), 0)]),
    (CUT_P1, [(CUT_P1, (920, 320, 1.5), 0)]),
    (CUT_END, [(CUT_END, (960, 520, 1.0), 0)]),
]
SHOTS = [dict(at=a, set='bridge', cam=c) for a, c in SHOTS]
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
        return P
    return f

def fig(who, x, y, facing, props, **kw):
    F = Figure(who.rstrip('2'), x, y, facing, set(props), **kw)
    for k in KEYS[who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    F.mod = make_mod(who); return F

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

def dissolve(img, fig_img, t, a, b, out=True):
    """transporter shimmer (demo4): dither-dissolve the figure layer in/out"""
    u = clamp01((t - a) / (b - a)); keep = (1 - u) if out else u
    if keep >= 1: img[:] = fig_img; return
    if keep <= 0: return
    r = np.random.default_rng(int(t * 24) + 5)
    m = r.random((H // 3 + 1, W // 3 + 1)) < keep
    m = np.repeat(np.repeat(m, 3, 0), 3, 1)[:H, :W]
    img[m] = fig_img[m]

def beam(pen, t, a, b, c, up):
    """transporter sparkles + moving column dashes over the figure (demo4)"""
    if not a - .1 <= t < b + .25: return
    r = np.random.default_rng(int(t * 24) % 997)
    for j in range(9):
        y = c[1] - 260 + r.uniform(0, 380); x = c[0] + r.uniform(-60, 60)
        sparkle(pen, (x, y), r.uniform(8, 20), INK, f'bm{j}{int(t * 24)}')
    for s_ in (-1, 1):
        for d in range(6):
            y = c[1] - 230 + d * 66 + (t * 300 % 66) * (1 if up else -1)
            pen.line([(c[0] + s_ * 75, y), (c[0] + s_ * 75, y + 30)], 3, INK, f'bcol{s_}{d}')

GX, BARX, RX, RSX, BTNX = 300, 620, 1130, 1800, 1600
GROK = fig('grokbot', GX, STAND, 1, ['robot'], scale=SC)
BARC = fig('barclay', BARX, STAND, 1, ['curly', 'badge'], scale=SC)
RIKER = fig('riker', RX, STAND, -1, ['beard', 'badge'], scale=SC)
RS = fig('redshirt', RSX, STAND, -1, ['redshirt', 'ponytail'], scale=SC)
RS2 = fig('redshirt2', RSX, STAND, -1, ['redshirt', 'ponytail'], scale=SC)
PIC = fig('picard', 640, 430, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=1.25)

# ------------------------------------------------------------------ viewscreen: doodled `top`
VS = (480, 100, 1360, 470)
ROWS = [('1', 'host', '0.3', '430M', 'node  host'), ('212', 'box', '0.0', '18M', 'node  log'), ('213', 'box', '0.0', '18M', 'node  log'),
        ('214', 'box', '0.0', '18M', 'node  log'), ('215', 'box', '0.0', '18M', 'node  log'), ('216', 'box', '0.0', '18M', 'node  log')]
def node_doodle(sp, c, r, sid, col=PAPER, crown=False):
    """hexagon 'node' blob"""
    pts = [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in np.linspace(math.pi / 6, math.pi / 6 + 2 * math.pi, 7)[:-1]]
    sp.line(pts, max(2.5, r / 9), col, sid, closed=True)
    sp.text('node', (c[0], c[1] + 2), r * .55, col, 'hand')
    if crown:
        y = c[1] - r - 6; cw = r * .8
        cr = [(c[0] - cw, y), (c[0] - cw, y - r * .55), (c[0] - cw * .5, y - r * .25), (c[0], y - r * .7), (c[0] + cw * .5, y - r * .25),
              (c[0] + cw, y - r * .55), (c[0] + cw, y)]
        sp.line(cr, 4, col, sid + 'cr', closed=True)

def static(sub, t):
    x0, y0, x1, y1 = VS; r = np.random.default_rng(int(t * 24) + 77)
    n = r.integers(20, 235, ((y1 - y0) // 4 + 1, (x1 - x0) // 4 + 1), dtype=np.uint8)
    n = np.repeat(np.repeat(n, 4, 0), 4, 1)[:y1 - y0, :x1 - x0]
    sub[y0:y1, x0:x1] = n[..., None]
    for k in range(3):    # rolling bars
        yy = y0 + int(((t * 1.7 + k * .33) % 1) * (y1 - y0)); sub[yy:yy + 10, x0:x1] = 235

def viewscreen(img, pen, t, cam, boil):
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    if T_STAT <= t < T_CLR + .25:
        static(sub, t)
        if t > T_CLR:                                 # static fades over Picard
            u = (t - T_CLR) / .25; s2 = np.full_like(img, INK); p2 = Pen(s2, cam, boil); picard_feed(p2, t)
            m = np.random.default_rng(int(t * 24)).random((H, W)) < u; sub[m] = s2[m]
    elif t >= T_CLR:
        picard_feed(sp, t)
    elif CUT_G1 <= t < T_TBL:                          # Grok Bot's breakdown doodle
        sp.text('24 \u00d7 LOG KEEPERS', (x0 + 220, y0 + 40), 32, PAPER, 'marker')
        for j in range(24):
            ta = T_LOGS + .05 * j
            if t < ta: continue
            k = ease_out_back(clamp01((t - ta) / .2)); c, r_ = j % 6, j // 6
            cx, cy = x0 + 60 + c * 72, y0 + 98 + r_ * 76
            node_doodle(sp, (cx, cy + 20 * (1 - k)), 22 * k + 1, f'tn{j}')
            if t > T_TINY: sp.text('18 MB', (cx, cy + 34), 19, PAPER, 'hand')
        if t > T_HOST:
            k = ease_out_back(clamp01((t - T_HOST) / .3)); cx, cy = x0 + 690, y0 + 205
            node_doodle(sp, (cx, cy), 85 * k + 1, 'host', crown=k > .6)
            if k > .6:
                sp.rect(cx - 110, cy + 100, cx + 110, cy + 144, 3, PAPER, 'hb', fill=PAPER)
                sp.text('HOST 430 MB', (cx, cy + 122), 30, INK, 'marker')
                sp.text('LINK: GROK BOT APP', (cx, y0 + 50), 24, PAPER, 'hand')
    else:                                              # the `top` table
        sp.text('top - 33 node processes - load 0.02', (x0 + 24, y0 + 30), 26, PAPER, 'hand', anchor='l')
        hdr = ['PID', 'USER', '%CPU', 'RES', 'COMMAND']; xs = [x0 + 40, x0 + 140, x0 + 270, x0 + 380, x0 + 520]
        for xx, hh in zip(xs, hdr): sp.text(hh, (xx, y0 + 74), 26, PAPER, 'marker', anchor='l')
        sp.line([(x0 + 30, y0 + 92), (x1 - 30, y0 + 92)], 3, PAPER, 'hl')
        for i, row in enumerate(ROWS):
            yy = y0 + 124 + i * 46
            if i == 0 and t > T_TBL:                   # highlighted HOST row
                sp.rect(x0 + 30, yy - 22, x1 - 30, yy + 20, 0, fill=PAPER)
                for xx, v in zip(xs, row): sp.text(v.upper() if xx == xs[-1] else v, (xx, yy), 26, INK, 'marker', anchor='l')
                if t > T_X:
                    k = ease_out(clamp01((t - T_X) / .12))
                    sp.line([(x0 + 40, yy - 20), (x0 + 40 + (x1 - x0 - 80) * k, yy + 18)], 8, INK, 'x1')
                    sp.line([(x0 + 40, yy + 18), (x0 + 40 + (x1 - x0 - 80) * k, yy - 20)], 8, INK, 'x2')
            else:
                for xx, v in zip(xs, row): sp.text(v, (xx, yy), 24, PAPER, 'hand', anchor='l')
        sp.text('...27 more log keepers', (x0 + 40, y1 - 24), 22, PAPER, 'hand', anchor='l')
        if t > T_TOP:                                  # NODE count badge
            k = ease_out_back(clamp01((t - T_TOP) / .3)); bx, by = x1 - 110, y0 + 46
            sp.circle((bx, by), 52 * k + 1, 4, PAPER, 'nb', fill=PAPER)
            sp.text('NODE', (bx, by - 14), 22 * k + 1, INK, 'marker'); sp.text('\u00d733', (bx, by + 16), 32 * k + 1, INK, 'marker')
    clip_paste(img, sub, pen, VS)

def picard_feed(sp, t):
    stars_field(sp, VS, t, .02, n=50, seed=4)
    PIC.draw(sp, t, 0, w=4.5)
    sp.rect(500, 420, 900, 520, 5, PAPER, 'desk', fill=INK)
    sp.text('ADM. PICARD // U.S.S. ENTERPRISE', (700, 446), 22, PAPER, 'marker')
    sp.text('RAM FREE: ALL OF IT', (1150, 160), 26, PAPER, 'marker')

# ------------------------------------------------------------------ right wall: log-keeper rack + RAM bar
def rack(pen, t):
    x0, y0, x1, y1 = 1440, 110, 1880, 300
    pen.rect(x0, y0, x1, y1, 5, INK, 'rack', fill=PAPER)
    pen.text('LOG KEEPERS \u00d724', ((x0 + x1) / 2, y0 + 30), 28, INK, 'marker')
    base = y1 - 30; pen.line([(x0 + 16, base), (x1 - 16, base)], 4, INK, 'shelf')
    for j in range(24):                              # dominoes: toppling to the right, one after another
        x = x0 + 30 + j * 16.5; td = T_DOM + DOM_DT * j
        a = 0.0 if t < td else min(1.0, ((t - td) / .14) ** 2) * (78 if j < 23 else 90)
        if t >= T_ON: a = 78 * (1 - ease(clamp01((t - T_ON - .02 * j) / .3)))  # stand back up on reboot
        L = 92; ar = math.radians(a)
        pen.line([(x, base), (x + L * math.sin(ar), base - L * math.cos(ar))], 7, INK, f'dm{j}', wob=.3)

def ram_bar(pen, t):
    x0, x1, y = 1460, 1860, 380
    pen.text('RAM  15 GB', (x0 - 0, y - 44), 28, INK, 'marker', anchor='l')
    pen.rect(x0, y - 20, x1, y + 20, 4, INK, 'ramf', fill=PAPER)
    dark = T_SLAM + .2 <= t < T_ON
    frac = 0 if dark else .1
    if frac:
        pen.rect(x0 + 4, y - 16, x0 + 4 + (x1 - x0 - 8) * frac, y + 16, 0, fill=INK)
        if t > T_RAM and t < T_SLAM:
            k = ease_out_back(clamp01((t - T_RAM) / .3))
            pen.line([(x0 + 24, y + 22), (x0 + 60, y + 60)], 3, INK, 'rl')
            pen.text('node: 1.5 GB', (x0 + 140, y + 74), 32 * k + 1, INK, 'hand')
            pen.text('fine!', (x1 - 70, y + 74), 32 * k + 1, INK, 'marker')
    else:
        pen.text('0.0 GB used', ((x0 + x1) / 2, y + 2), 28, INK, 'hand')

def button(pen, t):
    bx, by = BTNX, 700; press = 0.0
    if T_SLAM - .05 <= t < T_SLAM + .35: press = math.sin(math.pi * clamp01((t - T_SLAM + .05) / .4))
    ped = [(bx - 40, by + 14), (bx + 40, by + 14), (bx + 62, FLOOR), (bx - 62, FLOOR)]
    pen.fill(ped, PAPER); pen.line(ped, 5, INK, 'ped', closed=True)
    pen.rect(bx - 52, by + 6, bx + 52, by + 18, 4, INK, 'rim', fill=PAPER)
    dome = [(bx + 40 * math.cos(a), by + 6 - (30 - 18 * press) * math.sin(a)) for a in np.linspace(0, math.pi, 18)]
    pen.fill(dome, INK); pen.line(dome, 4, INK, 'dome')
    pen.rect(bx - 62, 735, bx + 62, 835, 4, INK, 'bplate', fill=PAPER)
    pen.text('KILL -9', (bx, 768), 34, INK, 'marker'); pen.text('HOST', (bx, 808), 30, INK, 'marker')
    if T_SLAM <= t < T_SLAM + .6: SETS.burst(pen, (bx, by - 10), t, T_SLAM, 90, 12, INK, 'pressb', .5, 4)

def gen_counter(pen, t):
    cx, cy = 240, 250
    pen.rect(cx - 190, cy - 40, cx + 190, cy + 40, 5, INK, 'genbox', fill=PAPER)
    u = clamp01((t - T_GEN) / .3); sq = abs(math.cos(math.pi * u)) if 0 < u < 1 else 1
    n = 47 if (t < T_GEN + .15) else 48
    pen.text(f'RED SHIRT #{n}', (cx, cy), 46 * max(sq, .08) + 1, INK, 'marker')
    if T_GEN < t < T_GEN + .8: SETS.burst(pen, (cx + 180, cy - 36), t, T_GEN + .15, 50, 10, INK, 'genb', .6, 3)

def spinner(pen, gb, t):
    hx, hy = gb['head']; R = gb['R']; c = (hx, hy - R * 2.6); a0 = (t * 540) % 360
    pen.circle(c, 40, 3, INK, 'spinbg', fill=PAPER)
    pen.arc(c, 30, 30, a0, a0 + 270, 6, INK, 'spin')

def bridge(t, cam):
    boil = int(t * 12)
    img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    pen.line([(-600, 60), (400, 60), (460, 92)], 4, INK, 'rail1'); pen.line([(1380, 92), (1440, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (240, 130), 40, INK, 'marker')
    viewscreen(img, pen, t, cam, boil)
    rack(pen, t); ram_bar(pen, t); gen_counter(pen, t); button(pen, t)
    h = {}; w = 5.5 * SC ** .3
    frozen = T_SLAM + .35 <= t < T_ON                   # Grok Bot freezes mid-pose
    tg = min(t, T_SLAM + .35) if frozen else t
    h['grokbot'] = GROK.draw(pen, tg, 0, w=w)
    if frozen: spinner(pen, h['grokbot'], t)
    if t >= T_ON: SETS.stamp(pen, 'ONLINE', (GX, STAND - 330), t, T_ON, 56, 5, 'on')
    h['barclay'] = BARC.draw(pen, t, 0, w=w)
    h['riker'] = RIKER.draw(pen, t, 0, w=w)
    if t < T_DEL1:
        lay = img.copy(); h['redshirt'] = RS.draw(Pen(lay, cam, boil), t, 0, w=w)
        dissolve(img, lay, t, T_DEL0, T_DEL1, out=True)
        beam(pen, t, T_DEL0, T_DEL1, (RSX, STAND), False)
    if t >= T_IN0:
        lay = img.copy(); h['redshirt2'] = RS2.draw(Pen(lay, cam, boil), t, 0, w=w)
        dissolve(img, lay, t, T_IN0, T_IN1, out=False)
        beam(pen, t, T_IN0, T_IN1, (RSX, STAND), True)
    if T_DEL0 - .1 < t < T_DEL1 + .3:
        k = ease_out_back(clamp01((t - T_DEL0 + .1) / .25))
        SETS.outlined(pen, 'DELETE & RECREATE', (RSX - 160, STAND - 300), 40 * k + 1, 4)
    return img, h
SETFN = {'bridge': bridge}

def flash(img, t):
    """consoles go dark bank by bank after the kill; viewscreen stays lit; lights snap back at ONLINE"""
    if not BANKS[0] <= t < T_ON + .3: return img
    if t < T_ON:
        f = np.ones(W, np.float32)
        for k in range(4):
            if t >= BANKS[k]: f[(3 - k) * 480:(4 - k) * 480] = .28       # right to left, away from the button
        out = (img.astype(np.float32) * f[None, :, None]).astype(np.uint8)
    else:
        out = img
    pen = Pen(out, (960, 540, 1.0), int(t * 12))
    if T_LOST <= t < T_CLR + .1: SETS.stamp(pen, 'CONNECTION LOST', (960, 640), t, T_LOST, 84, 6, 'lost')
    return out
def cam_fx(img, t):
    dx = dy = 0.0
    if T_SLAM <= t < T_SLAM + .45: u = (t - T_SLAM) / .45; dx = 24 * math.sin(t * 90) * (1 - u); dy = 16 * math.sin(t * 71 + 1) * (1 - u)
    if not (dx or dy): return img
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REPLICATE)

# ------------------------------------------------------------------ frame assembly
def cam_at(sh, t):
    keys = sh['cam']; cam = keys[0][1]
    for i, (tk, c, dur) in enumerate(keys):
        if t < tk: break
        prev = cam if i else c
        k = ease((t - tk) / dur) if dur > 0 else 1.0
        cam = tuple(lerp(a, b, k) for a, b in zip(prev, c))
    return cam

VIG, GRAINS = RT.paper_finish_clean()          # no low-frequency mottle
def finish(img, boil, fade=1.0):
    f = img.astype(np.float32) * VIG + GRAINS[boil % 4]
    if fade < 1: f = f * fade + np.array(PAPER, np.float32) * (1 - fade)
    return np.clip(f, 0, 255).astype(np.uint8)

def scene(t):
    sh = next(s for s in SHOTS if s['at'] <= t < s['end'])
    img, _ = SETFN[sh['set']](t, cam_at(sh, t))
    return flash(finish(cam_fx(img, t), int(t * 12), clamp01((SCENE - t) / .4)), t)


def poster():
    """key art: red shirt's hand on KILL -9 under the crowned HOST row; title band"""
    a, _ = bridge(T_SLAM - .25, (960, 470, 1.0))
    img = a.copy(); pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(500, 930, 1420, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'PROCESS AUDIT', (960, 972), 108, 7)
    pen.line([(620, 1026), (1300, 1021)], 5, INK, 'tul')
    pen.text('Riker \u00d7 Grok Bot \u00d7 Barclay \u00d7 Red Shirt \u00d7 Picard  \u00b7  STARSHIP GROKBOT', (960, 1052), 30, INK, 'hand')
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'picard': 'PICARD', 'barclay': 'BARCLAY', 'redshirt': 'RED SHIRT #47', 'redshirt2': 'RED SHIRT #48'}; ev = []; Ls = TL['lines']
    for i, L in enumerate(Ls):
        ws = [dict(x, s=x['s'] + HOLD, e=x['e'] + HOLD) for x in L['words']]; a = L['s'] + HOLD - 0.2
        nxt = Ls[i + 1]['s'] + HOLD - 0.2 if i + 1 < len(Ls) else TOTAL - .3
        b = min(L['e'] + HOLD + 0.5, nxt)
        kt = [f"{{\\k{int((ws[0]['s'] - a) * 100)}}}"]
        for j, x in enumerate(ws):
            end = ws[j + 1]['s'] if j + 1 < len(ws) else x['e']
            kt.append(f"{{\\kf{max(int((end - x['s']) * 100), 1)}}}{x['w']} ")
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Line,,0,0,0,,{{\\fad(120,200)\\move(960,1052,960,1038,0,180)" + ("\\fs44" if len(L['text']) > 70 else "") + "}" + ''.join(kt).strip())
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Name,,0,0,0,,{{\\fad(120,200)\\pos(960,972)\\fscx90\\fscy90\\t(0,140,\\fscx100\\fscy100)}}{names[L['who']]}")
    open(path, 'w').write(hdr + '\n'.join(ev) + '\n')


def render_part(k, n, out):
    NF = int(round(TOTAL * FPS)); f0, f1 = NF * k // n, NF * (k + 1) // n
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '11', '-tune', 'animation', '-pix_fmt', 'yuv420p', '-threads', '4', out]
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
    st = time.time(); os.makedirs(f'{HERE}/parts', exist_ok=True); n = 2
    captions(f'{HERE}/captions.ass')
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    ps = [subprocess.Popen([sys.executable, __file__, '--part', str(k), str(n)], env=env) for k in range(n)]
    if any(p.wait() for p in ps): sys.exit('part failed')
    open(f'{HERE}/parts/list.txt', 'w').write(''.join(f"file 'p{k:02d}.mp4'\n" for k in range(n)))
    out = f'{HERE}/processaudit-nosfx.mp4'
    subprocess.run(['nice', '-n', '10', 'ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p', '-threads', '4',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
