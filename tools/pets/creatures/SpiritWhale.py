# Spirit Whale (Mythic, Primordial Ice): small floating whale made of aurora light.
# Copied from the skill's axolotl example. Traits: a chubby deep-blue whale that hovers (lowest point about
# 0.25 m up), wavy aurora stripes along each side (teal and green glow, violet and pink don't), a pale belly,
# a tail that sweeps up into big flukes with glowing tips, round pectoral fins, a small dorsal fin and a few
# glowing star specks on its back.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'SpiritWhale'
RARITY = 'Mythic'
STUDS = 5.0
# deep blue in 4 tones (B2 tops, B1 main, B3 sides, B4 dark under-edges) + pale belly (WB/WD pleats)
# + aurora (GT teal and GG green glow, AV violet and AP pink plain) + star specks (ST glow)
PALETTE = dict(B1='2f4fb8', B2='4a6fd6', B3='243f97', B4='182b6b', WB='cfe3ff', WD='9fbde8',
               GT='3ff2d8', GG='7dff8a', AV='c08cff', AP='ff7fd0', ST='e9fbff',
               EY='121630', IR='3a8cff', WH='ffffff', MO='121630', PK='ff8fc0')
GLOW = {'GT', 'GG', 'ST'}
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, -0.05, 0.64), (0, -0.05, 0.94), 'root'),
         ('tail1', (0, 0.30, 0.64), (0, 0.56, 0.72), 'body'),
         ('tail2', (0, 0.56, 0.72), (0, 0.74, 0.92), 'tail1'),
         ('tail3', (0, 0.74, 0.92), (0, 0.94, 1.12), 'tail2')]
for _s, _sx in (('L', 1), ('R', -1)):
    BONES += [(f'fin.{_s}', (0.42 * _sx, -0.20, 0.50), (0.72 * _sx, -0.16, 0.40), 'body')]
HEAD = None


def build(K):
    span, sym = K.span, K.sym
    # body: chubby stepped bean, big round front (the whale's "head")
    span(-0.40, 0.20, -0.24, 0.24, 0.26, 0.33, 'WB', 'body')        # pale belly
    span(-0.48, 0.28, -0.32, 0.32, 0.33, 0.42, 'B1', 'body')        # lower core
    span(-0.52, 0.32, -0.38, 0.38, 0.42, 0.86, 'B1', 'body')        # core
    sym(-0.46, 0.26, 0.38, 0.42, 0.48, 0.80, 'B3', 'body')           # side step
    span(-0.48, 0.28, -0.32, 0.32, 0.86, 0.96, 'B1', 'body')        # upper core
    span(-0.40, 0.20, -0.24, 0.24, 0.96, 1.01, 'B2', 'body')        # back
    span(-0.57, -0.52, -0.32, 0.32, 0.46, 0.84, 'B1', 'body')       # rounded front plate
    span(-0.56, -0.48, -0.26, 0.26, 0.36, 0.46, 'WB', 'body')       # pale throat
    for x in (-0.12, 0.0, 0.12):                                     # throat pleats
        span(-0.565, -0.56, x - 0.012, x + 0.012, 0.37, 0.45, 'WD', 'body')
    # aurora ribbons: four bands flowing together in a wave down each flank
    wave = ((-0.44, -0.26, 0.0), (-0.26, -0.08, 0.035), (-0.08, 0.10, 0.01), (0.10, 0.26, -0.02))
    for sx in (1, -1):
        for k, z in (('GT', 0.71), ('AV', 0.64), ('GG', 0.57), ('AP', 0.50)):
            for y0, y1, dz in wave:
                span(y0, y1, 0.42 * sx, 0.43 * sx, z + dz, z + dz + 0.05, k, 'body')
    # glowing star specks on the back
    for y, x in ((-0.30, 0.12), (-0.14, -0.14), (0.04, 0.08), (0.14, -0.10)):
        span(y - 0.025, y + 0.025, x - 0.025, x + 0.025, 1.01, 1.025, 'ST', 'body')
    # dorsal fin
    span(0.00, 0.18, -0.04, 0.04, 1.01, 1.07, 'B2', 'body')
    span(0.08, 0.18, -0.035, 0.035, 1.07, 1.11, 'B3', 'body')
    # face on the front plate (y -0.57): big eyes, smile, blush
    span(-0.575, -0.57, -0.12, 0.12, 0.52, 0.54, 'MO', 'body')
    sym(-0.575, -0.57, 0.12, 0.16, 0.54, 0.56, 'MO', 'body')
    for sx in (1, -1):
        span(-0.58, -0.57, 0.09 * sx, 0.25 * sx, 0.62, 0.78, 'EY', 'body')
        span(-0.585, -0.58, 0.11 * sx, 0.21 * sx, 0.63, 0.70, 'IR', 'body')
        span(-0.59, -0.58, 0.16 * sx, 0.23 * sx, 0.72, 0.76, 'WH', 'body')
        span(-0.59, -0.58, 0.11 * sx, 0.135 * sx, 0.645, 0.67, 'WH', 'body')
        span(-0.575, -0.57, 0.23 * sx, 0.30 * sx, 0.55, 0.60, 'PK', 'body')
    # pectoral fins: big round paddles out and slightly down
    for sx, s in K.sides():
        b = f'fin.{s}'
        span(-0.32, -0.06, 0.42 * sx, 0.56 * sx, 0.44, 0.52, 'B3', b)
        span(-0.30, -0.06, 0.56 * sx, 0.68 * sx, 0.40, 0.48, 'B3', b)
        span(-0.26, -0.08, 0.68 * sx, 0.75 * sx, 0.37, 0.44, 'B4', b)
        span(-0.28, -0.08, 0.44 * sx, 0.64 * sx, 0.52, 0.54, 'B2', b)
    # tail: stalk sweeping up into big flukes with glowing tips
    span(0.32, 0.56, -0.24, 0.24, 0.46, 0.86, 'B1', 'tail1')
    span(0.32, 0.52, -0.16, 0.16, 0.86, 0.90, 'B2', 'tail1')
    span(0.32, 0.52, -0.16, 0.16, 0.43, 0.46, 'WB', 'tail1')
    sym(0.32, 0.54, 0.24, 0.25, 0.72, 0.77, 'GT', 'tail1')          # the top aurora band runs onto the tail
    span(0.56, 0.74, -0.15, 0.15, 0.62, 0.94, 'B1', 'tail2')
    sym(0.56, 0.72, 0.15, 0.16, 0.80, 0.84, 'GT', 'tail2')
    span(0.70, 0.86, -0.11, 0.11, 0.90, 1.10, 'B3', 'tail3')        # hub
    for sx in (1, -1):
        span(0.74, 0.92, 0.10 * sx, 0.30 * sx, 0.98, 1.10, 'B1', 'tail3')
        span(0.82, 1.00, 0.28 * sx, 0.46 * sx, 1.04, 1.16, 'B1', 'tail3')
        span(0.76, 0.90, 0.12 * sx, 0.28 * sx, 1.10, 1.12, 'B2', 'tail3')
        span(0.90, 1.04, 0.44 * sx, 0.56 * sx, 1.10, 1.20, 'GT', 'tail3')   # glowing fluke tips
        span(0.92, 0.96, 0.12 * sx, 0.28 * sx, 1.00, 1.08, 'AV', 'tail3')   # violet trailing edge


def idle(f):   # slow float bob, tail sways, fins paddle
    ph = TAU * f / 90
    return {'body': (2.5 * S(ph), 0, 0),
            'tail1': (-6 * S(ph - 0.6), 0, 5 * S(ph)), 'tail2': (-8 * S(ph - 1.2), 0, 6 * S(ph - 0.6)),
            'tail3': (-10 * S(ph - 1.8), 0, 7 * S(ph - 1.2)),
            'fin.L': (0, 12 * S(ph * 2), 0), 'fin.R': (0, -12 * S(ph * 2), 0),
            'root_loc': (0, 0, 0.04 * S(ph))}


def hop(f):    # swim: up-and-down undulation through the body and tail, fins stroke
    ph = TAU * f / 24
    return {'body': (5 * S(ph), 0, 0),
            'tail1': (-12 * S(ph - 0.8), 0, 0), 'tail2': (-16 * S(ph - 1.6), 0, 0), 'tail3': (-20 * S(ph - 2.4), 0, 0),
            'fin.L': (0, 18 * S(ph), 0), 'fin.R': (0, -18 * S(ph), 0),
            'root_loc': (0, 0, 0.06 * S(ph + 0.6))}


def cheer(f):  # rise up and spin round once, tail slaps down in a splash at the end
    L = 36
    t = EASE(max(0, min(f / 6, 1, (L - f) / 6)))
    spin = 360 * EASE(min(f / 26, 1))
    slap = S(math.pi * max(0, min((f - 24) / 10, 1))) if f >= 24 else 0
    return {'body': (-10 * t + 8 * slap, 0, 0),
            'tail1': (14 * t - 30 * slap, 0, 0), 'tail2': (16 * t - 34 * slap, 0, 0), 'tail3': (18 * t - 40 * slap, 0, 0),
            'fin.L': (0, 30 * t * S(TAU * f / 9), 0), 'fin.R': (0, -30 * t * S(TAU * f / 9), 0),
            'root': (0, 0, spin % 360),
            'root_loc': (0, 0, 0.30 * S(math.pi * min(f / 28, 1)))}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (36, cheer)}
PREVIEW = dict(target=(0, 0.22, 0.72), ortho=2.8, shots=[('Cheer', 14), ('Hop', 6)], loop='Idle')
