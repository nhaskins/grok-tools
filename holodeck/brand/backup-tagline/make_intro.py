"""STARSHIP GROKBOT intro bumper: exactly 24 frames (1.0 s), 1920x1080 @24, AAC stereo 48 kHz.
Frame 0 = finished logo card (social preview): saluting Grok-Bot-head starship + hand-lettered STARSHIP GROKBOT.
0.25 s the ship zips off right (speed lines, whoosh L->R), tiny ink splat + ding, then a fast ink wipe (0.70-0.96 s)
that leaves solid ink for the cut into the episode poster. Reuses the ship drawing from make_sting.py.
Usage: python make_intro.py [out.mp4] [--still]"""
import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import make_sting as MS
from make_sting import *          # Pen, PAPER, INK, ease..., SETS, W, H, paper_finish, splat, partial
import numpy as np, cv2

FPS, NF = 24, 24; DUR = NF / FPS
OUT = next((a for a in sys.argv[1:] if a.endswith('.mp4')), os.path.join(HERE, 'starship-grokbot-intro.mp4'))
T_GO, T_SPLAT, T_W0, T_W1 = 0.25, 0.50, 0.70, 0.96
# ship placement for the card (sting module reads these globals)
MS.CX, MS.CY, MS.SS = 1080, 385, 1.55
TT0 = 0.95                         # sting-time at which the ship is fully drawn + saluting
MS.T_ZIP, MS.T_ZIPEND = TT0 + T_GO, TT0 + T_GO + 0.32

STARS = [(170, 150, 1.0), (420, 520, .7), (1600, 120, .8), (1790, 470, 1.1), (300, 900, .8), (1660, 930, .9), (1450, 560, .6), (560, 110, .6)]
def logo(pen, t):
    pen.rect(40, 34, W - 40, H - 34, 5, INK, 'frame'); pen.rect(58, 52, W - 58, H - 52, 2, INK, 'frame2')
    for j, (x, y, s) in enumerate(STARS):
        r = 16 * s * (1 + .15 * math.sin(t * 9 + j))
        pen.line([(x - r, y), (x + r, y)], 4, INK, f'st{j}a'); pen.line([(x, y - r), (x, y + r)], 4, INK, f'st{j}b')
    SETS.outlined(pen, 'STARSHIP GROKBOT', (960, 720), 150, 8)
    pen.line([(420, 818), (960, 812), (1500, 820)], 7, INK, 'ul')
    pen.text('ink-on-paper adventures of a boxy little bot', (960, 885), 46, INK, 'hand')

def wipe(pen, t):
    k = ease(clamp01((t - T_W0) / (T_W1 - T_W0)))
    if k <= 0: return
    fx = -250 + 2450 * k
    ys = np.linspace(-60, H + 60, 24)
    edge = [(fx + 70 * math.sin(y * .013 + 1.3) + 35 * math.sin(y * .041), y) for y in ys]
    pen.fill([(-100, -60)] + edge + [(-100, H + 60)], INK)
    for j in range(6):                       # drips/blobs riding the front
        y = 90 + j * 180; pen.dot((edge[min(int(y / (H + 120) * 24), 23)][0] + 30, y), 20 + 6 * (j % 3), INK)

VIG, GRAINS = paper_finish()
def frame(i):
    t = i / FPS
    img = np.full((H, W, 3), PAPER, np.uint8); pen = Pen(img, (960, 540, 1.0), int(t * 12) + 5)
    tt = TT0 + t
    MS.speed_lines(pen, tt); MS.draw_ship(pen, tt)
    logo(pen, t)
    if t >= T_SPLAT: splat(pen, (1745, 330), t, T_SPLAT)
    wipe(pen, t)
    f = img.astype(np.float32) * VIG + GRAINS[int(t * 12) % 4]
    return np.clip(f, 0, 255).astype(np.uint8)

def audio(path):
    whoosh = ("anoisesrc=d=0.42:c=pink:r=48000:a=0.9,highpass=f=300,lowpass=f=5500,aformat=channel_layouts=stereo,"
              "aeval='val(ch)*pow(sin(PI*min(t/0.42,1)),2)*if(eq(ch,0),1-0.85*t/0.42,0.15+0.85*t/0.42)':c=same,"
              f"adelay={int((T_GO - .06) * 1000)}|{int((T_GO - .06) * 1000)}")
    dexp = "0.42*sin(2*PI*1568*t)*exp(-6*t)+0.2*sin(2*PI*2349*t)*exp(-8*t)+0.1*sin(2*PI*3136*t)*exp(-10*t)"
    ding = f"aevalsrc='{dexp}|{dexp}':s=48000:d=0.5,adelay={int(T_SPLAT * 1000)}|{int(T_SPLAT * 1000)}"
    swish = ("anoisesrc=d=0.3:c=brown:r=48000:a=0.7,lowpass=f=1800,aformat=channel_layouts=stereo,"
             "aeval='val(ch)*pow(sin(PI*min(t/0.3,1)),2)':c=same,"
             f"adelay={int(T_W0 * 1000)}|{int(T_W0 * 1000)}")
    fc = (f"{whoosh}[w];{ding}[d];{swish}[s];[w][d][s]amix=inputs=3:normalize=0:duration=longest,"
          f"apad,atrim=0:{DUR},afade=t=out:st={DUR - .06}:d=0.06,volume=-5dB,alimiter=limit=0.89,"
          "aformat=sample_rates=48000:channel_layouts=stereo[a]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-filter_complex', fc, '-map', '[a]', '-c:a', 'pcm_s16le', path], check=True)

if __name__ == '__main__':
    if '--still' in sys.argv:
        for i in (0, 8, 12, 18, 23): cv2.imwrite(f'/tmp/intro_{i:02d}.png', frame(i))
        sys.exit()
    wav = OUT + '.wav'; audio(wav)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-tune', 'animation', '-pix_fmt', 'yuv420p',
           '-r', str(FPS), '-frames:v', str(NF), '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-t', str(DUR), '-movflags', '+faststart', OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(NF): p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait(); os.remove(wav); print('done', OUT)
