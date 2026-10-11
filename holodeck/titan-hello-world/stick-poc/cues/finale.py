"""175.47-180.84: the Titan flies off into the starfield, slow push, hand-lettered end card, ink fades to paper."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

CUES = dict(
    segment=dict(name='finale', t0=175.47, t1=180.84),
    people=PEOPLE,
    events=dict(gone='b:178.93', card1='b:175.47+0.5', card2='b:175.47+1.4', card3='b:177.15', fade=179.55),
    shots=[dict(at='b:175.47', set='finale', bounce=0, kick=0.0,
                cam=[('b:175.47', (960, 540, 1.0)), ('b:175.47+0.1', (960, 540, 1.1), 5.2)])],
    transitions=[dict(at='b:175.47', kind='splat', pre=0.25, post=0.45, c=(960, 540), seed=21)],
)
