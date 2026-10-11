"""21.2-49.0: crew arrive one by one, stations boot on bars, power builds 39.4-46.65, warp jump on the drop."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

def walker(who, x0, x1, t_in, dur, facing, end_pose, y=STAND, keys=()):
    return dict(who=who, x=x0, y=y, facing=facing, pose='stand', moves=[(t_in, x1, y, dur)],
                mod=('walk', t_in, at(t_in, dur)), keys=[(at(t_in, dur), end_pose, .3)] + list(keys))

def arrivals():
    return [
        walker('ensign', 2100, 525, 'b:21.2+0.3', 3.0, -1, 'console'),
        walker('riker', -180, 1240, 'b:24.85+0.2', 3.2, 1, 'console', keys=[('b:26.66+0.4', 'console+look_l', .3), ('b:28.49', 'console', .3)]),
        walker('crew2', -180, 1545, 'b:28.49+0.1', 3.3, 1, 'console'),
        walker('grokbot', 2100, 980, 'b:32.14+0.1', 2.6, -1, 'front', keys=[('b:33.95', 'front+wave', .2), ('b:35.76', 'front', .3)]),
        dict(who='captain', x=-200, y=STAND, facing=1, pose='stand', mod=('walk', 'b:35.76+0.1', 'b:35.76+1.75'),
             moves=[('b:35.76+0.1', 640, STAND, 1.65), ('b:37.59-0.12', 718, 820, .25)],
             keys=[('b:37.59-0.12', 'sit', .25), ('b:37.59+0.3', 'sit+thumbs', .25), ('b:39.4', 'sit', .3),
                   ('b:46.21-0.15', 'sit+point+mouth=2', .15)]),
    ]

BOOT = {'OPS': 'b:24.85', 'HELM': 'b:28.49', 'SCI': 'b:32.14'}
CUES = dict(
    segment=dict(name='boot', t0=21.2, t1=49.0),
    people=PEOPLE,
    events=dict(boot='b:28.49', fl0='b:41.22', fl1='b:46.65', g0='b:39.4', g1='b:46.65-0.3', jump='b:46.65+0.35'),
    shots=[
        dict(at='b:21.2', set='bridge', bounce=2, kick=0.006, opt=dict(screen='off', boot=BOOT, gauge_level=0.08),
             cam=[('b:21.2', (980, 560, 1.0)), ('b:21.2+0.1', (900, 580, 1.12), 7.0)], cast=arrivals()),
        dict(at='b:28.49', set='bridge', bounce=2, kick=0.006, opt=dict(screen='boot', boot=BOOT, boot_len=7.0, gauge_level=0.12),
             cam=[('b:28.49', (1160, 560, 1.3)), ('b:32.14', (1080, 560, 1.25), 3.0)], cast=arrivals()),
        dict(at='b:35.76', set='bridge', bounce=3, kick=0.01, opt=dict(screen='stars', gauge_level=0.15),
             cam=[('b:35.76', (960, 560, 1.0)), ('b:37.59', (900, 590, 1.12), 1.6)], cast=arrivals()),
        dict(at='b:39.4', set='bridge', bounce=4, kick=0.02, opt=dict(screen='warp', gauge=('g0', 'g1', 0.15), flicker=('fl0', 'fl1')),
             cam=[('b:39.4', (700, 430, 1.45)), ('b:41.22', (760, 470, 1.6), 1.6)], cast=arrivals()),
        dict(at='b:43.05', set='bridge', bounce=6, kick=0.03, opt=dict(screen='countdown', gauge=('g0', 'g1', 0.15), flicker=('fl0', 'fl1'),
                                                                       countdown=[(45.30, '3'), (45.74, '2'), (46.21, '1')]),
             cam=[('b:43.05', (960, 540, 1.0)), ('b:43.05+0.1', (960, 430, 1.3), 3.4)], cast=arrivals()),
        dict(at='b:46.65', set='fullwarp', bounce=0, kick=0.03, opt=dict(c=(1150, 520), scale=1.5, facing=-1, label=True),
             cam=[('b:46.65', (960, 540, 1.0)), ('b:46.65+0.4', (960, 540, 1.12), 1.8)]),
    ],
    transitions=[dict(at='b:46.65', kind='splat', pre=0.2, post=0.32, c=(960, 300), seed=11)],
)
