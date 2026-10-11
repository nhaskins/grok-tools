"""Big FX pass over the remix cut: punch zooms, shakes, flashes, RGB split/glitch, whip transitions.
Reads titan-bridge-theme-remix.mp4 (no text), writes frames to ffmpeg which also burns titles+lyrics."""
import numpy as np, cv2, subprocess, sys
W,H,FPS=1280,708,24
beats=np.load('beats.npy'); bars=np.load('bars.npy'); D=float(open('dur.txt').read())
cuts=[float(l.split('-')[1].split()[0]) for l in open('remix-edl.txt')][:-1]
# section intensity: (start, intensity)
SECT=[(0,0.25),(39.4,0.6),(46.6,1.0),(66.5,0.3),(75.3,0.6),(82.5,1.15),(93.0,0.7),(125.6,0.8),(132.8,0.3),(140.0,1.0),(154.2,1.35),(175.5,1.0)]
def inten(t): return [i for s,i in SECT if t>=s][-1]
HITS=[46.65,82.5,140.0,154.2,157.26,175.5,18.6]   # big impacts: flash + heavy shake
rng=np.random.default_rng(7)
def last_before(arr,t):
    i=np.searchsorted(arr,t,side='right')-1
    return arr[i] if i>=0 else -99
yy,xx=np.mgrid[0:H,0:W]; vig=1-0.35*(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)/2; vig=vig[...,None].astype(np.float32)
def whip_offset(t):
    for c in cuts:
        d=t-c
        if -0.12<=d<0.12:
            # only whip on cuts inside energetic sections (and at section changes)
            I=inten(c); sec_change=any(abs(c-s)<0.3 for s,_ in SECT)
            if I<0.6 and not sec_change: return 0,0
            u=(d+0.12)/0.24; e=u*u*(3-2*u)
            off=int((e-0.5)*2*W*0.45)   # -0.45W .. +0.45W
            speed=abs(np.sin(np.pi*u))
            return off,int(60*speed)
    return 0,0
dec=subprocess.Popen(['ffmpeg','-v','error','-i','titan-bridge-theme-remix.mp4','-vf',f'scale={W}:{H}:flags=lanczos','-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i','titan-bridge-theme-epic.mp3',
    '-vf','ass=titles.ass,ass=lyrics.ass','-map','0:v','-map','1:a','-t',str(D),'-af',f'afade=t=out:st={D-3:.2f}:d=3',
    '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-movflags','+faststart','titan-bridge-theme-fx.mp4'],stdin=subprocess.PIPE)
n=0; fs=W*H*3
while True:
    buf=dec.stdout.read(fs)
    if len(buf)<fs: break
    f=np.frombuffer(buf,np.uint8).reshape(H,W,3).astype(np.float32)
    t=n/FPS; I=inten(t)
    db=t-last_before(beats,t); dbar=t-last_before(bars,t); dh=t-last_before(np.array(sorted(HITS)),t)
    # 1. punch zoom: every beat in big sections, every bar otherwise
    pz=(0.07*I*np.exp(-db/0.11)) if I>=1.0 else (0.05*I*np.exp(-dbar/0.15))
    pz+=0.12*np.exp(-dh/0.18)
    # slow drift in calm sections
    drift=0.04*((t%7.0)/7.0) if I<0.5 else 0
    z=1+pz+drift
    # 2. shake
    amp=28*np.exp(-dh/0.25)+ (10*I*np.exp(-dbar/0.2) if I>=1.0 else 0)
    sx,sy=(rng.normal(0,amp),rng.normal(0,amp)) if amp>0.5 else (0,0)
    rot=rng.normal(0,amp*0.04) if amp>0.5 else 0
    M=cv2.getRotationMatrix2D((W/2,H/2),rot,z); M[0,2]+=sx; M[1,2]+=sy
    f=cv2.warpAffine(f,M,(W,H),borderMode=cv2.BORDER_REFLECT)
    # 3. whip transition
    off,blur=whip_offset(t)
    if off:
        f=np.roll(f,off,axis=1)
        if blur>2: f=cv2.blur(f,(blur,1))
    # 4. RGB split + glitch slices
    k=int(14*np.exp(-dh/0.2)+ (8*I*np.exp(-db/0.1) if I>=1.0 else 3*I*np.exp(-dbar/0.12)) + (abs(off)/W*30))
    if k>=1:
        b,g,r=cv2.split(f); f=cv2.merge([np.roll(b,-k,axis=1),g,np.roll(r,k,axis=1)])
    if I>=1.15 and dbar<0.12 or dh<0.15:
        for _ in range(rng.integers(3,8)):
            y0=rng.integers(0,H-40); hh=rng.integers(6,40); f[y0:y0+hh]=np.roll(f[y0:y0+hh],int(rng.integers(-60,60)),axis=1)
    # 5. flash (white on hits, blue on big-section bars)
    fl=0.85*np.exp(-dh/0.09)
    if fl>0.01: f=f*(1-fl)+255*fl
    if I>=1.0:
        bf=0.25*np.exp(-dbar/0.08)
        if bf>0.01: f=f*(1-bf)+np.array([255,170,80],np.float32)*bf
    # 6. grade: vignette + grain
    f=f*vig+rng.normal(0,4,(H,W,1)).astype(np.float32)
    # fade in / out
    if t<1.5: f*=t/1.5
    if t>D-3: f*=max(0,(D-t)/3)
    enc.stdin.write(np.clip(f,0,255).astype(np.uint8).tobytes()); n+=1
    if n%480==0: print(n,file=sys.stderr,flush=True)
enc.stdin.close(); enc.wait(); print('frames',n)
