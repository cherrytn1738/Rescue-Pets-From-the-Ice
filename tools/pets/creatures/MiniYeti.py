# Mini Yeti (Epic): small shaggy yeti with a big grin.
# Copied from the skill's duck example (upright biped). Traits: a small upright white/pale-blue yeti, a blue-grey
# face under a shaggy brow fringe, a BIG wide grin with two little fangs and a pink tongue, stepped shaggy fur
# fringes (shoulders, waist, hem, elbows, sideburns, crown tuft), long arms with big blue-grey hands, big feet.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'MiniYeti'
RARITY = 'Epic'
STUDS = 5.0
# white fur in 4 tones (C2 tops, C1 main, C3 pale-blue sides/fringe undersides, C4 underside) + blue-grey skin
PALETTE = dict(C1='eef4fb', C2='ffffff', C3='c6dbf0', C4='9db6d3', BF='b5d3f0',
               SK='a9bdd8', SD='7589a8', NS='2a2f45', MO='35163a', TG='ff7896', FG='ffffff',
               EY='1a1d2c', IR='3f86e0', WH='ffffff', PK='ff9cc0')
GLOW = set()
EYES = ('EY', 'IR', 'WH', 'MO', 'TG', 'FG')   # the grin stays coloured on a Golden pet too
HP = (0, -0.04, 0.84)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0, 0.30), (0, 0, 0.80), 'root'),
         ('head', HP, (0, -0.04, 1.30), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'arm.{s}', (0.50 * sx, 0.0, 0.80), (0.50 * sx, 0.0, 0.14), 'body'),
              (f'leg.{s}', (0.17 * sx, 0.0, 0.24), (0.17 * sx, 0.0, 0.0), 'root')]
HEAD = dict(scale=1.3, pivot=HP, bones=('head',))


def build(K):
    span, sym = K.span, K.sym
    # legs + big blue-grey feet with pale toes
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.12, 0.12, 0.06 * sx, 0.28 * sx, 0.06, 0.26, 'C1', b)
        span(-0.26, 0.12, 0.05 * sx, 0.29 * sx, 0.0, 0.06, 'SD', b)
        for dx in (0.10, 0.17, 0.24):
            span(-0.29, -0.26, (dx - 0.025) * sx, (dx + 0.025) * sx, 0.0, 0.05, 'SK', b)
    # body: upright pear (wide hips, narrower chest), shaggy stepped fringes round the hem and waist
    span(-0.24, 0.24, -0.30, 0.30, 0.18, 0.24, 'C4', 'body')        # underside
    span(-0.27, 0.27, -0.35, 0.35, 0.24, 0.58, 'C1', 'body')        # hips
    span(-0.24, 0.24, -0.30, 0.30, 0.58, 0.80, 'C1', 'body')        # chest
    span(-0.20, 0.20, -0.26, 0.26, 0.80, 0.86, 'C2', 'body')        # shoulders top
    span(-0.28, -0.24, -0.18, 0.18, 0.60, 0.76, 'BF', 'body')       # pale-blue chest patch
    span(-0.30, -0.27, -0.20, 0.20, 0.30, 0.52, 'BF', 'body')       # pale-blue belly
    for z0, z1, w in ((0.24, 0.32, 0.38), (0.52, 0.60, 0.37)):        # fringe rings (hem, waist)
        span(-0.30, 0.30, -w, w, z0, z1, 'C1', 'body')
        span(-0.28, 0.28, -w + 0.02, w - 0.02, z1, z1 + 0.02, 'C2', 'body')
        for x in (-0.25, 0.0, 0.25):                                  # tufts hanging off the front
            span(-0.31, -0.27, x - 0.06, x + 0.06, z0 - 0.07, z0, 'C3', 'body')
        for y in (-0.15, 0.10):                                       # and off the sides
            sym(y - 0.06, y + 0.06, w - 0.04, w + 0.01, z0 - 0.07, z0, 'C3', 'body')
        for x in (-0.18, 0.18):                                       # and the back
            span(0.27, 0.31, x - 0.06, x + 0.06, z0 - 0.07, z0, 'C3', 'body')
    # long arms hanging a little out from the body: furry, a shoulder tuft, an elbow fringe, big blue-grey hands
    for sx, s in K.sides():
        b = f'arm.{s}'
        span(-0.10, 0.10, 0.42 * sx, 0.58 * sx, 0.50, 0.80, 'C1', b)
        span(-0.12, 0.12, 0.38 * sx, 0.60 * sx, 0.72, 0.86, 'C1', b)          # shoulder fluff
        span(-0.09, 0.09, 0.40 * sx, 0.57 * sx, 0.86, 0.89, 'C2', b)
        span(-0.12, 0.12, 0.60 * sx, 0.63 * sx, 0.68, 0.78, 'C3', b)          # shaggy tuft out the side
        span(-0.12, 0.12, 0.41 * sx, 0.60 * sx, 0.42, 0.50, 'C1', b)          # elbow fringe
        span(-0.12, 0.12, 0.60 * sx, 0.63 * sx, 0.38, 0.46, 'C3', b)
        span(-0.09, 0.09, 0.43 * sx, 0.57 * sx, 0.24, 0.42, 'C1', b)          # forearm
        span(-0.11, 0.11, 0.42 * sx, 0.58 * sx, 0.21, 0.25, 'C3', b)          # cuff
        span(-0.15, 0.10, 0.40 * sx, 0.61 * sx, 0.05, 0.21, 'SK', b)          # big hand
        span(-0.13, 0.08, 0.41 * sx, 0.60 * sx, 0.03, 0.05, 'SD', b)
        for dx in (0.45, 0.505, 0.56):                                         # finger grooves
            span(-0.155, -0.15, (dx - 0.007) * sx, (dx + 0.007) * sx, 0.05, 0.15, 'SD', b)
    # head (scaled 1.3 round the neck): big, wide, shaggy, blue-grey face inside the fur
    span(-0.30, 0.24, -0.35, 0.35, 0.84, 1.20, 'C1', 'head')        # skull
    span(-0.28, 0.22, -0.31, 0.31, 1.20, 1.26, 'C1', 'head')        # rounded top step
    span(-0.24, 0.18, -0.25, 0.25, 1.26, 1.30, 'C2', 'head')        # crown
    K.spike((0, -0.06, 1.28), (0, 0.1, 1), 0.22, 0.16, 'C1', 'C2', 'head')        # shaggy crest: middle tuft
    for sx in (1, -1):
        K.spike((0.13 * sx, -0.02, 1.27), (0.6 * sx, 0.1, 1), 0.16, 0.12, 'C1', 'C2', 'head')
        K.spike((0.34 * sx, -0.10, 1.10), (sx, -0.1, 0.7), 0.18, 0.12, 'C1', 'C3', 'head')   # shag spikes out the sides
        K.spike((0.34 * sx, 0.06, 0.94), (sx, 0.1, 0.25), 0.16, 0.11, 'C1', 'C3', 'head')
    sym(-0.26, 0.20, 0.35, 0.37, 0.90, 1.18, 'C1', 'head')           # side step
    for y in (-0.20, 0.04):                                           # jagged shag on the side
        sym(y, y + 0.12, 0.35, 0.39, 0.84, 0.90, 'C3', 'head')
    span(0.24, 0.28, -0.29, 0.29, 0.92, 1.20, 'C1', 'head')         # shag down the back of the head
    for x in (-0.20, 0.0, 0.20):
        span(0.24, 0.29, x - 0.06, x + 0.06, 0.82, 0.92, 'C3', 'head')
    sym(-0.20, 0.08, 0.37, 0.41, 0.80, 0.90, 'C3', 'head')           # sideburns hang below the jaw
    span(-0.26, 0.20, -0.30, 0.30, 0.81, 0.84, 'C4', 'head')        # chin underside
    span(-0.32, -0.30, -0.27, 0.27, 0.86, 1.18, 'SK', 'head')       # face plate
    span(-0.31, -0.30, -0.29, 0.29, 0.84, 0.88, 'SD', 'head')       # chin shade
    span(-0.36, -0.30, -0.33, 0.33, 1.18, 1.26, 'C1', 'head')       # shaggy brow fringe
    span(-0.34, -0.30, -0.29, 0.29, 1.26, 1.29, 'C2', 'head')
    for x in (-0.24, 0.0, 0.24):                                      # fringe teeth over the face
        span(-0.36, -0.32, x - 0.05, x + 0.05, 1.14, 1.18, 'C3', 'head')
    sym(-0.36, -0.30, 0.27, 0.33, 0.90, 1.18, 'C1', 'head')          # fur framing the face sides
    # face: big eyes under the fringe, small nose, BIG grin with 2 fangs and a tongue, blush
    for sx in (1, -1):
        span(-0.32, -0.30, 0.05 * sx, 0.18 * sx, 1.02, 1.15, 'EY', 'head')
        span(-0.325, -0.32, 0.07 * sx, 0.14 * sx, 1.03, 1.09, 'IR', 'head')
        span(-0.33, -0.32, 0.125 * sx, 0.17 * sx, 1.10, 1.14, 'WH', 'head')
        span(-0.33, -0.32, 0.065 * sx, 0.085 * sx, 1.035, 1.055, 'WH', 'head')
        span(-0.325, -0.32, 0.19 * sx, 0.25 * sx, 0.99, 1.03, 'PK', 'head')
    span(-0.33, -0.32, -0.035, 0.035, 1.00, 1.035, 'NS', 'head')
    span(-0.325, -0.32, -0.19, 0.19, 0.88, 0.98, 'MO', 'head')      # wide open grin
    sym(-0.325, -0.32, 0.19, 0.22, 0.94, 1.00, 'MO', 'head')         # upturned corners
    sym(-0.325, -0.32, 0.22, 0.245, 0.98, 1.025, 'MO', 'head')
    span(-0.33, -0.325, -0.10, 0.10, 0.88, 0.915, 'TG', 'head')     # tongue
    sym(-0.337, -0.325, 0.07, 0.12, 0.935, 0.98, 'FG', 'head')       # two little fangs from the top lip
    sym(-0.337, -0.325, 0.08, 0.11, 0.915, 0.935, 'FG', 'head')


def idle(f):    # breathing bob, a chuckly head tilt, arms sway like a little ape
    ph = TAU * f / 90
    ch = max(0, S(TAU * f / 45) - 0.7) * 3.3
    return {'body': (1.5 * S(ph), 0, 2 * S(ph * 0.5)), 'head': (-3 * S(ph + 0.6) - 4 * ch, 8 * S(ph * 0.5 + 1), 0),
            'arm.L': (8 * S(ph), -4 - 3 * S(ph), 0), 'arm.R': (-8 * S(ph), 4 + 3 * S(ph), 0),
            'root_loc': (0, 0, 0.01 * ch * abs(S(TAU * f / 6)))}


def hop(f):    # bouncy waddle-hop: rolls side to side, arms swing opposite the legs
    ph = TAU * f / 24; c = math.cos(ph)
    return {'root': (0, 8 * S(ph), 4 * c), 'body': (4, 0, 0), 'head': (-4 * abs(S(ph)), -5 * S(ph), 0),
            'leg.L': (-28 * S(ph), 0, 0), 'leg.R': (28 * S(ph), 0, 0),
            'arm.L': (30 * S(ph), -6, 0), 'arm.R': (-30 * S(ph), 6, 0),
            'root_loc': (0, 0, 0.10 * abs(S(ph)))}


def cheer(f):  # crouch -> jump with both arms thrown up -> land, arms wave at the top
    if f < 8: cr, up = EASE(f / 8), 0
    elif f < 26: u = (f - 8) / 18; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 34: cr, up = S(math.pi * (f - 26) / 8) * 0.8, 0
    else: cr, up = 0, 0
    arms = EASE(min(1, max(0, (f - 4) / 8))) * EASE(min(1, max(0, (38 - f) / 8)))
    wv = 15 * S(TAU * f / 10) * arms
    return {'body': (6 * cr - 8 * up, 0, 0), 'head': (-6 * cr + 12 * up, 0, 0),
            'arm.L': (0, -145 * arms - wv, 0), 'arm.R': (0, 145 * arms + wv, 0),
            'leg.L': (-12 * up + 8 * cr, 0, 0), 'leg.R': (12 * up + 8 * cr, 0, 0),
            'root_loc': (0, 0, 0.55 * up - 0.06 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (38, cheer)}
PREVIEW = dict(target=(0, 0.0, 0.90), ortho=2.8, shots=[('Cheer', 17), ('Hop', 6)], loop='Idle')
