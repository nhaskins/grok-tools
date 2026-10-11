"""158.66-175.47: climax - Titan at full warp, cut every bar, crew cheering, fireworks, everything bouncing on every beat."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

ALL = ('crew3', 'crew2', 'ensign', 'captain', 'grokbot', 'riker', 'crew4')
def cheering(x0=280, dx=230, pose='cheer'):
    return [dict(who=w, x=x0 + i * dx, y=STAND, facing=1, pose=pose + ('' if w == 'grokbot' else '+mouth=2'),
                 mod=('bop', 158.66, {'pump': 20})) for i, w in enumerate(ALL)]

BEAT = dict(jump='b:159.59', jump_every='beat', jump_h=45, shake_beat=5)
CUES = dict(
    segment=dict(name='climax', t0=158.66, t1=175.47),
    people=PEOPLE,
    events=dict(jump=999, warp=150, signal='b:164.93', light='b:164.93+0.9', sky=300, grok=100, alive=100, stars='b:173.82',
                rise_start='b:168.48-0.6', rise_top='b:170.27-0.3', high='b:170.27-0.3'),
    shots=[
        dict(at='w:engage+1.4', set='fullwarp', bounce=0, kick=0.04, shake_beat=7, opt=dict(jumping=False, c=(980, 520), scale=1.7, facing=-1, label=True),
             cam=[('w:engage+1.4', (960, 540, 1.0)), ('w:engage+1.5', (960, 540, 1.1), 0.9)]) if False else
        dict(at=158.66, set='fullwarp', bounce=0, kick=0.04, shake_beat=7, opt=dict(jumping=False, c=(980, 520), scale=1.7, facing=-1, label=True),
             cam=[(158.66, (960, 540, 1.0)), (158.7, (960, 540, 1.1), 0.9)]),
        dict(at='b:159.59', set='bridge', bounce=6, kick=0.04, **BEAT, opt=dict(screen='fireworks', confetti=True, chair=False),
             cam=[('b:159.59', (960, 560, 1.0))], cast=cheering()),
        dict(at='b:161.36', set='fullwarp', bounce=0, kick=0.04, shake_beat=7, opt=dict(jumping=False, c=(1100, 520), scale=1.9, facing=1),
             cam=[('b:161.36', (960, 540, 1.0)), ('b:161.36+0.1', (980, 520, 1.15), 1.7)]),
        dict(at='b:163.14', set='chorusline', bounce=7, kick=0.04, **BEAT,
             cam=[('b:163.14', (960, 560, 1.0))],
             cast=[dict(who=w, x=420 + i * 180, y=STAND, facing=1, pose='armlink', mod=('kick', 'b:163.14', {'amp': 80}))
                   for i, w in enumerate(ALL)]),
        dict(at='b:164.93', set='warpsky', bounce=0, kick=0.04, shake_beat=5,
             cam=[('b:164.93', (960, 540, 1.0)), ('b:164.93+0.1', (980, 500, 1.12), 1.7)]),
        dict(at='b:166.7', set='disco', bounce=8, kick=0.04, **BEAT, opt=dict(sign='TITAN!', notes_from=['grokbot']),
             cam=[('b:166.7', (960, 580, 1.1))],
             cast=[dict(who='grokbot', x=960, y=STAND, facing=1, pose='front', mod=('robotdance', 'b:166.7'))] +
                  [dict(who=w, x=x, y=STAND, facing=1, pose='cheer+mouth=2', mod=('bop', 'b:166.7', {'pump': 25}))
                   for w, x in (('captain', 520), ('riker', 1400), ('ensign', 300), ('crew2', 1620))]),
        dict(at='b:168.48', set='rise', bounce=6, kick=0.04, jump='b:168.48', jump_every='beat', jump_h=45,
             cam=[('b:168.48', (960, 500, 1.0)), ('b:168.48+0.3', (960, 120, 1.05), 1.3)],
             cast=[dict(who=w, x=x, y=y, facing=f, pose='cheer') for w, x, y, f in
                   (('ensign', 330, 754, 1), ('captain', 480, 740, 1), ('riker', 1440, 740, -1), ('grokbot', 1590, 754, -1))]),
        dict(at='b:170.27', set='bridge', bounce=6, kick=0.04, **BEAT, opt=dict(screen='fireworks', confetti=True, chair=False),
             cam=[('b:170.27', (960, 600, 1.25))], cast=cheering(pose='tada')),
        dict(at='b:172.06', set='fullwarp', bounce=0, kick=0.05, shake_beat=9, opt=dict(jumping=False, c=(900, 540), scale=1.9, facing=-1),
             cam=[('b:172.06', (960, 540, 1.0)), ('b:172.06+0.1', (960, 540, 1.08), 1.7)]),
        dict(at='b:173.82', set='heroic', bounce=6, kick=0.04, **BEAT, stroke=7,
             cam=[('b:173.82', (960, 600, 1.0))], cast=cheering(dx=225)),
    ],
    transitions=[],
)
