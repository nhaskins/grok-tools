"""DARK MODE SFX, synthesized with numpy (no copyrighted audio). Cue times come from darkmode.py."""
import sys; sys.argv = ['darkmode.py']
import numpy as np, soundfile as sf
import darkmode as S
SR = 48000; N = int((S.TOTAL + .5) * SR); out = np.zeros(N, np.float32); HOLD = S.HOLD; rng = np.random.default_rng(5)
def put(sig, t, g=1.0):
    i = int((t + HOLD) * SR); j = min(N, i + len(sig))
    if i < N: out[i:j] += g * np.asarray(sig, np.float32)[:j - i]
def tt(d): return np.arange(int(d * SR)) / SR
def click():
    t = tt(.06); return np.sin(2 * np.pi * 2600 * t) * np.exp(-140 * t) + rng.normal(0, 1, len(t)) * np.exp(-200 * t) * .6 + .5 * np.sin(2 * np.pi * 900 * t) * np.exp(-90 * t)
put(click(), S.T_DARK - .04, .9); put(click(), S.T_LIGHT - .04, .9)
# fluorescent flicker buzz on the way into the dark (120 Hz buzz, gated by the flicker)
t = tt(.3); bz = np.sign(np.sin(2 * np.pi * 120 * t)) * .3 * np.exp(-6 * t)
gate = np.ones_like(t); gate[(t >= .08) & (t < .14)] = 0; gate[(t >= .2) & (t < .24)] = 0
put(bz * gate, S.T_DARK, .5)
# BONK: hollow knock + short pitch drop
t = tt(.35); f = 420 * np.exp(-3 * t); put(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-14 * t) + .4 * np.sin(2 * np.pi * 1300 * t) * np.exp(-40 * t), S.T_BONK, 1.0)
# alt-text labels: a little pop per label
for j in range(6):
    t = tt(.12); f = 600 + 900 * j / 5 + 500 * t / .12
    put(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-30 * t), S.T_ALT + j * .2 + .02, .55)
# flashbang: bright noise whoosh + high sine "fwee" + sizzle tail
t = tt(1.0); n = rng.normal(0, 1, len(t))
hp = n - np.convolve(n, np.ones(8) / 8, 'same')
put(hp * np.exp(-4 * t) * .5 + np.sin(2 * np.pi * (3200 - 1200 * t) * t) * np.exp(-5 * t) * .25, S.T_LIGHT, 1.0)
t = tt(.7); put((rng.random(len(t)) < .03) * rng.normal(0, 1, len(t)) * np.exp(-3 * t) * .9 + hp[:len(t)] * .12 * np.exp(-5 * t), S.T_LIGHT + .08, .8)
# shades "ting"
t = tt(.6); put(np.sin(2 * np.pi * 2637 * t) * np.exp(-7 * t) * .5 + np.sin(2 * np.pi * 3951 * t) * np.exp(-9 * t) * .3, S.T_SHADES + .15, .7)
sf.write('sfx.wav', np.stack([out, out], 1), SR)
print('dark', round(S.T_DARK, 2), 'bonk', round(S.T_BONK, 2), 'alt', round(S.T_ALT, 2), 'light', round(S.T_LIGHT, 2), 'shades', round(S.T_SHADES, 2))
