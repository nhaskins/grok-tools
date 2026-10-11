"""Dialogue short #9: "TECHNICAL DEBT" - Riker's tower of IOU "deals" looms over the bridge; the Captain asks for a refactor;
Grok Bot pulls the one note marked DON'T TOUCH, the tower collapses, and he "refactors" everything into one box labelled LEGACY.
    python technicaldebt.py | --frames t ... | --poster"""
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
T_GROW = (w('r1', 'deals', -.1), LN['r1']['e'])       # extra notes pop onto the tower
T_INT = w('g1', 'interest', -.1)                      # interest counter takes off
T_PULL = w('r2', 'sprint', .05)                         # Grok Bot yanks DON'T TOUCH
T_BOX = w('g2', 'refactor', .05)                     # notes swoosh into the LEGACY box
T_LEG = w('g2', 'legacy', -.05)
CUT_R1 = LN['r1']['s'] - .15; CUT_G1 = LN['g1']['s'] - .15; CUT_C2 = LN['c2']['s'] - .15; CUT_R2 = LN['r2']['s'] - .15
CUT_WIDE = T_PULL - .25
KEYS = dict(
    captain=[(0, 'sit+look_l', 0), (w('c1', 'tower', -.15), 'sit+rsh=70+rel=20', .25), (LN['c1']['e'] + .3, 'sit+look_l', .3),
             (w('c2', 'number', -.15), 'sit+rsh=40+rel=100+lsh=40+lel=100+lookup=-.2', .3), (w('c2', 'refactor', -.1), 'sit+rsh=70+rel=20', .2),
             (T_PULL + .1, 'sit+surprise', .15), (T_LEG + .2, 'sit+facepalm', .3)],
    riker=[(0, 'idle+look_r', 0), (w('r1', 'those', -.15), 'palm', .25), (w('r1', 'great', -.1), 'proud', .25), (LN['r1']['e'] + .2, 'idle+look_r', .3),
           (w('g1', 'seconds', 0), 'chinrub', .3), (w('r2', 'pay', -.15), 'thumbs', .25), (T_PULL + .1, 'surprise', .15),
           (T_BOX + .6, 'idle+look_r', .4)],
    grokbot=[(0, 'idle+look_l', 0), (w('g1', 'interest', -.15), 'idle+rsh=70+rel=40+padd=1', .25), (LN['g1']['e'] + .3, 'idle+look_l', .3),
             (T_PULL - .25, 'idle+rsh=80+rel=10', .2), (T_PULL, 'pull', .12), (T_PULL + .5, 'idle+rsh=60+rel=50', .3),
             (w('g2', 'refactor', -.1), 'idle+rsh=60+rel=50+lsh=150+lel=10', .25), (T_LEG, 'thumbs', .25)],
)
NODS = dict(captain=[w('c2', 'refactor', .1)], riker=[w('r2', 'sprint', .05)], grokbot=[w('g2', 'complete', .05)])
SHOTS = [
    (0.0, 'bridge', [(0.0, (960, 470, 1.0), 0), (0.0, (980, 480, 1.04), LN['c1']['e'])]),
    (CUT_R1, 'bridge', [(CUT_R1, (680, 545, 1.12), 0), (CUT_R1, (690, 540, 1.16), 3.0)]),
    (CUT_G1, 'bridge', [(CUT_G1, (1420, 520, 1.2), 0)]),
    (CUT_C2, 'bridge', [(CUT_C2, (1330, 600, 1.4), 0)]),
    (CUT_R2, 'bridge', [(CUT_R2, (690, 555, 1.2), 0)]),
    (CUT_WIDE, 'bridge', [(CUT_WIDE, (960, 480, 1.0), 0), (T_BOX + .6, (960, 500, 1.06), 1.2)]),
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

def fig(who, x, y, facing, props, **kw):
    F = Figure(who, x, y, facing, set(props), **kw)
    for k in KEYS[who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    F.mod = make_mod(who); return F

RIKER = fig('riker', 360, STAND, 1, ['beard', 'badge'], scale=SC)
GROK = fig('grokbot', 1030, STAND, -1, ['robot'], scale=SC)
CHAIR_X, SEAT_Y = 1440, 790
CAPTAIN = fig('captain', CHAIR_X, SEAT_Y - 10, -1, ['cap', 'badge'], scale=SC)

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]


# ------------------------------------------------------------------ the tower of IOUs
NOTES = ['TODO: FIX LATER', 'IOU: 1 FAVOR (FERENGI)', "HACK: DON'T TOUCH", 'DEAL: TROMBONE GIG', 'IOU: POKER NIGHT',
         'TEMP FIX (2019)', 'IOU: 3 FAVORS', 'TODO: WRITE TESTS', 'DEAL: SHORE LEAVE', 'IOU: 2 FAVORS (Q)', 'FIXME',
         'DEAL: BAR TAB', 'IOU: 1 HOLODECK HOUR', 'TODO: EVERYTHING']
PULLED = 2; TX = 700; NW, NH = 330, 60; N0 = 9
_r = np.random.default_rng(3)
OFFX = _r.uniform(-28, 28, len(NOTES)); ROT = _r.uniform(-4, 4, len(NOTES))
FALL_VX = _r.uniform(-380, 380, len(NOTES)); FALL_SPIN = _r.uniform(-400, 400, len(NOTES)); FALL_DELAY = _r.uniform(0, .12, len(NOTES))
PILE = [(TX + _r.uniform(-280, 280), FLOOR - 26 - _r.uniform(0, 40), _r.uniform(-25, 25)) for _ in NOTES]
BOX = (TX - 40, FLOOR, 420, 230)          # centre-bottom x, floor y, w, h

def n_notes(t):
    a, b = T_GROW
    return N0 + int(round((len(NOTES) - N0) * clamp01((t - a) / (b - a))))

def sway(t):
    amp = 3 + 9 * clamp01((t - T_GROW[0]) / 2.5) + 10 * clamp01((t - CUT_R2) / 1.5)
    return amp * math.sin(t * 2 * math.pi * .9) + .4 * amp * math.sin(t * 2 * math.pi * 2.3)

def note_rest(i, t):
    """stacked position (centre) and rotation of note i"""
    hfrac = (i + .5) / len(NOTES)
    x = TX + OFFX[i] + sway(t) * hfrac ** 2 * 4.5
    y = FLOOR - NH * (i + .5)
    return x, y, ROT[i] + sway(t) * hfrac * .25

def draw_note(pen, c, rot, txt, sid, s=1.0, size=24):
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
    hw, hh = NW / 2 * s, NH / 2 * s - 3
    pts = [(c[0] + x * ca - y * sa, c[1] + x * sa + y * ca) for x, y in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
    pen.fill(pts, PAPER); pen.line(pts, 4, INK, sid, closed=True)
    pen.line([pts[0], (pts[0][0] + 16 * s, pts[0][1] + 2), (pts[0][0], pts[0][1] + 16 * s)], 2.5, INK, sid + 'pin')   # folded corner
    if s > .45: pen.text(txt, c, size * s, INK, 'marker')

def tower(pen, t, hands):
    n = n_notes(t)
    if t < T_PULL:
        for i in range(n):
            x, y, r = note_rest(i, t)
            pop = T_GROW[0] + (i - N0 + .5) / (len(NOTES) - N0) * (T_GROW[1] - T_GROW[0]) if i >= N0 else -9
            k = ease_out_back(clamp01((t - pop) / .2)) if i >= N0 else 1
            if i == PULLED and t > T_PULL - .25:   # Grok Bot's fingers on it
                x += 20 * clamp01((t - T_PULL + .25) / .25)
            draw_note(pen, (x, y - (1 - k) * 60), r, NOTES[i], f'n{i}', s=max(k, .05))
        if t > T_GROW[1] - .2 and T_GROW[1] - .2 < t < T_GROW[1] + .9:
            SETS.burst(pen, (TX, FLOOR - NH * len(NOTES) + 10), t, T_GROW[1] - .2, 90, n=12, sid='topb')
        return
    u0 = t - T_PULL
    for i in range(len(NOTES)):
        if i == PULLED: continue
        x0, y0, r0 = note_rest(i, T_PULL)
        u = max(u0 - FALL_DELAY[i] - .03 * abs(i - PULLED), 0)
        px, py, pr = PILE[i]
        x = x0 + FALL_VX[i] * u; y = y0 + .5 * 3800 * u * u; r = r0 + FALL_SPIN[i] * u
        if y >= py: x, y, r = px, py, pr                       # landed
        if t > T_BOX:                                           # swoosh into the box
            k = ease(clamp01((t - T_BOX - .03 * i) / .45))
            bx = BOX[0] + (i % 4 - 1.5) * 60; by = BOX[1] - BOX[3] * .55
            x, y, r = lerp(x, bx, k), lerp(y, by, k), lerp(r, 0, k)
            if k >= 1: continue
            draw_note(pen, (x, y), r, NOTES[i], f'n{i}', s=1 - .5 * k)
        else:
            draw_note(pen, (x, y), r, NOTES[i], f'n{i}')
    if u0 < .5:
        for j in range(5): pen.line([(TX - 260 + j * 130, FLOOR - 10), (TX - 300 + j * 150, FLOOR - 60 - 30 * (j % 2))], 3, INK, f'dust{j}')
    # Grok Bot keeps the DON'T TOUCH note in his hand
    h = hands.get('grokbot')
    if h:
        hx, hy = h['hand_r']
        draw_note(pen, (hx - 130 * .85, hy - 14), -8, NOTES[PULLED], 'npull', s=.85, size=30)

def legacy_box(pen, t):
    if t < T_BOX - .15: return
    k = ease_out_back(clamp01((t - T_BOX + .15) / .3))
    cx, fy, bw, bh = BOX; bw *= k; bh *= k
    pen.rect(cx - bw / 2, fy - bh, cx + bw / 2, fy, 6, INK, 'box', fill=PAPER)
    lid = clamp01((t - T_BOX - .75) / .2)
    if lid > 0:
        pen.line([(cx - bw / 2 - 10, fy - bh), (cx + bw / 2 + 10, fy - bh - 20 * (1 - lid))], 7, INK, 'lid')
    else:
        pen.line([(cx - bw / 2, fy - bh), (cx - bw / 2 - 80 * k, fy - bh - 140 * k)], 6, INK, 'lidopen')
    if k > .8:
        pen.text('LEGACY', (cx, fy - bh * .58), 74 * k, INK, 'marker')
    if t > T_LEG:
        SETS.stamp(pen, 'DO NOT OPEN', (cx, fy - bh * .22), t, T_LEG, 40, sid='dno')


# ------------------------------------------------------------------ set: bridge
VS = (560, 100, 1360, 480)
PANEL = (1450, 60, 1870, 330)
def interest(t):
    base = 1204
    if t < T_INT: return base + int(t * 7)
    return int(base * math.exp(1.15 * (t - T_INT)))

def bridge(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    pen.line([(-600, 60), (480, 60), (540, 92)], 4, INK, 'rail1'); pen.line([(1380, 92), (1440, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (250, 40), 40, INK, 'marker')
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vsframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil); stars_field(sp, VS, t, 0.03, n=45, seed=9); clip_paste(img, sub, pen, VS)
    # interest panel
    px0, py0, px1, py1 = PANEL
    pen.rect(px0, py0, px1, py1, 5, INK, 'ipanel', fill=PAPER)
    pen.text('INTEREST OWED', ((px0 + px1) / 2, py0 + 45), 40, INK, 'marker'); pen.line([(px0 + 30, py0 + 78), (px1 - 30, py0 + 76)], 3, INK, 'iul')
    v = interest(t)
    pen.text(f'{v:,}', ((px0 + px1) / 2, py0 + 140), 64 if v < 10 ** 7 else 52, INK, 'marker')
    pen.text('favors' if t < T_LEG + .3 else 'favors (still accruing)', ((px0 + px1) / 2, py0 + 210), 36, INK, 'hand')
    if T_INT < t: pen.line([(px1 - 60, py0 + 120), (px1 - 40, py0 + 95), (px1 - 20, py0 + 120)], 4, INK, 'iarr')
    # captain's chair (profile: back on the right, he faces left)
    cx = CHAIR_X; pen.line([(cx - 70, SEAT_Y + 36), (cx + 50, SEAT_Y + 36)], 7, INK, 'seat')
    back = [(cx + 40, SEAT_Y + 36), (cx + 56, SEAT_Y - 120), (cx + 86, SEAT_Y - 120), (cx + 74, SEAT_Y + 36)]
    pen.fill(back, PAPER); pen.line(back, 5, INK, 'cback', closed=True)
    pen.line([(cx, SEAT_Y + 36), (cx, FLOOR)], 6, INK, 'ped'); pen.line([(cx - 50, FLOOR), (cx + 50, FLOOR)], 6, INK, 'cbase')
    h = {}
    h['captain'] = CAPTAIN.draw(pen, t, 0, w=5.5 * SC ** .3)
    h['riker'] = RIKER.draw(pen, t, 0, w=5.5 * SC ** .3)
    h['grokbot'] = GROK.draw(pen, t, 0, w=5.5 * SC ** .3)
    tower(pen, t, h)
    if t >= T_BOX - .15: legacy_box(pen, t)
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
    """the teetering IOU tower at full height, everyone looking at it; title band below."""
    tt = LN['r1']['e'] + .4
    img, _ = bridge(tt, (960, 460, 1.0))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(420, 930, 1500, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'TECHNICAL DEBT', (960, 972), 104, 7)
    pen.line([(560, 1026), (1360, 1021)], 5, INK, 'tul')
    pen.text('the Captain \u00d7 Riker \u00d7 Grok Bot  \u00b7  STARSHIP GROKBOT', (960, 1052), 36, INK, 'hand')
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'captain': 'CAPTAIN'}; ev = []; Ls = TL['lines']
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
    out = f'{HERE}/technicaldebt.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
