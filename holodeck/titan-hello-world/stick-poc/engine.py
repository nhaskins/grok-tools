"""Data-driven stick-figure section renderer.

    python engine.py cues/chorus1.py                 # full render (video + captions + audio)
    python engine.py cues/chorus1.py --frames 80 83  # raw PNG frames (no captions) to check

A cue file is a plain Python module defining CUES (see cues/chorus1.py). It names the
segment, the people, and a list of shots (set, camera keys, cast + pose keys, beat mods),
plus transitions, named event times for gags, and caption styles. Times anywhere can be:
    82.5            absolute song seconds
    'w:grin'        sung time of a word (first occurrence inside the segment)
    'w:titan#1'     second occurrence;  'w:grin-0.15'  with an offset
    'b:82.5'        nearest bar downbeat (bars.npy);  'b:82.5+0.2'
Set pieces (backgrounds, gags) live in sets.py and read their timings from CUES['events'].
"""
import sys, os, re, math, json, time, subprocess, importlib.util
import numpy as np, cv2
cv2.setNumThreads(1)
from stickfig import *
from inkset import W, H, paper_finish

HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE)
BEATS = np.load(f'{PROJ}/beats.npy'); BARS = np.load(f'{PROJ}/bars.npy')
LY = json.load(open(f'{PROJ}/lyric-timing.json'))
FPS, BOIL_FPS = 24, 12


def since(arr, t):
    p = arr[arr <= t]; return t - p[-1] if len(p) else 9.0


class Ctx:
    """Per-render context handed to set pieces: time resolver, events, cast, hands."""
    def __init__(self, cues):
        self.cues = cues; self.t0, self.t1 = cues['segment']['t0'], cues['segment']['t1']
        self._ev = {}

    def norm(self, w): return re.sub(r"[^a-z0-9']", '', w.lower())

    def T(self, spec):
        if isinstance(spec, (int, float)): return float(spec)
        offs = lambda g: sum(float(x) for x in re.findall(r'[+-]\d*\.?\d+', g or ''))
        m = re.match(r'^([a-z_][a-z0-9_]*)((?:[+-]\d*\.?\d+)*)$', spec.strip())
        if m and m.group(1) in self.cues.get('events', {}):     # a named event, optionally offset ('reveal+0.35')
            return self.T(self.cues['events'][m.group(1)]) + offs(m.group(2))
        m = re.match(r'^(w|b):(.+?)(?:#(\d+))?((?:[+-]\d*\.?\d+)*)$', spec.strip())
        if not m: raise ValueError(f'bad time spec {spec!r}')
        kind, key, nth, off = m.group(1), m.group(2), int(m.group(3) or 0), offs(m.group(4))
        if kind == 'b':
            return float(BARS[np.argmin(abs(BARS - float(key)))]) + off
        hits = [x['s'] for l in LY for x in l['words']
                if self.norm(x['w']) == self.norm(key) and self.t0 - 1 <= x['s'] < self.t1 + 2]
        if len(hits) <= nth: raise ValueError(f'word {key!r} #{nth} not sung in segment')
        return hits[nth] + off

    def ev(self, name):
        sh = getattr(self, 'shot', None)
        if isinstance(name, (int, float)): return float(name)
        if sh is not None and '_ev' in sh: return sh['_ev'][name]
        if name not in self._ev: self._ev[name] = self.T(self.cues['events'][name])
        return self._ev[name]

    def opt(self, key, default=None):
        return self.shot.get('opt', {}).get(key, default)


def build(cues, ctx):
    """Resolve shots: absolute times, camera keys, Figures with keys/moves/mods."""
    people = cues['people']; shots = []
    for i, s in enumerate(cues['shots']):
        sh = dict(s); sh['t'] = ctx.T(s['at'])
        evs = dict(cues.get('events', {})); evs.update(s.get('events', {}))
        sh['_ev'] = {k: ctx.T(v) for k, v in evs.items()}
        sh['_jump'] = ctx.T(s['jump']) if s.get('jump') is not None else None
        def res(v):     # resolve 'w:'/'b:' time specs inside opt (section-local word lookup)
            if isinstance(v, str) and re.match(r'^(w|b):', v): return ctx.T(v)
            if isinstance(v, dict): return {k: res(x) for k, x in v.items()}
            if isinstance(v, (list, tuple)): return type(v)(res(x) for x in v)
            return v
        sh['opt'] = res(s.get('opt', {}))
        sh['cam'] = [(ctx.T(c[0]), c[1], c[2] if len(c) > 2 else 0.5) for c in s['cam']]
        figs = {}
        for c in s.get('cast', []):
            p = dict(people[c['who']]); p.update({k: v for k, v in c.items() if k in ('props', 'scale', 'col', 'back')})
            F = Figure(c.get('id', c['who']), c['x'], c['y'], c.get('facing', 1), set(p.get('props', ())),
                       back=p.get('back', False), col=INK if p.get('col', 'ink') == 'ink' else PAPER, scale=p.get('scale', 1.0))
            F.key(-1e8, c.get('pose', 'stand'), 0)
            for k in c.get('keys', []): F.key(ctx.T(k[0]), k[1], k[2] if len(k) > 2 else 0.25)
            for m in c.get('moves', []): F.move(ctx.T(m[0]), m[1], m[2], m[3] if len(m) > 3 else 0.4)
            if c.get('mod'): F.mod = make_mod(c['mod'], ctx)
            F.layer = c.get('layer', 'main'); F.nojump = c.get('nojump', False); F.halo_w = c.get('halo', None)
            figs[F.name] = F
        sh['figs'] = figs
        shots.append(sh)
    for i, sh in enumerate(shots): sh['end'] = shots[i + 1]['t'] if i + 1 < len(shots) else ctx.t1 + 1
    for tr in cues.get('transitions', []): tr['_t'] = ctx.T(tr['at'])
    return shots


def beat_phase(t):
    """(index of current beat, 0..1 phase within it)"""
    i = int(np.searchsorted(BEATS, t, side='right') - 1)
    if i < 0 or i + 1 >= len(BEATS): return max(i, 0), 0.0
    return i, (t - BEATS[i]) / (BEATS[i + 1] - BEATS[i])


def make_mod(spec, ctx):
    """Beat-synced pose overrides. spec = (name, start, [end], {params})."""
    name, start = spec[0], ctx.T(spec[1])
    end = ctx.T(spec[2]) if len(spec) > 2 and not isinstance(spec[2], dict) else 1e9
    prm = dict(spec[-1]) if isinstance(spec[-1], dict) else {}
    soft_from = ctx.T(prm.get('soft_from', 1e9))
    if name == 'pull':        # yank back on every beat
        def f(t, P):
            if start <= t < end:
                d = since(BEATS, t); k = math.exp(-d * 7) if d < 1 else 0
                P['lean'] -= 16 * k; P['lsh'] -= 10 * k; P['rsh'] -= 10 * k; P['lhip'] += 8 * k
            return P
    elif name == 'kick':      # can-can: alternate legs each beat, all in sync
        amp = prm.get('amp', 70)
        def f(t, P):
            if start <= t < end:
                i, ph = beat_phase(t); k = math.sin(math.pi * min(ph * 1.6, 1.0))
                a = amp * (prm.get('soft', 1.0) if t > soft_from else 1.0)
                leg = 'lhip' if i % 2 else 'rhip'; P[leg] += a * k; P[leg[0] + 'kn'] = -10 * (1 - k)
            return P
    elif name == 'bop':       # head-bop + arm pump on beats
        def f(t, P):
            if start <= t < end:
                d = since(BEATS, t); k = math.exp(-d * 8)
                P['tilt'] += 10 * k; P['rsh'] += prm.get('pump', 0) * k; P['lsh'] += prm.get('pump', 0) * k
            return P
    elif name == 'walk':      # leg swing + arm swing while walking (between start and end)
        rate = prm.get('rate', 2.2)
        def f(t, P):
            if start <= t < end:
                ph = math.sin(2 * math.pi * rate * (t - start)); k = min(1, (t - start) / .15, (end - t) / .15)
                P['lhip'] += 26 * ph * k; P['rhip'] -= 26 * ph * k; P['lkn'] -= 14 * max(ph, 0) * k; P['rkn'] -= 14 * max(-ph, 0) * k
                P['lsh'] -= 22 * ph * k; P['rsh'] += 22 * ph * k
            return P
    elif name == 'slide':     # trombone slide in and out on the beat
        def f(t, P):
            if start <= t < end:
                i, ph = beat_phase(t); k = 0.5 - 0.5 * math.cos(2 * math.pi * ph)
                P['rel'] = 70 * k; P['rsh'] = 90 - 25 * k
            return P
    elif name == 'robotdance':   # snap between arm poses on every beat
        moves = [(90, 90, 90, -90), (150, 30, 30, 150), (90, -90, 90, 90), (30, 150, 150, 30), (170, 0, 10, 0), (10, 0, 170, 0)]
        def f(t, P):
            if start <= t < end:
                i, ph = beat_phase(t); a = moves[i % len(moves)]; b = moves[(i + 1) % len(moves)]
                k = ease(clamp01((ph - 0.75) / 0.25))
                P['lsh'] = lerp(a[0], b[0], k); P['lel'] = lerp(a[1], b[1], k); P['rsh'] = lerp(a[2], b[2], k); P['rel'] = lerp(a[3], b[3], k)
                P['tilt'] += 8 * math.sin(math.pi * i)
            return P
    else:
        raise ValueError(name)
    return f


def cam_at(sh, t):
    keys = sh['cam']; cam = keys[0][1]
    for i, (tk, c, dur) in enumerate(keys):
        if t < tk: break
        prev = cam if i else c
        k = ease((t - tk) / dur) if dur > 0 else 1.0
        cam = tuple(lerp(a, b, k) for a, b in zip(prev, c))
    return cam


# ------------------------------------------------------------------ transitions
def splat_poly(cx, cy, R, seed, n=200):
    r = np.random.default_rng(seed); ph = r.uniform(0, 6.28, 6); amp = r.uniform(0.04, 0.12, 6)
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rad = R * (1 + sum(amp[k] * np.sin((k + 3) * a + ph[k]) for k in range(6)))
    return np.stack([cx + rad * np.cos(a), cy + rad * np.sin(a)], 1)


def apply_transition(img, t, tr, ctx):
    cut = tr['_t'] if '_t' in tr else ctx.T(tr['at']); pre, post = tr.get('pre', 0.2), tr.get('post', 0.3)
    if not (cut - pre <= t < cut + post) and not (tr.get('hold') and t >= cut): return img
    post = max(post, 1e-3)
    kind = tr['kind']; seed = tr.get('seed', 4); cx, cy = tr.get('c', (W / 2, H / 2))
    ink = np.array(INK, np.uint8)
    if kind == 'splat':
        if t < cut:     # ink blot grows over the outgoing shot, with flying droplets
            u = ease_out((t - (cut - pre)) / pre); R = 60 + u * 1350
            cv2.fillPoly(img, [np.round(splat_poly(cx, cy, R, seed) * 16).astype(np.int32)], INK, cv2.LINE_AA, shift=4)
            r = np.random.default_rng(seed + 1)
            for i in range(26):
                a = r.uniform(0, 6.28); d = R * r.uniform(1.05, 1.6); s = r.uniform(6, 30) * (0.4 + u)
                cv2.circle(img, (int(cx + d * math.cos(a)), int(cy + d * math.sin(a))), int(s), INK, -1, cv2.LINE_AA)
        elif t < cut + post or tr.get('hold'):
            if tr.get('hold'): return img if t < cut else np.full_like(img, INK)   # end card stays inked
            u = ease((t - cut) / post) ** 1.4; R = u * 1450
            m = np.zeros(img.shape[:2], np.uint8)
            if R > 5: cv2.fillPoly(m, [np.round(splat_poly(cx, cy, R, seed + 7) * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
            a = (m.astype(np.float32) / 255)[..., None]
            img = (img * a + ink * (1 - a)).astype(np.uint8)
    elif kind == 'wipe':  # dry-brush ink band sweeping left -> right
        yy = np.arange(H)
        r = np.random.default_rng(seed); ph = r.uniform(0, 6.28, 3)
        wob = 40 * np.sin(yy / 90 + ph[0]) + 18 * np.sin(yy / 23 + ph[1]) + 10 * np.sin(yy / 7 + ph[2])
        if t < cut:
            u = ease_out((t - (cut - pre)) / pre); edge = -250 + u * (W + 500) + wob
            xs = np.arange(W)[None, :]; m = xs < edge[:, None]
        else:
            u = ease((t - cut) / post); edge = -250 + u * (W + 500) + wob
            xs = np.arange(W)[None, :]; m = xs >= edge[:, None]
        # dry-brush gaps near the edge
        streak = (np.sin(yy / 3.1 + ph[1]) * np.sin(yy / 11.7 + ph[2]) > 0.55)[:, None] & (np.abs(xs - edge[:, None]) < 90)
        m = m & ~streak
        img = img.copy(); img[m] = ink
    return img


# ------------------------------------------------------------------ captions
def write_captions(cues, ctx, path):
    INKc, GREY, PAPERc = '&H00141618', '&H00A8A8A8', '&H00E6EEF3'
    def ts(x): x = max(x, 0); return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Lyric,Exo 2,66,{INKc},{GREY},{PAPERc},&H00000000,1,0,0,0,100,100,1,0,1,6,0,2,90,90,42,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    T0, T1 = ctx.t0, ctx.t1; styles = cues.get('captions', {}); keyw = set(cues.get('caption_keywords', []))
    ev = []
    for k, o in enumerate(LY):
        ws = o['words']; s0, e0 = ws[0]['s'], ws[-1]['e']
        if e0 < T0 or s0 > T1: continue
        nxt = LY[k + 1]['words'][0]['s'] if k + 1 < len(LY) else 999
        a = s0 - 0.3; b = min(e0 + 0.6, nxt - 0.3, T1 + 0.5); dur = int((b - a) * 1000)
        style = next((v for p, v in styles.items() if o['line'].startswith(p)), 'karaoke')
        pos = "\\pos(960,1038)"
        if style == 'karaoke':
            kt = [f"{{\\k{int((s0 - a) * 100)}}}"]
            for j, w in enumerate(ws):
                end = ws[j + 1]['s'] if j + 1 < len(ws) else w['e']; t0 = int((w['s'] - a) * 1000)
                pop = f"\\t({t0},{t0 + 90},\\fscy112)\\t({t0 + 90},{t0 + 260},\\fscy100)" if ctx.norm(w['w']) in keyw else ''
                kt.append(f"{{\\kf{max(int((end - w['s']) * 100), 1)}{pop}}}{w['w']}{'{\\fscy100}' if pop else ''} ")
            txt = f"{{\\fad(150,250)\\move(960,1052,960,1038,0,200)}}" + ''.join(kt).strip()
        else:
            parts = []
            for w in ws:   # words appear on their sung time; 'pop' also overshoots the scale
                t0 = int((w['s'] - a) * 1000)
                big = 128 if ctx.norm(w['w']) in keyw else 118
                sc = f"\\fscx{big}\\fscy{big}\\t({t0},{t0 + 220},\\fscx100\\fscy100)" if style == 'pop' else ''
                parts.append(f"{{\\alpha&HFF&{sc}\\t({t0},{t0 + 60},\\alpha&H00&)}}{w['w']}")
            body = ' '.join(parts); e1 = min(int((e0 - a) * 1000), dur - 350)
            if style == 'pop':
                txt = f"{{{pos}\\fad(0,120)}}" + body
            elif style == 'stretch':
                txt = f"{{{pos}\\fad(100,250)\\fscx80\\t(0,{e1},\\fscx112)\\t({e1},{dur},\\fscx260\\alpha&HFF&)}}" + body
            elif style == 'rise':
                txt = f"{{\\an2\\move(960,1038,960,960,{int((s0 - a) * 1000)},{dur})\\fad(100,350)\\t(0,{dur},\\fscx118\\fscy118)}}" + body
        ev.append(f"Dialogue: 1,{ts(a - T0)},{ts(b - T0)},Lyric,,0,0,0,,{txt}")
    open(path, 'w').write(hdr + '\n'.join(ev) + '\n')


# ------------------------------------------------------------------ render
VIG, GRAINS = paper_finish()

def render_frame(t, shots, ctx, sets):
    sh = next(s for s in shots if s['t'] <= t < s['end']) if t >= shots[0]['t'] else shots[0]
    img = np.full((H, W, 3), PAPER, np.uint8)
    boil = int(t * BOIL_FPS)
    cam = cam_at(sh, t)
    kick = 1 + sh.get('kick', 0.012) * math.exp(-since(BARS, t) * 6)
    cam = (cam[0], cam[1], cam[2] * kick)
    sk = sh.get('shake', 0) * math.exp(-(t - sh['t']) * 2.5) + sh.get('shake_beat', 0) * math.exp(-since(BEATS, t) * 10)
    if sk > 0.5:
        r = np.random.default_rng(int(t * FPS)); cam = (cam[0] + r.uniform(-sk, sk) / cam[2], cam[1] + r.uniform(-sk, sk) / cam[2], cam[2])
    bob = sh.get('bounce', 5) * math.exp(-since(BEATS, t) * 9)
    dB = since(BARS, t); jump = 0.0
    if sh.get('jump_every') == 'beat': dB = since(BEATS, t)
    jl = 0.3 if sh.get('jump_every') == 'beat' else 0.38
    if sh.get('_jump') is not None and dB < jl and sh['_jump'] <= t:
        u = dB / jl; jump = -sh.get('jump_h', 70) * 4 * u * (1 - u)
    pen = Pen(img, cam, boil)
    S = sets[sh['set']]
    ctx.t, ctx.shot, ctx.boil, ctx.pen, ctx.img, ctx.hands = t, sh, boil, pen, img, {}
    ctx.bob = bob; ctx.jump = jump; ctx.cam = cam
    if hasattr(S, 'bg'): S.bg(pen, t, ctx)
    for F in sh['figs'].values():
        if F.layer != 'main': continue
        seated = F.pos_at(t)[1] > 790 or getattr(F, 'nojump', False)
        ctx.hands[F.name] = F.draw(pen, t, bob + (0 if seated else jump), w=sh.get('stroke', 5.5) * F.scale ** .3,
                                   halo=F.halo_w if F.halo_w is not None else sh.get('halo', 0))
    if hasattr(S, 'fg'): S.fg(pen, t, ctx)
    for tr in ctx.cues.get('transitions', []):
        ctx.img = img = apply_transition(img, t, tr, ctx)
    return img


def finish(img, t, ctx):
    f = img.astype(np.float32) * VIG + GRAINS[int(t * BOIL_FPS) % 4]
    fin = clamp01((t - ctx.t0) / 0.3); fout = clamp01((ctx.t1 - t) / 0.3)
    endcol = np.array(INK if ctx.cues['segment'].get('fade_out_to') == 'ink' else PAPER, np.float32)
    if fin < 1: f = f * fin + np.array(PAPER, np.float32) * (1 - fin)
    if fout < 1: f = f * fout + endcol * (1 - fout)
    return np.clip(f, 0, 255).astype(np.uint8)


def load_cues(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path); mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod); return mod


def build_song(song):
    """Build every section with its own Ctx (word lookups stay inside the section window), then merge."""
    shots, trs = [], []
    for name in song['sections']:
        cues = load_cues(f'{HERE}/cues/{name}.py').CUES
        c = Ctx(cues); sh = build(cues, c)
        for x in sh: x['section'] = name
        shots += sh; trs += cues.get('transitions', [])
    shots.sort(key=lambda x: x['t'])
    for i, sh in enumerate(shots): sh['end'] = shots[i + 1]['t'] if i + 1 < len(shots) else song['t1'] + 1
    gc = Ctx(dict(segment=dict(name=song['name'], t0=song['t0'], t1=song['t1'], fade_out_to='paper'),
                  transitions=trs, events={}, captions=song['captions'], caption_keywords=song['caption_keywords']))
    return gc, shots


def render_range(shots, ctx, sets, f0, f1, out):
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '11', '-tune', 'animation', '-pix_fmt', 'yuv420p', '-g', '48', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); st = time.time()
    for i in range(f0, f1):
        t = i / FPS
        p.stdin.write(finish(render_frame(t, shots, ctx, sets), t, ctx).tobytes())
        if (i - f0) % 120 == 0: print(f'[{os.path.basename(out)}] {i - f0}/{f1 - f0} {time.time() - st:.1f}s', flush=True)
    p.stdin.close(); p.wait()


def main_song(path):
    song = load_cues(path).SONG
    import sets as SETS
    sets = {name: getattr(SETS, name) for name in dir(SETS) if not name.startswith('_')}
    ctx, shots = build_song(song)
    NF = int(round(song['t1'] * FPS))
    if '--frames' in sys.argv:
        for a in sys.argv[sys.argv.index('--frames') + 1:]:
            t = float(a); cv2.imwrite(f"{HERE}/raw_full_{a}.png", finish(render_frame(t, shots, ctx, sets), t, ctx))
        return
    if '--shots' in sys.argv:
        for sh in shots: print(f"{sh['t']:8.2f} {sh['end']:8.2f}  {sh['section']:10s} {sh['set']}")
        return
    os.makedirs(f'{HERE}/parts', exist_ok=True)
    if '--part' in sys.argv:
        k, n = (int(x) for x in sys.argv[sys.argv.index('--part') + 1:][:2])
        f0, f1 = NF * k // n, NF * (k + 1) // n
        render_range(shots, ctx, sets, f0, f1, f'{HERE}/parts/part{k:02d}.mp4'); return
    n = int(os.environ.get('JOBS', 8)); st = time.time()
    ass = f"{HERE}/captions-{song['name']}.ass"; write_captions(ctx.cues, ctx, ass)
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    procs = [subprocess.Popen([sys.executable, __file__, path, '--part', str(k), str(n)], env=env) for k in range(n)]
    rc = [p.wait() for p in procs]
    if any(rc): sys.exit(f'part failed {rc}')
    t_frames = time.time() - st
    with open(f'{HERE}/parts/list.txt', 'w') as fl:
        for k in range(n): fl.write(f"file 'part{k:02d}.mp4'\n")
    out = f"{HERE}/{song['out']}"
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{HERE}/parts/list.txt',
                    '-i', f'{PROJ}/titan-bridge-theme-epic.mp3', '-vf', f'ass={ass}', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '256k', '-t', f"{song['t1']}", '-movflags', '+faststart', out], check=True)
    print(f'done {out}  frames {t_frames:.1f}s  total {time.time() - st:.1f}s', flush=True)


def main():
    cue_path = sys.argv[1]
    mod = load_cues(cue_path)
    if hasattr(mod, 'SONG'): return main_song(cue_path)
    cues = mod.CUES
    import sets as SETS
    sets = {name: getattr(SETS, name) for name in dir(SETS) if not name.startswith('_')}
    ctx = Ctx(cues); shots = build(cues, ctx)
    seg = cues['segment']; T0, T1 = seg['t0'], seg['t1']; dur = T1 - T0
    if '--frames' in sys.argv:
        for a in sys.argv[sys.argv.index('--frames') + 1:]:
            t = float(a); cv2.imwrite(f"{HERE}/raw_{seg['name']}_{a}.png", finish(render_frame(t, shots, ctx, sets), t, ctx))
        return
    ass = f"{HERE}/captions-{seg['name']}.ass"; write_captions(cues, ctx, ass)
    out = f"{HERE}/{seg['out']}"; N = int(round(dur * FPS))
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-ss', str(T0), '-t', str(dur), '-i', f'{PROJ}/titan-bridge-theme-epic.mp3',
           '-vf', f"ass={ass}", '-af', f'afade=t=in:d=0.3,afade=t=out:st={dur - 0.3}:d=0.3',
           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-tune', 'animation',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-t', str(dur), '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); st = time.time()
    for i in range(N):
        t = T0 + i / FPS
        p.stdin.write(finish(render_frame(t, shots, ctx, sets), t, ctx).tobytes())
        if i % 96 == 0: print(f'{i}/{N} {time.time() - st:.1f}s', flush=True)
    p.stdin.close(); p.wait(); print('done', out, f'{time.time() - st:.1f}s')


if __name__ == '__main__':
    main()
