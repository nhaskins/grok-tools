"""HAILING LOOP SFX, synthesized with numpy (no copyrighted audio). Cue times come from hailingloop.py."""
import sys; sys.argv = ['hailingloop.py']
import numpy as np, soundfile as sf
import hailingloop as S
SR = 48000; N = int((S.TOTAL + .5) * SR); out = np.zeros(N, np.float32); HOLD = S.HOLD; rng = np.random.default_rng(18)
def put(sig, t, g=1.0):
    i = int((t + HOLD) * SR); j = min(N, i + len(sig))
    if 0 <= i < N: out[i:j] += g * np.asarray(sig, np.float32)[:j - i]
def tt(d): return np.arange(int(d * SR)) / SR
def lp(x, n=8): return np.convolve(x, np.ones(n) / n, 'same')
def chirp(f0, d=.12):   # comm-badge style hail chirp
    t = tt(d); return (np.sin(2 * np.pi * f0 * t) + .5 * np.sin(2 * np.pi * f0 * 1.5 * t)) * np.exp(-18 * t)
for k, tc in enumerate(S.STEPS):                   # each counter step: hail chirp, rising
    put(chirp(900 + 150 * k), tc, .35); put(chirp(1350 + 150 * k), tc + .09, .25)
tc = S.T_H128 + .1; r = 5                           # the loop: chirps speeding up until the dedupe
while tc < S.T_DD - .05:
    put(chirp(1100 + 600 * rng.random(), .06), tc, .18); tc += 1 / r; r = min(r * 1.12, 30)
tc = S.T_LOG + .2                                   # printer chatter for the log paper
while tc < S.T_DD:
    t = tt(.03); put(lp(rng.normal(0, 1, len(t)), 3) * np.exp(-120 * t), tc, .18); tc += .07
for st, g in ((S.T_DD, .8), (S.T_IGN, .55)):        # stamps: low thump + paper slap
    t = tt(.3); put(np.sin(2 * np.pi * 90 * t) * np.exp(-18 * t) + lp(rng.normal(0, 1, len(t)), 4) * np.exp(-40 * t) * .5, st + .02, g)
put(chirp(700, .1), S.T_ECHO, .15)                  # tiny echo "...out" chirp
sf.write('sfx.wav', np.stack([out, out], 1), SR)
print('dd', round(S.T_DD, 2), 'ign', round(S.T_IGN, 2))
