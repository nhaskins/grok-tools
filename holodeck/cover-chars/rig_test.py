"""~10 s RIG MOVEMENT TEST: cover robot (boxbot) + cover human (bean) walk toward each other with planted-foot gait
(2-bone leg IK onto fixed footfalls), robot waves, they alternate 'talking' (syllable-pulse envelopes), gestures,
head bobs, listener nods; ends on the human's chin-think. Wide -> slight push-in. Silent track.
    python rig_test.py | --still t ... | --sheet"""
import sys, os, math, subprocess
sys.path.insert(0, '/workspace/holodeck/titan-hello-world/stick-poc')
import numpy as np, cv2
from stickfig import *
from inkset import W, H, paper_finish
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24; DUR = 10.0; NF = int(DUR * FPS); LW = 3.2
FLOORY = 900

# ---------------------------------------------------------------- talk envelopes (fake syllable pulses)
def syl_env(t0, t1, seed, rate=5.2):
    rng = np.random.default_rng(seed); ts = []; x = t0 + .04
    while x < t1 - .05: ts.append((x, .55 + .45 * rng.random())); x += 1 / rate * (.75 + .5 * rng.random())
    return ts
LINES = {'robot': [(3.55, 5.15, 1), (7.45, 8.45, 3)], 'human': [(5.4, 7.2, 2)]}
SYL = {k: [s for a, b, sd in v for s in syl_env(a, b, sd)] for k, v in LINES.items()}
def talk(who, t):
    return min(1.0, max([a * math.exp(-((t - ts) / .065) ** 2) for ts, a in SYL[who]] + [0.0]))
def speaking(who, t): return any(a - .1 <= t <= b + .1 for a, b, _ in LINES[who])

# ---------------------------------------------------------------- figures
ROB_S, HUM_S = 1.76, 2.0
ROB_SEG, HUM_SEG = dict(th=44, sh=46, ua=36, fa=52), dict(th=52, sh=50, ua=40, fa=42)
RX0, RX1, HX0, HX1 = 520, 790, 1400, 1120
T_W0, T_W1 = 0.35, 2.75
ROBOT = Figure('rigbot', RX0, FLOORY - 138, 1, {'boxbot', 'antenna', 'feet'}, scale=ROB_S, seg=ROB_SEG)
HUMAN = Figure('righuman', HX0, FLOORY - 188, -1, {'bean', 'tuft', 'bowtie', 'shoes'}, scale=HUM_S, seg=HUM_SEG)
ROBOT.move(T_W0, RX1, FLOORY - 138, T_W1 - T_W0); HUMAN.move(T_W0 + .1, HX1, FLOORY - 188, T_W1 - T_W0 - .1)
T_THINK = 8.55
THINK = 'think+rsh=18+rel=162+lsh=-66+lel=88+tilt=-4+lean=10'
for k in [(0, 'idle', 0), (2.75, 'wave+lean=4', .3), (3.45, 'idle+lean=3', .3), (3.65, 'palm+lean=5', .3), (4.4, 'idle+rsh=40+rel=-50+lean=4', .3),
          (4.8, 'palm+lean=6', .25), (5.3, 'idle+look_r', .3), (7.4, 'palm+lean=4', .25), (8.1, 'idle+rsh=110+rel=40', .25),
          (8.6, 'idle+look_r+lean=3', .4)]:
    ROBOT.key(k[0] if k[0] > 0 else -1, k[1], k[2])
for k in [(0, 'idle', 0), (2.9, 'idle+rsh=120+rel=30', .3), (3.4, 'idle', .3), (5.35, 'palm+lean=6', .25), (6.0, 'idle+rsh=105+rel=35+lean=4', .25),
          (6.6, 'palm+lean=8', .25), (7.25, 'idle+lean=3', .3), (8.55, THINK, .45)]:
    HUMAN.key(k[0] if k[0] > 0 else -1, k[1], k[2])

# ---------------------------------------------------------------- planted-foot gait: footfalls + 2-bone IK
def leg_roots(F, t, P, bob):
    """exact leg-root positions, replicating _draw's lean/breathing so IK targets match what gets drawn"""
    x, y = F.pos_at(t); S = F.scale; f = F.facing; y = y + bob * S
    lean = P['lean'] + 1.3 * math.sin(t * 2 * math.pi / 3.1 + len(F.name)); ul = math.radians(lean)
    up = (f * math.sin(ul), -math.cos(ul)); hip = (x, y)
    sho = (hip[0] + up[0] * F.seg['torso'] * S, hip[1] + up[1] * F.seg['torso'] * S)
    neck = (sho[0] + up[0] * F.seg['neck'] * S, sho[1] + up[1] * F.seg['neck'] * S)
    return F._cust_geom(hip, sho, neck, up, P, f, S)['roots']

def ik(root, foot, L1, L2, f, flip=False):
    """returns (thigh angle, knee angle) in rig convention (deg from down, + = toward facing), knee bends forward"""
    dx, dy = (foot[0] - root[0]) * f, foot[1] - root[1]
    d = min(math.hypot(dx, dy), (L1 + L2) * .999); d = max(d, abs(L1 - L2) + 1e-3)
    phi = math.degrees(math.atan2(dx, dy))
    al = math.degrees(math.acos(np.clip((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1)))
    be = math.degrees(math.acos(np.clip((L2 * L2 + d * d - L1 * L1) / (2 * L2 * d), -1, 1)))
    a1, a2abs = (phi - al, phi + be) if flip else (phi + al, phi - be)
    return a1, a2abs - a1

class Gait:
    def __init__(self, F, x0, x1, step, lift):
        self.F = F; self.x0 = x0; D = x1 - x0; self.n = max(1, round(abs(D) / step)); self.h = D / self.n; self.lift = lift
        P0 = pose('stand'); r = leg_roots(F, 0, dict(P0, lean=-1.3 * math.sin(len(F.name))), 0)  # upright reference
        self.ox = {sd: r[(sd, True)][0] - F.pos_at(-1)[0] for sd in (-1, 1)}
    def phase(self, t):
        x = self.F.pos_at(t)[0]; return clamp01((x - self.x0) / (self.h * self.n)) * self.n
    def feet(self, t):
        ph = self.phase(t); k = min(int(ph), self.n - 1); fr = ph - k
        Fk = lambda i, sd: self.x0 + (i + .5) * self.h + self.ox[sd]
        mv = 1 if k % 2 == 0 else -1                       # which leg swings this step
        out = {}
        out[-mv] = (Fk(k, -mv), FLOORY)
        sx = lerp(Fk(k - 1, mv), Fk(k + 1, mv), ease(fr))
        out[mv] = (sx, FLOORY - self.lift * math.sin(math.pi * fr) * (0 < ph < self.n))
        return out, ph, fr
GR = Gait(ROBOT, RX0, RX1, 68, 20); GH = Gait(HUMAN, HX0, HX1, 92, 26)

def walking(g, t): ph = g.phase(t); return 0 < ph < g.n
def bob_of(g, t):
    if not walking(g, t): return 0.0
    _, ph, fr = g.feet(t); return 2.2 * math.cos(2 * math.pi * fr)          # down at double support, up mid-stance

NODS = {'robot': [5.75, 6.55], 'human': [3.95, 4.7, 7.85]}
def make_mod(F, g, who, seed):
    def mod(t, P):
        tk = talk(who, t); P['talk'] = tk
        P['tilt'] += 9 * tk * math.sin(t * 7.3 + seed)                        # head bob while talking
        for tn in NODS[who]:
            u = t - tn
            if 0 <= u < .7: P['tilt'] += 11 * math.sin(math.pi * u / .35) * (1 - u / .7)
        if walking(g, t):                                                       # arm counter-swing
            ph = g.phase(t); sw = math.sin(math.pi * ph)
            P['rsh'] += 18 * sw; P['lsh'] -= 18 * sw
        if who == 'robot': P['antamp'] = 6 + 6 * walking(g, t) + 6 * (2.7 < t < 3.5)
        b = bob_of(g, t); roots = leg_roots(F, t, P, b)
        if who == 'human' and t > T_THINK:                                      # arm IK: near hand to the chin (+ taps)
            wk = ease((t - T_THINK) / .45)
            x, y = F.pos_at(t); S = F.scale; f = F.facing; y += b * S
            lean = P['lean'] + 1.3 * math.sin(t * 2 * math.pi / 3.1 + len(F.name)); ul = math.radians(lean)
            up = (f * math.sin(ul), -math.cos(ul)); L = (F.seg['torso'] + F.seg['neck']) * S
            neck = (x + up[0] * L, y + up[1] * L); ht = math.radians(lean + P['tilt'] - 14 * P['lookup']); R = F.seg['r'] * S
            head = (neck[0] + f * math.sin(ht) * R, neck[1] - math.cos(ht) * R)
            tap = 6 * max(0.0, math.sin(2 * math.pi * 1.6 * (t - T_THINK - .5))) ** 2 * (t > T_THINK + .5)
            chin = (head[0] + f * R * .32, head[1] + R * .98 + tap)
            a1, a2 = ik(roots[(1, False)], chin, F.seg['ua'] * S, F.seg['fa'] * S, f, flip=True)
            P['rsh'], P['rel'] = lerp(P['rsh'], a1, wk), lerp(P['rel'], a2, wk)
        feet, _, _ = g.feet(t)
        for sd, (hk, kk) in ((-1, ('lhip', 'lkn')), (1, ('rhip', 'rkn'))):
            P[hk], P[kk] = ik(roots[(sd, True)], feet[sd], F.seg['th'] * F.scale, F.seg['sh'] * F.scale, F.facing)
        return P
    return mod
ROBOT.mod = make_mod(ROBOT, GR, 'robot', 1); HUMAN.mod = make_mod(HUMAN, GH, 'human', 2)

# ---------------------------------------------------------------- camera + frame
def cam(t):
    k = ease((t - 3.4) / 4.5)
    return (lerp(960, 955, k), lerp(600, 585, k), lerp(1.0, 1.2, k))
V2 = '--v2' in sys.argv
def paper_finish_clean():
    """v2: same as inkset.paper_finish (same RNG draw order -> identical fine grain/fibres/vignette) but WITHOUT the
    low-frequency 'low * 3' mottling, whose static ~30-60 px blotches read as a cloud around the robot's head."""
    r = np.random.default_rng(1)
    r.normal(0, 1, (34, 60))                                   # draw + discard the mottle field to keep the RNG in step
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vig = (1 - 0.16 * np.clip(d - 0.35, 0, None) ** 1.6).astype(np.float32)
    grains = []
    for i in range(4):
        g = r.normal(0, 5.0, (H, W)).astype(np.float32)
        fib = cv2.GaussianBlur(r.normal(0, 7, (H, W)).astype(np.float32), (0, 0), sigmaX=6, sigmaY=0.6)
        grains.append((g + fib)[..., None])
    return vig[..., None], grains
VIG, GRAINS = paper_finish_clean() if V2 else paper_finish()
def frame(t):
    boil = int(t * 8); img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, cam(t), boil)
    pen.line([(-400, FLOORY + 2), (2300, FLOORY + 2)], 2.2, INK, 'floor', wob=.4)
    for i in range(-6, 30): pen.line([(i * 80, FLOORY + 3), (i * 80 - 18, FLOORY + 16)], 1.6, INK, f'fh{i}', wob=.3)
    ROBOT.draw(pen, t, bob_of(GR, t), w=LW); HUMAN.draw(pen, t, bob_of(GH, t), w=LW)
    Pen(img, (960, 540, 1.0), boil).text('RIG TEST', (120, 60), 30, INK, 'serif')
    f = img.astype(np.float32) * VIG + GRAINS[boil % 4] * .6
    return np.clip(f, 0, 255).astype(np.uint8)

def foot_report():
    """measure stance-foot drift: drawn foot (leg end) of the planted leg, frame to frame"""
    worst = {}
    for F, g, nm in ((ROBOT, GR, 'robot'), (HUMAN, GH, 'human')):
        pen = Pen(np.full((H, W, 3), PAPER, np.uint8), (960, 540, 1.0), 0); prev = None; mx = 0; vert = 0
        for i in range(NF):
            t = i / FPS; feet, ph, fr = g.feet(t)
            F._last = None
            P = F.pose_at(t); P = F.mod(t, dict(P))
            roots = leg_roots(F, t, P, bob_of(g, t)); S = F.scale; f = F.facing
            ends = {}
            for sd, hk, kk in ((-1, 'lhip', 'lkn'), (1, 'rhip', 'rkn')):
                r = roots[(sd, True)]; a1, a2 = math.radians(P[hk]), math.radians(P[hk] + P[kk])
                j = (r[0] + f * math.sin(a1) * F.seg['th'] * S, r[1] + math.cos(a1) * F.seg['th'] * S)
                ends[sd] = (j[0] + f * math.sin(a2) * F.seg['sh'] * S, j[1] + math.cos(a2) * F.seg['sh'] * S)
            mvleg = (1 if int(min(ph, g.n - 1e-9)) % 2 == 0 else -1) if 0 < ph < g.n else None
            if prev:
                for sd in (-1, 1):
                    if sd != mvleg and (prev[1] is None or sd != prev[1]):
                        mx = max(mx, abs(ends[sd][0] - prev[0][sd][0])); vert = max(vert, abs(ends[sd][1] - FLOORY))
            prev = (ends, mvleg)
        worst[nm] = (round(mx, 2), round(vert, 2))
    return worst

if __name__ == '__main__':
    if '--still' in sys.argv:
        for a in sys.argv[sys.argv.index('--still') + 1:]: cv2.imwrite(f'{HERE}/rt_{a}.png', frame(float(a)))
        sys.exit()
    if '--feet' in sys.argv: print('planted-foot drift px (max horiz per frame, max vert off floor):', foot_report()); sys.exit()
    out = f'{HERE}/rig-test-v2.mp4' if V2 else f'{HERE}/rig-test.mp4'
    p = subprocess.Popen(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-t', str(DUR),
                          '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                          '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(NF): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('done', out)
