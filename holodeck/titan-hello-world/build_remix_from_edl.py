import subprocess,sys
suffix=sys.argv[1] if len(sys.argv)>1 else ''; W,H=(int(x) for x in (sys.argv[2] if len(sys.argv)>2 else '1280x708').split('x'))
out=sys.argv[3] if len(sys.argv)>3 else 'remix.mp4'
names=['bridge','ship','engine','captain','flyby']
clips=['titan-bridge-loop-v2','titan-starship-flying-loop','titan-engine-room-loop','titan-captain-closeup-loop','titan-planet-flyby-loop']
D=float(open('dur.txt').read())
segs=[(float(l[:7]),float(l[8:15]),names.index(l[16:].strip())) for l in open('remix-edl.txt')]
by=[[] for _ in clips]
for a,b,s in segs: by[s].append((a,b))
args=['ffmpeg','-v','error','-y']
for c in clips: args+=['-stream_loop','-1','-i',c+suffix+'.mp4']
args+=['-i','titan-bridge-theme-epic.mp3']
f=[f'[{i}:v]setpts=PTS-STARTPTS,scale={W}:{H}:flags=lanczos,setsar=1[c{i}]' for i in range(5)]
prev='c0'
for k in range(1,5):
    e='+'.join(f'between(t,{a:.3f},{b-0.001:.3f})' for a,b in by[k])
    f.append(f"[{prev}][c{k}]overlay=enable='{e}'[o{k}]"); prev=f'o{k}'
f.append(f"[{prev}]fade=t=in:st=0:d=1.5,fade=t=out:st={D-3:.2f}:d=3[v]")
args+=['-filter_complex',';'.join(f),'-map','[v]','-map','5:a:0','-t',str(D),'-c:v','libx264','-preset','medium','-crf','14','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k',out]
subprocess.check_call(args); print('ok',out)
