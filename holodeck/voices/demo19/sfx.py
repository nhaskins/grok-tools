"""WARP NINE RENDER SFX, synthesized with numpy (no copyrighted audio). Cue times come from warpnine.py."""
import sys; sys.argv = ['warpnine.py']
import numpy as np, soundfile as sf
import warpnine as S
SR = 48000; N = int((S.TOTAL + .5) * SR); out = np.zeros(N, np.float32); HOLD = S.HOLD; rng = np.random.default_rng(19)
def put(sig, t, g=1.0):
    i = int((t + HOLD) * SR); j = min(N, i + len(sig))
    if 0 <= i < N: out[i:j] += g * np.asarray(sig, np.float32)[:j - i]
def tt(d): return np.arange(int(d * SR)) / SR
def lp(x, n=8): return np.convolve(x, np.ones(n) / n, 'same')
def fsweep(f, t):   # phase-accumulated tone from a per-sample frequency curve
    return np.sin(2 * np.pi * np.cumsum(f) / SR)
# engine hum rise: from the climb to the blip, 45 -> 140 Hz, gain rising
d = S.T_BLIP - S.T_CLIMB; t = tt(d); u = t / d
f = 45 + 95 * np.clip((t - (S.T_757 - S.T_CLIMB) * .5) / d * 1.6, 0, 1) ** 1.3
hum = (fsweep(f, t) + .4 * fsweep(2 * f, t) + .15 * fsweep(3.01 * f, t)) * (.25 + .75 * u) * np.minimum(1, t / .5)
put(hum, S.T_CLIMB, .16)
# warp kick at "seven": low whoosh
t = tt(1.0); put(lp(rng.normal(0, 1, len(t)), 30) * np.exp(-3 * t) * np.minimum(1, t / .05), S.T_757, .5)
# after reboot: hum returns, then settles at the "nice" drop
d = S.T_NICE + .8 - S.T_ON; t = tt(d); f = np.where(t < d - .8, 110, 110 - 60 * np.clip((t - (d - .8)) / .6, 0, 1))
put(fsweep(f, t) * np.minimum(1, t / .6) * np.clip((d - t) / .3, 0, 1), S.T_ON, .07)
# blip zap
t = tt(.18); put(np.sign(np.sin(2 * np.pi * (2200 - 9000 * t) * t)) * np.exp(-14 * t) * .6 + rng.normal(0, 1, len(t)) * np.exp(-30 * t) * .4, S.T_BLIP, .35)
# rumble during the shake
d = S.T_BLK - S.T_BLIP + .1; t = tt(d); put(lp(rng.normal(0, 1, len(t)), 60) * 6 * np.sin(np.pi * t / d) ** .5, S.T_BLIP, .45)
# power-down whine: 1400 -> 60 Hz over the blackout
d = S.T_REB - S.T_BLK; t = tt(d); f = 1400 * (60 / 1400) ** (t / d)
put(fsweep(f, t) * np.exp(-1.2 * t / d) * np.minimum(1, t / .02), S.T_BLK, .22)
# light-bank clunks + power-up chime
for k in range(4): t = tt(.12); put(np.sin(2 * np.pi * 120 * t) * np.exp(-30 * t) + lp(rng.normal(0, 1, len(t)), 3) * np.exp(-60 * t) * .3, S.T_REB + .05 + .22 * k, .35)
for j, fr in enumerate((660, 880, 1320)):
    t = tt(.9); put((np.sin(2 * np.pi * fr * t) + .3 * np.sin(4 * np.pi * fr * t)) * np.exp(-4 * t), S.T_ON + .12 * j, .18)
# Riker plops onto the chair + nice-drop stamp thump
for st, g in ((S.T_SIT, .55), (S.T_NICE, .4)):
    t = tt(.3); put(np.sin(2 * np.pi * 90 * t) * np.exp(-18 * t) + lp(rng.normal(0, 1, len(t)), 4) * np.exp(-40 * t) * .5, st + .02, g)
sf.write('sfx.wav', np.stack([out, out], 1), SR)
print('peak', float(np.abs(out).max()))
