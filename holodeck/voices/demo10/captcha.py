"""Dialogue short #10: "CAPTCHA" - the Enterprise-D asks the Titan to prove it is not a robot; Grok Bot selects every
square (himself included); Riker passes by sitting backwards in a chair; Grok Bot tries it and topples over.
    python captcha.py | --frames t ... | --poster"""
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
    for x in L['words']: WT[L['id']].setdefault(x['w'].strip('.,!?:').lower(), x['s'])
LN = {L['id']: L for L in TL['lines']}
def w(line, word, off=0.0): return WT[line][word] + off
SC = 1.4; STAND = FLOOR - 110 * SC


# ------------------------------------------------------------------ cue table
T_POINT = w('p1', 'prove', -.15)
T_GRID = w('g1', 'select', -.1)                       # image grid appears on the Titan viewscreen
TAP0, TAP1 = w('g1', 'every', -.05), LN['g1']['e'] + .35
T_DENY = w('p2', 'denied', -.1)
T_SIT = w('r1', 'watch', -.05)                        # Riker lands in the chair (backwards)
T_TICK = w('p3', 'verified', -.15)                    # checkbox ticks itself
T_G2SIT = w('g2', 'will', -.1); T_FALL = LN['g2']['e'] + .05
CUT_G1 = LN['g1']['s'] - .2; CUT_GRID = T_GRID + .15; CUT_P2 = LN['p2']['s'] - .15; CUT_R1 = LN['r1']['s'] - .2
CUT_P3 = LN['p3']['s'] - .15; CUT_G2 = LN['g2']['s'] - .15
SC = 1.4; STAND = FLOOR - 110 * SC; SEATY = FLOOR - 58 * SC
CHAIR_X, CHAIR2_X = 760, 1500
POINT_R = 'front+lsh=10+lel=10+rsh=95+rel=-20'
KEYS = dict(
    picard=[(0, 'front+rsh=40+rel=110+tilt=4', 0), (w('p1', 'titan', -.1), 'front+lsh=20+lel=10+rsh=60+rel=80', .25),
            (T_POINT, POINT_R + '+mouth=1', .25), (LN['p1']['e'] + .3, 'front+rsh=40+rel=110+tilt=4', .3),
            (w('p2', 'selected', -.2), 'front+lsh=30+lel=-70+rsh=30+rel=-70', .25), (T_DENY, 'facepalmF', .25),
            (LN['p2']['e'] + .4, 'front', .3),
            (w('p3', 'only', -.15), 'front+lsh=20+lel=10+rsh=60+rel=80+lookup=-.2', .3), (T_TICK, 'front+mouth=2+rsh=150+rel=20', .2),
            (LN['p3']['e'] + .3, 'front+mouth=1', .3), (T_FALL + .1, 'facepalmF', .25)],
    grokbot=[(0, 'idle+look_l', 0), (CUT_G1 + .1, 'idle', .2), (T_GRID - .1, 'idle+rsh=130+rel=20', .2),
             (LN['g1']['e'] + .45, 'thumbs', .25), (T_DENY, 'surprise', .15), (LN['p2']['e'] + .3, 'idle+look_l+tilt=-12', .3),
             (T_SIT + .2, 'idle+look_l', .3), (w('g2', 'understood', -.1), 'pointup', .25), (T_G2SIT - .1, 'idle', .2),
             (T_G2SIT + .45, 'legover', .25), (T_FALL - .15, 'faint', .3)],
    riker=[(0, 'idle+look_r', 0), (T_GRID + .4, 'idle+look_r+lookup=.3', .3), (T_DENY + .2, 'chinrub', .3),
           (w('r1', 'allow', -.15), 'idle', .2), (T_SIT - .55, 'legover', .25), (T_SIT - .05, 'straddle', .25),
           (T_SIT + .5, 'straddle+thumbs', .25), (T_TICK + .2, 'straddle+mouth=2', .2), (T_FALL + .1, 'straddle+chinrub', .3)],
)
NODS = dict(picard=[w('p3', 'verified', .1)], grokbot=[w('g1', 'easy', .05)], riker=[w('r1', 'learn', .05)])
SHOTS = [
    (0.0, 'ent', [(0.0, (960, 500, 1.0), 0), (0.0, (1000, 480, 1.06), LN['p1']['e'])]),
    (CUT_G1, 'titan', [(CUT_G1, (980, 480, 1.0), 0)]),
    (CUT_GRID, 'titan', [(CUT_GRID, (1080, 360, 1.5), 0)]),
    (CUT_P2, 'ent', [(CUT_P2, (1060, 470, 1.08), 0)]),
    (CUT_R1, 'titan', [(CUT_R1, (700, 540, 1.2), 0)]),
    (CUT_P3, 'titan', [(CUT_P3, (900, 430, 1.15), 0)]),
    (CUT_G2, 'titan', [(CUT_G2, (1200, 520, 1.15), 0), (T_FALL + .3, (1080, 500, 1.05), .6)]),
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
        if who == 'picard' and w('p2', 'you', 0) < t < T_DENY:          # disapproving head shake
            P['tilt'] += 9 * math.sin((t - w('p2', 'you', 0)) * 2 * math.pi * 2.6)
        if who == 'grokbot' and TAP0 < t < TAP1:                         # rapid-fire tapping
            ph = (t - TAP0) * 7.0; P['rel'] += 26 * abs(math.sin(ph * math.pi)); P['rsh'] -= 14 * abs(math.sin(ph * math.pi))
        return P
    return f

def fig(who, x, y, facing, props, keyname=None, **kw):
    F = Figure(who, x, y, facing, set(props), **kw)
    for k in KEYS[keyname or who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    base = make_mod(keyname or who)
    def mod(t, P):
        P = base(t, P)
        x0, y0 = F.pos_at(t); x1, y1 = F.pos_at(t + .04)
        v = abs(x1 - x0) / .04
        if v > 40 and abs(y1 - y0) < 3:        # stride while walking
            a = min(v / 400, 1); ph = math.sin(t * 2 * math.pi * 2.4)
            P['lhip'] += 26 * a * ph; P['rhip'] -= 26 * a * ph
            P['lkn'] -= 22 * a * max(-ph, 0); P['rkn'] -= 22 * a * max(ph, 0)
            P['lsh'] -= 16 * a * ph; P['rsh'] += 16 * a * ph
        return P
    F.mod = mod; return F

RIKER = fig('riker', 380, STAND, 1, ['beard', 'badge'], scale=SC)
RIKER.move(w('r1', 'allow', -.15), CHAIR_X - 95, STAND, .8); RIKER.move(T_SIT - .3, CHAIR_X - 20, SEATY, .3)
GROK = fig('grokbot', 1340, STAND, -1, ['robot'], scale=SC)
GROK.move(CUT_G1 + .1, 1210, STAND, .5); GROK.move(T_G2SIT - .1, CHAIR2_X + 30, STAND, .5)
GROK.move(T_G2SIT + .55, CHAIR2_X + 20, SEATY - 10, .25); GROK.move(T_FALL - .15, CHAIR2_X + 110, FLOOR - 30, .3)
PIC = fig('picard', 640, 880, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=3.3)
PIC_M = fig('picard', 680, 520, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=1.05)

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

def chair(pen, cx, s=SC, mirror=False, sid='ch'):
    m = -1 if mirror else 1; sy = FLOOR - 52 * s
    pen.line([(cx - 52 * s * m, sy), (cx + 40 * s * m, sy)], 6, INK, sid + 'seat')
    back = [(cx + 34 * s * m, sy), (cx + 40 * s * m, FLOOR - 152 * s), (cx + 56 * s * m, FLOOR - 152 * s), (cx + 50 * s * m, sy)]
    pen.fill(back, PAPER); pen.line(back, 5, INK, sid + 'back', closed=True)
    pen.line([(cx - 6 * s * m, sy), (cx - 6 * s * m, FLOOR)], 6, INK, sid + 'ped'); pen.line([(cx - 44 * s * m, FLOOR), (cx + 32 * s * m, FLOOR)], 6, INK, sid + 'base')

def checkbox(pen, c, s, ticked, sid, col=INK, bg=PAPER, k=1.0):
    x, y = c; r = 32 * s
    pen.rect(x - r, y - r, x + r, y + r, 5, col, sid, fill=bg)
    if ticked and k > 0:
        pts = [(x - 20 * s, y + 2 * s), (x - 5 * s, y + 18 * s), (x + 26 * s, y - 24 * s)]
        pen.line(partial_line(pts, k), 8 * s ** .5, col, sid + 'ck')

def partial_line(pts, k):
    P = np.array(pts, float); seg = np.linalg.norm(np.diff(P, axis=0), axis=1); L = np.concatenate([[0], np.cumsum(seg)])
    tgt = L[-1] * clamp01(k); i = max(0, min(int(np.searchsorted(L, tgt)) - 1, len(seg) - 1)); f = (tgt - L[i]) / max(seg[i], 1e-6)
    return [tuple(p) for p in P[:i + 1]] + [tuple(P[i] + (P[i + 1] - P[i]) * f)]

# ------------------------------------------------------------------ doodles for the image grid
def d_ship(pen, c, s, sid):
    x, y = c
    pen.arc((x + 8 * s, y - 8 * s), 26 * s, 9 * s, 0, 360, 3, INK, sid + 'a')
    pen.line([(x - 4 * s, y - 2 * s), (x - 10 * s, y + 8 * s)], 3, INK, sid + 'b')
    pen.arc((x - 20 * s, y + 10 * s), 14 * s, 5 * s, 0, 360, 3, INK, sid + 'c')
    pen.line([(x - 30 * s, y - 14 * s), (x - 6 * s, y - 14 * s)], 3, INK, sid + 'd')
def d_planet(pen, c, s, sid):
    pen.circle(c, 18 * s, 3, INK, sid + 'p'); pen.arc(c, 32 * s, 8 * s, 190, 350, 3, INK, sid + 'r')
def d_cup(pen, c, s, sid):
    x, y = c; pen.line([(x - 14 * s, y - 12 * s), (x - 10 * s, y + 14 * s), (x + 10 * s, y + 14 * s), (x + 14 * s, y - 12 * s)], 3, INK, sid + 'c')
    pen.arc((x + 16 * s, y), 7 * s, 8 * s, -90, 90, 3, INK, sid + 'h')
    for j in range(2): pen.line([(x - 4 * s + 8 * j * s, y - 18 * s), (x - 1 * s + 8 * j * s, y - 30 * s)], 2, INK, sid + f's{j}')
def d_star(pen, c, s, sid): sparkle(pen, c, 20 * s, INK, sid)
def d_grok(pen, c, s, sid):
    x, y = c; pen.rect(x - 20 * s, y - 16 * s, x + 20 * s, y + 18 * s, 3, INK, sid + 'h')
    for dx in (-8, 8): pen.dot((x + dx * s, y - 4 * s), 3.5 * s, INK)
    pen.rect(x - 9 * s, y + 6 * s, x + 9 * s, y + 11 * s, 2, INK, sid + 'm'); pen.line([(x, y - 16 * s), (x + 3 * s, y - 28 * s)], 2.5, INK, sid + 'a')
def d_rock(pen, c, s, sid):
    x, y = c; pen.line([(x - 18 * s, y), (x - 8 * s, y - 14 * s), (x + 12 * s, y - 12 * s), (x + 20 * s, y + 4 * s), (x + 4 * s, y + 16 * s), (x - 14 * s, y + 12 * s)],
                       3, INK, sid, closed=True)
CELLS = [d_ship, d_planet, d_cup, d_star, d_rock, d_ship, d_grok, d_planet, d_star, d_cup, d_ship, d_rock]
GRID = (880, 180, 4, 3, 110, 92)        # x0, y0, cols, rows, cell w, cell h  (on the Titan viewscreen)
def tap_order():
    order = [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11]          # zig-zag, Grok Bot's own head (6) lands mid-run
    return order
def selected(t):
    if t < TAP0: return set()
    n = int(clamp01((t - TAP0) / (TAP1 - TAP0 - .1)) * 12 + .999)
    return set(tap_order()[:n])

def image_grid(sp, t, show_sel=True, x0=None, y0=None, cw=None, ch=None, s=1.0):
    gx, gy, nc, nr, gw, gh = GRID
    x0 = gx if x0 is None else x0; y0 = gy if y0 is None else y0; cw = gw if cw is None else cw; ch = gh if ch is None else ch
    sel = selected(t) if show_sel else set()
    for i in range(nc * nr):
        r, c = divmod(i, nc); cx0, cy0 = x0 + c * cw, y0 + r * ch
        on = i in sel
        sp.rect(cx0 + 4, cy0 + 4, cx0 + cw - 4, cy0 + ch - 4, 3, INK, f'cell{i}', fill=PAPER)
        CELLS[i](sp, (cx0 + cw / 2, cy0 + ch / 2), s * (.85 if on else 1.0), f'cd{i}')
        if on:
            sp.rect(cx0 + 4, cy0 + 4, cx0 + cw - 4, cy0 + ch - 4, 7, INK, f'cs{i}')
            sp.circle((cx0 + 18, cy0 + 18), 13, 0, INK, f'cdot{i}', fill=INK)
            sp.line([(cx0 + 11, cy0 + 18), (cx0 + 16, cy0 + 24), (cx0 + 25, cy0 + 12)], 3, PAPER, f'cck{i}')


# ------------------------------------------------------------------ set: Enterprise-D (full frame)
ES = (70, 40, 1850, 860); CARD = (1160, 170, 1790, 720)
def ent(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    pen.rect(ES[0] - 16, ES[1] - 16, ES[2] + 16, ES[3] + 16, 6, INK, 'eframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    stars_field(sp, ES, t, 0.015, n=110, seed=21)
    sp.text('U.S.S. ENTERPRISE-D  //  DOCKING CONTROL', (120, 95), 40, PAPER, 'marker', anchor='l')
    PIC.draw(sp, t, 0, w=8)
    sp.rect(240, 700, 1060, 980, 6, PAPER, 'desk', fill=INK); sp.line([(280, 740), (1020, 740)], 3, PAPER, 'desk2')
    sp.text('CAPT. PICARD  //  U.S.S. ENTERPRISE-D', (650, 805), 40, PAPER, 'marker')
    px0, py0, px1, py1 = CARD; cx = (px0 + px1) / 2
    sp.rect(px0, py0, px1, py1, 5, PAPER, 'card', fill=PAPER)
    sp.text('SECURITY CHECK', (cx, py0 + 52), 48, INK, 'marker'); sp.line([(px0 + 30, py0 + 88), (px1 - 30, py0 + 86)], 3, INK, 'cul')
    if t < CUT_G1:
        checkbox(sp, (px0 + 110, py0 + 230), 1.5, False, 'cb1')
        sp.text("I'm not a robot", (px0 + 190, py0 + 230), 52, INK, 'hand', anchor='l')
        sp.text('reCAPTAIN', (px1 - 100, py1 - 60), 30, INK, 'marker'); sp.text('privacy - terms - tea', (px1 - 150, py1 - 26), 22, INK, 'hand')
        sp.circle((px1 - 220, py1 - 60), 24, 4, INK, 'logo')
    else:
        sp.text('you selected:', (cx, py0 + 135), 34, INK, 'hand')
        image_grid(sp, LN['g1']['e'] + 1, True, px0 + 95, py0 + 160, 110, 92)
        sp.text('(including yourself)', (cx, py0 + 470), 34, INK, 'hand')
        if t > T_DENY: SETS.stamp(sp, 'ACCESS DENIED', (cx, py0 + 300), t, T_DENY, 62)
    clip_paste(img, sub, pen, ES)
    return img, {}


# ------------------------------------------------------------------ set: Titan bridge
VS = (560, 100, 1360, 480)
def titan(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    pen.line([(-600, 60), (480, 60), (540, 92)], 4, INK, 'rail1'); pen.line([(1380, 92), (1440, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (250, 40), 40, INK, 'marker')
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vsframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    stars_field(sp, VS, t, 0.02, n=40, seed=4)
    PIC_M.draw(sp, t, 0, w=4)
    sp.text('ENTERPRISE-D', (680, 135), 26, PAPER, 'marker')
    wx0, wy0, wx1, wy1 = 850, 120, 1340, 465; wc = (wx0 + wx1) / 2
    sp.rect(wx0, wy0, wx1, wy1, 4, PAPER, 'widget', fill=PAPER)
    if T_GRID <= t < CUT_R1:
        sp.text('select all squares with', (wc, wy0 + 24), 26, INK, 'hand'); sp.text('STARSHIPS', (wc, wy0 + 50), 30, INK, 'marker')
        image_grid(sp, t, True, wx0 + 25, wy0 + 70, 110, 90)
        if t > T_DENY: SETS.stamp(sp, 'DENIED', (wc, wy0 + 200), t, T_DENY, 60, sid='den2')
    else:
        tick = t >= T_TICK and t < T_FALL + .2
        k = clamp01((t - T_TICK) / .3)
        checkbox(sp, (wx0 + 70, wy0 + 120), 1.3, tick, 'cbm', k=k)
        sp.text("I'm not a robot", (wx0 + 130, wy0 + 120), 46, INK, 'hand', anchor='l')
        if tick and k > .6:
            SETS.stamp(sp, 'VERIFIED HUMAN', (wc, wy0 + 245), t, T_TICK + .2, 46, sid='vh')
        if t >= T_FALL + .2:
            sp.text('robot detected. try again.', (wc, wy0 + 250), 34, INK, 'hand')
        sp.text('reCAPTAIN', (wx1 - 80, wy1 - 30), 24, INK, 'marker')
    clip_paste(img, sub, pen, VS)
    console(pen, 230, 400, 712, sid='ops', mirror=True, label='OPS')
    chair(pen, CHAIR_X, sid='c1'); chair(pen, CHAIR2_X, mirror=True, sid='c2')
    h = {'riker': RIKER.draw(pen, t, 0, w=5.5 * SC ** .3), 'grokbot': GROK.draw(pen, t, 0, w=5.5 * SC ** .3)}
    if T_SIT <= t < T_SIT + .8:                          # landing puff
        a = 1 - clamp01((t - T_SIT - .5) / .3)
        for j in range(3): pen.arc((CHAIR_X - 60 + 60 * j, FLOOR - 10), 22 + 30 * clamp01((t - T_SIT) / .4), 10, 180, 360, 3, INK, f'pf{j}') if a > .3 else None
    if t >= T_FALL + .15:                                # Grok Bot down: THUD + dizzy stars
        k = ease_out_back(clamp01((t - T_FALL - .15) / .25))
        pen.text('THUD!', (CHAIR2_X + 230, FLOOR - 170), 72 * k + 1, INK, 'marker')
        hd = h['grokbot']['head']
        for j in range(3):
            a = t * 5 + j * 2.1; sparkle(pen, (hd[0] + 55 * math.cos(a), hd[1] - 60 + 16 * math.sin(a)), 13, INK, f'dz{j}')
    return img, h

SETFN = {'ent': ent, 'titan': titan}


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
    """Picard on screen with the I'm-not-a-robot card; title band below."""
    tt = T_POINT + .4
    img, _ = ent(tt, (960, 470, 1.0))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(560, 930, 1360, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'CAPTCHA', (960, 972), 110, 7)
    pen.line([(700, 1026), (1220, 1021)], 5, INK, 'tul')
    pen.text('Picard \u00d7 Grok Bot \u00d7 Riker  \u00b7  STARSHIP GROKBOT', (960, 1052), 36, INK, 'hand')
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
    out = f'{HERE}/captcha.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
