"""Dialogue short #8: "HALLUCINATION" - Grok Bot reports a purple nebula that is not there, doubles down with
made-up specifics and an imagined citation; Barclay has already rendered it on the holodeck (cinnamon included).
    python hallucination.py | --frames t ... | --poster"""
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
T_NEB = w('g1', 'nebula', -.05)        # scan report pops in
T_CONF = w('g1', 'ahead', 0)
T_TUMB = w('r1', 'completely', -.3)    # space tumbleweed
T_WIDTH = w('g2', 'forty', -.05); T_SCENT = w('g2', 'cinnamon', -.05); T_SRC = w('g3', 'study', -.25)
CUT_R1 = LN['r1']['s'] - .15; CUT_G2 = LN['g2']['s'] - .15; CUT_G3 = LN['g3']['s'] - .1; CUT_B1 = LN['b1']['s'] - .2
T_SNIFF = w('r2', 'smell', -.1)
KEYS = dict(
    grokbot=[(0, 'idle', 0), (w('g1', 'commander', -.1), 'idle+rsh=150+rel=10+look_l', .25), (LN['g1']['e'] + .2, 'idle+rsh=70+rel=40+padd=1', .3),
             (w('g2', 'forty', -.15), 'palm', .25), (w('g2', 'smells', -.1), 'pointup', .25), (w('g3', 'source', -.15), 'idle+rsh=70+rel=40+padd=1', .25),
             (w('g3', 'imagined', -.1), 'shrug', .25)],
    riker=[(0, 'idle+look_r', 0), (w('g1', 'nebula', 0), 'idle+look_l', .3), (w('r1', 'grok', -.15), 'point', .2),
           (w('r1', 'empty', -.1), 'palm', .25), (LN['r1']['e'] + .4, 'idle+look_r', .3), (w('g2', 'cinnamon', .1), 'chinrub', .3),
           (w('g3', 'imagined', .1), 'facepalm', .3)],
    barclay=[(0, 'hunch', 0), (w('b1', 'sir', -.15), 'present_padd', .25), (LN['b1']['e'] + .2, 'hunch+mouth=1', .3),
             (T_SNIFF, 'nervous', .2)],
    riker_h=[(0, 'idle+look_l', 0), (w('b1', 'holodeck', 0), 'surprise', .2), (w('r2', 'why', -.15), 'palm', .25), (T_SNIFF, 'chinrub+lookup=.3', .25)],
)
NODS = dict(grokbot=[w('g1', 'ahead', .05), w('g3', 'imagined', .05)], riker=[], barclay=[w('b1', 'holodeck', .05)], riker_h=[])
ENV['riker_h'] = ENV.get('riker')
SHOTS = [
    (0.0, 'titan', [(0.0, (1080, 470, 1.12), 0), (0.0, (1120, 460, 1.18), LN['g1']['e'])]),
    (CUT_R1, 'titan', [(CUT_R1, (800, 420, 1.3), 0)]),
    (CUT_G2, 'titan', [(CUT_G2, (1380, 440, 1.3), 0)]),
    (CUT_G3, 'titan', [(CUT_G3, (1500, 360, 1.55), 0), (LN['g3']['e'] - .2, (1380, 440, 1.3), .4)]),
    (CUT_B1, 'holo', [(CUT_B1, (940, 470, 1.12), 0), (LN['b1']['e'], (960, 450, 1.2), 2.0)]),
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
        return P
    return f

def fig(who, x, y, facing, props, keyname=None, **kw):
    F = Figure(who, x, y, facing, set(props), **kw)
    for k in KEYS[keyname or who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    F.mod = make_mod(keyname or who); return F

RIKER = fig('riker', 520, STAND, 1, ['beard', 'badge'], scale=SC)
GROK = fig('grokbot', 1240, STAND, -1, ['robot'], scale=SC)
BARCLAY = fig('barclay', 520, STAND, 1, ['curly', 'badge'], scale=SC)
RIKER_H = fig('riker', 1380, STAND, -1, ['beard', 'badge'], keyname='riker_h', scale=SC)

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

def tumbleweed(pen, c, t, sid, col):
    r = np.random.default_rng(5); ang = -t * 7
    pts = []
    for j in range(26):
        a = ang + j * 2.39; rr = 34 * (.4 + .6 * r.uniform())
        pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    pen.line(pts, 3, col, sid, wob=.6)
    pen.arc(c, 36, 36, 0, 360, 3, col, sid + 'o')

def nebula(pen, c, s, t, k, sid):
    """ink nebula: a soft spiral of scribbled cloud lobes with a few stars; k = 0..1 materialise"""
    if k <= 0: return
    cx, cy = c
    for j in reversed(range(9)):
        a = j * 0.7 + t * .25; d = (40 + 26 * j) * s * k
        p = (cx + d * math.cos(a), cy + .55 * d * math.sin(a))
        rx, ry = (70 + 8 * j) * s * k, (44 + 5 * j) * s * k
        pen.fill([(p[0] + rx * math.cos(a_), p[1] + ry * math.sin(a_)) for a_ in np.linspace(0, 6.283, 30)], PAPER)
        pen.arc(p, rx, ry, 0, 360, 4, INK, f'{sid}lb{j}', wob=.8)
        for h in range(3):    # hatching inside lobes
            yy = p[1] - ry * .4 + h * ry * .4
            pen.line([(p[0] - rx * .55, yy + 8), (p[0] + rx * .55, yy - 8)], 2, INK, f'{sid}h{j}{h}', wob=.5)
    pen.line([(cx + (14 * u) * s * k * math.cos(u * .9 + t * .25), cy + .55 * (14 * u) * s * k * math.sin(u * .9 + t * .25)) for u in np.linspace(0, 22, 60)],
             5, INK, sid + 'sp')
    for j in range(7):
        a = j * 1.9; d = 260 * s * k
        sparkle(pen, (cx + d * math.cos(a), cy + .5 * d * math.sin(a)), 14 * s * k * (1 + .2 * math.sin(t * 8 + j)), INK, f'{sid}st{j}')

def scent(pen, base, t, sid, n=3):
    for j in range(n):
        x0 = base[0] + (j - 1) * 40; ph = (t * .8 + j / n) % 1
        pts = [(x0 + 14 * math.sin(u * 9 + t * 4 + j), base[1] - 160 * u - 40 * ph) for u in np.linspace(0, 1, 14)]
        pen.line(pts, 3, INK, f'{sid}{j}', wob=.4)


# ------------------------------------------------------------------ set: Titan bridge
VS = (560, 100, 1360, 480)
PANEL = (1415, 70, 1885, 470)
REPORT = [(T_NEB, 'NEBULA DETECTED', 'marker', 38), (T_CONF, 'CONFIDENCE: 100%', 'marker', 38), (T_WIDTH, 'WIDTH: 40 LIGHT YEARS', 'marker', 34),
          (T_SCENT, 'SMELL: CINNAMON', 'marker', 38), (T_SRC, '[1] a study I just imagined', 'hand', 36)]
def titan(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    pen.line([(-600, 60), (480, 60), (540, 92)], 4, INK, 'rail1'); pen.line([(1380, 92), (1440, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (250, 40), 40, INK, 'marker')
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vsframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    stars_field(sp, VS, t, 0.01, n=45, seed=21)
    sp.text('FORWARD VIEW', (x0 + 24, y0 + 30), 26, PAPER, 'marker', anchor='l')
    if T_TUMB < t < T_TUMB + 2.2:
        u = (t - T_TUMB) / 2.2; tumbleweed(sp, (lerp(x0 - 40, x1 + 40, u), 420 - 30 * abs(math.sin(u * 9))), t, 'tw', PAPER)
    clip_paste(img, sub, pen, VS)
    cx = 960; pen.line([(cx - 60, 826), (cx + 60, 826)], 6, INK, 'seat')
    back = [(cx - 52, 826), (cx - 58, 680), (cx + 58, 680), (cx + 52, 826)]; pen.fill(back, PAPER); pen.line(back, 5, INK, 'cback', closed=True)
    pen.line([(cx, 826), (cx, FLOOR)], 6, INK, 'ped'); pen.line([(cx - 44, FLOOR), (cx + 44, FLOOR)], 6, INK, 'cbase')
    console(pen, 1620, 1810, 712, sid='sci', label='SCI')
    if t >= T_NEB:   # Grok Bot's scan report
        px0, py0, px1, py1 = PANEL; k = ease_out_back(clamp01((t - T_NEB) / .25))
        cxp, cyp = (px0 + px1) / 2, (py0 + py1) / 2
        pen.rect(cxp - (px1 - px0) / 2 * k, cyp - (py1 - py0) / 2 * k, cxp + (px1 - px0) / 2 * k, cyp + (py1 - py0) / 2 * k, 5, INK, 'rep', fill=PAPER)
        if k > .9:
            for j, (ta, txt, font, sz) in enumerate(REPORT):
                if t < ta: continue
                kk = ease_out_back(clamp01((t - ta) / .2))
                y = py0 + 50 + j * 74 + (12 if j == 4 else 0)
                pen.text(txt, (cxp - (14 if j == 0 else 0), y), sz * kk + 1, INK, font)
                if j == 0 and kk > .9: SETS.check(pen, (px1 - 26, y - 6), 1.3, 'repck')
            pen.line([(px0 + 30, py0 + 82), (px1 - 30, py0 + 80)], 3, INK, 'repul')
            if t >= T_SRC: pen.line([(px0 + 30, py0 + 340), (px1 - 30, py0 + 338)], 2, INK, 'repfn', wob=.5)
    h = {}
    h['riker'] = RIKER.draw(pen, t, 0, w=5.5 * SC ** .3)
    h['grokbot'] = GROK.draw(pen, t, 0, w=5.5 * SC ** .3)
    if t > T_SCENT and t < CUT_B1:   # imaginary cinnamon wafting off Grok Bot's report
        scent(pen, (1500, 60), t, 'gsc', 2)
    return img, h


# ------------------------------------------------------------------ set: holodeck (with the nebula)
WALL = (300, 140, 1620, 640); VP = (960, 390)
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
    pen.rect(205, 660, 470, 706, 4, INK, 'plate', fill=PAPER); pen.text('LT. BARCLAY // HOLODECK', (337, 683), 19, INK, 'marker')

def holo(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    holo_room(pen, t)
    k = ease_out_back(clamp01((t - CUT_B1 - .15) / .5))
    nebula(pen, (930, 380), 1.0, t, k, 'nb')
    if k > .9:
        pen.rect(700, 600, 1160, 660, 4, INK, 'nlab', fill=PAPER); pen.text('NEBULA (PURPLE, PROBABLY)', (930, 630), 30, INK, 'marker')
    if t > LN['b1']['s'] + .8: scent(pen, (930, 300), t, 'hsc', 3)
    if t > T_SNIFF:
        pen.text('cinnamon', (1150, 210), 46 * ease_out_back(clamp01((t - T_SNIFF) / .25)) + 1, INK, 'hand')
    h = {}
    h['barclay'] = BARCLAY.draw(pen, t, 0, w=5.5 * SC ** .3)
    h['riker'] = RIKER_H.draw(pen, t, 0, w=5.5 * SC ** .3)
    if t > T_SNIFF:   # Riker sniffs: smell lines toward his nose
        hd = h['riker']['head']
        for j in range(2): pen.line([(hd[0] - 70 - 20 * j, hd[1] - 30 + 24 * j), (hd[0] - 45, hd[1] + 2)], 3, INK, f'sn{j}', wob=.4)
    return img, h

SETFN = {'titan': titan, 'holo': holo}


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
    """bridge: Grok Bot proudly pointing at an empty viewscreen, scan report says NEBULA DETECTED 100%."""
    tt = T_SCENT + .45
    img, _ = titan(tt, (1110, 430, 1.08))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(400, 930, 1520, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'HALLUCINATION', (960, 972), 104, 7)
    pen.line([(560, 1026), (1360, 1021)], 5, INK, 'tul')
    pen.text('Grok Bot \u00d7 Riker \u00d7 Barclay  \u00b7  STARSHIP GROKBOT', (960, 1052), 36, INK, 'hand')
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'barclay': 'BARCLAY'}; ev = []; Ls = TL['lines']
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
    out = f'{HERE}/hallucination.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
