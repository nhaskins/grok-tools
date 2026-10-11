"""2.5 s "STARSHIP GROKBOT / SEASON ONE" ink title card (stamp thud at 0.45 s) (1080p24) for the season compilation."""
import sys, math, subprocess
sys.path.insert(0, '/workspace/holodeck/titan-hello-world/stick-poc'); sys.path.insert(0, '/workspace/holodeck/brand')
import numpy as np, cv2
from stickfig import *
from inkset import W, H, paper_finish, sparkle
import sets as SETS
FPS, NF = 24, 60
VIG, GRAINS = paper_finish()
EPS = ['The Daily Log', 'The Webhook', 'Holodeck Program 01', 'The Red Shirts', 'Merge Conflict', 'Ship It Friday',
       'Prompt Injection', 'Hallucination', 'Technical Debt', 'CAPTCHA', 'Context Window', 'Rate Limited']
T_STAMP = 0.45
def frame(i, t=None):
    t = i / FPS if t is None else t
    img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, (960, 540, 1.0), int(t * 12) + 2)
    pen.rect(40, 40, W - 40, H - 40, 6, INK, 'b1'); pen.rect(60, 60, W - 60, H - 60, 3, INK, 'b2')
    SETS.outlined(pen, 'STARSHIP GROKBOT', (960, 380), 160, 10)
    pen.line([(330, 480), (1590, 472)], 7, INK, 'ul')
    if t >= T_STAMP: SETS.stamp(pen, 'SEASON ONE', (960, 680), t, T_STAMP, 130, w=9, sid='s1')
    for j, (x, y) in enumerate([(230, 210), (1700, 240), (300, 880), (1640, 860), (960, 960), (330, 640), (1590, 650)]):
        sparkle(pen, (x, y), 24 + 6 * math.sin(t * 9 + j), INK, f'sp{j}')
    f = img.astype(np.float32) * VIG + GRAINS[int(t * 12) % 4]
    return np.clip(f, 0, 255).astype(np.uint8)
def audio(path):
    d = NF / FPS; ms = int(T_STAMP * 1000)
    thud = f"aevalsrc='0.9*sin(2*PI*(62-18*t)*t)*exp(-14*t)+0.25*sin(2*PI*124*t)*exp(-24*t)':s=48000:d=0.45,adelay={ms}"
    slap = f"anoisesrc=d=0.06:c=pink:r=48000:a=0.7,highpass=f=600,lowpass=f=5000,afade=t=out:st=0.01:d=0.05,adelay={ms}"
    room = f"anoisesrc=d={d}:c=brown:r=48000:a=0.05,lowpass=f=400"
    fc = (f"{thud}[t];{slap}[s];{room}[r];[t][s][r]amix=inputs=3:normalize=0:duration=longest,apad,atrim=0:{d},"
          f"afade=t=in:d=0.08,afade=t=out:st={d - .25}:d=0.25,volume=-6dB,aformat=sample_rates=48000:channel_layouts=stereo[a]")
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-filter_complex', fc, '-map', '[a]', '-c:a', 'pcm_s16le', path], check=True)
if __name__ == '__main__':
    if '--still' in sys.argv: cv2.imwrite('card_still2.png', frame(0, 1.4)); sys.exit()
    audio('card_audio.wav')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', '24', '-i', '-',
                          '-i', 'card_audio.wav',
                          '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-af', 'apad', '-t', str(NF / FPS), 'season-card.mp4'], stdin=subprocess.PIPE)
    for i in range(NF): p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait(); print('card ok')
