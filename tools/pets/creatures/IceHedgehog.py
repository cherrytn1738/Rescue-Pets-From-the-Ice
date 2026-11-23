# Ice Hedgehog (Uncommon): hedgehog whose spikes are icicles.
# Copied from the skill's red panda example. Traits: a round little body on stubby legs, a brown head with a cream
# face, pointed snout and big black nose, and a clear icy-blue quill coat whose chunky icicle spikes point back and up
# (a fringe of smaller icicles on the crown), so the outline is spiky from every side.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'IceHedgehog'
RARITY = 'Uncommon'
STUDS = 5.0
# icy quill coat in 4 tones (C2 tops, C1 main, C3 sides, C4 dark base) + white icicle tips (IT),
# brown fur (B1 main, B2 light, B3 side, B4 underside), cream face (CF, CS), pink feet/ears/blush
PALETTE = dict(C1='a8e4fb', C2='d6f5ff', C3='7ccbee', C4='4f9fd0', IT='f4fdff',
               B1='a8754c', B2='c79566', B3='86583a', B4='5e3b26',
               CF='f6e4c6', CS='e2c79f', PF='e9a78f', PI='ff9fb4', PK='ff8fa8', NS='22160f', DK='3a2418',
               EY='1b1512', IR='6b4a30', WH='ffffff')
GLOW = set()
HP = (0, -0.26, 0.34)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.06, 0.20), (0, 0.06, 0.56), 'root'),
         ('head', HP, (0, -0.26, 0.62), 'body'),
         ('nose', (0, -0.56, 0.32), (0, -0.68, 0.32), 'head')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{s}', (0.18 * sx, -0.38, 0.50), (0.22 * sx, -0.38, 0.58), 'head'),
              (f'leg.{s}', (0.18 * sx, -0.18, 0.14), (0.18 * sx, -0.18, 0.0), 'body'),
              (f'hind.{s}', (0.18 * sx, 0.26, 0.14), (0.18 * sx, 0.26, 0.0), 'body')]
HEAD = dict(scale=1.5, pivot=HP, bones=('head', 'nose', 'ear.L', 'ear.R'))

# icicle quills on the coat: (x, y, z, direction, length, width, colour). All lean back and up; the
# outer ones splay outward. Mirrored when x != 0.
QUILLS = [(0.00, -0.12, 0.58, (0, 0.55, 0.85), 0.34, 0.15, 'C1'),
          (0.16, -0.10, 0.54, (0.30, 0.55, 0.80), 0.30, 0.14, 'C2'),
          (0.00, 0.06, 0.60, (0, 0.70, 0.75), 0.38, 0.16, 'C2'),
          (0.17, 0.06, 0.56, (0.35, 0.65, 0.70), 0.34, 0.15, 'C1'),
          (0.30, 0.04, 0.44, (0.75, 0.50, 0.45), 0.30, 0.14, 'C2'),
          (0.00, 0.22, 0.58, (0, 0.85, 0.55), 0.38, 0.16, 'C1'),
          (0.17, 0.22, 0.54, (0.35, 0.80, 0.50), 0.34, 0.15, 'C2'),
          (0.30, 0.22, 0.40, (0.75, 0.60, 0.30), 0.30, 0.14, 'C1'),
          (0.10, 0.36, 0.48, (0.20, 0.95, 0.30), 0.32, 0.14, 'C2'),
          (0.27, 0.34, 0.36, (0.55, 0.80, 0.15), 0.28, 0.13, 'C1')]


def build(K):
    span, sym = K.span, K.sym
    # body: brown under-body, the coat overhangs it like a skirt
    span(-0.20, 0.32, -0.22, 0.22, 0.04, 0.10, 'B4', 'body')
    span(-0.26, 0.38, -0.28, 0.28, 0.10, 0.30, 'B1', 'body')
    sym(-0.20, 0.32, 0.28, 0.30, 0.12, 0.26, 'B3', 'body')
    span(-0.30, -0.26, -0.18, 0.18, 0.12, 0.28, 'CS', 'body')        # cream chest
    # the icy quill coat: stepped dome
    span(-0.24, 0.40, -0.34, 0.34, 0.26, 0.46, 'C1', 'body')
    sym(-0.18, 0.36, 0.34, 0.37, 0.28, 0.42, 'C3', 'body')
    span(0.40, 0.44, -0.26, 0.26, 0.28, 0.44, 'C3', 'body')
    span(-0.20, 0.36, -0.28, 0.28, 0.46, 0.56, 'C1', 'body')
    span(-0.12, 0.28, -0.18, 0.18, 0.56, 0.61, 'C2', 'body')
    span(-0.22, 0.42, -0.30, 0.30, 0.24, 0.26, 'C4', 'body')         # dark coat rim
    for x, y, z, d, L, w, k in QUILLS:
        for sx in ((1, -1) if x else (1,)):
            K.spike((x * sx, y, z), (d[0] * sx, d[1], d[2]), L, w, k, 'IT', 'body')
    # stubby legs, pinkish-tan feet
    for sx, s in K.sides():
        for b, y0, y1 in ((f'leg.{s}', -0.24, -0.12), (f'hind.{s}', 0.20, 0.32)):
            span(y0, y1, 0.12 * sx, 0.24 * sx, 0.04, 0.14, 'B3', b)
            span(y0 - 0.04, y1, 0.115 * sx, 0.245 * sx, 0.0, 0.04, 'PF', b)
            for dx in (0.15, 0.21):
                span(y0 - 0.045, y0 - 0.04, (dx - 0.006) * sx, (dx + 0.006) * sx, 0.0, 0.03, 'DK', b)
    # head (scaled 1.3 around the neck): brown top and back, cream face, pointed snout
    span(-0.30, -0.20, -0.18, 0.18, 0.18, 0.44, 'B1', 'head')
    span(-0.50, -0.24, -0.23, 0.23, 0.18, 0.48, 'B1', 'head')
    span(-0.48, -0.26, -0.19, 0.19, 0.48, 0.52, 'B2', 'head')
    sym(-0.48, -0.28, 0.23, 0.25, 0.22, 0.44, 'B3', 'head')
    span(-0.52, -0.50, -0.22, 0.22, 0.19, 0.44, 'CF', 'head')        # cream face plate
    span(-0.52, -0.50, -0.14, 0.14, 0.44, 0.47, 'CF', 'head')
    span(-0.48, -0.28, -0.18, 0.18, 0.16, 0.18, 'CS', 'head')        # chin
    sym(-0.50, -0.40, 0.25, 0.26, 0.22, 0.36, 'CF', 'head')           # cream cheeks wrap the side
    span(-0.60, -0.52, -0.12, 0.12, 0.20, 0.34, 'CF', 'head')        # snout
    span(-0.58, -0.52, -0.08, 0.08, 0.34, 0.37, 'CF', 'head')
    span(-0.60, -0.52, -0.10, 0.10, 0.19, 0.20, 'CS', 'head')
    for sx in (1, -1):
        span(-0.53, -0.52, 0.05 * sx, 0.17 * sx, 0.34, 0.46, 'EY', 'head')
        span(-0.535, -0.53, 0.07 * sx, 0.14 * sx, 0.35, 0.40, 'IR', 'head')
        span(-0.54, -0.53, 0.115 * sx, 0.16 * sx, 0.41, 0.45, 'WH', 'head')
        span(-0.54, -0.53, 0.075 * sx, 0.095 * sx, 0.36, 0.38, 'WH', 'head')
        span(-0.525, -0.52, 0.16 * sx, 0.22 * sx, 0.26, 0.31, 'PK', 'head')   # blush
    span(-0.605, -0.60, -0.005, 0.005, 0.21, 0.25, 'DK', 'head')    # mouth
    span(-0.66, -0.60, -0.06, 0.06, 0.27, 0.35, 'NS', 'nose')       # big black nose button
    span(-0.665, -0.66, -0.03, 0.0, 0.31, 0.34, 'WH', 'nose')
    # crown fringe: small icicles on the forehead leaning back
    for x, z, k in ((0.0, 0.52, 'C2'), (0.12, 0.50, 'C1'), (-0.12, 0.50, 'C1')):
        K.spike((x, -0.36, z), (x * 1.5, 0.6, 0.8), 0.20, 0.10, k, 'IT', 'head')
    # small round ears peeking out beside the fringe
    for sx, s in K.sides():
        b = f'ear.{s}'
        span(-0.42, -0.36, 0.15 * sx, 0.27 * sx, 0.46, 0.56, 'B1', b)
        span(-0.41, -0.37, 0.17 * sx, 0.25 * sx, 0.56, 0.59, 'B2', b)
        span(-0.425, -0.42, 0.17 * sx, 0.25 * sx, 0.48, 0.55, 'PI', b)


def idle(f):
    ph = TAU * f / 90
    sn = max(0, S(TAU * f / 30) - 0.5) * 2           # sniffing bursts
    return {'body': (1.5 * S(ph), 0, 1.5 * S(ph * 0.5)), 'head': (-3 * S(ph + 0.6), 0, 9 * S(TAU * f / 180)),
            'nose': (10 * sn * S(TAU * f / 4), 0, 0),
            'ear.L': (0, 5 * S(ph + 0.4), 0), 'ear.R': (0, -5 * S(ph + 1.2), 0),
            'root_loc': (0, 0, 0.008 * (1 + S(ph)))}


def hop(f):    # quick little scurry: two bounces per loop with a side-to-side rock, legs patter
    ph = TAU * f / 12; up = abs(S(math.pi * f / 12)); c = math.cos(ph)
    return {'body': (-3 * up, 5 * S(TAU * f / 24), 0), 'head': (3 * up, -4 * S(TAU * f / 24), 0),
            'leg.L': (-30 * c, 0, 0), 'leg.R': (30 * c, 0, 0), 'hind.L': (30 * c, 0, 0), 'hind.R': (-30 * c, 0, 0),
            'ear.L': (0, 6 * up, 0), 'ear.R': (0, -6 * up, 0),
            'root_loc': (0, 0, 0.10 * up)}


def cheer(f):  # crouch, hop up with a full spin, land and wiggle
    if f < 10: cr, up, sp = EASE(f / 10), 0, 0
    elif f < 26: u = (f - 10) / 16; cr, up, sp = 1 - EASE(min(u * 3, 1)), S(math.pi * u), EASE(u)
    elif f < 34: cr, up, sp = S(math.pi * (f - 26) / 8) * 0.8, 0, 1
    else: cr, up, sp = 0, 0, 1
    wig = 8 * S(TAU * f / 8) * (1 - EASE(min(1, abs(f - 37) / 3))) if f >= 34 else 0
    return {'body': (8 * cr - 10 * up, 0, (360 * sp if sp < 1 else 0) + wig), 'head': (-8 * cr + 12 * up, 0, -wig),
            'nose': (-10 * up, 0, 0),
            'leg.L': (-40 * up + 10 * cr, 0, 0), 'leg.R': (-40 * up + 10 * cr, 0, 0),
            'hind.L': (40 * up - 10 * cr, 0, 0), 'hind.R': (40 * up - 10 * cr, 0, 0),
            'ear.L': (0, 15 * up, 0), 'ear.R': (0, -15 * up, 0),
            'root_loc': (0, 0, 0.65 * up - 0.06 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (40, cheer)}
PREVIEW = dict(target=(0, 0.05, 0.45), ortho=2.4, shots=[('Cheer', 18), ('Hop', 6)], loop='Idle')
