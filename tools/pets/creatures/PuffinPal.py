# Puffin Pal (Common): puffin with a frosty striped beak.
# Copied from the skill's penguin example. Traits: a stout black-backed puffin with a white face and belly,
# a black collar and crown, an OVERSIZED tall triangular beak striped white / frosty blue / white / orange,
# folded black wings and big orange webbed feet.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'PuffinPal'
RARITY = 'Common'
STUDS = 5.0
# black plumage in 4 tones (K2 tops, K1 main, K3 sides/wings, K4 underside) + white face and belly,
# the striped beak (FB frosty blue, BW white, OR/OD orange), orange feet, eyes, blush
PALETTE = dict(K1='323646', K2='4a5064', K3='282b38', K4='1d2029', W1='f7f9fc', W2='dde3ec',
               FB='8fd3ff', FD='5fb4ec', BW='ffffff', OR='ff9a1f', OD='e8700f', FT='ff8a1f', FTD='e0640e',
               EY='15161f', IR='4f8fe0', WH='ffffff', PK='ff9fb4', RG='ff6a3d')
GLOW = set()
HP = (0, -0.05, 0.84)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0, 0.40), (0, 0, 0.80), 'root'),
         ('head', HP, (0, -0.05, 1.30), 'body'),
         ('tail', (0, 0.40, 0.30), (0, 0.56, 0.26), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'wing.{s}', (0.44 * sx, -0.10, 0.76), (0.44 * sx, 0.40, 0.70), 'body'),
              (f'leg.{s}', (0.19 * sx, -0.08, 0.16), (0.19 * sx, -0.08, 0.0), 'root')]
HEAD = dict(scale=1.35, pivot=HP, bones=('head',))


def build(K):
    span, sym = K.span, K.sym
    # body: stout upright egg, black back, white belly
    span(-0.32, 0.32, -0.32, 0.32, 0.12, 0.18, 'K4', 'body')        # underside
    span(-0.40, 0.40, -0.44, 0.44, 0.18, 0.64, 'K1', 'body')        # core
    span(-0.36, 0.36, -0.40, 0.40, 0.64, 0.84, 'K1', 'body')        # upper core
    span(-0.28, 0.28, -0.32, 0.32, 0.84, 0.88, 'K2', 'body')        # shoulders
    span(0.40, 0.45, -0.34, 0.34, 0.24, 0.76, 'K1', 'body')         # back round
    span(0.45, 0.48, -0.22, 0.22, 0.32, 0.66, 'K3', 'body')
    span(-0.44, -0.40, -0.34, 0.34, 0.22, 0.60, 'W1', 'body')       # white belly (rounded by steps)
    span(-0.44, -0.40, -0.28, 0.28, 0.60, 0.72, 'W1', 'body')
    span(-0.44, -0.40, -0.20, 0.20, 0.72, 0.78, 'W1', 'body')
    span(-0.48, -0.44, -0.26, 0.26, 0.28, 0.62, 'W1', 'body')       # belly bulge
    span(-0.48, -0.40, -0.26, 0.26, 0.18, 0.28, 'W2', 'body')       # belly shade underneath
    # short tail
    span(0.44, 0.54, -0.14, 0.14, 0.18, 0.34, 'K4', 'tail')
    span(0.54, 0.60, -0.08, 0.08, 0.18, 0.28, 'K4', 'tail')
    # folded wings: black, dark tips sweep back past the tail
    for sx, s in K.sides():
        b = f'wing.{s}'
        span(-0.24, 0.30, 0.44 * sx, 0.52 * sx, 0.36, 0.78, 'K3', b)
        span(-0.18, 0.24, 0.44 * sx, 0.52 * sx, 0.78, 0.82, 'K2', b)
        span(0.30, 0.44, 0.44 * sx, 0.51 * sx, 0.36, 0.62, 'K3', b)
        span(0.44, 0.56, 0.44 * sx, 0.49 * sx, 0.36, 0.50, 'K4', b)
        span(-0.16, 0.24, 0.52 * sx, 0.53 * sx, 0.56, 0.60, 'K2', b)  # feather line
    # head (scaled 1.35 round the neck): black crown and collar, white face and cheeks
    span(-0.30, 0.22, -0.30, 0.30, 0.84, 0.92, 'K1', 'head')        # collar
    span(-0.40, 0.30, -0.36, 0.36, 0.92, 1.30, 'K1', 'head')        # skull core
    sym(-0.36, 0.26, 0.36, 0.40, 0.92, 1.30, 'K1', 'head')          # rounded corners
    span(-0.38, 0.27, -0.36, 0.36, 1.30, 1.38, 'K1', 'head')        # rounded top
    span(-0.32, 0.22, -0.30, 0.30, 1.38, 1.44, 'K2', 'head')        # crown
    span(-0.22, 0.12, -0.18, 0.18, 1.44, 1.47, 'K2', 'head')        # crown cap
    span(0.30, 0.34, -0.30, 0.30, 0.98, 1.28, 'K3', 'head')         # back of head
    sym(-0.34, 0.06, 0.40, 0.44, 0.96, 1.26, 'W1', 'head')          # white cheek
    sym(-0.30, 0.02, 0.40, 0.44, 1.26, 1.30, 'W1', 'head')
    sym(0.06, 0.24, 0.40, 0.44, 1.00, 1.28, 'K3', 'head')           # nape
    span(-0.43, -0.40, -0.36, 0.36, 0.98, 1.27, 'W1', 'head')       # white face
    span(-0.43, -0.40, -0.31, 0.31, 1.27, 1.31, 'W1', 'head')
    span(-0.43, -0.40, -0.26, 0.26, 0.95, 0.98, 'W2', 'head')
    for sx in (1, -1):   # eyes: dark block + icy blue iris + 2 white shines
        span(-0.46, -0.43, 0.15 * sx, 0.30 * sx, 1.08, 1.28, 'EY', 'head')
        span(-0.465, -0.46, 0.19 * sx, 0.28 * sx, 1.10, 1.17, 'IR', 'head')
        span(-0.475, -0.46, 0.22 * sx, 0.28 * sx, 1.20, 1.26, 'WH', 'head')
        span(-0.475, -0.465, 0.17 * sx, 0.20 * sx, 1.11, 1.14, 'WH', 'head')
        span(-0.445, -0.43, 0.27 * sx, 0.35 * sx, 1.00, 1.06, 'PK', 'head')   # blush
        span(-0.475, -0.43, 0.12 * sx, 0.15 * sx, 0.96, 1.01, 'RG', 'head')   # beak corner rosette
    # BIG tall triangular beak, striped from the face out: white rim, frosty blue, white, orange, orange tip
    span(-0.47, -0.43, -0.13, 0.13, 0.91, 1.31, 'BW', 'head')
    span(-0.55, -0.47, -0.12, 0.12, 0.93, 1.29, 'FB', 'head')
    span(-0.555, -0.52, -0.122, 0.122, 0.94, 1.28, 'FD', 'head')    # frost line
    span(-0.59, -0.555, -0.11, 0.11, 0.95, 1.26, 'BW', 'head')
    span(-0.70, -0.59, -0.10, 0.10, 0.96, 1.23, 'OR', 'head')
    span(-0.66, -0.64, -0.103, 0.103, 0.98, 1.21, 'OD', 'head')     # groove
    span(-0.79, -0.70, -0.08, 0.08, 0.98, 1.18, 'OR', 'head')
    span(-0.86, -0.79, -0.06, 0.06, 0.99, 1.13, 'OR', 'head')
    span(-0.89, -0.86, -0.04, 0.04, 1.00, 1.09, 'OD', 'head')       # hooked tip
    # legs + big orange webbed feet
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.13, -0.03, 0.14 * sx, 0.24 * sx, 0.05, 0.14, 'FTD', b)
        span(-0.30, 0.00, 0.07 * sx, 0.31 * sx, 0.00, 0.05, 'FT', b)
        for dx in (0.09, 0.19, 0.29):
            span(-0.40, -0.30, (dx - 0.04) * sx, (dx + 0.04) * sx, 0.00, 0.05, 'FT', b)


# ---- clips: fn(frame) -> {bone: (rx, ry, rz) world degrees, 'root_loc': (x, y, z) metres} ----
def idle(f):   # breathing, a curious head tilt and a quick wing ruffle
    ph = TAU * f / 90
    t = EASE(min(f / 14, 1)) if f < 45 else 1 - EASE(min((f - 45) / 14, 1))
    ru = max(0, S(TAU * f / 90 + 2.4) - 0.7) * 3.3
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-4 * t, 14 * t, 3 * S(ph)), 'tail': (0, 0, 8 * S(2 * ph)),
            'wing.L': (0, -4 - 14 * ru * (S(TAU * f / 8) + 1) / 2, 0),
            'wing.R': (0, 4 + 14 * ru * (S(TAU * f / 8) + 1) / 2, 0)}


def hop(f):   # waddle with a little bounce
    ph = TAU * f / 24; c = math.cos(ph)
    return {'root': (0, 9 * S(ph), 5 * c), 'body': (2, 0, 0), 'head': (-4 * abs(S(ph)), -6 * S(ph), -4 * c),
            'leg.L': (-24 * S(ph), 0, 0), 'leg.R': (24 * S(ph), 0, 0), 'tail': (6, 0, -14 * S(ph)),
            'wing.L': (0, -8 - 6 * S(2 * ph), 0), 'wing.R': (0, 8 + 6 * S(2 * ph), 0),
            'root_loc': (0, 0, 0.08 * abs(S(ph)))}


def cheer(f):   # crouch, jump with fast wingbeats, land
    if f < 8: cr, up = EASE(f / 8), 0
    elif f < 26: u = (f - 8) / 18; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 34: cr, up = S(math.pi * (f - 26) / 8) * 0.8, 0
    else: cr, up = 0, 0
    w = (S(TAU * f / 6) + 1) / 2 * up
    return {'body': (6 * cr - 8 * up, 0, 0), 'head': (-6 * cr + 12 * up, 0, 0), 'tail': (-14 * up, 0, 0),
            'wing.L': (0, -10 - 80 * w, 0), 'wing.R': (0, 10 + 80 * w, 0),
            'leg.L': (-20 * up, 0, 0), 'leg.R': (-20 * up, 0, 0),
            'root_loc': (0, 0, 0.75 * up - 0.06 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (36, cheer)}
PREVIEW = dict(target=(0, -0.15, 1.10), ortho=3.3, shots=[('Cheer', 17), ('Hop', 6)], loop='Idle')
