"""make_ice_textures.py - the ice block's textures (tools/blender/ice_block.py maps its meshes onto them).

    python tools/make_ice_textures.py

Writes assets/textures/ice/:
  IceBlueAtlas.png  512 x 512, the Blue Ice block's atlas. Transparent where the ice is clear: Roblox honours
                    a MeshPart texture's alpha only while the part's Transparency is above 0, so the shell and
                    the inner bubbles run at Transparency 0.02 (IceLooks) and the alpha does the rest.
      S  x 0-255, y 0-511     a side face, box-projected (u across the face, v up it): deep blue at the base,
                              pale at the top, frosty edges, a clear middle, frost streaks and two cartoon
                              glints at the top left.
      G  x 256-511, y 0-255   eight gradient columns (32 px each, v = height): facets pick a column for their
                              hue and how clear they are (0 frosty, 1 semi, 2/3/5 equally clear in blue, cyan and
                              violet-blue, 4 frosty cyan, 6 deep, 7 white frost).
      P  x 256-511, y 256-479 flat swatches 32 x 32 (SWATCHES below, row by row).
      K  x 256-511, y 480-511 the crack strip: across the crack (u) a dark edge, a white core, a dark edge.
  IceGlow.png       256 x 256, a soft round glow (white): a broad body round the creature, falling smoothly to
                    exactly 0 at the rim.
  IceShimmer.png    256 x 256, one soft diagonal band (white), scrolled across the faces as a slow shimmer.
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "textures", "ice")

# Flat swatches in region P, row by row (8 per row). (name, (r, g, b), alpha 0-1). The Blender script reads this
# table from here (keep names stable: meshes are mapped to them).
SWATCHES = [
    # row 0: snow and frost
    ("SnowWhite", (246, 251, 255), 1.0), ("SnowShade", (214, 233, 250), 1.0), ("SnowBlue", (186, 218, 244), 1.0),
    ("FrostWhite", (232, 245, 255), 0.9), ("BubbleWhite", (240, 250, 255), 0.5), ("StreakWhite", (245, 251, 255), 0.3),
    ("CrystalPale", (205, 243, 255), 1.0), ("CrystalCyan", (130, 232, 255), 1.0),
    # row 1: ice blues (opaque: crystals and icicles)
    ("CrystalDeep", (72, 170, 236), 1.0), ("IceBlue", (160, 214, 246), 1.0), ("GlacierBlue", (92, 180, 232), 1.0),
    ("DeepIce", (48, 126, 194), 1.0), ("NavyIce", (30, 64, 112), 1.0), ("White", (255, 255, 255), 1.0),
    ("CrystalGlass", (170, 238, 255), 0.72), ("CrystalGlassDeep", (90, 190, 245), 0.8),
    # row 2: frosty rims and tops
    ("RimFrost", (220, 240, 255), 0.95), ("TopFrost", (226, 243, 255), 0.88), ("BaseDeep", (40, 98, 176), 0.9),
    ("SideFrost", (180, 222, 250), 0.8), ("WindowClear", (170, 220, 250), 0.22), ("Clear", (190, 230, 255), 0.12),
    ("FrostBlue", (150, 205, 245), 0.7), ("Glint", (255, 255, 255), 0.85),
]
ATLAS = 512


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def gradient(stops, t):
    """Colour stops [(t, (r, g, b)), ...] sampled at t (array) -> (..., 3) floats 0-255."""
    t = np.asarray(t, dtype=float)
    out = np.zeros(t.shape + (3,))
    xs = [s[0] for s in stops]
    for c in range(3):
        out[..., c] = np.interp(t, xs, [s[1][c] for s in stops])
    return out


def blob_noise(shape, seed, scale, octaves=3):
    """Smooth value noise in 0-1 (bilinear-upscaled random grids)."""
    rng = np.random.default_rng(seed)
    h, w = shape
    total = np.zeros(shape)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        cells = max(2, int(scale * (2 ** o)))
        grid = rng.random((cells + 1, cells + 1))
        img = Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
        total += amp * np.asarray(img, dtype=float) / 255
        norm += amp
        amp *= 0.5
    return total / norm


SIDE_STOPS = [(0.0, (34, 92, 182)), (0.18, (52, 128, 210)), (0.45, (104, 178, 236)), (0.75, (170, 222, 250)), (1.0, (228, 246, 255))]


def side_region():
    """Region S: 256 x 512 (u across, v up). Returns RGBA floats (0-255, alpha 0-1)."""
    h, w = 512, 256
    v = 1 - (np.arange(h)[:, None] + 0.5) / h  # 1 at the top row
    u = (np.arange(w)[None, :] + 0.5) / w
    u, v = np.broadcast_to(u, (h, w)), np.broadcast_to(v, (h, w))
    rgb = gradient(SIDE_STOPS, v)
    # frosty edges, a clear middle: distance to the edge in face units (the face is 0.8 as wide as tall)
    dx = np.minimum(u, 1 - u) * 0.8
    d_bottom, d_top = v, 1 - v
    edge = np.minimum(dx / 0.11, np.minimum(d_bottom / 0.07, d_top / 0.12))
    frame = 1 - smoothstep(0.0, 1.0, edge)  # 1 at the rim, 0 inside
    alpha = 0.36 + 0.56 * frame
    alpha += 0.22 * (1 - smoothstep(0.0, 0.2, v))  # a denser base
    # frost: soft blotches near the rim and a few streaks across
    frost = blob_noise((h, w), 7, 3)
    alpha += 0.12 * frost * (0.4 + frame)
    rng = np.random.default_rng(21)
    yy, xx = np.mgrid[0:h, 0:w]
    streak = np.zeros((h, w))
    for _ in range(7):
        cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        angle = rng.uniform(-0.9, -0.4) if rng.random() < 0.6 else rng.uniform(0.4, 0.9)
        length, width = rng.uniform(60, 140), rng.uniform(2.0, 4.5)
        ca, sa = np.cos(angle), np.sin(angle)
        along = (xx - cx) * ca + (yy - cy) * sa
        across = -(xx - cx) * sa + (yy - cy) * ca
        s = np.exp(-(across / width) ** 2) * np.clip(1 - (along / length) ** 2, 0, 1)
        # keep streaks out of the very middle (the creature)
        mid = np.exp(-(((xx - w / 2) / (w * 0.22)) ** 2 + ((yy - h * 0.52) / (h * 0.24)) ** 2))
        streak = np.maximum(streak, s * (1 - 0.8 * mid))
    alpha += 0.28 * streak
    rgb = rgb + (255 - rgb) * (0.55 * streak)[..., None] + (255 - rgb) * (0.35 * frame)[..., None]
    # two cartoon glints at the top left (and a small one at the bottom right)
    glint = np.zeros((h, w))
    for (cx, cy, length, width, angle) in [(62, 92, 70, 7.0, -0.78), (92, 70, 40, 3.8, -0.78), (205, 430, 26, 3.2, -0.78)]:
        ca, sa = np.cos(angle), np.sin(angle)
        along = (xx - cx) * ca + (yy - cy) * sa
        across = -(xx - cx) * sa + (yy - cy) * ca
        glint = np.maximum(glint, smoothstep(1.0, 0.6, np.abs(across) / width) * smoothstep(1.0, 0.7, np.abs(along) / length))
    alpha = np.maximum(alpha, 0.85 * glint)
    rgb = rgb + (255 - rgb) * glint[..., None]
    return rgb, np.clip(alpha, 0, 1)


CYAN_STOPS = [(0, (40, 140, 200)), (0.5, (110, 215, 240)), (1, (205, 248, 255))]
VIOLET_STOPS = [(0, (40, 80, 180)), (0.5, (96, 150, 235)), (1, (178, 210, 255))]
GRADIENT_COLUMNS = [  # (stops, alpha): 0 frosty, 1 semi, 2/3/5 equally clear in three blues, 4 frosty cyan, 6 deep, 7 white
    (SIDE_STOPS, 0.9), (SIDE_STOPS, 0.66), (SIDE_STOPS, 0.42), (CYAN_STOPS, 0.42), (CYAN_STOPS, 0.88), (VIOLET_STOPS, 0.42),
    ([(0, (28, 60, 150)), (0.5, (60, 118, 210)), (1, (130, 185, 245))], 0.88),
    ([(0, (190, 222, 248)), (0.6, (226, 243, 255)), (1, (246, 251, 255))], 0.94),
]


def atlas():
    rgb = np.zeros((ATLAS, ATLAS, 3))
    alpha = np.zeros((ATLAS, ATLAS))
    s_rgb, s_alpha = side_region()
    rgb[:, 0:256], alpha[:, 0:256] = s_rgb, s_alpha
    # G: gradient columns, v = height (row 0 = the top)
    v = 1 - (np.arange(256)[:, None] + 0.5) / 256
    for i, (stops, a) in enumerate(GRADIENT_COLUMNS):
        x0 = 256 + 32 * i
        col = gradient(stops, np.broadcast_to(v, (256, 32)))
        rgb[0:256, x0:x0 + 32] = col
        alpha[0:256, x0:x0 + 32] = a
    # P: swatches
    for i, (name, colour, a) in enumerate(SWATCHES):
        x0, y0 = 256 + 32 * (i % 8), 256 + 32 * (i // 8)
        rgb[y0:y0 + 32, x0:x0 + 32] = colour
        alpha[y0:y0 + 32, x0:x0 + 32] = a
    # K: the crack strip (u across the crack)
    u = (np.arange(256) + 0.5) / 256
    core = smoothstep(0.0, 0.3, u) * smoothstep(1.0, 0.7, u)  # white across, a thin dark edge each side
    dark = np.array((26, 58, 108), dtype=float)
    strip = dark[None, :] + (np.array((250, 253, 255)) - dark)[None, :] * core[:, None]
    rgb[480:512, 256:512] = strip[None, :, :]
    alpha[480:512, 256:512] = 1.0
    image = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
    return Image.fromarray(image, "RGBA")


def glow():
    n = 256
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx - n / 2 + 0.5, yy - n / 2 + 0.5) / (n / 2)
    a = 0.95 * (1 - smoothstep(0.15, 1.0, r)) ** 1.5  # a broad soft body (the creature covers the middle), 0 at the rim
    image = np.dstack([np.full((n, n, 3), 255), np.clip(a * 255, 0, 255)]).astype(np.uint8)
    return Image.fromarray(image, "RGBA")


def shimmer():
    n = 256
    yy, xx = np.mgrid[0:n, 0:n]
    d = ((xx - yy) % n) - n / 2  # one diagonal band through the middle, wrapping cleanly when tiled
    a = 0.85 * np.exp(-(d / 9.0) ** 2) + 0.35 * np.exp(-((d - 22) / 4.0) ** 2)
    image = np.dstack([np.full((n, n, 3), 255), np.clip(a * 255, 0, 255)]).astype(np.uint8)
    return Image.fromarray(image, "RGBA")


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, image in (("IceBlueAtlas", atlas()), ("IceGlow", glow()), ("IceShimmer", shimmer())):
        path = os.path.join(OUT, name + ".png")
        image.save(path, optimize=True)
        print("wrote", os.path.relpath(path, ROOT), image.size)


if __name__ == "__main__":
    main()
