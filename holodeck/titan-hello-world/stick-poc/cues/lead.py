"""150.67-157.26: lead-in to the climax, cut on every bar (then every beat): flashes of earlier gags."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

CUES = dict(
    segment=dict(name='lead', t0=150.67, t1=157.26),
    people=PEOPLE,
    events=dict(pull='b:150.67', sync_checks='b:150.67+0.9', sync='b:152.46-0.5',
                log='b:152.46', clock_spin='b:154.23-0.6', clock_land='b:154.23-0.1', yawn=300,
                warp='b:154.23-0.6', signal='b:154.23', light='b:154.23+1.0', sky=300,
                draft=150, deals=150.2, faster=150.4, think=150.6, grok=100, alive=100,
                rise_start='b:156.01', rise_top='b:156.9+0.2', high='b:156.9'),
    shots=[
        dict(at='b:150.67', set='tug', bounce=7, kick=0.035, opt=dict(crates=2),
             cam=[('b:150.67', (880, 650, 1.35))],
             cast=[dict(who=w, x=330 + i * 140, y=STAND, facing=1, pose='pull', mod=('pull', 'b:150.67'))
                   for i, w in enumerate(('crew2', 'ensign', 'riker', 'captain'))]),
        dict(at='b:152.46', set='log', bounce=7, kick=0.035, opt=dict(wild=16),
             cam=[('b:152.46', (1150, 560, 1.55))],
             cast=[dict(who='captain', x=830, y=SEAT, facing=1, pose='sit+mic+mouth=3')]),
        dict(at='b:154.23', set='warpsky', bounce=0, kick=0.03, cam=[('b:154.23', (960, 540, 1.0)), ('b:154.23+0.1', (900, 500, 1.15), 1.7)]),
        dict(at='b:156.01', set='draft', bounce=8, kick=0.04, opt=dict(sheets=3), cam=[('b:156.01', (800, 620, 2.0))],
             cast=[dict(who='riker', x=650, y=SEAT, facing=1, pose='sit+surprise'),
                   dict(who='ensign', x=1270, y=SEAT, facing=-1, pose='sit+scribble+scrib=2.2')]),
        dict(at=156.46, set='chorusline', bounce=8, kick=0.04, jump=156.46, jump_every='beat',
             cam=[(156.46, (960, 600, 1.35))],
             cast=[dict(who=w, x=600 + i * 180, y=STAND, facing=1, pose='armlink', mod=('kick', 156.46, {'amp': 80}))
                   for i, w in enumerate(('crew2', 'ensign', 'grokbot', 'captain', 'riker'))]),
        dict(at=156.9, set='rise', bounce=6, kick=0.04, cam=[(156.9, (960, 120, 1.05))]),
    ],
    transitions=[],
)
