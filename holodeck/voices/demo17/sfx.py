"""WRONG MONITOR SFX, synthesized with numpy (no copyrighted audio). Cue times come from wrongmonitor.py."""
import sys; sys.argv = ['wrongmonitor.py']
import numpy as np, soundfile as sf
import wrongmonitor as S
SR = 48000; N = int((S.TOTAL + .5) * SR); out = np.zeros(N, np.float32); HOLD = S.HOLD; rng = np.random.default_rng(17)
def put(sig, t, g=1.0):
    i = int((t + HOLD) * SR); j = min(N, i + len(sig))
    if i < N: out[i:j] += g * np.asarray(sig, np.float32)[:j - i]
def tt(d): return np.arange(int(d * SR)) / SR
def lp(x, n=8): return np.convolve(x, np.ones(n) / n, 'same')
def shimmer(d, up=True):   # transporter: tremolo chord of high partials + airy noise (as demo4)
    t = tt(d); env = np.sin(np.pi * t / d)
    ch = sum(a * np.sin(2 * np.pi * f * (1 + (.25 if up else -.15) * t / d) * t + k) for k, (a, f) in enumerate([(.16, 2093), (.14, 2637), (.12, 3136), (.1, 3951)]))
    n = rng.normal(0, 1, len(t)); n = n - lp(n, 12)
    return (ch * (.55 + .45 * np.sin(2 * np.pi * 17 * t)) + .12 * n) * env
put(shimmer(.75, False), S.T_BEAM, .7)                      # beam into the desktop
put(shimmer(.6, False), S.T_OUT, .55)                       # mini Grok Bot beams out of the desktop
put(shimmer(.6, True), S.T_BACK, .6)                        # ...and back onto the bridge
# inventory ticks: 3 monitors / 2 drivers / 1 pen
for tc in (S.T_N3, S.T_N2, S.T_N1):
    t = tt(.08); put(np.sin(2 * np.pi * 1600 * t) * np.exp(-50 * t), tc, .3)
# starship lands sideways: comedy "boing" down-sweep
t = tt(.35); put(np.sin(2 * np.pi * np.cumsum(500 - 900 * t) / SR * 1) * np.exp(-6 * t) * .5, S.T_SHIP + .15, .6)
# lag counter pops (pitch climbs) + stutter clicks that get denser
for k, tc in enumerate((S.T_L1, S.T_L12, S.T_L99)):
    t = tt(.14); f = 700 + 400 * k + 900 * t / .14
    put(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-25 * t), tc + .02, .5)
tc = S.T_WATCH + .3
while tc < S.T_REV - .1:
    rate = 3 if tc < S.T_L1 else 6 if tc < S.T_L12 else 10 if tc < S.T_L99 else 16
    t = tt(.02); put(lp(rng.normal(0, 1, len(t)), 2) * np.exp(-200 * t) * .35, tc, .5); tc += 1 / rate
# FIXPEN stamp: low thump + paper slap
t = tt(.3); put(np.sin(2 * np.pi * 90 * t) * np.exp(-18 * t) + lp(rng.normal(0, 1, len(t)), 4) * np.exp(-40 * t) * .5, S.T_FIX + .02, .8)
# clean pen stroke: soft felt-tip scratch
t = tt(1.3); n = rng.normal(0, 1, len(t)); put((n - lp(n, 6)) * .05 * np.sin(np.pi * t / 1.3), S.T_FIX + .1, 1.0)
sf.write('sfx.wav', np.stack([out, out], 1), SR)
print('beam', round(S.T_BEAM, 2), 'fix', round(S.T_FIX, 2), 'out', round(S.T_OUT, 2))
