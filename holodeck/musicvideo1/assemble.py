import json, subprocess, os
from PIL import Image, ImageDraw, ImageFont
A = json.load(open('analysis.json')); B = A['bars']; D = A['duration']
b = lambda i: round(B[i], 2)
# (bar_start, section, camera, action, text, sync)
S = [
 (None, 'Intro', 'Locked wide, slow L->R starfield drift + 2% push', 'Ink stars on paper, a few twinkle', '-', 'Cold open; first twinkle on hit 1.37 s'),
 (2, 'Intro/A', 'Slow pan right past ringed planet', 'Ringed planet rolls through frame', '-', 'Cut on bar 3 downbeat, right after the 3.99 s swell; ring catches the 5.39 s hit'),
 (6, 'A', 'Static wide, ship tiny lower-left, drifts up-right', 'Starship Grokbot glides into view', '-', 'Cut on bar 7; ship reaches frame centre by bar 8'),
 (8, 'A (dip)', 'Low angle, ship slides past camera, very slow', 'Hull fills frame; saucer GLINT star-flash', '-', 'Glint lands on bar 10 downbeat (~21.0 s)'),
 (12, 'Build', 'Punch-in medium, chair centre', 'RIKER swings leg over chair, sits backwards, beard-stroke', 'RIKER / Number One (backwards)', 'Cut on 25.03 hit; leg-swing on the 25.96 swell'),
 (14, 'Build', 'Holodeck grid wide, slow push into arch', 'BARCLAY opens program windows, hearts, faints from joy', 'LT. BARCLAY / Holodeck', 'Windows pop on beats; faint on bar 16 downbeat'),
 (16, 'Build', 'Viewscreen frame, push to Picard', 'PICARD sips tea, sets cup down, points: ENGAGE', 'PICARD / Enterprise-D', 'Point lands on bar 18 downbeat'),
 (18, 'Build', 'Medium, slight dutch tilt', 'GROK BOT stacks boxes, LED-meter mouth bounces to beat, stamps DONE', 'GROK BOT', 'Meter on every beat; DONE stamp on bar 20 downbeat'),
 (20, 'Build', 'Medium two-shot', 'RED SHIRT #47 beams in eager -> DELETE & RECREATE shimmer -> #48', 'ENS. RED SHIRT #47 -> #48', 'Beam-out on bar 21, #48 in on bar 22'),
 (22, 'Build (swell)', 'Low hero angle, slow push', 'CAPTAIN in chair rises, ENGAGE! point', 'THE CAPTAIN / ENGAGE!', 'Swell 47.93 s -> point on 49.3 downbeat'),
 (24, 'CLIMAX', 'Whip-zoom into ship, star streaks', 'WARP JUMP: streaks + ink flash', 'WARP 9', 'Exactly on 49.3 s climax downbeat (biggest section change)'),
 (25, 'Climax', 'Rapid cuts, one per bar (2.04 s)', 'Power-pose lineup: Picard hips, Riker grin, Grok Bot tada, Barclay thumbs, Red Shirt cheer', '-', 'One character punch-in per bar 25-27'),
 (28, 'Climax', 'Viewscreen snap-zoom', 'DAIMON GRUBB cameo, gold bars, fine print', 'DAIMON GRUBB (cameo)', 'Pops on 57.82 hit; out on 60.16 hit'),
 (30, 'Climax', 'Tracking banking flyby past planet', 'Ship banks past planet with light streaks', '-', 'Bank on 63.34 hit; second pass on 70.96 hit'),
 (36, 'Climax (final lift)', 'Bridge wide; ship passes overhead on screen', 'Full crew salute in sync, ship arcs toward camera', '-', 'Salute on 76.09 hit; ship hits camera on 83.78 hit'),
 (42, 'Outro', 'Static, existing sting timing', 'STARSHIP GROKBOT title stamp + ship zips off; credit line', 'STARSHIP GROKBOT / by Grok Bot & Nate Haskins', 'Stamp on 85.89 s bar; hold to fade-out at ~91 s'),
]
shots = []
for i, s in enumerate(S):
    st = 0.0 if s[0] is None else b(s[0]); en = b(S[i+1][0]) if i+1 < len(S) else D
    shots.append(dict(n=i+1, start=st, end=en, section=s[1], camera=s[2], action=s[3], text=s[4], sync=s[5]))
json.dump(shots, open('shots.json', 'w'), indent=1)
f = lambda t: f'{int(t//60)}:{t%60:05.2f}'
# grid
fh = ImageFont.truetype('/usr/share/fonts/truetype/sand-box/google/Patrick Hand/PatrickHand-Regular.ttf', 22)
fm = ImageFont.truetype('/usr/share/fonts/truetype/sand-box/google/Permanent Marker/PermanentMarker-Regular.ttf', 24)
tw, th, cap = 480, 270, 64; G = Image.new('RGB', (4*tw+50, 4*(th+cap)+90), (243, 238, 230)); d = ImageDraw.Draw(G)
d.text((20, 20), 'STARSHIP GROKBOT - music video storyboard v1 (%.1fs, %.1f BPM)' % (D, A['tempo']), font=fm, fill=(20, 22, 26))
for s in shots:
    k = s['n']-1; x = 10 + (k % 4)*(tw+10); y = 70 + (k//4)*(th+cap)
    G.paste(Image.open(f"frames/shot{s['n']:02d}.png").resize((tw, th)), (x, y)); d.rectangle([x, y, x+tw, y+th], outline=(20, 22, 26), width=2)
    d.text((x+4, y+th+2), f"#{s['n']}  {f(s['start'])}-{f(s['end'])}  {s['section']}", font=fm, fill=(20, 22, 26))
    d.text((x+4, y+th+32), s['action'][:52], font=fh, fill=(20, 22, 26))
G.save('storyboard.png')
# animatic: each still with slow zoom, cut on shot times
parts = []
for s in shots:
    dur = s['end']-s['start']; o = f"/tmp/an{s['n']:02d}.mp4"; nfr = int(round(s['end']*24))-int(round(s['start']*24))
    vf = (f"scale=1920:1080,zoompan=z='1+0.04*on/{nfr}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={nfr}:s=1280x720:fps=24,"
          f"drawtext=fontfile='/usr/share/fonts/truetype/sand-box/google/Permanent Marker/PermanentMarker-Regular.ttf':text='#{s['n']}  {f(s['start']).replace(':', chr(92)+':')}':x=20:y=20:fontsize=28:fontcolor=0x14161a:box=1:boxcolor=0xf3eee6")
    subprocess.run(['nice', '-n', '10', 'ffmpeg', '-loglevel', 'error', '-y', '-i', f"frames/shot{s['n']:02d}.png", '-vf', vf, '-frames:v', str(nfr), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-threads', '2', o], check=True)
    parts.append(o)
open('/tmp/an.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
subprocess.run(['nice', '-n', '10', 'ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', '/tmp/an.txt', '-i', 'track.mp3', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', 'animatic.mp4'], check=True)
# markdown
L = ['# Starship Grokbot music video - storyboard v1 (for review)', '',
     f"Track: `track.mp3` - {D:.1f} s, ~{A['tempo']:.1f} BPM (bar = {B[1]-B[0]:.2f} s), instrumental (whisper found no lyrics). First downbeat {B[0]:.2f} s.", '',
     'Sections (energy per 4-bar block, see `analysis.png`): Intro 0-4.7 s (big hit 1.37, swell 3.99) / A 4.7-17.0 (cinematic) / dip 17.0-25.1 / Build 25.1-49.3 (swells 25.96, 47.93) / **Climax 49.3-85.9** (hits 57.8, 63.3, 76.1, 83.8) / Outro 85.9-93.2 (tail fades ~91 s).', '',
     'Concept: TNG-opening-titles parody in ink on paper. Slow space shots first, then a no-voice crew roll-call with hand-lettered name cards, warp jump on the climax downbeat, end on the STARSHIP GROKBOT sting with the credit line. All cuts are on bar downbeats.', '',
     '| # | Time | Section | Camera / motion | Action | On-screen text | Beat sync |', '|---|---|---|---|---|---|---|']
for s in shots: L.append(f"| {s['n']} | {f(s['start'])}-{f(s['end'])} | {s['section']} | {s['camera']} | {s['action']} | {s['text']} | {s['sync']} |")
L += ['', 'Files: `storyboard.png` (grid), `animatic.mp4` (stills over the track), `frames/shotNN.png`, `analysis.json`, `analysis.png`, `shots.json`.', '',
      '## Open questions', '- Shots 14-15 are long (~12 s each); split into more crew action beats or keep slow cinematic?',
      '- Captain and Picard both on board: keep both, or drop the Captain for a second Riker/Grok Bot beat?',
      '- Paper-white space (series look) vs. ink-black space for the cinematic shots?',
      '- Title stamp at 85.9 s with the existing 3 s sting, then hold the logo card through the ~5 s tail?']
open('storyboard.md', 'w').write('\n'.join(L) + '\n')
for s in shots: print(s['n'], f(s['start']), f(s['end']), s['action'][:50])
