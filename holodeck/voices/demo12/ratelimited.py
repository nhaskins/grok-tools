"""Dialogue short #12: "RATE LIMITED" - Picard's "make it so" hits 429 TOO MANY REQUESTS; Grok Bot, bouncer at the
velvet rope, hands out numbers; Picard spams retries (queue: 47); the limit resets and the ship executes all 47 at once.
    python ratelimited.py | --frames t ... | --poster"""
import sys, os, json, math, subprocess, time
SP = '/workspace/holodeck/titan-hello-world/stick-poc'; sys.path.insert(0, SP)
import numpy as np, cv2
cv2.setNumThreads(1)
from stickfig import *
from inkset import W, H, FLOOR, console, paper_finish, sparkle, stars_field, ship
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

def wf(line, word, frac, off=0.0):      # word time, or a fraction through the line if whisper spelled it differently
    try: return w(line, word, off)
    except KeyError: L = LN[line]; return L['s'] + frac * (L['e'] - L['s']) + off

# ------------------------------------------------------------------ cue table
SC = 1.4; STAND = FLOOR - 110 * SC
T_429 = wf('p1', 'so', .9, .15)                         # first order bounces
T_TICK = wf('g1', 'take', .7, -.05)                  # dispenser spits ticket #48
P2S, P2E = LN['p2']['s'], LN['p2']['e']
T_RESET = wf('g2', 'reset', .3, -.05)
T_FLUSH = wf('g2', 'once', .9, -.1)                     # ...all 47 at once
T_FP = LN['r1']['e'] + .02                             # facepalm punch-in (2/3-frame close-up + hold)
CUT_G1 = LN['g1']['s'] - .15; CUT_P2 = P2S - .15; CUT_R1 = LN['r1']['s'] - .15; CUT_G2 = LN['g2']['s'] - .15
KEYS = dict(
    picard=[(0, 'idle', 0), (wf('p1', 'course', .2, -.1), 'point', .3), (T_429 + .1, 'surprise', .15), (T_429 + .7, 'idle', .3),
            (CUT_G1 + 1.2, 'hips', .3), (P2S - .05, 'point', .2), (P2S + .25 * (P2E - P2S), 'idle+rsh=40+rel=60', .15),
            (P2S + .4 * (P2E - P2S), 'point', .15), (P2S + .7 * (P2E - P2S), 'pointup', .15), (P2E + .2, 'hips', .3),
            (T_FP + .04, 'facepalm', .18), (T_RESET, 'idle', .3), (T_FLUSH, 'faint', .25)],
    grokbot=[(0, 'idle+look_l', 0), (T_429, 'palm', .2), (wf('g1', 'please', .6, -.1), 'idle+look_l', .3),
             (wf('g1', 'take', .7, -.05), 'present', .25), (LN['g1']['e'] + .3, 'idle+look_l', .3), (P2S + .3, 'palm', .2),
             (P2E + .3, 'idle+look_l', .3), (T_RESET - .1, 'tada', .25), (T_FLUSH, 'surprise', .15)],
    riker=[(0, 'idle+look_l', 0), (T_429 + .2, 'chinrub', .3), (P2S + .5, 'idle+look_l', .3), (LN['r1']['s'] - .1, 'palm', .25),
           (LN['r1']['e'] + .3, 'idle+look_l', .3), (T_FLUSH, 'surprise', .15)],
)
NODS = dict(picard=[], grokbot=[wf('g1', 'sorry', .1, .05)], riker=[wf('r1', 'slower', .9, .05)])

def queued(t):
    if t < T_429: return 0
    if t < P2S: return 1
    if t < P2E + .2: return 1 + int(46 * clamp01((t - P2S) / (P2E - P2S)) ** 1.4 + .5)
    if t < T_FLUSH: return 47
    return max(0, 47 - int((t - T_FLUSH) / .9 * 47))

def retry_after(t):
    if t < T_429: return None
    if t < P2E: return 30                                   # every retry resets the timer
    return int(math.ceil(30 * (1 - clamp01((t - P2E) / (T_RESET - P2E)))))

SHOTS = [
    (0.0, 'bridge', [(0.0, (960, 520, 1.0), 0), (0.0, (900, 500, 1.05), LN['p1']['e'])]),
    (CUT_G1, 'bridge', [(CUT_G1, (1150, 470, 1.25), 0)]),
    (CUT_P2, 'bridge', [(CUT_P2, (620, 470, 1.25), 0), (CUT_P2, (660, 460, 1.32), P2E - P2S)]),
    (CUT_R1, 'bridge', [(CUT_R1, (1250, 480, 1.2), 0)]),
    (T_FP, 'bridge', [(T_FP, (690, 735, 2.0), 0), (T_FP + .3, (690, 728, 2.06), .7)]),   # Picard ~2/3 of frame height
    (CUT_G2, 'bridge', [(CUT_G2, (960, 520, 1.0), 0)]),
]
SHOTS = [dict(at=a, set=s, cam=c) for a, s, c in SHOTS]
for i, s in enumerate(SHOTS): s['end'] = SHOTS[i + 1]['at'] if i + 1 < len(SHOTS) else 1e9

def shake(t): return 0 if t < T_FLUSH else 14 * math.exp(-(t - T_FLUSH) * 1.2)

def make_mod(who):
    env = ENV.get(who, np.zeros(1)); nods = NODS.get(who, [])
    def f(t, P):
        i = int(t * FPS); e = float(env[i]) if i < len(env) else 0.0
        e2 = float(env[max(i - 2, 0)]) if i < len(env) else 0.0
        P['talk'] = e; P['tilt'] += 7 * (e - e2) + 3 * e; P['lean'] += 2.5 * e * (1 - P['front'])
        for tn in nods:
            u = t - tn
            if 0 <= u < .7: P['tilt'] += 12 * math.sin(math.pi * u / .35) * (1 - u / .7)
        if who == 'picard' and P2S < t < P2E:               # stomps with each retry
            P['lean'] += 6 * abs(math.sin((t - P2S) * 2 * math.pi * 1.1))
        sk = shake(t)
        if sk > 1: P['lean'] += sk * .9 * math.sin(t * 23 + len(who)); P['tilt'] += sk * math.sin(t * 17)
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
        if v > 40 and abs(y1 - y0) < 3:
            a = min(v / 400, 1); ph = math.sin(t * 2 * math.pi * 2.4)
            P['lhip'] += 26 * a * ph; P['rhip'] -= 26 * a * ph
            P['lkn'] -= 22 * a * max(-ph, 0); P['rkn'] -= 22 * a * max(ph, 0)
            P['lsh'] -= 16 * a * ph; P['rsh'] += 16 * a * ph
        return P
    F.mod = mod; return F

PIC = fig('picard', 330, STAND, 1, ['shine', 'badge', 'collar'], scale=SC)
PIC.move(.25, 600, STAND, 1.0); PIC.move(P2S, 680, STAND, .5)
GROK = fig('grokbot', 960, STAND, -1, ['robot'], scale=SC)
RIKER = fig('riker', 1640, STAND, -1, ['beard', 'badge'], scale=SC)
RIKER.move(LN['r1']['s'] - .4, 1520, STAND, .7)

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

# ------------------------------------------------------------------ set: Titan bridge, velvet rope
VS = (560, 100, 1360, 470)
def ticket(pen, c, s, txt, sid, ang=0.0, sub=None):
    x, y = c; ca, sa = math.cos(ang), math.sin(ang)
    R_ = lambda dx, dy: (x + dx * ca - dy * sa, y + dx * sa + dy * ca)
    pts = [R_(-112 * s, -30 * s), R_(112 * s, -30 * s), R_(112 * s, 30 * s), R_(-112 * s, 30 * s)]
    pen.fill(pts, PAPER); pen.line(pts, 3.5, INK, sid, closed=True)
    pen.circle(R_(-112 * s, 0), 8 * s, 2.5, INK, sid + 'n1', fill=PAPER); pen.circle(R_(112 * s, 0), 8 * s, 2.5, INK, sid + 'n2', fill=PAPER)
    pen.text(txt, R_(0, -6 * s if sub else 0), int((30 if sub else 28) * s), INK, 'marker')
    if sub: pen.text(sub, R_(0, 19 * s), int(22 * s), INK, 'hand')

def bridge(t, cam):
    sk = shake(t)
    cam = (cam[0] + sk * math.sin(t * 41), cam[1] + sk * math.cos(t * 37), cam[2])
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    # viewscreen
    x0, y0, x1, y1 = VS; vc = (x0 + x1) / 2
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    fl = t >= T_FLUSH
    stars_field(sp, VS, t, 900 if fl else 60, streak=.9 if fl else 0)
    if fl:                                                   # 47 trips to Risa, all at once
        u = t - T_FLUSH
        for k in range(3):
            ph = u * 5.5 + k * 2.1
            ship(sp, (vc + 300 * math.sin(ph), (y0 + y1) / 2 + 90 * math.sin(2 * ph)), .55, PAPER, INK, f'zip{k}', facing=1 if math.cos(ph) > 0 else -1)
        sp.circle((x1 - 120, y1 - 90), 60, 4, PAPER, 'risa')
        sp.text('RISA', (x1 - 120, y1 - 90), 30, PAPER, 'marker')
        n = min(47, int(u / .9 * 47) + 1)
        sp.rect(vc - 290, y0 + 20, vc + 290, y0 + 92, 0, fill=INK)
        sp.text(f'MAKE IT SO  x{n}', (vc, y0 + 56), 58, PAPER, 'marker')
    elif t >= T_429:
        sp.rect(vc - 330, y0 + 40, vc + 330, y1 - 40, 0, fill=INK)
        sp.text('429', (vc, y0 + 135), 150, PAPER, 'marker')
        sp.text('TOO MANY REQUESTS', (vc, y0 + 240), 56, PAPER, 'marker')
        ra = retry_after(t)
        sp.text(f'Retry-After: {ra} seconds', (vc, y0 + 308), 48, PAPER, 'hand')
        if t >= T_RESET - .05: sp.text('RESET!', (vc, y1 - 30), 40, PAPER, 'marker')
    else:
        ship(sp, (vc, (y0 + y1) / 2), .7, PAPER, INK, 'ship', facing=1)
    clip_paste(img, sub, pen, VS)
    if T_429 <= t < T_429 + 1.0: SETS.burst(pen, (vc, (y0 + y1) / 2), t, T_429, 300, n=14, sid='b429')
    pen.text('U.S.S. TITAN', (1640, 140), 40, INK, 'marker')
    # retry queue board on the left wall
    qx0, qy0, qx1, qy1 = 70, 110, 470, 620
    pen.rect(qx0, qy0, qx1, qy1, 5, INK, 'qboard', fill=PAPER)
    pen.text('RETRY QUEUE', ((qx0 + qx1) / 2, qy0 + 40), 44, INK, 'marker')
    pen.line([(qx0 + 30, qy0 + 72), (qx1 - 30, qy0 + 70)], 3, INK, 'qul')
    n = queued(t)
    for j in range(min(n, 5)):
        ty = qy0 + 125 + j * 72
        if fl:                                               # tickets fly off as the queue flushes
            ty -= 0; 
        ticket(pen, ((qx0 + qx1) / 2 + 8 * math.sin(j * 1.7), ty), 1.0, 'MAKE IT SO', f'qt{j}', ang=.04 * math.sin(j * 2.3))
    if n > 5: pen.text(f'+{n - 5} more', ((qx0 + qx1) / 2, qy1 - 22), 34, INK, 'hand')
    pen.text(f'QUEUED: {n}', ((qx0 + qx1) / 2, qy1 + 45), 46, INK, 'marker')
    if fl:                                                   # flushed tickets flutter up and away
        for j in range(10):
            u = (t - T_FLUSH) * 1.4 - j * .08
            if 0 < u < 1.4:
                ticket(pen, (270 + 160 * u * math.sin(j * 3), 420 - 700 * u + 60 * math.cos(j * 2)), .6, 'MAKE IT SO', f'fl{j}', ang=u * 3 + j)
    # velvet rope: posts + droopy rope
    posts = (800, 1120); ptop = FLOOR - 170
    for k, px in enumerate(posts):
        pen.line([(px, FLOOR), (px, ptop)], 8, INK, f'post{k}'); pen.circle((px, ptop - 12), 14, 4, INK, f'pk{k}', fill=INK)
        pen.line([(px - 30, FLOOR - 4), (px + 30, FLOOR - 4)], 8, INK, f'pb{k}')
    rope = [(lerp(posts[0], posts[1], u), ptop + 10 + 70 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 16)]
    if T_RESET <= t:                                         # rope unhooked: hangs from the right post
        rope = [(posts[1] - 60 * math.sin(u * 1.3), ptop + 10 + 140 * u) for u in np.linspace(0, 1, 10)]
    pen.line(rope, 9, INK, 'rope'); pen.line(rope, 3, PAPER, 'ropeh')
    # TAKE A NUMBER dispenser on a stand
    dx = 1250; dy = FLOOR - 260
    pen.line([(dx, FLOOR), (dx, dy + 60)], 7, INK, 'dstand'); pen.line([(dx - 40, FLOOR - 3), (dx + 40, FLOOR - 3)], 7, INK, 'dbase')
    pen.circle((dx, dy), 62, 5, INK, 'disp', fill=PAPER)
    pen.text('TAKE A', (dx, dy - 16), 24, INK, 'marker'); pen.text('NUMBER', (dx, dy + 14), 24, INK, 'marker')
    if t >= T_TICK:
        k = ease_out_back(clamp01((t - T_TICK) / .3))
        ticket(pen, (dx + 30 + 100 * k, dy + 40 + 80 * k), 1.0, 'YOU ARE #48', 'tk48', ang=.12 * k, sub='now serving: #1')
    h = {}
    h['riker'] = RIKER.draw(pen, t, 0, w=5.5 * SC ** .3)
    h['grokbot'] = GROK.draw(pen, t, 0, w=5.5 * SC ** .3)
    h['picard'] = PIC.draw(pen, t, 0, w=5.5 * SC ** .3)
    # retry speech tags flying out of Picard on each "make it so"
    if P2S <= t < P2E + .3:
        ph = h['picard']['head']
        for j, fr in enumerate((.02, .3, .62)):
            ta = P2S + fr * (P2E - P2S); u = t - ta
            if 0 <= u < .8:
                pen.text(f'retry #{j + 2}' if j < 2 else 'retry #47', (ph[0] + 80 + 160 * u, ph[1] - 90 - 40 * j), 34, INK, 'hand')
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
    """the 429 slammed on the viewscreen, queue board full, Picard pointing; title band below."""
    tt = P2E - .1
    img, _ = bridge(tt, (900, 470, 1.0))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(440, 930, 1480, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'RATE LIMITED', (960, 972), 104, 7)
    pen.line([(580, 1026), (1340, 1021)], 5, INK, 'tul')
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
    out = f'{HERE}/ratelimited.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
