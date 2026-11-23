# Polar Bear Cub (Rare): chubby cub wearing a scarf.
# Copied from the skill's red panda example (chibi quadruped). Traits: a chubby cream-white cub on all fours,
# round ears with dark insides, cream muzzle with a big dark nose, dark eye patches, a bright red-and-white
# striped scarf round the neck with a hanging end on its own bone (it swings), stubby tail, dark paw pads.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'PolarBearCub'
RARITY = 'Rare'
STUDS = 5.0
# cream-white fur in 4 tones (C2 tops, C1 main, C3 sides, C4 underside) + cream muzzle, dark nose/pads/eye patches,
# red scarf (SR main, SD shade) with white stripes (SW)
PALETTE = dict(C1='f3efe4', C2='fffcf4', C3='e3dccb', C4='c2b59c', MZ='fff6e2', ER='8c7f86', EM='5f6478',
               NS='1d1b24', PD='3b3742', EY='1b1a24', IR='4f6a99', WH='ffffff', PK='ff9fb2',
               SR='e8343f', SD='b5202c', SW='ffffff', SG='e6e1ea')
GLOW = set()
HP = (0, -0.40, 0.80)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.05, 0.5), (0, 0.05, 0.8), 'root'),
         ('head', HP, (0, -0.40, 1.2), 'body'),
         ('tail', (0, 0.38, 0.58), (0, 0.48, 0.62), 'body'),
         ('scarf', (0.20, -0.61, 0.60), (0.20, -0.61, 0.22), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{s}', (0.24 * sx, -0.52, 1.18), (0.24 * sx, -0.52, 1.38), 'head'),
              (f'leg.{s}', (0.22 * sx, -0.21, 0.30), (0.22 * sx, -0.21, 0.0), 'body'),
              (f'hind.{s}', (0.22 * sx, 0.25, 0.30), (0.22 * sx, 0.25, 0.0), 'body')]
HEAD = dict(scale=1.38, pivot=HP, bones=('head', 'ear.L', 'ear.R'))


def build(K):
    span, sym = K.span, K.sym
    # body: short chubby stepped loaf, light back, darker belly
    span(-0.28, 0.32, -0.28, 0.28, 0.20, 0.28, 'C4', 'body')        # belly
    span(-0.36, 0.38, -0.40, 0.40, 0.28, 0.72, 'C1', 'body')        # core
    sym(-0.28, 0.32, 0.40, 0.44, 0.34, 0.64, 'C3', 'body')          # side step
    span(-0.30, 0.34, -0.34, 0.34, 0.72, 0.78, 'C2', 'body')        # back
    span(-0.18, 0.24, -0.22, 0.22, 0.78, 0.81, 'C2', 'body')        # back cap
    span(-0.42, -0.36, -0.30, 0.30, 0.32, 0.62, 'C1', 'body')       # chest
    span(-0.44, -0.42, -0.18, 0.18, 0.36, 0.56, 'MZ', 'body')       # cream bib
    # thick short legs, wide paws with dark pads
    for sx, s in K.sides():
        for b, y0, y1 in ((f'leg.{s}', -0.30, -0.12), (f'hind.{s}', 0.16, 0.34)):
            span(y0, y1, 0.12 * sx, 0.33 * sx, 0.07, 0.30, 'C1', b)
            span(y0 - 0.04, y1 + 0.02, 0.11 * sx, 0.34 * sx, 0.0, 0.07, 'C3', b)
            span(y0 - 0.045, y0 - 0.04, 0.15 * sx, 0.30 * sx, 0.0, 0.03, 'PD', b)     # dark sole edge
            for dx in (0.17, 0.225, 0.28):                                            # toe grooves
                span(y0 - 0.05, y0 - 0.04, (dx - 0.008) * sx, (dx + 0.008) * sx, 0.03, 0.06, 'PD', b)
        span(0.08, 0.38, 0.44 * sx, 0.47 * sx, 0.32, 0.58, 'C3', f'hind.{s}')        # round haunch
        span(0.12, 0.34, 0.44 * sx, 0.46 * sx, 0.58, 0.62, 'C2', f'hind.{s}')
    # stubby round tail
    span(0.38, 0.46, -0.10, 0.10, 0.50, 0.66, 'C1', 'tail')
    span(0.38, 0.44, -0.07, 0.07, 0.66, 0.69, 'C2', 'tail')
    # chunky scarf wrap round the neck (body bone): red band, white stripes across it, dark-red lower step
    span(-0.64, -0.24, -0.41, 0.41, 0.58, 0.80, 'SR', 'body')
    span(-0.60, -0.28, -0.37, 0.37, 0.55, 0.58, 'SD', 'body')
    for x in (-0.27, -0.09, 0.09, 0.27):
        span(-0.65, -0.64, x - 0.045, x + 0.045, 0.58, 0.80, 'SW', 'body')
    for y in (-0.50, -0.34):
        sym(y - 0.045, y + 0.045, 0.41, 0.42, 0.58, 0.80, 'SW', 'body')
    span(-0.70, -0.62, 0.10, 0.30, 0.56, 0.76, 'SD', 'body')       # knot
    span(-0.71, -0.70, 0.14, 0.26, 0.60, 0.72, 'SR', 'body')
    # hanging end (own bone): stripes across the length, white fringe at the bottom
    for i, (z0, z1) in enumerate(((0.50, 0.58), (0.42, 0.50), (0.34, 0.42), (0.26, 0.34))):
        k = 'SR' if i % 2 == 0 else 'SW'
        span(-0.66, -0.57, 0.10, 0.30, z0, z1, k, 'scarf')
        span(-0.665, -0.66, 0.10, 0.30, z0, z1, 'SD' if k == 'SR' else 'SG', 'scarf')
    for dx in (0.13, 0.20, 0.27):
        span(-0.64, -0.59, dx - 0.022, dx + 0.022, 0.19, 0.26, 'SW', 'scarf')
    # head (scaled around the neck): big and round
    span(-0.52, -0.36, -0.22, 0.22, 0.74, 0.86, 'C1', 'head')       # neck
    span(-0.76, -0.34, -0.32, 0.32, 0.80, 1.18, 'C1', 'head')       # skull
    span(-0.72, -0.38, -0.26, 0.26, 1.18, 1.24, 'C2', 'head')       # crown
    sym(-0.70, -0.42, 0.32, 0.35, 0.84, 1.10, 'C1', 'head')          # cheek side step
    sym(-0.64, -0.50, 0.35, 0.36, 0.84, 0.94, 'C3', 'head')          # cheek fluff
    span(-0.72, -0.40, -0.26, 0.26, 0.77, 0.80, 'C4', 'head')       # chin underside
    # muzzle: short cream block, big dark nose, little smile
    span(-0.88, -0.76, -0.15, 0.15, 0.81, 0.97, 'MZ', 'head')
    span(-0.86, -0.76, -0.10, 0.10, 0.97, 1.00, 'MZ', 'head')
    span(-0.91, -0.88, -0.07, 0.07, 0.90, 0.97, 'NS', 'head')
    span(-0.915, -0.91, -0.045, -0.015, 0.94, 0.96, 'WH', 'head')
    span(-0.885, -0.88, -0.012, 0.012, 0.85, 0.90, 'NS', 'head')
    sym(-0.885, -0.88, 0.012, 0.06, 0.84, 0.855, 'NS', 'head')
    for sx in (1, -1):   # eyes on dark patches: dark block, blue iris, 2 shines; blush
        span(-0.775, -0.76, 0.06 * sx, 0.23 * sx, 0.97, 1.15, 'EM', 'head')
        span(-0.785, -0.775, 0.08 * sx, 0.20 * sx, 0.99, 1.13, 'EY', 'head')
        span(-0.79, -0.785, 0.10 * sx, 0.17 * sx, 1.00, 1.06, 'IR', 'head')
        span(-0.795, -0.785, 0.14 * sx, 0.19 * sx, 1.07, 1.11, 'WH', 'head')
        span(-0.795, -0.785, 0.095 * sx, 0.115 * sx, 1.01, 1.03, 'WH', 'head')
        span(-0.77, -0.76, 0.24 * sx, 0.31 * sx, 0.88, 0.93, 'PK', 'head')
    # round ears: stepped, dark inside
    for sx, s in K.sides():
        b = f'ear.{s}'
        span(-0.58, -0.46, 0.14 * sx, 0.34 * sx, 1.18, 1.34, 'C1', b)
        span(-0.57, -0.47, 0.17 * sx, 0.31 * sx, 1.34, 1.38, 'C2', b)
        span(-0.585, -0.58, 0.18 * sx, 0.30 * sx, 1.22, 1.32, 'ER', b)


def idle(f):
    ph = TAU * f / 90
    tw = max(0, S(TAU * f / 45) - 0.8) * 5               # an ear flick now and then
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 8 * S(TAU * f / 90 + 1), 6 * S(TAU * f / 180)),
            'ear.L': (-12 * tw, 0, 0), 'ear.R': (3 * S(ph * 2), 0, 0),
            'tail': (0, 0, 10 * S(ph * 2)), 'scarf': (-4 * S(ph), 5 * S(ph + 0.8), 0)}


def hop(f):    # bouncy bound: front pair then back pair, body rocks, scarf trails
    ph = TAU * f / 24; c = math.cos(ph)
    a = 30 * S(ph)
    return {'leg.L': (-a, 0, 0), 'leg.R': (-a, 0, 0), 'hind.L': (a, 0, 0), 'hind.R': (a, 0, 0),
            'body': (5 * c, 0, 0), 'head': (-4 * c, 0, 0),
            'ear.L': (6 * abs(c), 0, 0), 'ear.R': (6 * abs(c), 0, 0),
            'tail': (12 * S(ph), 0, 0), 'scarf': (12 + 10 * S(ph - 1.0), 0, 0),
            'root_loc': (0, 0, 0.12 * abs(S(ph)))}


def cheer(f):  # crouch -> jump with front paws waving -> land
    if f < 8: cr, up = EASE(f / 8), 0
    elif f < 26: u = (f - 8) / 18; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 34: cr, up = S(math.pi * (f - 26) / 8) * 0.8, 0
    else: cr, up = 0, 0
    wv = 25 * S(TAU * f / 9) * up
    return {'body': (8 * cr - 22 * up, 0, 0), 'head': (-6 * cr + 14 * up, 0, 6 * S(TAU * f / 18) * up),
            'leg.L': (-55 * up + wv + 10 * cr, 0, 0), 'leg.R': (-55 * up - wv + 10 * cr, 0, 0),
            'hind.L': (30 * up - 10 * cr, 0, 0), 'hind.R': (30 * up - 10 * cr, 0, 0),
            'ear.L': (-10 * cr, 0, 0), 'ear.R': (-10 * cr, 0, 0),
            'tail': (-25 * up, 0, 0), 'scarf': (-40 * up + 12 * cr, 0, 15 * S(TAU * f / 12) * up),
            'root_loc': (0, 0, 0.6 * up - 0.08 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (36, cheer)}
PREVIEW = dict(target=(0, -0.10, 0.85), ortho=3.0, shots=[('Cheer', 17), ('Hop', 6)], loop='Idle')
