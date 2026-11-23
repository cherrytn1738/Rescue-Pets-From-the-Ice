# Seal Pup (Uncommon): round white pup with big dark eyes.
# Copied from the skill's axolotl example (low crawler). Traits: a round white pup lying on its belly, a big round head
# with very big dark eyes, a puffy white muzzle with a dark nose and whisker dots, grey speckles, slate-grey front
# flippers and a pair of tail flippers splayed out behind.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'SealPup'
RARITY = 'Uncommon'
STUDS = 5.0
# white fur in 4 tones (C2 tops, C1 main, C3 sides, C4 underside) + slate flippers (FL, FD), grey speckles (SP),
# dark nose / whisker dots (NS, DK), pink blush and tongue
PALETTE = dict(C1='f3f6fa', C2='ffffff', C3='d6dfe9', C4='a5b3c4', MZ='ffffff',
               FL='8fa3bb', FD='6c7f98', SP='66727f', NS='20242c', DK='2c323c', PK='ff9fb4', TG='ff7d9c',
               EY='14171f', IR='3b4c6e', WH='ffffff')
GLOW = set()
HP = (0, -0.28, 0.34)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.05, 0.20), (0, 0.05, 0.50), 'root'),
         ('head', HP, (0, -0.28, 0.72), 'body'),
         ('tail', (0, 0.38, 0.18), (0, 0.58, 0.12), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'flip.{s}', (0.30 * sx, -0.16, 0.16), (0.50 * sx, -0.02, 0.04), 'body'),
              (f'hflip.{s}', (0.05 * sx, 0.52, 0.12), (0.24 * sx, 0.74, 0.10), 'tail')]
HEAD = dict(scale=1.4, pivot=HP, bones=('head',))

SPECKLES = [  # (x, y, z, size): grey dots on the top and sides so the white pup isn't a blank blob
    (0.10, -0.12, 0.57, 0.05), (-0.12, 0.02, 0.57, 0.06), (0.05, 0.12, 0.57, 0.045), (-0.04, -0.20, 0.57, 0.04),
    (0.23, 0.06, 0.53, 0.045), (-0.23, -0.10, 0.53, 0.04), (0.10, 0.32, 0.42, 0.045),
    (0.37, 0.0, 0.30, 0.05), (-0.37, 0.12, 0.24, 0.045), (0.37, -0.14, 0.18, 0.04)]
HEAD_SPECKLES = [(0.12, -0.44, 0.75, 0.04), (-0.08, -0.36, 0.75, 0.045), (-0.15, -0.50, 0.75, 0.035),
                 (0.33, -0.38, 0.54, 0.04), (-0.33, -0.46, 0.50, 0.035)]


def build(K):
    span, sym = K.span, K.sym
    # body: round loaf lying on its belly, tapering to the tail
    span(-0.24, 0.30, -0.24, 0.24, 0.0, 0.06, 'C4', 'body')
    span(-0.30, 0.26, -0.34, 0.34, 0.06, 0.46, 'C1', 'body')
    sym(-0.24, 0.22, 0.34, 0.37, 0.10, 0.40, 'C3', 'body')
    span(-0.26, 0.24, -0.28, 0.28, 0.46, 0.53, 'C1', 'body')
    span(-0.18, 0.18, -0.20, 0.20, 0.53, 0.57, 'C2', 'body')
    span(0.26, 0.40, -0.27, 0.27, 0.04, 0.38, 'C1', 'body')
    sym(0.26, 0.38, 0.27, 0.29, 0.08, 0.32, 'C3', 'body')
    span(0.26, 0.38, -0.19, 0.19, 0.38, 0.42, 'C2', 'body')
    for x, y, z, w in SPECKLES:
        w *= 1.4
        if abs(x) < 0.36:
            span(y - w / 2, y + w / 2, x - w / 2, x + w / 2, z, z + 0.006, 'SP', 'body')
        else:
            sx = 1 if x > 0 else -1
            span(y - w / 2, y + w / 2, x, x + 0.006 * sx, z - w / 2, z + w / 2, 'SP', 'body')
    # tail: short taper, then two wide flippers fanned out in a V
    span(0.40, 0.54, -0.18, 0.18, 0.05, 0.26, 'C1', 'tail')
    span(0.40, 0.52, -0.12, 0.12, 0.26, 0.29, 'C2', 'tail')
    span(0.40, 0.54, -0.14, 0.14, 0.02, 0.05, 'C4', 'tail')
    for sx, s in K.sides():
        b = f'hflip.{s}'
        K.limb((0.05 * sx, 0.50, 0.12), (0.22 * sx, 0.70, 0.10), 0.18, 0.07, 'FL', b)
        K.limb((0.20 * sx, 0.66, 0.10), (0.30 * sx, 0.79, 0.09), 0.27, 0.06, 'FD', b)   # wide fin tip
    # front flippers: flat paddles out to the sides, dark claw dots
    for sx, s in K.sides():
        b = f'flip.{s}'
        K.limb((0.28 * sx, -0.18, 0.18), (0.50 * sx, -0.04, 0.04), 0.18, 0.08, 'FL', b, extend=0.04)
        K.limb((0.46 * sx, -0.07, 0.06), (0.56 * sx, 0.0, 0.02), 0.16, 0.06, 'FD', b)
    # head (scaled 1.4 around the neck): big and round, raised off the ground
    span(-0.36, -0.20, -0.24, 0.24, 0.18, 0.52, 'C1', 'head')
    span(-0.62, -0.24, -0.30, 0.30, 0.26, 0.66, 'C1', 'head')
    span(-0.58, -0.28, -0.25, 0.25, 0.66, 0.72, 'C1', 'head')
    span(-0.54, -0.32, -0.18, 0.18, 0.72, 0.75, 'C2', 'head')
    sym(-0.58, -0.28, 0.30, 0.33, 0.32, 0.60, 'C3', 'head')
    span(-0.58, -0.30, -0.22, 0.22, 0.23, 0.26, 'C4', 'head')
    span(-0.66, -0.62, -0.25, 0.25, 0.30, 0.62, 'C1', 'head')        # rounded front plate
    span(-0.65, -0.62, -0.20, 0.20, 0.62, 0.66, 'C1', 'head')
    span(-0.65, -0.62, -0.20, 0.20, 0.27, 0.30, 'C3', 'head')
    for x, y, z, w in HEAD_SPECKLES:
        w *= 1.3
        if abs(x) < 0.3:
            span(y - w / 2, y + w / 2, x - w / 2, x + w / 2, z, z + 0.006, 'SP', 'head')
        else:
            sx = 1 if x > 0 else -1
            span(y - w / 2, y + w / 2, x, x + 0.006 * sx, z - w / 2, z + w / 2, 'SP', 'head')
    # face: very big dark eyes, puffy muzzle, dark nose, whisker dots, blush
    for sx in (1, -1):
        span(-0.68, -0.66, 0.06 * sx, 0.24 * sx, 0.44, 0.62, 'EY', 'head')
        span(-0.685, -0.68, 0.08 * sx, 0.17 * sx, 0.45, 0.52, 'IR', 'head')
        span(-0.69, -0.68, 0.16 * sx, 0.225 * sx, 0.55, 0.605, 'WH', 'head')
        span(-0.69, -0.68, 0.085 * sx, 0.11 * sx, 0.46, 0.485, 'WH', 'head')
        span(-0.675, -0.66, 0.19 * sx, 0.25 * sx, 0.36, 0.41, 'PK', 'head')
        span(-0.72, -0.66, 0.0, 0.13 * sx, 0.31, 0.42, 'MZ', 'head')                     # muzzle puff
        for x, z in ((0.07, 0.37), (0.10, 0.34), (0.105, 0.39)):
            span(-0.725, -0.72, (x - 0.009) * sx, (x + 0.009) * sx, z - 0.009, z + 0.009, 'DK', 'head')
    span(-0.70, -0.66, -0.07, 0.07, 0.42, 0.44, 'MZ', 'head')
    span(-0.745, -0.72, -0.05, 0.05, 0.395, 0.45, 'NS', 'head')      # nose
    span(-0.75, -0.745, -0.03, -0.005, 0.43, 0.445, 'WH', 'head')
    span(-0.70, -0.66, -0.05, 0.05, 0.29, 0.31, 'TG', 'head')         # little tongue under the muzzle


def idle(f):
    ph = TAU * f / 90
    pat = max(0, S(TAU * f / 45) - 0.7) * 3.3                         # flipper pat now and then
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-3 * S(ph + 0.6), 8 * S(TAU * f / 180), 5 * S(TAU * f / 180 + 1)),
            'flip.L': (0, -18 * pat * abs(S(TAU * f / 8)), 0), 'flip.R': (0, 4 * S(ph), 0),
            'tail': (-4 * S(ph - 0.5), 0, 4 * S(ph)), 'hflip.L': (0, 0, 6 * S(ph * 2)), 'hflip.R': (0, 0, -6 * S(ph * 2))}


def hop(f):    # belly scoot: the front pushes up, then the rear humps forward (galumph), flippers push back
    ph = TAU * f / 24; up = max(0, S(ph)); c = math.cos(ph)
    return {'body': (-8 * S(ph), 0, 0), 'head': (8 * S(ph) - 4 * up, 0, 0),
            'flip.L': (-25 * c, 0, -15 * up), 'flip.R': (-25 * c, 0, 15 * up),
            'tail': (-14 * S(ph - 1.2), 0, 0), 'hflip.L': (-10 * S(ph - 1.6), 0, 0), 'hflip.R': (-10 * S(ph - 1.6), 0, 0),
            'root_loc': (0, 0, 0.10 * up + 0.02 * max(0, -S(ph)))}


def cheer(f):  # bounce up and clap the flippers, head thrown back, tail flippers wave
    t = EASE(max(0, min(f / 6, 1, (36 - f) / 6)))
    b = abs(S(TAU * f / 18))
    cl = abs(S(TAU * f / 9))
    return {'body': (-10 * b * t, 0, 0), 'head': (-14 * t, 10 * t * S(TAU * f / 36), 0),
            'flip.L': (0, -50 * cl * t, -30 * t), 'flip.R': (0, 50 * cl * t, 30 * t),
            'tail': (-25 * t - 8 * b * t, 0, 0), 'hflip.L': (0, 0, 20 * S(TAU * f / 9) * t), 'hflip.R': (0, 0, -20 * S(TAU * f / 9) * t),
            'root_loc': (0, 0, 0.30 * b * t)}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'Cheer': (36, cheer)}
PREVIEW = dict(target=(0, 0.05, 0.40), ortho=2.6, shots=[('Cheer', 13), ('Hop', 6)], loop='Idle')
