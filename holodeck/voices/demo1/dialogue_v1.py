"""Dialogue scene renderer: Riker x Grok Bot, "the daily log".
Voice -> timeline.json (line/word times + per-speaker RMS envelope per frame) -> cue table below -> frames.
    python dialogue.py            # full render (parallel parts, captions, audio)
    python dialogue.py --frames 1.2 6.5 ...   # raw check PNGs (no captions)
"""
import sys, os, json, math, subprocess, time
SP = '/workspace/holodeck/titan-hello-world/stick-poc'; sys.path.insert(0, SP)
import numpy as np, cv2
cv2.setNumThreads(1)
from stickfig import *
from inkset import W, H, FLOOR, console, paper_finish, sparkle
import sets as SETS
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(f'{HERE}/timeline.json')); FPS = 24; TOTAL = TL['total']
ENV = {k: np.array(v) for k, v in TL['env'].items()}
WT = {L['id']: {w['w'].strip('.,!?').lower(): w['s'] for w in L['words']} for L in TL['lines']}
LN = {L['id']: L for L in TL['lines']}
def w(line, word, off=0.0): return WT[line][word] + off
SC = 1.4; STAND = FLOOR - 110 * SC

# ------------------------------------------------------------------ cue table
CUES = dict(
    people=dict(riker=dict(props=['beard', 'badge'], x=740, facing=1),
                grokbot=dict(props=['robot'], x=1180, facing=-1)),
    keys=dict(
        riker=[(0, 'idle', 0), (w('r1', 'morning', -.25), 'wave', .3), (w('r1', "let's", -.2), 'palm', .3), (w('r1', 'log', .3), 'idle', .4),
               (w('g1', 'shipped'), 'idle+look_l+lookup=.5', .4), (w('g1', 'hundred', -.1), 'idle+mouth=3', .2),
               (w('r2', 'impressive', -.35), 'chinrub', .35), (w('r2', 'how', -.2), 'palm', .3), (w('r2', 'create', -.2), 'point', .2),
               (w('r2', 'create', .6), 'idle', .4),
               (w('g2', 'also', .2), 'idle+mouth=3', .2), (w('g2', 'perfectly'), 'chinrub', .4),
               (w('r3', "let's", -.3), 'pointup', .35), (w('r3', "captain's", -.1), 'palm', .3), (w('r3', 'log', .35), 'thumbs+mouth=1', .3)],
        grokbot=[(0, 'idle', 0), (w('r1', 'grok', .1), 'wave', .25), (w('r1', "let's"), 'idle', .3), (w('r1', 'daily'), 'thumbs', .25),
                 (w('g1', 'daily', -.2), 'tada', .25), (w('g1', 'i', -.3), 'pointup', .3), (w('g1', 'bugs', .2), 'proud', .3),
                 (w('r2', 'impressive', .4), 'proud', .3), (w('r2', 'create', -.1), 'idle+look_l', .15),
                 (w('g2', 'also', -.15), 'shrug', .25), (w('g2', 'perfectly', -.15), 'tada', .25), (w('g2', 'commander', .1), 'proud', .3),
                 (w('r3', 'out'), 'idle+look_r+lookup=.6', .3), (w('r3', 'log', .2), 'salute', .3)],
    ),
    nods=dict(grokbot=[w('r1', 'grok'), w('r1', 'daily')], riker=[w('g1', 'forty'), w('g1', 'three'), w('g2', 'balanced', .1)]),
    shots=[   # at, camera keys [(t, (cx, cy, zoom), ease)]
        dict(at=0.0, cam=[(0.0, (960, 500, 1.04), 0), (0.0, (960, 560, 1.2), 4.2)]),                       # wide two-shot, slow push
        dict(at=w('g1', 'daily', -.15), cam=[(0, (1110, 650, 2.1), 0), (5.0, (1120, 640, 2.2), 0.5)]),        # Grok Bot close (OTS Riker)
        dict(at=w('g1', 'shipped', -.1), cam=[(0, (960, 330, 1.55), 0), (5.6, (960, 320, 1.62), 2.6)]),      # insert: the log on the viewscreen
        dict(at=w('r2', 'impressive', -.4), cam=[(0, (820, 650, 2.1), 0), (8.3, (810, 640, 2.3), 3.3)]),      # Riker close
        dict(at=w('r2', 'create', .45), cam=[(0, (1170, 640, 2.4), 0), (11.75, (1170, 635, 2.55), 0.8)]),   # reaction: Grok Bot sweats
        dict(at=w('g2', 'perfectly', -.2), cam=[(0, (960, 490, 1.08), 0), (13.6, (960, 500, 1.13), 2.0)]),                                   # wide, screen + stamp
        dict(at=w('r3', "let's", -.3), cam=[(0, (880, 450, 1.3), 0), (15.5, (930, 490, 1.15), 4.0)]),      # Riker + screen, redact
    ],
    events=dict(header=w('g1', 'daily'), row1=w('g1', 'forty'), row2=w('g1', 'three'), row3=w('g2', 'three'),
                stamp=w('g2', 'balanced', -.05), redact=w('r3', 'out', -.1), sweat=w('r2', 'create', .5), unstamp=w('r3', "let's", -.3)),
)
EV = CUES['events']
for i, s in enumerate(CUES['shots']):
    s['end'] = CUES['shots'][i + 1]['at'] if i + 1 < len(CUES['shots']) else 1e9
    s['cam'] = [(s['at'] if k == 0 and c[0] == 0 and i else c[0], c[1], c[2]) for k, c in enumerate(s['cam'])]


def make_mod(who):
    env = ENV.get(who, np.zeros(1)); nods = CUES['nods'].get(who, [])
    def f(t, P):
        i = int(t * FPS); e = float(env[i]) if i < len(env) else 0.0
        e2 = float(env[max(i - 2, 0)]) if i < len(env) else 0.0
        P['talk'] = e
        P['tilt'] += 7 * (e - e2) + 3 * e          # head bobs with syllable onsets
        P['lean'] += 2.5 * e
        for tn in nods:                              # listener nods
            u = t - tn
            if 0 <= u < .7: P['tilt'] += 12 * math.sin(math.pi * u / .35) * (1 - u / .7)
        return P
    return f


FIGS = {}
for who, p in CUES['people'].items():
    F = Figure(who, p['x'], STAND, p['facing'], set(p['props']), scale=SC)
    for k in CUES['keys'][who]: F.key(k[0] if k[0] > 0 else -1e8, k[1], k[2])
    F.mod = make_mod(who); FIGS[who] = F


# ------------------------------------------------------------------ set: bridge + log viewscreen
VS = (610, 110, 1310, 470)

class Ctx:   # minimal stand-in for engine.Ctx so sets.bridge helpers can be reused
    shot = {'opt': {'gauge_level': .8}}
    def opt(self, k, d=None): return self.shot['opt'].get(k, d)
    def ev(self, k): return EV[k]
CTX = Ctx()

def rocket(pen, c, s, col, sid):
    x, y = c
    body = [(x - 26 * s, y + 8 * s), (x + 10 * s, y + 8 * s), (x + 30 * s, y), (x + 10 * s, y - 8 * s), (x - 26 * s, y - 8 * s)]
    pen.line(body, 3.5, col, sid, closed=True)
    pen.line([(x - 26 * s, y - 8 * s), (x - 36 * s, y - 18 * s), (x - 20 * s, y - 8 * s)], 3, col, sid + 'f1')
    pen.line([(x - 26 * s, y + 8 * s), (x - 36 * s, y + 18 * s), (x - 20 * s, y + 8 * s)], 3, col, sid + 'f2')
    for k in range(3): pen.line([(x - 40 * s - k * 9 * s, y - 6 * s + k * 6 * s), (x - 52 * s - k * 9 * s, y - 6 * s + k * 6 * s)], 2.5, col, sid + f'tr{k}')

def bug(pen, c, s, col, sid, t):
    x, y = c
    pen.arc((x, y), 16 * s, 11 * s, 0, 360, 3.5, col, sid + 'b')
    pen.circle((x + 19 * s, y), 6 * s, 3, col, sid + 'h')
    for k in (-1, 0, 1):
        wig = 3 * math.sin(t * 18 + k)
        for sd in (-1, 1): pen.line([(x + k * 8 * s, y + sd * 10 * s), (x + k * 10 * s + wig, y + sd * 20 * s)], 2.5, col, sid + f'l{k}{sd}')
    pen.line([(x + 23 * s, y - 4 * s), (x + 32 * s, y - 14 * s)], 2, col, sid + 'a1'); pen.line([(x + 23 * s, y + 4 * s), (x + 32 * s, y + 14 * s)], 2, col, sid + 'a2')

def count(t, t0, n, dur=.45):
    return int(round(n * ease_out(clamp01((t - t0) / dur))))

def screen(pen, t):
    x0, y0, x1, y1 = VS
    pen.rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, 5, INK, 'vsframe')
    pen.rect(x0, y0, x1, y1, 0, fill=INK)
    # idle starfield until the log comes up, then the log page
    if t < EV['header'] - .1:
        from inkset import stars_field
        stars_field(pen, VS, t, 0.05, n=70); return
    hdr = "DAILY LOG  //  GROK BOT"; n = int(clamp01((t - EV['header']) / .5) * len(hdr))
    pen.text(hdr[:n], (650, 160), 40, PAPER, 'marker', anchor='l')
    if n == len(hdr): pen.line([(650, 192), (1270, 188)], 3, PAPER, 'hul')
    rows = [('row1', 'rocket', 'FEATURES SHIPPED', 40, 250), ('row2', 'bug', 'BUGS FIXED', 300, 325), ('row3', 'bug', 'BUGS CREATED', 300, 400)]
    for key, icon, lab, num, y in rows:
        t0 = EV[key]
        if t < t0 - .05: continue
        k = ease_out_back(clamp01((t - t0 + .05) / .25))
        if icon == 'rocket': rocket(pen, (700 + 30 * (1 - k), y), 0.9 * k + .05, PAPER, key + 'ic')
        else: bug(pen, (690, y), 0.9 * k + .05, PAPER, key + 'ic', t)
        pen.text(f'{count(t, t0, num)} {lab}', (760, y), 38, PAPER, 'hand', anchor='l')
        if t > t0 + .5:
            mk = ease_out_back(clamp01((t - t0 - .5) / .2))
            if key == 'row3': pen.text('!?', (1235, y), 46 * mk + 2, PAPER, 'marker')
            else: pen.line([(1226, y), (1236, y + 12 * mk), (1256, y - 16 * mk)], 5, PAPER, key + 'ck')
    # redaction: a paper bar scribbles over row 3
    if t > EV['redact']:
        u = ease_out(clamp01((t - EV['redact']) / .45))
        xr = 660 + (1290 - 660) * u
        pen.rect(660, 375, xr, 425, 0, fill=PAPER)
        for k in range(int(u * 14)):
            if k < 3 or k > 10: pen.line([(660 + k * 45, 372), (690 + k * 45, 428)], 3, INK, f'rdx{k}')
        if u > .6: pen.text('REDACTED', (975, 400), 42 * ease_out_back((u - .6) / .4) + 2, INK, 'marker')

def bg(pen, t):
    SETS.floor(pen)
    screen(pen, t)
    pen.line([(-600, 60), (520, 60), (580, 100)], 4, INK, 'rail1'); pen.line([(1340, 100), (1400, 60), (2500, 60)], 4, INK, 'rail2')
    pen.text('U.S.S. TITAN', (960, 58), 44, INK, 'marker')
    CTX.t = t; SETS.bridge.minis(pen, t, CTX); SETS.bridge.gauge(pen, t, CTX)
    console(pen, 1360, 1530, 712, sid='helm', label='HELM')
    console(pen, 230, 400, 712, sid='ops', mirror=True, label='OPS')
    console(pen, 1640, 1810, 712, sid='sci', label='SCI')

def fg(pen, t, hands):
    # Grok Bot's LED antenna blinks while talking
    gb = hands['grokbot']
    # stamp over the screen
    if EV['stamp'] <= t < EV['unstamp']:
        SETS.stamp(pen, 'PERFECTLY BALANCED', (960, 300), t, EV['stamp'], 62)
    # sweat drop on the reaction shot
    ts = EV['sweat']
    if ts <= t < ts + 1.6:
        u = t - ts; hx, hy = gb['head']; R = gb['R']
        x, y = hx + R * 1.45, hy - R * .9 + R * 1.1 * ease(clamp01((u - .25) / 1.1))
        k = ease_out_back(clamp01(u / .2))
        pts = [(x + 10 * k * math.sin(a) * (1 - math.cos(a)) * .6, y + 16 * k * (-math.cos(a))) for a in np.linspace(0, 2 * math.pi, 24)]
        pen.fill(pts, PAPER); pen.line(pts, 3.5, INK, 'sweat', closed=True)
    # Riker's "!" on the punchline beat
    th = w('g1', 'hundred')
    if th <= t < th + .9:
        rh = hands['riker']['head']; k = ease_out_back(clamp01((t - th) / .2))
        pen.text('!', (rh[0] + 10, rh[1] - 70), 70 * k + 2, INK, 'marker', alpha=1 - clamp01((t - th - .6) / .3))


def cam_at(sh, t):
    keys = sh['cam']; cam = keys[0][1]
    for i, (tk, c, dur) in enumerate(keys):
        if t < tk: break
        prev = cam if i else c
        k = ease((t - tk) / dur) if dur > 0 else 1.0
        cam = tuple(lerp(a, b, k) for a, b in zip(prev, c))
    return cam

VIG, GRAINS = paper_finish()
def render(t):
    sh = next(s for s in CUES['shots'] if s['at'] <= t < s['end'])
    img = np.full((H, W, 3), PAPER, np.uint8); boil = int(t * 12)
    pen = Pen(img, cam_at(sh, t), boil)
    bg(pen, t)
    hands = {n: F.draw(pen, t, 0, w=5.5 * SC ** .3) for n, F in FIGS.items()}
    fg(pen, t, hands)
    f = img.astype(np.float32) * VIG + GRAINS[boil % 4]
    fin, fout = clamp01(t / .3), clamp01((TOTAL - t) / .4)
    f = f * min(fin, fout) + np.array(PAPER, np.float32) * (1 - min(fin, fout))
    return np.clip(f, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ captions (speaker name + karaoke sweep)
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
Style: Line,Exo 2,60,{INKc},{GREY},{PAPERc},&H00000000,1,0,0,0,100,100,1,0,1,6,0,2,90,90,42,1
Style: Name,Permanent Marker,56,{INKc},{INKc},{PAPERc},&H00000000,0,0,0,0,100,100,2,0,1,5,0,2,90,90,112,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    names = {'riker': 'RIKER', 'grokbot': 'GROK BOT'}; ev = []; Ls = TL['lines']
    for i, L in enumerate(Ls):
        ws = L['words']; a = L['s'] - 0.25
        nxt = Ls[i + 1]['s'] - 0.2 if i + 1 < len(Ls) else TOTAL - .3
        b = min(L['e'] + 0.5, nxt)
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
    out = f'{HERE}/riker-grokbot-dailylog.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt', '-i', f'{HERE}/mix.wav',
                    '-vf', f'ass={HERE}/captions.ass', '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                    '-tune', 'animation', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL}', '-movflags', '+faststart', out], check=True)
    print('done', out, f'{time.time() - st:.1f}s')
