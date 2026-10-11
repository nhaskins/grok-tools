"""Dialogue short #14: "THE STANDUP" - Picard calls a 15-minute standup; Grok Bot reports every subtask he has ever run;
the wall clock spins, the stardate climbs, calendar pages fly, beards grow to the floor. Box-only (Piper voices).
    python standup.py | --frames t ... | --poster"""
import sys, os, json, math, subprocess, time
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
SC = 1.4; STAND = FLOOR - 110 * SC

# ------------------------------------------------------------------ cue table
G1S, G1E, G2S, G2E = LN['g1']['s'], LN['g1']['e'], LN['g2']['s'], LN['g2']['e']
T_LAPSE = wt('g1', 'subtask')                        # time-lapse starts on the first "Subtask"
T_PI = G2E + .05                                     # punch-in on Riker's floor-length beard
T_BIRD = T_PI + .45
P2S, P2E, G3S, G3E = LN['p2']['s'], LN['p2']['e'], LN['g3']['s'], LN['g3']['e']
T_SUM = wt('g3', 'summary')
T_BOING = we('g3', 'thousand', 0, .08)               # clock springs off the wall
T_FAINT = T_BOING + .3
T_STAMP = T_BOING + .75
CUT_R1 = LN['r1']['s'] - .15; CUT_G1 = G1S - .15; CUT_P2 = P2S - .15; CUT_G3 = G3S - .15

# elapsed minutes: real time (1 min/s, starts at 0) until T_LAPSE, then exponential until the punch-in, then a steady
# (still absurd) rate. Target ~90 days (129,600 min) at the end of g2.
K = 1.45; U2 = T_PI - T_LAPSE; C = (129600 - T_LAPSE) / (math.exp(K * U2) - 1)
def elapsed(t):
    if t < T_LAPSE: return max(t, 0)
    u = min(t - T_LAPSE, U2); m = T_LAPSE + C * (math.exp(K * u) - 1)
    if t > T_PI: m += C * K * math.exp(K * U2) * .35 * (t - T_PI)
    return m
def rate(t, d=1 / 24): return (elapsed(t + d) - elapsed(t)) / d          # minutes per second
def fmt_elapsed(m):
    if m < 60: return f'{int(m)}:{int((m % 1) * 60):02d}'
    if m < 60 * 48: return f'{m / 60:.0f} hours'
    if m < 60 * 24 * 21: return f'{m / 1440:.0f} days'
    return f'{m / 10080:.0f} weeks'
def stardate(t): return 79042.1 + elapsed(t) / 525.6
def subtasks(t):
    if t < T_LAPSE: return 0
    if t < G2E: return 1 + int(3 * clamp01((t - T_LAPSE) / (wt('g2', 'subtask', 1) - T_LAPSE)) + .2) if t < wt('g2', 'subtask', 1) + .3 else 4
    return 4
def beard_k(t, start=1.4e3, full=1.2e5):                   # 0..1 beard growth from elapsed time (log scale)
    m = elapsed(t)
    return 0.0 if m < start else clamp01(math.log(m / start) / math.log(full / start))
def months(t): return int(elapsed(t) / 43800)              # calendar months flipped

KEYS = dict(
    picard=[(0, 'idle', 0), (wt('p1', 'quick', 0, -.1), 'point', .3), (LN['p1']['e'] + .1, 'idle', .3),
            (T_LAPSE + 1.0, 'hips', .4), (G2S + .3, 'idle+tilt=-10', .6), (P2S - .1, 'palm', .25), (P2E + .2, 'hips', .3),
            (T_SUM, 'surprise', .2), (T_FAINT, 'faint', .25)],
    grokbot=[(0, 'idle+look_l', 0), (G1S - .1, 'present', .25), (T_LAPSE + .4, 'idle+rsh=40+rel=70', .3),
             (G2E + .2, 'idle+look_l', .3), (G3S - .1, 'present', .25), (T_SUM, 'tada', .25), (T_FAINT + .3, 'idle+look_l', .3)],
    riker=[(0, 'idle+look_l', 0), (LN['r1']['s'] - .1, 'palm', .25), (LN['r1']['e'] + .1, 'idle+look_l', .3),
           (T_LAPSE + 1.5, 'chinrub', .4), (T_PI + .05, 'idle+lookup=-1+tilt=-14', .3), (T_PI + .9, 'chinrub+lookup=-1', .3),
           (P2S, 'idle+look_l', .3), (T_BOING, 'surprise', .15)],
)
NODS = dict(picard=[LN['p2']['s'] + .05], grokbot=[G1S + .05, G2S + .05, G3S + .05], riker=[LN['r1']['s'] + .05])

SHOTS = [
    (0.0, [(0.0, (960, 520, 1.0), 0), (0.0, (930, 505, 1.05), LN['p1']['e'])]),
    (CUT_R1, [(CUT_R1, (1190, 480, 1.25), 0)]),
    (CUT_G1, [(CUT_G1, (980, 470, 1.3), 0), (T_LAPSE + .8, (960, 520, 1.0), 2.4)]),       # pull out as time takes off
    (T_PI, [(T_PI, (1400, 735, 2.0), 0), (T_PI + .3, (1400, 728, 2.06), 1.2)]),          # Riker ~2/3 of frame height
    (CUT_P2, [(CUT_P2, (640, 480, 1.3), 0)]),
    (CUT_G3, [(CUT_G3, (960, 520, 1.0), 0)]),
]
SHOTS = [dict(at=a, set='bridge', cam=c) for a, c in SHOTS]
for i, s in enumerate(SHOTS): s['end'] = SHOTS[i + 1]['at'] if i + 1 < len(SHOTS) else 1e9

def shake(t): return 0 if t < T_BOING else 10 * math.exp(-(t - T_BOING) * 2.0)

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

PIC = fig('picard', 560, STAND, 1, ['shine', 'badge', 'collar'], scale=SC)
GROK = fig('grokbot', 960, STAND, -1, ['robot'], scale=SC)
RIKER = fig('riker', 1400, STAND, -1, ['beard', 'badge'], scale=SC)

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

# ------------------------------------------------------------------ props
CLK = (250, 330); CLR = 125
def wall_clock(pen, t):
    m = elapsed(t); rt = rate(t); c = CLK
    if t >= T_BOING:                                          # sprung: flies up/right, spins, falls off screen
        u = t - T_BOING
        c = (CLK[0] + 260 * u, CLK[1] - 520 * u + 900 * u * u); spin = u * 9
        # spring coil from the wall mount to the clock
        if u < .9:
            n = 9; pts = [(lerp(CLK[0], c[0], k / n) + 18 * (1 if k % 2 else -1) * (k not in (0, n)), lerp(CLK[1], c[1], k / n)) for k in range(n + 1)]
            pen.line(pts, 4, INK, 'spring')
        pen.circle(CLK, 10, 3, INK, 'mount', fill=INK)
    else: spin = 0
    jit = min(rt / 3000, 1) * 6
    c = (c[0] + jit * math.sin(t * 53), c[1] + jit * math.cos(t * 47))
    pen.circle(c, CLR, 7, INK, 'clk', fill=PAPER)
    for k in range(12):
        a = k * math.pi / 6 + spin; r0 = CLR * (.78 if k % 3 else .7)
        pen.line([(c[0] + r0 * math.sin(a), c[1] - r0 * math.cos(a)), (c[0] + CLR * .88 * math.sin(a), c[1] - CLR * .88 * math.cos(a))], 4 if k % 3 == 0 else 2.5, INK, f'tk{k}', wob=.3)
    degps = rt * 6                                             # minute hand deg/s
    if degps / FPS > 40:                                       # faster than the eye: blur disc + speed arcs
        pen.circle(c, CLR * .66, 0, fill=(150, 150, 152))
        for j in range(3):
            pen.arc(c, CLR * (.45 + .1 * j), CLR * (.45 + .1 * j), (t * 900 + j * 120) % 360, (t * 900 + j * 120) % 360 + 100, 3, INK, f'sa{j}')
    else:
        am = math.radians(m * 6) + spin; ah = math.radians(m * .5) + spin
        pen.line([c, (c[0] + CLR * .72 * math.sin(am), c[1] - CLR * .72 * math.cos(am))], 6, INK, 'mh')
        pen.line([c, (c[0] + CLR * .45 * math.sin(ah), c[1] - CLR * .45 * math.cos(ah))], 8, INK, 'hh')
    pen.circle(c, 9, 0, fill=INK)
    if t < T_BOING:
        pen.text('TIMEBOX: 15 MIN', (CLK[0], CLK[1] + CLR + 46), 40, INK, 'marker')
        if degps / FPS > 40:                                   # whoosh lines around the rim
            for j in range(4):
                a = t * 7 + j * math.pi / 2
                pen.arc(c, CLR + 22, CLR + 22, math.degrees(a), math.degrees(a) + 40, 3, INK, f'rim{j}')

MON = ['OCT', 'NOV', 'DEC', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP']
CAL = (1700, 330)
def calendar(pen, t):
    x, y = CAL; mo = months(t)
    pen.rect(x - 85, y - 95, x + 85, y + 95, 5, INK, 'cal', fill=PAPER)
    pen.rect(x - 85, y - 95, x + 85, y - 45, 0, fill=INK)
    pen.text(MON[mo % 12], (x, y - 70), 40, PAPER, 'marker')
    for r in range(3):
        for q in range(5): pen.circle((x - 60 + q * 30, y - 15 + r * 34), 4, 2, INK, f'cd{r}{q}')
    pen.circle((x - 50, y - 105), 6, 3, INK, 'cr1'); pen.circle((x + 50, y - 105), 6, 3, INK, 'cr2')
    # pages flying off: one per month flipped + a flurry while the rate is extreme
    m = elapsed(t); n_fly = 8
    if m > 20000 and t < T_PI + 4:
        for j in range(n_fly):
            u = ((t * 1.7 + j / n_fly) % 1.0)
            px = x + 30 + 380 * u * (1 if j % 2 else .6); py = y - 60 - 260 * u + 300 * u * u * (j % 3) / 2
            if t >= T_PI and t < CUT_G3: px -= 0
            SETS.paper_sheet(pen, (px, py), u * 5 + j, .9, f'pg{j}')

def report_scroll(pen, t, hand):
    """Grok Bot's status report: a paper strip from his hand, piling up in zigzag folds on the floor in front of him."""
    if t < G1S - .1: return
    talked = clamp01((t - G1S) / (G2E - G1S))
    pile_h = 30 + 330 * talked ** 1.2                             # folds stack up to ~360 px
    px0, px1 = 700, 860                                          # pile between Picard and Grok Bot
    nf = int(pile_h / 22)
    pts = []
    for k in range(nf + 1):
        yk = FLOOR - k * 22
        pts += [(px0 + 6 * math.sin(k * 1.3), yk), (px1 + 6 * math.cos(k * 1.7), yk - 11)]
    pen.line(pts, 3.5, INK, 'pile', wob=.6)
    for k in range(0, nf, 2):
        yk = FLOOR - k * 22 - 6
        pen.line([(px0 + 30, yk), (px1 - 40, yk - 6)], 1.6, INK, f'ptx{k}', wob=.8)
    top = pts[-1] if pts else (px0, FLOOR)
    pen.line([hand, ((hand[0] + top[0]) / 2 - 20, (hand[1] + top[1]) / 2 + 30), top], 10, INK, 'strip')
    pen.line([hand, ((hand[0] + top[0]) / 2 - 20, (hand[1] + top[1]) / 2 + 30), top], 5, PAPER, 'striph')
    pen.circle(hand, 13, 3.5, INK, 'roll', fill=PAPER)
    if t > T_LAPSE:
        n = subtasks(t) if t < G2E + .1 else 4
        pen.text(f'subtask {n} ... done', (px0 + 80, FLOOR - pile_h - 36), 30, INK, 'hand')

def beard(pen, h, k, f, sid, outline=False):
    """grown beard: tapered scribbly hank from the chin; reaches the floor at k=1 and pools along it"""
    if k <= 0.01: return
    hd, R = h['head'], h['R']
    cx, cy = hd[0] + f * R * .5, hd[1] + R * .8
    L = (FLOOR - cy) * k * (1.0 if not outline else .55)
    n = 14; left, right = [], []
    for i in range(n + 1):
        u = i / n; y = cy + L * u; wv = R * (.5 - .3 * u) + 3
        x = cx + f * 10 * math.sin(u * 7 + i) * u
        left.append((x - wv, y)); right.append((x + wv + 4 * math.sin(i * 2.1), y))
    if k > .97 and not outline:                                  # pools on the floor toward the front
        pool = [(cx + f * 40 * j, FLOOR - 6 + 3 * math.sin(j)) for j in range(1, 5)]
        right += pool
    poly = left + right[::-1]
    if outline:
        pen.fill(poly, PAPER); pen.line(poly, 3, INK, sid, closed=True)
        for j in range(3): pen.line([(cx - 8 + 8 * j, cy + 10), (cx - 6 + 8 * j, cy + L * .8)], 1.6, INK, f'{sid}s{j}')
    else:                                                         # ink hair: outline + wavy strands (body stays readable)
        pen.line(poly, 3.2, INK, sid, closed=True)
        for j in range(6):
            o = (j - 2.5) / 2.5
            st = [(cx + o * (R * (.5 - .3 * u) + 3) * .8 + f * 10 * math.sin(u * 7 + i) * u + 3 * math.sin(u * 19 + j), cy + L * u)
                  for i, u in enumerate(np.linspace(0.04, .97, 12))]
            pen.line(st, 2.2, INK, f'{sid}h{j}')

def bird(pen, t, h, f):
    u = t - T_BIRD
    if not 0 <= u < 1.6 or t >= CUT_P2: return
    hd, R = h['head'], h['R']
    k = ease_out_back(clamp01(u / .25))
    b = (hd[0] + f * R * .4, hd[1] + R * 2.2 - 34 * k)
    pen.circle(b, 13 * k, 3, INK, 'bird', fill=PAPER)
    pen.line([(b[0] + f * 11 * k, b[1] - 2), (b[0] + f * 21 * k, b[1] + 1), (b[0] + f * 11 * k, b[1] + 4)], 2.5, INK, 'beak')
    pen.dot((b[0] + f * 4 * k, b[1] - 4), 2.4 * k, INK)
    if u > .25: pen.text('tweet!', (b[0] - f * 70, b[1] - 46), 36, INK, 'hand')

VS = (560, 100, 1360, 470)
def viewscreen(img, pen, t, cam, boil):
    x0, y0, x1, y1 = VS; vc = (x0 + x1) / 2
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    lap = t >= T_LAPSE
    stars_field(sp, VS, t, 60 + (min(rate(t), 4e4) / 40 if lap else 0), streak=.9 if lap and rate(t) > 2000 else 0)
    sp.rect(vc - 360, y0 + 22, vc + 360, y1 - 22, 0, fill=INK)
    if t >= T_SUM - .05 and t < T_BOING + .6:
        sp.text('SUMMARY', (vc, y0 + 110), 96, PAPER, 'marker')
        sp.text('PART 1 / 40,000', (vc, y0 + 230), 80, PAPER, 'marker')
    else:
        sp.text('DAILY STANDUP', (vc, y0 + 70), 66, PAPER, 'marker')
        sp.text(f'STARDATE {stardate(t):,.1f}', (vc, y0 + 160), 62, PAPER, 'marker')
        sp.text(f'ELAPSED: {fmt_elapsed(elapsed(t))}   (timebox 15:00)', (vc, y0 + 236), 42, PAPER, 'hand')
        if lap: sp.text(f'SUBTASKS REPORTED: {subtasks(t)} of 48,112', (vc, y0 + 300), 40, PAPER, 'hand')
    clip_paste(img, sub, pen, VS)
    if t >= T_STAMP: SETS.stamp(pen, 'STANDUP: DAY 92', (vc, (y0 + y1) / 2 + 20), t, T_STAMP, 70, 6, 'st92')

def bridge(t, cam):
    sk = shake(t)
    cam = (cam[0] + sk * math.sin(t * 41), cam[1] + sk * math.cos(t * 37), cam[2])
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    viewscreen(img, pen, t, cam, boil)
    pen.text('U.S.S. TITAN', (1700, 140), 40, INK, 'marker')
    wall_clock(pen, t)
    calendar(pen, t)
    h = {}
    h['riker'] = RIKER.draw(pen, t, 0, w=5.5 * SC ** .3)
    beard(pen, h['riker'], beard_k(t), -1, 'rbeard')
    h['grokbot'] = GROK.draw(pen, t, 0, w=5.5 * SC ** .3)
    report_scroll(pen, t, h['grokbot']['hand_r'])
    if t < T_FAINT + .1:
        h['picard'] = PIC.draw(pen, t, 0, w=5.5 * SC ** .3)
        beard(pen, h['picard'], beard_k(t, 4e3, 1.3e5), 1, 'pbeard', outline=True)
    else:
        h['picard'] = PIC.draw(pen, t, 0, w=5.5 * SC ** .3)
    bird(pen, t, h['riker'], -1)
    if T_BOING <= t < T_BOING + .8: pen.text('BOING!', (CLK[0] + 120, CLK[1] - 180), 60, INK, 'marker')
    if T_FAINT + .2 <= t < T_FAINT + 1.2: pen.text('THUD', (PIC.pos_at(t)[0] - 40, FLOOR - 40), 44, INK, 'marker')
    return img, h

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

VIG, GRAINS = RT.paper_finish_clean()          # no low-frequency mottle
def finish(img, boil, fade=1.0):
    f = img.astype(np.float32) * VIG + GRAINS[boil % 4]
    if fade < 1: f = f * fade + np.array(PAPER, np.float32) * (1 - fade)
    return np.clip(f, 0, 255).astype(np.uint8)

def scene(t):
    sh = next(s for s in SHOTS if s['at'] <= t < s['end'])
    img, _ = SETFN[sh['set']](t, cam_at(sh, t))
    return finish(img, int(t * 12), clamp01((SCENE - t) / .4))


def poster():
    tt = T_PI - .2
    img, _ = bridge(tt, (960, 500, 1.0))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(500, 930, 1420, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'THE STANDUP', (960, 972), 104, 7)
    pen.line([(640, 1026), (1280, 1021)], 5, INK, 'tul')
    pen.text('Picard \u00d7 Grok Bot \u00d7 Riker  \u00b7  STARSHIP GROKBOT', (960, 1052), 34, INK, 'hand')
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
    out = f'{HERE}/standup-nosfx.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
