"""Dialogue short #5: "MERGE CONFLICT" - Riker and Grok Bot both edit the Captain's log at once; it diffs into
chaos (conflict markers on the viewscreen); Admiral Picard resolves it: "Accept theirs." (theirs = his: tea).
    python mergeconflict.py | --frames t ... (video times) | --poster"""
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
T_CONF = LN['g1']['e'] + .1                  # CONFLICT! stamp, screen shows the markers
T_CLICK = w('p1', 'accept', .1)             # Picard clicks ACCEPT THEIRS
T_TEA = w('g2', 'reads', -.05)               # Titan screen flips to the resolved log
CUT_G = LN['g1']['s'] - .2; CUT_R2 = LN['r2']['s'] - .15; CUT_P = LN['p1']['s'] - .15; CUT_G2 = w('g2', 'the', -.12); CUT_END = LN['g2']['e'] + .05
TYPE = 'scribble+padd=1+lookup=.35'
KEYS = dict(
    riker=[(0, 'idle+look_r', 0), (w('r1', "captain's", -.2), TYPE, .25), (w('r1', 'saved', -.1), 'proud', .25), (w('r1', 'single-handedly', -.1), TYPE, .25),
           (LN['r1']['e'] + .1, 'idle+lookup=.4', .3), (w('g1', 'ninety', -.1), TYPE, .3), (T_CONF, 'surprise', .15),
           (w('r2', 'why', -.15), 'point+lookup=.3', .25), (w('r2', 'angle', -.1), 'palm', .25), (LN['r2']['e'] + .2, 'idle', .3),
           (LN['g2']['s'] + .2, 'idle+lookup=.4', .3), (w('g2', 'hot', -.05), 'idle+look_r+mouth=3', .2), (CUT_END + .5, 'facepalm', .3)],
    grokbot=[(0, 'idle+look_l', 0), (w('r1', 'saved', -.1), 'idle+lookup=.4', .3), (w('g1', "captain's", -.2), TYPE, .25), (w('g1', 'vibes', -.1), 'thumbs', .2),
             (T_CONF, 'surprise', .15), (w('r2', 'angle', .1), 'shrug', .25), (LN['r2']['e'] + .3, 'idle', .3),
             (CUT_G2, 'thumbs', 0), (w('g2', 'log', -.1), 'pointup', .25), (w('g2', 'hot', .2), 'idle+look_l', .25), (CUT_END + .7, 'shrug', .25)],
    picard=[(0, 'front+rsh=40+rel=110+tilt=4', 0), (w('p1', 'resolve', -.15), 'front+rsh=40+rel=110+tilt=-4', .3),
            (w('p1', 'accept', -.25), 'front+lsh=10+lel=10+rsh=95+rel=-20', .25)],
)
NODS = dict(riker=[], grokbot=[w('r1', 'again', .1)], picard=[w('p1', 'theirs', .15)])
SHOTS = [
    (0.0, 'titan', [(0.0, (900, 500, 1.06), 0), (0.0, (820, 470, 1.2), CUT_G)]),
    (CUT_G, 'titan', [(CUT_G, (1100, 470, 1.2), 0), (T_CONF - .05, (960, 400, 1.6), .3)]),
    (CUT_P, 'ent', [(CUT_P, (960, 500, 1.0), 0), (w('p1', 'accept', -.3), (920, 515, 1.08), .6)]),
    (CUT_G2, 'titan', [(CUT_G2, (960, 470, 1.25), 0), (CUT_END, (960, 500, 1.06), .6)]),
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

RIKER = fig('riker', 540, STAND, 1, ['beard', 'badge'], scale=SC)
GROK = fig('grokbot', 1400, STAND, -1, ['robot'], scale=SC)
PIC = fig('picard', 640, 880, 1, ['shine', 'badge', 'collar'], col=PAPER, scale=3.3)


# ------------------------------------------------------------------ helpers
def clip_paste(img, sub, pen, rect):
    X0, Y0 = pen.S(rect[:2]); X1, Y1 = pen.S(rect[2:])
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    if X1 > X0 and Y1 > Y0: img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]

def said(line, t):
    """words of a line revealed as they are spoken (typed live)"""
    return [x['w'] for x in LN[line]['words'] if x['s'] - .05 <= t]

def wrap(words, n):
    out, cur = [], ''
    for x in words:
        if len(cur) + len(x) + 1 > n and cur: out.append(cur); cur = x
        else: cur = (cur + ' ' + x).strip()
    if cur: out.append(cur)
    return out

def teacup(pen, c, s, col, sid, t):
    x, y = c
    pts = [(x - 34 * s, y - 30 * s), (x - 26 * s, y + 18 * s), (x + 26 * s, y + 18 * s), (x + 34 * s, y - 30 * s)]
    pen.line(pts, 5, col, sid + 'cup'); pen.line([(x - 34 * s, y - 30 * s), (x + 34 * s, y - 30 * s)], 5, col, sid + 'rim')
    pen.arc((x + 40 * s, y - 8 * s), 14 * s, 16 * s, -80, 80, 5, col, sid + 'h')
    pen.line([(x - 52 * s, y + 24 * s), (x + 52 * s, y + 24 * s)], 5, col, sid + 'sau')
    for j in range(3):   # steam
        ph = (t * .8 + j / 3) % 1
        pen.line([(x - 16 * s + j * 16 * s + 6 * math.sin(k * 3 + t * 4 + j) * s, y - 44 * s - k * 50 * s - ph * 20 * s) for k in np.linspace(0, 1, 6)], 3, col, sid + f'st{j}')


# ------------------------------------------------------------------ set: Titan bridge, the log on the viewscreen
VS = (540, 100, 1380, 490)
RW = ["Commander", "Riker", "saved", "the", "ship", "again,", "single-handedly."]
def screen(pen, img, t):
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vsframe')
    sub = np.full_like(img, INK); sp = Pen(sub, pen.cam, pen.boil)
    L0 = x0 + 34; TY = y0 + 40; LH = 53; FS = 44
    tea = t >= T_TEA + .25
    hdr = 'captains_log.txt' + ('   (resolved)' if tea else '   (CONFLICT)' if t >= T_CONF else '')
    sp.text(hdr, (L0, TY), 30, PAPER, 'marker', anchor='l'); sp.line([(L0, TY + 24), (x1 - 34, TY + 24)], 2.5, PAPER, 'hdrul', wob=.5)
    if tea:
        u = t - T_TEA
        if True:
            s = 'Tea. Earl Grey. Hot.'; n = int(clamp01((u - .25) / .7) * len(s))
            sp.text(s[:n], ((x0 + x1) / 2 - 60, y0 + 190), 64, PAPER, 'marker')
            if u > 1.0: sp.text('-- ADM. PICARD', ((x0 + x1) / 2 + 140, y0 + 280), 34, PAPER, 'hand')
            teacup(sp, (x1 - 110, y0 + 330), 1.0, PAPER, 'tc', t)
            if u > 1.0: SETS.check(sp, (x0 + 90, y0 + 290), 1.6, 'rchk')
    elif t < T_CONF:
        rw = said('r1', t)
        if rw and rw[0].lower().startswith("captain"): rw = rw[2:]
        gw = said('g1', t)
        if gw and gw[0].lower().startswith("captain"): gw = gw[2:]
        if not gw:
            lines = wrap(rw, 30)
            jit = 0
        else:           # both editing: words interleave into a mash
            mash = []
            for i in range(max(len(RW), len(gw))):
                if i < len(rw): mash.append(rw[i])
                if i < len(gw): mash.append(gw[i])
            lines = wrap(mash, 30); jit = 3
        r = np.random.default_rng(int(t * 12))
        for j, s in enumerate(lines[:6]):
            sp.text(s, (L0 + r.uniform(-jit, jit), TY + 70 + j * LH + r.uniform(-jit, jit)), FS, PAPER, 'hand', anchor='l')
        if (int(t * 3) % 2 == 0) and t > LN['r1']['s']:   # caret
            last = lines[-1] if lines else ''
            cx = L0 + len(last) * FS * .40 + 8; cy = TY + 70 + (max(len(lines), 1) - 1) * LH
            sp.rect(cx, cy - 18, cx + 5, cy + 18, 0, fill=PAPER)
    else:
        rows = ['<<<<<<< HEAD (riker)', 'Commander Riker saved the ship', 'again, single-handedly.', '=======',
                'Shields: 90%. Vibes: excellent :)', '>>>>>>> grokbot']
        u = t - T_CONF
        for j, s in enumerate(rows):
            if u < .08 * j: break
            mark = s[0] in '<=>'
            sp.text(s, (L0, TY + 62 + j * LH), FS if not mark else 38, PAPER, 'marker' if mark else 'hand', anchor='l')
        ta = w('r2', 'angle', -.1)
        if t > ta:           # scribbled circles around the angle brackets
            k = clamp01((t - ta) / .35)
            for j, yy in ((0, TY + 62), (5, TY + 62 + 5 * LH)):
                pts = [(L0 + 100 + 122 * math.cos(a), yy + 28 * math.sin(a)) for a in np.linspace(0, 2 * math.pi * 1.1 * k, 30)]
                if len(pts) > 1: sp.line(pts, 4, PAPER, f'circ{j}', wob=1.5)
    if T_TEA <= t < T_TEA + .25:     # ink sweep wipes the conflict off the screen
        ex = x0 + (x1 - x0) * ease((t - T_TEA) / .25)
        sp.rect(x0, y0, ex, y1, 0, fill=INK); sp.line([(ex, y0), (ex, y1)], 8, PAPER, 'wipe', wob=2)
    clip_paste(img, sub, pen, VS)
    if T_CONF <= t < T_TEA:     # CONFLICT! stamp on the frame
        SETS.burst(pen, (960, 96), t, T_CONF, 120, 16, INK, 'cfb', .6, 4)
        SETS.stamp(pen, 'CONFLICT!', (1250, 86), t, T_CONF, 54)

def titan(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    SETS.floor(pen); screen(pen, img, t)
    pen.line([(-600, 60), (460, 60), (520, 92)], 4, INK, 'rail1'); pen.line([(1400, 92), (1460, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (250, 40), 40, INK, 'marker')
    console(pen, 130, 320, 712, sid='ops', mirror=True, label='OPS'); console(pen, 1620, 1810, 712, sid='sci', label='SCI')
    # the Captain's chair (empty: it's his log they're fighting over)
    cx = 960; pen.line([(cx - 60, 826), (cx + 60, 826)], 6, INK, 'seat')
    back = [(cx - 52, 826), (cx - 58, 680), (cx + 58, 680), (cx + 52, 826)]; pen.fill(back, PAPER); pen.line(back, 5, INK, 'cback', closed=True)
    pen.line([(cx, 826), (cx, FLOOR)], 6, INK, 'ped'); pen.line([(cx - 44, FLOOR), (cx + 44, FLOOR)], 6, INK, 'cbase')
    pen.rect(cx - 50, 720, cx + 50, 760, 3, INK, 'cplate', fill=PAPER); pen.text('CAPT.', (cx, 740), 24, INK, 'marker')
    hands = {'riker': RIKER.draw(pen, t, 0, w=5.5 * SC ** .3), 'grokbot': GROK.draw(pen, t, 0, w=5.5 * SC ** .3)}
    if CUT_END + .5 < t:       # sweat + a shared look
        k = ease_out_back(clamp01((t - CUT_END - .5) / .25))
        SETS.outlined(pen, '...', (960, 590), 70 * k + 1, 5)
    return img, hands


# ------------------------------------------------------------------ set: Enterprise-D viewscreen (Picard resolves it)
ES = (70, 40, 1850, 860)
def ent(t, cam):
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12); pen = Pen(img, cam, boil)
    pen.rect(ES[0] - 16, ES[1] - 16, ES[2] + 16, ES[3] + 16, 6, INK, 'eframe')
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    stars_field(sp, ES, t, 0.015, n=110, seed=21)
    sp.text('U.S.S. ENTERPRISE-D  //  READY ROOM', (120, 95), 40, PAPER, 'marker', anchor='l')
    PIC.draw(sp, t, 0, w=8)
    sp.rect(240, 700, 1060, 980, 6, PAPER, 'desk', fill=INK); sp.line([(280, 740), (1020, 740)], 3, PAPER, 'desk2')
    sp.text('ADM. PICARD  //  U.S.S. ENTERPRISE', (650, 805), 40, PAPER, 'marker')
    teacup(sp, (950, 676), .8, PAPER, 'etea', t)
    px0, py0, px1, py1 = 1160, 170, 1790, 720
    sp.rect(px0, py0, px1, py1, 5, PAPER, 'mr', fill=PAPER)
    sp.text('MERGE CONFLICT', ((px0 + px1) / 2, py0 + 50), 44, INK, 'marker')
    sp.text("captains_log.txt  (2 versions)", ((px0 + px1) / 2, py0 + 105), 32, INK, 'hand')
    sp.line([(px0 + 30, py0 + 135), (px1 - 30, py0 + 133)], 3, INK, 'mrul')
    for j, (lab, y) in enumerate((('ACCEPT OURS', py0 + 210), ('ACCEPT THEIRS', py0 + 320))):
        on = j == 1 and t > T_CLICK
        sp.rect(px0 + 70, y - 40, px1 - 70, y + 40, 5, INK, f'btn{j}', fill=INK if on else PAPER)
        sp.text(lab, ((px0 + px1) / 2, y), 40, PAPER if on else INK, 'marker')
    if t > T_CLICK:
        SETS.burst(sp, ((px0 + px1) / 2, py0 + 320), t, T_CLICK, 120, 14, INK, 'clk', .5, 4)
        if t > T_CLICK + .35:
            sp.text('theirs = ADM. PICARD', ((px0 + px1) / 2, py0 + 430), 38, INK, 'hand')
            SETS.stamp(sp, 'RESOLVED', ((px0 + px1) / 2, py0 + 500), t, T_CLICK + .5, 46)
    clip_paste(img, sub, pen, ES)
    return img, {}

SETFN = {'titan': titan, 'ent': ent}


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
    """the conflict on the viewscreen, Riker and Grok Bot reacting; title band below."""
    tt = w('r2', 'brackets', .2)
    img, _ = titan(tt, (960, 470, 1.1))
    pen = Pen(img, (960, 540, 1.0), 3)
    pen.rect(380, 930, 1540, 1076, 0, fill=PAPER)
    SETS.outlined(pen, 'MERGE CONFLICT', (960, 972), 104, 7)
    pen.line([(560, 1026), (1360, 1021)], 5, INK, 'tul')
    pen.text('Riker  \u00d7  Grok Bot  \u00d7  Picard', (960, 1052), 36, INK, 'hand')
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
    out = f'{HERE}/mergeconflict.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
