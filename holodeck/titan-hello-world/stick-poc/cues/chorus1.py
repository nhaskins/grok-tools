"""Cue table: first chorus + bridge (77.5-104.0 s). Rendered by:  python engine.py cues/chorus1.py
Times: number | 'w:word[#n][+-off]' | 'b:approx[+-off]' (see engine.py)."""

STAND = 770          # hip height for a standing figure on FLOOR=880
SEAT = 822           # hip height seated on a stool/chair

CUES = dict(
    segment=dict(name='chorus1', t0=77.07, t1=104.1, out='titan-stick-chorus1-poc.mp4', fade_out_to='ink'),   # song cut starts on the 77.07 bar

    people=dict(
        captain=dict(props=['cap', 'badge']),
        riker=dict(props=['beard', 'badge']),
        ensign=dict(props=['ponytail', 'badge']),
        crew2=dict(props=['badge']),
        grokbot=dict(props=['robot']),
    ),

    # named gag timings, read by sets.py via ctx.ev(name)
    events=dict(
        pull='w:pull', sync_checks='w:keep', sync='w:sync',
        draft='w:draft-0.1', deals='w:deals', faster='w:faster', think='w:think',
        log='w:log', clock_spin='w:quarter-0.25', clock_land='w:five', yawn='w:five+0.15',
        grok='w:grok', alive='w:alive',
        warp='w:warp', signal='w:signal', light='w:light', sky='w:sky',
        rise_start='b:98.71+0.2', rise_top='w:high', high='w:high',
    ),

    shots=[
        # --- build: tug-of-war on the CODE crate, synchronized yanks on every beat
        dict(at='b:77.07', set='tug', bounce=4, kick=0.012,
             cam=[('b:77.07', (820, 640, 1.2)), ('b:80.67', (860, 680, 1.45), 0.35)],
             cast=[dict(who=w, x=x, y=STAND, facing=1, pose='stand',
                        keys=[(77.07, 'look_r', 0), ('b:78.88-0.2', 'pull', 0.4), ('w:sync', 'pull+smile', 0.1)],
                        mod=('pull', 'w:pull', 'b:82.48'))
                   for w, x in (('crew2', 330), ('ensign', 470), ('riker', 610), ('captain', 750))]),
        # --- HIT (ink splat): drafting deals at full speed, cut on every bar
        dict(at='b:82.48', set='draft', bounce=7, kick=0.03,
             cam=[('b:82.48', (960, 690, 1.75)), ('b:84.29', (800, 620, 2.0), 0)],
             cast=[dict(who='riker', x=650, y=SEAT, facing=1, pose='sit+scribble', keys=[('w:think', 'sit+surprise', .15)]),
                   dict(who='ensign', x=1270, y=SEAT, facing=-1, pose='sit+scribble')]),
        dict(at='b:86.08', set='log', bounce=6, kick=0.03,
             cam=[('b:86.08', (1000, 600, 1.5)), ('b:87.89', (1130, 600, 1.5), 0)],
             cast=[dict(who='captain', x=830, y=SEAT, facing=1, pose='sit+mic', keys=[('w:five+0.15', 'sit+yawn', .3)])]),
        dict(at='b:89.68', set='chorusline', bounce=6, kick=0.03, jump='b:89.68',
             cam=[('b:89.68', (960, 560, 1.15)), ('b:91.49', (960, 560, 1.38), 0), ('b:93.3', (960, 560, 1.15), 1.4)],
             cast=[dict(who=w, x=x, y=STAND, facing=1, pose='armlink',
                        mod=('kick', 'b:89.68', {'amp': 72, 'soft_from': 'b:93.3', 'soft': 0.45}))
                   for w, x in (('crew2', 600), ('ensign', 780), ('grokbot', 960), ('captain', 1140), ('riker', 1320))]),
        # --- bridge (ink wipe): warp the signal, fireworks light the sky
        dict(at='b:95.09', set='warpsky', bounce=0, kick=0.015,
             cam=[('b:95.09', (960, 540, 1.0)), ('b:96.9', (900, 480, 1.12), 0.5)], cast=[]),
        dict(at='b:98.71', set='rise', bounce=5, kick=0.015, jump='w:rising',
             cam=[('b:98.71', (960, 540, 1.0)), ('w:rising', (960, 300, 1.0), 1.0),
                  ('w:titan#1', (960, -60, 1.05), 0.9), ('w:high', (960, -160, 1.15), 0.8)],
             cast=[dict(who=w, x=x, y=y, facing=f, pose='look_r' if f > 0 else 'look_l',
                        keys=[('b:98.71', {'lookup': 1, 'mouth': 3}, .3), ('w:titan', 'pointup+smile', .25), ('w:rising', 'cheer', .25)])
                   for w, x, y, f in (('ensign', 330, 754, 1), ('captain', 480, 740, 1), ('riker', 1440, 740, -1), ('grokbot', 1590, 754, -1))]),
    ],

    transitions=[
        dict(at='b:82.48', kind='splat', pre=0.22, post=0.34, c=(1060, 520), seed=4),
        dict(at='b:95.09', kind='wipe', pre=0.34, post=0, seed=2),
        dict(at='b:104.1', kind='splat', pre=0.45, post=0.35, c=(960, 470), seed=9),   # into the mid instrumental
    ],

    captions={'We pull': 'pop', 'We draft': 'pop', "Captain's": 'pop', 'Grok Bot': 'pop', 'Warp': 'stretch', 'Titan rising': 'rise'},
    caption_keywords=['code', 'sync', 'deals', 'faster', 'think', 'log', 'five', 'grok', 'bot', 'mission', 'alive', 'warp', 'signal', 'sky', 'titan', 'rising', 'high'],
)
