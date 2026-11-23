# Frost Mouse (Common, Fresh Snow): pale blue mouse with an icicle tail.
# Copied from the skill's red panda / bunny examples. Traits: big round ears (pink inside), pale blue fur with a
# white muzzle and belly, long pink feet, and a long thin tail that freezes into a jagged icicle (main spike + shards).
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'FrostMouse'
RARITY = 'Common'
STUDS = 5.0
# pale blue fur in 4 tones (C2 tops, C1 main, C3 sides, C4 underside) + white muzzle/belly, pink ears/feet,
# icy cyan icicle (IC main, ID dark facets, IT white tip), dark markings (DK)
PALETTE = dict(C1='d8e8fa', C2='f0f7ff', C3='b6cce8', C4='8ba6c9', CR='f6f9ff',
               PI='ffa9c0', PF='ffb6c6', PD='e0819a', NS='ff6f92', PK='ff9fb4', DK='34465f',
               IC='9fe4ff', ID='5cc2ee', IT='f2fdff',
               EY='1b2233', IR='3f78c0', WH='ffffff')
GLOW = set()
HP = (0, -0.28, 0.56)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.02, 0.28), (0, 0.02, 0.56), 'root'),
         ('head', HP, (0, -0.28, 0.92), 'body'),
         ('nose', (0, -0.62, 0.68), (0, -0.70, 0.68), 'head'),
         ('tail1', (0, 0.34, 0.22), (0, 0.64, 0.14), 'body'),
         ('tail2', (0, 0.64, 0.14), (0, 0.76, 0.40), 'tail1'),
         ('tail3', (0, 0.76, 0.40), (0, 0.90, 1.05), 'tail2')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{s}', (0.18 * sx, -0.40, 0.88), (0.30 * sx, -0.40, 1.12), 'head'),
              (f'leg.{s}', (0.13 * sx, -0.28, 0.20), (0.13 * sx, -0.28, 0.0), 'body'),
              (f'hind.{s}', (0.30 * sx, 0.16, 0.30), (0.30 * sx, 0.16, 0.0), 'body')]
HEAD = dict(scale=1.35, pivot=HP, bones=('head', 'nose', 'ear.L', 'ear.R'))


def build(K):
    span, sym = K.span, K.sym
    # body: low rounded loaf, white belly
    span(-0.24, 0.30, -0.22, 0.22, 0.06, 0.14, 'C4', 'body')
    span(-0.30, 0.36, -0.30, 0.30, 0.14, 0.50, 'C1', 'body')
    sym(-0.22, 0.30, 0.30, 0.33, 0.20, 0.44, 'C3', 'body')
    span(-0.24, 0.32, -0.24, 0.24, 0.50, 0.58, 'C1', 'body')
    span(-0.14, 0.26, -0.16, 0.16, 0.58, 0.62, 'C2', 'body')
    span(0.36, 0.39, -0.20, 0.20, 0.20, 0.44, 'C3', 'body')
    span(-0.34, -0.30, -0.18, 0.18, 0.16, 0.44, 'CR', 'body')       # white chest
    span(-0.36, -0.34, -0.11, 0.11, 0.20, 0.38, 'CR', 'body')
    # front legs: small, pink paws
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.34, -0.22, 0.07 * sx, 0.19 * sx, 0.04, 0.20, 'C1', b)
        span(-0.38, -0.22, 0.065 * sx, 0.195 * sx, 0.0, 0.04, 'PF', b)
        for dx in (0.11, 0.15):
            span(-0.385, -0.38, (dx - 0.006) * sx, (dx + 0.006) * sx, 0.0, 0.03, 'PD', b)
    # hind legs: round haunch + long pink mouse foot
    for sx, s in K.sides():
        b = f'hind.{s}'
        span(0.00, 0.30, 0.30 * sx, 0.38 * sx, 0.10, 0.36, 'C1', b)
        span(0.04, 0.26, 0.30 * sx, 0.36 * sx, 0.36, 0.40, 'C2', b)
        span(0.04, 0.26, 0.38 * sx, 0.40 * sx, 0.14, 0.32, 'C3', b)
        span(-0.20, 0.30, 0.22 * sx, 0.38 * sx, 0.0, 0.06, 'PF', b)
        span(-0.20, 0.30, 0.22 * sx, 0.38 * sx, 0.06, 0.10, 'C1', b)
        for dx in (0.26, 0.30, 0.34):
            span(-0.205, -0.20, (dx - 0.006) * sx, (dx + 0.006) * sx, 0.0, 0.04, 'PD', b)
    # head (scaled 1.35 around the neck): round, white pointy muzzle
    span(-0.36, -0.20, -0.18, 0.18, 0.50, 0.62, 'C1', 'head')
    span(-0.58, -0.22, -0.26, 0.26, 0.60, 0.86, 'C1', 'head')
    span(-0.56, -0.24, -0.22, 0.22, 0.86, 0.90, 'C1', 'head')
    span(-0.52, -0.28, -0.17, 0.17, 0.90, 0.93, 'C2', 'head')
    sym(-0.54, -0.26, 0.26, 0.29, 0.64, 0.82, 'C3', 'head')
    span(-0.54, -0.26, -0.20, 0.20, 0.57, 0.60, 'C4', 'head')
    span(-0.22, -0.19, -0.20, 0.20, 0.64, 0.84, 'C3', 'head')
    span(-0.66, -0.58, -0.15, 0.15, 0.60, 0.74, 'CR', 'head')       # muzzle
    span(-0.64, -0.58, -0.06, 0.06, 0.74, 0.77, 'CR', 'head')
    span(-0.65, -0.58, -0.15, 0.15, 0.585, 0.60, 'C4', 'head')
    for sx in (1, -1):
        for x, z in ((0.10, 0.70), (0.12, 0.665), (0.13, 0.70)):      # whisker dots
            span(-0.665, -0.66, (x - 0.008) * sx, (x + 0.008) * sx, z - 0.008, z + 0.008, 'DK', 'head')
        span(-0.60, -0.58, 0.06 * sx, 0.19 * sx, 0.76, 0.89, 'EY', 'head')
        span(-0.605, -0.60, 0.08 * sx, 0.16 * sx, 0.77, 0.83, 'IR', 'head')
        span(-0.61, -0.60, 0.13 * sx, 0.18 * sx, 0.84, 0.88, 'WH', 'head')
        span(-0.61, -0.60, 0.085 * sx, 0.105 * sx, 0.78, 0.80, 'WH', 'head')
        span(-0.595, -0.58, 0.19 * sx, 0.25 * sx, 0.68, 0.73, 'PK', 'head')   # blush
    span(-0.70, -0.66, -0.08, 0.08, 0.63, 0.71, 'CR', 'nose')
    span(-0.715, -0.70, -0.045, 0.045, 0.665, 0.72, 'NS', 'nose')
    span(-0.72, -0.715, -0.02, 0.02, 0.70, 0.712, 'WH', 'nose')
    span(-0.705, -0.70, -0.006, 0.006, 0.63, 0.665, 'DK', 'nose')
    # ears: big round discs, pink inside, dark rim at the back
    for sx, s in K.sides():
        b = f'ear.{s}'
        span(-0.44, -0.36, 0.16 * sx, 0.44 * sx, 0.92, 1.14, 'C1', b)
        span(-0.43, -0.37, 0.20 * sx, 0.40 * sx, 0.86, 1.20, 'C1', b)
        span(-0.42, -0.38, 0.23 * sx, 0.37 * sx, 1.20, 1.23, 'C2', b)
        span(-0.45, -0.44, 0.20 * sx, 0.40 * sx, 0.95, 1.11, 'PI', b)
        span(-0.45, -0.44, 0.24 * sx, 0.36 * sx, 0.91, 1.16, 'PI', b)
        span(-0.36, -0.35, 0.20 * sx, 0.40 * sx, 0.94, 1.12, 'C3', b)
    # tail: thin fur, then frost creeps up it and it ends in a jagged icicle
    K.limb((0, 0.34, 0.22), (0, 0.64, 0.14), 0.09, 0.09, 'C3', 'tail1', extend=0.04)
    K.limb((0, 0.62, 0.13), (0, 0.74, 0.36), 0.09, 0.09, 'C3', 'tail2', extend=0.04)
    K.limb((0, 0.70, 0.28), (0, 0.78, 0.44), 0.14, 0.14, 'ID', 'tail2')                   # frost collar
    span(0.71, 0.87, -0.11, 0.11, 0.42, 0.54, 'IC', 'tail3')                               # icicle base
    K.spike((0, 0.79, 0.50), (0, 0.22, 1), 0.78, 0.24, 'IC', 'IT', 'tail3')                # main icicle
    K.spike((0.08, 0.80, 0.56), (0.75, 0.25, 0.65), 0.36, 0.13, 'ID', 'IT', 'tail3')       # jagged shards
    K.spike((-0.08, 0.84, 0.72), (-0.75, 0.35, 0.6), 0.34, 0.12, 'ID', 'IT', 'tail3')
    K.spike((0, 0.90, 0.60), (0, 1, 0.45), 0.30, 0.12, 'IC', 'IT', 'tail3')
    K.spike((0.05, 0.92, 0.90), (0.6, 0.5, 0.6), 0.20, 0.09, 'ID', 'IT', 'tail3')


def idle(f):
    ph = TAU * f / 90
    tw = max(0, S(TAU * f / 30) - 0.6) * 2.5            # nose twitch bursts
    fl = max(0, S(TAU * f / 45 + 1) - 0.85) * 6.6        # quick left-ear flick
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 0, 7 * S(TAU * f / 180)),
            'nose': (8 * tw * S(TAU * f / 4), 0, 0),
            'ear.L': (0, -14 * fl, 0), 'ear.R': (0, -4 * S(ph + 1.2), 0),
            'tail1': (0, 0, 6 * S(ph)), 'tail2': (0, 0, 8 * S(ph - 0.6)), 'tail3': (0, 6 * S(ph - 1.2), 0)}


def hop(f):    # scurry: two quick little hops per loop, legs alternate, tail streams back
    ph = TAU * f / 12; up = abs(S(math.pi * f / 12))
    c = math.cos(ph)
    return {'body': (-4 * up + 2 * c, 0, 0), 'head': (3 * up, 0, 0),
            'leg.L': (-25 * c, 0, 0), 'leg.R': (-25 * c, 0, 0),
            'hind.L': (25 * c, 0, 0), 'hind.R': (25 * c, 0, 0),
            'ear.L': (0, 8 * up, 0), 'ear.R': (0, -8 * up, 0),
            'tail1': (-8 * up, 0, 0), 'tail2': (6 * up, 0, 0), 'tail3': (0, 8 * S(ph), 0),
            'root_loc': (0, 0, 0.14 * up)}


def cheer(f):  # crouch, leap with a full spin, land; ears up, icicle tail wags
    if f < 10: cr, up, sp = EASE(f / 10), 0, 0
    elif f < 28: u = (f - 10) / 18; cr, up, sp = 1 - EASE(min(u * 3, 1)), S(math.pi * u), EASE(u)
    elif f < 36: cr, up, sp = S(math.pi * (f - 28) / 8) * 0.8, 0, 1
    else: cr, up, sp = 0, 0, 1
    wag = 20 * S(TAU * f / 10) * (1 - cr)
    return {'body': (8 * cr - 12 * up, 0, 360 * sp if sp < 1 else 0), 'head': (-6 * cr + 10 * up, 0, 0),
            'leg.L': (-40 * up + 10 * cr, 0, 0), 'leg.R': (-40 * up + 10 * cr, 0, 0),
            'hind.L': (40 * up - 10 * cr, 0, 0), 'hind.R': (40 * up - 10 * cr, 0, 0),
            'ear.L': (0, 18 * up, 0), 'ear.R': (0, -18 * up, 0),
            'tail1': (-15 * up, 0, wag * 0.5), 'tail2': (0, 0, wag * 0.7), 'tail3': (0, wag, 0),
            'root_loc': (0, 0, 0.75 * up - 0.08 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (40, cheer)}
PREVIEW = dict(target=(0, 0.1, 0.75), ortho=2.8, shots=[('Cheer', 19), ('Hop', 6)], loop='Idle')
