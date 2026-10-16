"""Dialogue short #19: "WARP NINE RENDER" - the Titan renders video at 757% CPU ("warp nine"), memory runs out (no swap),
blip + shake + blackout, systems reboot, and the crew does the classic fake-turbulence lean while nothing shakes.
Picard: "It's a video render. Sit down." CPU drops to a calm nice -n 10. xAI voices (Riker = Nate's own voice, no pitch shift).
    python warpnine.py | --frames t ... | --poster"""
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
T_CLIMB = wt('r1', 'how', 0, -.05); T_757 = wt('b1', 'seven', 0, -.05); T_W9 = wt('b1', 'warp', 0, -.05)
T_MEM = wt('g1', 'memory', 0, -.05); T_SWAP = wt('g1', 'there', 0, -.05)
T_BLIP = LN['g1']['e'] + .3; T_BLK = T_BLIP + .55; T_REB = T_BLK + .8; T_ON = T_REB + 1.0
T_LL = wt('r2', 'lean', 0, -.05)
LEANSEQ = [(T_LL, 0), (T_LL + .3, -1), (T_LL + .85, -1), (T_LL + 1.25, 1), (T_LL + 1.8, 1), (T_LL + 2.1, -.5), (T_LL + 2.2, -.5), (T_LL + 2.42, 0)]
T_SIT = wt('p1', 'sit', 0, -.05); T_NICE = T_SIT + .35
CUT_B1 = LN['b1']['s'] - .15; CUT_G1 = LN['g1']['s'] - .15; CUT_WIDE = T_BLIP - .05; CUT_P1 = LN['p1']['s'] - .15; CUT_END = T_SIT - .2
def seq(t, S):
    if t <= S[0][0]: return S[0][1]
    for (a, va), (b, vb) in zip(S, S[1:]):
        if t < b: return lerp(va, vb, ease((t - a) / (b - a)))
    return S[-1][1]
def lean_amt(t): return seq(t, LEANSEQ)           # -1 = whole crew leans screen-left
def cpu(t):
    if t < T_CLIMB: return 118
    if t < T_757: return lerp(118, 420, ease(clamp01((t - T_CLIMB) / (T_757 - T_CLIMB))))
    if t < T_BLK: return 757 + 60 * math.exp(-6 * (t - T_757)) * math.sin(30 * (t - T_757))   # slam + overshoot wobble
    if t < T_REB: return 0
    if t < T_NICE: return lerp(0, 757, ease(clamp01((t - T_REB) / 1.2))) + 6 * math.sin(t * 40)
    return lerp(757, 100, ease_out(clamp01((t - T_NICE) / .6)))
def warp(t):
    if t < T_CLIMB: return 1
    if t < T_W9: return lerp(1, 6, ease(clamp01((t - T_CLIMB) / (T_W9 - T_CLIMB))))
    if t < T_BLK: return 9 + .15 * math.sin(t * 50)
    if t < T_REB: return 0
    if t < T_NICE: return lerp(0, 9, ease(clamp01((t - T_REB) / 1.2)))
    return lerp(9, 1, ease_out(clamp01((t - T_NICE) / .6)))
def mem(t):
    if t < T_757: return .42
    if t < T_MEM: return lerp(.42, .9, ease(clamp01((t - T_757) / (T_MEM - T_757))))
    if t < T_BLK: return .9 + .09 * clamp01((t - T_SWAP) / (T_BLIP - T_SWAP))
    if t < T_REB: return 0
    return lerp(.0, .45, ease(clamp01((t - T_REB) / 1.0)))

FACE = dict(grokbot=1, barclay=1, riker=-1, redshirt=-1, picard=1)
KEYS = dict(
    grokbot=[(0, 'idle+look_r', 0), (LN['g1']['s'] - .05, 'point', .25), (T_SWAP, 'nervous', .2), (T_REB + .3, 'idle+look_r', .3),
             (LN['p1']['s'] + .2, 'idle', .3), (T_NICE + .1, 'thumbs', .25)],
    barclay=[(0, 'hunch', 0), (LN['b1']['s'] - .05, 'present_padd', .2), (T_W9, 'cheer', .15), (LN['b1']['e'] + .3, 'hunch', .3),
             (T_SWAP, 'nervous', .2), (T_REB + .4, 'surprise', .2), (LN['s1']['e'], 'hunch', .3), (CUT_P1 + .3, 'nervous', .3)],
    riker=[(0, 'look_l', 0), (LN['r1']['s'] - .05, 'palm', .25), (LN['r1']['e'] + .2, 'look_l', .3), (T_W9, 'smile+look_l', .2),
           (T_SWAP, 'think', .3), (T_REB + .4, 'surprise', .2), (LN['s1']['e'] - .5, 'look_r', .3),
           (LN['r2']['s'] - .05, 'tada', .25), (T_LL - .2, 'idle+look_l', .3), (CUT_P1 + .2, 'look_l', .3)],
    redshirt=[(0, 'idle+look_l', 0), (T_757 + .2, 'surprise', .2), (LN['b1']['e'] + .3, 'idle+look_l', .3), (T_REB + .4, 'cheer', .2),
              (LN['s1']['e'] + .2, 'idle+look_l', .3)],
    picard=[(0, 'front', 0), (LN['p1']['s'] - .1, 'facepalm', .25), (wt('p1', "it's", 0, -.1), 'front+lsh=40+lel=-95+rsh=40+rel=-95', .3),
            (T_SIT - .1, 'point', .2)],
)
NODS = dict(riker=[LN['r1']['s'] + .05, LN['r2']['s'] + .05], picard=[wt('p1', 'sit', 0, .02)], barclay=[LN['b1']['s'] + .05],
            redshirt=[LN['s1']['s'] + .05], grokbot=[LN['g1']['s'] + .05])

SHOTS = [
    (0.0, [(0.0, (960, 520, 1.0), 0), (0.0, (975, 515, 1.05), LN['r1']['e'])]),
    (CUT_B1, [(CUT_B1, (1200, 420, 1.28), 0), (CUT_B1, (1200, 410, 1.34), LN['b1']['e'] - CUT_B1)]),   # Barclay + gauges
    (CUT_G1, [(CUT_G1, (620, 560, 1.45), 0), (CUT_G1, (620, 560, 1.52), LN['g1']['e'] - CUT_G1)]),    # Grok Bot sweats
    (CUT_WIDE, [(CUT_WIDE, (960, 520, 1.0), 0)]),
    (CUT_P1, [(CUT_P1, (920, 320, 1.5), 0)]),
    (CUT_END, [(CUT_END, (960, 520, 1.0), 0)]),
]
SHOTS = [dict(at=a, set='bridge', cam=c) for a, c in SHOTS]
for i, s in enumerate(SHOTS): s['end'] = SHOTS[i + 1]['at'] if i + 1 < len(SHOTS) else 1e9

def make_mod(who):
    env = ENV.get(who, np.zeros(1)); nods = NODS.get(who, []); fc = FACE[who]
    def f(t, P):
        i = int(t * FPS); e = float(env[i]) if i < len(env) else 0.0
        e2 = float(env[max(i - 2, 0)]) if i < len(env) else 0.0
        P['talk'] = e; P['tilt'] += 7 * (e - e2) + 3 * e; P['lean'] += 2.5 * e * (1 - P['front'])
        if who != 'picard': L = lean_amt(t); P['lean'] += 30 * L * fc * (1 - P['front']) * LEANSIGN; P['tilt'] += 10 * L * fc * LEANSIGN
        for tn in nods:
            u = t - tn
            if 0 <= u < .7: P['tilt'] += 12 * math.sin(math.pi * u / .35) * (1 - u / .7)
        return P
    return f
LEANSIGN = -1

def fig(who, x, y, facing, props, **kw):
    F = Figure(who, x, y, facing, set(props), **kw)
    for k in KEYS[who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    F.mod = make_mod(who); return F

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

GROK = fig('grokbot', 300, STAND, 1, ['robot'], scale=SC)
BARC = fig('barclay', 620, STAND, 1, ['curly', 'badge'], scale=SC)
RIKER = fig('riker', 1130, STAND, -1, ['beard', 'badge'], scale=SC)
RCHAIR = 960
KEYS['riker_sit'] = [(0, 'straddle+look_l', 0), (T_SIT + .5, 'straddle+smile+look_l', .3)]; FACE['riker_sit'] = -1
RSIT = Figure('riker', RCHAIR, SEATY, -1, {'beard', 'badge'}, scale=SC)
for k in KEYS['riker_sit']: RSIT.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
RSIT.mod = make_mod('riker')
RS = fig('redshirt', 1850, STAND, -1, ['redshirt', 'ponytail'], scale=SC)
PIC = fig('picard', 640, 430, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=1.25)

def chair(pen, cx, s, m, sid):
    """swivel chair (demo16); m = -1: back on the left, Riker sits backwards"""
    sy = FLOOR - 52 * s
    pen.line([(cx - 52 * s * m, sy), (cx + 40 * s * m, sy)], 6 * s ** .5, INK, sid + 'seat')
    back = [(cx + 34 * s * m, sy), (cx + 40 * s * m, FLOOR - 152 * s), (cx + 56 * s * m, FLOOR - 152 * s), (cx + 50 * s * m, sy)]
    pen.fill(back, PAPER); pen.line(back, 5 * s ** .5, INK, sid + 'back', closed=True)
    pen.line([(cx - 6 * s * m, sy), (cx - 6 * s * m, FLOOR)], 6 * s ** .5, INK, sid + 'ped')
    pen.line([(cx - 44 * s, FLOOR), (cx + 32 * s, FLOOR)], 6 * s ** .5, INK, sid + 'base')

VS = (480, 100, 1360, 470)
def viewscreen(img, pen, t, cam, boil):
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    w9 = warp(t) / 9
    if t >= CUT_P1:
        stars_field(sp, VS, t, .02, n=50, seed=4)
        PIC.draw(sp, t, 0, w=4.5)
        sp.rect(500, 420, 900, 520, 5, PAPER, 'desk', fill=INK)
        sp.text('ADM. PICARD // U.S.S. ENTERPRISE', (700, 446), 22, PAPER, 'marker')
        sp.rect(840, 385, 872, 420, 3, PAPER, 'cup'); sp.arc((876, 402), 9, 9, -90, 90, 3, PAPER, 'hdl')
        sp.text('RENDER: 100%', (1160, 160), 24, PAPER, 'marker')
    else:
        stars_field(sp, VS, t, .02 + .3 * w9, n=60, seed=4)
        if w9 > .3:     # speed lines streaking out from the centre
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; rng = np.random.default_rng(int(t * 24) % 7)
            for j in range(26):
                a = j / 26 * 2 * math.pi + rng.random() * .1; r0 = 40 + 280 * ((t * 2.5 * w9 + j * .37) % 1)
                L = 40 + 120 * w9
                sp.line([(cx + r0 * math.cos(a), cy + r0 * .5 * math.sin(a)), (cx + (r0 + L) * math.cos(a), cy + (r0 + L) * .5 * math.sin(a))],
                        3, PAPER, f'sl{j}')
    clip_paste(img, sub, pen, VS)

def dial(pen, c, R, frac, label, val, sid):
    x, y = c
    pen.arc((x, y), R, R, 180, 360, 5, INK, sid + 'a')
    pen.line([(x - R, y), (x + R, y)], 4, INK, sid + 'b')
    for k in range(9):
        a = math.pi + k / 8 * math.pi
        pen.line([(x + R * .82 * math.cos(a), y + R * .82 * math.sin(a)), (x + R * math.cos(a), y + R * math.sin(a))], 3, INK, sid + f't{k}')
    a = math.pi + clamp01(frac) * math.pi
    pen.line([(x, y), (x + R * .78 * math.cos(a), y + R * .78 * math.sin(a))], 6, INK, sid + 'n')
    pen.circle((x, y), 8, 0, fill=INK)
    pen.text(label, (x, y + 34), 24, INK, 'marker'); pen.text(val, (x, y + 70), 36, INK, 'marker')

def gauges(pen, t):
    c = cpu(t); w = warp(t)
    calm = t >= T_NICE
    dial(pen, (1540, 250), 100, c / 800, 'CPU', f'{int(round(c))}%' if not calm else '100%', 'cpu')
    dial(pen, (1780, 250), 80, w / 9.5, 'WARP FACTOR', '9' if w >= 8.7 else f'{w:.1f}', 'wf')
    if T_757 <= t < T_BLK and t - T_757 < .6: SETS.burst(pen, (1540, 220), t, T_757, 150, 12, INK, 'cb', .6, 3)
    if calm:
        k = ease_out_back(clamp01((t - T_NICE) / .3))
        if k > .05:
            pen.rect(1540 - 120 * k, 380 - 28 * k, 1540 + 120 * k, 380 + 28 * k, 4, INK, 'nicebox', fill=PAPER)
            pen.text('nice -n 10', (1540, 384), 34 * k, INK, 'hand')
    # MEM bar
    m = mem(t); x0, x1, y = 1450, 1860, 430
    if not calm:
        pen.rect(x0, y - 18, x1, y + 18, 4, INK, 'memf', fill=PAPER)
        if m > .01:
            pen.rect(x0 + 4, y - 14, x0 + 4 + (x1 - x0 - 8) * m, y + 14, 0, fill=INK)
        pen.text('MEM', (x0 - 50, y + 4), 28, INK, 'marker')
        if m > .85 and int(t * 6) % 2 == 0: SETS.outlined(pen, 'NO SWAP!', (x1 - 120, y - 46), 34, 4)

def sweat(pen, gb, t, ts):
    u = t - ts
    if not (0 <= u < 1.6): return
    hx, hy = gb['head']; R = gb['R']
    x, y = hx + R * 1.45, hy - R * .9 + R * 1.1 * ease(clamp01((u - .25) / 1.1))
    k = ease_out_back(clamp01(u / .2))
    pts = [(x + 10 * k * math.sin(a) * (1 - math.cos(a)) * .6, y + 16 * k * (-math.cos(a))) for a in np.linspace(0, 2 * math.pi, 24)]
    pen.fill(pts, PAPER); pen.line(pts, 3.5, INK, 'sweat', closed=True)

def bridge(t, cam):
    boil = int(t * 12)
    img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    pen.line([(-600, 60), (400, 60), (460, 92)], 4, INK, 'rail1'); pen.line([(1380, 92), (1440, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (240, 130), 40, INK, 'marker')
    viewscreen(img, pen, t, cam, boil)
    gauges(pen, t)
    h = {}; w = 5.5 * SC ** .3
    h['grokbot'] = GROK.draw(pen, t, 0, w=w)
    sweat(pen, h['grokbot'], t, T_SWAP); sweat(pen, h['grokbot'], t, T_SWAP + 1.2)
    h['barclay'] = BARC.draw(pen, t, 0, w=w)
    chair(pen, RCHAIR, SC, -1.0, 'rch')
    if t < T_SIT: h['riker'] = RIKER.draw(pen, t, 0, w=w)
    else:
        h['riker'] = RSIT.draw(pen, t, 0, w=w)
        if t - T_SIT < .5: SETS.burst(pen, (RCHAIR, SEATY - 80), t, T_SIT, 160, 10, INK, 'sitb', .5, 3)
        if t > T_SIT + .4: SETS.outlined(pen, '*backwards*', (RCHAIR, SEATY - 270), 34, 4, 'hand')
    h['redshirt'] = RS.draw(pen, t, 0, w=w)
    L = lean_amt(t)
    if abs(L) > .3 and T_LL < t < LEANSEQ[-1][0]: SETS.outlined(pen, '*lean*', (960, 600), 40, 4, 'hand')
    return img, h
SETFN = {'bridge': bridge}
DARK = 0.1
def flash(img, t):
    if T_BLIP <= t < T_BLIP + .12:                         # the light blip
        return np.clip(img.astype(np.float32) * .35 + 255 * .65, 0, 255).astype(np.uint8)
    if T_BLK <= t < T_REB: return np.zeros_like(img)        # full black
    if T_REB <= t < T_ON + .6:                               # lights come back one bank at a time, flickering
        f = np.full(W, DARK, np.float32)
        for k in range(4):
            tk = T_REB + .05 + .22 * k
            on = t >= tk and not (tk + .06 < t < tk + .12)
            if on: f[k * 480:(k + 1) * 480] = 1.0
        out = (img.astype(np.float32) * f[None, :, None]).astype(np.uint8)
        pen = Pen(out, (960, 540, 1.0), int(t * 12))
        if t < T_ON: SETS.outlined(pen, 'REBOOTING...', (960, 560), 96, 6)
        else: SETS.stamp(pen, 'ONLINE', (960, 560), t, T_ON, 110, 6, 'on')
        return out
    return img
def cam_fx(img, t):
    """screen shake before the blackout; camera tilt while the crew fakes turbulence (nothing is actually shaking)"""
    dx = dy = ang = 0.0
    if T_BLIP <= t < T_BLK: u = (t - T_BLIP) / (T_BLK - T_BLIP); dx = 28 * math.sin(t * 90) * (1 - u * .3); dy = 18 * math.sin(t * 71 + 1)
    if T_LL <= t < LEANSEQ[-1][0]: ang = -4.0 * lean_amt(t)
    if not (dx or dy or ang): return img
    M = cv2.getRotationMatrix2D((W / 2, H / 2), ang, 1.0 + abs(ang) * .02); M[0, 2] += dx; M[1, 2] += dy
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
    """key art: CPU slammed to 757%, warp nine, speed lines, MEM red; title band"""
    a, _ = bridge(T_MEM + .4, (960, 470, 1.0))
    img = a.copy(); pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(500, 930, 1420, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'WARP NINE RENDER', (960, 972), 108, 7)
    pen.line([(600, 1026), (1320, 1021)], 5, INK, 'tul')
    pen.text('Riker \u00d7 Barclay \u00d7 Picard \u00d7 Red Shirt \u00d7 Grok Bot  \u00b7  STARSHIP GROKBOT', (960, 1052), 30, INK, 'hand')
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'picard': 'PICARD', 'barclay': 'BARCLAY', 'redshirt': 'RED SHIRT'}; ev = []; Ls = TL['lines']
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
    out = f'{HERE}/warpnine-nosfx.mp4'
    subprocess.run(['nice', '-n', '10', 'ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p', '-threads', '4',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
