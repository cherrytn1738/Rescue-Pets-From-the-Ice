# Arctic Fox Kit (Uncommon): white fox cub with a blue tail tip.
# Copied from the skill's arctic fox example. Traits: a cub (big head, short legs, short body), white fur
# with dark socks, dark ear backs and ear tips, and a huge fluffy curled tail ending in a clear blue tip.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'ArcticFoxKit'
RARITY = 'Uncommon'
STUDS = 5.0
# white fur in 4 tones (C2 tops, C1 main, C3 sides, C4 underside) + dark markings + blue tail tip
PALETTE = dict(C1='f4f7fb', C2='ffffff', C3='dde6f0', C4='b9c6d6', DK='3b4356', DM='6b7690',
               TB='2f8cff', TL='7cc2ff', TD='1f63d6',
               EY='1d2030', IR='3f86e8', WH='ffffff', NS='22242f', NH='c9d2e0', PK='ffaec2', PD='9aa9c0')
GLOW = set()
HP = (0, -0.36, 0.70)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.05, 0.40), (0, 0.05, 0.70), 'root'),
         ('head', HP, (0, -0.36, 1.10), 'body'),
         ('jaw', (0, -0.70, 0.72), (0, -0.84, 0.70), 'head'),
         ('tail1', (0, 0.40, 0.50), (0, 0.74, 0.54), 'body'),
         ('tail2', (0, 0.74, 0.54), (0, 0.94, 0.90), 'tail1'),
         ('tail3', (0, 0.94, 0.90), (0, 0.94, 1.30), 'tail2')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{s}', (0.21 * sx, -0.51, 1.12), (0.24 * sx, -0.51, 1.40), 'head'),
              (f'leg.{s}', (0.16 * sx, -0.21, 0.24), (0.16 * sx, -0.21, 0.0), 'body'),
              (f'hind.{s}', (0.16 * sx, 0.27, 0.24), (0.16 * sx, 0.27, 0.0), 'body')]
HEAD = dict(scale=1.45, pivot=HP, bones=('head', 'jaw', 'ear.L', 'ear.R'))


def build(K):
    span, sym = K.span, K.sym

    def hs(y0, y1, x0, x1, z0, z1, k, b='head'):   # head parts drawn in the example's coordinates
        span(y0 + 0.04, y1 + 0.04, x0, x1, z0 - 0.10, z1 - 0.10, k, b)

    # body: short cub loaf
    span(-0.26, 0.34, -0.22, 0.22, 0.18, 0.24, 'C4', 'body')        # belly
    span(-0.32, 0.40, -0.30, 0.30, 0.24, 0.58, 'C1', 'body')        # core
    sym(-0.24, 0.32, 0.30, 0.34, 0.30, 0.52, 'C3', 'body')          # side step
    span(-0.26, 0.34, -0.24, 0.24, 0.58, 0.64, 'C2', 'body')        # back
    span(-0.14, 0.26, -0.14, 0.14, 0.64, 0.67, 'C2', 'body')        # back cap
    # chest ruff
    span(-0.42, -0.32, -0.26, 0.26, 0.28, 0.64, 'C2', 'body')
    span(-0.48, -0.42, -0.16, 0.16, 0.34, 0.56, 'C2', 'body')
    # legs: short stubby cub legs with dark socks
    for sx, s in K.sides():
        for b, y0, y1 in ((f'leg.{s}', -0.28, -0.14), (f'hind.{s}', 0.20, 0.34)):
            span(y0, y1, 0.09 * sx, 0.24 * sx, 0.10, 0.24, 'C1', b)
            span(y0 - 0.01, y1 + 0.01, 0.085 * sx, 0.245 * sx, 0.05, 0.10, 'DM', b)
            span(y0 - 0.04, y1 + 0.02, 0.08 * sx, 0.25 * sx, 0.0, 0.05, 'DK', b)
        span(0.12, 0.40, 0.30 * sx, 0.36 * sx, 0.26, 0.50, 'C3', f'hind.{s}')   # haunch
    # head (scaled 1.45 around the neck): rounder skull, short snout
    hs(-0.52, -0.36, -0.20, 0.20, 0.74, 0.86, 'C1')                 # neck
    hs(-0.78, -0.34, -0.31, 0.31, 0.80, 1.20, 'C1')                 # skull
    hs(-0.72, -0.40, -0.25, 0.25, 1.20, 1.26, 'C2')                 # crown
    hs(-0.30, -0.34, -0.24, 0.24, 0.84, 1.14, 'C3')                 # back of head
    sym(-0.66 + 0.04, -0.42 + 0.04, 0.31, 0.37, 0.82 - 0.10, 1.04 - 0.10, 'C2', 'head')    # cheek ruff
    sym(-0.62 + 0.04, -0.50 + 0.04, 0.37, 0.42, 0.82 - 0.10, 0.92 - 0.10, 'C2', 'head')    # cheek tuft
    hs(-0.90, -0.78, -0.15, 0.15, 0.84, 0.97, 'C1')                 # snout (short: a cub)
    hs(-0.88, -0.78, -0.11, 0.11, 0.97, 1.00, 'C2')                 # snout top
    hs(-0.96, -0.90, -0.09, 0.09, 0.85, 0.95, 'C1')                 # snout tip
    hs(-0.99, -0.96, -0.06, 0.06, 0.88, 0.95, 'NS')                 # nose
    hs(-0.995, -0.99, -0.03, 0.0, 0.925, 0.94, 'NH')                # nose shine (not WH: goes gold on a Golden pet)
    hs(-0.92, -0.78, -0.10, 0.10, 0.79, 0.84, 'C3', 'jaw')          # lower jaw
    hs(-0.90, -0.80, -0.06, 0.06, 0.84, 0.845, 'PK', 'jaw')         # mouth
    for sx in (1, -1):   # big cub eyes
        hs(-0.80, -0.78, 0.08 * sx, 0.24 * sx, 0.98, 1.16, 'EY')
        hs(-0.805, -0.80, 0.11 * sx, 0.20 * sx, 0.99, 1.06, 'IR')
        hs(-0.81, -0.80, 0.16 * sx, 0.22 * sx, 1.09, 1.14, 'WH')
        hs(-0.81, -0.80, 0.105 * sx, 0.13 * sx, 1.005, 1.03, 'WH')
        hs(-0.795, -0.78, 0.23 * sx, 0.30 * sx, 0.88, 0.94, 'PK')   # blush
    # ears: stepped triangles, pink inside, dark backs and dark tips
    for sx, s in K.sides():
        b = f'ear.{s}'
        rows = ((0.06, 0.36, 1.22, 1.30), (0.10, 0.36, 1.30, 1.38), (0.15, 0.35, 1.38, 1.45),
                (0.20, 0.34, 1.45, 1.51), (0.25, 0.33, 1.51, 1.55))
        for i, (x0, x1, z0, z1) in enumerate(rows):
            hs(-0.60, -0.48, x0 * sx, x1 * sx, z0, z1, 'DK' if i >= 3 else 'C1', b)
            hs(-0.48, -0.46, (x0 + 0.02) * sx, (x1 - 0.01) * sx, z0, z1, 'DM' if i < 3 else 'DK', b)   # dark back
        for x0, x1, z0, z1 in ((0.12, 0.30, 1.24, 1.32), (0.16, 0.30, 1.32, 1.40), (0.21, 0.30, 1.40, 1.45)):
            hs(-0.615, -0.60, x0 * sx, x1 * sx, z0, z1, 'PK', b)
    # tail: big fluffy curl, white base, clear blue tip
    span(0.40, 0.76, -0.20, 0.20, 0.36, 0.70, 'C1', 'tail1')          # root
    sym(0.46, 0.74, 0.20, 0.25, 0.40, 0.66, 'C3', 'tail1')
    span(0.46, 0.74, -0.16, 0.16, 0.70, 0.74, 'C2', 'tail1')
    span(0.74, 1.14, -0.31, 0.31, 0.44, 0.92, 'C1', 'tail2')          # fattest part
    sym(0.78, 1.10, 0.31, 0.35, 0.50, 0.86, 'C3', 'tail2')
    span(1.14, 1.20, -0.22, 0.22, 0.50, 0.86, 'C3', 'tail2')
    span(0.78, 1.10, -0.22, 0.22, 0.40, 0.44, 'C4', 'tail2')
    span(0.80, 1.12, -0.27, 0.27, 0.92, 1.06, 'C2', 'tail3')          # curl up
    span(0.80, 1.12, -0.27, 0.27, 1.06, 1.24, 'TB', 'tail3')          # blue tip
    sym(0.84, 1.08, 0.27, 0.30, 1.08, 1.22, 'TD', 'tail3')
    span(1.12, 1.15, -0.20, 0.20, 1.08, 1.22, 'TD', 'tail3')
    span(0.68, 0.80, -0.20, 0.20, 1.10, 1.24, 'TB', 'tail3')          # tip curls forward (hook)
    span(0.66, 0.68, -0.14, 0.14, 1.12, 1.22, 'TD', 'tail3')
    span(0.70, 0.80, -0.14, 0.14, 1.24, 1.28, 'TL', 'tail3')
    span(0.84, 1.08, -0.20, 0.20, 1.24, 1.32, 'TL', 'tail3')
    span(0.90, 1.02, -0.09, 0.09, 1.32, 1.37, 'TL', 'tail3')


def idle(f):
    ph = TAU * f / 90
    tw = max(0, S(TAU * f / 45) - 0.8) * 5               # quick ear twitch now and then
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 8 * S(TAU * f / 90 + 1.0), 8 * S(TAU * f / 180)),
            'ear.L': (0, -15 * tw, 0), 'ear.R': (0, 4 * S(ph * 2), 0),
            'tail1': (0, 0, 8 * S(ph)), 'tail2': (0, 0, 10 * S(ph - 0.6)), 'tail3': (0, 0, 12 * S(ph - 1.2))}


def hop(f):    # bouncy cub bound: all four paws push off together
    u = f / 24
    up = S(math.pi * u)
    sw = S(TAU * u)
    return {'body': (-8 * sw, 0, 0), 'head': (6 * sw, 0, 0),
            'leg.L': (-30 * sw, 0, 0), 'leg.R': (-30 * sw, 0, 0),
            'hind.L': (30 * sw, 0, 0), 'hind.R': (30 * sw, 0, 0),
            'ear.L': (8 * up, 0, 0), 'ear.R': (8 * up, 0, 0),
            'tail1': (-10 * up, 0, 6 * sw), 'tail2': (-6 * up, 0, 8 * S(TAU * u - 0.6)), 'tail3': (0, 0, 10 * S(TAU * u - 1.2)),
            'root_loc': (0, 0, 0.22 * up)}


def cheer(f):  # crouch, happy jump with a tail wag and head tilt, land and settle
    if f < 10: cr, up = EASE(f / 10), 0
    elif f < 26: u = (f - 10) / 16; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 34: cr, up = S(math.pi * (f - 26) / 8) * 0.7, 0
    else: cr, up = 0, 0
    wg = S(TAU * f / 9)
    env = S(math.pi * f / 36)
    return {'body': (8 * cr - 12 * up, 0, 0), 'head': (-6 * cr + 10 * up, 12 * env, 0), 'jaw': (14 * up, 0, 0),
            'leg.L': (-40 * up + 10 * cr, 0, 0), 'leg.R': (-40 * up + 10 * cr, 0, 0),
            'hind.L': (30 * up - 10 * cr, 0, 0), 'hind.R': (30 * up - 10 * cr, 0, 0),
            'ear.L': (-12 * cr, 0, 0), 'ear.R': (-12 * cr, 0, 0),
            'tail1': (-15 * up, 0, 22 * wg * env), 'tail2': (0, 0, 26 * S(TAU * f / 9 - 0.8) * env),
            'tail3': (0, 0, 30 * S(TAU * f / 9 - 1.6) * env),
            'root_loc': (0, 0, 0.55 * up - 0.06 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (36, cheer)}
PREVIEW = dict(target=(0, 0.1, 0.80), ortho=3.0, shots=[('Cheer', 18), ('Hop', 12)], loop='Idle')
