"""Gallery of every pose in stickfig.POSES -> pose_test.png (props rotate: cap, beard, shine, robot)."""
import numpy as np, cv2
from stickfig import *
names = list(POSES); cols = 8; rows = (len(names) + cols - 1) // cols
img = np.full((rows * 270 + 40, 1920, 3), PAPER, np.uint8); pen = Pen(img, (960, img.shape[0] / 2, 1.0), boil=3)
pen.cam = (960, img.shape[0] / 2, 1.0); pen.W, pen.H = 1920, img.shape[0]
for i, n in enumerate(names):
    x = 120 + (i % cols) * 240; y = 150 + (i // cols) * 270
    props = [{'cap', 'badge'}, {'beard', 'badge'}, {'shine', 'badge'}, {'robot'}][i % 4]
    F = Figure(n, x, y, facing=1 if i % 2 == 0 else -1, props=props, scale=0.8); F.key(0, n if n != 'sit' else 'sit+thumbs', 0)
    F.draw(pen, 1.0)
    pen.text(n, (x, y + 112), 26)
cv2.imwrite('pose_test.png', img)
