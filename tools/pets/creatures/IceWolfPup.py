# Ice Wolf Pup (Epic): silver wolf pup with glowing blue eyes.
# Copied from the skill's arctic fox example. Traits: silver-grey pup with a darker saddle and dark-tipped
# big upright ears, a pale chest ruff and muzzle, small glowing ice-blue eyes, a frosty spiky mane tuft
# on the crown and a bushy tail with a frosted tip.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'IceWolfPup'
RARITY = 'Epic'
STUDS = 5.0
# silver fur in 4 tones (C2 tops, C1 main, C3 sides, C4 underside) + dark saddle + pale ruff + frost + glowing eyes
PALETTE = dict(C1='aab4c4', C2='cdd5e1', C3='8d98aa', C4='6e788b', SD='5a6377', S2='474f61', CR='eef2f8',
               FR='e2f3ff', FB='9fd6ff', IN='e9c3cf',
               EY='121622', IR='58d2ff', WH='ffffff', NS='1f2230', NH='b9c3d3', PK='ffaec2', PD='7f8aa0')
GLOW = {'IR'}
HP = (0, -0.38, 0.76)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.05, 0.46), (0, 0.05, 0.76), 'root'),
         ('head', HP, (0, -0.38, 1.16), 'body'),
         ('jaw', (0, -0.76, 0.80), (0, -0.92, 0.78), 'head'),
         ('tail1', (0, 0.44, 0.64), (0, 0.68, 0.74), 'body'),
         ('tail2', (0, 0.68, 0.74), (0, 0.86, 1.00), 'tail1'),
         ('tail3', (0, 0.86, 1.00), (0, 0.92, 1.24), 'tail2')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{s}', (0.21 * sx, -0.52, 1.16), (0.24 * sx, -0.52, 1.46), 'head'),
              (f'leg.{s}', (0.16 * sx, -0.23, 0.30), (0.16 * sx, -0.23, 0.0), 'body'),
              (f'hind.{s}', (0.16 * sx, 0.31, 0.30), (0.16 * sx, 0.31, 0.0), 'body')]
HEAD = dict(scale=1.4, pivot=HP, bones=('head', 'jaw', 'ear.L', 'ear.R'))


def build(K):
    span, sym = K.span, K.sym

    def hs(y0, y1, x0, x1, z0, z1, k, b='head'):   # head parts drawn in the example's coordinates
        span(y0 + 0.02, y1 + 0.02, x0, x1, z0 - 0.04, z1 - 0.04, k, b)

    # body: silver loaf with a dark saddle over the back
    span(-0.28, 0.38, -0.22, 0.22, 0.24, 0.30, 'C4', 'body')        # belly
    span(-0.34, 0.44, -0.30, 0.30, 0.30, 0.64, 'C1', 'body')        # core
    sym(-0.26, 0.36, 0.30, 0.34, 0.36, 0.52, 'C3', 'body')          # side step
    sym(-0.16, 0.36, 0.30, 0.345, 0.52, 0.64, 'SD', 'body')         # saddle drapes down the sides
    span(-0.24, 0.40, -0.26, 0.26, 0.64, 0.70, 'SD', 'body')        # saddle
    span(-0.08, 0.32, -0.15, 0.15, 0.70, 0.73, 'S2', 'body')        # saddle cap
    # pale chest ruff, stepping forward
    span(-0.44, -0.34, -0.27, 0.27, 0.32, 0.74, 'CR', 'body')
    span(-0.50, -0.44, -0.19, 0.19, 0.38, 0.66, 'CR', 'body')
    span(-0.54, -0.50, -0.09, 0.09, 0.44, 0.58, 'CR', 'body')
    # frosted scruff behind the head
    span(-0.30, -0.10, -0.18, 0.18, 0.70, 0.78, 'FR', 'body')
    # legs: pup legs, pale paws
    for sx, s in K.sides():
        for b, y0, y1 in ((f'leg.{s}', -0.30, -0.16), (f'hind.{s}', 0.24, 0.38)):
            span(y0, y1, 0.09 * sx, 0.24 * sx, 0.07, 0.30, 'C1', b)
            span(y0 - 0.04, y1 + 0.02, 0.08 * sx, 0.25 * sx, 0.0, 0.07, 'CR', b)
            for dx in (0.13, 0.20):                                          # toe grooves
                span(y0 - 0.05, y0 - 0.04, (dx - 0.006) * sx, (dx + 0.006) * sx, 0.0, 0.05, 'PD', b)
        span(0.16, 0.44, 0.30 * sx, 0.36 * sx, 0.30, 0.54, 'C3', f'hind.{s}')   # haunch
    # head (scaled 1.4 around the neck)
    hs(-0.52, -0.36, -0.20, 0.20, 0.74, 0.86, 'C1')                 # neck
    hs(-0.78, -0.34, -0.30, 0.30, 0.80, 1.20, 'C1')                 # skull
    hs(-0.72, -0.40, -0.24, 0.24, 1.20, 1.26, 'C3')                 # darker crown
    sym(-0.72 + 0.02, -0.44 + 0.02, 0.30, 0.34, 0.82 - 0.04, 1.00 - 0.04, 'CR', 'head')    # pale cheek ruff
    sym(-0.66 + 0.02, -0.52 + 0.02, 0.34, 0.38, 0.80 - 0.04, 0.92 - 0.04, 'C2', 'head')    # cheek tuft
    hs(-0.96, -0.78, -0.15, 0.15, 0.84, 0.97, 'CR')                 # pale muzzle
    hs(-0.94, -0.78, -0.11, 0.11, 0.97, 1.01, 'C1')                 # muzzle top
    hs(-1.03, -0.96, -0.10, 0.10, 0.85, 0.96, 'CR')                 # muzzle tip
    hs(-1.06, -1.03, -0.06, 0.06, 0.89, 0.96, 'NS')                 # nose
    hs(-1.065, -1.06, -0.035, -0.005, 0.935, 0.95, 'NH')            # nose shine (goes gold on a Golden pet)
    hs(-0.98, -0.78, -0.10, 0.10, 0.79, 0.84, 'C2', 'jaw')          # lower jaw
    hs(-0.94, -0.80, -0.06, 0.06, 0.84, 0.845, 'PK', 'jaw')         # mouth
    for sx in (1, -1):   # small glowing eyes: dark block, glowing iris, one shine
        hs(-0.795, -0.78, 0.10 * sx, 0.23 * sx, 1.00, 1.12, 'EY')
        hs(-0.80, -0.795, 0.12 * sx, 0.21 * sx, 1.01, 1.09, 'IR')
        hs(-0.805, -0.80, 0.165 * sx, 0.20 * sx, 1.055, 1.085, 'WH')
        hs(-0.805, -0.80, 0.125 * sx, 0.14 * sx, 1.02, 1.035, 'WH')
    # ears: big upright stepped triangles, dark tips, pale pink inside
    for sx, s in K.sides():
        b = f'ear.{s}'
        rows = ((0.06, 0.38, 1.20, 1.30), (0.10, 0.38, 1.30, 1.40), (0.15, 0.37, 1.40, 1.49),
                (0.20, 0.36, 1.49, 1.57), (0.25, 0.34, 1.57, 1.63))
        for i, (x0, x1, z0, z1) in enumerate(rows):
            hs(-0.60, -0.48, x0 * sx, x1 * sx, z0, z1, ('C1', 'C1', 'C3', 'SD', 'S2')[i], b)
        for x0, x1, z0, z1 in ((0.12, 0.32, 1.22, 1.32), (0.16, 0.32, 1.32, 1.42), (0.21, 0.32, 1.42, 1.50)):
            hs(-0.615, -0.60, x0 * sx, x1 * sx, z0, z1, 'IN', b)
    # frosty mane tuft: icy spikes sweeping back between the ears
    K.spike((0, -0.50, 1.20), (0, 0.25, 1), 0.42, 0.17, 'FR', 'FB', 'head')
    for sx in (1, -1):
        K.spike((0.07 * sx, -0.42, 1.20), (0.30 * sx, 0.45, 1), 0.32, 0.14, 'FR', 'FB', 'head')
    # tail: bushy, perked up in a curve, frosted tip
    span(0.44, 0.68, -0.13, 0.13, 0.56, 0.80, 'C1', 'tail1')
    span(0.48, 0.66, -0.10, 0.10, 0.80, 0.84, 'SD', 'tail1')
    span(0.64, 0.96, -0.20, 0.20, 0.70, 1.04, 'C1', 'tail2')          # bushiest part
    sym(0.68, 0.92, 0.20, 0.23, 0.74, 1.00, 'C3', 'tail2')
    span(0.96, 1.00, -0.14, 0.14, 0.74, 1.00, 'C3', 'tail2')
    span(0.68, 0.92, -0.15, 0.15, 1.04, 1.08, 'SD', 'tail2')
    span(0.68, 0.92, -0.15, 0.15, 0.66, 0.70, 'C4', 'tail2')
    span(0.78, 1.02, -0.16, 0.16, 1.08, 1.26, 'FR', 'tail3')          # frosted tip
    sym(0.82, 0.98, 0.16, 0.18, 1.10, 1.24, 'FB', 'tail3')
    span(0.82, 0.98, -0.09, 0.09, 1.26, 1.31, 'FB', 'tail3')

def idle(f):     # breathing, a curious pup head tilt, ear flick, tail sway
    ph = TAU * f / 96
    tilt = max(0, S(TAU * f / 96 - 0.5)) ** 2              # holds a tilt for a moment each loop
    tw = max(0, S(TAU * f / 48) - 0.8) * 5
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 16 * tilt, 6 * S(ph)),
            'ear.L': (0, -12 * tw, 0), 'ear.R': (0, 10 * tilt, 0),
            'tail1': (0, 0, 8 * S(ph * 2)), 'tail2': (0, 0, 10 * S(ph * 2 - 0.6)), 'tail3': (0, 0, 12 * S(ph * 2 - 1.2))}


def hop(f):      # trot: diagonal pairs, body bob, tail swings late
    ph = TAU * f / 12; c = math.cos(ph)
    a = 30 * S(ph)
    return {'leg.L': (-a, 0, 0), 'hind.R': (-a, 0, 0), 'leg.R': (a, 0, 0), 'hind.L': (a, 0, 0),
            'body': (0, 3 * c, 2 * S(ph)), 'head': (-3 * abs(S(ph)), -3 * c, -2 * S(ph)),
            'ear.L': (6 * abs(c), 0, 0), 'ear.R': (6 * abs(c), 0, 0),
            'tail1': (-5, 0, 10 * S(ph - 0.8)), 'tail2': (0, 0, 12 * S(ph - 1.4)), 'tail3': (0, 0, 14 * S(ph - 2.0)),
            'root_loc': (0, 0, 0.05 * abs(S(ph)))}


def cheer(f):    # a little howl (head up, jaw open, tail wagging), then a happy hop
    rise = EASE(min(f / 8, 1)) * (1 - EASE(min(max(f - 22, 0) / 6, 1)))
    if f < 28: up = 0
    elif f < 38: up = S(math.pi * (f - 28) / 10)
    else: up = 0
    wg = S(TAU * f / 8) * S(math.pi * f / 40)
    return {'body': (-10 * rise - 10 * up, 0, 0), 'head': (-30 * rise + 8 * up, 0, 0), 'jaw': (22 * rise, 0, 0),
            'leg.L': (-8 * rise - 35 * up, 0, 0), 'leg.R': (-8 * rise - 35 * up, 0, 0),
            'hind.L': (10 * rise + 30 * up, 0, 0), 'hind.R': (10 * rise + 30 * up, 0, 0),
            'ear.L': (0, 10 * rise, 0), 'ear.R': (0, -10 * rise, 0),
            'tail1': (-12 * rise, 0, 24 * wg), 'tail2': (0, 0, 28 * S(TAU * f / 8 - 0.8) * S(math.pi * f / 40)),
            'tail3': (0, 0, 32 * S(TAU * f / 8 - 1.6) * S(math.pi * f / 40)),
            'root_loc': (0, 0, 0.45 * up)}


CLIPS = {'Idle': (96, idle), 'Hop': (24, hop), 'Cheer': (40, cheer)}
PREVIEW = dict(target=(0, 0.1, 0.85), ortho=3.1, shots=[('Cheer', 16), ('Hop', 3)], loop='Idle')
