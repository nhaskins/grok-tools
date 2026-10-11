"""HELLO v3 (expanded dialogue, 5 lines): series stick-figure Grok Bot (stickfig robot prop) walks out toward camera (fake depth via a tracking camera that zooms + drifts down),
waves at camera, push-in to a 2/3 shot, says "Hello, Starship Grok Bot." (Piper en_US-ryan-low + robot.sh, box CPU only;
RMS lip-sync, boxbot talking mouth). Fork of robot_welcome.py + poster frame 0 / ink wipe (demo13 recipe).
Local rig only. Reuses rig_test's planted-foot gait + IK and the v2 (no-mottle) paper.
    python robot_welcome.py | --still t ... """
import sys, os, math, json, subprocess
sys.argv_saved = list(sys.argv); sys.argv = [sys.argv[0]]          # rig_test reads argv at import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_test as RT
sys.argv = sys.argv_saved
import numpy as np, cv2
from stickfig import *
from inkset import W, H
import sets as SETS
HERE = os.path.dirname(os.path.abspath(__file__)); D = f'{HERE}/hello3'
TL = json.load(open(f'{D}/timeline.json')); ENV = np.array(TL['env'])
FPS = 24; SCENE = TL['total']; HOLD, WIPE = 0.5, 0.33; DUR = SCENE + HOLD; NF = int(round(DUR * FPS)); LW = 3.2; FLOORY = RT.FLOORY
VIG, GRAINS = RT.paper_finish_clean()

X0, X1, T_W0, T_W1 = 300, 600, 0.3, 3.0
S = 2.0                                                        # series Grok Bot (stickfig 'robot' prop, standard SEG)
HIPY = FLOORY - 104 * S                                        # slight knee bend so the planted-foot IK never runs out of reach
BOT = Figure('grokbot', X0, HIPY, 1, {'robot'}, scale=S)
BOT.move(T_W0, X1, HIPY, T_W1 - T_W0)
LN = {L['id']: L for L in TL['lines']}
T_LINE = LN['l1']['s']; T_END = LN['l5']['e']
def wt(lid, w, k=0):
    """start time of the k-th caption word in line lid that starts with w"""
    return [x['s'] for x in LN[lid]['words'] if x['w'].lower().startswith(w.lower())][k]
REST = 'front+mouth=1+lsh=14+lel=6+rsh=14+rel=6'
for k in [(0, 'idle+lean=3', 0), (2.95, 'front', .3), (3.25, 'front+wave', .25), (4.25, 'front+mouth=1', .3),
          (T_LINE - .1, 'front+mouth=1+rsh=52+rel=58+lsh=16+lel=8', .3),               # "Hello from..." open hand
          (LN['l1']['e'] + .02, REST, .3),
          (wt('l2', 'nice') - .12, 'front+mouth=2+lsh=38+lel=34+rsh=38+rel=34', .28),   # "Nice to meet you" both palms open
          (LN['l2']['e'] + .02, REST, .25),
          (wt('l3', "i'm") - .12, 'front+mouth=1+rsh=28+rel=-118+lsh=14+lel=6', .25),  # "I'm here" forearm across chest
          (wt('l3', 'help') - .1, 'front+mouth=1+lsh=52+lel=40+rsh=52+rel=40', .3),   # "help you get things done" offer
          (wt('l3', 'alongside') - .12, 'front+mouth=2+rsh=104+rel=10+lsh=14+lel=6', .35),  # sweep toward the crew
          (LN['l3']['e'] + .05, REST, .3),
          (wt('l4', 'starship') - .15, 'front+mouth=2+rsh=150+rel=-110+lsh=14+lel=6', .28),  # salute on the ship's name
          (wt('l4', 'here') - .08, 'front+mouth=2+lsh=40+lel=95+rsh=40+rel=95', .25),  # ta-da, hands up
          (LN['l4']['e'] + .02, REST, .25),
          (wt('l5', 'thanks') - .18, 'front+wave+wave=.6+mouth=2', .22),               # small wave on "Thanks!"
          (T_END + .5, 'front+mouth=2+lsh=14+lel=6+rsh=14+rel=6', .35)]:
    BOT.key(k[0] if k[0] > 0 else -1, k[1], k[2])
NODS = [LN[i]['s'] for i in ('l2', 'l3', 'l4', 'l5')] + [wt('l3', 'alongside'), wt('l4', 'help')]

def std_roots(F, t, P, bob):                                   # standard rig: both legs hang from the hip point
    x, y = F.pos_at(t); y = y + bob * F.scale
    return {(-1, True): (x, y), (1, True): (x, y)}
RT.leg_roots = std_roots                                       # Gait() looks this up at construction
G = RT.Gait(BOT, X0, X1, 38 * S, 11 * S)
T_IKOFF = T_W1 + .05

def talk(t):
    i = int(t * FPS); return float(ENV[i]) if i < len(ENV) else 0.0

def mod(t, P):
    tk = talk(t); P['talk'] = tk
    i = int(t * FPS); e2 = float(ENV[max(i - 2, 0)]) if i < len(ENV) else 0.0
    P['tilt'] += 7 * (tk - e2) + 3 * tk                         # episode head bob on syllable onsets
    for tn in NODS:                                             # sentence-start nods (episode recipe)
        u = t - tn
        if 0 <= u < .7: P['tilt'] += 10 * math.sin(math.pi * u / .35) * (1 - u / .7)
    if RT.walking(G, t):
        sw = math.sin(math.pi * G.phase(t)); P['rsh'] += 16 * sw; P['lsh'] -= 16 * sw
    wgt = 1 - clamp01((t - T_IKOFF) / .25)                     # planted-foot IK during the walk, released into the turn
    if wgt > 0:
        b = RT.bob_of(G, t); roots = std_roots(BOT, t, P, b); feet, _, _ = G.feet(t)
        for sd, (hk, kk) in ((-1, ('lhip', 'lkn')), (1, ('rhip', 'rkn'))):
            a1, a2 = RT.ik(roots[(sd, True)], feet[sd], BOT.seg['th'] * S, BOT.seg['sh'] * S, BOT.facing)
            P[hk] = lerp(P[hk], a1, wgt); P[kk] = lerp(P[kk], a2, wgt)
    return P
BOT.mod = mod

# ---------------------------------------------------------------- camera: fake depth, then 2/3 push-in
CHEST_Y = HIPY - 139                                        # mid-point of antenna-top (HIPY-330) .. mid-thigh (HIPY+52)
Z23 = 1.88                                                  # 382 world px * 1.88 = ~720 px = 2/3 of frame height
def cam(t):
    hx = BOT.pos_at(t)[0]
    k = ease(clamp01((t - T_W0 + .1) / (T_W1 - T_W0 + .3)))           # approach: tiny & high -> full figure, feet low
    z = lerp(0.42, 1.0, k); sx = lerp(820, 930, k); sy = lerp(600, 975, k)
    cx = hx - (sx - W / 2) / z; cy = FLOORY - (sy - H / 2) / z
    p = ease(clamp01((t - 4.15) / 0.85))                             # push-in to 2/3 shot, slow creep while talking
    zp = Z23 + .06 * clamp01((t - 5.0) / (T_END - 5.0))
    cx2, cy2 = hx, CHEST_Y
    return (lerp(cx, cx2, p), lerp(cy, cy2, p), lerp(z, zp, p))

def frame(t):
    boil = int(t * 8); img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, cam(t), boil)
    pen.line([(-3000, FLOORY + 2), (4000, FLOORY + 2)], 2.2, INK, 'floor', wob=.4)
    for i in range(-40, 60): pen.line([(i * 80, FLOORY + 3), (i * 80 - 18, FLOORY + 16)], 1.6, INK, f'fh{i}', wob=.3)
    BOT.draw(pen, t, RT.bob_of(G, t), w=5.5 * S ** .3)
    f = img.astype(np.float32) * VIG + GRAINS[boil % 4] * .6
    return np.clip(f, 0, 255).astype(np.uint8)

def poster():
    img = frame(3.7)                                         # mid-wave, full figure, facing camera
    pen = Pen(img, (960, 540, 1.0), 3)
    SETS.outlined(pen, 'HELLO, STARSHIP GROKBOT', (960, 120), 96, 7)
    pen.line([(560, 172), (1360, 167)], 5, INK, 'tul')
    pen.text('STARSHIP GROKBOT  \u00b7  Grok Bot says hello', (960, 212), 32, INK, 'hand')
    return img

_POSTER = None
def render(T):
    global _POSTER
    if _POSTER is None: _POSTER = poster()
    if T < HOLD: return _POSTER.copy()
    sc = frame(T - HOLD)
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
    ev = []; Ls = TL['lines']
    for i, L in enumerate(Ls):
        ws = [dict(x, s=x['s'] + HOLD, e=x['e'] + HOLD) for x in L['words']]; a = L['s'] + HOLD - .2
        nxt = Ls[i + 1]['s'] + HOLD - .2 if i + 1 < len(Ls) else DUR - .05
        b = min(L['e'] + HOLD + .5, nxt)
        kt = [f"{{\\k{int((ws[0]['s'] - a) * 100)}}}"]
        for j, x in enumerate(ws):
            end = ws[j + 1]['s'] if j + 1 < len(ws) else x['e']
            kt.append(f"{{\\kf{max(int((end - x['s']) * 100), 1)}}}{x['w']} ")
        fi = 120 if i == 0 else 60
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Line,,0,0,0,,{{\\fad({fi},120)\\move(960,1052,960,1038,0,180)}}" + ''.join(kt).strip())
    a0 = Ls[0]['s'] + HOLD - .2; b0 = min(Ls[-1]['e'] + HOLD + .5, DUR - .05)
    ev.append(f"Dialogue: 1,{ts(a0)},{ts(b0)},Name,,0,0,0,,{{\\fad(120,200)\\pos(960,972)\\fscx90\\fscy90\\t(0,140,\\fscx100\\fscy100)}}GROK BOT")
    open(path, 'w').write(hdr + '\n'.join(ev) + '\n')

def measure():
    """ink bbox of head+torso (exclude antenna/legs) at the 2/3 shot -> fraction of frame height"""
    t = 6.0; img = frame(t); ink = img.mean(2) < 90
    pen = Pen(np.zeros((H, W, 3), np.uint8), cam(t)); top = pen.S((0, HIPY - 330))[1]
    ys, xs = np.where(ink); print('z', cam(t)[2], 'ink top', ys.min(), 'hip screen y', pen.S((0, HIPY))[1])

if __name__ == '__main__':
    if '--poster' in sys.argv:
        im = poster(); cv2.imwrite(f'{D}/thumbnail.png', im); cv2.imwrite(f'{HERE}/grokbot-hello3-thumb.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 92]); sys.exit()
    if '--measure' in sys.argv: measure(); sys.exit()
    if '--still' in sys.argv:
        for a in sys.argv[sys.argv.index('--still') + 1:]: cv2.imwrite(f'{D}/rh_{a}.png', render(float(a)))
        sys.exit()
    captions(f'{D}/captions.ass'); raw = f'{D}/raw.mp4'
    p = subprocess.Popen(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '11', '-pix_fmt', 'yuv420p', raw], stdin=subprocess.PIPE)
    for i in range(NF): p.stdin.write(render(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    out = f'{HERE}/grokbot-hello-starship-v3.mp4'
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', raw, '-i', f'{D}/mix.wav', '-af', f'adelay={int(HOLD * 1000)}:all=1,apad', '-vf', f'ass={D}/captions.ass',
                    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-r', '24', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-t', f'{DUR}', '-movflags', '+faststart', out], check=True)
    print('done', out)
