"""131.01-150.67: final chorus. Chorus-1 gags escalated; 132.8-140 dip held calmer; 140+ full energy."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

PULLERS = ('crew4', 'crew3', 'crew2', 'ensign', 'riker', 'grokbot', 'captain')
def tug_cast(jump=False):
    return [dict(who=w, x=170 + i * 125, y=STAND, facing=1, pose='pull', keys=[('w:sync', 'pull+smile', .1)],
                 mod=('pull', 'w:pull', 'b:134.61')) for i, w in enumerate(PULLERS)]

LINE = ('crew5', 'crew3', 'crew2', 'ensign', 'grokbot', 'captain', 'riker', 'crew4', 'crew6')
CUES = dict(
    segment=dict(name='chorus2', t0=131.01, t1=150.67),
    people=PEOPLE,
    events=dict(pull='w:pull', sync_checks='w:keep', sync='w:sync',
                draft='w:draft-0.1', deals='w:deals', faster='w:faster', think='w:think',
                log='w:log', clock_spin='w:quarter-0.25', clock_land='w:five', yawn='w:five+0.15',
                grok='w:grok', alive='w:alive'),
    shots=[
        dict(at='b:131.01', set='tug', bounce=6, kick=0.03, opt=dict(crates=3, sign='git pull --all'),
             cam=[('b:131.01', (985, 600, 1.0)), ('b:131.01+0.1', (1000, 620, 1.1), 1.7)], cast=tug_cast()),
        dict(at='b:132.79', set='tug', bounce=3, kick=0.01, opt=dict(crates=3, sign='git pull --all'),      # dip: calmer, slow push
             cam=[('b:132.79', (700, 660, 1.3)), ('b:132.79+0.1', (760, 640, 1.4), 1.7)], cast=tug_cast()),
        dict(at='b:134.61', set='draft', bounce=3, kick=0.008, opt=dict(sheets=2),                           # dip: one held shot
             cam=[('b:134.61', (960, 690, 1.6)), ('b:134.61+0.1', (820, 640, 1.95), 3.4)],
             cast=[dict(who='riker', x=650, y=SEAT, facing=1, pose='sit+scribble+scrib=1.8', keys=[('w:think', 'sit+surprise', .15)]),
                   dict(who='ensign', x=1270, y=SEAT, facing=-1, pose='sit+scribble+scrib=1.8')]),
        dict(at='b:138.18', set='log', bounce=3, kick=0.01, opt=dict(wild=9),
             cam=[('b:138.18', (1000, 600, 1.4)), ('b:139.97', (1130, 600, 1.5), 0)],
             cast=[dict(who='captain', x=830, y=SEAT, facing=1, pose='sit+mic', keys=[('w:five+0.15', 'sit+yawn', .3)])]),
        dict(at='b:141.76', set='chorusline', bounce=7, kick=0.03, jump='b:141.76',
             cam=[('b:141.76', (960, 560, 1.0)), ('b:143.55', (960, 560, 1.4), 0), ('b:145.31', (960, 560, 1.0), 0),
                  ('b:147.1', (700, 580, 1.45), 0), ('b:148.89', (960, 560, 1.05), 0)],
             cast=[dict(who=w, x=240 + i * 180, y=STAND, facing=1, pose='armlink', mod=('kick', 'b:141.76', {'amp': 75}))
                   for i, w in enumerate(LINE)]),
    ],
    transitions=[dict(at='b:141.76', kind='splat', pre=0.2, post=0.3, c=(960, 540), seed=17)],
)
