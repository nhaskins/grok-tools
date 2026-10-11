# listen-free proxies: duration, median F0, F0 spread, peak, RMS, whisper transcript
import sys, numpy as np, librosa
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
for f in sys.argv[1:]:
    y, sr = librosa.load(f, sr=16000)
    f0, vf, _ = librosa.pyin(y, fmin=50, fmax=400, sr=sr)
    f0 = f0[~np.isnan(f0)]
    segs, _ = m.transcribe(y.astype(np.float32), beam_size=5)
    txt = " ".join(s.text.strip() for s in segs)
    print(f"{f.split('/')[-1]}: {len(y)/sr:.2f}s F0med {np.median(f0) if len(f0) else 0:.0f}Hz F0sd {np.std(f0) if len(f0) else 0:.0f} peak {np.abs(y).max():.2f} rms {np.sqrt((y**2).mean()):.3f} | {txt}", flush=True)
