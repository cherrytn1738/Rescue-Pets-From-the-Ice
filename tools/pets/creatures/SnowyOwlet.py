# Snowy Owlet (Uncommon): big-eyed owl chick with frosted feathers.
# Copied from the skill's owl example. Traits: a round white owl chick with HUGE round eyes (golden iris),
# dark slate speckles and bars over the crown, chest, wings and tail, frosty pale-blue feather tips on the
# wings, tail and ear tufts, small ear tufts, a dark hooked beak and fluffy feathered feet.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'SnowyOwlet'
RARITY = 'Uncommon'
STUDS = 5.0
# white plumage in 4 tones (C2 tops, C1 main, C3 sides/wings, C4 underside) + dark speckles, frost-blue tips,
# golden eyes, dark beak, blush
PALETTE = dict(C1='f2f5fa', C2='ffffff', C3='d9e2ee', C4='aebdcf', SP='3a4256', FR='a6dbff', FD='78bff0',
               IR='ffd84a', EY='1a1b26', WH='ffffff', BK='4a5062', BD='2b2f3c', CL='5a6275', PK='ffa6b8')
GLOW = set()
HP = (0, -0.05, 0.93)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.0, 0.5), (0, 0.0, 0.85), 'root'),
         ('head', (0, -0.05, 0.95), (0, -0.05, 1.4), 'body'),
         ('tail', (0, 0.40, 0.42), (0, 0.62, 0.34), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'wing.{s}', (0.50 * sx, -0.2, 0.86), (0.50 * sx, 0.4, 0.86), 'body'),
              (f'leg.{s}', (0.19 * sx, -0.10, 0.22), (0.19 * sx, -0.10, 0.0), 'root')]
HEAD = dict(scale=1.38, pivot=HP, bones=('head',))


def build(K):
    span, sym = K.span, K.sym
    # body: round upright egg
    span(-0.30, 0.30, -0.32, 0.32, 0.18, 0.26, 'C4', 'body')        # underside
    span(-0.40, 0.36, -0.46, 0.46, 0.26, 0.90, 'C1', 'body')        # core
    sym(-0.32, 0.28, 0.46, 0.50, 0.32, 0.84, 'C3', 'body')          # side step
    span(-0.30, 0.32, -0.38, 0.38, 0.90, 0.96, 'C2', 'body')        # shoulders top
    span(0.36, 0.42, -0.34, 0.34, 0.32, 0.84, 'C1', 'body')         # back round
    span(-0.44, -0.40, -0.32, 0.32, 0.30, 0.84, 'C2', 'body')       # fluffy chest
    span(-0.47, -0.44, -0.22, 0.22, 0.34, 0.74, 'C2', 'body')
    span(-0.46, -0.40, -0.26, 0.26, 0.26, 0.30, 'FR', 'body')       # frosty fluff under the chest
    # dark speckle bars on the chest
    for c, z in ((-0.12, 0.66), (0.10, 0.68), (-0.17, 0.52), (0.0, 0.56), (0.16, 0.50), (-0.08, 0.42), (0.09, 0.40)):
        span(-0.48, -0.47, c - 0.045, c + 0.045, z, z + 0.03, 'SP', 'body')
    for x, z in ((-0.20, 0.72), (0.22, 0.62)):   # and on the back
        span(0.42, 0.43, x - 0.05, x + 0.05, z, z + 0.03, 'SP', 'body')
    # tail fan: white with dark bars and frost tips
    span(0.42, 0.52, -0.24, 0.24, 0.30, 0.52, 'C3', 'tail')
    span(0.52, 0.60, -0.30, 0.30, 0.24, 0.44, 'C1', 'tail')
    span(0.60, 0.66, -0.24, 0.24, 0.22, 0.36, 'FR', 'tail')
    span(0.60, 0.61, -0.26, 0.26, 0.37, 0.40, 'SP', 'tail')
    for x in (-0.15, 0.0, 0.15):
        span(0.52, 0.58, x - 0.03, x + 0.03, 0.44, 0.46, 'C2', 'tail')
    # folded wings: white with dark bars, frost-blue tips sweeping back
    for sx, s in K.sides():
        b = f'wing.{s}'
        span(-0.26, 0.36, 0.50 * sx, 0.58 * sx, 0.36, 0.84, 'C3', b)
        span(-0.20, 0.30, 0.50 * sx, 0.58 * sx, 0.84, 0.88, 'C2', b)
        span(0.36, 0.48, 0.50 * sx, 0.57 * sx, 0.36, 0.70, 'FR', b)
        span(0.48, 0.58, 0.50 * sx, 0.55 * sx, 0.38, 0.56, 'FD', b)
        span(-0.20, 0.30, 0.50 * sx, 0.57 * sx, 0.32, 0.36, 'FR', b)
        for y, z in ((-0.12, 0.72), (0.12, 0.74), (0.00, 0.60), (0.22, 0.56), (-0.14, 0.48), (0.10, 0.44)):
            span(y - 0.05, y + 0.05, 0.58 * sx, 0.59 * sx, z, z + 0.035, 'SP', b)
    # neck + head (scaled round the neck)
    span(-0.30, 0.22, -0.30, 0.30, 0.90, 0.98, 'C1', 'head')
    span(-0.40, 0.30, -0.37, 0.37, 0.98, 1.32, 'C1', 'head')        # skull core
    sym(-0.40, 0.26, 0.37, 0.40, 0.98, 1.32, 'C1', 'head')          # rounded back corners
    span(-0.40, 0.27, -0.37, 0.37, 1.32, 1.40, 'C1', 'head')        # rounded top, step 1
    span(-0.40, 0.22, -0.33, 0.33, 1.40, 1.44, 'C1', 'head')        # rounded top, step 2
    sym(-0.32, 0.22, 0.40, 0.44, 1.04, 1.32, 'C3', 'head')          # cheek step
    span(-0.30, 0.16, -0.28, 0.28, 1.44, 1.50, 'C2', 'head')        # crown
    span(-0.20, 0.10, -0.16, 0.16, 1.50, 1.53, 'C2', 'head')        # crown cap
    span(0.30, 0.34, -0.30, 0.30, 1.04, 1.32, 'C3', 'head')         # back round
    for x, y in ((-0.16, -0.14), (0.14, -0.10), (0.0, 0.02), (-0.10, 0.10), (0.18, 0.08)):   # crown speckles
        span(y - 0.035, y + 0.035, x - 0.035, x + 0.035, 1.53, 1.545, 'SP', 'head')
    for sx in (1, -1):
        span(0.10, 0.18, 0.44 * sx, 0.45 * sx, 1.20, 1.23, 'SP', 'head')      # side speckle
        span(0.34, 0.35, 0.10 * sx, 0.18 * sx, 1.22, 1.25, 'SP', 'head')      # back speckle
    for sx in (1, -1):   # small ear tufts with frosty tips
        span(-0.26, -0.02, 0.20 * sx, 0.37 * sx, 1.40, 1.56, 'C1', 'head')
        span(-0.22, -0.04, 0.26 * sx, 0.40 * sx, 1.56, 1.66, 'C2', 'head')
        span(-0.18, -0.07, 0.31 * sx, 0.42 * sx, 1.66, 1.75, 'FR', 'head')
        span(-0.15, -0.09, 0.36 * sx, 0.43 * sx, 1.75, 1.79, 'FD', 'head')
    # facial disc: frosty rim, white disc (two lobes with a notch, point at the beak)
    span(-0.405, -0.40, -0.39, 0.39, 0.98, 1.32, 'FR', 'head')
    span(-0.405, -0.40, -0.36, 0.36, 1.32, 1.40, 'FR', 'head')
    span(-0.415, -0.405, -0.37, 0.37, 1.04, 1.32, 'C2', 'head')
    span(-0.415, -0.405, -0.34, 0.34, 1.32, 1.38, 'C2', 'head')
    sym(-0.415, -0.405, 0.04, 0.30, 1.38, 1.41, 'C2', 'head')
    span(-0.415, -0.405, -0.28, 0.28, 1.00, 1.04, 'C2', 'head')
    for sx in (1, -1):   # HUGE round eyes: dark rim, golden iris, pupil, 2 shines
        span(-0.425, -0.415, 0.06 * sx, 0.32 * sx, 1.08, 1.37, 'EY', 'head')     # rounded: cross of 2 boxes
        span(-0.425, -0.415, 0.04 * sx, 0.34 * sx, 1.11, 1.34, 'EY', 'head')
        span(-0.435, -0.425, 0.08 * sx, 0.30 * sx, 1.10, 1.35, 'IR', 'head')
        span(-0.435, -0.425, 0.06 * sx, 0.32 * sx, 1.13, 1.32, 'IR', 'head')
        span(-0.445, -0.435, 0.13 * sx, 0.25 * sx, 1.15, 1.30, 'EY', 'head')
        span(-0.445, -0.435, 0.11 * sx, 0.27 * sx, 1.17, 1.28, 'EY', 'head')
        span(-0.455, -0.445, 0.17 * sx, 0.24 * sx, 1.22, 1.29, 'WH', 'head')
        span(-0.455, -0.445, 0.12 * sx, 0.15 * sx, 1.16, 1.19, 'WH', 'head')
        span(-0.425, -0.415, 0.26 * sx, 0.33 * sx, 1.015, 1.06, 'PK', 'head')   # blush
    # small dark hooked beak between the eyes
    span(-0.48, -0.415, -0.05, 0.05, 1.04, 1.15, 'BK', 'head')
    span(-0.51, -0.48, -0.04, 0.04, 1.00, 1.11, 'BK', 'head')
    span(-0.52, -0.49, -0.03, 0.03, 0.97, 1.02, 'BD', 'head')
    # fluffy feathered feet with dark claws
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.16, -0.02, 0.12 * sx, 0.26 * sx, 0.07, 0.22, 'C3', b)
        span(-0.18, 0.0, 0.10 * sx, 0.28 * sx, 0.0, 0.07, 'C1', b)
        for dx in (0.12, 0.19, 0.26):
            span(-0.27, -0.18, (dx - 0.03) * sx, (dx + 0.03) * sx, 0.0, 0.06, 'C1', b)
            span(-0.30, -0.27, (dx - 0.015) * sx, (dx + 0.015) * sx, 0.0, 0.035, 'CL', b)


# ---- clips: fn(frame) -> {bone: (rx, ry, rz) world degrees, 'root_loc': (x, y, z) metres} ----
def idle(f):   # breathing, a big curious head tilt and back, a little wing ruffle
    ph = TAU * f / 90
    t = EASE(min(f / 14, 1)) if f < 45 else 1 - EASE(min((f - 45) / 14, 1))
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-3 * t, 18 * t, 4 * S(ph)), 'tail': (0, 0, 6 * S(ph * 2)),
            'wing.L': (0, -3 - 3 * S(ph), 0), 'wing.R': (0, 3 + 3 * S(ph), 0)}


def hop(f):   # waddle hop
    ph = TAU * f / 24; c = math.cos(ph)
    return {'root': (0, 8 * S(ph), 5 * c), 'body': (3, 0, 0), 'head': (-4 * abs(S(ph)), -6 * S(ph), -4 * c),
            'leg.L': (-24 * S(ph), 0, 0), 'leg.R': (24 * S(ph), 0, 0), 'tail': (6, 0, -14 * S(ph)),
            'wing.L': (0, -8 - 6 * S(2 * ph), 0), 'wing.R': (0, 8 + 6 * S(2 * ph), 0),
            'root_loc': (0, 0, 0.09 * abs(S(ph)))}


def cheer(f):   # crouch, flap up into the air, land
    if f < 8: cr, up = EASE(f / 8), 0
    elif f < 28: u = (f - 8) / 20; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 36: cr, up = S(math.pi * (f - 28) / 8) * 0.8, 0
    else: cr, up = 0, 0
    w = (S(TAU * f / 8) + 1) / 2 * up
    return {'body': (6 * cr - 6 * up, 0, 0), 'head': (-6 * cr + 10 * up, 0, 0), 'tail': (-12 * up, 0, 0),
            'wing.L': (0, -10 - 80 * w, 0), 'wing.R': (0, 10 + 80 * w, 0),
            'leg.L': (-18 * up, 0, 0), 'leg.R': (-18 * up, 0, 0),
            'root_loc': (0, 0, 0.8 * up - 0.06 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (40, cheer)}
PREVIEW = dict(target=(0, -0.1, 1.25), ortho=3.6, shots=[('Cheer', 18), ('Hop', 6)], loop='Idle')
