"""Dialogue short #13: "THINKING PARTNER" - the two doodles from the 'Thinking with AI' cover hop out of the book onto
the Titan bridge. The Thinker asks Grok Bot (book edition) the meaning of life; Grok Bot answers with a better question.
Riker tries it too. Button: Riker's thought cloud fills with a trombone (2/3 punch-in + hold).
    python thinkingpartner.py | --frames t ... | --poster"""
import sys, os, json, math, subprocess, time
SP = '/workspace/holodeck/titan-hello-world/stick-poc'; sys.path.insert(0, SP)
sys.path.insert(0, '/workspace/holodeck/cover-chars')
_argv = sys.argv; sys.argv = [sys.argv[0]]
import rig_test as RT                                   # planted IK helpers + no-mottle paper
sys.argv = _argv
import numpy as np, cv2
cv2.setNumThreads(1)
from stickfig import *
from inkset import W, H, FLOOR, console, sparkle, stars_field, thoughtcloud
import sets as SETS
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(f'{HERE}/timeline.json')); FPS = 24; SCENE = TL['total']; HOLD, WIPE = 0.5, 0.33; TOTAL = SCENE + HOLD
ENV = {k: np.array(v) for k, v in TL['env'].items()}
WT = {L['id']: {} for L in TL['lines']}
for L in TL['lines']:
    for x in L['words']: WT[L['id']].setdefault(x['w'].strip('.,!?:').lower(), x['s'])
LN = {L['id']: L for L in TL['lines']}
def w(line, word, off=0.0): return WT[line][word] + off

# ------------------------------------------------------------------ layout + cue table
SC = 1.4; STAND = FLOOR - 110 * SC
K = 0.66                                                 # cover-rig scale -> bridge scale (matches Riker's height)
KC = 0.30                                                # scale while still drawn on the book cover
RB = dict(S=1.76, hip=138, seg=dict(th=44, sh=46, ua=36, fa=52))
HB = dict(S=2.0, hip=188, seg=dict(th=52, sh=50, ua=40, fa=42))
BOOK = (90, FLOOR - 470, 430, FLOOR)
COVER_FEET = FLOOR - 78
R_COVER_X, H_COVER_X = 200, 322
R_X, H_X, RIK_X = 640, 860, 1390
HOP_R = (0.75, 1.3); HOP_H = (1.2, 1.75)
CUT_R1 = LN['r1']['s'] - .2; CUT_T1 = LN['t1']['s'] - .15; CUT_G1 = LN['g1']['s'] - .15; CUT_T2 = LN['t2']['s'] - .15
CUT_R2 = LN['r2']['s'] - .2; CUT_G2 = LN['g2']['s'] - .15; T_BTN = LN['g2']['e'] + .12
T_THINK = w('t2', 'hmm', -.1); T_BULB = w('t2', 'better', -.05); T_TROMB = T_BTN + .3
Q_TICKS = [w('t1', 'meaning'), w('g1', 'think'), w('r2', 'meaning'), w('g2', 'think')]

def hop(t, a, b, x0, y0, x1, y1, s0, s1):
    """(x, hipY, scale) for a hop off the cover: arc up then down, scale grows cover->bridge size"""
    u = clamp01((t - a) / (b - a)); e = ease(u)
    return lerp(x0, x1, e), lerp(y0, y1, e) - 170 * math.sin(math.pi * u), lerp(s0, s1, e)

def robot_state(t):
    s0, s1 = RB['S'] * KC, RB['S'] * K
    return hop(t, *HOP_R, R_COVER_X, COVER_FEET - RB['hip'] * KC, R_X, FLOOR - RB['hip'] * K, s0, s1)
def human_state(t):
    s0, s1 = HB['S'] * KC, HB['S'] * K
    return hop(t, *HOP_H, H_COVER_X, COVER_FEET - HB['hip'] * KC, H_X, FLOOR - HB['hip'] * K, s0, s1)

TUCK = 'idle+lhip=35+lkn=-70+rhip=45+rkn=-80+rsh=150+rel=10+lsh=-150+lel=-10'
KEYS = dict(
    grokbot=[(0, 'idle', 0), (HOP_R[0] + .05, TUCK, .12), (HOP_R[1] - .05, 'idle+rsh=120+rel=20', .12), (HOP_R[1] + .5, 'idle', .3),
             (LN['r1']['e'] - .5, 'idle+tilt=6', .3), (CUT_G1 + .1, 'palm+lean=4', .25), (LN['g1']['e'] + .2, 'idle', .3),
             (CUT_G2 + .1, 'palm+lean=4', .25), (LN['g2']['e'] + .25, 'idle+mouth=1', .3)],
    thinker=[(0, 'idle', 0), (HOP_H[0] + .05, TUCK, .12), (HOP_H[1] - .05, 'idle', .12),
             (CUT_T1 + .1, 'palm+lean=6', .25), (LN['t1']['e'] + .2, 'idle', .3),
             (T_THINK, 'think+rsh=18+rel=162+lsh=-66+lel=88+tilt=-4+lean=10', .4), (LN['t2']['e'] + .4, 'idle+look_r', .4),
             (LN['g2']['s'] + .5, 'idle', .4)],
    riker=[(0, 'idle', 0), (LN['r1']['s'] - .1, 'palm', .25), (w('r1', 'give', 0), 'idle+rsh=105+rel=35', .25),
           (LN['r1']['e'] + .2, 'idle', .3), (CUT_T2, 'hips', .3), (LN['r2']['s'] - .05, 'idle+rsh=80+rel=20', .25),
           (w('r2', 'what', -.1), 'point', .2), (LN['r2']['e'] + .2, 'hips', .3), (T_BTN + .05, 'chinrub', .3)],
)
NODS = dict(thinker=[w('g1', 'think', .05)], grokbot=[w('t2', 'questions', .05)], riker=[w('t1', 'life', .05)])

def env_mod(who, F=None):
    env = ENV.get(who, np.zeros(1)); nods = NODS.get(who, [])
    def f(t, P):
        i = int(t * FPS); e = float(env[i]) if i < len(env) else 0.0
        e2 = float(env[max(i - 2, 0)]) if i < len(env) else 0.0
        P['talk'] = e; P['tilt'] += 7 * (e - e2) + 3 * e; P['lean'] += 2.5 * e * (1 - P.get('front', 0))
        for tn in nods:
            u = t - tn
            if 0 <= u < .7: P['tilt'] += 12 * math.sin(math.pi * u / .35) * (1 - u / .7)
        if who == 'grokbot': P['antamp'] = 7 + 8 * e + 10 * (HOP_R[0] < t < HOP_R[1] + .4)
        if who == 'riker' and t > T_BTN + .35:            # slow beard stroke
            P['rel'] += 12 * math.sin((t - T_BTN) * 2 * math.pi * .9)
        if who == 'thinker' and t > T_THINK and F is not None:
            P = think_ik(F, t, P)
        return P
    return f

def think_ik(F, t, P):
    """near hand onto the chin (arm IK from the exact rig root), with small taps"""
    wk = ease((t - T_THINK) / .4) * (1 - ease((t - LN['t2']['e'] - .4) / .4))
    if wk <= 0: return P
    x, y = F.pos_at(t); S = F.scale; f = F.facing
    lean = P['lean'] + 1.3 * math.sin(t * 2 * math.pi / 3.1 + len(F.name)); ul = math.radians(lean)
    up = (f * math.sin(ul), -math.cos(ul)); L = (F.seg['torso'] + F.seg['neck']) * S
    neck = (x + up[0] * L, y + up[1] * L); ht = math.radians(lean + P['tilt'] - 14 * P['lookup']); R = F.seg['r'] * S
    head = (neck[0] + f * math.sin(ht) * R, neck[1] - math.cos(ht) * R)
    tap = 5 * max(0.0, math.sin(2 * math.pi * 1.6 * (t - T_THINK - .5))) ** 2 * (t > T_THINK + .5)
    chin = (head[0] + f * R * .32, head[1] + R * .98 + tap)
    roots = RT.leg_roots(F, t, P, 0)
    a1, a2 = RT.ik(roots[(1, False)], chin, F.seg['ua'] * S, F.seg['fa'] * S, f, flip=True)
    P['rsh'], P['rel'] = lerp(P['rsh'], a1, wk), lerp(P['rel'], a2, wk)
    return P

def keyed(F, who):
    for k in KEYS[who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])

ROBOT = Figure('coverbot', R_COVER_X, 0, 1, {'boxbot', 'antenna', 'feet'}, scale=RB['S'] * KC, seg=RB['seg']); keyed(ROBOT, 'grokbot')
HUMAN = Figure('coverhuman', H_COVER_X, 0, -1, {'bean', 'tuft', 'bowtie', 'shoes'}, scale=HB['S'] * KC, seg=HB['seg']); keyed(HUMAN, 'thinker')
ROBOT.mod = env_mod('grokbot', ROBOT); HUMAN.mod = env_mod('thinker', HUMAN)
ROBOT.pos_at = lambda t: robot_state(t)[:2]; HUMAN.pos_at = lambda t: human_state(t)[:2]

RIKER = Figure('riker', 2200, STAND, -1, {'beard', 'badge'}, scale=SC); keyed(RIKER, 'riker')
RIKER.move(1.0, RIK_X, STAND, 1.5)
_rbase = env_mod('riker')
def _rmod(t, P):
    P = _rbase(t, P)
    x0, y0 = RIKER.pos_at(t); x1, _ = RIKER.pos_at(t + .04); v = abs(x1 - x0) / .04
    if v > 40:                                           # series walking stride (CAPTCHA)
        a = min(v / 400, 1); ph = math.sin(t * 2 * math.pi * 2.4)
        P['lhip'] += 26 * a * ph; P['rhip'] -= 26 * a * ph
        P['lkn'] -= 22 * a * max(-ph, 0); P['rkn'] -= 22 * a * max(ph, 0)
        P['lsh'] -= 16 * a * ph; P['rsh'] += 16 * a * ph
    return P
RIKER.mod = _rmod

SHOTS = [
    (0.0, [(0.0, (900, 540, 1.0), 0), (0.0, (860, 560, 1.06), 2.4)]),
    (CUT_R1, [(CUT_R1, (1010, 560, 1.15), 0)]),
    (CUT_T1, [(CUT_T1, (770, 610, 1.6), 0)]),
    (CUT_G1, [(CUT_G1, (760, 620, 1.85), 0)]),
    (CUT_T2, [(CUT_T2, (870, 560, 1.6), 0), (CUT_T2, (880, 550, 1.66), LN['t2']['e'] - CUT_T2)]),
    (CUT_R2, [(CUT_R2, (1010, 560, 1.15), 0)]),
    (CUT_G2, [(CUT_G2, (760, 620, 1.9), 0)]),
    (T_BTN, [(T_BTN, (1500, 645, 1.92), 0), (T_BTN + .35, (1504, 640, 1.98), SCENE - T_BTN - .35)]),   # Riker ~2/3 of frame
]
SHOTS = [dict(at=a, cam=c) for a, c in SHOTS]
for i, s in enumerate(SHOTS): s['end'] = SHOTS[i + 1]['at'] if i + 1 < len(SHOTS) else 1e9

# ------------------------------------------------------------------ doodles
def bulb(pen, c, s, t, t0, sid='bulb'):
    k = ease_out_back(clamp01((t - t0) / .25))
    if k <= 0: return
    x, y = c; s = s * k
    pen.circle((x, y), 26 * s, 4, INK, sid + 'g', fill=PAPER)
    pen.line([(x - 12 * s, y + 22 * s), (x - 11 * s, y + 38 * s), (x + 11 * s, y + 38 * s), (x + 12 * s, y + 22 * s)], 4, INK, sid + 'b')
    for j in range(2): pen.line([(x - 11 * s, y + 29 * s + j * 6 * s), (x + 11 * s, y + 29 * s + j * 6 * s)], 3, INK, sid + f'th{j}')
    pen.line([(x - 8 * s, y + 8 * s), (x - 4 * s, y - 6 * s), (x, y + 4 * s), (x + 4 * s, y - 6 * s), (x + 8 * s, y + 8 * s)], 3, INK, sid + 'f')
    if t - t0 > .15:
        for j in range(7):
            a = -math.pi / 2 + (j - 3) * .42; r0, r1 = 36 * s, (50 + 6 * math.sin(t * 9 + j)) * s
            pen.line([(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))], 4, INK, sid + f'r{j}')

def trombone(pen, c, s, t, t0, sid='tb'):
    k = ease_out_back(clamp01((t - t0) / .25))
    if k <= 0: return
    x, y = c; s = s * k; sl = 6 * math.sin((t - t0) * 7) * s * (t - t0 < 1.0)
    pen.line([(x - 70 * s, y - 10 * s), (x + 40 * s, y - 10 * s)], 4, INK, sid + 'a')            # upper tube -> bell
    pen.line([(x - 70 * s + sl, y + 10 * s), (x + 20 * s, y + 10 * s)], 4, INK, sid + 'b')       # slide
    pen.arc((x - 70 * s + sl, y), 10 * s, 10 * s, 90, 270, 4, INK, sid + 'u')                   # U bend
    pen.line([(x + 20 * s, y + 10 * s), (x + 20 * s, y - 10 * s)], 3, INK, sid + 'c')
    pen.line([(x + 40 * s, y - 10 * s), (x + 70 * s, y - 30 * s), (x + 70 * s, y + 10 * s), (x + 40 * s, y - 4 * s)], 4, INK, sid + 'bell')
    for j in range(3):
        nx, ny = x + 100 * s + 22 * j * s, y - 26 * s - 20 * j * s + 5 * math.sin(t * 6 + j) * s       # doodled eighth notes
        pen.fill([(nx + 7 * s * math.cos(q), ny + 5 * s * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 12)], INK)
        pen.line([(nx + 6 * s, ny), (nx + 6 * s, ny - 22 * s), (nx + 14 * s, ny - 14 * s)], 3, INK, sid + f'n{j}')

def counter(sp, t):
    q = sum(t >= x for x in Q_TICKS); last = max([x for x in Q_TICKS if t >= x], default=-9)
    pop = 1 + .25 * max(0.0, 1 - (t - last) / .25)
    sp.text('QUESTIONS ASKED', (800, 350), 34, PAPER, 'marker'); sp.text(str(q), (1110, 350), 52 * pop, PAPER, 'marker')
    sp.text('ANSWERS GIVEN', (800, 428), 34, PAPER, 'marker'); sp.text('0', (1110, 428), 52, PAPER, 'marker')
    sp.line([(600, 390), (1320, 388)], 2, PAPER, 'cdiv', wob=.3)

def book(pen, t):
    x0, y0, x1, y1 = BOOK
    pen.line([(x1, y0), (x1 + 26, y0 + 18), (x1 + 26, y1 - 4), (x1, y1)], 4, INK, 'bkspine')       # page block
    for j in range(3): pen.line([(x1 + 7 + 6 * j, y0 + 10 + 4 * j), (x1 + 7 + 6 * j, y1 - 6)], 2, INK, f'bkpg{j}', wob=.3)
    pen.rect(x0, y0, x1, y1, 5, INK, 'bkcover', fill=PAPER)
    pen.text('Thinking with AI', ((x0 + x1) / 2, y0 + 50), 40, INK, 'serif')
    pen.text('Nate Haskins', ((x0 + x1) / 2, y1 - 28), 26, INK, 'serif')
    thoughtcloud(pen, (262, FLOOR - 300), 92, 52, t, sid='bkcloud', n=10, w=2.6, puffs=((262, FLOOR - 228, 8),), boil=1.0)
    if .25 < t < 1.9:                                    # magic sparkles as the doodles wake up
        for j in range(6):
            a = t * 3 + j * 1.05; r = 150 + 30 * math.sin(t * 5 + j)
            sparkle(pen, (262 + r * math.cos(a) * .9, FLOOR - 230 + r * math.sin(a) * 1.1), 12 + 4 * math.sin(t * 9 + j), INK, f'bks{j}')

# ------------------------------------------------------------------ set: Titan bridge
VS = (560, 100, 1360, 480)
def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

def titan(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    pen.line([(-600, 60), (480, 60), (540, 92)], 4, INK, 'rail1'); pen.line([(1380, 92), (1440, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (250, 40), 40, INK, 'marker')
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vsframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    stars_field(sp, VS, t, 0.02, n=40, seed=13)
    sp.text('THINKING PARTNER MODE', (960, 180), 44, PAPER, 'marker'); sp.line([(700, 215), (1220, 213)], 3, PAPER, 'vsul')
    counter(sp, t)
    clip_paste(img, sub, pen, VS)
    console(pen, 1580, 1750, 712, sid='sci', label='SCI')
    book(pen, t)
    ws = 5.5 * SC ** .3
    rx, ry, rs = robot_state(t); hx, hy, hs = human_state(t)
    ROBOT.scale = rs; HUMAN.scale = hs
    lw = lambda s, base: lerp(2.6, 4.8, clamp01((s - base * KC) / (base * (K - KC))))
    ROBOT.draw(pen, t, 0, w=lw(rs, RB['S'])); HUMAN.draw(pen, t, 0, w=lw(hs, HB['S']))
    for a, b, (x, s) in ((HOP_R[1], 'r', (R_X, 1)), (HOP_H[1], 'h', (H_X, 1))):          # landing puffs
        if a <= t < a + .45:
            u = clamp01((t - a) / .45)
            for j in range(3): pen.arc((x - 50 + 50 * j, FLOOR - 8), 16 + 26 * u, 8, 180, 360, 3, INK, f'pf{b}{j}')
    RIKER.draw(pen, t, 0, w=ws)
    if t > T_THINK + .2 and t < LN['t2']['e'] + 1.2:     # Thinker's cloud + lightbulb
        k = ease_out_back(clamp01((t - T_THINK - .2) / .35)); hxh = hx + 40
        if k > .05:
            thoughtcloud(pen, (hxh, FLOOR - 470), 150 * k, 80 * k, t, sid='tcloud', n=11, w=4,
                         puffs=((hx + 10, FLOOR - 368, 10 * k), (hx - 4, FLOOR - 340, 6 * k)), boil=1.0)
            if t < T_BULB: pen.text('?', (hxh, FLOOR - 470), 90 * k, INK, 'marker')
            bulb(pen, (hxh, FLOOR - 478), 1.2, t, T_BULB)
    if t > T_TROMB:                                      # button: Riker's cloud fills with a trombone
        k = ease_out_back(clamp01((t - T_TROMB) / .3)); cx_, cy_ = RIK_X + 240, STAND - 250
        thoughtcloud(pen, (cx_, cy_), 140 * k, 70 * k, t, sid='rcloud', n=11, w=4,
                     puffs=((RIK_X + 85, STAND - 205, 10 * k), (RIK_X + 52, STAND - 188, 6 * k)), boil=1.0)
        trombone(pen, (cx_ - 40, cy_ + 10), 1.55 * k, t, T_TROMB + .15)
    return img

# ------------------------------------------------------------------ frame assembly
def cam_at(sh, t):
    keys = sh['cam']; cam = keys[0][1]
    for i, (tk, c, dur) in enumerate(keys):
        if t < tk: break
        prev = cam if i else c
        k = ease((t - tk) / dur) if dur > 0 else 1.0
        cam = tuple(lerp(a, b, k) for a, b in zip(prev, c))
    return cam

VIG, GRAINS = RT.paper_finish_clean()                    # no low-frequency mottle (the "cloud" Nathan flagged)
def finish(img, boil, fade=1.0):
    f = img.astype(np.float32) * VIG + GRAINS[boil % 4]
    if fade < 1: f = f * fade + np.array(PAPER, np.float32) * (1 - fade)
    return np.clip(f, 0, 255).astype(np.uint8)

def scene(t):
    sh = next(s for s in SHOTS if s['at'] <= t < s['end'])
    return finish(titan(t, cam_at(sh, t)), int(t * 12), clamp01((SCENE - t) / .4))

def poster():
    tt = T_BULB + .6
    img = titan(tt, (1000, 470, 1.12))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(500, 925, 1420, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'THINKING PARTNER', (960, 972), 104, 7)
    pen.line([(620, 1026), (1300, 1021)], 5, INK, 'tul')
    pen.text('Thinking with AI \u00d7 STARSHIP GROKBOT  \u00b7  Riker \u00d7 Grok Bot \u00d7 The Thinker', (960, 1052), 32, INK, 'hand')
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'thinker': 'THE THINKER'}; ev = []; Ls = TL['lines']
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
        im = poster(); cv2.imwrite(f'{HERE}/thumbnail.png', im); cv2.imwrite(f'{HERE}/thinkingpartner-thumb.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 92]); sys.exit()
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
    out = f'{HERE}/thinkingpartner-nosfx.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
