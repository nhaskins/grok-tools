"""Shared cast definitions + helpers for the section cue files."""
STAND = 770          # hip height for a standing figure (FLOOR 880)
SEAT = 822           # hip height seated

PEOPLE = dict(
    captain=dict(props=['cap', 'badge']),
    riker=dict(props=['beard', 'badge']),
    ensign=dict(props=['ponytail', 'badge']),
    crew2=dict(props=['badge']),
    crew3=dict(props=['badge', 'shine']),
    crew4=dict(props=['badge']),
    crew5=dict(props=['badge', 'ponytail']),
    crew6=dict(props=['badge']),
    grokbot=dict(props=['robot']),
)

def bridge_crew(pose_cap='sit', extra=(), keys=None):
    """Standard bridge stations: captain in the chair, ensign at OPS, Riker at HELM, crew2 at SCI, Grok Bot at tactical."""
    keys = keys or {}
    c = [dict(who='captain', x=718, y=820, facing=1, pose=pose_cap, keys=keys.get('captain', [])),
         dict(who='ensign', x=525, y=STAND, facing=-1, pose='console', keys=keys.get('ensign', [])),
         dict(who='riker', x=1240, y=STAND, facing=1, pose='console', keys=keys.get('riker', [])),
         dict(who='crew2', x=1545, y=STAND, facing=1, pose='console', keys=keys.get('crew2', [])),
         dict(who='grokbot', x=980, y=STAND, facing=1, pose='front', keys=keys.get('grokbot', []))]
    return c + list(extra)

def lineup(names, x0, dx, pose, y=STAND, facing=1, **kw):
    return [dict(who=n, x=x0 + i * dx, y=y, facing=facing, pose=pose, **kw) for i, n in enumerate(names)]

CAPTION_STYLES = {'Titan, engage': 'pop', 'Engage!': 'pop', 'We pull': 'pop', 'We draft': 'pop', "Captain's": 'pop', 'Grok Bot': 'pop',
                  'Warp': 'stretch', 'Titan rising': 'rise'}
KEYWORDS = ['titan', "titan's", 'engage', 'engage!', 'webhooks', 'riker', 'picard', 'enterprise', 'grin', 'shields', 'green', 'boldest', 'stars',
            'code', 'sync', 'deals', 'faster', 'think', 'log', 'five', 'grok', 'bot', 'mission', 'alive', 'warp', 'signal', 'sky', 'rising', 'high']

def at(spec, d):
    """time spec + seconds: at('b:21.2+0.3', 3.0) -> 'b:21.2+0.3+3.0'"""
    return f'{spec}{d:+g}' if isinstance(spec, str) else spec + d
