"""THE STANDUP SFX, synthesized with numpy (no copyrighted audio). Uses the episode's own cue functions."""
import sys; sys.argv = ['standup.py']
import numpy as np, soundfile as sf, math
import standup as S
SR = 48000; N = int((S.TOTAL + .5) * SR); out = np.zeros(N, np.float32); HOLD = S.HOLD
def put(sig, t, g=1.0):
    i = int((t + HOLD) * SR); j = min(N, i + len(sig))
    if i < N: out[i:j] += g * sig[:j - i]
def tt(d): return np.arange(int(d * SR)) / SR
def tick(f=2200):
    t = tt(.05); return (np.sin(2 * np.pi * f * t) * np.exp(-90 * t) + .5 * np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-120 * t)).astype(np.float32)
rng = np.random.default_rng(3)
# real-time ticks, then ticks that follow the minute hand until they blur into a whirr
last = -1; t = 0.25; whirr_from = None
while t < S.T_BOING:
    m = int(S.elapsed(t))
    if m != last:
        if S.rate(t) > 9:                                       # > 9 ticks/s (1 tick per clock minute): switch to whirr
            whirr_from = t; break
        put(tick(2200 if m % 2 else 1900), t, 1.0); last = m
    t += 1 / 480
if whirr_from:
    d = S.T_BOING - whirr_from; ts = tt(d); tg = whirr_from + ts
    rt = np.array([S.rate(x) for x in np.linspace(whirr_from, S.T_BOING, 200)])
    f = np.interp(ts, np.linspace(0, d, 200), 9 + 30 * np.log10(np.maximum(rt, 1) / 9 + 1))   # tick-rate Hz, rising
    ph = 2 * np.pi * np.cumsum(f) / SR
    clicks = np.maximum(np.sin(ph), 0) ** 30                       # click train at the rising rate
    noise = rng.normal(0, 1, len(ts)).astype(np.float32)
    car = np.sin(2 * np.pi * 2000 * ts)
    w = (clicks * car * .45 + .04 * noise * (np.sin(ph * .5) * .5 + .5)).astype(np.float32)
    env = np.minimum(1, ts / .4) * np.minimum(1, (d - ts) / .05)
    duck = np.where((tg >= S.T_PI) & (tg < S.CUT_P2), .45, 1.0)  # quieter under the punch-in
    put((w * env * duck).astype(np.float32), whirr_from, 2.0)
# calendar pages flutter (soft paper swishes) while they fly
for k in range(14):
    t0 = S.T_LAPSE + 3.0 + k * .55
    if t0 > S.T_PI + 3.5: break
    d = .18; ts = tt(d); n = rng.normal(0, 1, len(ts)) * np.sin(np.pi * ts / d) ** 2
    n = np.convolve(n, np.ones(6) / 6, 'same') - np.convolve(n, np.ones(60) / 60, 'same')
    put(n.astype(np.float32), t0, .12)
# bird chirp
for k, d0 in enumerate((0, .16)):
    ts = tt(.11); f = 2600 + 1800 * ts / .11
    put((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * ts / .11)).astype(np.float32), S.T_BIRD + .25 + d0, .35)
# BOING (spring): vibrato sine with decay
ts = tt(.9); f = 170 * (1 + .18 * np.sin(2 * np.pi * 11 * ts) * np.exp(-2 * ts)) + 40 * np.exp(-6 * ts)
put((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-3.2 * ts) * .9 + .3 * np.sin(4 * np.pi * np.cumsum(f) / SR) * np.exp(-5 * ts)).astype(np.float32), S.T_BOING, .7)
# faint THUD
ts = tt(.35); f = 70 - 25 * ts / .35
th = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-11 * ts) + rng.normal(0, 1, len(ts)) * np.exp(-60 * ts) * .25
put(th.astype(np.float32), S.T_FAINT + .2, 1.0)
# stamp thump
ts = tt(.25); put((np.sin(2 * np.pi * 95 * ts) * np.exp(-18 * ts) + rng.normal(0, 1, len(ts)) * np.exp(-50 * ts) * .3).astype(np.float32), S.T_STAMP + .08, .8)
sf.write('sfx.wav', np.stack([out, out], 1), SR)
print('whirr from', round(whirr_from or -1, 2), 'boing', round(S.T_BOING, 2), 'faint', round(S.T_FAINT, 2), 'stamp', round(S.T_STAMP, 2))
