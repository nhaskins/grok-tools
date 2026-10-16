"""Dialogue short #18: "HAILING LOOP" - Titan hails the Enterprise-D; Riker and Picard acknowledge each other's acknowledgments
until the HAILS counter explodes and the hail log buries the bridge. Grok Bot adds a dedupe rule; one echo "...out" still slips
through and gets stamped IGNORED. xAI voices (Riker = Nate's own voice, no pitch shift).
    python hailingloop.py | --frames t ... | --poster"""
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
T_H1 = wt('r1', 'hail', 0, -.05)                                   # first hail goes out
T_H2 = LN['p1']['s']; T_H4 = wt('p1', 'our', 0, -.05)
T_H16 = wt('r2', 'acknowledged', 0, -.05); T_H128 = wt('r2', 'acknowledgment', 0, -.05)
T_BLUR = wt('r2', 'acknowledge', 0, -.05)                            # arrows blur into a loop
T_LOG = T_BLUR                                                       # log paper starts spilling
T_DD = wt('g1', 'rule:', 0, -.05) if any(x['w'] == 'rule:' for x in LN['g1']['words']) else wt('g1', 'adding', 0, .3)
T_ECHO = LN['p2']['e'] + .25; T_IGN = T_ECHO + .55; T_SHRUG = T_IGN + .35
CUT_P1 = LN['p1']['s'] - .15; CUT_R2 = LN['r2']['s'] - .15; CUT_S1 = LN['s1']['s'] - .15; CUT_G1 = LN['g1']['s'] - .15
CUT_P2 = LN['p2']['s'] - .15; CUT_END = T_ECHO - .1
def hails(t):
    if t < T_H1: return 0
    if t < T_H2: return 1
    if t < T_H4: return 2
    if t < T_H16: return 4
    if t < T_H128: return 16
    if t < T_DD: return min(9998, int(128 * 2 ** ((t - T_H128) * 2.2)))
    return 10000
def hail_str(n): return '9999+' if n >= 10000 else str(n)
STEPS = [T_H1, T_H2, T_H4, T_H16, T_H128]

KEYS = dict(
    grokbot=[(0, 'idle+look_r', 0), (LN['g1']['s'] - .05, 'point', .25), (T_DD, 'proud', .2), (LN['g1']['e'] + .3, 'idle+look_r', .3),
             (T_IGN - .15, 'point', .2), (T_IGN + .5, 'thumbs', .25)],
    riker=[(0, 'straddle+look_l', 0), (LN['r1']['s'] - .05, 'straddle+rsh=80+rel=10', .25), (LN['r1']['e'] + .2, 'straddle+look_l', .3),
           (LN['r2']['s'] - .05, 'straddle+rsh=20+rel=150+tilt=12+mouth=2', .2), (T_H16, 'straddle+rsh=80+rel=10+mouth=1', .2),
           (LN['r2']['e'] + .3, 'straddle+chinrub', .3), (LN['s1']['s'] + .2, 'straddle+look_r', .3), (LN['g1']['s'] + .2, 'straddle+look_l', .3),
           (T_SHRUG, 'straddle+lsh=48+lel=78+rsh=48+rel=78+tilt=10+mouth=1', .25)],
    redshirt=[(0, 'idle+look_l', 0), (T_LOG + .4, 'surprise', .2), (LN['s1']['s'] - .1, 'handear+look_l', .25), (LN['s1']['e'] + .3, 'idle+look_l', .3)],
    picard=[(0, 'front+rsh=40+rel=110+tilt=4', 0), (LN['p1']['s'] - .1, 'front+lsh=30+lel=-70+rsh=30+rel=-70', .3),
            (wt('p1', 'our', 0, -.1), 'front+lsh=20+lel=10+rsh=60+rel=80', .25), (LN['p1']['e'] + .3, 'front+rsh=40+rel=110+tilt=4', .3),
            (LN['r2']['s'] + .4, 'front+lsh=40+lel=-95+rsh=40+rel=-95', .3),
            (LN['p2']['s'] - .1, 'front+rsh=100+rel=128+tilt=14', .3), (wt('p2', 'picard', 0, -.1), 'front+rsh=40+rel=110+tilt=4', .3)],
)
NODS = dict(riker=[LN['r1']['s'] + .05, LN['r2']['s'] + .05], picard=[LN['p1']['s'] + .05, wt('p2', 'out', 0, .02)],
            redshirt=[LN['s1']['s'] + .05], grokbot=[LN['g1']['s'] + .05])

VC = (920, 285)
SHOTS = [
    (0.0, [(0.0, (960, 520, 1.0), 0), (0.0, (975, 515, 1.05), LN['r1']['e'])]),
    (CUT_P1, [(CUT_P1, (920, 320, 1.5), 0), (CUT_P1, (920, 310, 1.56), LN['p1']['e'] - CUT_P1)]),    # into the link
    (CUT_R2, [(CUT_R2, (960, 520, 1.0), 0)]),
    (CUT_S1, [(CUT_S1, (1440, 640, 1.45), 0), (CUT_S1, (1440, 650, 1.5), LN['s1']['e'] - CUT_S1)]),  # the log pile
    (CUT_G1, [(CUT_G1, (960, 520, 1.0), 0)]),
    (CUT_P2, [(CUT_P2, (920, 320, 1.5), 0)]),
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

GROK = fig('grokbot', 330, STAND, 1, ['robot'], scale=SC)
RIKER = fig('riker', 980, SEATY, -1, ['beard', 'badge'], scale=SC)
RS = fig('redshirt', 1850, STAND, -1, ['redshirt', 'ponytail'], scale=SC)
PIC = fig('picard', 640, 430, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=1.25)
RCHAIR = 980

def chair(pen, cx, s, m, sid):
    """swivel chair (demo16); m = -1: back on the left, Riker sits backwards"""
    sy = FLOOR - 52 * s
    pen.line([(cx - 52 * s * m, sy), (cx + 40 * s * m, sy)], 6 * s ** .5, INK, sid + 'seat')
    back = [(cx + 34 * s * m, sy), (cx + 40 * s * m, FLOOR - 152 * s), (cx + 56 * s * m, FLOOR - 152 * s), (cx + 50 * s * m, sy)]
    pen.fill(back, PAPER); pen.line(back, 5 * s ** .5, INK, sid + 'back', closed=True)
    pen.line([(cx - 6 * s * m, sy), (cx - 6 * s * m, FLOOR)], 6 * s ** .5, INK, sid + 'ped')
    pen.line([(cx - 44 * s, FLOOR), (cx + 32 * s, FLOOR)], 6 * s ** .5, INK, sid + 'base')

# ------------------------------------------------------------------ the link diagram (right half of the viewscreen)
VS = (480, 100, 1360, 470)
TI, EN = (1000, 300), (1250, 300)          # ship icons
def icon(sp, c, label, sid, saucer_first=True):
    x, y = c
    sp.arc((x, y - 12), 34, 11, 0, 360, 3, PAPER, sid + 'sau')
    sp.line([(x + 4, y - 4), (x + 14, y + 10)], 3, PAPER, sid + 'nk')
    sp.line([(x - 6, y + 10), (x + 30, y + 10), (x + 30, y + 18), (x - 6, y + 18)], 3, PAPER, sid + 'hul', closed=True)
    for dy in (-2, 26): sp.line([(x + 20, y + dy), (x + 50, y + dy)], 4, PAPER, sid + f'nc{dy}')
    sp.text(label, (x + 12, y + 58), 19, PAPER, 'marker')
def arrow(sp, a, b, sid, w=3, head=14):
    sp.line([a, b], w, PAPER, sid)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s_ in (-1, 1): sp.line([b, (b[0] - head * math.cos(ang + s_ * .5), b[1] - head * math.sin(ang + s_ * .5))], w, PAPER, sid + f'h{s_}')
def link(sp, t):
    icon(sp, TI, 'TITAN', 'ti'); icon(sp, EN, 'ENTERPRISE-D', 'en')
    sp.text('SUBSPACE LINK', ((TI[0] + EN[0]) / 2 + 20, 140), 24, PAPER, 'marker')
    ax0, ax1, yu, yd = TI[0] + 62, EN[0] - 44, 262, 330
    if T_H1 <= t < T_BLUR:
        arrow(sp, (ax0, yu), (ax1, yu), 'au'); arrow(sp, (ax1, yd), (ax0, yd), 'ad')
        # a ping-pong blip bouncing between the ships, faster after each step
        rate = 1.0 if t < T_H2 else 2.0 if t < T_H4 else 3.5 if t < T_H16 else 6
        ph = ((t - T_H1) * rate) % 2
        if ph < 1: p = (lerp(ax0, ax1, ph), yu)
        else: p = (lerp(ax1, ax0, ph - 1), yd)
        sp.circle(p, 9, 0, fill=PAPER)
        last = max(c for c in STEPS if c <= t)
        if t - last < .4: sparkle(sp, p, 16, PAPER, f'pp{int(t * 24)}')
    elif T_BLUR <= t < T_DD:
        # arrows blur into a spinning loop doodle
        cx, cy = (ax0 + ax1) / 2, (yu + yd) / 2; sp_ = 9 * (t - T_BLUR) + 3 * (t - T_BLUR) ** 2
        for j in range(4):
            a0 = (sp_ * 60 + j * 90) % 360
            sp.arc((cx, cy), 92 - 6 * j, 34 - 3 * j, a0, a0 + 230, 3, PAPER, f'loop{j}')
            a1 = math.radians(a0 + 230); hp = (cx + (92 - 6 * j) * math.cos(a1), cy + (34 - 3 * j) * math.sin(a1))
            sp.circle(hp, 5, 0, fill=PAPER)
        for j in range(3): sp.line([(cx - 120 + 30 * j, cy - 55 - 4 * j), (cx - 90 + 30 * j, cy - 62 - 4 * j)], 2, PAPER, f'sl{j}')
    elif t >= T_DD:
        arrow(sp, (ax0, yu), (ax1, yu), 'au')
        SETS.stamp(sp, 'DEDUPE', ((ax0 + ax1) / 2 + 10, 380), t, T_DD, 52, sid='dd')
        if t >= T_ECHO:     # tiny echo bubble from the Titan still says "...out"
            k = ease_out_back(clamp01((t - T_ECHO) / .25)); bx, by = TI[0] + 10, 205
            sp.circle((bx, by), 34 * k + 1, 3, PAPER, 'eb', fill=INK)
            sp.line([(bx + 10, by + 30 * k), (TI[0] - 4, TI[1] - 26)], 3, PAPER, 'ebt')
            sp.text('...out', (bx, by + 2), 20 * k + 1, PAPER, 'hand')
            if t >= T_IGN: SETS.stamp(sp, 'IGNORED', (bx + 120, by + 5), t, T_IGN, 32, sid='ig')

def viewscreen(img, pen, t, cam, boil):
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    stars_field(sp, VS, t, .02, n=50, seed=4)
    sp.line([(925, y0 + 10), (925, y1 - 10)], 2, PAPER, 'split')
    PIC.draw(sp, t, 0, w=4.5)
    sp.rect(500, 420, 900, 520, 5, PAPER, 'desk', fill=INK)
    sp.text('ADM. PICARD // U.S.S. ENTERPRISE', (700, 446), 22, PAPER, 'marker')
    sp.rect(840, 385, 872, 420, 3, PAPER, 'cup'); sp.arc((876, 402), 9, 9, -90, 90, 3, PAPER, 'hdl')
    for j in range(2): sp.line([(848 + 12 * j, 378), (844 + 12 * j + 4 * math.sin(t * 6 + j), 354)], 2, PAPER, f'stm{j}')
    link(sp, t)
    clip_paste(img, sub, pen, VS)

def counter(pen, t):
    n = hails(t)
    if not n: return
    x, y = 1600, 250
    k = ease_out_back(clamp01((t - T_H1) / .25))
    last = max([c for c in STEPS + [T_DD] if c <= t]); sq = 1 + .25 * max(0, 1 - (t - last) / .25)
    jx = 5 * math.sin(t * 50) if T_H128 <= t < T_DD else 0
    pen.rect(x - 200 * k + jx, y - 62 * k, x + 200 * k + jx, y + 62 * k, 5, INK, 'cnt', fill=PAPER)
    pen.text(f'HAILS: {hail_str(n)}', (x + jx, y + 4), 56 * k * sq, INK, 'marker')
    if t >= T_DD:
        pen.text('(frozen)', (x, y + 92), 28, INK, 'hand')
        if t - T_DD < .7: SETS.burst(pen, (x, y), t, T_DD, 240, 12, INK, 'cbdd', .6, 3)
    elif t - last < .5 and last > T_H1: SETS.outlined(pen, '!', (x + 230, y - 40), 70, 5)

# ------------------------------------------------------------------ hail log: paper spills off the console and piles up
CON = (1380, FLOOR - 120, 1560, FLOOR)
def log_amount(t):
    if t < T_LOG: return 0.0
    u = min(t, T_DD) - T_LOG
    return min(1.0, .12 * u + .07 * u * u)
def hail_log(pen, t):
    x0, y0, x1, y1 = CON
    pen.rect(x0, y0, x1, y1, 5, INK, 'con', fill=PAPER)
    pen.rect(x0 + 20, y0 + 18, x1 - 20, y0 + 50, 3, INK, 'conscr')
    pen.text('HAIL LOG', ((x0 + x1) / 2, y0 + 34), 18, INK, 'marker')
    for j in range(4): pen.circle((x0 + 40 + 34 * j, y0 + 80), 7, 3, INK, f'cb{j}')
    a = log_amount(t)
    if a <= 0: return
    # slot on top, a strip curling up and over the console
    sx = x0 + 120; top = y0 - 30 - 120 * a
    strip = [(sx, y0), (sx + 4 * math.sin(t * 9), (y0 + top) / 2), (sx + 40, top), (x1 + 30, top + 20), (x1 + 60, FLOOR - 40 - 160 * a)]
    pen.line(strip, 4, INK, 'strip'); pen.line([(p[0] + 26, p[1]) for p in strip], 4, INK, 'strip2')
    # the pile: zig-zag folds stacking up on the floor to the right
    nf = int(2 + 12 * a); hp = 9 * (1 + 1.0 * a)
    for i in range(nf):
        y = FLOOR - 6 - i * hp; w = 170 + 90 * a - 5 * i + 10 * math.sin(i * 1.7)
        cx = x1 + 110 + 8 * math.sin(i * 2.3)
        pts = [(cx - w / 2, y), (cx + w / 2, y - hp * .5), (cx - w / 2 + 6, y - hp)]
        pen.line(pts, 3.5, INK, f'fold{i}')
        if i % 2 == 0: pen.text('HAIL ACK', (cx, y - hp * .35), 12, INK, 'hand')
    if a > .3:      # sheets spilling across the floor
        for j in range(int(5 * a)):
            px = x0 - 40 - 70 * j; SETS.paper_sheet(pen, (px, FLOOR - 10), 8 * math.sin(j * 1.9), .45, f'ps{j}')

def bridge(t, cam):
    boil = int(t * 12)
    img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    pen.line([(-600, 60), (400, 60), (460, 92)], 4, INK, 'rail1'); pen.line([(1380, 92), (1440, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (1640, 120), 40, INK, 'marker')
    viewscreen(img, pen, t, cam, boil)
    counter(pen, t)
    hail_log(pen, t)
    h = {}; w = 5.5 * SC ** .3
    h['grokbot'] = GROK.draw(pen, t, 0, w=w)
    chair(pen, RCHAIR, SC, -1.0, 'rch')       # Riker sits backwards
    h['riker'] = RIKER.draw(pen, t, 0, w=w)
    h['redshirt'] = RS.draw(pen, t, 0, w=w)
    if LN['s1']['s'] <= t < LN['s1']['e'] + .2: SETS.outlined(pen, '(whisper)', (1850, 330), 32, 3, 'hand')
    if T_SHRUG + .1 <= t: SETS.outlined(pen, '*shrug*', (RCHAIR + 40, SEATY - 250), 36, 4, 'hand')
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
    """key art: the spinning hail loop, HAILS climbing, log paper piling up; title band"""
    a, _ = bridge(T_DD - .35, (960, 470, 1.0))
    img = a.copy(); pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(500, 930, 1420, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'HAILING LOOP', (960, 972), 108, 7)
    pen.line([(600, 1026), (1320, 1021)], 5, INK, 'tul')
    pen.text('Riker \u00d7 Picard \u00d7 Red Shirt \u00d7 Grok Bot  \u00b7  STARSHIP GROKBOT', (960, 1052), 30, INK, 'hand')
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
    out = f'{HERE}/hailingloop-nosfx.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
