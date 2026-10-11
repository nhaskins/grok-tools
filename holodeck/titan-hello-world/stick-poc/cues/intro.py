"""0-21.2: ink draws the Titan, title card; "Titan, engage" on the bridge."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

CUES = dict(
    segment=dict(name='intro', t0=0.0, t1=21.2),
    people=PEOPLE,
    events=dict(draw_a='b:2.97', draw_b='b:10.29-0.3', title='b:10.29', sub='b:12.1', engage='w:engage'),
    shots=[
        dict(at=0.0, set='title', bounce=0, kick=0.006, cam=[(0.0, (960, 540, 1.0)), ('b:2.97', (960, 520, 1.1), 14.5)]),
        dict(at='b:17.55', set='engage', bounce=4, kick=0.015, opt=dict(word='engage', word_size=150),
             cam=[('b:17.55', (900, 560, 1.2)), ('w:engage-0.05', (920, 520, 1.42), 0.25)],
             cast=[dict(who='captain', x=820, y=STAND, facing=1, pose='look_r',
                        keys=[('w:titan,-0.1', 'stand+lookup=0.6', .3), ('w:engage-0.3', 'tada', .2), ('w:engage-0.06', 'point+mouth=2', .1)]),
                   dict(who='ensign', x=525, y=STAND, facing=-1, pose='console', keys=[('w:engage+0.2', 'console+look_r', .3)]),
                   dict(who='riker', x=1240, y=STAND, facing=1, pose='console', keys=[('w:engage+0.1', 'steer', .2)])]),
    ],
    transitions=[dict(at='b:17.55', kind='wipe', pre=0.4, post=0.35, seed=1)],
)
