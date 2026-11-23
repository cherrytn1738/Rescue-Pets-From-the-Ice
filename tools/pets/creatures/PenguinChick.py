# Penguin Chick (Common): grey fluffball with a tiny orange beak.
# Copied from the skill's penguin example. Traits: a round downy grey ball body with fluff tufts poking out,
# a dark cap and white face mask (emperor-chick style), a TINY orange beak, little stubby flippers,
# orange feet and a big fluff tuft on top of the head.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'PenguinChick'
RARITY = 'Common'
STUDS = 5.0
# downy grey in 4 tones (G2 tops, G1 main, G3 sides, G4 underside) + pale belly, charcoal cap, white mask,
# orange beak/feet, eyes, blush
PALETTE = dict(G1='adb0b8', G2='d0d3d9', G3='92959f', G4='757884', BL='e6e8ec', BS='c8cad1',
               DK='3b4052', D2='51586d', W1='f7f9fc', W2='dfe5ef',
               OR='ff8a1f', OD='e0640e', EY='1b1d2b', IR='3d6fd1', WH='ffffff', PK='ff9fb4')
GLOW = set()
HP = (0, -0.04, 0.82)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0, 0.40), (0, 0, 0.80), 'root'),
         ('head', HP, (0, -0.04, 1.30), 'body'),
         ('tuft', (0, -0.06, 1.46), (0, -0.06, 1.62), 'head'),
         ('tail', (0, 0.46, 0.24), (0, 0.60, 0.20), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'flipper.{s}', (0.50 * sx, -0.04, 0.66), (0.62 * sx, -0.04, 0.34), 'body'),
              (f'leg.{s}', (0.20 * sx, -0.10, 0.14), (0.20 * sx, -0.10, 0.0), 'root')]
HEAD = dict(scale=1.35, pivot=HP, bones=('head', 'tuft'))


def build(K):
    span, sym = K.span, K.sym
    # body: a round stepped ball, wider than tall
    span(-0.30, 0.30, -0.30, 0.30, 0.10, 0.16, 'G4', 'body')        # underside
    span(-0.40, 0.40, -0.42, 0.42, 0.16, 0.24, 'G1', 'body')        # lower step
    span(-0.46, 0.46, -0.50, 0.50, 0.24, 0.62, 'G1', 'body')        # core
    span(-0.42, 0.42, -0.46, 0.46, 0.62, 0.76, 'G1', 'body')        # upper step
    span(-0.34, 0.34, -0.40, 0.40, 0.76, 0.84, 'G2', 'body')        # shoulders
    sym(-0.34, 0.34, 0.50, 0.55, 0.30, 0.56, 'G3', 'body')          # side round
    span(0.46, 0.51, -0.36, 0.36, 0.30, 0.58, 'G1', 'body')         # back round
    span(0.51, 0.54, -0.22, 0.22, 0.36, 0.52, 'G3', 'body')
    # pale fluffy belly
    span(-0.50, -0.46, -0.34, 0.34, 0.24, 0.60, 'BL', 'body')
    span(-0.54, -0.50, -0.24, 0.24, 0.30, 0.54, 'BL', 'body')
    span(-0.48, -0.40, -0.26, 0.26, 0.14, 0.24, 'BS', 'body')
    # down fluff tufts poking out round the ball (they make it read fuzzy, also in silhouette)
    for sx in (1, -1):
        span(-0.06, 0.08, 0.55 * sx, 0.63 * sx, 0.42, 0.52, 'G2', 'body')
        span(0.10, 0.22, 0.55 * sx, 0.61 * sx, 0.28, 0.38, 'G1', 'body')
        span(-0.20, -0.08, 0.50 * sx, 0.57 * sx, 0.16, 0.24, 'G3', 'body')
        span(-0.10, 0.04, 0.46 * sx, 0.52 * sx, 0.66, 0.74, 'G2', 'body')
        span(0.54, 0.60, 0.12 * sx, 0.22 * sx, 0.46, 0.56, 'G2', 'body')
    span(0.54, 0.60, -0.06, 0.06, 0.24, 0.32, 'G1', 'body')
    # tail stub
    span(0.50, 0.60, -0.12, 0.12, 0.16, 0.28, 'G4', 'tail')
    # little flippers held out from the ball
    for sx, s in K.sides():
        b = f'flipper.{s}'
        K.limb((0.46 * sx, -0.04, 0.64), (0.66 * sx, -0.04, 0.38), 0.26, 0.09, 'G3', b, extend=0.04)
        K.limb((0.64 * sx, -0.04, 0.40), (0.74 * sx, -0.04, 0.26), 0.18, 0.08, 'G4', b, extend=0.02)
    # head (scaled 1.35 round the neck): a rounded dome, grey below, charcoal cap, white face mask
    span(-0.32, 0.24, -0.32, 0.32, 0.82, 0.90, 'G1', 'head')        # neck
    span(-0.34, 0.26, -0.34, 0.34, 0.90, 0.96, 'G1', 'head')
    span(-0.38, 0.30, -0.38, 0.38, 0.96, 1.22, 'G1', 'head')        # skull core
    span(-0.38, 0.30, -0.38, 0.38, 1.22, 1.28, 'DK', 'head')        # cap
    span(-0.34, 0.26, -0.34, 0.34, 1.28, 1.36, 'DK', 'head')
    span(-0.26, 0.18, -0.26, 0.26, 1.36, 1.42, 'D2', 'head')        # crown
    span(-0.16, 0.10, -0.16, 0.16, 1.42, 1.45, 'D2', 'head')
    sym(-0.30, 0.22, 0.38, 0.42, 1.00, 1.22, 'G3', 'head')          # cheek step
    sym(-0.30, 0.22, 0.38, 0.42, 1.22, 1.26, 'DK', 'head')
    span(0.30, 0.34, -0.30, 0.30, 1.08, 1.26, 'DK', 'head')         # back of head
    span(0.30, 0.34, -0.30, 0.30, 1.00, 1.08, 'G1', 'head')
    # white face mask (cap dips to a widow's peak between the eyes)
    span(-0.41, -0.38, -0.34, 0.34, 0.96, 1.22, 'W1', 'head')
    sym(-0.41, -0.38, 0.06, 0.32, 1.22, 1.30, 'W1', 'head')
    sym(-0.41, -0.38, 0.10, 0.24, 1.30, 1.33, 'W1', 'head')
    span(-0.40, -0.34, -0.26, 0.26, 0.92, 0.96, 'W2', 'head')
    for sx in (1, -1):   # eyes: dark block + blue iris + 2 white shines, proud of the mask
        span(-0.44, -0.41, 0.07 * sx, 0.22 * sx, 1.06, 1.26, 'EY', 'head')
        span(-0.445, -0.44, 0.11 * sx, 0.20 * sx, 1.08, 1.15, 'IR', 'head')
        span(-0.455, -0.44, 0.14 * sx, 0.20 * sx, 1.18, 1.24, 'WH', 'head')
        span(-0.455, -0.445, 0.09 * sx, 0.12 * sx, 1.09, 1.12, 'WH', 'head')
        span(-0.425, -0.41, 0.23 * sx, 0.31 * sx, 0.99, 1.05, 'PK', 'head')   # blush
    # tiny orange beak
    span(-0.49, -0.41, -0.05, 0.05, 1.00, 1.07, 'OR', 'head')
    span(-0.52, -0.49, -0.03, 0.03, 1.01, 1.05, 'OD', 'head')
    # big fluff tuft on top
    span(-0.14, 0.04, -0.09, 0.09, 1.45, 1.56, 'G1', 'tuft')
    span(-0.11, 0.01, -0.06, 0.06, 1.56, 1.72, 'G2', 'tuft')
    span(-0.20, -0.08, -0.035, 0.035, 1.68, 1.78, 'G2', 'tuft')    # curl forward
    sym(-0.08, 0.02, 0.07, 0.14, 1.52, 1.62, 'G2', 'tuft')          # side wisps
    sym(-0.06, 0.0, 0.12, 0.19, 1.60, 1.67, 'G2', 'tuft')
    # legs + orange feet
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.14, -0.04, 0.15 * sx, 0.25 * sx, 0.05, 0.12, 'OD', b)
        span(-0.30, 0.00, 0.09 * sx, 0.31 * sx, 0.00, 0.05, 'OR', b)
        for dx in (0.11, 0.20, 0.29):
            span(-0.38, -0.30, (dx - 0.035) * sx, (dx + 0.035) * sx, 0.00, 0.05, 'OR', b)


# ---- clips: fn(frame) -> {bone: (rx, ry, rz) world degrees, 'root_loc': (x, y, z) metres} ----
def idle(f):   # breathing, a slow head tilt and a little flipper wiggle now and then
    ph = TAU * f / 90
    wig = max(0, S(TAU * f / 45) - 0.5) * 2
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 8 * S(TAU * f / 90), 4 * S(ph)),
            'tuft': (0, 10 * S(2 * ph), 0), 'tail': (0, 0, 8 * S(2 * ph)),
            'flipper.L': (0, -10 - 14 * wig * S(TAU * f / 9), 0), 'flipper.R': (0, 10 + 14 * wig * S(TAU * f / 9), 0)}


def hop(f):   # waddle with a little bounce
    ph = TAU * f / 24; c = math.cos(ph)
    return {'root': (0, 10 * S(ph), 5 * c), 'body': (2, 0, 0), 'head': (-4 * abs(S(ph)), -6 * S(ph), -4 * c),
            'tuft': (0, -14 * S(ph), 0),
            'leg.L': (-22 * S(ph), 0, 0), 'leg.R': (22 * S(ph), 0, 0), 'tail': (6, 0, -16 * S(ph)),
            'flipper.L': (0, -20 - 10 * S(2 * ph), 0), 'flipper.R': (0, 20 + 10 * S(2 * ph), 0),
            'root_loc': (0, 0, 0.08 * abs(S(ph)))}


def cheer(f):   # crouch, jump with flippers flapping fast, land
    if f < 8: cr, up = EASE(f / 8), 0
    elif f < 26: u = (f - 8) / 18; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 34: cr, up = S(math.pi * (f - 26) / 8) * 0.8, 0
    else: cr, up = 0, 0
    w = (S(TAU * f / 6) + 1) / 2 * up
    return {'body': (6 * cr - 6 * up, 0, 0), 'head': (-6 * cr + 10 * up, 0, 0),
            'tuft': (0, 0, 0), 'tail': (-12 * up, 0, 0),
            'flipper.L': (0, -15 - 75 * w, 0), 'flipper.R': (0, 15 + 75 * w, 0),
            'leg.L': (-20 * up, 0, 0), 'leg.R': (-20 * up, 0, 0),
            'root_loc': (0, 0, 0.75 * up - 0.06 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (36, cheer)}
PREVIEW = dict(target=(0, -0.05, 1.10), ortho=3.3, shots=[('Cheer', 17), ('Hop', 6)], loop='Idle')
