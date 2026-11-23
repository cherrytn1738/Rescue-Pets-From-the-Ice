# Glacier Otter (Rare): otter floating on its back, holding a snowflake.
# Copied from the skill's axolotl example (low long body). Traits: a brown otter lying on its back with a cream
# belly on top, head raised to look forward (cream muzzle, dark nose, tiny ears), front paws holding up a big
# pale-blue snowflake (a flat star of boxes, thin bars glow softly), hind feet sticking up, a long flat tail.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'GlacierOtter'
RARITY = 'Rare'
STUDS = 5.0
# brown fur in 4 tones (C2 tops, C1 main, C3 sides, C4 underside) + cream belly/muzzle, dark paws, ice-blue flake
PALETTE = dict(C1='b07445', C2='cc9460', C3='925a33', C4='74462a', CR='f2dfbd', CL='fff1d8', MZ='f6e6c8',
               NS='2a1a14', DK='3a2418', PW='6b4228', PP='3a2418', ER='603a22',
               EY='1d1414', IR='7a5533', WH='ffffff', PK='ff9fae', SF='a8dcff', SC='e6f7ff')
GLOW = {'SF'}
HP = (0, -0.30, 0.30)          # head pivot (neck)
SH = (-0.16, 0.38)             # shoulder line (y, z): the arms and the snowflake turn round it together
FC = (0.0, -0.10, 1.02)        # snowflake centre
TILT = -30                     # snowflake tipped back toward the sky (degrees about X)
BONES = [('root', (0, 0, 0), (0, 0, 0.2), None),
         ('body', (0, 0.05, 0.22), (0, 0.05, 0.42), 'root'),
         ('head', HP, (0, -0.30, 0.70), 'body'),
         ('flake', (0, SH[0], SH[1]), FC, 'body'),
         ('tail1', (0, 0.40, 0.18), (0, 0.62, 0.18), 'body'),
         ('tail2', (0, 0.62, 0.18), (0, 0.86, 0.18), 'tail1')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'arm.{s}', (0.24 * sx, SH[0], SH[1]), (0.30 * sx, -0.10, 0.94), 'body'),
              (f'hind.{s}', (0.17 * sx, 0.30, 0.30), (0.19 * sx, 0.40, 0.56), 'body')]
HEAD = dict(scale=1.35, pivot=HP, bones=('head',))


def build(K):
    span, sym = K.span, K.sym
    # body lying on its back: dark back underneath, brown sides, cream belly on top
    span(-0.24, 0.34, -0.20, 0.20, 0.0, 0.10, 'C4', 'body')
    span(-0.32, 0.40, -0.28, 0.28, 0.10, 0.36, 'C1', 'body')
    sym(-0.26, 0.34, 0.28, 0.32, 0.14, 0.32, 'C3', 'body')
    span(-0.30, 0.38, -0.22, 0.22, 0.36, 0.42, 'CR', 'body')       # belly
    span(-0.20, 0.28, -0.15, 0.15, 0.42, 0.45, 'CL', 'body')       # belly top
    span(-0.30, 0.38, -0.282, 0.282, 0.30, 0.36, 'C2', 'body')     # light rim where the belly meets the sides
    # long flat tail out the back
    span(0.40, 0.62, -0.13, 0.13, 0.10, 0.26, 'C1', 'tail1')
    span(0.42, 0.60, -0.09, 0.09, 0.26, 0.28, 'C2', 'tail1')
    span(0.62, 0.84, -0.10, 0.10, 0.12, 0.24, 'C1', 'tail2')
    span(0.64, 0.82, -0.06, 0.06, 0.24, 0.26, 'C2', 'tail2')
    span(0.84, 0.92, -0.06, 0.06, 0.14, 0.22, 'C3', 'tail2')
    # hind feet sticking up at the back, dark webbed soles facing the sky
    for sx, s in K.sides():
        b = f'hind.{s}'
        K.limb((0.17 * sx, 0.28, 0.30), (0.19 * sx, 0.40, 0.54), 0.13, 0.13, 'C1', b)
        span(0.32, 0.50, 0.09 * sx, 0.29 * sx, 0.52, 0.60, 'PW', b)
        span(0.34, 0.48, 0.11 * sx, 0.27 * sx, 0.60, 0.61, 'PP', b)
        for dx in (0.13, 0.19, 0.25):                                   # toes
            span(0.30, 0.32, (dx - 0.022) * sx, (dx + 0.022) * sx, 0.53, 0.59, 'PW', b)
    # front paws reaching up to hold the snowflake
    for sx, s in K.sides():
        b = f'arm.{s}'
        K.limb((0.24 * sx, SH[0], SH[1]), (0.31 * sx, -0.11, 0.90), 0.13, 0.13, 'C1', b, extend=0.04)
        span(-0.17, -0.05, 0.22 * sx, 0.38 * sx, 0.90, 1.04, 'PW', b)  # paw gripping the flake's side
        span(-0.175, -0.17, 0.25 * sx, 0.35 * sx, 0.92, 1.02, 'PP', b)
    # the snowflake: three crossing bars + a tick near each tip + a centre plate, tipped back
    R0 = K.Euler((math.radians(TILT), 0, 0)).to_matrix()
    c = K.Vector(FC)
    for a in (0, 60, 120):
        Ra = R0 @ K.Euler((0, math.radians(a), 0)).to_matrix()
        K.box(c, (0.07, 0.05, 0.60), 'SF', 'flake', R=Ra)
        for t in (0.21, -0.21):                                        # ticks across each arm near the tip
            p = c + Ra @ K.Vector((0, 0, t))
            K.box(p, (0.16, 0.05, 0.05), 'SF', 'flake', R=Ra)
    K.box(c, (0.13, 0.07, 0.13), 'SC', 'flake', R=R0)
    # head (scaled 1.35 round the neck): raised, looking forward; brown top, cream lower face
    span(-0.56, -0.28, -0.24, 0.24, 0.28, 0.60, 'C1', 'head')       # skull
    span(-0.52, -0.32, -0.19, 0.19, 0.60, 0.64, 'C2', 'head')       # crown
    sym(-0.52, -0.32, 0.24, 0.27, 0.32, 0.56, 'C3', 'head')          # side step
    span(-0.57, -0.56, -0.22, 0.22, 0.29, 0.42, 'MZ', 'head')       # cream lower face
    sym(-0.52, -0.34, 0.27, 0.275, 0.30, 0.40, 'MZ', 'head')         # cream cheeks round the side
    span(-0.64, -0.56, -0.14, 0.14, 0.31, 0.43, 'MZ', 'head')       # muzzle
    span(-0.63, -0.56, -0.10, 0.10, 0.43, 0.45, 'MZ', 'head')
    span(-0.66, -0.64, -0.055, 0.055, 0.39, 0.44, 'NS', 'head')     # nose
    span(-0.665, -0.66, -0.035, -0.01, 0.425, 0.435, 'WH', 'head')
    span(-0.645, -0.64, -0.01, 0.01, 0.35, 0.39, 'NS', 'head')      # mouth
    sym(-0.645, -0.64, 0.01, 0.05, 0.34, 0.355, 'NS', 'head')
    for sx in (1, -1):
        for x, z in ((0.08, 0.40), (0.11, 0.37), (0.11, 0.42)):        # whisker dots
            span(-0.645, -0.64, (x - 0.008) * sx, (x + 0.008) * sx, z - 0.008, z + 0.008, 'DK', 'head')
        span(-0.58, -0.56, 0.06 * sx, 0.17 * sx, 0.46, 0.57, 'EY', 'head')
        span(-0.585, -0.58, 0.08 * sx, 0.14 * sx, 0.47, 0.52, 'IR', 'head')
        span(-0.59, -0.58, 0.12 * sx, 0.16 * sx, 0.525, 0.56, 'WH', 'head')
        span(-0.59, -0.58, 0.075 * sx, 0.095 * sx, 0.475, 0.495, 'WH', 'head')
        span(-0.575, -0.57, 0.16 * sx, 0.22 * sx, 0.40, 0.44, 'PK', 'head')
        span(-0.42, -0.34, 0.19 * sx, 0.27 * sx, 0.60, 0.65, 'C2', 'head')   # tiny round ears
        span(-0.425, -0.42, 0.21 * sx, 0.25 * sx, 0.61, 0.64, 'ER', 'head')


def hold(rx):   # arms and the snowflake turn together round the shoulder line
    return {'arm.L': (rx, 0, 0), 'arm.R': (rx, 0, 0), 'flake': (rx, 0, 0)}


def idle(f):    # floating: gentle rocking roll + pitch, bob, tail sways, feet paddle, flake lifted to admire
    ph = TAU * f / 90
    p = {'root': (2.5 * S(ph + 1.2), 4 * S(ph), 0), 'head': (-3 * S(ph + 0.6), -3 * S(ph), 5 * S(ph * 0.5)),
         'tail1': (0, 0, 8 * S(ph)), 'tail2': (0, 0, 10 * S(ph - 0.7)),
         'hind.L': (6 * S(ph * 2), 0, 0), 'hind.R': (-6 * S(ph * 2), 0, 0),
         'root_loc': (0, 0, 0.02 * S(ph + 0.5))}
    p.update(hold(-4 * S(ph * 2)))
    return p


def hop(f):     # back-scoot wiggle: body wiggles side to side, tail sweeps, feet kick in turn
    ph = TAU * f / 24
    p = {'root': (-3, 6 * S(ph), 0), 'body': (0, 0, 12 * S(ph)), 'head': (0, -4 * S(ph), -10 * S(ph)),
         'tail1': (0, 0, -16 * S(ph - 0.6)), 'tail2': (0, 0, -20 * S(ph - 1.2)),
         'hind.L': (20 * S(ph), 0, 0), 'hind.R': (-20 * S(ph), 0, 0),
         'root_loc': (0, 0, 0.05 * abs(S(ph)))}
    p.update(hold(-6 * abs(S(ph))))
    return p


def cheer(f):   # bounce up and spin round once on its back, flake raised high, feet kicking
    L = 36
    up = S(math.pi * min(1, f / 28))
    spin = 360 * EASE(min(1, f / 28))
    k = 25 * S(TAU * f / 8) * up
    p = {'root': (-6 * up, 0, spin), 'head': (8 * up, 0, 0),
         'tail1': (-20 * up, 0, 12 * S(TAU * f / 12)), 'tail2': (-15 * up, 0, 14 * S(TAU * f / 12 - 1)),
         'hind.L': (k, 0, 0), 'hind.R': (-k, 0, 0),
         'root_loc': (0, 0, 0.35 * up)}
    p.update(hold(-30 * up))
    return p


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (36, cheer)}
PREVIEW = dict(target=(0, 0.05, 0.60), ortho=3.0, shots=[('Cheer', 10), ('Hop', 6)], loop='Idle')
