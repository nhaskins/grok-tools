"""Dialogue short #4: "THE RED SHIRTS" - an eager Red Shirt bot reports its leads; context is at 95%;
Grok Bot hits DELETE & RECREATE; a fresh Red Shirt beams in. (True story: Nathan's Red Shirt bots get
recreated to wipe their context and save tokens.)  python redshirts.py | --frames t ... | --poster"""
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
T_PRESS = w('g1', 'tokens', -.02)              # Grok Bot slaps the button
T_OUT0, T_OUT1 = T_PRESS + .15, T_PRESS + .6  # Red Shirt #46 beams out (waving)
T_IN0 = T_PRESS + .78; T_IN1 = min(T_IN0 + .5, LN['s3']['s'] - .05)   # #47 beams in
T_GEN = T_PRESS + .55                          # generation counter flips
CUT_R = LN['r1']['s'] - .15; CUT_S2 = LN['s2']['s'] - .15; CUT_G = LN['g1']['s'] - .15; CUT_S3 = T_IN0 - .08; CUT_R2 = LN['r2']['s'] - .15
KEYS = dict(
    redshirt=[(0, 'idle', 0), (w('s1', 'commander', -.2), 'salute', .2), (w('s1', 'forty', -.2), 'cheer', .25), (w('s1', 'contracting', -.2), 'thumbs', .25),
              (LN['s1']['e'] + .2, 'idle+look_r', .3), (w('r1', 'outstanding', -.1), 'proud+look_r', .25), (w('r1', 'ninety-five', -.1), 'idle+look_r+mouth=1', .3),
              (w('s2', 'thank', -.15), 'salute+mouth=1', .2), (w('s2', 'wait', -.15), 'idle+lookup=-.9', .3), (w('s2', 'red', -.15), 'surprise', .2),
              (LN['g1']['s'] + .2, 'idle+look_r+tilt=10+lsh=35+lel=95+rsh=35+rel=95', .3), (T_PRESS + .05, 'wave+mouth=2', .15)],
    redshirt2=[(0, 'tada', 0), (w('s3', 'hi', -.1), 'wave', .15), (w('s3', 'new', -.1), 'front+mouth=2', .2), (w('s3', 'did', -.1), 'shrug', .2),
               (LN['s3']['e'] + .1, 'idle+look_r', .3), (w('r2', 'welcome', -.1), 'cheer', .2), (LN['r2']['e'] + .1, 'thumbs', .2)],
    riker=[(0, 'idle', 0), (w('s1', 'forty', .1), 'chinrub', .3), (w('r1', 'outstanding', -.2), 'thumbs', .25), (w('r1', 'context', -.15), 'idle+look_r', .3),
           (w('r1', 'ninety-five', -.1), 'palm', .25), (LN['r1']['e'] + .2, 'idle', .3), (LN['g1']['s'] + .1, 'idle+look_r', .3),
           (T_OUT1, 'chinrub', .3), (w('r2', 'absolutely', -.15), 'shrug', .25), (w('r2', 'welcome', -.15), 'thumbs', .25)],
    grokbot=[(0, 'idle', 0), (w('g1', 'nothing', -.15), 'palm', .2), (w('g1', 'saving', -.15), 'idle+rsh=75+rel=30', .2),
             (T_PRESS, 'idle+rsh=60+rel=20+lean=6', .06), (T_PRESS + .4, 'idle+rsh=66+rel=26', .2), (T_PRESS + .8, 'idle', .3),
             (LN['r2']['e'] + .15, 'thumbs', .2)],
)
NODS = dict(redshirt=[w('r1', 'work', .05)], redshirt2=[], riker=[w('s1', 'gigs', .1), w('r2', 'nothing', .1)], grokbot=[w('s3', 'anything', .1)])
SHOTS = [
    (0.0, 'bridge', [(0.0, (960, 520, 1.04), 0), (0.0, (900, 525, 1.12), CUT_R)]),
    (CUT_R, 'bridge', [(CUT_R, (1150, 520, 1.2), 0), (CUT_R, (1170, 520, 1.22), 3.5)]),
    (CUT_S2, 'bridge', [(CUT_S2, (640, 560, 1.6), 0), (w('s2', 'wait', -.2), (620, 545, 1.72), 1.2)]),
    (CUT_G, 'bridge', [(CUT_G, (1180, 520, 1.18), 0), (T_PRESS - .05, (980, 505, 1.08), .45)]),
    (CUT_S3, 'bridge', [(CUT_S3, (660, 540, 1.5), 0)]),
    (CUT_R2, 'bridge', [(CUT_R2, (960, 520, 1.06), 0), (CUT_R2, (960, 520, 1.1), 3)]),
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
        if who.startswith('redshirt'):          # eager bounce
            P['tilt'] += 2.0 * math.sin(t * 2 * math.pi * 2.3)
        return P
    return f

def fig(who, x, y, facing, props, **kw):
    F = Figure(who, x, y, facing, set(props), **kw)
    for k in KEYS[who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    F.mod = make_mod(who); return F

RS_X = 600
RS1 = fig('redshirt', RS_X, STAND, 1, ['redshirt'], scale=SC)
RS2 = fig('redshirt2', RS_X, STAND, 1, ['redshirt'], scale=SC)
RIKER = fig('riker', 1060, STAND, -1, ['beard', 'badge'], scale=SC)
GROK = fig('grokbot', 1530, STAND, -1, ['robot'], scale=SC)
BTN = (1415, 640)


# ------------------------------------------------------------------ helpers
def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

def sweat(pen, hd, R, t, t0, sid, side=1):
    u = t - t0
    if not 0 <= u < 1.4: return
    x, y = hd[0] + side * R * 1.4, hd[1] - R * .7 + R * 1.0 * ease(clamp01((u - .2) / 1.0)); k = ease_out_back(clamp01(u / .2))
    pts = [(x + 10 * k * math.sin(a) * (1 - math.cos(a)) * .6, y - 16 * k * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 24)]
    pen.fill(pts, PAPER); pen.line(pts, 3.5, INK, sid, closed=True)

def gen(t): return 47 if t >= T_GEN else 46

POSTER_LV = None
def ctx_level(t):
    if POSTER_LV is not None: return POSTER_LV
    """0..1 context fill: climbs while the bot works, 95% on 'ninety-five', drains on the wipe, starts again for #47"""
    if t < T_PRESS + .25:
        a = .35 + .45 * ease(clamp01(t / LN['s1']['e']))
        return a + (.95 - a) * ease(clamp01((t - w('r1', 'context', -.1)) / (w('r1', 'percent') - w('r1', 'context', -.1)))) if t > w('r1', 'context', -.1) else a
    if t < T_IN1: return .95 * (1 - ease(clamp01((t - T_PRESS - .25) / .45)))
    return .02 + .10 * clamp01((t - T_IN1) / 6)

def dissolve(img, fig_img, t, a, b, sid, out=True):
    """transporter shimmer: dither-dissolve the figure layer in/out"""
    u = clamp01((t - a) / (b - a)); keep = (1 - u) if out else u
    if keep >= 1: img[:] = fig_img; return
    if keep <= 0: return
    r = np.random.default_rng(int(t * 24) + 5)
    m = r.random((H // 3 + 1, W // 3 + 1)) < keep
    m = np.repeat(np.repeat(m, 3, 0), 3, 1)[:H, :W]
    img[m] = fig_img[m]


# ------------------------------------------------------------------ set: Titan bridge
VS = (610, 110, 1310, 470)
CARDS = [(LN['s1']['s'] + .1 + 2.6 * (j / 24) ** 1.3, j) for j in range(24)]
def screen(pen, img, t):
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vsframe')
    sub = np.full_like(img, INK); sp = Pen(sub, pen.cam, pen.boil)
    stars_field(sp, VS, t, 0.02, n=40)
    sp.text('MISSION: JOBS + CONTRACTING', (x0 + 30, y0 + 34), 30, PAPER, 'marker', anchor='l')
    for ta, j in CARDS:          # lead cards stack in, little briefcase / $ doodles
        if t < ta: continue
        k = ease_out_back(clamp01((t - ta) / .2)); c, r = j % 8, j // 8
        cx, cy = x0 + 70 + c * 80, y0 + 98 + r * 80 + 40 * (1 - k)
        sp.rect(cx - 32, cy - 33, cx + 32, cy + 33, 3, PAPER, f'cd{j}', fill=PAPER)
        if j % 3 == 2: sp.text('$', (cx, cy - 8), 34, INK, 'marker')
        else:
            sp.rect(cx - 15, cy - 18, cx + 15, cy + 2, 3, INK, f'bc{j}'); sp.line([(cx - 6, cy - 18), (cx - 6, cy - 24), (cx + 6, cy - 24), (cx + 6, cy - 18)], 3, INK, f'bh{j}')
        sp.line([(cx - 22, cy + 17), (cx + 22, cy + 17)], 2.5, INK, f'cl{j}', wob=.4)
    nl = int(40 * clamp01((t - LN['s1']['s']) / (w('s1', 'forty', .2) - LN['s1']['s'])))
    ng = int(12 * clamp01((t - w('s1', 'and')) / (w('s1', 'gigs', .2) - w('s1', 'and'))))
    sp.text(f'JOB LEADS: {nl}    GIGS: {ng}', (x0 + 30, y1 - 24), 30, PAPER, 'marker', anchor='l')
    if t > T_PRESS + .5: SETS.stamp(sp, 'SAVED TO FILE', ((x0 + x1) / 2, (y0 + y1) / 2), t, T_PRESS + .5, 44)
    clip_paste(img, sub, pen, VS)

def gauge(pen, t):
    gx0, gy0, gx1, gy1 = 1380, 120, 1840, 300
    pen.rect(gx0, gy0, gx1, gy1, 5, INK, 'gbox', fill=PAPER)
    pen.text('CONTEXT', (gx0 + 24, gy0 + 34), 34, INK, 'marker', anchor='l')
    lv = ctx_level(t)
    bx0, bx1, by0, by1 = gx0 + 24, gx1 - 24, gy0 + 64, gy0 + 112
    pen.rect(bx0, by0, bx1, by1, 4, INK, 'gbar')
    hot = lv > .85
    if lv > .005:
        pen.rect(bx0 + 4, by0 + 4, bx0 + 4 + (bx1 - bx0 - 8) * lv, by1 - 4, 0, fill=INK)
    for k in (.25, .5, .75): pen.line([(bx0 + (bx1 - bx0) * k, by1 + 2), (bx0 + (bx1 - bx0) * k, by1 + 12)], 3, INK, f'tk{k}')
    pen.text(f'{lv * 100:.0f}%', (gx1 - 70, gy0 + 34), 34, INK, 'marker')
    pen.text(f'{int(round(lv * 1000))}K TOKENS', ((gx0 + gx1) / 2, gy1 - 30), 32, INK, 'hand')
    if hot and int(t * 6) % 2 == 0:       # flashing warning ticks
        for s_ in (-1, 1): pen.text('!', ((gx0 + gx1) / 2 + s_ * 150, gy1 - 30), 38, INK, 'marker')

def gen_counter(pen, t):
    cx, cy = 330, 330
    pen.rect(cx - 210, cy - 46, cx + 210, cy + 46, 5, INK, 'genbox', fill=PAPER)
    u = clamp01((t - T_GEN) / .3); sq = abs(math.cos(math.pi * u)) if 0 < u < 1 else 1
    n = 46 if (t < T_GEN + .15) else 47
    pen.text(f'RED SHIRT #{n}', (cx, cy), 52 * max(sq, .08) + 1, INK, 'marker')
    if T_GEN < t < T_GEN + .8: SETS.burst(pen, (cx + 200, cy - 40), t, T_GEN + .15, 50, 10, INK, 'genb', .6, 3)

def button(pen, t):
    bx, by = BTN; press = 0.0
    if T_PRESS <= t < T_PRESS + .4: press = math.sin(math.pi * clamp01((t - T_PRESS) / .4))
    ped = [(bx - 40, by + 14), (bx + 40, by + 14), (bx + 62, FLOOR), (bx - 62, FLOOR)]
    pen.fill(ped, PAPER); pen.line(ped, 5, INK, 'ped', closed=True)
    pen.rect(bx - 52, by + 6, bx + 52, by + 18, 4, INK, 'rim', fill=PAPER)
    dome = [(bx + 40 * math.cos(a), by + 6 - (30 - 18 * press) * math.sin(a)) for a in np.linspace(0, math.pi, 18)]
    pen.fill(dome, INK); pen.line(dome, 4, INK, 'dome')
    pen.rect(bx - 115, 735, bx + 115, 835, 4, INK, 'bplate', fill=PAPER)
    pen.text('DELETE &', (bx, 765), 34, INK, 'marker'); pen.text('RECREATE', (bx, 806), 34, INK, 'marker')
    if T_PRESS <= t < T_PRESS + .6: SETS.burst(pen, (bx, by - 10), t, T_PRESS, 80, 12, INK, 'pressb', .5, 4)

def poof(pen, t, c):
    u = (t - T_OUT1 + .15) / .55
    if not 0 <= u < 1: return
    for j in range(7):
        a = j * 2 * math.pi / 7 + .4; d = 40 + 90 * ease_out(u); r = (26 + 20 * math.sin(j * 1.7)) * (1 - u * .7)
        pen.circle((c[0] + d * math.cos(a), c[1] + d * math.sin(a) * .8), r, 4, INK, f'pf{j}', fill=PAPER)

def beam(pen, t, a, b, c):
    """transporter sparkles rising/falling in a column over the figure"""
    if not a - .1 <= t < b + .25: return
    r = np.random.default_rng(int(t * 24) % 997)
    for j in range(9):
        y = c[1] - 260 + r.uniform(0, 380); x = c[0] + r.uniform(-60, 60)
        sparkle(pen, (x, y), r.uniform(8, 20), INK, f'bm{j}{int(t * 24)}')
    for s_ in (-1, 1):
        for d in range(6):
            y = c[1] - 230 + d * 66 + (t * 300 % 66) * (1 if a == T_IN0 else -1)
            pen.line([(c[0] + s_ * 75, y), (c[0] + s_ * 75, y + 30)], 3, INK, f'bcol{s_}{d}')

def bridge(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen); screen(pen, img, t)
    pen.line([(-600, 60), (520, 60), (580, 100)], 4, INK, 'rail1'); pen.line([(1340, 100), (1400, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (960, 58), 44, INK, 'marker')
    gauge(pen, t); gen_counter(pen, t)
    console(pen, 140, 330, 712, sid='ops', mirror=True)
    pen.rect(110, 650, 470, 700, 4, INK, 'plate', fill=PAPER)
    pen.text(f'ENS. RED SHIRT #{gen(t)} // JOBS', (290, 675), 23, INK, 'marker')
    button(pen, t)
    hands = {'riker': RIKER.draw(pen, t, 0, w=5.5 * SC ** .3), 'grokbot': GROK.draw(pen, t, 0, w=5.5 * SC ** .3)}
    # Red Shirt layer(s): drawn on a copy, then dissolved in/out
    wd = 5.5 * SC ** .3
    if t < T_OUT1:
        lay = img.copy(); hp = RS1.draw(Pen(lay, cam, boil), t, 0, w=wd); hands['redshirt'] = hp
        dissolve(img, lay, t, T_OUT0, T_OUT1, 'o', out=True)
        sweat(pen, hp['head'], hp['R'], t, w('s2', 'red', -.2), 'sw1', side=-1)
        sweat(pen, hp['head'], hp['R'], t, w('g1', 'nothing', -.1), 'sw2', side=-1)
        if w('s2', 'red', -.05) < t < LN['g1']['s'] + .3:   # ?! beside (not over) the head
            k = ease_out_back(clamp01((t - w('s2', 'red', -.05)) / .2))
            SETS.outlined(pen, '?!', (hp['head'][0] + 95, hp['head'][1] - 50), 60 * k + 1, 5)
    if t >= T_IN0:
        lay = img.copy(); hp = RS2.draw(Pen(lay, cam, boil), t, 0, w=wd); hands['redshirt2'] = hp
        dissolve(img, lay, t, T_IN0, T_IN1, 'i', out=False)
        if T_IN1 <= t < T_IN1 + .6:
            for j in range(4): sparkle(pen, (hp['head'][0] + 90 * math.cos(j * 1.6 + 1), hp['head'][1] + 70 * math.sin(j * 1.6 + 1)), 16 * (1 - (t - T_IN1) / .6) + 1, INK, f'nsp{j}')
    beam(pen, t, T_OUT0, T_OUT1, (RS_X, STAND)); beam(pen, t, T_IN0, T_IN1, (RS_X, STAND))
    poof(pen, t, (RS_X, STAND - 120))
    return img, hands

SETFN = {'bridge': bridge}


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
    """Grok Bot mid-press, Red Shirt #46 waving as he beams out, gauge at 95%, counter #46; title band below."""
    global POSTER_LV; POSTER_LV = .95; tt = T_OUT0 + .12
    img, _ = bridge(tt, (960, 500, 1.0))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(380, 930, 1540, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'THE RED SHIRTS', (960, 972), 104, 7)
    pen.line([(560, 1026), (1360, 1021)], 5, INK, 'tul')
    pen.text('featuring Ens. Red Shirt #46 (and #47)  \u00b7  Riker \u00d7 Grok Bot', (960, 1052), 34, INK, 'hand')
    POSTER_LV = None
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'redshirt': 'RED SHIRT #46', 'redshirt2': 'RED SHIRT #47'}; ev = []; Ls = TL['lines']
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
    out = f'{HERE}/redshirts.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
