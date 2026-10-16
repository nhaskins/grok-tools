"""Season-two thumbnail: header "STARSHIP GROKBOT - SEASON TWO" + row of the 5 episode posters (v3) (frame 0)."""
import sys, glob
sys.path.insert(0, '.'); import npfix
sys.path.insert(0, '/workspace/holodeck/titan-hello-world/stick-poc')
import numpy as np, cv2
from stickfig import *
from inkset import W, H, paper_finish
import sets as SETS
img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, (960, 540, 1.0), 2)
SETS.outlined(pen, 'STARSHIP GROKBOT', (700, 105), 104, 8)
SETS.stamp(pen, 'SEASON TWO', (1530, 108), 9, 0, 78, w=7, sid='s2')
pen.line([(140, 178), (1260, 172)], 6, INK, 'ul')
cw, ch, g = 560, 315, 24; y0 = 250
P = sorted(glob.glob('posters/*.png'))
for k, p in enumerate(P):
    r, c = divmod(k, 3); n_r = min(3, len(P) - r * 3); xr = (W - (n_r * cw + (n_r - 1) * g)) // 2
    x = xr + c * (cw + g); y = y0 + r * (ch + g + 10)
    img[y:y + ch, x:x + cw] = cv2.resize(cv2.imread(p), (cw, ch), interpolation=cv2.INTER_AREA)
    pen.rect(x - 3, y - 3, x + cw + 3, y + ch + 3, 5, INK, f'fr{k}')
    pen.circle((x + 24, y + 24), 19, 3, INK, f'nc{k}', fill=INK); pen.text(str(k + 1), (x + 24, y + 24), 24, PAPER, 'marker')
VIG, GR = paper_finish()
f = np.clip(img.astype(np.float32) * VIG + GR[0] * .6, 0, 255).astype(np.uint8)
cv2.imwrite('starship-grokbot-season2-thumb.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 90]); print('ok')
