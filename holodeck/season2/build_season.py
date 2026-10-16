"""Season Two compilation: intro (credited) + 2.5 s SEASON TWO card + 5 plain episodes (poster hold +1.2 s) + sting. Per-segment gain to -16 LUFS, limiter, AAC 48k stereo, 2-pass H.264 6.5 Mbps, faststart. nice -n 10, -threads 4."""
import subprocess, re, json, sys
V = '/workspace/holodeck/voices'; B = '/workspace/holodeck/brand'
EPS = [('demo16/voiceclone.mp4', 'Voice Clone'), ('demo17/wrongmonitor.mp4', 'Wrong Monitor'),
       ('demo18/hailingloop.mp4', 'Hailing Loop'), ('demo19/warpnine.mp4', 'Warp Nine Render'), ('demo20/processaudit.mp4', 'Process Audit')]
EXTRA = 1.2     # v2: freeze each episode's poster (frame 0) +1.2 s -> ~1.74 s hold; audio padded with silence
SEGS = [(f'{B}/starship-grokbot-intro.mp4', 'intro', 0)] + [('season-card.mp4', 'card', 0)] + \
       [(f'{V}/{f}', n, EXTRA) for f, n in EPS] + [('sting.mp4', 'sting', 0)]
def dur(f): return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))
def lufs(f, ss):
    o = subprocess.run(['ffmpeg', '-nostdin', '-nostats', '-ss', str(ss), '-i', f, '-map', '0:a:0', '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1])
args, fc, cat, chap, t = [], [], '', [], 0.0
for i, (f, n, ss) in enumerate(SEGS):
    d = dur(f) + ss
    g = 0.0 if n == 'card' else -16.0 - lufs(f, 0)
    args += ['-i', f]
    tp = f'tpad=start_mode=clone:start_duration={ss},' if ss else ''
    dl = f'adelay={int(ss * 1000)}:all=1,' if ss else ''
    fc.append(f'[{i}:v:0]{tp}setpts=PTS-STARTPTS,fps=24,scale=1920:1080,format=yuv420p,setsar=1[v{i}]')
    fc.append(f'[{i}:a:0]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={g:.2f}dB,asetpts=PTS-STARTPTS,'
              f'{dl}apad,atrim=0:{d:.4f}[a{i}]')
    cat += f'[v{i}][a{i}]'
    chap.append(dict(name=n, start=round(t, 3), dur=round(d, 3), gain=round(g, 2)))
    t += d
fc.append(f'{cat}concat=n={len(SEGS)}:v=1:a=1[vc][ac0]')
fc.append('[ac0]alimiter=limit=0.89:level=false[ac]')
json.dump(dict(total=t, segs=chap), open('chapters.json', 'w'), indent=1)
base = ['nice', '-n', '10', 'ffmpeg', '-nostdin', '-y', '-loglevel', 'error'] + args + ['-filter_complex', ';'.join(fc), '-map', '[vc]', '-map', '[ac]',
        '-c:v', 'libx264', '-preset', 'slow', '-b:v', '6500k', '-maxrate', '9000k', '-bufsize', '13000k', '-pix_fmt', 'yuv420p', '-r', '24', '-threads', '4']
subprocess.run(base + ['-pass', '1', '-passlogfile', '/tmp/s2pass', '-an', '-f', 'null', '/dev/null'], check=True)
subprocess.run(base + ['-pass', '2', '-passlogfile', '/tmp/s2pass', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
                       '-movflags', '+faststart', 'starship-grokbot-season2.mp4'], check=True)
print(json.dumps(chap, indent=0)); print('total', t)
