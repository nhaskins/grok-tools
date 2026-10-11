"""HUD / overlay layer drawn on top of FX frames (before ASS text)."""
import numpy as np, cv2
W,H,FPS=1280,708,24   # HUD design grid; drawn here, then scaled to the frame size
CY=(255,220,120)   # cyan-ish (BGR)
AM=(64,176,255)    # amber
GR=(112,255,96)
spec=np.load('spec24.npy'); rms=np.load('rms24.npy'); SR_HOP=22050/918
NAMES=['INTRO','BUILD','DROP','BREAKDOWN','BUILD','DROP II','CRUISE','BUILD','BREAKDOWN','DROP III','CLIMAX','FINALE']
rng=np.random.default_rng(3)
P=rng.random((140,3)).astype(np.float32)  # particles x,y,depth
# barrel distortion maps (viewscreen bend)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
nx=(xx-W/2)/(W/2); ny=(yy-H/2)/(H/2); r2=nx*nx+ny*ny; k=0.045
MX=(nx*(1+k*r2))*W/2+W/2; MY=(ny*(1+k*r2))*H/2+H/2
SCAN=np.ones((H,1,1),np.float32); SCAN[::3]=0.82
FONT=cv2.FONT_HERSHEY_SIMPLEX; MONO=cv2.FONT_HERSHEY_PLAIN
def T(o,s,p,c,sc=1.0,th=1,font=MONO): cv2.putText(o,s,p,font,sc,c,th,cv2.LINE_AA)
def letterbox_h(t):
    a,b=154.2,175.5
    if a<=t<b: return int(78*min(1,(t-a)/0.6))
    if b<=t<b+1.0: return int(78*(1-(t-b)/1.0))
    return 0
_FR={}
def _full(FW,FH):
    if (FW,FH) not in _FR:
        yy2,xx2=np.mgrid[0:FH,0:FW].astype(np.float32)
        nx=(xx2-FW/2)/(FW/2); ny=(yy2-FH/2)/(FH/2); r2=nx*nx+ny*ny
        mx=(nx*(1+k*r2))*FW/2+FW/2; my=(ny*(1+k*r2))*FH/2+FH/2
        sc=np.ones((FH,1,1),np.float32); sc[::3]=0.82
        _FR[(FW,FH)]=(yy2[:,:1,None].copy(),mx,my,sc)
    return _FR[(FW,FH)]
def draw(f,t,I,sect_i,bar_i,db,dbar,dh,bpm=136):
    FH,FW=f.shape[:2]; S=FW/W
    YYF,MXF,MYF,SCANF=_full(FW,FH)
    fi=min(int(t*SR_HOP),len(rms)-1); lv=float(rms[fi]); sp=spec[fi]
    beat=np.exp(-db/0.15); hit=np.exp(-dh/0.25)
    o=np.zeros((H,W,3),np.uint8)   # additive glow layer
    # --- perspective grid (drops / energetic) ---
    ga=0.0 if I<0.6 else (0.55 if I>=1.0 else 0.3)
    if ga>0:
        g=np.zeros_like(o); hz=int(H*0.60); vx=W//2
        for i in range(-14,15):
            x=vx+i*130; cv2.line(g,(vx+i*8,hz),(x if abs(i)<6 else vx+i*400,H),CY,1,cv2.LINE_AA)
        ph=(t*1.6)%1.0
        for j in range(12):
            z=(j+ph)/12; y=int(hz+(H-hz)*z**2.2); cv2.line(g,(0,y),(W,y),CY,1,cv2.LINE_AA)
        fade=np.clip((yy[:,:1]-hz)/(H-hz),0,1)[...,None]
        o=cv2.add(o,(g*fade*ga*(0.6+0.8*beat)).astype(np.uint8))
    # --- particles / star dust ---
    sp_speed=0.002+0.012*I
    P[:,0]=(P[:,0]-sp_speed*(0.3+P[:,2]))%1.0
    for x,y,d in P:
        c=int(90+160*d); cv2.circle(o,(int(x*W),int(y*H)),1 if d<0.7 else 2,(c,c,c),-1,cv2.LINE_AA)
    # --- frame border + corner brackets ---
    m=14; L=46; bc=tuple(int(v*(0.55+0.45*beat)) for v in CY)
    cv2.rectangle(o,(m,m),(W-m,H-m),(70,60,40),1)
    for (x,y,sx,sy) in [(m,m,1,1),(W-m,m,-1,1),(m,H-m,1,-1),(W-m,H-m,-1,-1)]:
        cv2.line(o,(x,y),(x+sx*L,y),bc,2,cv2.LINE_AA); cv2.line(o,(x,y),(x,y+sy*L),bc,2,cv2.LINE_AA)
    T(o,'NCC-TITAN  //  HOLODECK PROGRAM 01',(W//2-170,H-m-4),(150,130,90),0.8)
    # --- heading tape (top centre) ---
    hd=(t*9)%360; cx=W//2
    cv2.line(o,(cx-180,40),(cx+180,40),(120,100,70),1)
    for d in range(-20,21):
        deg=int(hd)+d; x=int(cx+(deg-hd)*9)
        if deg%5==0:
            cv2.line(o,(x,40),(x,32 if deg%10 else 26),CY,1,cv2.LINE_AA)
            if deg%10==0: T(o,f'{deg%360:03d}',(x-12,22),CY,0.8)
    cv2.drawMarker(o,(cx,46),AM,cv2.MARKER_TRIANGLE_UP,10,1)
    # --- targeting reticle (energetic sections) ---
    if I>=0.6:
        c=(W//2,H//2-20); s=1+0.12*beat+0.3*hit; a=t*40
        rc=tuple(int(v*(0.45+0.4*beat)) for v in CY)
        for k in range(3):
            st=a+k*120; cv2.ellipse(o,c,(int(70*s),int(70*s)),0,st,st+70,rc,1,cv2.LINE_AA)
        cv2.ellipse(o,c,(int(100*s),int(100*s)),0,-a,-a+40,AM,1,cv2.LINE_AA)
        cv2.ellipse(o,c,(int(100*s),int(100*s)),0,-a+180,-a+220,AM,1,cv2.LINE_AA)
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            cv2.line(o,(c[0]+dx*int(18*s),c[1]+dy*int(18*s)),(c[0]+dx*int(40*s),c[1]+dy*int(40*s)),rc,1,cv2.LINE_AA)
        if dh<0.6: T(o,'TARGET LOCK',(c[0]-55,c[1]+int(125*s)),AM,1.0)
    # --- radar (bottom-left) ---
    rc_=(86,H-96); R=56
    cv2.circle(o,rc_,R,(110,90,60),1,cv2.LINE_AA); cv2.circle(o,rc_,R//2,(80,70,50),1,cv2.LINE_AA)
    cv2.line(o,(rc_[0]-R,rc_[1]),(rc_[0]+R,rc_[1]),(70,60,45),1); cv2.line(o,(rc_[0],rc_[1]-R),(rc_[0],rc_[1]+R),(70,60,45),1)
    ang=(t*2.2)%(2*np.pi)
    for k in range(10):
        aa=ang-k*0.06; col=tuple(int(v*(1-k/10)) for v in GR)
        cv2.line(o,rc_,(int(rc_[0]+R*np.cos(aa)),int(rc_[1]+R*np.sin(aa))),col,1,cv2.LINE_AA)
    for bx,by in [(0.4,-0.3),(-0.5,0.2),(0.1,0.6)]:
        cv2.circle(o,(int(rc_[0]+bx*R),int(rc_[1]+by*R)),2,GR,-1)
    T(o,'SCAN',(rc_[0]-16,rc_[1]+R+16),GR,0.8)
    # --- readout panel (top-right) ---
    px,py=W-250,70
    ov=f.copy(); cv2.rectangle(ov,(int((px-12)*S),int((py-22)*S)),(int((W-26)*S),int((py+150)*S)),(20,12,8),-1); f[:]=cv2.addWeighted(ov,0.45,f,0.55,0)
    T(o,'TITAN // BRIDGE TELEMETRY',(px,py),AM,0.9)
    T(o,f'BPM      {bpm}',(px,py+24),CY,1.0); T(o,f'SECTION  {NAMES[sect_i]}',(px,py+44),CY,1.0)
    T(o,f'BAR      {bar_i:03d}',(px,py+64),CY,1.0)
    mm=int(t//60); ss=t%60; T(o,f'T+       {mm:02d}:{ss:05.2f}',(px,py+84),CY,1.0)
    T(o,'WARP',(px,py+112),AM,1.0)
    cv2.rectangle(o,(px+50,py+102),(px+210,py+114),(90,70,50),1)
    wl=int(158*lv); cv2.rectangle(o,(px+51,py+103),(px+51+wl,py+113),AM if lv<0.85 else (80,80,255),-1)
    T(o,f'{lv*9.9:3.1f}',(px+215,py+113),AM,0.9)
    T(o,'SHIELDS',(px,py+136),GR,0.9)
    for s_ in range(10):
        on=s_<int(10*(0.55+0.45*np.sin(t*0.5)**2)); cv2.rectangle(o,(px+70+s_*14,py+127),(px+80+s_*14,py+137),GR if on else (40,60,40),-1)
    # --- spectrum (bottom-right) ---
    bx0,by0=W-28-24*11,H-40
    for i,v in enumerate(sp):
        h=int(4+70*v); col=AM if i<8 else CY
        cv2.rectangle(o,(bx0+i*11,by0-h),(bx0+i*11+7,by0),col,-1)
    T(o,'AUDIO SPECTRUM',(bx0,by0+16),(150,130,90),0.8)
    # --- lens flare streaks on hits / drop beats ---
    fl=0.9*hit+(0.45*beat if I>=1.0 else 0)
    if fl>0.05:
        small=cv2.cvtColor(cv2.resize(f,(64,36)),cv2.COLOR_BGR2GRAY); yx=np.unravel_index(np.argmax(small),small.shape)
        sy,sx=int(yx[0]*H/36),int(yx[1]*W/64)
        st=np.zeros_like(o); cv2.line(st,(0,sy),(W,sy),(255,190,110),3); cv2.circle(st,(sx,sy),18,(255,220,180),-1)
        st=cv2.GaussianBlur(st,(0,0),sigmaX=40,sigmaY=3)
        o=cv2.add(o,(st*min(fl,1.0)).astype(np.uint8))
    # composite: glow (blurred copy) + crisp layer, additive
    if S!=1: o=cv2.resize(o,(FW,FH),interpolation=cv2.INTER_CUBIC)
    glow=cv2.GaussianBlur(o,(0,0),4*S)
    out=f.astype(np.float32)+o.astype(np.float32)*0.9+glow.astype(np.float32)*0.6
    # CRT: scanlines + rolling bar + flicker + bend
    out*=SCANF
    rb=((t*0.25)%1.3-0.15)*FH; out+=18*np.exp(-((YYF-rb)/(30*S))**2)
    out*=1+0.015*np.sin(t*60)
    out=cv2.remap(np.clip(out,0,255).astype(np.uint8),MXF,MYF,cv2.INTER_LINEAR,borderValue=(0,0,0))
    # letterbox (climax) drawn after bend, HUD readouts stay visible over it
    lb=int(letterbox_h(t)*S)
    if lb: out[:lb]=out[:lb]//5; out[FH-lb:]=out[FH-lb:]//5
    return out
