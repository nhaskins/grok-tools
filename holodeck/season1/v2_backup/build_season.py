"""Season compilation v2 (poster holds frozen +1.2 s; 2.5 s card; Red Shirts v2, Rate Limited v3).
v1 doc: intro (1 s) + season card (1.5 s) + 12 plain episodes (each trimmed 0.2 s -> 0.3 s poster hold)
+ sting (3 s). Per-segment linear gain to -16 LUFS (measured), limiter, 48 kHz stereo AAC, 2-pass H.264 ~6.5 Mbps, faststart."""
import subprocess, re, json, sys
V = '/workspace/holodeck/voices'; B = '/workspace/holodeck/brand'
EPS = [('demo1/riker-grokbot-dailylog-v2.mp4', 'The Daily Log'), ('demo2/webhook-picard.mp4', 'The Webhook'),
       ('demo3/barclay-episode.mp4', 'Holodeck Program 01'), ('demo4/redshirts-v2.mp4', 'The Red Shirts'),
       ('demo5/mergeconflict.mp4', 'Merge Conflict'), ('demo6/shipitfriday.mp4', 'Ship It Friday'),
       ('demo7/promptinjection.mp4', 'Prompt Injection'), ('demo8/hallucination.mp4', 'Hallucination'),
       ('demo9/technicaldebt.mp4', 'Technical Debt'), ('demo10/captcha.mp4', 'CAPTCHA'),
       ('demo11/contextwindow-v2.mp4', 'Context Window'), ('demo12/ratelimited-v3.mp4', 'Rate Limited')]
EXTRA = 1.2     # v2: freeze each episode's poster (frame 0) +1.2 s -> ~1.74 s hold; audio padded with silence
SEGS = [(f'{B}/starship-grokbot-intro.mp4', 'intro', 0)] + [('season-card.mp4', 'card', 0)] + \
       [(f'{V}/{f}', n, EXTRA) for f, n in EPS] + [(f'{B}/starship-grokbot-sting.mp4', 'sting', 0)]
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
base = ['ffmpeg', '-nostdin', '-y', '-loglevel', 'error'] + args + ['-filter_complex', ';'.join(fc), '-map', '[vc]', '-map', '[ac]',
        '-c:v', 'libx264', '-preset', 'slow', '-b:v', '6500k', '-maxrate', '9000k', '-bufsize', '13000k', '-pix_fmt', 'yuv420p', '-r', '24']
subprocess.run(base + ['-pass', '1', '-passlogfile', '/tmp/s1pass', '-an', '-f', 'null', '/dev/null'], check=True)
subprocess.run(base + ['-pass', '2', '-passlogfile', '/tmp/s1pass', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
                       '-movflags', '+faststart', 'starship-grokbot-season1-v2.mp4'], check=True)
print(json.dumps(chap, indent=0)); print('total', t)
