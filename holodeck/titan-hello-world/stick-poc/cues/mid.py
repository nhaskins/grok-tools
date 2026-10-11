"""104.1-131.01: instrumental mini-story (2-bar cuts): Grok Bot disco, Riker's trombone, poker, away mission, dance party; build back to the bridge."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

def back_to_stations():
    c = bridge_crew(keys={'captain': [('b:129.22', 'sit+point', .2)]})
    starts = {'captain': (-90, 718), 'ensign': (2010, 525), 'riker': (-90, 1240), 'crew2': (2010, 1545), 'grokbot': (2010, 980)}
    for d in c:
        x0, x1 = starts[d['who']]; d['facing'] = 1 if x1 > x0 else -1
        if d['who'] in ('ensign',): d['facing'] = -1
        y = d['y']; d['x'] = x0; d['y'] = STAND
        d['moves'] = [('b:125.64', x1, STAND, 1.25)] + ([('b:125.64+1.3', x1, 820, .2)] if d['who'] == 'captain' else [])
        d['mod'] = ('walk', 'b:125.64', 'b:125.64+1.25', {'rate': 3.2})
        d['keys'] = [('b:125.64', 'stand+mouth=3', 0), ('b:125.64+1.3', d['pose'], .2)] + d['keys']
    # Riker and crew2 face right at their stations; ensign walks in from the right facing left
    return c

CUES = dict(
    segment=dict(name='mid', t0=104.1, t1=131.01),
    people=PEOPLE,
    events=dict(wah='b:109.48+0.9', reveal='b:113.08', wah2='b:122.04-0.5', fl0='b:127.43', fl1='b:131.01', g0='b:125.64', g1='b:131.01-0.3'),
    shots=[
        dict(at='b:104.1', set='disco', bounce=5, kick=0.02, opt=dict(sign='GROK BOT  //  DJ SET'),
             cam=[('b:104.1', (960, 560, 1.12)), ('b:104.1+0.1', (960, 580, 1.3), 3.4)],
             cast=[dict(who='grokbot', x=960, y=STAND, facing=1, pose='front', mod=('robotdance', 'b:104.1')),
                   dict(who='captain', x=560, y=STAND, facing=1, pose='front+smile', mod=('bop', 'b:104.1', {'pump': 40})),
                   dict(who='riker', x=1360, y=STAND, facing=-1, pose='front+grin', mod=('bop', 'b:104.1', {'pump': 40}))]),
        dict(at='b:107.69', set='stage', bounce=4, kick=0.02, opt=dict(trombone='riker', sign='LIVE: RIKER & THE BRASS'),
             cam=[('b:107.69', (1000, 580, 1.2)), ('b:109.48', (980, 560, 1.32), 0.4)],
             cast=[dict(who='riker', x=720, y=STAND, facing=1, pose='trombone+mouth=3', mod=('slide', 'b:107.69')),
                   dict(who='captain', x=1380, y=STAND, facing=-1, pose='look_l', keys=[('wah', 'salute', .2)]),
                   dict(who='ensign', x=1580, y=STAND, facing=-1, pose='look_l', keys=[('wah', 'handear+mouth=3', .2)])]),
        dict(at='b:111.27', set='poker', bounce=4, kick=0.02,
             cam=[('b:111.27', (960, 600, 1.2)), ('reveal', (960, 640, 1.42), 0.3)],
             cast=[dict(who='riker', x=600, y=SEAT, facing=1, pose='sit+cards+mouth=2', keys=[('reveal+0.35', 'sit+surprise', .15)]),
                   dict(who='captain', x=1320, y=SEAT, facing=-1, pose='sit+cards', keys=[('reveal+0.35', 'sit+surprise', .15)]),
                   dict(who='grokbot', x=960, y=STAND, facing=1, pose='front', keys=[('reveal-0.1', 'front+tada', .2)]),
                   dict(who='ensign', x=1620, y=STAND, facing=-1, pose='look_l', keys=[('reveal+0.4', 'cheer', .2)])]),
        dict(at='b:114.87', set='planet', bounce=4, kick=0.02,
             opt=dict(beam={'captain': 'b:114.87+0.5', 'riker': 'b:114.87+0.9', 'ensign': 'b:114.87+1.3'}, blob=(1480, 1480)),
             cam=[('b:114.87', (960, 560, 1.0)), ('b:114.87+0.1', (1050, 580, 1.15), 3.4)],
             cast=[dict(who=w, x=-900, y=STAND, facing=1, pose='stand', moves=[(tb, x, STAND, 0)], keys=k)
                   for w, x, tb, k in (('captain', 650, 'b:114.87+0.5', [('b:116.66-0.9', 'point', .2)]),
                                       ('riker', 860, 'b:114.87+0.9', [('b:116.66-0.7', 'surprise', .2)]),
                                       ('ensign', 1070, 'b:114.87+1.3', [('b:116.66-0.5', 'wave', .2)]))]),
        dict(at='b:116.66', set='planet', bounce=6, kick=0.02, opt=dict(blob=(1100, 2000)),
             cam=[('b:116.66', (850, 560, 1.0)), ('b:116.66+0.1', (1250, 560, 1.0), 3.5)],
             cast=[dict(who=w, x=x, y=STAND, facing=1, pose='stand+mouth=2', moves=[('b:116.66', x + 950, STAND, 3.6)],
                        mod=('walk', 'b:116.66', 'b:118.44', {'rate': 2.27}))
                   for w, x in (('grokbot', 760), ('ensign', 560), ('riker', 360), ('captain', 160))]),
        dict(at='b:118.44', set='disco', bounce=6, kick=0.025, jump='b:118.44', opt=dict(sign='DANCE-OFF!'),
             cam=[('b:118.44', (960, 580, 1.0)), ('b:120.26', (960, 600, 1.22), 0.0)],
             cast=[dict(who='captain', x=420, y=STAND, facing=1, pose='front+grin', mod=('kick', 'b:118.44', {'amp': 60})),
                   dict(who='ensign', x=690, y=STAND, facing=1, pose='front+smile', mod=('robotdance', 'b:118.44')),
                   dict(who='grokbot', x=960, y=STAND, facing=1, pose='front', mod=('robotdance', 'b:118.44')),
                   dict(who='riker', x=1230, y=STAND, facing=1, pose='front+grin', mod=('kick', 'b:118.44', {'amp': 60})),
                   dict(who='crew2', x=1500, y=STAND, facing=1, pose='front+smile', mod=('bop', 'b:118.44', {'pump': 50}))]),
        dict(at='b:122.04', set='planet', bounce=6, kick=0.025, jump='b:122.04', opt=dict(blob=(960, 960)),
             cam=[('b:122.04', (960, 560, 1.05)), ('b:122.04+0.1', (960, 580, 1.2), 3.5)],
             cast=[dict(who=w, x=x, y=STAND, facing=1, pose=p, mod=m) for w, x, p, m in
                   (('captain', 480, 'front+grin', ('kick', 'b:122.04', {'amp': 60})), ('riker', 700, 'front+grin', ('bop', 'b:122.04', {'pump': 60})),
                    ('ensign', 1220, 'front+smile', ('robotdance', 'b:122.04')), ('grokbot', 1440, 'front', ('robotdance', 'b:122.04')))]),
        # build back to the bridge (cut every bar)
        dict(at='b:125.64', set='bridge', bounce=5, kick=0.025, opt=dict(screen='stars', gauge=('g0', 'g1', 0.1)),
             cam=[('b:125.64', (960, 550, 1.0))], cast=back_to_stations()),
        dict(at='b:127.43', set='bridge', bounce=6, kick=0.03, opt=dict(screen='warp', gauge=('g0', 'g1', 0.1), flicker=('fl0', 'fl1')),
             cam=[('b:127.43', (700, 430, 1.45)), ('b:127.43+0.1', (740, 450, 1.6), 1.7)], cast=back_to_stations()),
        dict(at='b:129.22', set='bridge', bounce=7, kick=0.035, opt=dict(screen='countdown', gauge=('g0', 'g1', 0.1), flicker=('fl0', 'fl1'),
                                                                         countdown=[(129.66, '3'), (130.10, '2'), (130.57, '1')]),
             cam=[('b:129.22', (960, 540, 1.0)), ('b:129.22+0.1', (960, 430, 1.3), 1.7)], cast=back_to_stations()),
    ],
    transitions=[dict(at='b:131.01', kind='splat', pre=0.22, post=0.34, c=(960, 300), seed=14)],
)
