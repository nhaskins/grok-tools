"""157.26-158.66: "Engage!" - giant hand-lettered punch with screen shake, the whole crew pointing."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

CUES = dict(
    segment=dict(name='engage', t0=157.26, t1=158.66),
    people=PEOPLE,
    events=dict(engage='w:engage'),
    shots=[dict(at='w:engage', set='engage', bounce=6, kick=0.05, shake=26, opt=dict(screen='warp', word='ENGAGE!', word_size=250, chair=False),
                cam=[('w:engage', (960, 600, 1.0)), ('w:engage+0.05', (960, 620, 1.08), 1.2)],
                cast=lineup(('crew3', 'crew2', 'ensign', 'captain', 'riker', 'grokbot', 'crew4'), 260, 230, 'point+mouth=2', facing=1))],
    transitions=[],
)
