"""Rough key-frame stills for the music-video storyboard (one per shot) -> frames/shotNN.png"""
import sys, os, json, math
sys.path.insert(0, '/workspace/grok-tools/holodeck/voices/demo20'); import npfix
SP = '/workspace/holodeck/titan-hello-world/stick-poc'; sys.path.insert(0, SP)
sys.path.insert(0, '/workspace/holodeck/brand')
import numpy as np, cv2
from stickfig import *
from inkset import W, H, FLOOR, stars_field, ship, sparkle, chair, paper_finish
import sets as SETS
import make_sting as MS
VIG, GR = paper_finish(); os.makedirs('frames', exist_ok=True)
def F(who, x, y, f, props, pose, **kw):
    g = Figure(who, x, y, f, set(props), **kw); g.key(-1e8, pose, 0); return g
def new(bg=PAPER): img = np.full((H, W, 3), bg, np.uint8); return img, Pen(img, (960, 540, 1.0), 2)
def card(pen, name, sub, x=960, y=930):
    pen.rect(x-330, y-62, x+330, y+70, 5, INK, 'nc', fill=PAPER)
    SETS.outlined(pen, name, (x, y-12), 64, 5); pen.text(sub, (x, y+42), 32, INK, 'hand')
def space(pen, n=160, streak=0.0, seed=7):
    stars_field(pen, (0, 0, W, H), 0, 0, n=n, seed=seed, streak=streak, col=INK)
def grokship(pen, c, s, t=0.9):
    pen.cam = (960 - (c[0] - MS.CX) / s, 540 - (c[1] - MS.CY) / s, s) if False else pen.cam
    MS.CX, MS.CY, MS.SS = c[0], c[1], s; MS.draw_ship(pen, t)
def save(i, img): cv2.imwrite(f'frames/shot{i:02d}.png', np.clip(img.astype(np.float32)*VIG+GR[0], 0, 255).astype(np.uint8))
SC = 1.5; ST = FLOOR - 110*SC
# 1 starfield drift
img, p = new(); space(p, 220); p.text('slow drift  \u2192', (960, 980), 40, INK, 'marker'); save(1, img)
# 2 planet + ring flyby
img, p = new(); space(p, 160, seed=3)
p.circle((700, 640), 330, 6, INK, 'pl', fill=PAPER)
for k in range(5): p.arc((700, 640), 330, 330, 200+k*8, 250+k*8, 3, INK, f'sh{k}')
p.arc((700, 640), 560, 110, -20, 200, 6, INK, 'ring', rot=-12)
save(2, img)
# 3 ship glides in (small, from lower-left)
img, p = new(); space(p, 160, seed=5); p.circle((1500, 300), 120, 5, PAPER, 'pl2', fill=PAPER)
sh = Pen(img, (960, 540, 1.0), 2); grokship(sh, (520, 720), .55)
p.text('\u2197 glides into view', (950, 900), 38, INK, 'marker'); save(3, img)
# 4 ship passes camera, saucer glint
img, p = new(); space(p, 120, seed=9); grokship(p, (1100, 600), 2.1)
for a in range(8): ang = a*math.pi/4; p.line([(1290+30*math.cos(ang), 430+30*math.sin(ang)), (1290+110*math.cos(ang), 430+110*math.sin(ang))], 6, INK, f'gl{a}')
p.circle((1290, 430), 26, 0, INK, 'g', fill=INK); save(4, img)
# 5 Riker backwards chair
img, p = new(); SETS.floor(p); chair(p, 900)
F('riker', 900, ST, 1, ['beard', 'badge'], 'legover', scale=SC).draw(p, 0, 0, w=6)
p.arc((960, 700), 120, 60, 200, 330, 4, INK, 'swing'); p.text('SWING!', (1180, 520), 60, INK, 'marker')
card(p, 'RIKER', 'Number One (backwards)'); save(5, img)
# 6 Barclay holodeck faint
img, p = new()
for i in range(-10, 11): p.line([(960, 520), (960+i*260, 1080)], 3, INK, f'gr{i}')
for j, y in enumerate([600, 680, 790, 960]): p.line([(0, y), (W, y)], 3, INK, f'gh{j}')
p.line([(760, 520), (760, 160), (1160, 160), (1160, 520)], 8, INK, 'arch')
for k, (x, y) in enumerate([(320, 260), (1540, 300), (1500, 560)]): p.rect(x-130, y-80, x+130, y+80, 4, INK, f'w{k}', fill=PAPER); p.text(['RISA.prog', 'TITAN v2', 'MUSIC VID'][k], (x, y), 34, INK, 'marker')
F('barclay', 960, ST, 1, ['curly', 'badge'], 'faint', scale=SC).draw(p, 0, 0, w=6)
for k in range(3): SETS.heart(p, (1080+k*70, 380-k*50), 0.25, INK, f'h{k}')
card(p, 'LT. BARCLAY', 'Holodeck (faints from joy)'); save(6, img)
# 7 Picard viewscreen tea ENGAGE point
img, p = new(); p.rect(200, 80, 1720, 820, 0, fill=INK); stars_field(p, (200, 80, 1720, 820), 0, 0, n=60, seed=4)
F('picard', 860, 640, 1, ['shine', 'badge', 'collar'], 'point', col=PAPER, scale=2.0).draw(p, 0, 0, w=6)
p.rect(560, 640, 1260, 780, 5, PAPER, 'desk', fill=INK); p.text('ADM. PICARD // U.S.S. ENTERPRISE', (910, 680), 30, PAPER, 'marker')
p.rect(620, 590, 680, 640, 4, PAPER, 'cup'); p.text('TEA. EARL GREY. HOT.', (1450, 200), 30, PAPER, 'hand')
card(p, 'PICARD', 'Enterprise-D (with tea)'); save(7, img)
# 8 Grok Bot DONE stamp
img, p = new(); SETS.floor(p)
F('grokbot', 760, ST, 1, ['robot'], 'cheer', scale=SC*1.1).draw(p, 0, 0, w=6)
for k in range(4): p.rect(1150+k*40, 700-k*70, 1400+k*40, 800-k*70, 4, INK, f'bx{k}', fill=PAPER)
SETS.stamp(p, 'DONE', (1350, 420), 1, 0, 110, 6, 'done')
for k in range(6): p.rect(690+k*24, 300-k*14, 708+k*24, 320, 0, fill=INK)
p.text('LED mouth meter', (450, 230), 30, INK, 'hand'); card(p, 'GROK BOT', 'Ships it. Stamps it.'); save(8, img)
# 9 Red shirt 47 -> 48
img, p = new(); SETS.floor(p)
F('redshirt', 640, ST, 1, ['redshirt', 'ponytail'], 'cheer', scale=SC).draw(p, 0, 0, w=6)
for k in range(8): sparkle(p, (560+k*25, 300+(k*67) % 400), 16, INK, f'sp{k}')
p.text('\u2192', (960, 620), 160, INK, 'marker')
F('redshirt', 1280, ST, -1, ['redshirt', 'ponytail'], 'shrug', scale=SC).draw(p, 0, 0, w=6)
SETS.outlined(p, 'DELETE & RECREATE', (960, 220), 64, 5); p.text('#47', (640, 860), 50, INK, 'marker'); p.text('#48', (1280, 860), 50, INK, 'marker')
card(p, 'ENS. RED SHIRT', '#47 \u2192 #48 (expendable, eager)'); save(9, img)
# 10 Captain chair Engage
img, p = new(); SETS.floor(p); p.rect(820, 640, 1100, 840, 6, INK, 'cchair', fill=PAPER)
F('captain', 960, ST+30, 1, ['cap', 'badge'], 'point', scale=SC).draw(p, 0, 0, w=6)
SETS.outlined(p, 'ENGAGE!', (1400, 380), 110, 7); card(p, 'THE CAPTAIN', 'Engage!'); save(10, img)
# 11 warp streak
img, p = new(); space(p, 60, seed=11)
r_ = np.random.default_rng(3)
for k in range(40):
    y = r_.uniform(60, 1000); x = r_.uniform(0, 1500); p.line([(x, y), (x + r_.uniform(200, 600), y)], 3 + (k % 3), INK, f'ws{k}')
grokship(p, (960, 560), 1.2, t=1.3)
p.text('WARP JUMP  (CLIMAX DOWNBEAT)', (960, 980), 46, INK, 'marker'); save(11, img)
# 12 crew lineup
img, p = new(); SETS.floor(p)
for k, (who, pr, ps) in enumerate([('picard', ['shine', 'badge', 'collar'], 'hips'), ('riker', ['beard', 'badge'], 'grin'), ('grokbot', ['robot'], 'tada'),
                                     ('barclay', ['curly', 'badge'], 'thumbs'), ('redshirt', ['redshirt', 'ponytail'], 'cheer')]):
    F(who, 300+k*330, ST, 1, pr, ps, scale=SC).draw(p, 0, 0, w=6)
p.text('POWER-POSE LINEUP (cut on every bar)', (960, 160), 50, INK, 'marker'); save(12, img)
# 13 Ferengi cameo
img, p = new(); p.rect(200, 80, 1720, 820, 0, fill=INK)
F('ferengi', 900, 700, 1, ['ferengi'], 'grin', col=PAPER, scale=2.2).draw(p, 0, 0, w=6)
for k in range(3): p.rect(1250+k*30, 640-k*40, 1390+k*30, 680-k*40, 4, PAPER, f'gb{k}', fill=INK)
p.text('TRADE AGREEMENT (fine print)', (1400, 200), 34, PAPER, 'hand'); card(p, 'DAIMON GRUBB', 'cameo (non-canon)'); save(13, img)
# 14 chase flyby
img, p = new(); space(p, 140, streak=.4, seed=13); grokship(p, (1150, 520), 1.4)
p.circle((350, 820), 400, 6, INK, 'pl3', fill=PAPER); p.text('banking flyby, camera tracks', (960, 980), 40, INK, 'marker'); save(14, img)
# 15 crew salute + ship toward camera
img, p = new(); SETS.floor(p); grokship(p, (960, 330), .8)
for k, (who, pr) in enumerate([('riker', ['beard', 'badge']), ('grokbot', ['robot']), ('barclay', ['curly', 'badge']), ('redshirt', ['redshirt', 'ponytail'])]):
    F(who, 420+k*360, ST, 1, pr, 'salute', scale=SC).draw(p, 0, 0, w=6)
save(15, img)
# 16 title sting + credit
img, p = new(); MS.CX, MS.CY, MS.SS = 900, 500, 1.6; MS.title(p, 2.3)
for k in range(9): p.line([(1500+k*10, 300+k*40), (1880, 300+k*40)], 4, INK, f'sl{k}')
p.text('by Grok Bot & Nate Haskins', (960, 760), 46, INK, 'hand'); save(16, img)
print('ok')
