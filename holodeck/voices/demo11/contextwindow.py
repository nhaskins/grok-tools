"""Dialogue short #11: "CONTEXT WINDOW" - after a 400-page briefing Grok Bot has forgotten the mission; Barclay draws
him a bigger head (it bonks the ceiling); now he remembers Riker's poetry, so Barclay shrinks it... too far.
    python contextwindow.py | --frames t ... | --poster"""
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
SC = 1.4; STAND = FLOOR - 110 * SC
T_ASK = w('c1', 'grok', -.15)
T_FULL = w('g1', 'full', -.05)                         # gauge hits 100%, page 1 falls off
T_Q = w('g1', 'what', -.05)
T_WALK_B = LN['g1']['e'] - .5                          # Barclay strides in with the giant stylus
T_DRAW0 = LN['b1']['e'] + .05; T_DRAW1 = T_DRAW0 + 1.0  # scribble -> head inflates
T_BONK = T_DRAW1 - .1
T_POEM = w('g2', 'poetry', -.3)
T_SHRINK0 = w('r1', 'smaller', 0); T_SHRINK1 = T_SHRINK0 + .7
CUT_G1 = LN['g1']['s'] - .15; CUT_B1 = LN['b1']['s'] - .2; CUT_DRAW = T_DRAW0 - .1; CUT_G2 = LN['g2']['s'] - .15
CUT_R1 = LN['r1']['s'] - .15
POINT = 'idle+rsh=105+rel=-5'
KEYS = dict(
    captain=[(0, POINT, 0), (w('c1', 'concludes', -.1), POINT + '+mouth=1', .2), (w('c1', 'briefing', 0), 'idle+rsh=60+rel=60', .3),
             (T_ASK, 'palm', .25), (LN['c1']['e'] + .3, 'idle', .3), (T_Q + .2, 'chinrub', .3),
             (T_BONK, 'surprise', .15), (T_BONK + .8, 'idle', .3), (T_POEM + .3, 'idle+look_l', .3), (T_SHRINK1, 'surprise', .15)],
    grokbot=[(0, 'idle+look_l', 0), (T_ASK + .2, 'idle', .3), (w('g1', 'my', -.1), 'pointup', .25), (T_Q, 'shrug', .25),
             (CUT_B1 + .2, 'idle', .3), (T_DRAW0, 'surprise', .2), (T_BONK + .2, 'shrug', .3), (w('g2', 'remember', -.15), 'cheer', .3),
             (T_POEM, 'pointup', .25), (LN['g2']['e'] + .3, 'idle', .3), (T_SHRINK1, 'surprise', .2)],
    barclay=[(0, 'hunch', 0), (w('b1', 'worry', -.15), 'present_padd', .25), (T_DRAW0 - .15, 'idle+rsh=110+rel=20', .2),
             (T_DRAW0, 'scribble+rsh=110', .15), (T_DRAW1, 'proud', .3), (w('r1', 'barclay', 0), 'nervous', .2),
             (T_SHRINK0 - .1, 'scribble+rsh=110', .15), (T_SHRINK1, 'nervous+mouth=3', .2)],
    riker=[(0, 'idle+look_r', 0), (T_Q + .1, 'chinrub', .3), (T_BONK, 'surprise', .15), (T_BONK + .7, 'idle+look_r', .3),
           (T_POEM, 'facepalm', .25), (w('r1', 'barclay', -.15), 'point', .25), (T_SHRINK1 + .1, 'facepalm', .3)],
)
NODS = dict(captain=[w('c1', 'mission', .05)], grokbot=[], barclay=[w('b1', 'head', .05)], riker=[])

def head_scale(t):
    if t < T_DRAW0: return 1.0
    if t < T_SHRINK0:
        u = clamp01((t - T_DRAW0) / (T_DRAW1 - T_DRAW0))
        hs = 1 + 6.8 * ease(u) + .35 * math.sin(u * 22) * (1 - u)       # inflates in pen-stroke spurts
        if t > T_BONK: hs -= .5 * math.exp(-(t - T_BONK) * 7) * abs(math.sin((t - T_BONK) * 30))  # squash on the bonk
        return hs
    u = clamp01((t - T_SHRINK0) / (T_SHRINK1 - T_SHRINK0))
    return lerp(7.8, .38, ease(u))

SHOTS = [
    (0.0, 'brief', [(0.0, (960, 520, 1.0), 0), (0.0, (900, 500, 1.06), LN['c1']['e'])]),
    (CUT_G1, 'brief', [(CUT_G1, (1250, 470, 1.3), 0)]),
    (CUT_B1, 'brief', [(CUT_B1, (1450, 560, 1.15), 0)]),
    (CUT_DRAW, 'brief', [(CUT_DRAW, (1300, 500, 1.0), 0)]),
    (CUT_G2, 'brief', [(CUT_G2, (1100, 470, 1.0), 0)]),
    (CUT_R1, 'brief', [(CUT_R1, (1000, 520, 1.0), 0), (T_SHRINK1, (1350, 560, 1.25), .6)]),
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
        if who == 'grokbot':
            P['hs'] = head_scale(t)
            if P['hs'] > 2: P['tilt'] *= .3; P['lean'] += 3 * math.sin(t * 3)     # wobbly under the weight
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
        if v > 40 and abs(y1 - y0) < 3:        # stride while walking
            a = min(v / 400, 1); ph = math.sin(t * 2 * math.pi * 2.4)
            P['lhip'] += 26 * a * ph; P['rhip'] -= 26 * a * ph
            P['lkn'] -= 22 * a * max(-ph, 0); P['rkn'] -= 22 * a * max(ph, 0)
            P['lsh'] -= 16 * a * ph; P['rsh'] += 16 * a * ph
        return P
    F.mod = mod; return F

CAPT = fig('captain', 1250, STAND, -1, ['cap', 'badge'], scale=SC)
CAPT.move(.3, 1180, STAND, .7); CAPT.move(T_ASK - .1, 1120, STAND, .5)
RIKER = fig('riker', 170, STAND, 1, ['beard', 'badge'], scale=SC)
RIKER.move(w('r1', 'barclay', -.3), 420, STAND, .6)
GROK = fig('grokbot', 1500, STAND, -1, ['robot'], scale=SC)
BARC = fig('barclay', 2150, STAND, -1, ['curly', 'badge'], scale=SC)
BARC.move(T_WALK_B, 1790, STAND, 1.1)

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

# ------------------------------------------------------------------ set: briefing room
SCR = (200, 150, 940, 600); CEIL = 110
BRIEF = ['PAGE 1: THE MISSION IS TO', 'deliver the tea to Starbase 9', 'PAGE 2: about the tea...', 'page 37: more tea facts',
         'page 112: tea, continued', 'page 250: appendix (tea)', 'page 399: closing remarks', 'page 400: any questions?']
def ctx_level(t):
    return min(.86 + .14 * clamp01(t / max(T_FULL, .1)), 1.0)

def brief(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen)
    pen.line([(-700, CEIL), (2600, CEIL)], 6, INK, 'ceil')
    for k in range(-6, 26): pen.line([(k * 110, CEIL), (k * 110 - 30, CEIL - 60)], 2.5, INK, f'ch{k}', wob=.4)
    pen.text('BRIEFING ROOM', (1600, CEIL + 50), 40, INK, 'marker')
    # long table
    pen.line([(120, 760), (960, 760)], 7, INK, 'tbl'); pen.line([(180, 760), (180, FLOOR)], 6, INK, 'tl1'); pen.line([(900, 760), (900, FLOOR)], 6, INK, 'tl2')
    for j in range(5): pen.rect(220 + j * 145, 730, 310 + j * 145, 758, 3, INK, f'pad{j}', fill=PAPER)
    # the screen: scrolling briefing; the oldest line falls off when the context fills up
    x0, y0, x1, y1 = SCR
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'sframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    sp.text('MISSION BRIEFING', (x0 + 30, y0 + 40), 40, PAPER, 'marker', anchor='l')
    sp.text('PAGE 400 of 400', (x1 - 30, y0 + 40), 30, PAPER, 'marker', anchor='r')
    sp.line([(x0 + 24, y0 + 72), (x1 - 24, y0 + 70)], 3, PAPER, 'sul')
    for j, ln in enumerate(BRIEF):
        y = y0 + 112 + j * 52
        if j < 2 and t > T_FULL:                       # page 1 drops out of the window
            u = t - T_FULL - .12 * j
            if u > 0: y += 900 * u * u; 
            sp.text(ln, (x0 + 40 + 30 * max(u, 0), y), 32, PAPER, 'hand', anchor='l')
            continue
        sp.text(ln, (x0 + 40, y), 32, PAPER, 'hand', anchor='l')
    clip_paste(img, sub, pen, SCR)
    # context gauge on the wall
    gx0, gy0, gx1, gy1 = 990, 200, 1070, 600
    pen.rect(gx0, gy0, gx1, gy1, 5, INK, 'gauge', fill=PAPER)
    if t < T_DRAW1:
        lv = ctx_level(t)
        pen.rect(gx0 + 6, gy1 - 6 - (gy1 - gy0 - 12) * lv, gx1 - 6, gy1 - 6, 0, fill=INK)
        lab = 'CONTEXT 100% FULL' if t >= T_FULL else f'CONTEXT {lv * 100:.0f}%'
    else:
        lab = 'CONTEXT: 2M TOKENS' if t < T_SHRINK1 else 'CONTEXT: 8 TOKENS'
        lv = .25 if t < T_SHRINK1 else .99
        pen.rect(gx0 + 6, gy1 - 6 - (gy1 - gy0 - 12) * lv, gx1 - 6, gy1 - 6, 0, fill=INK)
    lw = 10 + 17 * len(lab)
    pen.rect((gx0 + gx1) / 2 - lw / 2, gy0 - 54, (gx0 + gx1) / 2 + lw / 2, gy0 - 8, 3, INK, 'glab', fill=PAPER)
    pen.text(lab, ((gx0 + gx1) / 2, gy0 - 30), 30, INK, 'marker')
    if T_FULL <= t < T_FULL + 1.2: SETS.stamp(pen, 'FULL', ((gx0 + gx1) / 2, (gy0 + gy1) / 2), t, T_FULL, 34, sid='gfull')
    h = {}
    h['riker'] = RIKER.draw(pen, t, 0, w=5.5 * SC ** .3)
    h['captain'] = CAPT.draw(pen, t, 0, w=5.5 * SC ** .3)
    h['barclay'] = BARC.draw(pen, t, 0, w=5.5 * SC ** .3)
    h['grokbot'] = GROK.draw(pen, t, 0, w=5.5 * SC ** .3)
    # Captain's pointer while briefing
    P = CAPT.pose_at(t)
    if P['rsh'] > 95:
        hx, hy = h['captain']['hand_r']; pen.line([(hx, hy), (hx - 150, hy - 40)], 4, INK, 'ptr')
    # Grok Bot's question marks
    gh = h['grokbot']['head']; R = h['grokbot']['R']
    if T_Q <= t < CUT_B1 + .6:
        for j in range(3):
            k = ease_out_back(clamp01((t - T_Q - .12 * j) / .25))
            if k > 0: pen.text('?', (gh[0] - 90 + 90 * j, gh[1] - R - 60 - 18 * (j % 2)), 64 * k + 1, INK, 'marker')
    # Barclay's giant stylus + scribble marks on the head
    bh = h['barclay']['hand_r']
    if t > T_WALK_B:
        tip = (bh[0] - 150, bh[1] - 110)
        pen.line([bh, tip], 14, INK, 'sty'); pen.line([(bh[0] + 18, bh[1] + 14), bh], 14, INK, 'sty2')
        pen.line([tip, (tip[0] - 16, tip[1] - 12)], 6, INK, 'stytip')
    for (a, b) in ((T_DRAW0, T_DRAW1), (T_SHRINK0, T_SHRINK1)):
        if a <= t < b + .3:
            for j in range(6):
                ang = t * 20 + j * 1.1; rr = R * (.7 + .25 * math.sin(j * 2.3))
                if (t - a) * 6 > j: pen.line([(gh[0] + rr * math.cos(ang), gh[1] + rr * math.sin(ang)),
                                              (gh[0] + rr * math.cos(ang + .7), gh[1] + rr * math.sin(ang + .7))], 3, INK, f'scr{j}')
    if T_BONK <= t < T_BONK + 1.0:
        k = ease_out_back(clamp01((t - T_BONK) / .2))
        pen.text('BONK!', (gh[0] + 40, CEIL - 50), 84 * k + 1, INK, 'marker')
        SETS.burst(pen, (gh[0], CEIL + 8), t, T_BONK, 120, n=12, sid='bonkb')
    if T_POEM <= t < T_SHRINK0 + .2:                       # what he remembers now
        k = ease_out_back(clamp01((t - T_POEM) / .3))
        bx, by = 640, 380
        pen.rect(bx - 210 * k, by - 95 * k, bx + 210 * k, by + 95 * k, 5, INK, 'poem', fill=PAPER)
        if k > .8:
            pen.text("RIKER'S POETRY", (bx, by - 50), 40, INK, 'marker')
            pen.text('"Ode to My Trombone"', (bx, by + 5), 34, INK, 'hand'); pen.text('(47 verses)', (bx, by + 52), 32, INK, 'hand')
            pen.line([(bx + 210, by), (gh[0] - R, gh[1] - R * .2)], 3, INK, 'poemptr', wob=.5)
    if t >= T_SHRINK1:
        pen.text('oops.', (1790, 380), 46, INK, 'hand')
        k = clamp01((t - T_SHRINK1 - .15) / .25)
        if k > 0:
            pen.text('(head)', (gh[0] - 150, gh[1] - 90), 40 * k + 1, INK, 'hand')
            pen.line([(gh[0] - 110, gh[1] - 66), (gh[0] - 14, gh[1] - 10)], 3, INK, 'harr')
            pen.line([(gh[0] - 14, gh[1] - 10), (gh[0] - 34, gh[1] - 14)], 3, INK, 'harr2'); pen.line([(gh[0] - 14, gh[1] - 10), (gh[0] - 22, gh[1] - 30)], 3, INK, 'harr3')
    return img, h

SETFN = {'brief': brief}


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
    """the giant head bonking the ceiling, context label; title band below."""
    tt = T_BONK + .35
    img, _ = brief(tt, (1150, 480, .98))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(420, 930, 1500, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'CONTEXT WINDOW', (960, 972), 100, 7)
    pen.line([(560, 1026), (1360, 1021)], 5, INK, 'tul')
    pen.text('Grok Bot \u00d7 Barclay \u00d7 the Captain \u00d7 Riker  \u00b7  STARSHIP GROKBOT', (960, 1052), 34, INK, 'hand')
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'barclay': 'BARCLAY', 'captain': 'CAPTAIN'}; ev = []; Ls = TL['lines']
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
    out = f'{HERE}/contextwindow.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
