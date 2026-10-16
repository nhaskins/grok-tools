"""Dialogue short #17: "WRONG MONITOR" - true story: Grok Bot beams into Nate's Linux desktop to fix the Gaomon pen display
that keeps drawing on the sideways monitor. Fix #1 (a 3-second watcher loop) causes input-lag blips (1 -> 12 -> 99); fix #2 is
one login script that exits, plus `fixpen`. Picard approves of a fix that knows when to stop. xAI voices (Riker = Nate's voice).
    python wrongmonitor.py | --frames t ... | --poster"""
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
SC = 1.4; STAND = FLOOR - 110 * SC; SEATY = FLOOR - 58 * SC

# ------------------------------------------------------------------ cue table
T_BEAM = wt('g1', 'beaming', 0, -.05); T_BEAM1 = T_BEAM + .6          # bridge Grok Bot dissolves, mini Grok materializes in the desktop
T_N3 = wt('g1', 'three'); T_N2 = wt('g1', 'two'); T_N1 = wt('g1', 'one')
T_SHIP = wt('b1', 'starship', 0, -.05)
T_WATCH = wt('g2', 'watcher', 0, -.05)
T_L1 = wt('g2', 'seconds', 0, .1); T_L12 = wt('r2', 'pen', 0, -.05); T_L99 = wt('r2', 'barclay', 0, -.05)
T_REV = LN['g3']['s'] - .05; T_FIX = wt('g3', 'fixpen', 0, -.05)
T_OUT = LN['p1']['e'] + .35; T_OUT1 = T_OUT + .55; T_BACK = T_OUT1 + .05; T_BACK1 = T_BACK + .55
CUT_G1 = LN['g1']['s'] - .15; CUT_B1 = LN['b1']['s'] - .15; CUT_G2 = LN['g2']['s'] - .15; CUT_R2 = LN['r2']['s'] - .15
CUT_G3 = LN['g3']['s'] - .15; CUT_P1 = LN['p1']['s'] - .15; CUT_END = T_OUT - .15
def blips(t):
    return 0 if t < T_L1 or t >= T_REV else 1 if t < T_L12 else 12 if t < T_L99 else 99

KEYS = dict(
    grokbot=[(0, 'idle+look_r', 0), (T_BACK, 'salute', .2)],
    riker=[(0, 'sit+look_r', 0), (LN['r1']['s'] + .05, 'sit+palm', .25), (wt('r1', 'again', 0, -.1), 'sit+rsh=80+rel=10', .2),
           (LN['r1']['e'] + .3, 'sit+chinrub', .3), (LN['r2']['s'] - .05, 'sit+rsh=20+rel=150+mouth=3', .2), (wt('r2', 'stutters', 0, -.1), 'sit+point', .2),
           (LN['r2']['e'] + .3, 'sit+chinrub', .3), (T_FIX, 'sit+thumbs', .25)],
    barclay=[(0, 'hunch', 0), (LN['b1']['s'] - .05, 'present_padd', .25), (wt('b1', 'sideways', 0, -.1), 'nervous', .2),
             (wt('r2', 'barclay', 0, -.05), 'surprise', .15), (LN['r2']['e'] + .2, 'nervous', .3), (T_FIX + .2, 'tada', .25)],
    picard=[(0, 'front+rsh=40+rel=110+tilt=4', 0), (LN['p1']['s'] - .1, 'front+lsh=30+lel=-70+rsh=30+rel=-70', .3),
            (wt('p1', 'fix', 0, -.1), 'front+lsh=20+lel=10+rsh=60+rel=80', .25), (wt('p1', 'stop', 0, -.05), 'front+rsh=40+rel=110+tilt=4', .3)],
)
NODS = dict(riker=[LN['r1']['s'] + .05, LN['r2']['s'] + .05], picard=[wt('p1', 'finally', 0, .02)], barclay=[LN['b1']['s'] + .05],
            grokbot=[LN['g1']['s'] + .05, LN['g2']['s'] + .05, LN['g3']['s'] + .05])

SHOTS = [
    (0.0, [(0.0, (960, 520, 1.0), 0), (0.0, (980, 520, 1.05), LN['r1']['e'])]),
    (CUT_G1, [(CUT_G1, (920, 330, 1.55), 0), (CUT_G1, (920, 320, 1.6), LN['g1']['e'] - CUT_G1)]),     # push into the desktop
    (CUT_B1, [(CUT_B1, (700, 520, 1.12), 0)]),
    (CUT_G2, [(CUT_G2, (920, 330, 1.55), 0)]),
    (CUT_R2, [(CUT_R2, (960, 520, 1.0), 0)]),
    (CUT_G3, [(CUT_G3, (920, 330, 1.55), 0), (CUT_G3, (920, 320, 1.6), LN['g3']['e'] - CUT_G3)]),
    (CUT_P1, [(CUT_P1, (1010, 420, 1.3), 0), (CUT_P1, (1012, 400, 1.34), LN['p1']['e'] - CUT_P1)]),
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
    F = Figure(who, x, y, facing, set(props), **kw)
    for k in KEYS[who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    F.mod = make_mod(who); return F

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

BARC = fig('barclay', 250, STAND, 1, ['curly', 'badge'], scale=SC)
GROK = fig('grokbot', 560, STAND, 1, ['robot'], scale=SC)
RIKER = fig('riker', 1500, SEATY, -1, ['beard', 'badge'], scale=SC)
PIC = fig('picard', 800, 430, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=1.25)
RCHAIR = 1500
# mini Grok Bot inside the desktop (paper ink on the ink screen)
MINI = Figure('grokbot', 1285, 400, -1, {'robot'}, col=PAPER, scale=.6)
MINI.key(-1e8, 'idle+look_l', 0)
for k in [(LN['g1']['s'] + .3, 'present', .25), (wt('g1', 'confused', 0, -.1), 'shrug', .2), (LN['g1']['e'] + .3, 'idle+look_l', .3),
          (LN['g2']['s'], 'proud', .25), (wt('g2', 'watcher', 0, -.1), 'point', .2), (LN['g2']['e'] + .3, 'idle+look_l', .3),
          (T_L99, 'surprise', .15), (LN['g3']['s'], 'palm', .25), (T_FIX, 'thumbs', .2), (LN['g3']['e'] + .3, 'idle+look_l', .3),
          (T_OUT - .4, 'salute', .2)]:
    MINI.key(*k)
MINI.mod = make_mod('grokbot')

def dissolve(img, lay, t, a, b, seed, out=True):
    """transporter shimmer: dither-dissolve a layer in/out (from demo4)"""
    u = clamp01((t - a) / (b - a)); keep = (1 - u) if out else u
    if keep >= 1: img[:] = lay; return
    if keep <= 0: return
    r = np.random.default_rng(int(t * 24) + seed)
    m = r.random((H // 3 + 1, W // 3 + 1)) < keep
    m = np.repeat(np.repeat(m, 3, 0), 3, 1)[:H, :W]
    img[m] = lay[m]
def beam(pen, t, a, b, c, s=1.0, col=INK, sid='bm'):
    """transporter sparkles + side columns over a figure"""
    if not a - .1 <= t < b + .25: return
    r = np.random.default_rng(int(t * 24) % 997)
    for j in range(9):
        sparkle(pen, (c[0] + r.uniform(-60, 60) * s, c[1] - 260 * s + r.uniform(0, 380) * s), r.uniform(8, 20) * s, col, f'{sid}{j}{int(t * 24)}')
    for s_ in (-1, 1):
        for d in range(6):
            y = c[1] - 230 * s + (d * 66 + (t * 300 % 66)) * s
            pen.line([(c[0] + s_ * 75 * s, y), (c[0] + s_ * 75 * s, y + 30 * s)], 3, col, f'{sid}c{s_}{d}')
def grok_vis(t):
    """'out' (on bridge) / 'in' (inside the desktop) and the dissolve windows"""
    return t < T_BEAM1, T_BEAM <= t < T_OUT1     # bridge Grok visible until beamed out; back at T_BACK

# ------------------------------------------------------------------ the doodled desktop
VS = (480, 100, 1360, 470)
UW = (510, 190, 820, 320); PT = (850, 150, 930, 400); GM = (965, 215, 1330, 390)   # ultrawide, portrait (sideways), Gaomon 21"
def monitor(sp, r, label, sid):
    x0, y0, x1, y1 = r
    sp.rect(x0, y0, x1, y1, 4, PAPER, sid)
    sp.line([((x0 + x1) / 2, y1), ((x0 + x1) / 2, y1 + 14)], 4, PAPER, sid + 's'); sp.line([((x0 + x1) / 2 - 22, y1 + 14), ((x0 + x1) / 2 + 22, y1 + 14)], 4, PAPER, sid + 'b')
    sp.text(label, ((x0 + x1) / 2, y0 + 20), 20, PAPER, 'marker')
def ship_doodle(sp, c, s, rot, sid):
    """saucer + neck + hull + two nacelles, rotated by rot degrees (Barclay's starship)"""
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    R = lambda p: (c[0] + (p[0] * ca - p[1] * sa) * s, c[1] + (p[0] * sa + p[1] * ca) * s)
    sp.arc(R((-30, 0)), 34 * s, 12 * s, 0, 360, 3, PAPER, sid + 'sau', rot=rot)
    sp.line([R((-5, 6)), R((20, 18))], 3, PAPER, sid + 'nk')
    sp.line([R((10, 18)), R((50, 18)), R((54, 26)), R((14, 26))], 3, PAPER, sid + 'hul', closed=True)
    for dy in (-6, 40): sp.line([R((30, dy)), R((70, dy))], 4, PAPER, sid + f'nc{dy}')
    for dy in (-6, 40): sp.line([R((36, 22)), R((44, dy))], 2, PAPER, sid + f'py{dy}')
def pen_cursor(sp, p, sid):
    """little stylus doodle with its tip at p"""
    x, y = p
    sp.line([(x, y), (x + 10, y - 10), (x + 46, y - 46), (x + 36, y - 56), (x, y - 20), (x, y)], 3, PAPER, sid, closed=True)
def scribble(sp, r, k, t, sid, jit=0.0):
    """pen stroke across rect r, revealed to fraction k; jit = stutter (segments jump)"""
    x0, y0, x1, y1 = r; n = 40; pts = []; m = max(2, int(n * k))
    for i in range(m):
        u = i / (n - 1); x = lerp(x0, x1, u); y = (y0 + y1) / 2 + (y1 - y0) * .32 * math.sin(u * 7.5)
        if jit: y += jit * (((i * 7 + int(t * 12) * 3) % 5) - 2) * 4; x += jit * (((i * 3 + int(t * 12)) % 3) - 1) * 6
        pts.append((x, y))
    if jit:
        for i in range(0, m - 1, 3): sp.line(pts[i:i + 3], 4, PAPER, f'{sid}{i}')
    else: sp.line(pts, 4, PAPER, sid)
    return pts[-1]

def desktop(sp, t, mini_lay=None):
    x0, y0, x1, y1 = VS
    sp.text('nate@titan-desktop:~$  (COSMIC)', (x0 + 24, y0 + 26), 22, PAPER, 'hand', anchor='l')
    monitor(sp, UW, 'ULTRAWIDE', 'uw'); monitor(sp, PT, '', 'pt'); monitor(sp, GM, 'GAOMON 21"', 'gm')
    sp.text('SIDEWAYS', ((PT[0] + PT[2]) / 2, PT[1] - 14), 18, PAPER, 'marker')
    fixed = t >= T_FIX
    if not fixed:
        # the confused pen: lands on the portrait monitor
        k = clamp01((t - .3) / 1.6); tip = scribble(sp, (PT[0] + 10, PT[1] + 60, PT[2] - 10, PT[1] + 130), k, t, 'wrong')
        if t >= T_SHIP:
            k2 = ease_out_back(clamp01((t - T_SHIP) / .3)); ship_doodle(sp, ((PT[0] + PT[2]) / 2 - 18, PT[1] + 240), .8 * k2 + .01, 90, 'bship')
        if T_WATCH <= t < T_REV:   # watcher fix: pen now hits the Gaomon, but stutters
            jit = 0.4 if t < T_L1 else 1.0 if t < T_L12 else 1.6 if t < T_L99 else 2.4
            tip = scribble(sp, (GM[0] + 30, GM[1] + 50, GM[2] - 30, GM[3] - 30), clamp01((t - T_WATCH) / 3), t, 'stut', jit)
            # watcher eye blinking every "3 s" (sped up so it reads)
            ex, ey = UW[0] + 60, UW[3] - 40; op = .2 + .8 * abs(math.sin((t - T_WATCH) * 3))
            sp.arc((ex, ey), 26, 13 * op + 1, 0, 360, 3, PAPER, 'eye'); sp.circle((ex, ey), 6, 0, fill=PAPER)
            sp.text('watcher: every 3 s', (ex + 40, ey + 2), 20, PAPER, 'hand', anchor='l')
        pen_cursor(sp, (tip[0] + (5 * math.sin(t * 40) if T_L1 <= t < T_REV else 0), tip[1]), 'cur')
    else:
        tip = scribble(sp, (GM[0] + 30, GM[1] + 50, GM[2] - 30, GM[3] - 30), clamp01((t - T_FIX) / 1.4), t, 'clean')
        pen_cursor(sp, tip, 'cur')
        sp.text('~/.config/scripts/map-gaomon.sh  (exit 0)', ((UW[0] + UW[2]) / 2, UW[1] + 70), 17, PAPER, 'hand')
        SETS.stamp(sp, 'FIXPEN', ((UW[0] + UW[2]) / 2, UW[1] + 115), t, T_FIX, 50, sid='fx')
    # g1 inventory tags
    for tc, txt, y in ((T_N3, '3 MONITORS', y1 - 24), (T_N2, '2 DRIVERS', y1 - 24), (T_N1, '1 CONFUSED PEN?', y1 - 24)):
        if tc <= t < T_SHIP:
            k = ease_out_back(clamp01((t - tc) / .2)); xx = {T_N3: 640, T_N2: 880, T_N1: 1110}[tc]
            sp.text(txt, (xx, y), 22 * k + 1, PAPER, 'marker')

def lag_counter(pen, t):
    n = blips(t)
    if not n: return
    x, y = 1640, 250
    k = ease_out_back(clamp01((t - T_L1) / .25))
    last = max(c for c in (T_L1, T_L12, T_L99) if c <= t); sq = 1 + .25 * max(0, 1 - (t - last) / .25)
    jx = 6 * math.sin(t * 50) if n >= 12 else 0
    pen.rect(x - 230 * k + jx, y - 70 * k, x + 230 * k + jx, y + 70 * k, 5, INK, 'cnt', fill=PAPER)
    pen.text('INPUT LAG BLIPS', (x + jx, y - 28 * k), 34 * k, INK, 'marker')
    pen.text(str(n), (x + jx, y + 26 * k), 58 * k * sq, INK, 'marker')
    if n == 99 and t - T_L99 < .7: SETS.burst(pen, (x, y), t, T_L99, 260, 12, INK, 'cb99', .6, 3)
    if t - last < .5 and last > T_L1: SETS.outlined(pen, '!', (x + 260, y - 50), 70, 5)

def viewscreen(img, pen, t, cam, boil):
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    if CUT_P1 <= t < CUT_END:
        stars_field(sp, VS, t, .02, n=50, seed=4)
        PIC.draw(sp, t, 0, w=4.5)
        sp.rect(560, 420, 1060, 520, 5, PAPER, 'desk', fill=INK)
        sp.text('ADM. PICARD // U.S.S. ENTERPRISE', (810, 448), 24, PAPER, 'marker')
        sp.rect(1000, 385, 1036, 420, 3, PAPER, 'cup'); sp.arc((1040, 402), 10, 10, -90, 90, 3, PAPER, 'hdl')
        for j in range(2): sp.line([(1010 + 12 * j, 378), (1006 + 12 * j + 4 * math.sin(t * 6 + j), 352)], 2, PAPER, f'stm{j}')
        sp.text('INPUT LAG BLIPS: 0', (1220, 160), 28, PAPER, 'marker'); SETS.check(sp, (1220, 230), 40, 'pchk')
    else:
        desktop(sp, t)
        if T_BEAM <= t < T_OUT1:      # mini Grok Bot in the desktop
            lay = sub.copy(); lp = Pen(lay, cam, boil); MINI.draw(lp, t, 0, w=4)
            if t < T_BEAM1: dissolve(sub, lay, t, T_BEAM + .1, T_BEAM1, 7, out=False)
            elif t >= T_OUT: dissolve(sub, lay, t, T_OUT, T_OUT1 - .05, 9, out=True)
            else: sub[:] = lay
            beam(sp, t, T_BEAM + .1, T_BEAM1, (1285, 440), .55, PAPER, 'mb')
            beam(sp, t, T_OUT, T_OUT1, (1285, 440), .55, PAPER, 'mo')
    clip_paste(img, sub, pen, VS)

def bridge(t, cam):
    boil = int(t * 12)
    img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    pen.line([(-600, 60), (400, 60), (460, 92)], 4, INK, 'rail1'); pen.line([(1380, 92), (1440, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (1640, 120), 40, INK, 'marker')
    viewscreen(img, pen, t, cam, boil)
    lag_counter(pen, t)
    h = {}
    h['barclay'] = BARC.draw(pen, t, 0, w=5.5 * SC ** .3)
    chair(pen, RCHAIR, SC, -1.0, 'rch')   # Riker sits backwards
    h['riker'] = RIKER.draw(pen, t, 0, w=5.5 * SC ** .3)
    # Grok Bot on the bridge: there until he beams into the desktop, back (saluting) at the end
    gx = (560, STAND)
    if t < T_BEAM1 or t >= T_BACK:
        lay = img.copy(); lp = Pen(lay, cam, boil); h['grokbot'] = GROK.draw(lp, t, 0, w=5.5 * SC ** .3)
        if t < T_BEAM: img[:] = lay
        elif t < T_BEAM1: dissolve(img, lay, t, T_BEAM, T_BEAM1 - .05, 3, out=True)
        else: dissolve(img, lay, t, T_BACK, T_BACK1, 5, out=False)
    beam(pen, t, T_BEAM, T_BEAM1, (gx[0], gx[1] + 40), 1.0, INK, 'gb')
    beam(pen, t, T_BACK, T_BACK1, (gx[0], gx[1] + 40), 1.0, INK, 'gk')
    if T_BEAM <= t < T_BEAM1 + .3:      # shimmer arc from Grok Bot up into the viewscreen
        u = clamp01((t - T_BEAM) / .6)
        for j in range(6):
            v = clamp01(u * 1.3 - j * .06); p = (lerp(gx[0], 1285, v), lerp(gx[1] - 120, 400, v) - 120 * math.sin(math.pi * v))
            sparkle(pen, p, 14 - j, INK, f'trail{j}{boil}')
    if T_BACK + .3 <= t: SETS.outlined(pen, '*salute*', (gx[0] + 150, gx[1] - 260), 36, 4, 'hand')
    return img, h

# swivel chair (from demo16), sat forwards
def chair(pen, cx, s, m, sid):
    sy = FLOOR - 52 * s
    pen.line([(cx - 52 * s * m, sy), (cx + 40 * s * m, sy)], 6 * s ** .5, INK, sid + 'seat')
    back = [(cx + 34 * s * m, sy), (cx + 40 * s * m, FLOOR - 152 * s), (cx + 56 * s * m, FLOOR - 152 * s), (cx + 50 * s * m, sy)]
    pen.fill(back, PAPER); pen.line(back, 5 * s ** .5, INK, sid + 'back', closed=True)
    pen.line([(cx - 6 * s * m, sy), (cx - 6 * s * m, FLOOR)], 6 * s ** .5, INK, sid + 'ped')
    pen.line([(cx - 44 * s, FLOOR), (cx + 32 * s, FLOOR)], 6 * s ** .5, INK, sid + 'base')

SETFN = {'bridge': bridge}
def flash(img, t): return img

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
    return flash(finish(img, int(t * 12), clamp01((SCENE - t) / .4)), t)


def poster():
    """key art: desktop with the stuttering pen and the rotated starship, LAG counter at 99, mini Grok shrugging; title band"""
    a, _ = bridge(T_L99 + .5, (960, 470, 1.0))
    img = a.copy(); pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(500, 930, 1420, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'WRONG MONITOR', (960, 972), 108, 7)
    pen.line([(600, 1026), (1320, 1021)], 5, INK, 'tul')
    pen.text('Riker \u00d7 Grok Bot \u00d7 Barclay \u00d7 Picard  \u00b7  STARSHIP GROKBOT', (960, 1052), 30, INK, 'hand')
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'picard': 'PICARD', 'barclay': 'BARCLAY', 'redshirt': 'RED SHIRT', }; ev = []; Ls = TL['lines']
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
    st = time.time(); os.makedirs(f'{HERE}/parts', exist_ok=True); n = 3
    captions(f'{HERE}/captions.ass')
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    ps = [subprocess.Popen([sys.executable, __file__, '--part', str(k), str(n)], env=env) for k in range(n)]
    if any(p.wait() for p in ps): sys.exit('part failed')
    open(f'{HERE}/parts/list.txt', 'w').write(''.join(f"file 'p{k:02d}.mp4'\n" for k in range(n)))
    out = f'{HERE}/wrongmonitor-nosfx.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
