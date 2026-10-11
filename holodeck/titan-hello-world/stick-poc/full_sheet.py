"""Contact sheet of stills pulled from the finished full video (captions included).
python full_sheet.py [video] -> stills-full/*.png + full-sheet.png (4x4) + /tmp/fs_q{1..4}.png quarter sheets for review"""
import subprocess, sys, os, cv2, numpy as np
V = sys.argv[1] if len(sys.argv) > 1 else 'titan-stick-full.mp4'
SHOTS = [(13.0, 'intro: title card'), (20.3, '"Titan, engage"'), (45.4, 'build: countdown'), (47.4, 'drop: warp jump'),
         (55.0, 'verse 1 (POC)'), (67.7, '"Shields up, systems green"'), (70.9, '"The boldest crew..."'), (81.9, '"...keep it in sync"'),
         (92.5, '"Grok Bot crew..."'), (110.0, 'mid: Riker\'s trombone'), (113.6, 'mid: poker'), (140.5, 'final chorus: wild clock'),
         (146.3, 'final chorus: chorus line'), (157.6, '"Engage!"'), (166.0, 'climax: fireworks'), (178.4, 'finale: end card')]
os.makedirs('stills-full', exist_ok=True)
ims = []
for t, lab in SHOTS:
    f = f'stills-full/t{t:06.1f}.png'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', str(t), '-i', V, '-frames:v', '1', f], check=True)
    im = cv2.resize(cv2.imread(f), (960, 540), interpolation=cv2.INTER_AREA)
    im = cv2.copyMakeBorder(im, 0, 44, 0, 0, cv2.BORDER_CONSTANT, value=(243, 238, 230))
    cv2.putText(im, f'{t:.1f}s  {lab}', (12, 572), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2, cv2.LINE_AA)
    ims.append(cv2.copyMakeBorder(im, 6, 6, 6, 6, cv2.BORDER_CONSTANT, value=(40, 40, 40)))
rows = [np.hstack(ims[i:i + 4]) for i in range(0, 16, 4)]
cv2.imwrite('full-sheet.png', np.vstack(rows))
for q in range(4):
    cv2.imwrite(f'/tmp/fs_q{q + 1}_{os.getpid()}.png', np.vstack([np.hstack(ims[q * 4:q * 4 + 2]), np.hstack(ims[q * 4 + 2:q * 4 + 4])]))
print(os.getpid())
