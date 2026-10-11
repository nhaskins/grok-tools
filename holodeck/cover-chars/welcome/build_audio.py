"""Welcome clip audio: take s3 placed at T_LINE, whisper word times, 24 fps RMS envelope, hum bed (demo12 recipe)."""
import json, subprocess, numpy as np, librosa, soundfile as sf
from faster_whisper import WhisperModel
D = '/workspace/holodeck/cover-chars/welcome'; FPS = 24; SR = 44100; T_LINE = 5.2; TOTAL = 8.0
TEXT = "Welcome to Starship Grokbot."
y, _ = librosa.load(f'{D}/line.mp3', sr=SR, mono=True); dur = len(y) / SR
m = WhisperModel("small.en", device="cpu", compute_type="int8")
segs, _ = m.transcribe(librosa.resample(y, orig_sr=SR, target_sr=16000).astype(np.float32), beam_size=5, word_timestamps=True, initial_prompt=TEXT)
ws = [dict(w=w.word.strip(), s=round(T_LINE + w.start, 3), e=round(T_LINE + w.end, 3)) for s in segs for w in s.words]
print([x['w'] for x in ws])
caps = TEXT.split()                                # captions use the script spelling, timed by whisper's words
if len(caps) == len(ws):
    for x, c in zip(ws, caps): x['w'] = c
mix = np.zeros(int(TOTAL * SR), np.float32); i0 = int(T_LINE * SR); mix[i0:i0 + len(y)] += y[:len(mix) - i0]
nf = int(TOTAL * FPS); hop = SR // FPS; env = np.zeros(nf + 2, np.float32)
for f in range(nf):
    seg = mix[f * hop:(f + 1) * hop]; env[f] = np.sqrt((seg ** 2).mean()) if len(seg) else 0
v = env[env > 0.005]; ref = np.percentile(v, 95); env = np.clip((env - 0.01) / (ref - 0.01), 0, 1) ** 0.8
sf.write(f'{D}/dialogue.wav', mix, SR)
json.dump(dict(total=TOTAL, fps=FPS, line=dict(s=T_LINE, e=round(T_LINE + dur, 3), words=ws), env=[round(float(x), 3) for x in env]),
          open(f'{D}/timeline.json', 'w'))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{D}/dialogue.wav',
    '-f', 'lavfi', '-t', f'{TOTAL}', '-i', 'sine=f=55:r=44100', '-f', 'lavfi', '-t', f'{TOTAL}', '-i', 'sine=f=110.6:r=44100',
    '-f', 'lavfi', '-t', f'{TOTAL}', '-i', 'anoisesrc=c=brown:r=44100:a=0.5',
    '-filter_complex', '[1]volume=0.018[h1];[2]volume=0.008[h2];[3]lowpass=f=400,volume=0.05[n];'
    '[h1][h2][n]amix=inputs=3:normalize=0,afade=t=in:d=0.4,afade=t=out:st=%.2f:d=0.6[bed];'
    '[0][bed]amix=inputs=2:normalize=0,alimiter=limit=0.95[o]' % (TOTAL - 0.6),
    '-map', '[o]', '-ar', '48000', '-ac', '2', f'{D}/mix.wav'], check=True)
print('line', T_LINE, '->', round(T_LINE + dur, 2), ws)
