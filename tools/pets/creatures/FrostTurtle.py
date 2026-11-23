# Frost Turtle (Rare, Ancient Ice): turtle with a shell of ice crystals.
# Copied from the skill's axolotl example. Traits: a green-teal chibi turtle with a stepped domed shell
# crowned by clusters of pale-blue ice crystals pointing up and out (the spiky silhouette), stubby splayed
# legs with pale claws, a tiny tail and a big round smiling head.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'FrostTurtle'
RARITY = 'Rare'
STUDS = 5.0
# green-teal skin in 4 tones (S2 tops, S1 main, S3 sides, S4 underside) + deep teal shell (H*) + ice crystals (IC/IL/IT)
PALETTE = dict(S1='5cc9a4', S2='8ee3c2', S3='3fa886', S4='2c7d66',
               H1='2f86a3', H2='4fa9c4', H3='236a85', H4='174b61', PL='cfeed9',
               IC='9fdcff', IL='d6f3ff', IT='f2fbff', TO='e9f6ee',
               EY='1b2430', IR='2f7f9a', WH='ffffff', MO='1f4f45', PK='ff9cb4')
GLOW = set()
HP = (0, -0.42, 0.26)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.2), None),
         ('body', (0, 0.0, 0.20), (0, 0.0, 0.50), 'root'),
         ('shell', (0, 0.0, 0.45), (0, 0.0, 0.80), 'body'),
         ('head', HP, (0, -0.42, 0.60), 'body'),
         ('tail', (0, 0.42, 0.18), (0, 0.58, 0.16), 'body')]
for _s, _sx in (('L', 1), ('R', -1)):
    BONES += [(f'leg.{_s}', (0.32 * _sx, -0.26, 0.20), (0.32 * _sx, -0.26, 0.0), 'body'),
              (f'hind.{_s}', (0.32 * _sx, 0.26, 0.20), (0.32 * _sx, 0.26, 0.0), 'body')]
HEAD = dict(scale=1.3, pivot=HP, bones=('head',))


def build(K):
    span, sym = K.span, K.sym
    # body under the shell: pale plastron and a skin band
    span(-0.38, 0.36, -0.30, 0.30, 0.08, 0.14, 'S4', 'body')
    span(-0.42, 0.40, -0.34, 0.34, 0.14, 0.20, 'PL', 'body')
    # shell: wide rim, then stepped dome narrowing in both x and y
    span(-0.46, 0.44, -0.42, 0.42, 0.20, 0.28, 'H3', 'shell')
    span(-0.47, 0.45, -0.38, 0.38, 0.20, 0.27, 'H4', 'shell')          # rim front/back lip
    span(-0.40, 0.38, -0.37, 0.37, 0.28, 0.42, 'H1', 'shell')
    span(-0.32, 0.30, -0.29, 0.29, 0.42, 0.52, 'H1', 'shell')
    span(-0.22, 0.20, -0.19, 0.19, 0.52, 0.58, 'H2', 'shell')
    # scute plates on the sides and front (lighter squares)
    for sx in (1, -1):
        for y0, y1 in ((-0.28, -0.06), (0.04, 0.26)):
            span(y0, y1, 0.37 * sx, 0.38 * sx, 0.30, 0.40, 'H2', 'shell')
    span(-0.41, -0.40, -0.12, 0.12, 0.30, 0.40, 'H2', 'shell')
    # ice crystals: a big central cluster, side clusters leaning out, a ring round the rim
    sp = K.spike
    sp((0, -0.02, 0.56), (0, 0, 1), 0.56, 0.20, 'IC', 'IT', 'shell')
    sp((0.07, 0.08, 0.56), (0.45, 0.35, 1), 0.38, 0.14, 'IL', 'IT', 'shell')
    sp((-0.08, -0.10, 0.56), (-0.4, -0.45, 1), 0.36, 0.14, 'IL', 'IT', 'shell')
    for sx in (1, -1):
        sp((0.20 * sx, -0.14, 0.48), (0.7 * sx, -0.3, 1), 0.42, 0.15, 'IC', 'IT', 'shell')
        sp((0.18 * sx, 0.16, 0.48), (0.6 * sx, 0.45, 1), 0.36, 0.14, 'IL', 'IT', 'shell')
        sp((0.33 * sx, 0.0, 0.36), (1.0 * sx, 0.0, 0.55), 0.30, 0.12, 'IC', 'IT', 'shell')
        sp((0.10 * sx, -0.26, 0.48), (0.35 * sx, -0.7, 1), 0.26, 0.11, 'IL', 'IT', 'shell')
    sp((0, 0.28, 0.44), (0, 0.8, 0.8), 0.30, 0.12, 'IC', 'IT', 'shell')
    # legs: stubby, splayed out under the rim, pale claws
    for sx, s in K.sides():
        for b, y0, y1 in ((f'leg.{s}', -0.34, -0.18), (f'hind.{s}', 0.18, 0.34)):
            span(y0, y1, 0.24 * sx, 0.44 * sx, 0.05, 0.20, 'S1', b)
            span(y0 + 0.02, y1 - 0.02, 0.44 * sx, 0.47 * sx, 0.07, 0.18, 'S3', b)
            span(y0 - 0.02, y1 + 0.01, 0.26 * sx, 0.46 * sx, 0.0, 0.05, 'S3', b)
            for dx in (0.30, 0.36, 0.42):
                span(y0 - 0.05, y0 - 0.02, (dx - 0.015) * sx, (dx + 0.015) * sx, 0.0, 0.035, 'TO', b)
    # tail: tiny pointed nub
    span(0.40, 0.52, -0.07, 0.07, 0.10, 0.20, 'S1', 'tail')
    span(0.52, 0.60, -0.04, 0.04, 0.11, 0.17, 'S3', 'tail')
    # head (scaled 1.4 around the neck): round, big eyes, smile
    span(-0.50, -0.38, -0.11, 0.11, 0.16, 0.32, 'S1', 'head')       # neck
    span(-0.78, -0.48, -0.20, 0.20, 0.20, 0.48, 'S1', 'head')       # skull
    span(-0.74, -0.52, -0.15, 0.15, 0.48, 0.52, 'S2', 'head')       # crown
    sym(-0.74, -0.52, 0.20, 0.23, 0.24, 0.44, 'S3', 'head')          # cheek side step
    span(-0.74, -0.50, -0.15, 0.15, 0.17, 0.20, 'S4', 'head')       # chin
    span(-0.81, -0.78, -0.16, 0.16, 0.23, 0.46, 'S1', 'head')       # face plate
    span(-0.80, -0.78, -0.11, 0.11, 0.46, 0.49, 'S2', 'head')
    # face (y -0.81)
    span(-0.815, -0.81, -0.06, 0.06, 0.27, 0.285, 'MO', 'head')     # smile
    sym(-0.815, -0.81, 0.06, 0.09, 0.285, 0.30, 'MO', 'head')
    for sx in (1, -1):
        span(-0.82, -0.81, 0.04 * sx, 0.15 * sx, 0.33, 0.45, 'EY', 'head')
        span(-0.825, -0.82, 0.06 * sx, 0.13 * sx, 0.34, 0.40, 'IR', 'head')
        span(-0.83, -0.82, 0.095 * sx, 0.14 * sx, 0.41, 0.44, 'WH', 'head')
        span(-0.83, -0.82, 0.055 * sx, 0.075 * sx, 0.35, 0.37, 'WH', 'head')
        span(-0.815, -0.81, 0.15 * sx, 0.19 * sx, 0.30, 0.34, 'PK', 'head')   # blush


def idle(f):
    ph = TAU * f / 90
    look = S(TAU * f / 90)
    return {'body': (1.0 * S(ph), 0, 0), 'shell': (0, 1.5 * S(ph + 0.8), 0),
            'head': (-4 * S(ph * 2 + 0.6), 6 * S(ph + 1.0), 14 * look),
            'tail': (0, 0, 14 * S(ph * 3)),
            'leg.L': (4 * S(ph), 0, 0), 'leg.R': (-4 * S(ph), 0, 0),
            'root_loc': (0, 0, 0.008 * (1 + S(ph * 2)))}


def hop(f):   # waddle: diagonal leg pairs, body rolls side to side, little bounce
    ph = TAU * f / 24; c = math.cos(ph); a = 24 * S(ph)
    return {'leg.L': (-a, 0, 0), 'hind.R': (-a, 0, 0), 'leg.R': (a, 0, 0), 'hind.L': (a, 0, 0),
            'body': (0, 5 * c, 4 * S(ph)), 'shell': (0, 2 * c, 0), 'head': (-3 * abs(S(ph)), -4 * c, -5 * S(ph)),
            'tail': (0, 0, -16 * S(ph - 0.8)),
            'root_loc': (0, 0, 0.05 * abs(S(ph)))}


def cheer(f):  # crouch, happy jump with legs flailing and a half twist, land and settle
    if f < 8: cr, up = EASE(f / 8), 0
    elif f < 24: u = (f - 8) / 16; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 32: cr, up = S(math.pi * (f - 24) / 8) * 0.8, 0
    else: cr, up = 0, 0
    fl = 30 * S(TAU * f / 8) * up
    tw = 20 * S(TAU * max(0, f - 8) / 16) * up
    return {'body': (6 * cr - 10 * up, 0, tw), 'shell': (0, 4 * S(TAU * f / 8) * up, 0),
            'head': (-6 * cr + 16 * up, 0, -tw * 0.5),
            'leg.L': (-30 * up + fl, 0, 0), 'leg.R': (-30 * up - fl, 0, 0),
            'hind.L': (30 * up - fl, 0, 0), 'hind.R': (30 * up + fl, 0, 0),
            'tail': (0, 0, 30 * S(TAU * f / 6) * up),
            'root_loc': (0, 0, 0.55 * up - 0.06 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (36, cheer)}
PREVIEW = dict(target=(0, -0.10, 0.50), ortho=2.6, shots=[('Cheer', 16), ('Hop', 6)], loop='Idle')
