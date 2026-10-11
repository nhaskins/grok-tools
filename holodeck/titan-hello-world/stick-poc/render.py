"""Titan stick-figure proof of concept: verse 1 (49.0-66.5 s).
Usage:  python render.py                 -> full render to titan-stick-verse1-poc.mp4
        python render.py --frames 52 56  -> write raw PNG frames (no captions) for checking
"""
import sys, os, math, json, time, subprocess
import numpy as np, cv2
from stickfig import *
from inkset import stars_field, sparkle, webhook, ship, console, chair, paper_finish

HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE)
T0, T1, FPS, W, H = 49.0, 66.5, 24, 1920, 1080
BOIL_FPS = 12
BEATS = np.load(f'{PROJ}/beats.npy'); BARS = np.load(f'{PROJ}/bars.npy')
LY = json.load(open(f'{PROJ}/lyric-timing.json'))
def word(w, nth=0):
    """time of the nth sung occurrence of word w inside the segment"""
    hits = [x['s'] for l in LY for x in l['words'] if x['w'].strip(',!.').lower() == w.lower() and T0 <= x['s'] < T1 + 2]
    return hits[nth]
def since(arr, t):
    p = arr[arr <= t]; return t - p[-1] if len(p) else 9.0

# bars inside the window: 50.29 52.13 53.94 55.75 57.59 59.40 61.21 63.02 64.83 66.46
B = {i: float(b) for i, b in enumerate(BARS)}
bar = lambda t: float(BARS[np.argmin(abs(BARS - t))])
CUT_B, CUT_C, PUSH_C, CUT_D, PUSH_D, CUT_E, PUSH_E, CUT_F = (bar(x) for x in (50.29, 53.94, 55.75, 57.59, 59.40, 61.21, 63.02, 64.83))

FLOOR = 880

# ------------------------------------------------------------------ cast
def make_cast():
    c = {}
    # bridge (wide / medium) cast
    cap = Figure('captain', 645, FLOOR - 110, 1, {'cap', 'badge'})
    cap.key(0, 'idle').key(49.6, 'idle+look_r', .4)
    cap.move(CUT_C - 0.01, 718, 820, 0)                          # seated in the chair from shot C
    cap.key(CUT_C - 0.01, 'sit', 0).key(word("titan's") - .12, 'sit+thumbs', .22)
    cap.key(word('bridge') - .1, 'sit+tada', .25).key(word('logs') - .05, 'sit+look_l', .3)
    c['captain'] = cap
    rk = Figure('riker', 1240, FLOOR - 110, 1, {'beard', 'badge'})
    rk.key(0, 'console').key(49.4, 'steer', .3).key(word('logs'), 'console+look_l', .3)
    rk.key(CUT_D - 0.01, 'console', 0).key(word('helm') - .1, 'steer', .2)
    rk.key(word('grin') - .2, 'grin', .28).key(word('plan') - .15, 'plan', .3)
    c['riker'] = rk
    en = Figure('ensign', 525, FLOOR - 110, -1, {'ponytail', 'badge'})
    en.key(0, 'console').key(word('logs') + .25, 'surprise', .3)
    c['ensign'] = en
    # viewscreen-shot cast (seen from behind, foreground)
    bc = Figure('cap_back', 300, 950, 1, {'cap'}, back=True, scale=3.0)
    bc.key(0, 'front').key(word('past') - .15, 'front+pointupL', .25).key(word('fly') + .15, 'front', .4)
    bc.key(CUT_E, 'front', 0).key(word('line') - .15, 'front+handear', .25).key(word('man') - .1, 'front+thumbs', .2)
    c['cap_back'] = bc
    br = Figure('rik_back', 1630, 950, -1, {'beard'}, back=True, scale=3.0)
    br.key(0, 'front').key(word('webhooks'), 'front+look_l', .3).key(CUT_E, 'front', 0)
    br.key(word('enterprise') - .1, 'front+pointup', .25)
    c['rik_back'] = br
    pic = Figure('picard', 960, 700, 1, {'shine', 'badge', 'collar'}, col=PAPER, scale=2.6)
    pic.key(0, 'front').key(word('picard') + .25, 'front+wave', .25).key(word('line') + .1, 'front+smile', .3)
    pic.key(word('man') - .1, 'front+thumbs', .2)
    c['picard'] = pic
    return c
CAST = make_cast()

# ------------------------------------------------------------------ props / set pieces
def logs_stack(pen, t, x, base):
    t0 = word('logs') - .05
    if t < t0: n = 3
    else: n = int(3 + min(t - t0, .6) / .6 * 34 + max(t - t0 - .6, 0) * 22)
    sway = 0 if t < t0 else min(t - t0, 1.5) / 1.5
    r = np.random.default_rng(5)
    jx = r.normal(0, 4, 120); ja = r.normal(0, 2.5, 120)
    for i in range(min(n, 120)):
        h = i / max(n, 1)
        cx = x + jx[i] + sway * 34 * math.sin(t * 5.5) * h ** 2
        cy = base - 7 - i * 10
        a = math.radians(ja[i] + sway * 6 * math.sin(t * 5.5) * h)
        ca, sa = math.cos(a), math.sin(a)
        pts = [(cx + px * ca - py * sa, cy + px * sa + py * ca) for px, py in ((-40, -5), (40, -5), (40, 5), (-40, 5))]
        pen.fill(pts, PAPER); pen.line(pts, 3, INK, f'log{i}', closed=True)
        if i % 3 == 0: pen.line([(cx - 30, cy), (cx + 10, cy)], 2, INK, f'lt{i}', wob=0.4)

def bridge_set(pen, t):
    pen.line([(-600, FLOOR), (2500, FLOOR)], 6, INK, 'floor')
    for k in range(-6, 30):
        x = k * 90; pen.line([(x, FLOOR + 4), (x - 28, FLOOR + 40)], 2.5, INK, f'fh{k}', wob=0.6)
    # viewscreen with live stars
    vx0, vy0, vx1, vy1 = 610, 110, 1310, 470
    pen.rect(vx0 - 14, vy0 - 14, vx1 + 14, vy1 + 14, 5, INK, 'vsframe')
    pen.rect(vx0, vy0, vx1, vy1, 0, fill=INK)
    stars_field(pen, (vx0, vy0, vx1, vy1), t, 0.07, n=90)
    # ceiling rails
    pen.line([(-600, 60), (520, 60), (580, 100)], 4, INK, 'rail1'); pen.line([(1340, 100), (1400, 60), (2500, 60)], 4, INK, 'rail2')
    # USS TITAN sign
    pen.text('U.S.S. TITAN', (960, 58), 44, INK, 'marker')
    tt = t - word("titan's")
    if 0 < tt < 0.9:
        k = ease_out(tt / .35); fade = 1 - clamp01((tt - .5) / .4)
        if fade > 0:
            for i in range(10):
                a = i * math.pi / 5 + 0.3; r0, r1 = 150 + 30 * k, 150 + 75 * k
                pen.line([(960 + r0 * math.cos(a) * 1.5, 58 + r0 * math.sin(a) * .35), (960 + r1 * math.cos(a) * 1.5, 58 + r1 * math.sin(a) * .35)], 4 * fade + .5, INK, f'burst{i}')
    console(pen, 1300, 1470, 712, sid='helm', label='HELM')
    console(pen, 270, 440, 712, sid='ops', mirror=True, label='OPS')
    chair(pen, 720)

# ------------------------------------------------------------------ shots
def shot_bridge(img, t, cam, boil, bob, focus=None):
    pen = Pen(img, cam, boil)
    bridge_set(pen, t)
    logs_stack(pen, t, 355, 712 + 4)
    for n in ('captain', 'riker', 'ensign'):
        CAST[n].draw(pen, t, bob)
    if t >= CUT_D:   # Riker callout
        k = ease_out_back((t - word('riker') + .05) / .3)
        if k > 0.01 and t < PUSH_D + .1:
            hx, hy = CAST['riker'].pos_at(t)
            pen.text('RIKER', (hx - 150, hy - 255), 46 * max(k, .05), INK, 'marker')
            pen.line([(hx - 105, hy - 225), (hx - 60, hy - 185), (hx - 32, hy - 170)], 4, INK, 'rkarrow')
            pen.line([(hx - 32, hy - 170), (hx - 50, hy - 168)], 4, INK, 'rka1'); pen.line([(hx - 32, hy - 170), (hx - 40, hy - 186)], 4, INK, 'rka2')
        tg = t - word('grin')
        if 0 < tg < 0.7:     # "ding" sparkle off the grin
            hx, hy = CAST['riker'].pos_at(t)
            sparkle(pen, (hx + 36, hy - 112), 12 * ease_out_back(tg / .2) * (1 - clamp01((tg - .45) / .25)) + .1, INK, 'ding')
        if t > word('plan') - .1 and t < CUT_E:
            pen.text('the plan:', (CAST['riker'].pos_at(t)[0] + 175, 540), 34, INK, 'hand',
                     alpha=clamp01((t - word('plan')) / .2))
    return pen

def shot_screen(img, t, cam, boil, bob, picard=False):
    pen = Pen(img, cam, boil)
    vx0, vy0, vx1, vy1 = 150, 70, 1770, 790
    pen.rect(vx0 - 18, vy0 - 18, vx1 + 18, vy1 + 18, 6, INK, 'bigframe')
    # contents drawn on a separate black canvas, then clipped into the screen rect
    sub = np.full_like(img, INK); sp = Pen(sub, cam, boil)
    if not picard:
        push = ease((t - CUT_B) / (CUT_C - CUT_B))
        stars_field(sp, (vx0, vy0, vx1, vy1), t, 0.08 + 0.18 * push, n=170, streak=0.12 + 0.35 * push)
        ts = t - word('stars')
        if ts > 0:
            r = np.random.default_rng(11)
            for i in range(7):
                p = (r.uniform(vx0 + 120, vx1 - 120), r.uniform(vy0 + 80, vy1 - 160)); dl = i * .07
                k = ease_out_back((ts - dl) / .25) * (1 - clamp01((ts - dl - .7) / .4))
                if k > 0.02: sparkle(sp, p, 26 * k, PAPER, f'tw{i}')
        tw = t - word('webhooks') + .25
        if tw > 0:
            r = np.random.default_rng(3)
            for i in range(5):
                dl = i * .18; u = (tw - dl) / 1.25
                if 0 < u < 1.2:
                    x = lerp(vx0 - 150, vx1 + 150, u); y = vy0 + 120 + i * 120 + 30 * math.sin(u * 9 + i)
                    webhook(sp, (x, y), 0.25 * math.sin(u * 9 + i + 1.2), 2.0 + .4 * (i % 2), PAPER, f'wh{i}')
    else:
        stars_field(sp, (vx0, vy0, vx1, vy1), t, 0.02, n=120, seed=21)
        tp = t - word('picard') + .1
        if tp > 0.15 or (0 < tp and int(tp * 40) % 2):   # flicker on
            te = t - word('enterprise') + .15
            if te > 0:
                u = te / 1.6
                if u < 1.1: ship(sp, (lerp(vx1 + 250, vx0 - 350, u), 245 - 40 * u), 0.55, PAPER, INK, 'ent', facing=-1)
            sp.text('INCOMING HAIL  :  U.S.S. ENTERPRISE', (960, vy0 + 45), 38, PAPER, 'hand')
            CAST['picard'].draw(sp, t, bob)
            sp.rect(vx0 + 330, 600, vx1 - 330, 840, 6, PAPER, 'desk', fill=INK)
            sp.line([(vx0 + 380, 640), (vx1 - 380, 640)], 3, PAPER, 'desk2')
            sp.text('ADM. PICARD  //  U.S.S. ENTERPRISE', (960, 700), 34, PAPER, 'marker')   # name card
        if 0 < tp < 0.4:
            r = np.random.default_rng(int(tp * 48))
            for i in range(14):
                y = r.uniform(vy0, vy1); sp.line([(vx0, y), (vx1, y)], r.uniform(2, 8), PAPER, f'st{i}', wob=2)
    X0, Y0 = pen.S((vx0, vy0)); X1, Y1 = pen.S((vx1, vy1))
    X0, Y0, X1, Y1 = max(int(X0), 0), max(int(Y0), 0), min(int(X1), W), min(int(Y1), H)
    img[Y0:Y1, X0:X1] = sub[Y0:Y1, X0:X1]
    # foreground crew from behind + console rail
    for n in ('cap_back', 'rik_back'):
        CAST[n].draw(pen, t, bob * 1.6, w=8, halo=10)
    # console rail is fixed in screen space (foreground), leaving a clean caption band below it
    rp = Pen(img, (W / 2, H / 2, 1.0), boil)
    rp.fill([(-20, 905), (W + 20, 905), (W + 20, H + 20), (-20, H + 20)], PAPER)
    rp.line([(-20, 905), (W + 20, 905)], 7, INK, 'rail'); rp.line([(-20, 922), (W + 20, 922)], 3, INK, 'rail2')
    for k in range(2):
        x = 60 + k * 1700; rp.rect(x, 940, x + 60, 952, 3, INK, f'rb{k}', fill=INK)
    return pen

def shot_space(img, t, cam, boil, bob):
    pen = Pen(img, cam, boil)
    r = np.random.default_rng(9)
    for i in range(140):
        x = (r.uniform(-200, 2300) - (t - CUT_F) * r.uniform(60, 220)) % 2400 - 250; y = r.uniform(-100, 1000)
        if i % 9 == 0: sparkle(pen, (x, y), 9, INK, f'ss{i}')
        else: pen.dot((x, y), r.uniform(1.4, 3.6), INK)
    for i in range(7):   # speed lines
        y = 330 + i * 45; x = 1250 + (i % 3) * 60 - ((t * 900 + i * 230) % 500)
        pen.line([(x, y), (x + 140 + 40 * (i % 2), y)], 3, INK, f'sl{i}', wob=0.5)
    c = (900 + (t - CUT_F) * 25, 470 + 6 * math.sin(t * 2.2))
    ship(pen, c, 1.45, sid='titan')
    pen.text('U.S.S. TITAN', (c[0] - 190, c[1] + 150), 40, INK, 'marker')
    ts = t - word('shields') + .02
    if ts > 0:
        k = ease_out_back(ts / .35, 2.6)
        rx, ry = 520 * k, 230 * k
        n = 30
        for i in range(n):         # dashed dome
            a0 = i * 360 / n; pen.arc(c, rx, ry, a0, a0 + 7, 5, INK, f'dome{i}', n=4)
        pen.arc(c, rx * 1.04, ry * 1.06, 200, 340, 3, INK, 'domehi')
        for j, tk in enumerate((0.0, word('up') - word('shields'))):
            u = (ts - tk) / .6
            if 0 < u < 1: pen.arc(c, 520 * (1 + .35 * u), 230 * (1 + .35 * u), 0, 360, 8 * (1 - u) + .6, INK, f'rip{j}')
    return pen

def render_frame(t):
    img = np.full((H, W, 3), PAPER, np.uint8)
    boil = int(t * BOIL_FPS)
    db = since(BEATS, t); dB = since(BARS, t)
    bob = 5 * math.exp(-db * 9)
    kick = 1 + 0.012 * math.exp(-dB * 6)
    if t < CUT_B:
        k = ease((t - T0) / (CUT_B - T0)); cam = (lerp(930, 960, k), lerp(535, 540, k), lerp(1.04, 1.0, k) * kick)
        shot_bridge(img, t, cam, boil, bob)
    elif t < CUT_C:
        k = ease((t - CUT_B) / (CUT_C - CUT_B)); cam = (960, lerp(540, 470, k), lerp(1.0, 1.08, k) * kick)
        shot_screen(img, t, cam, boil, bob)
    elif t < CUT_D:
        k = ease((t - PUSH_C) / 0.9)
        cam = (lerp(960, 560, k), lerp(540, 610, k), lerp(1.0, 1.5, k) * kick)
        shot_bridge(img, t, cam, boil, bob)
    elif t < CUT_E:
        k = ease((t - PUSH_D) / 0.6)
        cam = (lerp(1390, 1330, k), lerp(640, 690, k), lerp(1.65, 2.0, k) * kick)
        shot_bridge(img, t, cam, boil, bob)
    elif t < CUT_F:
        k = ease((t - PUSH_E) / 0.8)
        cam = (lerp(960, 900, k), lerp(500, 470, k), lerp(1.0, 1.1, k) * kick)
        shot_screen(img, t, cam, boil, bob, picard=True)
    else:
        k = ease((t - CUT_F) / (T1 - CUT_F)); cam = (lerp(960, 950, k), 520, lerp(1.0, 1.12, k) * kick)
        shot_space(img, t, cam, boil, bob)
    return img

# ------------------------------------------------------------------ paper finish
VIG, GRAINS = paper_finish()

def finish(img, t):
    f = img.astype(np.float32) * VIG + GRAINS[int(t * BOIL_FPS) % 4]
    fade = min(clamp01((t - T0) / 0.3), clamp01((T1 - t) / 0.3))
    if fade < 1: f = f * fade + np.array(PAPER, np.float32) * (1 - fade)
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    if '--frames' in sys.argv:
        for a in sys.argv[sys.argv.index('--frames') + 1:]:
            t = float(a); cv2.imwrite(f'{HERE}/raw_{a}.png', finish(render_frame(t), t))
        sys.exit()
    out = f'{HERE}/titan-stick-verse1-poc.mp4'
    N = int(round((T1 - T0) * FPS)); dur = T1 - T0
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-ss', str(T0), '-t', str(dur), '-i', f'{PROJ}/titan-bridge-theme-epic.mp3',
           '-vf', f"ass={HERE}/captions.ass", '-af', f'afade=t=in:d=0.3,afade=t=out:st={dur - 0.3}:d=0.3',
           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-tune', 'animation',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-t', str(dur), '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); st = time.time()
    for i in range(N):
        t = T0 + i / FPS
        p.stdin.write(finish(render_frame(t), t).tobytes())
        if i % 48 == 0: print(f'{i}/{N} {time.time() - st:.1f}s', flush=True)
    p.stdin.close(); p.wait(); print('done', out, f'{time.time() - st:.1f}s')
