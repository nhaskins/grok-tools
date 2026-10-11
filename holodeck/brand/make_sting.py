"""STARSHIP GROKBOT brand sting: 3.0 s, 1920x1080 @24, AAC stereo 48 kHz.
Ink draws a starship whose bridge is Grok Bot's boxy head (he salutes), it zips off with
speed lines (whoosh panned L->R), hand-lettered STARSHIP GROKBOT stamps in with an ink splat (ding),
then the ink fades back to clean paper. Audio is pure ffmpeg synthesis (no samples).
Usage: python make_sting.py [out.mp4]"""
import sys, math, subprocess, os
SP = '/workspace/holodeck/titan-hello-world/stick-poc'; sys.path.insert(0, SP)
import numpy as np, cv2
from stickfig import *
from inkset import W, H, paper_finish
import sets as SETS

FPS, DUR = 24, 3.0
NF = int(DUR * FPS)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'starship-grokbot-sting.mp4')
T_ZIP, T_ZIPEND, T_STAMP, T_OUT0, T_OUT1 = 1.0, 1.5, 1.55, 2.45, 2.85
CX, CY, SS = 900, 500, 1.6

def ell(c, rx, ry, a0=0, a1=2 * math.pi, n=40):
    return [(c[0] + rx * math.cos(a), c[1] + ry * math.sin(a)) for a in np.linspace(a0, a1, n)]

# ship parts in local coords (relative to CX,CY), stroke order = draw-on order
PARTS = [
    ('nacL', ell((-250, -78), 125, 20), True),
    ('pyL', [(-200, -58), (-150, 40)], False),
    ('nacR', ell((-230, -34), 125, 20), True),
    ('pyR', [(-180, -18), (-135, 46)], False),
    ('hull', ell((-120, 62), 112, 34), True),
    ('dish', ell((-5, 60), 10, 14, -math.pi / 2, math.pi / 2, 12), False),
    ('neck', [(-70, 36), (-30, -20), (20, -20), (-20, 36)], False),
    ('saucer', ell((60, -38), 165, 52), True),
    ('rim', ell((60, -26), 150, 36, .15, math.pi - .15, 24), False),
]
STROKE_T = (0.04, 0.80)

def partial(pts, k):
    if k >= 1: return pts
    P = np.array(pts, float); seg = np.linalg.norm(np.diff(P, axis=0), axis=1); L = np.concatenate([[0], np.cumsum(seg)])
    tgt = L[-1] * k; i = int(np.searchsorted(L, tgt)) - 1; i = max(0, min(i, len(seg) - 1))
    f = (tgt - L[i]) / max(seg[i], 1e-6)
    return [tuple(p) for p in P[:i + 1]] + [tuple(P[i] + (P[i + 1] - P[i]) * f)]

def ship_xf(t):
    """world offset + horizontal stretch: tiny wind-up, then zip off to the right"""
    dx, st = 0.0, 1.0
    if T_ZIP - .12 <= t < T_ZIP: dx = -28 * ease((t - (T_ZIP - .12)) / .12)
    elif t >= T_ZIP:
        u = clamp01((t - T_ZIP) / (T_ZIPEND - T_ZIP)); dx = -28 + 1900 * u ** 2.2; st = 1 + .35 * min(u * 3, 1)
    bob = 6 * math.sin(t * 7) if t < T_ZIP else 0
    return dx, st, bob

def X(p, t):
    dx, st, bob = ship_xf(t)
    return (CX + dx + p[0] * st * SS, CY + bob + p[1] * SS)

def draw_ship(pen, t):
    t0, t1 = STROKE_T; n = len(PARTS)
    for i, (sid, pts, closed) in enumerate(PARTS):
        a = t0 + (t1 - t0) * i / n * .85; b = a + (t1 - t0) / n * 1.6
        k = clamp01((t - a) / (b - a))
        if k <= 0: continue
        if closed and k >= 1: pen.fill([X(p, t) for p in pts], PAPER)
        pen.line([X(p, t) for p in partial(pts, k)], 6, INK, 'sh' + sid)
    # Grok Bot head as the bridge
    kb = clamp01((t - .62) / .2)
    if kb > 0:
        s = ease_out_back(kb)
        hx, hy = 66, -118; hw = 40 * s
        box = [(hx - hw, hy - hw), (hx + hw, hy - hw), (hx + hw, hy + hw * .9), (hx - hw, hy + hw * .9)]
        pen.fill([X(p, t) for p in box], PAPER); pen.line([X(p, t) for p in box], 6, INK, 'gbh', closed=True)
        if s > .6:
            for ex in (-14, 14): pen.dot(X((hx + ex, hy - 8), t), 7, INK)
            pen.rect(*X((hx - 16, hy + 12), t), *X((hx + 16, hy + 22), t), 4, INK, 'gbm')
            tip = X((hx + 4, hy - hw - 30), t)
            pen.line([X((hx, hy - hw), t), tip], 4, INK, 'gba'); 
            blink = (t > .95 and int(t * 10) % 2 == 0)
            pen.circle(tip, 7, 4, INK, 'gbt', fill=INK if blink else PAPER)
    # salute: little arm from the right side of the head up to the "brow"
    ks = clamp01((t - .82) / .12)
    if ks > 0 and t < T_ZIP + .1:
        sh = (106, -102); hand = (lerp(122, 104, ks), lerp(-72, -146, ks)); el = (lerp(136, 132, ks), lerp(-74, -112, ks))
        pen.line([X(sh, t), X(el, t), X(hand, t)], 5, INK, 'sal')
        pen.line([X((hand[0] - 2, hand[1]), t), X((hand[0] - 20, hand[1] + 4), t)], 5, INK, 'salh')

def speed_lines(pen, t):
    if t < T_ZIP: return
    dx, st, _ = ship_xf(t); head = CX + dx - 300 * st * SS
    fade = 1 - clamp01((t - (T_ZIPEND + .05)) / .35)
    if fade <= 0: return
    r = np.random.default_rng(7)
    for i in range(11):
        y = CY - 170 + i * 34 + r.uniform(-6, 6)
        x1 = min(head + r.uniform(-40, 40), W + 40)
        L = (180 + 520 * clamp01((t - T_ZIP) / .35)) * r.uniform(.6, 1.1)
        x0 = max(x1 - L * 1.3, CX - 700 + r.uniform(0, 200))
        if t > T_ZIPEND: x0 = lerp(x0, x1, clamp01((t - T_ZIPEND) / .4))
        if x1 - x0 > 20: pen.line([(x0, y), (x1, y)], 4 if i % 3 else 6, INK, f'sp{i}')
    for i in range(3):   # puff clouds left behind at the wind-up spot
        k = clamp01((t - T_ZIP) / .5)
        if k < 1: pen.circle((CX - 560 - 60 * k - i * 40, CY - 60 + i * 80), 24 + 50 * k, 4, INK, f'pf{i}')

def splat(pen, c, t, t0):
    k = ease_out((t - t0) / .12)
    if k <= 0: return
    r = np.random.default_rng(11)
    rad = [26 * (1 + .45 * r.uniform(-1, 1) + (.5 if j % 5 == 0 else 0)) for j in range(28)]
    pen.fill([(c[0] + k * rr * math.cos(a), c[1] + k * rr * math.sin(a)) for rr, a in zip(rad, np.linspace(0, 2 * math.pi, 28, endpoint=False))], INK)
    for j in range(7):
        a = r.uniform(0, 2 * math.pi); d = (38 + r.uniform(0, 40)) * k
        pen.dot((c[0] + d * math.cos(a), c[1] + d * math.sin(a)), r.uniform(3, 8) * k, INK)

def title(pen, t):
    k = (t - T_STAMP) / .22
    if k <= 0: return
    s = 1.0 + .6 * (1 - ease_out_back(clamp01(k), 1.6))
    splat(pen, (1650, 600), t, T_STAMP + .06)
    SETS.outlined(pen, 'STARSHIP GROKBOT', (960, 560), 132 * s, 8)
    ku = clamp01((t - T_STAMP - .2) / .25)
    if ku > 0: pen.line(partial([(470, 650), (960, 645), (1440, 652)], ku), 7, INK, 'ul')

VIG, GRAINS = paper_finish()
def frame(i):
    t = i / FPS
    img = np.full((H, W, 3), PAPER, np.uint8)
    pen = Pen(img, (960, 540, 1.0), int(t * 12))
    if t < T_OUT1:
        speed_lines(pen, t); draw_ship(pen, t); title(pen, t)
    f = img.astype(np.float32) * VIG + GRAINS[int(t * 12) % 4]
    fade = 1 - ease(clamp01((t - T_OUT0) / (T_OUT1 - T_OUT0)))
    pap = np.full_like(f, 0) + np.array(PAPER, np.float32) * VIG + GRAINS[int(t * 12) % 4]
    f = f * fade + pap * (1 - fade)
    return np.clip(f, 0, 255).astype(np.uint8)

def audio(path):
    whoosh = (f"anoisesrc=d=0.75:c=pink:r=48000:a=0.9,highpass=f=300,lowpass=f=5200,"
              f"aformat=channel_layouts=stereo,"
              f"aeval='val(ch)*pow(sin(PI*min(t/0.75,1)),2)*if(eq(ch,0),1-0.85*t/0.75,0.15+0.85*t/0.75)':c=same,"
              f"adelay={int((T_ZIP - .08) * 1000)}|{int((T_ZIP - .08) * 1000)}")
    ding = ("aevalsrc='0.42*sin(2*PI*1568*t)*exp(-3.2*t)+0.2*sin(2*PI*2349*t)*exp(-4.5*t)+0.1*sin(2*PI*3136*t)*exp(-6*t)"
            "|0.42*sin(2*PI*1568*t)*exp(-3.2*t)+0.2*sin(2*PI*2349*t)*exp(-4.5*t)+0.1*sin(2*PI*3136*t)*exp(-6*t)':s=48000:d=1.4,"
            f"adelay={int((T_STAMP + .06) * 1000)}|{int((T_STAMP + .06) * 1000)}")
    thud = ("aevalsrc='0.5*sin(2*PI*95*t)*exp(-14*t)|0.5*sin(2*PI*95*t)*exp(-14*t)':s=48000:d=0.4,"
            f"adelay={int((T_STAMP + .06) * 1000)}|{int((T_STAMP + .06) * 1000)}")
    scratch = ("anoisesrc=d=0.8:c=white:r=48000:a=0.08,bandpass=f=3500:w=2500,"
               "aeval='val(0)*(0.6+0.4*sin(2*PI*9*t))':c=mono,aformat=channel_layouts=stereo")
    fc = (f"{scratch}[s];{whoosh}[w];{ding}[d];{thud}[h];[s][w][d][h]amix=inputs=4:normalize=0:duration=longest,"
          f"apad,atrim=0:{DUR},afade=t=out:st={DUR - .35}:d=0.35,volume=-5dB,alimiter=limit=0.89,aformat=sample_rates=48000:channel_layouts=stereo[a]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-filter_complex', fc, '-map', '[a]', '-c:a', 'pcm_s16le', path], check=True)

if __name__ == '__main__':
    wav = OUT + '.wav'; audio(wav)
    if '--still' in sys.argv:
        for tt in (0.4, 0.95, 1.2, 1.8, 2.3, 2.95): cv2.imwrite(f'/tmp/sting_{tt}.png', frame(int(tt * FPS)))
        sys.exit()
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-tune', 'animation', '-pix_fmt', 'yuv420p',
           '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-t', str(DUR), '-movflags', '+faststart', OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(NF): p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait(); os.remove(wav); print('done', OUT)
