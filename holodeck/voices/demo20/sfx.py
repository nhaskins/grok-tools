"""PROCESS AUDIT SFX, synthesized with numpy (no copyrighted audio). Cue times come from processaudit.py."""
import sys; sys.argv = ['processaudit.py']
import numpy as np, soundfile as sf
import processaudit as S
SR = 48000; N = int((S.TOTAL + .5) * SR); out = np.zeros(N, np.float32); HOLD = S.HOLD; rng = np.random.default_rng(20)
def put(sig, t, g=1.0):
    i = int((t + HOLD) * SR); j = min(N, i + len(sig))
    if 0 <= i < N: out[i:j] += g * np.asarray(sig, np.float32)[:j - i]
def tt(d): return np.arange(int(d * SR)) / SR
def lp(x, n=8): return np.convolve(x, np.ones(n) / n, 'same')
def fsweep(f): return np.sin(2 * np.pi * np.cumsum(f) / SR)
def pop(t0, fr=900, g=.12):
    t = tt(.08); put(np.sin(2 * np.pi * fr * t) * np.exp(-50 * t), t0, g)
# NODE badge pop + node doodles popping in + HOST reveal
pop(S.T_TOP, 700, .2)
for j in range(24): pop(S.T_LOGS + .05 * j, 1200 + 30 * j, .05)
t = tt(.5); put(fsweep(np.linspace(300, 900, len(t))) * np.exp(-5 * t), S.T_HOST, .14)
# button SLAM: heavy thump + click
t = tt(.4); put(np.sin(2 * np.pi * 70 * t) * np.exp(-12 * t) + lp(rng.normal(0, 1, len(t)), 6) * np.exp(-35 * t) * .8, S.T_SLAM, .6)
t = tt(.03); put(rng.normal(0, 1, len(t)) * np.exp(-150 * t), S.T_SLAM - .01, .3)
# static: band-limited noise while the viewscreen is static, fading as it clears
d = S.T_CLR + .25 - S.T_STAT; t = tt(d); n = rng.normal(0, 1, len(t)); n = n - lp(n, 4)
put(n * np.minimum(1, t / .03) * np.clip((d - t) / .4, 0, 1) * (.8 + .2 * np.sin(2 * np.pi * 7 * t)), S.T_STAT, .1)
# power-down whine 1200 -> 50 Hz across the banks
d = S.BANKS[-1] + .5 - S.BANKS[0]; t = tt(d); f = 1200 * (50 / 1200) ** (t / d)
put(fsweep(f) * np.exp(-1.0 * t / d) * np.minimum(1, t / .02), S.BANKS[0], .2)
for b in S.BANKS: t = tt(.15); put(np.sin(2 * np.pi * 110 * t) * np.exp(-25 * t), b, .3)      # bank clunks
# domino clicks
for j in range(24):
    t = tt(.03); put(lp(rng.normal(0, 1, len(t)), 2) * np.exp(-120 * t), S.T_DOM + S.DOM_DT * j + .1, .25)
# CONNECTION LOST stamp thump
t = tt(.3); put(np.sin(2 * np.pi * 90 * t) * np.exp(-18 * t) + lp(rng.normal(0, 1, len(t)), 4) * np.exp(-40 * t) * .5, S.T_LOST + .02, .4)
# DELETE & RECREATE: transporter shimmer out + in (high sparkly chirps)
for a, b in ((S.T_DEL0, S.T_DEL1), (S.T_IN0, S.T_IN1)):
    d = b - a + .2; t = tt(d); env = np.sin(np.pi * t / d)
    sh = sum(np.sin(2 * np.pi * (2400 + 300 * k) * t + 4 * np.sin(2 * np.pi * (6 + k) * t)) for k in range(4)) / 4
    put(sh * env * (.6 + .4 * np.sin(2 * np.pi * 30 * t)), a, .1)
# gen counter tick
pop(S.T_GEN + .15, 1500, .15)
# reboot: clunk + 3-note chime
t = tt(.12); put(np.sin(2 * np.pi * 120 * t) * np.exp(-30 * t), S.T_ON, .35)
for j, fr in enumerate((660, 880, 1320)):
    t = tt(.9); put((np.sin(2 * np.pi * fr * t) + .3 * np.sin(4 * np.pi * fr * t)) * np.exp(-4 * t), S.T_ON + .05 + .12 * j, .18)
sf.write('sfx.wav', np.stack([out, out], 1), SR)
print('peak', float(np.abs(out).max()))
