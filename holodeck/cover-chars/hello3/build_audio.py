"""Hello v3 audio: 5 Piper (en_US-ryan-low) lines through the episode Grok Bot chain (voices/finalize.sh robot),
laid on a timeline, whisper word times per line, 24 fps RMS envelope, hum bed, whole mix normalized to -16 LUFS."""
import json, subprocess, re, numpy as np, librosa, soundfile as sf
from faster_whisper import WhisperModel
D = '/workspace/holodeck/cover-chars/hello3'; FPS = 24; SR = 44100; T0 = 5.0; TAIL = 1.3
LINES = [  # id, take, caption text (real spelling), gap before
    ('l1', 's1c', "Hello from Starship Grok Bot.", 0.0),
    ('l2', 's2a', "Nice to meet you.", 0.35),
    ('l3', 's3a', "I'm here to help you get things done alongside the crew.", 0.3),
    ('l4', 's4d', "Starship Grok Bot, here to help.", 0.45),
    ('l5', 's5a', "Thanks!", 0.35)]
m = WhisperModel("small.en", device="cpu", compute_type="int8")
t = T0; out = []; ys = []
for lid, take, text, gap in LINES:
    t += gap
    y, _ = librosa.load(f'{D}/takes/{take}-fx.mp3', sr=SR, mono=True); dur = len(y) / SR
    segs, _ = m.transcribe(librosa.resample(y, orig_sr=SR, target_sr=16000).astype(np.float32), beam_size=5, word_timestamps=True,
                           initial_prompt=text)
    ws = [dict(w=w.word.strip(), s=round(t + w.start, 3), e=round(t + w.end, 3)) for s in segs for w in s.words]
    caps = text.split()
    # whisper writes "Grokbot" as one word: split its time across the caption's "Grok Bot"
    wl = []
    for x in ws:
        if re.match(r'(?i)gr?o[ck]+bot', x['w']) and len(ws) < len(caps):
            mid = round((x['s'] + x['e']) / 2, 3); wl += [dict(x, w='Grok', e=mid), dict(x, w='Bot', s=mid)]
        else: wl.append(x)
    for j in range(1, len(wl)):
        if wl[j]['e'] - wl[j]['s'] < .1 and wl[j]['s'] - wl[j - 1]['e'] > .15: wl[j]['s'] = round(wl[j - 1]['e'] + .08, 3)
    if len(wl) == len(caps):
        for x, c in zip(wl, caps): x['w'] = c
    else:                                   # fallback: even spread
        print('WORD COUNT MISMATCH', lid, [x['w'] for x in wl]); wl = [dict(w=c, s=round(t + dur * k / len(caps), 3), e=round(t + dur * (k + 1) / len(caps), 3)) for k, c in enumerate(caps)]
    out.append(dict(id=lid, take=take, text=text, s=round(t, 3), e=round(t + dur, 3), words=wl)); ys.append((t, y)); t += dur
    print(lid, take, round(out[-1]['s'], 2), '->', round(out[-1]['e'], 2), [x['w'] for x in wl])
TOTAL = round(t + TAIL, 2)
mix = np.zeros(int(TOTAL * SR), np.float32)
for t0, y in ys: i0 = int(t0 * SR); mix[i0:i0 + len(y)] += y
nf = int(TOTAL * FPS); hop = SR // FPS; env = np.zeros(nf + 2, np.float32)
for f in range(nf):
    seg = mix[f * hop:(f + 1) * hop]; env[f] = np.sqrt((seg ** 2).mean()) if len(seg) else 0
v = env[env > 0.005]; ref = np.percentile(v, 95); env = np.clip((env - 0.01) / (ref - 0.01), 0, 1) ** 0.8
sf.write(f'{D}/dialogue.wav', mix, SR)
json.dump(dict(total=TOTAL, fps=FPS, lines=out, env=[round(float(x), 3) for x in env]), open(f'{D}/timeline.json', 'w'))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{D}/dialogue.wav',
    '-f', 'lavfi', '-t', f'{TOTAL}', '-i', 'sine=f=55:r=44100', '-f', 'lavfi', '-t', f'{TOTAL}', '-i', 'sine=f=110.6:r=44100',
    '-f', 'lavfi', '-t', f'{TOTAL}', '-i', 'anoisesrc=c=brown:r=44100:a=0.5',
    '-filter_complex', '[1]volume=0.018[h1];[2]volume=0.008[h2];[3]lowpass=f=400,volume=0.05[n];'
    '[h1][h2][n]amix=inputs=3:normalize=0,afade=t=in:d=0.4,afade=t=out:st=%.2f:d=0.6[bed];'
    '[0][bed]amix=inputs=2:normalize=0[o]' % (TOTAL - 0.6),
    '-map', '[o]', '-ar', '48000', '-ac', '2', f'{D}/mix_raw.wav'], check=True)
# whole-mix loudness -> -16 LUFS (measure, gain, limiter at -1.5 dBFS)
r = subprocess.run(['ffmpeg', '-i', f'{D}/mix_raw.wav', '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]); g = -16.0 - I
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{D}/mix_raw.wav', '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:level=false',
                '-ar', '48000', f'{D}/mix.wav'], check=True)
print('total', TOTAL, 'raw I', I, 'gain', round(g, 2))
