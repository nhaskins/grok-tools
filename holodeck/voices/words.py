import sys, numpy as np, librosa
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
for f in sys.argv[1:]:
    y, sr = librosa.load(f, sr=16000)
    segs, _ = m.transcribe(y.astype(np.float32), beam_size=5, word_timestamps=True)
    ws = [(w.word.strip(), round(w.start,2), round(w.end,2)) for s in segs for w in s.words]
    rms = librosa.feature.rms(y=y)[0]
    print(f.split('/')[-1], f"{len(y)/sr:.2f}s peakRMS {rms.max():.3f}", ws, flush=True)
