# Aurora Fox (Mythic): fox whose tail ripples with northern lights.
# Copied from the skill's arctic fox example. Traits: an elegant long-legged fox in deep night blue/violet
# with pale markings (chest ruff, muzzle, cheeks, socks, ear tips, star freckles) and a huge S-curled tail
# on a 4-bone chain, banded violet, pink, teal and green; two thin rings and the tip glow. Idle ripples it.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'AuroraFox'
RARITY = 'Mythic'
STUDS = 5.0
# night-blue fur in 4 tones (C2 tops, C1 main, C3 sides, C4 underside) + pale markings + aurora bands
PALETTE = dict(C1='413fa2', C2='6462d0', C3='333188', C4='252466', PM='e9edff', P2='c3c9f2', ST='fff3c4',
               AV='b56cff', VD='8247d6', AP='ff70cf', PD2='cf47a6', AT='2fdfe0', TD='1fa3b3',
               AG='45f59e', GD='22b874', AW='d6fff0', GP='ffa3e4', GG='8dffc8',
               EY='151838', IR='5ff0d0', WH='ffffff', NS='10122b', PK='ff9fc8', PI='e7a8ff', PD='8a90c8')
GLOW = {'GP', 'GG'}
HP = (0, -0.40, 0.86)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.05, 0.56), (0, 0.05, 0.86), 'root'),
         ('head', HP, (0, -0.40, 1.26), 'body'),
         ('jaw', (0, -0.78, 0.88), (0, -0.92, 0.86), 'head'),
         ('tail1', (0, 0.44, 0.74), (0, 0.78, 0.82), 'body'),
         ('tail2', (0, 0.78, 0.82), (0, 1.02, 1.20), 'tail1'),
         ('tail3', (0, 1.02, 1.20), (0, 1.02, 1.54), 'tail2'),
         ('tail4', (0, 1.02, 1.58), (0, 0.62, 1.66), 'tail3')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{s}', (0.21 * sx, -0.55, 1.28), (0.24 * sx, -0.55, 1.56), 'head'),
              (f'leg.{s}', (0.165 * sx, -0.24, 0.44), (0.165 * sx, -0.24, 0.0), 'body'),
              (f'hind.{s}', (0.165 * sx, 0.30, 0.44), (0.165 * sx, 0.30, 0.0), 'body')]
HEAD = dict(scale=1.3, pivot=HP, bones=('head', 'jaw', 'ear.L', 'ear.R'))


def build(K):
    span, sym = K.span, K.sym

    def hs(y0, y1, x0, x1, z0, z1, k, b='head'):   # head parts drawn in the example's coordinates
        span(y0, y1, x0, x1, z0 + 0.06, z1 + 0.06, k, b)

    # body: sleek loaf, raised on long legs
    span(-0.30, 0.40, -0.22, 0.22, 0.36, 0.42, 'C4', 'body')        # belly
    span(-0.36, 0.46, -0.29, 0.29, 0.42, 0.78, 'C1', 'body')        # core
    sym(-0.28, 0.38, 0.29, 0.33, 0.48, 0.72, 'C3', 'body')          # side step
    span(-0.30, 0.40, -0.23, 0.23, 0.78, 0.84, 'C2', 'body')        # back
    span(-0.16, 0.30, -0.13, 0.13, 0.84, 0.87, 'C2', 'body')        # back cap
    # pale chest ruff
    span(-0.46, -0.36, -0.26, 0.26, 0.46, 0.84, 'PM', 'body')
    span(-0.52, -0.46, -0.17, 0.17, 0.52, 0.76, 'PM', 'body')
    span(-0.55, -0.52, -0.08, 0.08, 0.56, 0.68, 'P2', 'body')
    # star freckles on the flanks
    sym(0.00, 0.06, 0.33, 0.335, 0.62, 0.68, 'ST', 'body')
    sym(0.14, 0.18, 0.33, 0.335, 0.54, 0.58, 'ST', 'body')
    sym(-0.12, -0.09, 0.33, 0.335, 0.56, 0.59, 'ST', 'body')
    # legs: long and slender, pale socks
    for sx, s in K.sides():
        for b, y0, y1 in ((f'leg.{s}', -0.30, -0.18), (f'hind.{s}', 0.24, 0.36)):
            span(y0, y1, 0.10 * sx, 0.23 * sx, 0.10, 0.44, 'C1', b)
            span(y0 - 0.01, y1 + 0.01, 0.095 * sx, 0.235 * sx, 0.05, 0.10, 'P2', b)
            span(y0 - 0.04, y1 + 0.02, 0.09 * sx, 0.24 * sx, 0.0, 0.05, 'PM', b)
            span(y0 - 0.05, y0 - 0.04, 0.159 * sx, 0.171 * sx, 0.0, 0.04, 'PD', b)   # toe groove
        span(0.16, 0.44, 0.29 * sx, 0.35 * sx, 0.44, 0.68, 'C3', f'hind.{s}')   # haunch
    # head (scaled 1.3 around the neck)
    hs(-0.52, -0.36, -0.20, 0.20, 0.74, 0.86, 'C1')                 # neck
    hs(-0.78, -0.34, -0.29, 0.29, 0.80, 1.20, 'C1')                 # skull
    hs(-0.72, -0.40, -0.23, 0.23, 1.20, 1.26, 'C2')                 # crown
    hs(-0.785, -0.78, -0.03, 0.03, 1.14, 1.20, 'AT')                # little teal star on the brow
    hs(-0.785, -0.78, -0.06, 0.06, 1.16, 1.18, 'AT')
    sym(-0.72, -0.44, 0.29, 0.33, 0.82 + 0.06, 1.00 + 0.06, 'PM', 'head')   # pale cheek ruff
    sym(-0.66, -0.52, 0.33, 0.37, 0.82 + 0.06, 0.92 + 0.06, 'P2', 'head')   # cheek tuft
    hs(-0.94, -0.78, -0.14, 0.14, 0.84, 0.97, 'PM')                 # pale muzzle
    hs(-0.92, -0.78, -0.10, 0.10, 0.97, 1.00, 'C2')                 # muzzle top
    hs(-1.04, -0.94, -0.08, 0.08, 0.85, 0.95, 'PM')                 # muzzle tip
    hs(-1.07, -1.04, -0.05, 0.05, 0.89, 0.95, 'NS')                 # nose
    hs(-0.98, -0.78, -0.10, 0.10, 0.79, 0.84, 'P2', 'jaw')          # lower jaw
    hs(-0.94, -0.80, -0.06, 0.06, 0.84, 0.845, 'PK', 'jaw')         # mouth
    for sx in (1, -1):   # eyes: dark block, aurora-teal iris, 2 shines
        hs(-0.80, -0.78, 0.09 * sx, 0.23 * sx, 1.00, 1.14, 'EY')
        hs(-0.805, -0.80, 0.12 * sx, 0.20 * sx, 1.01, 1.07, 'IR')
        hs(-0.81, -0.80, 0.16 * sx, 0.21 * sx, 1.09, 1.13, 'WH')
        hs(-0.81, -0.80, 0.115 * sx, 0.135 * sx, 1.025, 1.045, 'WH')
        hs(-0.795, -0.78, 0.23 * sx, 0.28 * sx, 0.92, 0.97, 'PK')   # blush
    # ears: tall stepped triangles, lavender inside, pale tips
    for sx, s in K.sides():
        b = f'ear.{s}'
        rows = ((0.06, 0.36, 1.22, 1.30), (0.10, 0.36, 1.30, 1.38), (0.15, 0.35, 1.38, 1.46),
                (0.20, 0.34, 1.46, 1.53), (0.25, 0.33, 1.53, 1.58))
        for i, (x0, x1, z0, z1) in enumerate(rows):
            hs(-0.60, -0.48, x0 * sx, x1 * sx, z0, z1, ('C1', 'C1', 'C2', 'PM', 'PM')[i], b)
        for x0, x1, z0, z1 in ((0.12, 0.30, 1.24, 1.32), (0.16, 0.30, 1.32, 1.40), (0.21, 0.30, 1.40, 1.46)):
            hs(-0.615, -0.60, x0 * sx, x1 * sx, z0, z1, 'PI', b)
    # tail: the hero piece. 4 bones in an S curl, banded violet -> pink -> teal -> green, glowing rings + tip
    span(0.44, 0.68, -0.17, 0.17, 0.62, 0.90, 'C1', 'tail1')          # root, body colour
    sym(0.48, 0.66, 0.17, 0.21, 0.66, 0.86, 'C3', 'tail1')
    span(0.68, 0.80, -0.21, 0.21, 0.60, 0.94, 'AV', 'tail1')          # violet band
    sym(0.70, 0.78, 0.21, 0.24, 0.64, 0.90, 'VD', 'tail1')
    span(0.80, 0.90, -0.29, 0.29, 0.70, 1.22, 'AV', 'tail2')          # fattest: violet
    span(0.90, 0.93, -0.30, 0.30, 0.69, 1.23, 'GP', 'tail2')          # glowing pink ring
    span(0.93, 1.16, -0.29, 0.29, 0.70, 1.22, 'AP', 'tail2')          # pink
    sym(0.82, 0.90, 0.29, 0.33, 0.76, 1.16, 'VD', 'tail2')
    sym(0.93, 1.12, 0.29, 0.33, 0.76, 1.16, 'PD2', 'tail2')
    span(1.16, 1.20, -0.21, 0.21, 0.78, 1.14, 'PD2', 'tail2')
    span(0.84, 1.12, -0.21, 0.21, 0.66, 0.70, 'PD2', 'tail2')
    span(0.84, 1.18, -0.28, 0.28, 1.22, 1.42, 'AT', 'tail3')          # teal, rising
    sym(0.88, 1.14, 0.28, 0.32, 1.24, 1.40, 'TD', 'tail3')
    span(1.18, 1.21, -0.20, 0.20, 1.24, 1.40, 'TD', 'tail3')
    span(0.83, 1.19, -0.29, 0.29, 1.42, 1.45, 'GG', 'tail3')          # glowing green ring
    span(0.84, 1.18, -0.28, 0.28, 1.45, 1.58, 'AG', 'tail3')          # green
    sym(0.88, 1.14, 0.28, 0.31, 1.46, 1.56, 'GD', 'tail3')
    span(0.70, 1.14, -0.23, 0.23, 1.58, 1.74, 'AG', 'tail4')          # tip curls forward over the back
    sym(0.74, 1.10, 0.23, 0.26, 1.60, 1.72, 'GD', 'tail4')
    span(0.74, 1.08, -0.16, 0.16, 1.74, 1.79, 'AW', 'tail4')
    span(0.56, 0.70, -0.18, 0.18, 1.50, 1.70, 'AW', 'tail4')          # pale tip hooks down
    span(0.53, 0.56, -0.08, 0.08, 1.56, 1.64, 'GG', 'tail4')          # glowing tip spark


def idle(f):     # breathing, slow head turn, and the tail ripples: each link lags the one before
    ph = TAU * f / 90
    tw = max(0, S(TAU * f / 45) - 0.8) * 5
    d = {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 0, 8 * S(ph)),
         'ear.L': (0, -12 * tw, 0), 'ear.R': (0, 4 * S(ph * 2), 0)}
    for i in range(4):
        d[f'tail{i + 1}'] = (5 * S(ph * 2 - 0.9 * i), 4 * S(ph - 0.7 * i), 9 * S(ph - 0.8 * i))
    return d


def hop(f):      # light prancing trot; the tail streams and waves behind
    ph = TAU * f / 12; c = math.cos(ph)
    a = 32 * S(ph)
    d = {'leg.L': (-a, 0, 0), 'hind.R': (-a, 0, 0), 'leg.R': (a, 0, 0), 'hind.L': (a, 0, 0),
         'body': (0, 3 * c, 2 * S(ph)), 'head': (-3 * abs(S(ph)), -3 * c, -2 * S(ph)),
         'ear.L': (5 * abs(c), 0, 0), 'ear.R': (5 * abs(c), 0, 0),
         'root_loc': (0, 0, 0.06 * abs(S(ph)))}
    for i in range(4):
        d[f'tail{i + 1}'] = (6 if i == 0 else 4 * S(ph - 0.8 * i), 0, 9 * S(TAU * f / 24 - 0.9 * i))
    return d


def cheer(f):    # crouch, leap into a full twirl with the tail swirling, land and settle
    if f < 8: cr, up = EASE(f / 8), 0
    elif f < 28: u = (f - 8) / 20; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 36: cr, up = S(math.pi * (f - 28) / 8) * 0.7, 0
    else: cr, up = 0, 0
    spin = 360 * EASE(min(max(f - 8, 0) / 20, 1))
    d = {'root': (0, 0, spin), 'body': (8 * cr - 10 * up, 0, 0), 'head': (-6 * cr + 12 * up, 0, 0), 'jaw': (12 * up, 0, 0),
         'leg.L': (-35 * up + 10 * cr, 0, 0), 'leg.R': (-35 * up + 10 * cr, 0, 0),
         'hind.L': (30 * up - 10 * cr, 0, 0), 'hind.R': (30 * up - 10 * cr, 0, 0),
         'ear.L': (-12 * cr, 0, 0), 'ear.R': (-12 * cr, 0, 0),
         'root_loc': (0, 0, 0.6 * up - 0.08 * cr)}
    env = S(math.pi * f / 40)
    for i in range(4):
        d[f'tail{i + 1}'] = (-8 * up, 0, -18 * up + 16 * env * S(TAU * f / 12 - 0.9 * i))
    return d


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (40, cheer)}
PREVIEW = dict(target=(0, 0.2, 0.95), ortho=3.6, shots=[('Cheer', 15), ('Hop', 3)], loop='Idle')
