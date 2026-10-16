import librosa, numpy as np, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
y, sr = librosa.load('track.mp3', sr=22050, mono=True)
dur = len(y)/sr
tempo, bf = librosa.beat.beat_track(y=y, sr=sr, units='frames')
bt = librosa.frames_to_time(bf, sr=sr); tempo=float(np.atleast_1d(tempo)[0])
# downbeat phase: pick the offset (0-3) with the highest low-freq onset strength
oenv = librosa.onset.onset_strength(y=y, sr=sr)
S = np.abs(librosa.stft(y)); low = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S[:40]), sr=sr)
ph = int(np.argmax([low[bf[k::4]].mean() for k in range(4)]))
bars = bt[ph::4]
rms = librosa.feature.rms(y=y)[0]; rt = librosa.times_like(rms, sr=sr)
# sections: agglomerative on chroma+mfcc, beat-synced
feat = np.vstack([librosa.feature.mfcc(y=y,sr=sr,n_mfcc=13), librosa.feature.chroma_cqt(y=y,sr=sr)])
fs = librosa.util.sync(feat, bf); k = max(4, min(9, int(dur//20)))
bnd = librosa.segment.agglomerative(fs, k); bnd_t = sorted(set([0.0]+[float(bt[min(b,len(bt)-1)]) for b in bnd[1:]]+[dur]))
secs=[]
gm = rms.mean()
for a,b in zip(bnd_t[:-1], bnd_t[1:]):
    m = rms[(rt>=a)&(rt<b)].mean(); secs.append(dict(start=round(a,2), end=round(b,2), energy=round(float(m/gm),2)))
for i,s in enumerate(secs):
    e=s['energy']; s['label']='intro' if i==0 else 'outro' if i==len(secs)-1 else ('climax' if e>1.15 else 'build' if e>0.8 else 'calm')
# hits: strongest onset peaks
pk = librosa.util.peak_pick(oenv,pre_max=20,post_max=20,pre_avg=40,post_avg=40,delta=oenv.std()*1.5,wait=40)
pt = librosa.times_like(oenv,sr=sr)[pk]; ps = oenv[pk]
hits = sorted([dict(t=round(float(t),2), strength=round(float(s/oenv.max()),2)) for t,s in sorted(zip(pt,ps),key=lambda x:-x[1])[:15]], key=lambda h:h['t'])
# swells: biggest 4s rms rises
w=int(4*sr/512); d = np.array([rms[i+w:i+2*w].mean()-rms[i:i+w].mean() for i in range(0,len(rms)-2*w,w//2)])
sw = [dict(t=round(float(rt[i*(w//2)+w]),2), rise=round(float(d[i]/gm),2)) for i in np.argsort(-d)[:4]]
out=dict(duration=round(dur,2), tempo=round(tempo,1), beats=[round(float(b),3) for b in bt], downbeat_phase=ph, bars=[round(float(b),3) for b in bars], sections=secs, hits=hits, swells=sorted(sw,key=lambda s:s['t']))
# vocals?
try:
    from faster_whisper import WhisperModel
    y16=librosa.resample(y,orig_sr=sr,target_sr=16000)
    m=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=4)
    seg,_=m.transcribe(y16,vad_filter=True,language='en')
    out['lyrics']=[dict(start=round(s.start,2),end=round(s.end,2),text=s.text.strip()) for s in seg]
except Exception as e: out['lyrics_error']=str(e)
json.dump(out,open('analysis.json','w'),indent=1)
fig,ax=plt.subplots(figsize=(16,4)); ax.plot(rt,rms,'k',lw=.8)
for s in secs: ax.axvspan(s['start'],s['end'],alpha=.15,color={'intro':'b','build':'y','climax':'r','calm':'g','outro':'purple'}[s['label']]); ax.text(s['start']+.5,rms.max()*.95,s['label'])
for b in bars: ax.axvline(b,color='gray',lw=.3)
for h in hits: ax.axvline(h['t'],color='r',lw=1.2)
ax.set_xlabel('s'); ax.set_title(f"track: {dur:.1f}s  {tempo:.1f} BPM"); plt.tight_layout(); plt.savefig('analysis.png',dpi=90)
print(json.dumps({k:v for k,v in out.items() if k not in('beats','bars')},indent=1))
