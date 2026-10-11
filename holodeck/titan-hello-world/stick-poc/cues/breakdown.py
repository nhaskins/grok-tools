"""66.5-77.07: systems green, heroic silhouette lineup, tension build into the chorus."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

CUES = dict(
    segment=dict(name='breakdown', t0=66.5, t1=77.07),
    people=PEOPLE,
    events=dict(chk=66.65, green='w:systems+0.1', stars='w:stars', fl0='b:75.26', fl1='b:77.07', g0='b:75.26', g1='b:77.07-0.2'),
    shots=[
        dict(at=66.5, set='bridge', bounce=3, kick=0.01, opt=dict(screen='stars', checks='chk', stamp=('green', 'ALL SYSTEMS GREEN')),
             cam=[(66.5, (960, 520, 1.15)), ('b:66.46+0.2', (960, 500, 1.22), 1.6)],
             cast=bridge_crew(keys={'captain': [('w:green-0.1', 'sit+thumbs', .2)], 'riker': [('w:green', 'thumbs', .2)],
                                    'grokbot': [('w:green', 'front+tada', .2)]})),
        dict(at='b:68.22', set='heroic', bounce=2, kick=0.0, stroke=7.5,
             cam=[('b:68.22', (960, 620, 1.0)), ('b:68.22+0.1', (960, 580, 1.14), 6.9)],
             cast=[dict(who='crew2', x=520, y=STAND, facing=1, pose='pointup', keys=[('w:stars', 'pointup+smile', .3)]),
                   dict(who='ensign', x=730, y=STAND, facing=1, pose='salute'),
                   dict(who='captain', x=960, y=STAND, facing=1, pose='hips', keys=[('w:boldest-0.1', 'hips+mouth=2', .3)]),
                   dict(who='riker', x=1190, y=STAND, facing=-1, pose='grin'),
                   dict(who='grokbot', x=1400, y=STAND, facing=-1, pose='front', keys=[('w:stars', 'front+tada', .3)])]),
        dict(at='b:75.26', set='bridge', bounce=5, kick=0.03, opt=dict(screen='warp', gauge=('g0', 'g1', 0.3), flicker=('fl0', 'fl1')),
             cam=[('b:75.26', (960, 540, 1.05)), ('b:75.26+0.1', (900, 520, 1.35), 1.7)],
             cast=bridge_crew(keys={'captain': [('b:76.16', 'sit+point', .2)]})),
    ],
    transitions=[dict(at='b:68.22', kind='wipe', pre=0.25, post=0.35, seed=5),
                 dict(at='b:77.07', kind='wipe', pre=0.3, post=0.3, seed=6)],
)
