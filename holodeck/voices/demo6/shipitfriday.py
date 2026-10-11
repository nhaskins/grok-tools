"""Dialogue short #6: "SHIP IT FRIDAY" - Grok Bot deploys to the warp core at 4:59 PM on a Friday; the core
sputters; "It worked on my starship."; Barclay gets on-call.   python shipitfriday.py | --frames t ... | --poster"""
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
T_PRESS = w('g1', 'core', -.05)              # Grok Bot slaps DEPLOY
T_BOOM = LN['r1']['e'] + .05                 # the core starts to sputter
T_NEVER = w('r2', 'weekend', -.05)           # counter -> NEVER, ON-CALL stamp
T_FAINT = LN['r2']['e'] + .3
CUT_R = LN['r1']['s'] - .15; CUT_B = LN['b1']['s'] - .2; CUT_G2 = LN['g2']['s'] - .15; CUT_R2 = LN['r2']['s'] - .15
KEYS = dict(
    grokbot=[(0, 'idle', 0), (w('g1', 'okay', -.15), 'thumbs', .2), (w('g1', 'deploying', -.1), 'idle+rsh=75+rel=30', .25),
             (T_PRESS, 'idle+rsh=60+rel=20+lean=6', .06), (T_PRESS + .4, 'proud', .3), (T_BOOM, 'surprise', .15),
             (w('g2', 'worry', -.15), 'palm', .2), (w('g2', 'worked', -.15), 'thumbs', .2), (T_NEVER + .3, 'idle+look_l', .3), (T_FAINT + .2, 'shrug', .25)],
    riker=[(0, 'idle+look_r', 0), (w('g1', 'four', -.1), 'idle+look_r+lookup=.4', .3), (w('r1', 'friday', -.15), 'palm', .25),
           (w('r1', 'nobody', -.15), 'point', .2), (T_BOOM, 'surprise', .15), (LN['b1']['s'] + .3, 'idle+look_l', .3),
           (w('g2', 'starship', .1), 'facepalm', .3), (LN['g2']['e'] + .2, 'idle', .3), (w('r2', 'good', -.15), 'thumbs', .25),
           (w('r2', 'weekend', -.1), 'point', .2), (T_FAINT + .3, 'idle', .3)],
    barclay=[(0, 'hunch', 0), (T_BOOM, 'nervous', .15), (w('b1', 'commander', -.15), 'present_padd', .25), (w('b1', 'noise', -.15), 'surprise', .2),
             (LN['b1']['e'] + .3, 'nervous', .3), (w('r2', 'barclay', -.05), 'hunch+mouth=1+lookup=.3', .25), (T_FAINT, 'faint', .32)],
)
NODS = dict(grokbot=[w('g2', 'starship', .05)], riker=[w('g1', 'nine', .1)], barclay=[w('r2', 'news', .1)])
SHOTS = [
    (0.0, 'eng', [(0.0, (960, 500, 1.04), 0), (w('g1', 'deploying', -.2), (1250, 480, 1.22), 1.0)]),
    (CUT_R, 'eng', [(CUT_R, (1180, 470, 1.24), 0), (T_BOOM - .05, (960, 500, 1.05), .3)]),
    (CUT_B, 'eng', [(CUT_B, (600, 500, 1.3), 0), (CUT_B, (580, 510, 1.38), 2.6)]),
    (CUT_G2, 'eng', [(CUT_G2, (1250, 480, 1.25), 0)]),
    (CUT_R2, 'eng', [(CUT_R2, (960, 500, 1.06), 0), (T_NEVER, (960, 500, 1.1), 1.5)]),
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
        if who == 'barclay' and t < T_FAINT:
            k = 2.2 if t > T_BOOM else 1.0
            P['tilt'] += k * 2.2 * math.sin(t * 2 * math.pi * 4.7); P['lsh'] += k * 3 * math.sin(t * 2 * math.pi * 6.1)
        return P
    return f

def fig(who, x, y, facing, props, **kw):
    F = Figure(who, x, y, facing, set(props), **kw)
    for k in KEYS[who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    F.mod = make_mod(who); return F

BARCLAY = fig('barclay', 580, STAND, 1, ['curly', 'badge'], scale=SC)
BARCLAY.move(T_FAINT, 560, FLOOR - 14, .32)
RIKER = fig('riker', 1220, STAND, -1, ['beard', 'badge'], scale=SC)
GROK = fig('grokbot', 1650, STAND, -1, ['robot'], scale=SC)
BTN = (1535, 640)


# ------------------------------------------------------------------ helpers
def sweat(pen, hd, R, t, t0, sid, side=1):
    u = t - t0
    if not 0 <= u < 1.4: return
    x, y = hd[0] + side * R * 1.4, hd[1] - R * .7 + R * 1.0 * ease(clamp01((u - .2) / 1.0)); k = ease_out_back(clamp01(u / .2))
    pts = [(x + 10 * k * math.sin(a) * (1 - math.cos(a)) * .6, y - 16 * k * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 24)]
    pen.fill(pts, PAPER); pen.line(pts, 3.5, INK, sid, closed=True)

def ell(c, rx, ry, n=28): return [(c[0] + rx * math.cos(a), c[1] + ry * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n)]

def sput(t): return clamp01((t - T_BOOM) / .2)    # 0 = healthy, 1 = sputtering

# ------------------------------------------------------------------ set: engineering
CORE_X, CORE_TOP = 960, 70
def core(pen, t):
    s = sput(t); r = np.random.default_rng(int(t * 24) + 3)
    jx = s * r.uniform(-7, 7); cx = CORE_X + jx
    x0, x1 = cx - 70, cx + 70
    pen.rect(x0, CORE_TOP, x1, FLOOR - 60, 6, INK, 'core', fill=PAPER)
    ix0, ix1 = cx - 34, cx + 34
    pen.rect(ix0, CORE_TOP + 10, ix1, FLOOR - 70, 3, INK, 'corein')
    span = FLOOR - 70 - (CORE_TOP + 10)
    speed = 160 if s < .5 else 160 + 260 * math.sin(t * 9) ** 2
    for k in range(7):          # glow bands cycling up the core (flicker when sick)
        y = FLOOR - 70 - ((t * speed + k * span / 7) % span)
        if s > .5 and r.random() < .35: continue
        hgt = 18 if s < .5 else r.uniform(6, 30)
        pen.rect(ix0 + 4, y - hgt / 2, ix1 - 4, y + hgt / 2, 0, fill=INK)
    for k, y in enumerate(range(CORE_TOP + 90, FLOOR - 80, 120)):    # rings
        tl = s * r.uniform(-8, 8)
        pts = [(p[0], p[1] + tl * (p[0] - cx) / 100) for p in ell((cx, y), 100, 18)]
        pen.line(pts, 5, INK, f'ring{k}', closed=True)
    base = [(cx - 130, FLOOR), (cx - 90, FLOOR - 70), (cx + 90, FLOOR - 70), (cx + 130, FLOOR)]
    pen.fill(base, PAPER); pen.line(base, 6, INK, 'cbase', closed=True)
    pen.text('WARP CORE', (cx, FLOOR - 32), 30, INK, 'marker')
    if s > 0:
        for j in range(3):      # sparks off the rings
            tb = T_BOOM + j * .23 + .5 * math.floor((t - T_BOOM) / .7)
            SETS.burst(pen, (cx + (110 if j % 2 else -110), CORE_TOP + 210 + j * 120), t, tb, 70, 10, INK, f'spk{j}{int(tb * 10)}', .35, 4)

def smoke(pen, t):
    if t < T_BOOM: return
    for j in range(7):      # puffs venting from the top of the core, drifting outward
        ph = ((t - T_BOOM) * .55 + j / 7) % 1; u = t - T_BOOM - j * .1
        if u < 0: continue
        sd = 1 if j % 2 else -1
        x = CORE_X + sd * (40 + 260 * ph) + 20 * math.sin(j * 2.1 + t * 1.3)
        y = CORE_TOP + 20 - 120 * ph + 30 * ph * ph; r = 14 + 26 * ph
        pen.circle((x, y), r, 4, INK, f'sm{j}', fill=PAPER)
    for j in range(2):      # little side puffs from ring seams
        ph = ((t - T_BOOM) * .8 + j / 2) % 1; sd = 1 if j else -1
        pen.circle((CORE_X + sd * (110 + 90 * ph), CORE_TOP + 330 + j * 120 - 40 * ph), 10 + 18 * ph, 3.5, INK, f'ss{j}', fill=PAPER)

def screen_box(pen, rect, sid, alarm):
    x0, y0, x1, y1 = rect
    pen.rect(x0 - 12, y0 - 12, x1 + 12, y1 + 12, 5, INK, sid + 'f')
    pen.rect(x0, y0, x1, y1, 0, fill=INK)
    if alarm:   # flashing hazard ticks around the frame
        for k in range(int((x1 - x0) / 60)):
            xx = x0 + 20 + k * 60; pen.line([(xx, y0 - 24), (xx + 26, y0 - 40)], 6, INK, f'{sid}hz{k}')

LEFT = (60, 100, 760, 430); RIGHT = (1150, 100, 1850, 430)
def clock_screen(pen, t):
    al = sput(t) > 0 and int(t * 4) % 2 == 0
    screen_box(pen, LEFT, 'ls', al)
    x0, y0, x1, y1 = LEFT; cx = (x0 + x1) / 2
    pen.text('FRI  4:59 PM', (cx, y0 + 70), 72, PAPER, 'marker')
    pen.text('MINUTES UNTIL WEEKEND:', (cx, y0 + 170), 46, PAPER, 'marker')
    if t < T_NEVER: pen.text('1', (cx, y0 + 260), 96, PAPER, 'marker')
    else:
        k = ease_out_back(clamp01((t - T_NEVER) / .25))
        pen.text('NEVER', (cx, y0 + 262), 96 * k + 1, PAPER, 'marker')

def deploy_screen(pen, t):
    s = sput(t); al = s > 0 and int(t * 4) % 2 == 1
    screen_box(pen, RIGHT, 'rs', al)
    x0, y0, x1, y1 = RIGHT; cx = (x0 + x1) / 2
    if t < T_BOOM:
        pen.text('DEPLOY -> WARP CORE', (cx, y0 + 60), 50, PAPER, 'marker')
        lv = ease(clamp01((t - T_PRESS) / (T_BOOM - T_PRESS - .1))) if t > T_PRESS else 0
        pen.rect(x0 + 50, y0 + 120, x1 - 50, y0 + 190, 5, PAPER, 'pbar')
        if lv > .01: pen.rect(x0 + 58, y0 + 128, x0 + 58 + (x1 - x0 - 116) * lv, y0 + 182, 0, fill=PAPER)
        pen.text(f'{lv * 100:.0f}%', (cx, y0 + 250), 64, PAPER, 'marker')
    else:
        pen.text('WARP CORE: ?!?', (cx, y0 + 60), 56, PAPER, 'marker')
        k = ease_out_back(clamp01((t - T_BOOM - .3) / .25))
        if k > .02:
            bw, bh = 240 * k, 62 * k
            pen.rect(cx - bw, y0 + 200 - bh, cx + bw, y0 + 200 + bh, 6, PAPER, 'rb', fill=INK if int(t * 3) % 2 else None)
            pen.text('ROLLBACK?', (cx, y0 + 200), 74 * k + 1, PAPER, 'marker')
    if t > T_NEVER: SETS.stamp(pen, 'ON-CALL: LT. BARCLAY', (cx, y0 + 200), t, T_NEVER + .15, 52)

def button(pen, t):
    bx, by = BTN; press = 0.0
    if T_PRESS <= t < T_PRESS + .4: press = math.sin(math.pi * clamp01((t - T_PRESS) / .4))
    ped = [(bx - 40, by + 14), (bx + 40, by + 14), (bx + 62, FLOOR), (bx - 62, FLOOR)]
    pen.fill(ped, PAPER); pen.line(ped, 5, INK, 'ped', closed=True)
    pen.rect(bx - 52, by + 6, bx + 52, by + 18, 4, INK, 'rim', fill=PAPER)
    dome = [(bx + 40 * math.cos(a), by + 6 - (30 - 18 * press) * math.sin(a)) for a in np.linspace(0, math.pi, 18)]
    pen.fill(dome, INK); pen.line(dome, 4, INK, 'dome')
    pen.rect(bx - 95, 745, bx + 95, 815, 4, INK, 'bplate', fill=PAPER); pen.text('DEPLOY', (bx, 780), 40, INK, 'marker')
    if T_PRESS <= t < T_PRESS + .6: SETS.burst(pen, (bx, by - 10), t, T_PRESS, 80, 12, INK, 'pressb', .5, 4)

def eng(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    for y in (480, 505): pen.line([(-600, y), (2500, y)], 3, INK, f'pipe{y}', wob=.6)
    pen.text('ENGINEERING', (410, 40), 36, INK, 'marker')
    clock_screen(pen, t); deploy_screen(pen, t)
    core(pen, t); button(pen, t)
    console(pen, 70, 400, 712, sid='engc', mirror=True)
    pen.rect(40, 650, 440, 700, 4, INK, 'plate', fill=PAPER); pen.text('LT. BARCLAY // ENGINEERING', (240, 675), 22, INK, 'marker')
    hands = {n: F.draw(pen, t, 0, w=5.5 * SC ** .3) for n, F in (('barclay', BARCLAY), ('riker', RIKER), ('grokbot', GROK))}
    smoke(pen, t)
    b = hands['barclay']
    sweat(pen, b['head'], b['R'], t, T_BOOM + .1, 'sw1', side=-1)
    sweat(pen, b['head'], b['R'], t, T_NEVER, 'sw2', side=-1)
    if t > T_FAINT + .1:
        SETS.stamp(pen, 'WEEKEND: CANCELLED', (600, 600), t, T_FAINT + .2, 44)
    return img, hands

SETFN = {'eng': eng}


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
    """the core sputtering with ROLLBACK? up, clock at 4:59, everyone reacting; title band below."""
    tt = T_BOOM + .9
    img, _ = eng(tt, (960, 480, 1.0))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(380, 930, 1540, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'SHIP IT FRIDAY', (960, 972), 104, 7)
    pen.line([(560, 1026), (1360, 1021)], 5, INK, 'tul')
    pen.text('Grok Bot  \u00d7  Riker  \u00d7  featuring Lt. Barclay', (960, 1052), 36, INK, 'hand')
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
    out = f'{HERE}/shipitfriday.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
