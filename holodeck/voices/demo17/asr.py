import glob, librosa, numpy as np, re, difflib, sys
from faster_whisper import WhisperModel
import tts as _t
m = WhisperModel("small.en", device="cpu", compute_type="int8")
for lid, v, txt, fx in _t.LINES:
    ref = re.sub(r'\[[a-z]+\]|<[^>]+>', '', txt).lower(); ref = re.sub(r'[^a-z ]', '', ref).split()
    for f in sorted(glob.glob(f'takes/{lid}_?_fin.mp3')):
        y, _ = librosa.load(f, sr=16000); s, _ = m.transcribe(y.astype(np.float32), beam_size=5)
        h = ' '.join(x.text for x in s).strip(); hw = re.sub(r'[^a-z ]', '', h.lower()).split()
        r = difflib.SequenceMatcher(None, ref, hw).ratio()
        print(f'{f} {len(y)/16000:.2f}s match={r:.2f} | {h}', flush=True)
