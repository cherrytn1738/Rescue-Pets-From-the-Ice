# Snow Bunny (Common, Fresh Snow): round white bunny with fluffy earmuff ears.
# Copied from the skill's bunny example. Traits: a rounder white loaf body, short ears that flop down over
# the sides of the head and end in big round fluff pom-poms (the "earmuffs"), pom tail, big back feet.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'SnowBunny'
RARITY = 'Common'
STUDS = 5.0
# white fur in 4 tones (C2 tops, C1 main, C3 sides, C4 underside) + ice-blue earmuff fluff + pink accents
PALETTE = dict(C1='f2f5fa', C2='ffffff', C3='d9e3ee', C4='aebdcf', CR='e4f1ff', CL='ffffff', MF='bfe1ff', MD='8fc2ef',
               EY='1d2230', IR='4a6fa8', WH='ffffff', NS='ff7d9c', PK='ffb3c4', PI='ffc6d2', DK='5d6b82')
GLOW = set()
HP = (0, -0.25, 0.70)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.02, 0.30), (0, 0.02, 0.62), 'root'),
         ('head', HP, (0, -0.25, 1.05), 'body'),
         ('nose', (0, -0.56, 0.84), (0, -0.62, 0.84), 'head'),
         ('tail', (0, 0.34, 0.32), (0, 0.52, 0.34), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{s}', (0.15 * sx, -0.36, 1.04), (0.30 * sx, -0.36, 1.10), 'head'),
              (f'leg.{s}', (0.12 * sx, -0.31, 0.20), (0.12 * sx, -0.31, 0.0), 'body'),
              (f'hind.{s}', (0.26 * sx, 0.14, 0.30), (0.26 * sx, 0.14, 0.0), 'body')]
HEAD = dict(scale=1.4, pivot=HP, bones=('head', 'nose', 'ear.L', 'ear.R'))


def build(K):
    span, sym = K.span, K.sym
    # body: a rounder sitting loaf than the example, pale blue-white belly
    span(-0.28, 0.30, -0.28, 0.28, 0.08, 0.16, 'C4', 'body')
    span(-0.34, 0.36, -0.35, 0.35, 0.16, 0.54, 'C1', 'body')
    sym(-0.26, 0.30, 0.35, 0.38, 0.22, 0.48, 'C3', 'body')
    span(-0.28, 0.32, -0.28, 0.28, 0.54, 0.64, 'C1', 'body')
    span(-0.18, 0.26, -0.20, 0.20, 0.64, 0.70, 'C2', 'body')
    span(-0.38, -0.34, -0.22, 0.22, 0.20, 0.52, 'CR', 'body')
    span(-0.40, -0.38, -0.14, 0.14, 0.26, 0.46, 'CR', 'body')
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.39, -0.27, 0.06 * sx, 0.17 * sx, 0.04, 0.20, 'C1', b)
        span(-0.42, -0.27, 0.055 * sx, 0.175 * sx, 0.0, 0.04, 'C3', b)
        span(-0.425, -0.42, 0.10 * sx, 0.11 * sx, 0.0, 0.03, 'DK', b)
    for sx, s in K.sides():
        b = f'hind.{s}'
        span(-0.02, 0.32, 0.32 * sx, 0.43 * sx, 0.12, 0.40, 'C1', b)
        span(0.02, 0.28, 0.31 * sx, 0.41 * sx, 0.40, 0.46, 'C2', b)
        span(-0.06, -0.02, 0.32 * sx, 0.41 * sx, 0.16, 0.34, 'C3', b)
        span(0.32, 0.36, 0.32 * sx, 0.41 * sx, 0.16, 0.36, 'C3', b)
        span(-0.28, 0.34, 0.22 * sx, 0.40 * sx, 0.03, 0.12, 'C1', b)
        span(-0.28, 0.34, 0.22 * sx, 0.40 * sx, 0.0, 0.03, 'C4', b)
        span(-0.32, -0.28, 0.23 * sx, 0.39 * sx, 0.0, 0.08, 'C3', b)
        for dx in (0.28, 0.34):
            span(-0.325, -0.32, (dx - 0.006) * sx, (dx + 0.006) * sx, 0.0, 0.06, 'DK', b)
    # tail: big round pom-pom
    span(0.36, 0.56, -0.16, 0.16, 0.16, 0.52, 'CL', 'tail')
    span(0.38, 0.60, -0.21, 0.21, 0.21, 0.47, 'CL', 'tail')
    span(0.40, 0.56, -0.11, 0.11, 0.52, 0.56, 'CL', 'tail')
    span(0.60, 0.63, -0.13, 0.13, 0.26, 0.42, 'C3', 'tail')
    sym(0.42, 0.56, 0.21, 0.24, 0.26, 0.42, 'C3', 'tail')
    # head (scaled 1.4 around the neck)
    span(-0.40, -0.18, -0.18, 0.18, 0.64, 0.74, 'C1', 'head')
    span(-0.50, -0.24, -0.20, 0.20, 0.68, 0.72, 'C4', 'head')
    span(-0.56, -0.18, -0.28, 0.28, 0.76, 1.00, 'C1', 'head')
    span(-0.54, -0.20, -0.24, 0.24, 1.00, 1.05, 'C1', 'head')
    span(-0.54, -0.20, -0.24, 0.24, 0.72, 0.76, 'C1', 'head')
    sym(-0.50, -0.22, 0.28, 0.31, 0.76, 0.92, 'C3', 'head')
    span(-0.50, -0.24, -0.20, 0.20, 1.05, 1.09, 'C2', 'head')
    span(-0.18, -0.14, -0.22, 0.22, 0.78, 0.98, 'C3', 'head')
    span(-0.60, -0.50, -0.12, 0.12, 0.72, 0.86, 'CR', 'head')
    span(-0.58, -0.56, -0.16, 0.16, 0.74, 0.84, 'CR', 'head')
    span(-0.61, -0.60, -0.005, 0.005, 0.74, 0.81, 'DK', 'head')
    for sx in (1, -1):
        for x, z in ((0.075, 0.80), (0.10, 0.77), (0.10, 0.83)):
            span(-0.605, -0.60, (x - 0.008) * sx, (x + 0.008) * sx, z - 0.008, z + 0.008, 'DK', 'head')
        span(-0.58, -0.56, 0.08 * sx, 0.21 * sx, 0.87, 1.00, 'EY', 'head')
        span(-0.585, -0.58, 0.11 * sx, 0.18 * sx, 0.88, 0.94, 'IR', 'head')
        span(-0.59, -0.58, 0.145 * sx, 0.195 * sx, 0.95, 0.99, 'WH', 'head')
        span(-0.59, -0.58, 0.105 * sx, 0.125 * sx, 0.895, 0.915, 'WH', 'head')
        span(-0.575, -0.56, 0.19 * sx, 0.26 * sx, 0.79, 0.84, 'PK', 'head')
    span(-0.62, -0.60, -0.04, 0.04, 0.82, 0.87, 'NS', 'nose')
    span(-0.625, -0.62, -0.025, 0.025, 0.85, 0.865, 'WH', 'nose')
    # earmuff ears: up out of the crown, arching outward, flopping down the sides into big fluff poms
    for sx, s in K.sides():
        b = f'ear.{s}'
        span(-0.42, -0.30, 0.10 * sx, 0.22 * sx, 1.05, 1.15, 'C1', b)                # ear root
        span(-0.43, -0.42, 0.12 * sx, 0.20 * sx, 1.06, 1.13, 'PI', b)
        K.limb((0.20 * sx, -0.36, 1.12), (0.31 * sx, -0.36, 1.06), 0.10, 0.12, 'C2', b, extend=0.05)
        K.limb((0.31 * sx, -0.36, 1.08), (0.33 * sx, -0.37, 0.96), 0.10, 0.12, 'C1', b, extend=0.04)
        # the pom: a stepped round fluff ball over the cheek, ice-blue inside like a real earmuff
        span(-0.49, -0.25, 0.28 * sx, 0.42 * sx, 0.78, 0.98, 'MF', b)
        span(-0.46, -0.28, 0.27 * sx, 0.45 * sx, 0.81, 0.95, 'MF', b)
        span(-0.51, -0.23, 0.30 * sx, 0.40 * sx, 0.81, 0.95, 'MF', b)
        span(-0.46, -0.28, 0.30 * sx, 0.40 * sx, 0.75, 1.01, 'MF', b)
        span(-0.44, -0.30, 0.45 * sx, 0.46 * sx, 0.83, 0.93, 'MD', b)                 # darker centre dimple
        span(-0.47, -0.27, 0.31 * sx, 0.39 * sx, 1.01, 1.02, 'CL', b)                 # light top


def idle(f):
    ph = TAU * f / 90
    tw = max(0, S(TAU * f / 30) - 0.6) * 2.5
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 0, 6 * S(TAU * f / 180)),
            'nose': (8 * tw * S(TAU * f / 4), 0, 0),
            'ear.L': (0, 4 * S(ph + 0.4), 0), 'ear.R': (0, -4 * S(ph + 1.2), 0),
            'tail': (0, 0, 6 * S(ph * 2))}


def hop(f):
    if f < 5: cr, up = EASE(f / 5), 0
    elif f < 17: u = (f - 5) / 12; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    else: u = (f - 17) / 7; cr, up = S(math.pi * u) * 0.8, 0
    return {'body': (6 * cr - 10 * up, 0, 0), 'head': (-5 * cr + 8 * up, 0, 0),
            'leg.L': (-30 * up, 0, 0), 'leg.R': (-30 * up, 0, 0),
            'hind.L': (35 * up - 8 * cr, 0, 0), 'hind.R': (35 * up - 8 * cr, 0, 0),
            'ear.L': (0, 10 * up, 0), 'ear.R': (0, -10 * up, 0),
            'tail': (-15 * up, 0, 0), 'root_loc': (0, 0, 0.32 * up - 0.05 * cr)}


def cheer(f):
    if f < 12: cr, up = EASE(f / 12), 0
    elif f < 30: u = (f - 12) / 18; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 38: cr, up = S(math.pi * (f - 30) / 8) * 0.9, 0
    else: cr, up = 0, 0
    tw = 25 * S(TAU * max(0, f - 12) / 18) * up
    return {'body': (10 * cr - 15 * up, 0, tw), 'head': (-8 * cr + 12 * up, 0, -tw * 0.5),
            'leg.L': (-45 * up + 10 * cr, 0, 0), 'leg.R': (-45 * up + 10 * cr, 0, 0),
            'hind.L': (45 * up - 12 * cr, 0, 0), 'hind.R': (45 * up - 12 * cr, 0, 0),
            'ear.L': (0, 18 * up, 0), 'ear.R': (0, -18 * up, 0),
            'tail': (-20 * up, 0, 0), 'root_loc': (0, 0, 0.85 * up - 0.10 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (40, cheer)}
PREVIEW = dict(target=(0, 0.0, 0.80), ortho=2.6, shots=[('Cheer', 21), ('Hop', 10)], loop='Idle')
