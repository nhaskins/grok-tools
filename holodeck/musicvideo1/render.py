"""Final music video renderer. python render.py PART NPARTS -> final/partN.mp4 (video only)."""
import sys, os, json, math, subprocess
sys.path.insert(0, '/workspace/grok-tools/holodeck/voices/demo20'); import npfix
SP = '/workspace/holodeck/titan-hello-world/stick-poc'; sys.path.insert(0, SP); sys.path.insert(0, '/workspace/holodeck/brand')
import numpy as np, cv2
from stickfig import *
from inkset import W, H, FLOOR, stars_field, sparkle, chair, paper_finish
import sets as SETS
import make_sting as MS
os.chdir(os.path.dirname(os.path.abspath(__file__)))
A = json.load(open('analysis.json')); B = A['bars']; D = A['duration']; BEATS = np.array(A['beats']); FPS = 24
VIG, GR = paper_finish(); SC = 1.5; ST = FLOOR - 110*SC
def bph(t):  # 1 right on a beat, decays
    p = BEATS[BEATS <= t]; return math.exp(-(t - p[-1]) * 7) if len(p) else 0
def card(pen, name, sub, u, x=960, y=930):
    k = ease_out_back(clamp01((u - .15) / .35))
    if k <= .02: return
    yy = y + (1-k)*260
    pen.rect(x-330, yy-62, x+330, yy+70, 5, INK, 'nc', fill=PAPER); SETS.outlined(pen, name, (x, yy-12), 64, 5); pen.text(sub, (x, yy+42), 32, INK, 'hand')
def ship(pen, c, s, t=1.0, bob=0):
    MS.CX, MS.CY, MS.SS = c[0], c[1] + bob, s; MS.draw_ship(pen, min(t, .99))
def F(who, x, y, f, props, keys, scale=SC, **kw):
    g = Figure(who, x, y, f, set(props), scale=scale, **kw)
    for k in keys: g.key(*k)
    return g
RK = ['beard', 'badge']; BC = ['curly', 'badge']; PC = ['shine', 'badge', 'collar']; GB = ['robot']; RS = ['redshirt', 'ponytail']
def bridge_bg(p):
    SETS.floor(p); p.rect(260, 90, 1660, 560, 6, INK, 'vs', fill=PAPER); stars_field(p, (270, 100, 1650, 550), 0, 0, n=50, seed=8, col=INK)

# ---------------------------------------------------------------- shots: fn(p, u, t, d) u=local time, d=dur
def s_stars(p, u, t, d):
    p.cam = (960 - 30*u, 540, 1 + .02*u/d); stars_field(p, (-200, -200, 2200, 1300), 0, 0, n=240, seed=7, col=INK)
    for k, (x, y) in enumerate([(400, 300), (1300, 220), (1600, 700), (700, 800)]):
        tw = math.exp(-abs(t - (1.37 + k*.8))*4); 
        if tw > .05: sparkle(p, (x, y), 10 + 40*tw, INK, f'tw{k}')
def s_planet(p, u, t, d):
    x = 1500 - 1100*ease(u/d); stars_field(p, (0, 0, W, H), 0, 0, n=160, seed=3, col=INK)
    c = (x, 620); p.circle(c, 330, 6, INK, 'pl', fill=PAPER)
    for k in range(5): p.arc(c, 330, 330, 200+k*8+u*3, 250+k*8+u*3, 3, INK, f'sh{k}')
    p.arc(c, 560, 110, -20, 200, 6, INK, 'ring', rot=-12)
    g = math.exp(-abs(t-5.39)*5)
    if g > .05: sparkle(p, (x+520, 560), 60*g, INK, 'rg')
def s_glide(p, u, t, d):
    k = ease(u/d); stars_field(p, (0, 0, W, H), 0, 0, n=160, seed=5, col=INK)
    ship(p, (lerp(200, 980, k), lerp(820, 470, k)), lerp(.3, .8, k), bob=6*math.sin(u*2))
def s_pass(p, u, t, d):
    k = u/d; p.cam = (960, 540, 1 + .08*k); stars_field(p, (0, 0, W, H), 0, 0, n=120, seed=9, col=INK)
    x = lerp(1900, 500, k); ship(p, (x, 600), 2.1)
    g = math.exp(-abs(t - B[10])*3.5)
    if g > .04:
        gx = x + 190
        for a in range(8):
            ang = a*math.pi/4 + u*.5; L = 40 + 260*g
            p.line([(gx+30*math.cos(ang), 430+30*math.sin(ang)), (gx+L*math.cos(ang), 430+L*math.sin(ang))], 3+4*g, INK, f'gl{a}')
        p.circle((gx, 430), 10+26*g, 0, INK, 'g', fill=INK)
def s_riker(p, u, t, d):
    p.cam = (960, 600, 1 + .05*u/d); SETS.floor(p); chair(p, 900)
    sw = B[12] + .9 - t + u  # local of swing ~0.9
    g = F('riker', lerp(1500, 900, ease(u/.6)), ST, -1 if u < .6 else 1, RK,
          [(0, 'stand', 0), (.6, 'legover', .3), (1.2, 'straddle', .35), (2.2, 'chinrub', .3), (3.2, 'grin', .25)])
    g.draw(p, u, bob=-4*bph(t), w=6)
    if .7 < u < 1.5: p.arc((960, 700), 120, 60, 200, 330, 4, INK, 'swing'); SETS.outlined(p, 'SWING!', (1250, 480), 70*ease_out_back(clamp01((u-.7)/.2)), 5)
    if u > 3.2: sparkle(p, (860, 300), 30, INK, 'tooth')
    card(p, 'RIKER', 'Number One (backwards)', u)
def holo(p, u):
    for i in range(-10, 11): p.line([(960, 520), (960+i*260, 1080)], 3, INK, f'gr{i}')
    for j, y in enumerate([600, 680, 790, 960]): p.line([(0, y), (W, y)], 3, INK, f'gh{j}')
    p.line([(760, 520), (760, 160), (1160, 160), (1160, 520)], 8, INK, 'arch')
def s_barclay(p, u, t, d):
    p.cam = (960, 540, 1 + .08*u/d); holo(p, u)
    for k, (x, y) in enumerate([(320, 260), (1540, 300), (1500, 560)]):
        kk = ease_out_back(clamp01((u - .3 - k*.51)/.25))
        if kk > .05: p.rect(x-130*kk, y-80*kk, x+130*kk, y+80*kk, 4, INK, f'w{k}', fill=PAPER); p.text(['RISA.prog', 'TITAN v2', 'MUSIC VID'][k], (x, y), 34*kk, INK, 'marker')
    g = F('barclay', 960, ST, 1, BC, [(0, 'nervous', 0), (1.6, 'surprise', .2), (2.2, 'cheer', .2), (3.0, 'faint', .45)])
    g.move(3.0, 860, ST + 40, .45); g.draw(p, u, w=6)
    for k in range(4):
        hk = u - 1.8 - k*.25
        if hk > 0: SETS.heart(p, (1060+k*60 + 20*math.sin(hk*5), 420 - hk*120 - k*30), .2+.05*bph(t), INK, f'h{k}')
    if u > 3.2: SETS.outlined(p, 'THUD', (700, 820), 70, 5)
    card(p, 'LT. BARCLAY', 'Holodeck (faints from joy)', u)
def s_picard(p, u, t, d):
    p.cam = (960, 480, 1 + .12*ease(u/d)); p.rect(200, 80, 1720, 820, 0, fill=INK); stars_field(p, (200, 80, 1720, 820), u, .03, n=70, seed=4)
    g = F('picard', 860, 640, 1, PC, [(0, 'mic', 0), (1.4, 'stand', .3), (2.0, 'point', .15)], col=PAPER, scale=2.0)
    g.draw(p, u, w=6)
    cup = (650, 560 + 50*ease(clamp01((u-1.2)/.4))) if u > 1.2 else (980, 380)
    p.rect(560, 640, 1260, 780, 5, PAPER, 'desk', fill=INK); p.rect(cup[0]-30, cup[1]-25, cup[0]+30, cup[1]+25, 4, PAPER, 'cup', fill=INK)
    for k in range(3): p.line([(cup[0]-15+k*15, cup[1]-35-((u*60+k*20) % 40)), (cup[0]-10+k*15, cup[1]-70-((u*60+k*20) % 40))], 3, PAPER, f'st{k}')
    p.text('TEA. EARL GREY. HOT.', (1450, 200), 30, PAPER, 'hand')
    if u > 2.0: SETS.outlined(p, 'ENGAGE.', (1400, 420), 110*ease_out_back(clamp01((u-2)/.25)), 6)
    card(p, 'PICARD', 'Enterprise-D (with tea)', u)
def s_grokbot(p, u, t, d):
    p.cam = (960, 540, 1); SETS.floor(p)
    g = F('grokbot', 760, ST, 1, GB, [(0, 'present', 0), (1, 'console', .2), (2, 'console', .2), (2.9, 'tada', .2)], scale=SC*1.1)
    g.draw(p, u, bob=-10*bph(t), w=6)
    nb = min(5, int(u/.51)+1)
    for k in range(nb): 
        dk = clamp01((u - k*.51)/.2); p.rect(1150+k*40, 700-k*70 - 300*(1-dk), 1400+k*40, 800-k*70-300*(1-dk), 4, INK, f'bx{k}', fill=PAPER)
    lv = int(1 + 5*bph(t))
    for k in range(lv): p.rect(690+k*24, 300-k*14, 708+k*24, 320, 0, fill=INK)
    if u > 2.95: SETS.stamp(p, 'DONE', (1400, 380), u, 2.95, 110, 6, 'done'); SETS.burst(p, (1400, 380), u, 2.95, 260, sid='db')
    card(p, 'GROK BOT', 'Ships it. Stamps it.', u)
def beam(p, x, k, sid):
    for j in range(10): sparkle(p, (x - 90 + (j*41) % 180, ST - 300 + (j*67 + int(k*300)) % 330), 10 + 10*math.sin(k*20+j), INK, f'{sid}{j}')
def s_redshirt(p, u, t, d):
    SETS.floor(p); lb = B[21] - B[20]
    if u < lb:
        g = F('redshirt', 960, ST, 1, RS, [(0, 'wave', 0), (.6, 'cheer', .2)]); g.draw(p, u, bob=-8*bph(t), w=6)
        p.text('#47', (960, 280), 70, INK, 'marker')
        if u > lb - .6: beam(p, 960, u, 'bo'); SETS.outlined(p, 'DELETE & RECREATE', (960, 180), 64, 5)
    else:
        v = u - lb
        if v < .5: beam(p, 960, u, 'bi')
        if v > .2:
            g = F('redshirt', 960, ST, 1, RS, [(0, 'shrug', 0), (.8, 'thumbs', .2), (1.4, 'cheer', .2)]); g.draw(p, v, w=6)
            p.text('#48', (960, 280), 70, INK, 'marker')
        SETS.outlined(p, 'DELETE & RECREATE', (960, 180), 64, 5)
    card(p, 'ENS. RED SHIRT', '#47 \u2192 #48 (expendable, eager)', u)
def s_helm(p, u, t, d):  # replaces the Captain: Grok Bot takes the helm, Riker yells punch it
    p.cam = (960, 560, 1 + .1*ease(u/d)); bridge_bg(p)
    p.rect(620, 700, 900, 760, 5, INK, 'con', fill=PAPER)
    gb = F('grokbot', 760, ST, -1, GB, [(0, 'steer', 0)], scale=SC); gb.draw(p, u, bob=-6*bph(t), w=6)
    rk = F('riker', 1300, ST, -1, RK, [(0, 'think', 0), (1.6, 'pointup', .2), (2.6, 'cheer', .2)]); rk.draw(p, u, w=6)
    kk = clamp01((u-1.6)/1.2)
    for j in range(8): p.rect(640+j*32, 715, 660+j*32, 745, 0, fill=INK if (j + int(u*8)) % 3 == 0 else PAPER)
    if u > 1.6: SETS.outlined(p, 'PUNCH IT!', (1350, 420), 100*ease_out_back(clamp01((u-1.6)/.25)), 6)
    lv = clamp01((u - 2.6)/(d-2.6)); p.line([(870, 700), (870 + 120*math.cos(-1.3 - 1.4*lv), 700 + 120*math.sin(-1.3-1.4*lv))], 8, INK, 'lever')
    card(p, 'GROK BOT & RIKER', 'Hands on the throttle', u)
def s_warp(p, u, t, d):
    k = u/d; p.cam = (960, 540, 1 + .4*ease_out(k))
    if u < .12: p.img[:] = INK
    stars_field(p, (-400, -300, 2320, 1380), u*4, .5, n=200, seed=11, col=INK, streak=.9)
    ship(p, (960, 560), 1.2 + .3*k)
    SETS.outlined(p, 'WARP 9', (960, 820), 120*ease_out_back(clamp01((u-.1)/.3)), 7)
LINE = [('picard', PC, 'hips', 'PICARD'), ('riker', RK, 'grin', 'RIKER'), ('grokbot', GB, 'tada', 'GROK BOT'), ('barclay', BC, 'thumbs', 'BARCLAY'), ('redshirt', RS, 'cheer', 'RED SHIRT')]
def s_lineup(p, u, t, d):
    SETS.floor(p); seg = d/5; i = min(4, int(u/seg)); v = u - i*seg
    p.cam = (300 + i*330, 600, 1.7 - .25*ease(clamp01(v/.2)))
    for k, (who, pr, ps, nm) in enumerate(LINE):
        F(who, 300+k*330, ST, 1, pr, [(0, 'stand', 0), (i*seg if k == i else -1, ps, .15)] if k >= i else [(0, ps, 0)], scale=SC).draw(p, u, bob=-6*bph(t), w=6)
    SETS.burst(p, (300 + i*330, ST - 250), v, .05, 220, sid=f'lb{i}')
    SETS.outlined(p, LINE[i][3], (300 + i*330, 260), 70, 5)
def s_ferengi(p, u, t, d):
    zk = ease_out_back(clamp01((t-57.82+.3)/.3)); p.cam = (960, 450, .8 + .2*zk)
    p.rect(200, 80, 1720, 820, 0, fill=INK)
    F('ferengi', 900, 700, 1, ['ferengi'], [(0, 'grin', 0), (1, 'tada', .2), (2, 'grin', .2)], col=PAPER, scale=2.2).draw(p, u, w=6)
    for k in range(min(4, int(u/.5)+1)): p.rect(1250+k*30, 640-k*40, 1390+k*30, 680-k*40, 4, PAPER, f'gb{k}', fill=INK)
    p.text('TRADE AGREEMENT (fine print)', (1400, 200), 34, PAPER, 'hand')
    for k in range(int(u*3)): p.text('subject to rule of acquisition #' + str(k+1), (1400, 240+k*26), 20, PAPER, 'hand')
    if t > 60.16 - .1: SETS.outlined(p, 'NO DEAL', (960, 400), 120, 7)
    card(p, 'DAIMON GRUBB', 'cameo (non-canon)', u)
def s_bank(p, u, t, d):
    k = u/d; stars_field(p, (0, 0, W, H), u, .08, n=140, seed=13, col=INK, streak=.4)
    p.circle((350 - 200*k, 820), 400, 6, INK, 'pl3', fill=PAPER)
    bank = math.sin(clamp01((t-63.34+.3)/1.5)*math.pi)
    c = (lerp(1700, 300, ease(k)), 520 - 160*bank)
    ship(p, c, 1.1 + .3*bank)
    for j in range(6): p.line([(c[0]+300, c[1]-60+j*30), (c[0]+300+300*(.5+bank), c[1]-60+j*30)], 4, INK, f'bl{j}')
def s_trombone(p, u, t, d):
    p.cam = (960, 600, 1.05 + .05*math.sin(u*3)); SETS.floor(p)
    F('riker', 900, ST, 1, RK, [(0, 'trombone', 0)]).draw(p, u, bob=-12*bph(t), w=6)
    sl = 60*bph(t); p.line([(1060, 470), (1200 + sl, 470)], 7, INK, 'slide'); p.line([(1200+sl, 470), (1200+sl, 510), (1060, 510)], 7, INK, 'slide2')
    p.circle((1050, 490), 40, 6, INK, 'bell')
    for j, bt in enumerate(BEATS[(BEATS > t - u) & (BEATS <= t)][-6:]):
        a = t - bt; SETS.note(p, (1260 + a*260, 420 - a*200 - 40*math.sin(a*6)), 50, 1, f'n{j}', double=j % 2)
    card(p, 'RIKER', 'Trombone solo (smooth)', u)
def s_disco(p, u, t, d):
    holo(p, u); p.cam = (960, 540, 1)
    for k in range(5):
        a = u*2 + k*1.2; p.line([(960, 60), (960 + 900*math.sin(a), 1000)], 3, INK, f'sp{k}')
    p.circle((960, 60), 50, 5, INK, 'ball', fill=PAPER)
    for k in range(6): p.line([(915+k*18, 20), (915+k*18, 100)], 2, INK, f'bl{k}')
    seq = ['tada', 'pointup', 'cheer', 'tada', 'thumbs', 'surprise', 'cheer', 'tada']
    ks = [(0, 'stand', 0)] + [(float(b - (t-u)), seq[j % len(seq)], .12) for j, b in enumerate(BEATS[(BEATS > t-u) & (BEATS < t-u+d)])]
    F('barclay', 760, ST, 1, BC, ks).draw(p, u, bob=-18*bph(t), w=6)
    F('barclay', 1200, ST, -1, BC, ks, scale=SC*.9).draw(p, u, bob=-18*bph(t), w=5)
    p.text('HOLO-BARCLAY', (1200, 400), 34, INK, 'marker')
    card(p, 'LT. BARCLAY', 'Dance-off vs. himself', u)
def s_dodge(p, u, t, d):
    SETS.floor(p); hit = 76.09 - (t - u)
    rk = clamp01((u - (hit - .8))/.8); ry = lerp(-200, ST - 200, rk*rk)
    x = 960 if u < hit - .25 else lerp(960, 1300, ease(clamp01((u - hit + .25)/.25)))
    F('redshirt', x, ST, 1, RS, [(0, 'proud', 0), (hit-.9, 'surprise', .15), (hit-.25, 'kneeup', .15), (hit+.3, 'cheer', .2)]).draw(p, u, w=6)
    if u < hit: p.circle((960, ry), 110, 6, INK, 'rock', fill=PAPER); p.text('BOULDER', (960, ry), 34, INK, 'marker')
    else:
        p.circle((960, ST - 80), 110, 6, INK, 'rock', fill=PAPER); SETS.burst(p, (960, ST - 40), u, hit, 300, sid='rk')
        SETS.outlined(p, 'STILL #48!', (1300, 300), 80, 5)
    card(p, 'ENS. RED SHIRT', 'Survives an episode (first time)', u)
def s_approve(p, u, t, d):
    bridge_bg(p)
    F('picard', 700, ST, 1, PC, [(0, 'mic', 0), (1.2, 'point', .2), (2.5, 'proud', .2)]).draw(p, u, w=6)
    F('grokbot', 1250, ST, -1, GB, [(0, 'present', 0), (1.6, 'tada', .2)]).draw(p, u, bob=-8*bph(t), w=6)
    if u > 1.2: SETS.outlined(p, 'MAKE IT SO.', (700, 330), 90*ease_out_back(clamp01((u-1.2)/.25)), 6)
    if u > 2.0: SETS.stamp(p, 'APPROVED', (1300, 330), u, 2.0, 80, 6, 'ap'); SETS.burst(p, (1300, 330), u, 2.0, 280, sid='ab')
    card(p, 'PICARD & GROK BOT', 'Make it so. (Shipped.)', u)
def s_salute(p, u, t, d):
    bridge_bg(p); hit = 83.78 - (t-u); k = clamp01(u/hit)
    ship(p, (lerp(1400, 960, k), lerp(200, 330, k)), lerp(.3, 1.4, k*k))
    for j, (who, pr) in enumerate([('picard', PC), ('riker', RK), ('grokbot', GB), ('barclay', BC), ('redshirt', RS)]):
        F(who, 300+j*330, ST, 1, pr, [(0, 'stand', 0), (76.09 - (t-u) if 76.09 > t-u else .3 + j*.1, 'salute', .2)]).draw(p, u, w=6)
    if u > hit:
        p.img[:] = (p.img*.3 + np.array(PAPER)*.7).astype(np.uint8) if u - hit < .15 else p.img
        ship(p, (960, 500), 3.0 + 4*(u-hit))
def s_logo(p, u, t, d):
    ts = u + 1.4
    if ts < MS.T_ZIPEND + .3: MS.CX, MS.CY, MS.SS = 900, 500, 1.6; MS.speed_lines(p, ts); MS.draw_ship(p, ts)
    MS.CX, MS.CY, MS.SS = 900, 500, 1.6; MS.title(p, ts)
    if ts > MS.T_STAMP + .3:
        k = clamp01((ts - MS.T_STAMP - .3)/.4); p.text('by Grok Bot & Nate Haskins', (960, 760), 46, INK, 'hand', alpha=k)
    for j in range(5):
        tw = 0.5 + .5*math.sin(u*2 + j); sparkle(p, (300 + j*330, 200 + (j % 2)*700), 8 + 10*tw, INK, f'ls{j}')
SHOTS = [  # (start, fn, label)
 (0, s_stars, 'Starfield drift'), (B[2], s_planet, 'Ringed planet flyby'), (B[6], s_glide, 'Starship Grokbot glides into view'),
 (B[8], s_pass, 'Ship passes camera, saucer glint'), (B[12], s_riker, 'Riker swings onto chair backwards'), (B[14], s_barclay, 'Barclay holodeck, faints from joy'),
 (B[16], s_picard, 'Picard sips tea, ENGAGE.'), (B[18], s_grokbot, 'Grok Bot stacks boxes, stamps DONE'), (B[20], s_redshirt, 'Red Shirt #47 -> #48'),
 (B[22], s_helm, 'Grok Bot at the helm, Riker: PUNCH IT! (replaces Captain)'), (B[24], s_warp, 'WARP 9 jump (climax)'), (B[25], s_lineup, 'Power-pose lineup, punch-in per character'),
 (B[28], s_ferengi, 'Daimon Grubb cameo, NO DEAL'), (B[30], s_bank, 'Ship banks past planet'), (B[32], s_trombone, 'Riker trombone solo'),
 (B[34], s_disco, 'Barclay holodeck dance-off vs. himself'), (B[36], s_dodge, 'Red Shirt #48 dodges boulder'), (B[38], s_approve, 'Picard MAKE IT SO / Grok Bot APPROVED'),
 (B[40], s_salute, 'Crew salute, ship arcs into camera'), (B[42], s_logo, 'STARSHIP GROKBOT logo + credit, held to end')]
def frame(i):
    t = i / FPS; j = max(k for k, s in enumerate(SHOTS) if s[0] <= t + 1e-9)
    st = SHOTS[j][0]; en = SHOTS[j+1][0] if j+1 < len(SHOTS) else D
    img = np.full((H, W, 3), PAPER, np.uint8); p = Pen(img, (960, 540, 1.0), int(t*12))
    SHOTS[j][1](p, t - st, t, en - st)
    return np.clip(img.astype(np.float32)*VIG + GR[int(t*12) % 4], 0, 255).astype(np.uint8)
if __name__ == '__main__':
    if sys.argv[1] == 'list':
        f = lambda t: f'{int(t//60)}:{t%60:05.2f}'
        for k, s in enumerate(SHOTS): print(k+1, f(s[0]), f(SHOTS[k+1][0] if k+1 < len(SHOTS) else D), s[2])
        sys.exit()
    if sys.argv[1] == 'test':
        for tt in map(float, sys.argv[2:]): cv2.imwrite(f'final/test_{tt:06.2f}.png', frame(int(tt*FPS)))
        sys.exit()
    part, n = int(sys.argv[1]), int(sys.argv[2]); N = int(round(D*FPS)); a, b = N*part//n, N*(part+1)//n
    ff = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '4', f'final/part{part}.mp4'], stdin=subprocess.PIPE)
    for i in range(a, b):
        ff.stdin.write(frame(i).tobytes())
        if i % 120 == 0: print(part, i, b, flush=True)
    ff.stdin.close(); ff.wait()
