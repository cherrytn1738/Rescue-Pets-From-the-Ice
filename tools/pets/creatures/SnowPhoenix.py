# Snow Phoenix (Legendary): white bird with icy flame feathers.
# Copied from the skill's owl example. Traits: an upright white bird with a sweeping crest and long tail plumes
# shaped like flames, each ending in stepped icy-cyan flame tips that glow (GLOW on the tips only), flame-tipped
# wings that flap in Cheer, flame tufts at the sides of the head, slate legs and a gold beak so the white body doesn't read as a blob.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'SnowPhoenix'
RARITY = 'Legendary'
STUDS = 5.0
# white 4 tones (W2 tops, W1 main, W3 sides/wings, W4 underside), icy flame: FL light cyan, FM mid blue,
# FT glowing tips; BK/BD gold beak, LG/LD slate legs
PALETTE = dict(W1='f4f7fc', W2='ffffff', W3='d8e2ef', W4='aebdd2', FL='a8ecff', FM='4fb6ff', FT='5fe8ff',
               BK='ffbf3f', BD='d98a12', LG='4e5d80', LD='35415e',
               EY='1a1e36', IR='37b4ff', WH='ffffff', PK='ffa3bd')
GLOW = {'FT'}
HP = (0, -0.04, 0.86)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.0, 0.40), (0, 0.0, 0.80), 'root'),
         ('head', HP, (0, -0.04, 1.30), 'body'),
         ('crest', (0, -0.06, 1.28), (0, 0.20, 1.60), 'head'),
         ('tail', (0, 0.36, 0.42), (0, 0.80, 0.60), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'wing.{s}', (0.40 * sx, -0.16, 0.78), (0.40 * sx, 0.40, 0.78), 'body'),
              (f'leg.{s}', (0.16 * sx, -0.06, 0.20), (0.16 * sx, -0.06, 0.0), 'root')]
HEAD = dict(scale=1.35, pivot=HP, bones=('head', 'crest'))


def build(K):
    span, sym = K.span, K.sym
    # body: upright stepped egg
    span(-0.26, 0.26, -0.28, 0.28, 0.16, 0.24, 'W4', 'body')        # underside
    span(-0.34, 0.32, -0.38, 0.38, 0.24, 0.80, 'W1', 'body')        # core
    sym(-0.26, 0.24, 0.38, 0.41, 0.30, 0.74, 'W3', 'body')           # side step
    span(-0.26, 0.28, -0.30, 0.30, 0.80, 0.88, 'W2', 'body')        # shoulders
    span(0.32, 0.38, -0.28, 0.28, 0.30, 0.76, 'W3', 'body')         # back round
    span(-0.40, -0.34, -0.28, 0.28, 0.30, 0.78, 'W2', 'body')       # chest puff
    span(-0.44, -0.40, -0.18, 0.18, 0.38, 0.70, 'W2', 'body')
    # icy flame emblem on the chest: a small stepped flame
    span(-0.45, -0.44, -0.08, 0.08, 0.42, 0.50, 'FL', 'body')
    span(-0.45, -0.44, -0.05, 0.05, 0.50, 0.58, 'FL', 'body')
    span(-0.45, -0.44, -0.02, 0.02, 0.58, 0.64, 'FL', 'body')
    # tail: three long flame plumes sweeping back and up, white into cyan into blue, glowing stepped tips
    span(0.36, 0.56, -0.10, 0.10, 0.30, 0.48, 'W1', 'tail')         # centre plume
    span(0.54, 0.72, -0.10, 0.10, 0.36, 0.56, 'W3', 'tail')
    span(0.70, 0.88, -0.09, 0.09, 0.46, 0.68, 'FL', 'tail')
    span(0.84, 1.00, -0.08, 0.08, 0.58, 0.80, 'FM', 'tail')
    span(0.90, 1.02, -0.07, 0.07, 0.80, 0.92, 'FT', 'tail')
    span(0.96, 1.04, -0.04, 0.04, 0.92, 1.02, 'FT', 'tail')
    for sx in (1, -1):                                                # side plumes, splayed out
        span(0.36, 0.52, 0.10 * sx, 0.24 * sx, 0.28, 0.44, 'W3', 'tail')
        span(0.50, 0.66, 0.16 * sx, 0.30 * sx, 0.32, 0.50, 'W1', 'tail')
        span(0.64, 0.78, 0.22 * sx, 0.36 * sx, 0.40, 0.60, 'FL', 'tail')
        span(0.74, 0.86, 0.26 * sx, 0.38 * sx, 0.52, 0.70, 'FM', 'tail')
        span(0.78, 0.88, 0.28 * sx, 0.37 * sx, 0.70, 0.80, 'FT', 'tail')
        span(0.82, 0.88, 0.31 * sx, 0.35 * sx, 0.80, 0.88, 'FT', 'tail')
    # folded wings: white, light-cyan lower edge, long primaries sweeping back into flame tips
    for sx, s in K.sides():
        b = f'wing.{s}'
        span(-0.22, 0.30, 0.40 * sx, 0.48 * sx, 0.40, 0.78, 'W3', b)
        span(-0.18, 0.26, 0.40 * sx, 0.48 * sx, 0.78, 0.82, 'W2', b)
        span(-0.20, 0.30, 0.40 * sx, 0.48 * sx, 0.34, 0.40, 'FL', b)
        span(0.30, 0.46, 0.40 * sx, 0.47 * sx, 0.40, 0.72, 'W3', b)
        span(0.46, 0.60, 0.40 * sx, 0.46 * sx, 0.44, 0.66, 'FL', b)
        span(0.58, 0.70, 0.41 * sx, 0.45 * sx, 0.48, 0.64, 'FM', b)
        span(0.68, 0.76, 0.41 * sx, 0.45 * sx, 0.52, 0.62, 'FT', b)
        for z0 in (0.66, 0.54):
            span(-0.16, 0.30, 0.48 * sx, 0.49 * sx, z0, z0 + 0.03, 'W4', b)
    # neck + head (scaled 1.35 around the neck)
    span(-0.24, 0.18, -0.24, 0.24, 0.84, 0.92, 'W1', 'head')
    span(-0.34, 0.24, -0.32, 0.32, 0.92, 1.24, 'W1', 'head')        # skull
    sym(-0.28, 0.18, 0.32, 0.36, 0.96, 1.20, 'W3', 'head')           # cheek step
    span(-0.30, 0.20, -0.26, 0.26, 1.24, 1.30, 'W2', 'head')        # crown
    span(0.24, 0.28, -0.26, 0.26, 0.96, 1.20, 'W3', 'head')         # back of head
    for sx in (1, -1):   # eyes: dark block, icy iris, 2 shines
        span(-0.36, -0.34, 0.08 * sx, 0.22 * sx, 1.02, 1.16, 'EY', 'head')
        span(-0.365, -0.36, 0.10 * sx, 0.18 * sx, 1.03, 1.10, 'IR', 'head')
        span(-0.37, -0.36, 0.15 * sx, 0.21 * sx, 1.11, 1.15, 'WH', 'head')
        span(-0.37, -0.36, 0.105 * sx, 0.125 * sx, 1.045, 1.065, 'WH', 'head')
        span(-0.355, -0.34, 0.22 * sx, 0.29 * sx, 0.97, 1.01, 'PK', 'head')   # blush
        # flame tufts sweeping back off the sides of the head
        span(0.02, 0.20, 0.36 * sx, 0.42 * sx, 1.12, 1.22, 'FL', 'head')
        span(0.12, 0.26, 0.37 * sx, 0.42 * sx, 1.22, 1.30, 'FM', 'head')
        span(0.20, 0.28, 0.38 * sx, 0.41 * sx, 1.30, 1.35, 'FT', 'head')
    # gold beak, small and hooked
    span(-0.44, -0.34, -0.06, 0.06, 0.98, 1.06, 'BK', 'head')
    span(-0.48, -0.44, -0.04, 0.04, 0.96, 1.04, 'BK', 'head')
    span(-0.50, -0.47, -0.025, 0.025, 0.93, 0.99, 'BD', 'head')
    # crest: a big flame plume sweeping up and back off the crown, two shorter side plumes
    span(-0.24, 0.02, -0.08, 0.08, 1.30, 1.42, 'W1', 'crest')
    span(-0.18, 0.10, -0.08, 0.08, 1.42, 1.52, 'W2', 'crest')
    span(-0.08, 0.20, -0.07, 0.07, 1.52, 1.60, 'FL', 'crest')
    span(0.06, 0.30, -0.07, 0.07, 1.58, 1.66, 'FM', 'crest')
    span(0.20, 0.34, -0.06, 0.06, 1.66, 1.72, 'FT', 'crest')
    span(0.28, 0.36, -0.04, 0.04, 1.72, 1.78, 'FT', 'crest')
    for sx in (1, -1):
        span(-0.20, 0.00, 0.08 * sx, 0.18 * sx, 1.30, 1.38, 'W1', 'crest')
        span(-0.12, 0.10, 0.09 * sx, 0.18 * sx, 1.38, 1.46, 'FL', 'crest')
        span(0.00, 0.18, 0.10 * sx, 0.18 * sx, 1.44, 1.52, 'FM', 'crest')
        span(0.12, 0.24, 0.11 * sx, 0.17 * sx, 1.50, 1.57, 'FT', 'crest')
    # slate legs and three-toed feet
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.10, 0.0, 0.11 * sx, 0.21 * sx, 0.06, 0.20, 'LG', b)
        span(-0.16, 0.02, 0.10 * sx, 0.22 * sx, 0.0, 0.06, 'LG', b)
        for dx in (0.11, 0.16, 0.21):
            span(-0.26, -0.16, (dx - 0.022) * sx, (dx + 0.022) * sx, 0.0, 0.045, 'LD', b)


def idle(f):   # breathing, crest and tail plumes flicker like flames, a slow wing ruffle
    ph = TAU * f / 90
    fl = S(TAU * f / 30)
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 0, 10 * S(TAU * f / 180)),
            'crest': (5 * fl, 0, 4 * S(TAU * f / 45)), 'tail': (4 * S(ph * 2), 0, 6 * S(TAU * f / 45 + 1)),
            'wing.L': (0, -3 * S(ph) - 2, 0), 'wing.R': (0, 3 * S(ph) + 2, 0)}


def hop(f):    # little flutter-hop: bounce with quick half flaps
    ph = TAU * f / 24
    up = abs(S(ph))
    w = 0.5 + 0.5 * S(TAU * f / 12 - math.pi / 2)
    return {'body': (4 - 4 * up, 0, 0), 'head': (-3 * up, 0, 0), 'crest': (8 * up, 0, 0),
            'leg.L': (-25 * up, 0, 0), 'leg.R': (-25 * up, 0, 0), 'tail': (-10 * up, 0, 0),
            'wing.L': (0, -10 - 35 * w, 0), 'wing.R': (0, 10 + 35 * w, 0),
            'root_loc': (0, 0, 0.22 * up)}


def cheer(f):  # crouch, then jump with big wing flaps, crest and tail fanning
    if f < 8: cr, up = EASE(f / 8), 0
    elif f < 30: u = (f - 8) / 22; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 36: cr, up = S(math.pi * (f - 30) / 6) * 0.6, 0
    else: cr, up = 0, 0
    w = 0.5 - 0.5 * math.cos(TAU * (f - 8) * 3 / 22) if 8 <= f < 30 else 0
    return {'body': (8 * cr - 8 * up, 0, 0), 'head': (-6 * cr + 10 * up, 0, 0), 'crest': (14 * up, 0, 0),
            'leg.L': (-30 * up, 0, 0), 'leg.R': (-30 * up, 0, 0), 'tail': (-16 * up, 0, 0),
            'wing.L': (0, -15 * cr - 95 * w * up - 10 * up, 0), 'wing.R': (0, 15 * cr + 95 * w * up + 10 * up, 0),
            'root_loc': (0, 0, 0.70 * up - 0.06 * cr)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (40, cheer)}
PREVIEW = dict(target=(0, 0.1, 1.05), ortho=3.1, shots=[('Cheer', 19), ('Hop', 6)], loop='Idle')
