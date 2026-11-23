# Frost Dragon Hatchling (Legendary): baby dragon, pale blue scales, frosty breath.
# Copied from the skill's arctic fox example and rebuilt as a chubby baby dragon sitting up. Traits: pale blue
# scales with a light belly plate, small golden horns, a ridge of ice spikes down the back and tail, stubby
# flapping wings, a tail curled round to its right side, and a little frosty breath puff at the mouth (soft glow).
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'FrostDragonHatchling'
RARITY = 'Legendary'
STUDS = 5.0
# pale blue scales in 4 tones (C2 tops, C1 main, C3 sides, C4 underside), cream belly plate, ice-cyan spikes,
# periwinkle wing membranes, golden horns, frost breath
PALETTE = dict(C1='cde9fd', C2='eaf7ff', C3='a6cef1', C4='6f9dd4', BL='fbfdff', BG='c2d6ee',
               IC='6fdcff', IT='e2fcff', MB='7da6f5', HN='ffe4a3', HT='ffc14d', CW='ffffff',
               EY='1b2240', IR='ffc23a', WH='ffffff', PK='ff9fb8', DK='34507e',
               FB='f2fbff', FC='c4ecff', SP='7ff2ff')
GLOW = {'SP'}
HP = (0, -0.06, 0.70)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.0, 0.14), (0, 0.0, 0.60), 'root'),
         ('head', HP, (0, -0.06, 1.10), 'body'),
         ('jaw', (0, -0.42, 0.78), (0, -0.60, 0.76), 'head'),
         ('breath', (0.14, -0.60, 0.77), (0.26, -0.74, 0.77), 'head'),
         ('tail1', (0, 0.28, 0.18), (-0.16, 0.50, 0.12), 'body'),
         ('tail2', (-0.16, 0.50, 0.12), (-0.44, 0.46, 0.09), 'tail1'),
         ('tail3', (-0.44, 0.46, 0.09), (-0.56, 0.20, 0.07), 'tail2')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'wing.{s}', (0.24 * sx, 0.24, 0.64), (0.80 * sx, 0.24, 1.00), 'body'),
              (f'leg.{s}', (0.26 * sx, -0.28, 0.56), (0.26 * sx, -0.38, 0.34), 'body'),
              (f'hind.{s}', (0.38 * sx, 0.04, 0.26), (0.38 * sx, -0.20, 0.0), 'body')]
HEAD = dict(scale=1.35, pivot=HP, bones=('head', 'jaw', 'breath'))


def ridge(K, base, d, L, w, bone):
    K.spike(base, d, L, w, 'IC', 'IT', bone)


def build(K):
    span, sym = K.span, K.sym
    # body: chubby sitting pear, wide at the bottom
    span(-0.26, 0.26, -0.28, 0.28, 0.06, 0.14, 'C4', 'body')        # underside
    span(-0.32, 0.32, -0.36, 0.36, 0.14, 0.46, 'C1', 'body')        # lower core
    sym(-0.24, 0.26, 0.36, 0.40, 0.18, 0.42, 'C3', 'body')           # side step
    span(-0.28, 0.28, -0.30, 0.30, 0.46, 0.66, 'C1', 'body')        # upper core
    span(-0.20, 0.24, -0.22, 0.22, 0.66, 0.72, 'C2', 'body')        # shoulders
    span(0.32, 0.36, -0.26, 0.26, 0.18, 0.44, 'C3', 'body')         # back round
    # belly plate: pot belly with segment grooves
    span(-0.37, -0.32, -0.22, 0.22, 0.12, 0.46, 'BL', 'body')
    span(-0.32, -0.28, -0.17, 0.17, 0.46, 0.64, 'BL', 'body')
    for z in (0.20, 0.29, 0.38):
        span(-0.38, -0.37, -0.18, 0.18, z, z + 0.02, 'BG', 'body')
    for z in (0.52, 0.59):
        span(-0.33, -0.32, -0.14, 0.14, z, z + 0.02, 'BG', 'body')
    # back ridge: ice spikes leaning back
    ridge(K, (0, 0.10, 0.70), (0, 0.4, 1), 0.28, 0.16, 'body')
    ridge(K, (0, 0.26, 0.60), (0, 0.8, 1), 0.24, 0.14, 'body')
    ridge(K, (0, 0.35, 0.40), (0, 1, 0.6), 0.18, 0.12, 'body')
    # arms: little front paws held on the chest
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.36, -0.22, 0.20 * sx, 0.32 * sx, 0.40, 0.58, 'C1', b)
        span(-0.32, -0.24, 0.20 * sx, 0.32 * sx, 0.58, 0.62, 'C2', b)
        span(-0.44, -0.32, 0.18 * sx, 0.31 * sx, 0.30, 0.42, 'C3', b)
        for dx in (0.21, 0.28):
            span(-0.46, -0.44, (dx - 0.02) * sx, (dx + 0.02) * sx, 0.32, 0.37, 'CW', b)
    # hind legs: haunches on the sides, big feet forward, white claws
    for sx, s in K.sides():
        b = f'hind.{s}'
        span(-0.16, 0.22, 0.30 * sx, 0.46 * sx, 0.08, 0.36, 'C1', b)
        span(-0.12, 0.18, 0.30 * sx, 0.44 * sx, 0.36, 0.40, 'C2', b)
        span(-0.10, 0.16, 0.46 * sx, 0.49 * sx, 0.12, 0.32, 'C3', b)
        span(-0.46, -0.10, 0.22 * sx, 0.42 * sx, 0.0, 0.10, 'C1', b)
        span(-0.42, -0.14, 0.24 * sx, 0.40 * sx, 0.10, 0.13, 'C2', b)
        span(-0.46, 0.18, 0.22 * sx, 0.46 * sx, 0.0, 0.02, 'C4', b)
        for dx in (0.26, 0.32, 0.38):
            span(-0.50, -0.46, (dx - 0.022) * sx, (dx + 0.022) * sx, 0.0, 0.05, 'CW', b)
    # stubby wings: a stepped arm bar rising outward past the head, periwinkle membrane with a scalloped edge
    for sx, s in K.sides():
        b = f'wing.{s}'
        span(0.20, 0.30, 0.24 * sx, 0.42 * sx, 0.62, 0.72, 'C3', b)
        span(0.20, 0.30, 0.42 * sx, 0.58 * sx, 0.70, 0.82, 'C3', b)
        span(0.21, 0.29, 0.58 * sx, 0.72 * sx, 0.80, 0.94, 'C3', b)
        span(0.21, 0.29, 0.70 * sx, 0.80 * sx, 0.92, 1.04, 'C3', b)
        span(0.22, 0.28, 0.76 * sx, 0.82 * sx, 1.04, 1.12, 'HN', b)            # wing claw
        span(0.22, 0.28, 0.30 * sx, 0.44 * sx, 0.44, 0.62, 'MB', b)
        span(0.22, 0.28, 0.44 * sx, 0.58 * sx, 0.50, 0.70, 'MB', b)
        span(0.22, 0.28, 0.58 * sx, 0.70 * sx, 0.60, 0.80, 'MB', b)
        span(0.22, 0.28, 0.70 * sx, 0.78 * sx, 0.74, 0.92, 'MB', b)
        for x, z0 in ((0.44, 0.50), (0.58, 0.60), (0.70, 0.74)):
            span(0.215, 0.285, (x - 0.012) * sx, (x + 0.012) * sx, z0, z0 + 0.24, 'C3', b)
    # tail: three fat segments curling round to the right side, ice spikes on top, arrow tip
    K.limb((0, 0.26, 0.20), (-0.16, 0.50, 0.12), 0.26, 0.22, 'C1', 'tail1', extend=0.10)
    K.limb((-0.16, 0.50, 0.12), (-0.44, 0.46, 0.09), 0.20, 0.17, 'C3', 'tail2', extend=0.08)
    K.limb((-0.44, 0.46, 0.09), (-0.56, 0.20, 0.07), 0.15, 0.13, 'C1', 'tail3', extend=0.04)
    ridge(K, (-0.09, 0.40, 0.26), (0, 0.4, 1), 0.18, 0.12, 'tail1')
    ridge(K, (-0.30, 0.49, 0.17), (-0.2, 0.4, 1), 0.15, 0.10, 'tail2')
    K.spike((-0.555, 0.22, 0.07), (-0.3, -1, 0.15), 0.20, 0.15, 'IC', 'IT', 'tail3')
    # head (scaled 1.35 around the neck)
    span(-0.22, 0.08, -0.18, 0.18, 0.66, 0.76, 'C1', 'head')        # neck
    span(-0.44, 0.10, -0.30, 0.30, 0.76, 1.14, 'C1', 'head')        # skull
    sym(-0.38, 0.04, 0.30, 0.34, 0.80, 1.08, 'C3', 'head')           # cheek step
    span(-0.38, 0.04, -0.24, 0.24, 1.14, 1.19, 'C2', 'head')        # crown
    span(0.10, 0.14, -0.24, 0.24, 0.80, 1.08, 'C3', 'head')         # back of head
    span(-0.62, -0.44, -0.18, 0.18, 0.80, 0.94, 'C1', 'head')       # snout
    span(-0.60, -0.44, -0.14, 0.14, 0.94, 0.97, 'C2', 'head')       # snout top
    for sx in (1, -1):
        span(-0.625, -0.62, 0.06 * sx, 0.11 * sx, 0.88, 0.91, 'DK', 'head')   # nostrils
    span(-0.58, -0.40, -0.15, 0.15, 0.74, 0.80, 'BL', 'jaw')        # light lower jaw
    span(-0.585, -0.58, -0.07, 0.07, 0.785, 0.80, 'DK', 'jaw')      # little smile
    for sx in (1, -1):   # eyes: dark block, gold iris, 2 white shines, all proud of the face
        span(-0.46, -0.44, 0.07 * sx, 0.23 * sx, 0.97, 1.11, 'EY', 'head')
        span(-0.465, -0.46, 0.10 * sx, 0.19 * sx, 0.98, 1.05, 'IR', 'head')
        span(-0.47, -0.46, 0.15 * sx, 0.21 * sx, 1.06, 1.10, 'WH', 'head')
        span(-0.47, -0.46, 0.105 * sx, 0.125 * sx, 0.995, 1.015, 'WH', 'head')
        span(-0.455, -0.44, 0.22 * sx, 0.29 * sx, 0.91, 0.96, 'PK', 'head')   # blush
    # horns: small stepped golden horns sweeping up and back
    for sx in (1, -1):
        span(-0.10, 0.04, 0.12 * sx, 0.22 * sx, 1.19, 1.26, 'HN', 'head')
        span(-0.04, 0.08, 0.14 * sx, 0.21 * sx, 1.26, 1.33, 'HN', 'head')
        span(0.02, 0.10, 0.15 * sx, 0.20 * sx, 1.33, 1.38, 'HT', 'head')
    # ear frills: little fins stepping back off the sides of the head
    sym(0.00, 0.12, 0.34, 0.40, 0.96, 1.08, 'C3', 'head')
    sym(0.06, 0.16, 0.40, 0.45, 1.01, 1.12, 'C3', 'head')
    ridge(K, (0, 0.06, 1.16), (0, 0.5, 1), 0.17, 0.11, 'head')
    # frosty breath: a small round frost cloud drifting from the corner of the mouth, two glinting sparkles
    span(-0.66, -0.60, 0.12, 0.20, 0.74, 0.80, 'FC', 'breath')
    span(-0.73, -0.63, 0.17, 0.33, 0.70, 0.80, 'FB', 'breath')
    span(-0.71, -0.65, 0.19, 0.31, 0.67, 0.83, 'FB', 'breath')
    span(-0.75, -0.61, 0.21, 0.29, 0.72, 0.78, 'FB', 'breath')
    span(-0.70, -0.66, 0.30, 0.37, 0.80, 0.86, 'FC', 'breath')
    span(-0.765, -0.75, 0.22, 0.25, 0.79, 0.82, 'SP', 'breath')
    span(-0.69, -0.67, 0.36, 0.39, 0.88, 0.91, 'SP', 'breath')

def idle(f):
    ph = TAU * f / 90
    puff = max(0, S(TAU * f / 90 - 1.0) - 0.5) * 2      # a soft frosty puff once a loop
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6) - 4 * puff, 0, 8 * S(TAU * f / 180)),
            'jaw': (10 * puff, 0, 0), 'breath': (-6 * puff, 0, 8 * S(ph * 2)),
            'wing.L': (0, -6 * S(ph) - 3, 0), 'wing.R': (0, 6 * S(ph) + 3, 0),
            'tail1': (0, 0, 6 * S(ph)), 'tail2': (0, 0, 8 * S(ph - 0.6)), 'tail3': (0, 0, 12 * S(ph - 1.2))}


def hop(f):
    if f < 5: cr, up = EASE(f / 5), 0
    elif f < 17: u = (f - 5) / 12; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    else: u = (f - 17) / 7; cr, up = S(math.pi * u) * 0.8, 0
    fl = 30 * up * (0.5 + 0.5 * S(TAU * f / 12))
    return {'body': (6 * cr - 8 * up, 0, 0), 'head': (-5 * cr + 6 * up, 0, 0),
            'leg.L': (-20 * up, 0, 0), 'leg.R': (-20 * up, 0, 0),
            'hind.L': (30 * up - 8 * cr, 0, 0), 'hind.R': (30 * up - 8 * cr, 0, 0),
            'wing.L': (0, -10 - fl, 0), 'wing.R': (0, 10 + fl, 0),
            'tail1': (-12 * up, 0, 0), 'tail2': (0, 0, 8 * up), 'root_loc': (0, 0, 0.28 * up - 0.04 * cr)}


def cheer(f):
    if f < 10: cr, up = EASE(f / 10), 0
    elif f < 30: u = (f - 10) / 20; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 38: cr, up = S(math.pi * (f - 30) / 8) * 0.8, 0
    else: cr, up = 0, 0
    fl = (0.5 + 0.5 * S(TAU * (f - 10) / 10 - math.pi / 2)) * up
    return {'body': (8 * cr - 12 * up, 0, 0), 'head': (-6 * cr + 14 * up, 0, 0), 'jaw': (20 * up, 0, 0),
            'breath': (-10 * up, 0, 0),
            'leg.L': (-50 * up, 0, -20 * up), 'leg.R': (-50 * up, 0, 20 * up),
            'hind.L': (40 * up - 10 * cr, 0, 0), 'hind.R': (40 * up - 10 * cr, 0, 0),
            'wing.L': (0, -10 - 55 * fl - 10 * cr, 0), 'wing.R': (0, 10 + 55 * fl + 10 * cr, 0),
            'tail1': (-18 * up, 0, 0), 'tail2': (0, 0, 20 * S(TAU * f / 12) * up), 'tail3': (0, 0, 25 * S(TAU * f / 12 - 1) * up),
            'root_loc': (0, 0, 0.75 * up - 0.08 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (40, cheer)}
PREVIEW = dict(target=(0, -0.1, 0.85), ortho=2.8, shots=[('Cheer', 20), ('Hop', 10)], loop='Idle')
