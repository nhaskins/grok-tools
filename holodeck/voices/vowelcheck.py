"""Judge 'Grok Bot' takes: whisper word (no prompt, so it can't be nudged toward 'Bot') + F1/F2 trajectory of the
vowel in the second word. /a/ (bot): high F1 (~650-800 Hz), F2 low and flat. /oU/ (boat): F1 lower (~450-550) and
F2 glides down toward /U/ over the vowel. Score: F1 mean (higher = better) and F2 drop start->end (smaller = better)."""
import sys, re, numpy as np, parselmouth, librosa
from faster_whisper import WhisperModel
M = WhisperModel('small.en', device='cpu', compute_type='int8')

def diph(p):
    """/aI/ (Rise-uh): F1 starts high (~650+) and falls, F2 rises (~+400 Hz). /i:/ (REE-sa): F1 low (~300) flat,
    F2 high (~2000+) flat. Reports F1/F2 start->end over the first vowel (voiced frames of the word's first 55%)."""
    segs, _ = M.transcribe(librosa.load(p, sr=16000)[0].astype(np.float32), word_timestamps=True, beam_size=5)
    ws = [w for s in segs for w in s.words]; txt = ''.join(w.word for w in ws).strip()
    tgt = next((ws[i + 1] for i, w in enumerate(ws[:-1]) if w.word.strip(' ,.').lower() == AFTER), None)
    if tgt is None: print(f'{p.split("/")[-1]}: ?? | {txt}'); return
    snd = parselmouth.Sound(p)
    fm = snd.to_formant_burg(time_step=.005, max_number_of_formants=5, maximum_formant=5000); pit = snd.to_pitch(time_step=.005)
    a, b = tgt.start, tgt.start + .55 * (tgt.end - tgt.start)
    ts = [t for t in np.arange(a, b, .005) if pit.get_value_at_time(t) == pit.get_value_at_time(t)]
    if len(ts) < 8: print(f'{p.split("/")[-1]}: short vowel | {txt}'); return
    F1 = np.array([fm.get_value_at_time(1, t) for t in ts]); F2 = np.array([fm.get_value_at_time(2, t) for t in ts])
    q = max(len(ts) // 4, 2)
    f1a, f1b, f2a, f2b = (np.nanmedian(x) for x in (F1[:q], F1[-q:], F2[:q], F2[-q:]))
    f1pk = np.nanpercentile(F1, 80)
    ok = f1pk > 550 and f2b - f2a > 250
    print(f'{p.split("/")[-1]}: word="{tgt.word.strip()}" F1 {f1a:.0f}->{f1b:.0f} (pk {f1pk:.0f}) F2 {f2a:.0f}->{f2b:.0f} '
          f'{"AI-OK" if ok else "--"} | {txt}')
AFTER = None
args = sys.argv[1:]
if '--after' in args:            # diphthong mode: first vowel of the word after AFTER (e.g. "for" -> Risa)
    i = args.index('--after'); AFTER = args[i + 1].lower(); args = args[:i] + args[i + 2:]
for p in args:
    if AFTER: diph(p); continue
    segs, _ = M.transcribe(librosa.load(p, sr=16000)[0].astype(np.float32), word_timestamps=True, beam_size=5)
    ws = [w for s in segs for w in s.words]
    txt = ''.join(w.word for w in ws).strip()
    # second word of the name: the word after one containing 'gr' (or a single 'g..bot'-ish word)
    tgt = None
    for i, w in enumerate(ws):
        if re.search(r'gr|cr|kr', w.word.lower()):
            if re.search(r'b[a-z]*t|boat|bought', w.word.lower()): tgt = w
            elif i + 1 < len(ws): tgt = ws[i + 1]
            break
    if tgt is None: print(f'{p}: ?? | {txt}'); continue
    snd = parselmouth.Sound(p)
    a, b = tgt.start, tgt.end
    if 'gr' in tgt.word.lower() or 'cr' in tgt.word.lower(): a = (a + b) / 2   # merged word: take the second half
    fm = snd.to_formant_burg(time_step=.005, max_number_of_formants=5, maximum_formant=5000)
    pit = snd.to_pitch(time_step=.005)
    ts = [t for t in np.arange(a, b, .005) if pit.get_value_at_time(t) == pit.get_value_at_time(t)]   # voiced only
    if len(ts) < 6: print(f'{p}: short vowel | {txt}'); continue
    ts = ts[1:-1]; n = len(ts)
    F1 = np.array([fm.get_value_at_time(1, t) for t in ts]); F2 = np.array([fm.get_value_at_time(2, t) for t in ts])
    q = max(n // 4, 1)
    print(f'{p.split("/")[-1]}: word="{tgt.word.strip()}" F1={np.nanmedian(F1):.0f} F2 {np.nanmedian(F2[:q]):.0f}->{np.nanmedian(F2[-q:]):.0f} '
          f'(drop {np.nanmedian(F2[:q]) - np.nanmedian(F2[-q:]):+.0f}) | {txt}')
