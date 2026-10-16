"""Lay the finalized lines on a timeline, mix dialogue (+ quiet bridge hum), and write
timeline.json: per line start/end + whisper word times (absolute), and per-speaker RMS envelopes at 24 fps."""
import json, subprocess, numpy as np, librosa
from faster_whisper import WhisperModel
D = '/workspace/holodeck/voices/demo17'; FPS = 24; SR = 44100
LINES = [  # id, speaker, text (captions), gap before (s)
    ('r1', 'riker',   "Grok Bot, my pen is drawing on the wrong monitor. Again.", 0.2),
    ('g1', 'grokbot', "Beaming into your desktop now. I detect three monitors, two drivers, and one very confused pen.", 0.35),
    ('b1', 'barclay', "I, I drew a starship, but it landed on the sideways screen!", 0.35),
    ('g2', 'grokbot', "Fixed. I added a watcher that checks the pen every three seconds.", 0.3),
    ('r2', 'riker',   "Great. Now my pen stutters worse than Barclay.", 0.5),
    ('g3', 'grokbot', "Revised. One script at login, then it exits. Type fixpen if you ever replug.", 0.35),
    ('p1', 'picard',  "Finally. A fix that knows when to stop.", 0.4),
]
TAIL = 2.6
m = WhisperModel("small.en", device="cpu", compute_type="int8")
t = 0.0; out = []; clips = []
for lid, who, text, gap in LINES:
    y, _ = librosa.load(f'{D}/{lid}.mp3', sr=SR, mono=True)
    t += gap; dur = len(y) / SR
    y16 = librosa.resample(y, orig_sr=SR, target_sr=16000)
    segs, _ = m.transcribe(y16.astype(np.float32), beam_size=5, word_timestamps=True, initial_prompt=text)
    ws = [dict(w=w.word.strip(), s=round(t + w.start, 3), e=round(t + w.end, 3)) for s in segs for w in s.words]
    for i in range(len(ws) - 1, 0, -1):     # whisper splits "ninety-five" into "ninety" + "-five": merge
        if ws[i]['w'].startswith('-'): ws[i - 1]['w'] += ws[i]['w']; ws[i - 1]['e'] = ws[i]['e']; del ws[i]
    caps = text.split()
    if len(ws) != len(caps):
        print('  word count', len(ws), '!=', len(caps), '-> script words, time-spread over whisper span')
        a0, a1 = (ws[0]['s'], ws[-1]['e']) if ws else (t, t + dur); L = sum(len(c) for c in caps); acc = 0
        nw = []
        for c in caps:
            s0 = a0 + (a1 - a0) * acc / L; acc += len(c); nw.append(dict(w=c, s=round(s0, 3), e=round(a0 + (a1 - a0) * acc / L, 3)))
        ws = nw
    else:
        for x, c in zip(ws, caps): x['w'] = c
    out.append(dict(id=lid, who=who, text=text, s=round(t, 3), e=round(t + dur, 3), words=ws))
    clips.append((t, y)); print(lid, who, f'{t:.2f}-{t+dur:.2f}', [x['w'] for x in ws])
    t += dur
total = t + TAIL
mix = np.zeros(int(total * SR) + SR, np.float32); env = {}
nf = int(round(total * FPS))
for (t0, y), L in zip(clips, out):
    i0 = int(t0 * SR); mix[i0:i0 + len(y)] += y
    e = env.setdefault(L['who'], np.zeros(nf + 2, np.float32))
    hop = SR // FPS
    for f in range(int(t0 * FPS), min(nf, int((t0 + len(y) / SR) * FPS) + 1)):
        a = int(f * hop - i0); seg = y[max(a, 0):max(a + hop, 0)]
        if len(seg): e[f] = max(e[f], float(np.sqrt((seg ** 2).mean())))
mix = mix[:int(total * SR)]
import soundfile as sf
sf.write(f'{D}/dialogue.wav', mix, SR)
for k in env:   # normalize 0..1 with a soft knee; 95th percentile of voiced frames = fully open
    e = env[k]; v = e[e > 0.005]; ref = np.percentile(v, 95) if len(v) else 1
    env[k] = np.clip((e - 0.01) / (ref - 0.01), 0, 1) ** 0.8
json.dump(dict(total=round(total, 3), fps=FPS, lines=out, env={k: [round(float(x), 3) for x in v] for k, v in env.items()}),
          open(f'{D}/timeline.json', 'w'))
# bed: very quiet low hum + filtered noise air, under the dialogue
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{D}/dialogue.wav',
    '-f', 'lavfi', '-t', f'{total}', '-i', 'sine=f=55:r=44100', '-f', 'lavfi', '-t', f'{total}', '-i', 'sine=f=110.6:r=44100',
    '-f', 'lavfi', '-t', f'{total}', '-i', 'anoisesrc=c=brown:r=44100:a=0.5',
    '-filter_complex', '[1]volume=0.018[h1];[2]volume=0.008[h2];[3]lowpass=f=400,volume=0.05[n];'
    '[h1][h2][n]amix=inputs=3:normalize=0,afade=t=in:d=0.4,afade=t=out:st=%.2f:d=0.6[bed];'
    '[0][bed]amix=inputs=2:normalize=0,alimiter=limit=0.95[o]' % (total - 0.6),
    '-map', '[o]', '-ar', '44100', '-ac', '1', f'{D}/mix.wav'], check=True)
print('total', round(total, 2))
