"""Dialogue short #16: "VOICE CLONE" - Grok Bot clones Riker's voice so he can attend Riker's meetings. The copies multiply on
the comm (RIKERS: 2 -> 37) until Barclay finds the tell: the real one sits on his chair backwards. Every Riker flips his chair
at once; Picard facepalms. First episode on xAI voices (Riker = Nate's custom voice).
    python voiceclone.py | --frames t ... | --poster"""
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
from inkset import W, H, FLOOR, stars_field, ship
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
T_UPL = 0.0                                             # viewscreen: waveform + UPLOAD 100% stamp (stamps in at the start)
T_STAMP = wt('g1', 'cloned', 0, .05)
T_COPY = LN['g2']['s'] - .05                            # Grok Bot sprouts a doodled beard, counter appears at 2
T_C4 = wt('s1', 'four', 0, -.05); T_C9 = wt('s1', 'comm', 0, -.05); T_C37 = LN['s1']['e'] + .2
T_FLIP = LN['b1']['e'] + .12                            # every Riker flips his chair backwards (whoosh)
T_FP = T_FLIP + .75                                     # Picard punch-in facepalm, held to the end
CUT_R1 = LN['r1']['s'] - .15; CUT_G2 = LN['g2']['s'] - .15; CUT_S1 = LN['s1']['s'] - .15
CUT_P1 = LN['p1']['s'] - .15; CUT_B1 = LN['b1']['s'] - .15
def rikers(t):
    return 1 if t < T_COPY else 2 if t < T_C4 else 4 if t < T_C9 else 9 if t < T_C37 else 37

KEYS = dict(
    grokbot=[(0, 'idle+look_r', 0), (LN['g1']['s'] - .05, 'palm', .25), (wt('g1', 'attend', 0, -.15), 'present', .25),
             (LN['g1']['e'] + .3, 'idle+look_r', .3), (T_COPY, 'proud', .25), (wt('g2', 'swagger', 0, -.1), 'thumbs', .2),
             (LN['g2']['e'] + .3, 'idle+look_r', .3), (CUT_B1 + .3, 'idle+look_l', .3), (T_FLIP, 'surprise', .15)],
    riker=[(0, 'sit+look_l', 0), (LN['r1']['s'] + .1, 'sit+mouth=2', .2), (wt('r1', 'nobody', 0, -.1), 'sit+chinrub', .25),
           (wt('r1', 'years', 0, -.1), 'sit+rsh=80+rel=10', .2), (T_COPY + .1, 'sit+rsh=20+rel=150+mouth=3', .2),
           (CUT_S1 + .2, 'sit+chinrub', .3), (T_FLIP - .02, 'straddle+mouth=2', .22)],
    redshirt=[(0, 'idle+look_l', 0), (LN['s1']['s'] - .1, 'handear+look_l', .25), (T_C37 - .1, 'surprise', .2), (CUT_P1 + .5, 'idle+look_l', .3)],
    barclay=[(0, 'hunch', 0), (T_COPY + .2, 'nervous', .3), (LN['b1']['s'] - .05, 'present_padd', .25), (wt('b1', 'real', 0, -.1), 'point+rsh=60', .2),
             (wt('b1', 'backwards', 0, -.1), 'proud', .2), (T_FLIP + .3, 'tada', .2)],
    picard=[(0, 'front+rsh=40+rel=110+tilt=4', 0), (LN['p1']['s'] - .1, 'front+lsh=30+lel=-70+rsh=30+rel=-70', .3),
            (wt('p1', 'which', 0, -.1), 'front+lsh=20+lel=10+rsh=60+rel=80', .25), (T_FP - .05, 'facepalmF', .15)],
)
NODS = dict(grokbot=[LN['g1']['s'] + .05, LN['g2']['s'] + .05], riker=[wt('r1', 'nobody', 0, .02)], redshirt=[LN['s1']['s'] + .05],
            picard=[wt('p1', 'number', 0, .02)], barclay=[LN['b1']['s'] + .05, wt('b1', 'backwards', 0, .02)])

SHOTS = [
    (0.0, [(0.0, (960, 520, 1.0), 0), (0.0, (900, 520, 1.06), LN['g1']['e'])]),
    (CUT_R1, [(CUT_R1, (1000, 560, 1.18), 0)]),
    (CUT_G2, [(CUT_G2, (960, 520, 1.0), 0)]),
    (CUT_S1, [(CUT_S1, (1060, 540, 1.04), 0), (CUT_S1, (1100, 540, 1.0), LN['s1']['e'] + .5 - CUT_S1)]),
    (CUT_P1, [(CUT_P1, (1010, 420, 1.3), 0), (CUT_P1, (1012, 400, 1.34), LN['p1']['e'] - CUT_P1)]),
    (CUT_B1, [(CUT_B1, (960, 520, 1.0), 0)]),
    (T_FP, [(T_FP, (820, 300, 3.1), 0), (T_FP + .3, (820, 296, 3.2), 1.5)]),          # Picard ~2/3 of frame height
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
    base = make_mod(who)
    def mod(t, P):
        P = base(t, P)
        x0, y0 = F.pos_at(t); x1, y1 = F.pos_at(t + .04)
        v = abs(x1 - x0) / .04
        if v > 40:
            a = min(v / 400, 1); ph = math.sin(t * 2 * math.pi * 2.4)
            P['lhip'] += 26 * a * ph; P['rhip'] -= 26 * a * ph
            P['lkn'] -= 22 * a * max(-ph, 0); P['rkn'] -= 22 * a * max(ph, 0)
        return P
    F.mod = mod; return F


def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

BARC = fig('barclay', 250, STAND, 1, ['curly', 'badge'], scale=SC)
GROK = fig('grokbot', 620, STAND, 1, ['robot'], scale=SC)
RIKER = fig('riker', 1000, SEATY, -1, ['beard', 'badge'], scale=SC)
RS = fig('redshirt', 1760, STAND, -1, ['redshirt', 'ponytail'], scale=SC)
PIC = fig('picard', 800, 430, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=1.25)
RCHAIR = 1000

# clones: (x, scale, arrive) - they glide in on swivel chairs from the right, sat forwards (the tell)
CLONES = [(1180, 1.0, T_C4), (1330, .95, T_C4 + .12)] + \
    [(x, s, T_C9 + .07 * i) for i, (x, s) in enumerate([(1110, .78), (1250, .8), (1400, .76), (1520, .9), (1640, .74), (1460, .72), (1590, .95)])] + \
    [(x, s, T_C37 + .05 * i) for i, (x, s) in enumerate([(1060, .62), (1170, .6), (1290, .64), (1360, .58), (1700, .62), (1820, .66), (1880, .9), (1540, .6), (1230, .56)])]
CLONES.sort(key=lambda c: c[1])                          # smaller (further back) first
CL = []
for i, (x, s, ta) in enumerate(CLONES):
    sy = FLOOR - 58 * s
    F = Figure('riker', 2200, sy, -1, {'beard', 'badge'}, scale=s)
    F.move(ta, x, sy, .35)
    F.key(-1e8, 'sit+look_l', 0); F.key(ta + .3 + (i % 3) * .1, 'sit+chinrub', .3); F.key(T_FLIP - .02, 'straddle+mouth=2', .22)
    if i % 2: F.key(T_C37 + .6, 'sit+rsh=80+rel=10', .25); F.key(T_C37 + 1.4, 'sit+chinrub', .3)
    def mod(t, P, i=i):
        P['tilt'] += 3 * math.sin(t * 5 + i); return P
    F.mod = mod; CL.append((F, s, ta))

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

# ------------------------------------------------------------------ props
def chair(pen, cx, s, m, sid):
    """swivel chair; m = +1 back on the right (sat forwards, facing left), -1 back on the left (backwards); |m|<1 mid-spin"""
    sy = FLOOR - 52 * s
    pen.line([(cx - 52 * s * m, sy), (cx + 40 * s * m, sy)], 6 * s ** .5, INK, sid + 'seat')
    back = [(cx + 34 * s * m, sy), (cx + 40 * s * m, FLOOR - 152 * s), (cx + 56 * s * m, FLOOR - 152 * s), (cx + 50 * s * m, sy)]
    if abs(m) > .08: pen.fill(back, PAPER); pen.line(back, 5 * s ** .5, INK, sid + 'back', closed=True)
    pen.line([(cx - 6 * s * m, sy), (cx - 6 * s * m, FLOOR)], 6 * s ** .5, INK, sid + 'ped')
    pen.line([(cx - 44 * s, FLOOR), (cx + 32 * s, FLOOR)], 6 * s ** .5, INK, sid + 'base')
def chair_m(t):
    if t < T_FLIP: return 1.0
    return math.cos(math.pi * clamp01((t - T_FLIP) / .25))
def spin_lines(pen, cx, s, t, sid):
    u = t - T_FLIP
    if 0 <= u < .45:
        a = 1 - u / .45
        for j in range(3):
            y = FLOOR - (60 + 40 * j) * s
            pen.arc((cx, y), 90 * s, 18 * s, 200 + 40 * j, 340 + 40 * j - 120 * (1 - a), 3, INK, f'{sid}sp{j}')

def wall_counter(pen, t):
    if t < T_COPY: return
    x, y = 1560, 250; n = rikers(t)
    k = ease_out_back(clamp01((t - T_COPY) / .25))
    last = max([T_COPY, T_C4, T_C9, T_C37][i] for i in range(4) if [T_COPY, T_C4, T_C9, T_C37][i] <= t)
    sq = 1 + .25 * max(0, 1 - (t - last) / .25)
    pen.rect(x - 175 * k, y - 62 * k, x + 175 * k, y + 62 * k, 5, INK, 'cnt', fill=PAPER)
    pen.text(f'RIKERS: {n}', (x, y + 4), 62 * k * sq, INK, 'marker')
    if n == 37 and t - T_C37 < .7: SETS.burst(pen, (x, y), t, T_C37, 220, 12, INK, 'cb37', .6, 3)
    if t - last < .5 and last > T_COPY: SETS.outlined(pen, '!', (x + 205, y - 40), 70, 5)

def beard_on_grok(pen, h, t):
    if t < T_COPY: return
    hd, R = h['head'], h['R']; k = clamp01((t - T_COPY) / .3)
    if k <= 0: return
    top = hd[1] + R * .95; L = R * (.3 + 1.3 * k)
    pts = [(hd[0] - R * 1.0, top), (hd[0] - R * .85, top + L * .6), (hd[0], top + L), (hd[0] + R * .85, top + L * .6), (hd[0] + R * 1.0, top)]
    pen.fill(pts, PAPER); pen.line(pts, 4.5, INK, 'gbeard', closed=True)
    for j in range(6): pen.line([(hd[0] + R * (-.75 + .3 * j), top + R * .12), (hd[0] + R * (-.65 + .26 * j), top + L * (.45 + .1 * (j % 2)))], 2.5, INK, f'gbh{j}')
    if t - T_COPY < .6: SETS.outlined(pen, '*fizz*', (hd[0] + R * 1.6, hd[1] - R * 1.6), 40, 4, 'hand')

def facepalm_slap(pen, t):
    if T_FP <= t < T_FP + .6:
        k = ease_out_back(clamp01((t - T_FP) / .18)); SETS.outlined(pen, 'SMACK.', (965, 175), 46 * k + 1, 4)

VS = (480, 100, 1360, 470)
def wave_doodle(sp, x0, y0, x1, y1, t, w=4):
    n = 70; pts = []
    for i in range(n):
        u = i / (n - 1); x = lerp(x0, x1, u)
        a = (y1 - y0) / 2 * (.25 + .75 * abs(math.sin(u * 9.1 + 1.3)) * abs(math.sin(u * 3.3)))
        pts.append((x, (y0 + y1) / 2 + a * math.sin(u * 60 + t * 4)))
    sp.line(pts, w, PAPER, 'wave')
def viewscreen(img, pen, t, cam, boil):
    x0, y0, x1, y1 = VS; vc = (x0 + x1) / 2
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    stars_field(sp, VS, t, .02, n=50, seed=4)
    if t < CUT_P1:
        sp.text('VOICE PRINT: CMDR. RIKER', (vc, y0 + 50), 40, PAPER, 'marker')
        wave_doodle(sp, x0 + 60, y0 + 100, x1 - 60, y1 - 90, t)
        sp.rect(x0 + 60, y1 - 60, x1 - 60, y1 - 34, 3, PAPER, 'bar', fill=INK)
        sp.rect(x0 + 64, y1 - 56, x0 + 64 + (x1 - x0 - 128) * clamp01((t + .3) / (T_STAMP + .3)), y1 - 38, 0, fill=PAPER)
        if t >= T_STAMP:
            SETS.stamp(sp, 'UPLOAD 100%', (vc + 160, y0 + 200), t, T_STAMP, 70, sid='upl')
    else:
        PIC.draw(sp, t, 0, w=4.5)
        sp.rect(560, 420, 1060, 520, 5, PAPER, 'desk', fill=INK)
        sp.text('ADM. PICARD // U.S.S. ENTERPRISE', (810, 448), 24, PAPER, 'marker')
        # tea
        sp.rect(1000, 385, 1036, 420, 3, PAPER, 'cup'); sp.arc((1040, 402), 10, 10, -90, 90, 3, PAPER, 'hdl')
        for j in range(2): sp.line([(1010 + 12 * j, 378), (1006 + 12 * j + 4 * math.sin(t * 6 + j), 352)], 2, PAPER, f'stm{j}')
        wave_doodle(sp, 1110, 140, 1330, 230, t, 3)                 # the cloned voice print, still live
        sp.text('RIKER  x' + str(rikers(t)), (1220, 270), 30, PAPER, 'marker')
    clip_paste(img, sub, pen, VS)

def bridge(t, cam):
    boil = int(t * 12)
    img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    pen.line([(-600, 60), (400, 60), (460, 92)], 4, INK, 'rail1'); pen.line([(1380, 92), (1440, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (1640, 120), 40, INK, 'marker')
    viewscreen(img, pen, t, cam, boil)
    wall_counter(pen, t)
    h = {}; m = chair_m(t); w = 5.5 * SC ** .3
    for i, (F, s, ta) in enumerate(CL):                 # the crowd of copies (behind the cast)
        if t < ta: continue
        x, _ = F.pos_at(t)
        chair(pen, x, s, m, f'cc{i}'); F.draw(pen, t, 0, w=w * s ** .6); spin_lines(pen, x, s, t, f'cl{i}')
        if t < ta + .4 and x > 1900 - 1: pass
    h['barclay'] = BARC.draw(pen, t, 0, w=w)
    chair(pen, RCHAIR, SC, m, 'rch')
    h['riker'] = RIKER.draw(pen, t, 0, w=w); spin_lines(pen, RCHAIR, SC, t, 'rk')
    h['grokbot'] = GROK.draw(pen, t, 0, w=w); beard_on_grok(pen, h['grokbot'], t)
    h['redshirt'] = RS.draw(pen, t, 0, w=w)
    if T_FLIP <= t < T_FLIP + .6:
        k = ease_out_back(clamp01((t - T_FLIP) / .2)); SETS.outlined(pen, 'WHOOSH!', (1380, 470), 80 * k + 1, 6)
    if LN['s1']['s'] <= t < LN['s1']['e'] + .2:
        SETS.outlined(pen, '(whisper)', (1760, 330), 32, 3, 'hand')
    facepalm_slap(pen, t)
    return img, h

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
    """key art: the crowd of bearded copies at RIKERS: 37, bearded Grok Bot front and centre; title band below"""
    a, _ = bridge(T_C37 + 1.0, (1000, 470, 1.0))
    img = a.copy(); pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(500, 930, 1420, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'VOICE CLONE', (960, 972), 108, 7)
    pen.line([(640, 1026), (1280, 1021)], 5, INK, 'tul')
    pen.text('Grok Bot \u00d7 Riker (\u00d737) \u00d7 Red Shirt \u00d7 Picard \u00d7 Barclay  \u00b7  STARSHIP GROKBOT', (960, 1052), 30, INK, 'hand')
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'picard': 'PICARD', 'barclay': 'BARCLAY', 'redshirt': 'RED SHIRT', 'g2': 'GROK BOT (AS RIKER)'}; ev = []; Ls = TL['lines']
    for i, L in enumerate(Ls):
        ws = [dict(x, s=x['s'] + HOLD, e=x['e'] + HOLD) for x in L['words']]; a = L['s'] + HOLD - 0.2
        nxt = Ls[i + 1]['s'] + HOLD - 0.2 if i + 1 < len(Ls) else TOTAL - .3
        b = min(L['e'] + HOLD + 0.5, nxt)
        kt = [f"{{\\k{int((ws[0]['s'] - a) * 100)}}}"]
        for j, x in enumerate(ws):
            end = ws[j + 1]['s'] if j + 1 < len(ws) else x['e']
            kt.append(f"{{\\kf{max(int((end - x['s']) * 100), 1)}}}{x['w']} ")
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Line,,0,0,0,,{{\\fad(120,200)\\move(960,1052,960,1038,0,180)}}" + ''.join(kt).strip())
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Name,,0,0,0,,{{\\fad(120,200)\\pos(960,972)\\fscx90\\fscy90\\t(0,140,\\fscx100\\fscy100)}}{names.get(L['id'], names[L['who']])}")
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
    out = f'{HERE}/voiceclone-nosfx.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
