"""'Thinking with AI' book-cover recreation in the stick-figure rig (test, not an episode).
Cover robot (boxbot: cube head on a box torso, antenna ball) leans toward the cover human (bean torso, tuft, bow tie,
thinking pose, knee up) under a scribbled thought cloud with a small thought circle; serif lettering top and bottom.
Beat: ink draws in (0-2.8 s) -> gentle idle (chin tap, robot lean/bob, antenna wiggle, knee step, cloud boil) -> settles
on the cover pose and holds. Coordinates come from the 190x327 cover (proportions only, not traced).
    python cover.py            -> thinking-with-ai-cover-test.mp4 (1080p24, silent AAC track)
    python cover.py --still T  -> still_T.png        python cover.py --compare -> compare.png"""
import sys, os, math, subprocess
sys.path.insert(0, '/workspace/holodeck/titan-hello-world/stick-poc')
import numpy as np, cv2
from stickfig import *
from inkset import W, H, paper_finish, thoughtcloud
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24; DUR = 8.5; NF = int(DUR * FPS)
REF = '/workspace/natehaskinscom/static/images/thinking-with-ai-doodle.png'

def C(x4, y4):            # 4x-upscaled cover-crop coords -> screen (cover px * 3.1, centred)
    x, y = x4 / 4, y4 / 4 + 20
    return 960 + (x - 95) * 3.1, 33 + y * 3.1

LW = 3.2                  # thin single-weight cover line
# ---------------------------------------------------------------- timing
T_IDLE0, T_IDLE1, T_SETTLE = 2.9, 6.6, 7.3
def amt(t):               # idle motion amount: 0 while drawing in, ramps up, back to 0 to settle on the cover pose
    return ease((t - T_IDLE0) / .5) * (1 - ease((t - T_IDLE1) / (T_SETTLE - T_IDLE1)))
REVEAL = dict(cloud=(0.0, 1.0), robot=(0.55, 1.65), human=(1.15, 2.25), title=(1.85, 2.6), name=(2.2, 2.8))

# ---------------------------------------------------------------- characters
ROBOT_POSE = {'lean': 4, 'tilt': 6, 'rsh': 31, 'rel': -66, 'lsh': -10, 'lel': -122, 'lhip': 2, 'lkn': 0, 'rhip': 3, 'rkn': -1}
HUMAN_POSE = {**POSES['think'], **POSES['kneeup'], **dict(lean=16, tilt=-4, rsh=18, rel=162, lsh=-66, lel=88, rhip=85, rkn=-62, lhip=-4, lkn=-2, look=0)}
rx, ry = C(195, 770); hx, hy = C(530, 690)
ROBOT = Figure('coverbot', rx, ry, 1, {'boxbot', 'antenna', 'feet'}, scale=1.76, seg=dict(th=44, sh=46, ua=36, fa=52))
HUMAN = Figure('coverhuman', hx, hy, -1, {'bean', 'tuft', 'bowtie', 'shoes'}, scale=2.0, seg=dict(th=52, sh=50, ua=40, fa=42))
ROBOT.key(-1, ROBOT_POSE, 0); HUMAN.key(-1, HUMAN_POSE, 0)

def robot_mod(t, P):
    a = amt(t)
    P['lean'] += 3.0 * a * math.sin(2 * math.pi * .45 * t)                    # leans in toward the human
    P['tilt'] += 4 * a * math.sin(2 * math.pi * .45 * t + .8)
    P['antamp'] = 9 * a                                                       # antenna ball wiggle
    P['lel'] += 10 * a * math.sin(2 * math.pi * .7 * t)
    return P
def human_mod(t, P):
    a = amt(t)
    tap = max(0.0, math.sin(2 * math.pi * 1.7 * t)) ** 2                     # chin taps
    P['rel'] -= 9 * a * tap; P['rsh'] -= 3 * a * tap
    st = math.sin(2 * math.pi * .5 * t)                                       # knee-lift step
    P['rhip'] += 9 * a * st; P['rkn'] -= 7 * a * st
    P['tilt'] += 5 * a * math.sin(2 * math.pi * .35 * t + 1.2)
    return P
ROBOT.mod = robot_mod; HUMAN.mod = human_mod

# ---------------------------------------------------------------- elements (each drawn on its own layer)
def el_cloud(pen, t):
    cx, cy = C(300, 296)
    thoughtcloud(pen, (cx, cy), 168, 138, t, 'cloud', n=12, w=LW, seed=7, dip=.12, boil=amt(t) + .3,
                 puffs=((*C(345, 600), 23),))
def el_robot(pen, t):
    bob = 2.2 * amt(t) * math.sin(2 * math.pi * .9 * t)
    ROBOT.draw(pen, t, bob, w=LW)
def el_human(pen, t):
    HUMAN.draw(pen, t, 0, w=LW)
def el_title(pen, t):
    pen.text('Thinking with AI', (960, 68), 76, INK, 'serif')
def el_name(pen, t):
    pen.text('Nate Haskins', (960, 1018), 36, INK, 'serif')
ELEMENTS = [('cloud', el_cloud), ('robot', el_robot), ('human', el_human), ('title', el_title), ('name', el_name)]

KEY = np.array([255, 0, 255], np.uint8)
def layer(fn, t, boil):
    a = np.full((H, W, 3), PAPER, np.uint8); fn(Pen(a, (960, 540, 1.0), boil), t)
    b = np.full((H, W, 3), KEY, np.uint8); fn(Pen(b, (960, 540, 1.0), boil), t)
    cov = np.abs(b.astype(np.int16) - KEY).sum(2) > 40          # covered = ink or paper fill
    return a, cov

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
NOISE = cv2.GaussianBlur(np.random.default_rng(3).random((H, W)).astype(np.float32), (0, 0), 25)
NOISE = (NOISE - NOISE.min()) / (NOISE.max() - NOISE.min())
def field(name, cov):
    """per-pixel 'arrival time' 0..1 for the pen sweep: cloud traced round its centre, figures top->bottom, text left->right"""
    ys, xs = np.nonzero(cov)
    if not len(ys): return np.zeros((H, W), np.float32)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    if name == 'cloud':
        cx, cy = C(300, 296); f = (np.arctan2(YY - cy, XX - cx) / (2 * np.pi) + .75) % 1
    elif name in ('title', 'name'):
        f = (XX - x0) / max(x1 - x0, 1)
    else:
        f = (YY - y0) / max(y1 - y0, 1)
    return np.clip(.85 * f + .15 * NOISE, 0, 1)

VIG, GRAINS = paper_finish()
def frame(t):
    boil = int(t * 8)
    out = np.full((H, W, 3), PAPER, np.uint8)
    for name, fn in ELEMENTS:
        a0, a1 = REVEAL[name]
        if t < a0: continue
        img, cov = layer(fn, t, boil)
        if t < a1:
            p = ease((t - a0) / (a1 - a0)) * 1.12
            al = np.clip((p - field(name, cov)) / .05, 0, 1) * cov
            out = (out * (1 - al[..., None]) + img * al[..., None]).astype(np.uint8)
        else:
            out[cov] = img[cov]
    f = out.astype(np.float32) * VIG + GRAINS[boil % 4] * .6
    return np.clip(f, 0, 255).astype(np.uint8)

def ref_img():
    a = cv2.imread(REF, cv2.IMREAD_UNCHANGED)
    if a.ndim == 3 and a.shape[2] == 4:
        al = a[:, :, 3:] / 255.; a = (a[:, :, :3] * al + 255 * (1 - al)).astype(np.uint8)
    return a

if __name__ == '__main__':
    if '--still' in sys.argv:
        for a in sys.argv[sys.argv.index('--still') + 1:]: cv2.imwrite(f'{HERE}/still_{a}.png', frame(float(a)))
        sys.exit()
    if '--compare' in sys.argv:
        ref = ref_img(); fr = frame(DUR - .3)
        h = 1000
        L = cv2.resize(ref, (int(ref.shape[1] * h / ref.shape[0]), h), interpolation=cv2.INTER_LANCZOS4)
        x0 = int(960 - 95 * 3.1); Rr = fr[33:33 + int(327 * 3.1), max(x0, 0):x0 + int(190 * 3.1)]   # the cover-sized region
        Rr = cv2.resize(Rr, (int(Rr.shape[1] * h / Rr.shape[0]), h), interpolation=cv2.INTER_AREA)
        pad = np.full((h + 90, L.shape[1] + Rr.shape[1] + 90, 3), 255, np.uint8)
        pad[60:60 + h, 30:30 + L.shape[1]] = L; pad[60:60 + h, 60 + L.shape[1]:60 + L.shape[1] + Rr.shape[1]] = Rr
        cv2.putText(pad, 'original doodle (190x327, lanczos)', (30, 40), cv2.FONT_HERSHEY_SIMPLEX, .9, (60, 60, 60), 2, cv2.LINE_AA)
        cv2.putText(pad, 'stick rig render (final frame)', (60 + L.shape[1], 40), cv2.FONT_HERSHEY_SIMPLEX, .9, (60, 60, 60), 2, cv2.LINE_AA)
        cv2.imwrite(f'{HERE}/compare.png', pad); print('compare.png'); sys.exit()
    out = f'{HERE}/thinking-with-ai-cover-test.mp4'
    p = subprocess.Popen(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-t', str(DUR),
                          '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                          '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(NF): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('done', out)
