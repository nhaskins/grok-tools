"""Full song: python engine.py cues/song.py   (renders all sections in parallel, joins, muxes audio, burns one caption file)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CAPTION_STYLES, KEYWORDS

SONG = dict(name='full', t0=0.0, t1=180.84, out='titan-stick-full.mp4',
            sections=['intro', 'boot', 'verse1', 'breakdown', 'chorus1', 'mid', 'chorus2', 'lead', 'engage', 'climax', 'finale'],
            captions=CAPTION_STYLES, caption_keywords=KEYWORDS)
