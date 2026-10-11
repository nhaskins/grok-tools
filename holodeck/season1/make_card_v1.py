"""1.5 s "STARSHIP GROKBOT - SEASON ONE" ink title card (1080p24) for the season compilation."""
import sys, math, subprocess
sys.path.insert(0, '/workspace/holodeck/titan-hello-world/stick-poc'); sys.path.insert(0, '/workspace/holodeck/brand')
import numpy as np, cv2
from stickfig import *
from inkset import W, H, paper_finish, sparkle
import sets as SETS
FPS, NF = 24, 36
VIG, GRAINS = paper_finish()
EPS = ['The Daily Log', 'The Webhook', 'Holodeck Program 01', 'The Red Shirts', 'Merge Conflict', 'Ship It Friday',
       'Prompt Injection', 'Hallucination', 'Technical Debt', 'CAPTCHA', 'Context Window', 'Rate Limited']
def frame(i, t=None):
    t = i / FPS if t is None else t
    img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, (960, 540, 1.0), int(t * 12) + 2)
    pen.rect(40, 40, W - 40, H - 40, 6, INK, 'b1'); pen.rect(60, 60, W - 60, H - 60, 3, INK, 'b2')
    SETS.outlined(pen, 'STARSHIP GROKBOT', (960, 220), 120, 8)
    pen.line([(470, 300), (1450, 294)], 6, INK, 'ul')
    if t >= .15: SETS.stamp(pen, 'SEASON ONE', (960, 410), t, .15, 96, w=7, sid='s1')
    for j, e in enumerate(EPS):                       # episode list pops in, two columns
        k = clamp01((t - .35 - j * .05) / .15)
        if k <= 0: continue
        c, r = j // 6, j % 6
        x = 560 + c * 800; y = 560 + r * 66
        pen.text(f'{j + 1:>2}. {e}', (x - 230, y), int(44 * (.6 + .4 * k)), INK, 'hand', anchor='l')
    for j, (x, y) in enumerate([(250, 200), (1680, 230), (300, 900), (1640, 880), (960, 980)]):
        sparkle(pen, (x, y), 22 + 6 * math.sin(t * 9 + j), INK, f'sp{j}')
    f = img.astype(np.float32) * VIG + GRAINS[int(t * 12) % 4]
    return np.clip(f, 0, 255).astype(np.uint8)
if __name__ == '__main__':
    if '--still' in sys.argv: cv2.imwrite('card_still.png', frame(0, 1.4)); sys.exit()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', '24', '-i', '-',
                          '-f', 'lavfi', '-t', str(NF / FPS), '-i', 'anullsrc=r=48000:cl=stereo',
                          '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', 'season-card.mp4'], stdin=subprocess.PIPE)
    for i in range(NF): p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait(); print('card ok')
