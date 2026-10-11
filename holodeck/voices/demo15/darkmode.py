"""Dialogue short #15: "DARK MODE" - Barclay ships a dark mode nobody tested: ink on black, so everyone vanishes and only
the outlined text survives. Grok Bot fixes the contrast with alt text; the switch back is a flashbang. Box-only (Piper voices).
    python darkmode.py | --frames t ... | --poster"""
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
T_DARK = we('b1', 'eyes', 0, .12)                      # CLICK: dark mode on
T_BONK = wt('r1', 'where', 0, -.15)                    # Riker walks into Grok Bot in the dark
T_ALT = we('g1', 'text', 0, .05)                       # alt-text labels start popping
T_LIGHT = LN['p1']['e'] + .3                           # CLICK back: flashbang
T_SHADES = LN['g2']['s'] - .05
CUT_R1 = LN['r1']['s'] - .15; CUT_P1 = LN['p1']['s'] - .15; CUT_G2 = LN['g2']['s'] - .15
def dark(t):
    if t < T_DARK or t >= T_LIGHT: return False
    u = t - T_DARK                                       # fluorescent-tube flicker on the way in
    return not (.08 <= u < .14 or .2 <= u < .24)

KEYS = dict(
    barclay=[(0, 'hunch', 0), (wt('b1', 'gave', 0, -.1), 'present_padd', .25), (wt('b1', 'easier', 0, -.2), 'point+rsh=60', .2),
             (T_DARK - .05, 'proud', .2), (CUT_P1, 'nervous', .25), (T_LIGHT - .2, 'point+rsh=60', .15), (T_LIGHT + .1, 'facepalm', .15),
             (T_SHADES + 1.2, 'nervous', .3)],
    riker=[(0, 'idle+look_l', 0), (LN['r1']['s'], 'idle+lsh=60+lel=10+rsh=70+rel=10', .3), (T_BONK + .02, 'surprise', .1),
           (T_BONK + .5, 'idle+look_l', .3), (T_LIGHT + .05, 'facepalm', .15), (T_SHADES + 1.0, 'idle+look_l', .3)],
    picard=[(0, 'idle+look_l', 0), (CUT_P1, 'hips', .3), (wt('p1', 'turn', 0, -.1), 'point', .2), (T_LIGHT + .04, 'facepalm', .12)],
    grokbot=[(0, 'idle+look_l', 0), (LN['g1']['s'] - .1, 'palm', .25), (T_ALT - .1, 'present', .2), (LN['g1']['e'] + .6, 'idle+look_l', .3),
             (T_SHADES, 'tada', .25), (LN['g2']['e'] + .2, 'idle+thumb=1+rsh=50+rel=-60', .3)],
)
NODS = dict(barclay=[LN['b1']['s'] + .05], riker=[LN['r1']['s'] + .05], picard=[wt('p1', 'now', 0, .02)], grokbot=[LN['g1']['s'] + .05, LN['g2']['s'] + .05])

SHOTS = [
    (0.0, [(0.0, (960, 520, 1.0), 0), (0.0, (760, 500, 1.12), T_DARK - .3)]),
    (CUT_R1, [(CUT_R1, (1000, 500, 1.08), 0)]),
    (CUT_P1, [(CUT_P1, (960, 520, 1.0), 0), (CUT_P1, (900, 505, 1.05), LN['p1']['e'] - CUT_P1)]),
    (T_LIGHT + .05, [(T_LIGHT + .05, (720, 735, 2.0), 0), (T_LIGHT + .35, (720, 728, 2.06), 1.4)]),     # Picard ~2/3 of frame height
    (CUT_G2, [(CUT_G2, (960, 520, 1.0), 0)]),
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
    base = make_mod(who)
    def mod(t, P):
        P = base(t, P)
        x0, y0 = F.pos_at(t); x1, y1 = F.pos_at(t + .04)
        v = abs(x1 - x0) / .04
        if v > 40:
            a = min(v / 400, 1); ph = math.sin(t * 2 * math.pi * 2.4)
            P['lhip'] += 26 * a * ph; P['rhip'] -= 26 * a * ph
            P['lkn'] -= 22 * a * max(-ph, 0); P['rkn'] -= 22 * a * max(ph, 0)
        return P
    F.mod = mod; return F

BARC = fig('barclay', 330, STAND, 1, ['curly', 'badge'], scale=SC)
PIC = fig('picard', 740, STAND, -1, ['shine', 'badge', 'collar'], scale=SC)
GROK = fig('grokbot', 1060, STAND, -1, ['robot'], scale=SC)
RIKER = fig('riker', 1480, STAND, -1, ['beard', 'badge'], scale=SC)
RIKER.move(LN['r1']['s'] + .2, 1150, STAND, T_BONK - LN['r1']['s'] - .2)        # arms out, shuffles into Grok Bot
RIKER.move(T_BONK + .05, 1185, STAND, .25)                                        # bounces back a step

def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

# ------------------------------------------------------------------ props
SW = (500, 560)                                         # theme switch wall plate
def switch(pen, t, dk):
    x, y = SW; on = T_DARK <= t < T_LIGHT                 # lever down = dark
    if not dk:
        pen.rect(x - 38, y - 70, x + 38, y + 70, 5, INK, 'plate', fill=PAPER)
        pen.rect(x - 12, y - 40, x + 12, y + 40, 3, INK, 'slot', fill=INK)
        ly = y + (26 if on else -26)
        pen.rect(x - 22, ly - 14, x + 22, ly + 14, 4, INK, 'lever', fill=PAPER)
    SETS.outlined(pen, 'THEME', (x, y - 108), 40, 4)
    SETS.outlined(pen, 'LIGHT', (x + 95, y - 30), 30, 3, 'hand'); SETS.outlined(pen, 'DARK', (x + 92, y + 34), 30, 3, 'hand')
    if T_DARK - .05 <= t < T_DARK + .5 or T_LIGHT - .05 <= t < T_LIGHT + .5:
        SETS.outlined(pen, 'CLICK!', (x - 10, y - 170), 46, 5)

def head_pt(F, t, dy=0): x, y = F.pos_at(t); return (x, y - 230 * SC / 1.4 + dy)
def LABELS(t):
    rx = RIKER.pos_at(t)[0]
    return [((rx + 20, 330), '[RIKER, LOST]'), ((250, 545), '[BARCLAY, SWEATING]'),
            ((1080, 445), '[GROK BOT, HELPFUL]'), ((700, 345), '[CAPTAIN, NOT AMUSED]'),
            ((230, 905), '[FLOOR]'), ((960, 175), '[VIEWSCREEN, ALSO DARK]')]
ORDER = [2, 0, 1, 4, 5, 3]                               # pop order (Picard last, right before he speaks)
def alt_labels(pen, t):
    if t < T_ALT: return
    L = LABELS(t)
    for j, idx in enumerate(ORDER):
        t0 = T_ALT + j * .2; k = ease_out_back(clamp01((t - t0) / .2))
        if k <= .02: continue
        c, txt = L[idx]
        SETS.outlined(pen, txt, c, 38 * k, 4, 'marker')

def shades(pen, h, t):
    if t < T_SHADES: return
    hd, R = h['head'], h['R']; k = ease_out_back(clamp01((t - T_SHADES) / .25))
    yo = -40 * (1 - k); ex = hd[0] - R * .35; ey = hd[1] - R * .1 + yo
    for dx in (-R * .32, R * .32):
        pen.rect(ex + dx - R * .26, ey - R * .17, ex + dx + R * .26, ey + R * .19, 0, fill=INK)
    pen.line([(ex - R * .06, ey - R * .05), (ex + R * .06, ey - R * .05)], 3, INK, 'brg')
    pen.line([(ex + R * .58, ey - R * .08), (hd[0] + R * .9, ey - R * .2)], 3, INK, 'arm')
    if t - T_SHADES < .5: SETS.burst(pen, (ex - R * .3, ey - R * .3), t, T_SHADES + .15, 40, n=6, sid='glint', dur=.4, w=2.5)

VS = (560, 100, 1360, 470)
def viewscreen(img, pen, t, cam, boil):
    x0, y0, x1, y1 = VS; vc = (x0 + x1) / 2
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    stars_field(sp, VS, t, 60)
    if t >= T_LIGHT:
        sp.rect(vc - 330, y0 + 60, vc + 330, y1 - 60, 0, fill=INK)
        sp.text('BRIGHTNESS', (vc, y0 + 140), 80, PAPER, 'marker')
        n = 100 if t < LN['g2']['s'] else min(110, 100 + int((t - wt('g2', 'one')) / .5 * 10)) if t > wt('g2', 'one') else 100
        sp.text(f'{n}%', (vc, y0 + 255), 110, PAPER, 'marker')
    else:
        ship(sp, (vc, (y0 + y1) / 2), .7, PAPER, INK, 'ship', facing=1)
    clip_paste(img, sub, pen, VS)

def bridge(t, cam):
    dk = dark(t); boil = int(t * 12)
    img = np.full((H, W, 3), INK if dk else PAPER, np.uint8); pen = Pen(img, cam, boil)
    h = {}
    if not dk:
        SETS.floor(pen)
        viewscreen(img, pen, t, cam, boil)
        h['barclay'] = BARC.draw(pen, t, 0, w=5.5 * SC ** .3)
        h['picard'] = PIC.draw(pen, t, 0, w=5.5 * SC ** .3)
        h['grokbot'] = GROK.draw(pen, t, 0, w=5.5 * SC ** .3)
        h['riker'] = RIKER.draw(pen, t, 0, w=5.5 * SC ** .3)
        shades(pen, h['grokbot'], t)
        if t >= T_LIGHT:                                           # squint/sizzle marks on everyone after the flash
            u = t - T_LIGHT
            if u < 2.2:
                for who in ('picard', 'riker', 'barclay'):
                    hd, R = h[who]['head'], h[who]['R']
                    for j in range(5):
                        a = -math.pi / 2 + (j - 2) * .45; r0 = R * 1.35 + 4 * math.sin(t * 30 + j)
                        pen.line([(hd[0] + r0 * math.cos(a), hd[1] + r0 * math.sin(a)), (hd[0] + (r0 + 18) * math.cos(a), hd[1] + (r0 + 18) * math.sin(a))], 2.5, INK, f'sz{who}{j}')
    # outlined text: the only thing that survives dark mode
    SETS.outlined(pen, 'U.S.S. TITAN', (1680, 140), 44, 4)
    switch(pen, t, dk)
    if dk:
        if T_BONK <= t < T_BONK + .9:
            k = ease_out_back(clamp01((t - T_BONK) / .2)); SETS.outlined(pen, 'BONK!', (1110, 470), 70 * k, 6)
        if T_BONK + .35 <= t < T_BONK + 1.2: SETS.outlined(pen, 'ow.', (1250, 420), 44, 4, 'hand')
        alt_labels(pen, t)
    if T_LIGHT <= t < T_LIGHT + .8:
        k = ease_out_back(clamp01((t - T_LIGHT - .05) / .2)); SETS.outlined(pen, 'FZZT!', (930, 520), 80 * k, 6)
    return img, h

SETFN = {'bridge': bridge}

def flash(img, t):
    """the switch back to light mode is a flashbang: white-out that decays over ~0.6 s"""
    u = t - T_LIGHT
    if 0 <= u < .7:
        a = 1.0 if u < .12 else (1 - (u - .12) / .58) ** 1.6
        img = (img.astype(np.float32) * (1 - a) + 255 * a).clip(0, 255).astype(np.uint8)
    return img

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
    """split key art: light half (the crew) | dark half (only outlined text), wavy diagonal edge; title band below"""
    lt, dt = T_DARK - .45, T_ALT + 1.3
    a, _ = bridge(lt, (960, 520, 1.0)); b, _ = bridge(dt, (960, 520, 1.0))
    yy, xx = np.mgrid[0:H, 0:W]
    edge = 1000 + (yy - 540) * .35 + 30 * np.sin(yy / 70)
    img = np.where((xx < edge)[..., None], a, b)
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(500, 930, 1420, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'DARK MODE', (960, 972), 108, 7)
    pen.line([(660, 1026), (1260, 1021)], 5, INK, 'tul')
    pen.text('Barclay \u00d7 Riker \u00d7 Grok Bot \u00d7 Picard  \u00b7  STARSHIP GROKBOT', (960, 1052), 32, INK, 'hand')
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
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT', 'picard': 'PICARD', 'barclay': 'BARCLAY'}; ev = []; Ls = TL['lines']
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
    out = f'{HERE}/darkmode-nosfx.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
