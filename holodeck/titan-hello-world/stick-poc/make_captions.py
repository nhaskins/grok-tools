"""Monochrome karaoke captions for the stick POC (times shifted to segment start)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE)
T0, T1 = 49.0, 66.5
L = json.load(open(f'{PROJ}/lyric-timing.json'))
def ts(t):
    t = max(t, 0); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
# ASS colours are &HAABBGGRR. Ink #141618-ish, paper #F3EEE6, unsung grey.
INK, GREY, PAPER = '&H00141618', '&H00A8A8A8', '&H00E6EEF3'
hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Lyric,Exo 2,66,{INK},{GREY},{PAPER},&H00000000,1,0,0,0,100,100,1,0,1,6,0,2,90,90,42,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
KEY = {"Titan's", 'Riker', 'Picard', 'Enterprise,', 'Shields'}
ev = []
for k, o in enumerate(L):
    ws = o['words']; s0, e0 = ws[0]['s'], ws[-1]['e']
    if e0 < T0 or s0 > T1: continue
    nxt = L[k + 1]['words'][0]['s'] if k + 1 < len(L) else 999
    a = s0 - 0.3; b = min(e0 + 0.6, nxt - 0.3, T1 + 0.5)
    kt = [f"{{\\k{int((s0 - a) * 100)}}}"]
    for j, w in enumerate(ws):
        end = ws[j + 1]['s'] if j + 1 < len(ws) else w['e']
        d = max(int((end - w['s']) * 100), 1)
        t0 = int((w['s'] - a) * 1000)
        pop = f"\\t({t0},{t0 + 90},\\fscy112)\\t({t0 + 90},{t0 + 260},\\fscy100)" if w['w'] in KEY else ''
        kt.append(f"{{\\kf{d}{pop}}}{w['w']}{'{\\fscy100}' if pop else ''} ")
    ev.append(f"Dialogue: 1,{ts(a - T0)},{ts(b - T0)},Lyric,,0,0,0,,{{\\fad(150,250)\\move(960,1052,960,1038,0,200)}}" + ''.join(kt).strip())
open(f'{HERE}/captions.ass', 'w').write(hdr + '\n'.join(ev) + '\n')
print(len(ev), 'lines')
