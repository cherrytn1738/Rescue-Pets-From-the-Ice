# Crystal Stag (Epic, Ancient Ice): fawn with glowing crystal antlers.
# Copied from the skill's arctic fox example. Traits: a tan fawn with white spots on its back and sides,
# long thin legs with dark hooves, big sideways ears, a little white-tipped tail, and branching icy-cyan
# crystal antlers whose tine tips glow (GLOW = the tip key only).
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'CrystalStag'
RARITY = 'Epic'
STUDS = 5.0
# tan fur in 4 tones (F2 tops, F1 main, F3 sides, F4 dark underside/ear rims) + cream belly/muzzle, white spots,
# crystal antlers (AN main, AL light tines, AG glowing tips)
PALETTE = dict(F1='ecbd85', F2='f8d6a6', F3='d29c62', F4='8a5631', CR='f6e7d0', SP='fff8ec',
               HF='3d2a20', NS='2a1d1a', PK='ffa9b8',
               AN='5fd8f5', AL='a8ecff', AG='c9fbff',
               EY='1e1820', IR='7a4a2a', WH='ffffff')
GLOW = {'AG'}
HP = (0, -0.40, 1.02)   # head pivot (top of the neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.05, 0.55), (0, 0.05, 0.85), 'root'),
         ('head', HP, (0, -0.40, 1.30), 'body'),
         ('tail', (0, 0.42, 0.80), (0, 0.52, 0.90), 'body')]
for _s, _sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{_s}', (0.18 * _sx, -0.50, 1.26), (0.46 * _sx, -0.50, 1.34), 'head'),
              (f'leg.{_s}', (0.155 * _sx, -0.24, 0.54), (0.155 * _sx, -0.24, 0.0), 'body'),
              (f'hind.{_s}', (0.155 * _sx, 0.28, 0.56), (0.155 * _sx, 0.28, 0.0), 'body')]
HEAD = dict(scale=1.35, pivot=HP, bones=('head', 'ear.L', 'ear.R'))


def build(K):
    span, sym, sp = K.span, K.sym, K.spike
    # body: a compact stepped loaf on long legs
    span(-0.30, 0.36, -0.19, 0.19, 0.48, 0.54, 'CR', 'body')        # pale belly
    span(-0.36, 0.42, -0.26, 0.26, 0.54, 0.82, 'F1', 'body')        # core
    sym(-0.30, 0.36, 0.26, 0.30, 0.58, 0.78, 'F3', 'body')           # side step
    span(-0.30, 0.38, -0.20, 0.20, 0.82, 0.87, 'F2', 'body')        # back
    span(-0.40, -0.36, -0.18, 0.18, 0.58, 0.80, 'CR', 'body')       # chest bib
    # white fawn spots: two rows along the back, a scatter on each flank
    for y in (-0.18, 0.02, 0.22):
        sym(y, y + 0.07, 0.07, 0.14, 0.87, 0.885, 'SP', 'body')
    for y, z in ((-0.22, 0.70), (-0.02, 0.72), (0.18, 0.70), (-0.12, 0.62), (0.08, 0.62), (0.26, 0.63)):
        sym(y, y + 0.07, 0.30, 0.31, z, z + 0.06, 'SP', 'body')
    # neck rising to the head
    span(-0.46, -0.28, -0.12, 0.12, 0.80, 1.06, 'F1', 'body')
    span(-0.47, -0.46, -0.08, 0.08, 0.82, 1.02, 'CR', 'body')
    # long thin legs, dark hooves; a haunch on the hind legs
    for sx, s in K.sides():
        for b, y0, y1, top in ((f'leg.{s}', -0.30, -0.18, 0.56), (f'hind.{s}', 0.22, 0.34, 0.58)):
            span(y0, y1, 0.10 * sx, 0.21 * sx, 0.08, top, 'F1', b)
            span(y0 + 0.01, y1 - 0.01, 0.21 * sx, 0.22 * sx, 0.10, 0.36, 'F3', b)   # outer shade
            span(y0 - 0.01, y1 + 0.01, 0.095 * sx, 0.215 * sx, 0.0, 0.08, 'HF', b)
        span(0.16, 0.40, 0.21 * sx, 0.29 * sx, 0.46, 0.76, 'F3', f'hind.{s}')        # haunch
    # tail: short, flicked up, white underside
    span(0.42, 0.50, -0.06, 0.06, 0.72, 0.88, 'F1', 'tail')
    span(0.50, 0.52, -0.05, 0.05, 0.73, 0.86, 'SP', 'tail')
    span(0.43, 0.49, -0.04, 0.04, 0.88, 0.91, 'F4', 'tail')
    # head (scaled 1.35 round the top of the neck)
    span(-0.68, -0.36, -0.22, 0.22, 0.97, 1.26, 'F1', 'head')       # skull
    span(-0.64, -0.40, -0.17, 0.17, 1.26, 1.30, 'F2', 'head')       # crown
    sym(-0.64, -0.42, 0.22, 0.25, 1.00, 1.20, 'F3', 'head')          # cheek step
    span(-0.66, -0.40, -0.16, 0.16, 0.94, 0.97, 'CR', 'head')       # chin
    span(-0.78, -0.68, -0.11, 0.11, 0.98, 1.11, 'F1', 'head')       # snout
    span(-0.76, -0.68, -0.08, 0.08, 1.11, 1.14, 'F2', 'head')
    span(-0.77, -0.68, -0.09, 0.09, 0.95, 0.98, 'CR', 'head')       # pale lower muzzle
    span(-0.80, -0.78, -0.05, 0.05, 1.04, 1.10, 'NS', 'head')       # nose
    span(-0.805, -0.80, -0.02, 0.02, 1.075, 1.09, 'WH', 'head')
    for sx in (1, -1):   # big dark deer eyes
        span(-0.70, -0.68, 0.08 * sx, 0.21 * sx, 1.13, 1.25, 'EY', 'head')
        span(-0.705, -0.70, 0.10 * sx, 0.17 * sx, 1.14, 1.19, 'IR', 'head')
        span(-0.71, -0.70, 0.145 * sx, 0.195 * sx, 1.20, 1.24, 'WH', 'head')
        span(-0.71, -0.70, 0.10 * sx, 0.12 * sx, 1.15, 1.17, 'WH', 'head')
        span(-0.695, -0.68, 0.16 * sx, 0.22 * sx, 1.03, 1.08, 'PK', 'head')   # blush
    # big ears sticking out sideways, pink inside, dark rim at the tip
    for sx, s in K.sides():
        b = f'ear.{s}'
        span(-0.54, -0.46, 0.18 * sx, 0.31 * sx, 1.18, 1.31, 'F1', b)
        span(-0.54, -0.46, 0.31 * sx, 0.42 * sx, 1.23, 1.38, 'F1', b)
        span(-0.535, -0.465, 0.42 * sx, 0.49 * sx, 1.29, 1.42, 'F4', b)
        span(-0.55, -0.54, 0.24 * sx, 0.40 * sx, 1.25, 1.34, 'PK', b)
    # crystal antlers: a two-part beam per side, glowing tips on every tine
    for sx in (1, -1):
        K.limb((0.09 * sx, -0.48, 1.27), (0.19 * sx, -0.46, 1.45), 0.085, 0.085, 'AN', 'head', extend=0.03)
        K.limb((0.19 * sx, -0.46, 1.45), (0.31 * sx, -0.43, 1.58), 0.075, 0.075, 'AN', 'head', extend=0.03)
        sp((0.15 * sx, -0.47, 1.38), (0.35 * sx, -1, 0.7), 0.18, 0.065, 'AL', 'AG', 'head')     # brow tine, forward
        sp((0.24 * sx, -0.45, 1.51), (0.2 * sx, 0.8, 0.7), 0.14, 0.055, 'AL', 'AG', 'head')     # back tine
        sp((0.31 * sx, -0.43, 1.57), (-0.15 * sx, 0.1, 1), 0.20, 0.07, 'AL', 'AG', 'head')      # fork: up
        sp((0.30 * sx, -0.43, 1.57), (1 * sx, 0.1, 0.55), 0.18, 0.065, 'AL', 'AG', 'head')      # fork: out

def idle(f):
    ph = TAU * f / 90
    tw = max(0, S(TAU * f / 45) - 0.8) * 5               # quick ear flick now and then
    return {'body': (1.2 * S(ph), 0, 0), 'head': (-3 * S(ph + 0.6), 7 * S(TAU * f / 90 + 0.4), 8 * S(TAU * f / 90)),
            'ear.L': (0, -14 * tw, 0), 'ear.R': (0, -4 * S(ph * 2), 0),
            'tail': (-10 * max(0, S(TAU * f / 30) - 0.5) * 2, 0, 0)}


def hop(f):    # springy prance: front legs then hind, bounce at the root
    ph = TAU * f / 24; c = math.cos(ph)
    a = 30 * S(ph)
    return {'leg.L': (-a, 0, 0), 'leg.R': (-a * 0.8, 0, 0), 'hind.L': (a, 0, 0), 'hind.R': (a * 0.8, 0, 0),
            'body': (4 * c, 0, 0), 'head': (-4 * c, 0, 0),
            'ear.L': (0, 8 * abs(c), 0), 'ear.R': (0, -8 * abs(c), 0),
            'tail': (-12 * abs(S(ph)), 0, 0),
            'root_loc': (0, 0, 0.12 * abs(S(ph)))}


def cheer(f):  # pronk: crouch, spring straight up with legs tucked, head toss, land and settle
    if f < 8: cr, up = EASE(f / 8), 0
    elif f < 24: u = (f - 8) / 16; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 32: cr, up = S(math.pi * (f - 24) / 8) * 0.8, 0
    else: cr, up = 0, 0
    toss = 14 * S(TAU * max(0, f - 8) / 16) * up
    return {'body': (6 * cr - 8 * up, 0, 0), 'head': (-8 * cr + 12 * up, toss, 0),
            'leg.L': (-35 * up + 8 * cr, 0, 0), 'leg.R': (-35 * up + 8 * cr, 0, 0),
            'hind.L': (35 * up - 8 * cr, 0, 0), 'hind.R': (35 * up - 8 * cr, 0, 0),
            'ear.L': (0, 18 * up, 0), 'ear.R': (0, -18 * up, 0),
            'tail': (-30 * up, 0, 0), 'root_loc': (0, 0, 0.60 * up - 0.08 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (36, cheer)}
PREVIEW = dict(target=(0, -0.10, 1.08), ortho=3.4, shots=[('Cheer', 16), ('Hop', 6)], loop='Idle')
