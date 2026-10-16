"""VOICE CLONE SFX, synthesized with numpy (no copyrighted audio). Cue times come from voiceclone.py."""
import sys; sys.argv = ['voiceclone.py']
import numpy as np, soundfile as sf
import voiceclone as S
SR = 48000; N = int((S.TOTAL + .5) * SR); out = np.zeros(N, np.float32); HOLD = S.HOLD; rng = np.random.default_rng(16)
def put(sig, t, g=1.0):
    i = int((t + HOLD) * SR); j = min(N, i + len(sig))
    if i < N: out[i:j] += g * np.asarray(sig, np.float32)[:j - i]
def tt(d): return np.arange(int(d * SR)) / SR
def lp(x, n=8): return np.convolve(x, np.ones(n) / n, 'same')
# UPLOAD 100% stamp: low thump + paper slap
t = tt(.3); put(np.sin(2 * np.pi * 90 * t) * np.exp(-18 * t) + lp(rng.normal(0, 1, len(t)), 4) * np.exp(-40 * t) * .5, S.T_STAMP, .8)
# beard *fizz*: short crackle
t = tt(.45); put((rng.random(len(t)) < .05) * rng.normal(0, 1, len(t)) * np.exp(-5 * t) * .6, S.T_COPY, .7)
# counter: rising pop per change (pitch climbs with the count)
for k, tc in enumerate([S.T_COPY, S.T_C4, S.T_C9, S.T_C37]):
    t = tt(.14); f = 700 + 300 * k + 900 * t / .14
    put(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-25 * t), tc + .02, .5)
# clones gliding in on swivel chairs: soft castor rumble + zip per wave
for tc, n in ((S.T_C4, 2), (S.T_C9, 7), (S.T_C37, 9)):
    t = tt(.5); r = lp(rng.normal(0, 1, len(t)), 30) * np.sin(np.pi * t / .5) * (.6 + .1 * n)
    z = np.sin(2 * np.pi * (1500 - 900 * t) * t) * np.exp(-6 * t) * .12
    put(r * .9 + z, tc, .6)
# chair flip: big whoosh (band-swept noise) + squeak
t = tt(.55); n = rng.normal(0, 1, len(t)); env = np.sin(np.pi * np.clip(t / .55, 0, 1)) ** 2
put((lp(n, 6) - lp(n, 40)) * env * 1.2, S.T_FLIP - .05, 1.0)
t = tt(.12); put(np.sin(2 * np.pi * (2400 + 600 * t / .12) * t) * np.exp(-20 * t) * .25, S.T_FLIP + .22, 1.0)
# facepalm SMACK: flesh slap
t = tt(.18); put(lp(rng.normal(0, 1, len(t)), 3) * np.exp(-45 * t) + .5 * np.sin(2 * np.pi * 180 * t) * np.exp(-30 * t), S.T_FP, .9)
sf.write('sfx.wav', np.stack([out, out], 1), SR)
print('stamp', round(S.T_STAMP, 2), 'copy', round(S.T_COPY, 2), 'flip', round(S.T_FLIP, 2), 'fp', round(S.T_FP, 2))
