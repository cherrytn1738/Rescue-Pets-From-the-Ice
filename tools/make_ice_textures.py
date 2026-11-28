"""make_ice_textures.py - the ice block's textures (tools/blender/ice_block.py maps its meshes onto them).

    python tools/make_ice_textures.py

Writes assets/textures/ice/:
  Ice<LayerId>Atlas.png   512 x 512, one per glacier layer (LAYERS below: FreshSnow, BlueIce, AncientIce, CrystalIce,
                    PrimordialIce, FrozenCore); every block mesh uses the same UVs, so a layer is a texture swap.
                    Transparent where the ice is clear: Roblox honours a MeshPart texture's alpha only while the
                    part's Transparency is above 0, so the shell and the bubbles run at 0.02 (IceLooks) and the
                    alpha does the rest.
      S  x 0-255, y 0-511     a side face, box-projected (u across the face, v up it): the layer's colour from the
                              base up, frosty edges, a clearer middle, frost streaks and cartoon glints.
      G  x 256-511, y 0-255   eight gradient columns (32 px each, v = height): 0 frosty, 1 semi, 2/3/5 clear in
                              three hues, 4 frosty second hue, 6 deep, 7 white frost (the rounded edges use 0 and 7).
      P  x 256-511, y 256-479 flat swatches 32 x 32 (SWATCHES below, row by row; a layer can recolour any).
      K  x 256-511, y 480-511 the crack strip: across the crack (u) a dark edge, a bright core, a dark edge.
  IceGlow.png       256 x 256, a soft round glow (white): a broad body round the creature, 0 at the rim.
  IceShimmer.png    256 x 256, one soft diagonal band (white), scrolled across the faces as a slow shimmer.
  IceHalo.png       256 x 256, a soft ring (white): the rarity aura round the whole block, clear in the middle so
                    it never washes over the block or the creature.
  IceRay.png        128 x 256, a soft light ray (white): bright at the bottom, fading up and to the sides.
  IceFlame.png      128 x 128, a soft flame wisp (white), for the Legendary aura's flickering flames.
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "textures", "ice")

# Flat swatches in region P, row by row (8 per row). (name, (r, g, b), alpha 0-1). The Blender script reads this
# table from here (keep names stable: meshes are mapped to them). These are Blue Ice's; a layer overrides some.
SWATCHES = [
    # row 0: snow and frost
    ("SnowWhite", (246, 251, 255), 1.0), ("SnowShade", (214, 233, 250), 1.0), ("SnowBlue", (186, 218, 244), 1.0),
    ("FrostWhite", (232, 245, 255), 0.9), ("BubbleWhite", (240, 250, 255), 0.5), ("StreakWhite", (245, 251, 255), 0.3),
    ("CrystalPale", (205, 243, 255), 1.0), ("CrystalCyan", (130, 232, 255), 1.0),
    # row 1: ice blues (opaque: crystals and icicles)
    ("CrystalDeep", (72, 170, 236), 1.0), ("IceBlue", (160, 214, 246), 1.0), ("GlacierBlue", (92, 180, 232), 1.0),
    ("DeepIce", (48, 126, 194), 1.0), ("NavyIce", (30, 64, 112), 1.0), ("White", (255, 255, 255), 1.0),
    ("CrystalGlass", (170, 238, 255), 0.72), ("CrystalGlassDeep", (90, 190, 245), 0.8),
    # row 2: frosty rims and tops, the shatter pieces' broken faces
    ("RimFrost", (220, 240, 255), 0.95), ("TopFrost", (226, 243, 255), 0.88), ("BaseDeep", (40, 98, 176), 0.9),
    ("SideFrost", (180, 222, 250), 0.8), ("WindowClear", (170, 220, 250), 0.22), ("Clear", (190, 230, 255), 0.12),
    ("FrostBlue", (150, 205, 245), 0.7), ("Glint", (255, 255, 255), 0.85),
    # row 3: broken ice (shatter pieces and falling chunks)
    ("Fracture", (214, 238, 255), 0.92), ("FractureDeep", (120, 180, 235), 0.92),
]
ATLAS = 512

# Each layer (LayerConfig.Layers' Look): the side colours from the base up, how clear the middle is, how frosty the
# rim, the frost streaks and glints, the second hue, the white frost, the crack strip, and any swatches recoloured.
LAYERS = {
    # (cooler than the first cut: under the pink-dusk light the white block melted into the pink snow)
    "FreshSnow": dict(  # packed white snow, soft edges, a clear icy blue tint
        stops=[(0.0, (142, 186, 238)), (0.3, (190, 220, 252)), (0.7, (222, 238, 255)), (1.0, (244, 249, 255))],
        centre=0.6, rim=0.97, base=0.25, streaks=0.0, glints=0.5, snowy=True,
        second=[(0, (168, 202, 240)), (1, (232, 244, 255))], white=[(0, (208, 228, 252)), (1, (248, 251, 255))],
        crack=((92, 130, 186), (178, 206, 238)),
        swatches={"BaseDeep": ((196, 216, 240), 0.95), "TopFrost": ((246, 250, 255), 0.95), "RimFrost": ((248, 251, 255), 0.98),
                  "Fracture": ((240, 246, 255), 0.95), "FractureDeep": ((206, 224, 246), 0.95)}),
    # (bluer and more saturated than the first cut: under the pink-dusk light it leaned lavender)
    "BlueIce": dict(  # clear pale blue
        stops=[(0.0, (20, 84, 196)), (0.18, (34, 122, 228)), (0.45, (76, 168, 248)), (0.75, (140, 206, 255)), (1.0, (208, 238, 255))],
        centre=0.36, rim=0.92, base=0.22, streaks=0.28, glints=1.0,
        second=[(0, (40, 140, 200)), (0.5, (110, 215, 240)), (1, (205, 248, 255))], white=[(0, (190, 222, 248)), (0.6, (226, 243, 255)), (1, (246, 251, 255))],
        crack=((26, 58, 108), (250, 253, 255)), swatches={}),
    "AncientIce": dict(  # deep blue with trapped bubbles
        stops=[(0.0, (12, 34, 104)), (0.25, (24, 62, 156)), (0.6, (52, 104, 200)), (1.0, (120, 168, 236))],
        centre=0.42, rim=0.9, base=0.25, streaks=0.2, glints=0.9,
        second=[(0, (20, 70, 150)), (1, (110, 170, 240))], white=[(0, (110, 150, 220)), (1, (200, 222, 250))],
        crack=((10, 26, 70), (226, 238, 255)),
        swatches={"BaseDeep": ((16, 42, 120), 0.92), "TopFrost": ((176, 206, 246), 0.88), "RimFrost": ((170, 200, 244), 0.94),
                  "CrystalPale": ((150, 190, 245), 1.0), "CrystalCyan": ((90, 140, 230), 1.0), "IceBlue": ((110, 160, 236), 1.0),
                  "GlacierBlue": ((60, 110, 210), 1.0), "BubbleWhite": ((220, 236, 255), 0.6), "FractureDeep": ((50, 96, 190), 0.92)}),
    "CrystalIce": dict(  # faceted, sparkling: very clear cyan, so the creature shows
        stops=[(0.0, (30, 150, 206)), (0.35, (84, 206, 236)), (0.7, (164, 238, 252)), (1.0, (228, 252, 255))],
        centre=0.26, rim=0.86, base=0.15, streaks=0.18, glints=1.4,
        second=[(0, (60, 190, 230)), (1, (220, 255, 255))], white=[(0, (180, 238, 252)), (1, (244, 254, 255))],
        crack=((20, 90, 130), (250, 255, 255)),
        swatches={"CrystalPale": ((210, 252, 255), 1.0), "CrystalCyan": ((120, 240, 255), 1.0), "IceBlue": ((170, 236, 250), 1.0),
                  "GlacierBlue": ((70, 200, 240), 1.0), "BaseDeep": ((40, 150, 200), 0.85)}),
    "PrimordialIce": dict(  # dark teal with glowing veins
        stops=[(0.0, (4, 34, 40)), (0.3, (10, 66, 74)), (0.65, (28, 112, 114)), (1.0, (96, 176, 170))],
        centre=0.42, rim=0.9, base=0.25, streaks=0.16, glints=0.9,
        second=[(0, (10, 70, 76)), (1, (90, 190, 180))], white=[(0, (70, 140, 140)), (1, (170, 222, 214))],
        crack=((4, 30, 34), (120, 255, 226)),
        swatches={"BaseDeep": ((6, 40, 46), 0.94), "TopFrost": ((140, 200, 194), 0.9), "RimFrost": ((130, 196, 190), 0.94),
                  "CrystalPale": ((120, 214, 200), 1.0), "CrystalCyan": ((60, 190, 176), 1.0), "IceBlue": ((80, 170, 164), 1.0),
                  "GlacierBlue": ((30, 120, 120), 1.0), "BubbleWhite": ((160, 230, 220), 0.5), "Fracture": ((140, 214, 206), 0.92),
                  "FractureDeep": ((20, 96, 100), 0.92)}),
    "FrozenCore": dict(  # black ice lit from inside, orange veins; glossy rims so it reads as ice
        stops=[(0.0, (8, 8, 18)), (0.3, (18, 20, 38)), (0.7, (34, 38, 70)), (1.0, (86, 96, 136))],
        centre=0.4, rim=0.92, base=0.25, streaks=0.12, glints=1.2,
        second=[(0, (24, 26, 52)), (1, (96, 106, 150))], white=[(0, (70, 80, 120)), (1, (150, 162, 200))],
        crack=((10, 6, 6), (255, 150, 70)),
        swatches={"BaseDeep": ((10, 10, 22), 0.95), "TopFrost": ((120, 130, 170), 0.9), "RimFrost": ((120, 132, 176), 0.95),
                  "CrystalPale": ((70, 76, 116), 1.0), "CrystalCyan": ((44, 48, 84), 1.0), "IceBlue": ((60, 66, 104), 1.0),
                  "GlacierBlue": ((32, 36, 66), 1.0), "BubbleWhite": ((255, 190, 140), 0.45), "StreakWhite": ((255, 200, 160), 0.25),
                  "Fracture": ((90, 96, 140), 0.92), "FractureDeep": ((40, 30, 40), 0.92)}),
}


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


def side_region(look):
    """Region S: 256 x 512 (u across, v up). Returns RGB floats (0-255) and alpha (0-1)."""
    h, w = 512, 256
    v = 1 - (np.arange(h)[:, None] + 0.5) / h  # 1 at the top row
    u = (np.arange(w)[None, :] + 0.5) / w
    u, v = np.broadcast_to(u, (h, w)), np.broadcast_to(v, (h, w))
    rgb = gradient(look["stops"], v)
    # frosty edges, a clearer middle: distance to the edge in face units (the face is 0.8 as wide as tall)
    dx = np.minimum(u, 1 - u) * 0.8
    edge = np.minimum(dx / 0.11, np.minimum(v / 0.07, (1 - v) / 0.12))
    frame = 1 - smoothstep(0.0, 1.0, edge)  # 1 at the rim, 0 inside
    alpha = look["centre"] + (look["rim"] - look["centre"]) * frame
    alpha += look["base"] * (1 - smoothstep(0.0, 0.2, v))  # a denser base
    frost = blob_noise((h, w), 7, 3)
    alpha += 0.12 * frost * (0.4 + frame)
    yy, xx = np.mgrid[0:h, 0:w]
    if look.get("snowy"):  # packed snow: soft lumpy blotches instead of streaks
        lumps = blob_noise((h, w), 31, 6)
        rgb = rgb + (255 - rgb) * (0.35 * lumps)[..., None]
        alpha += 0.1 * lumps
    rng = np.random.default_rng(21)
    streak = np.zeros((h, w))
    for _ in range(7):
        cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        angle = rng.uniform(-0.9, -0.4) if rng.random() < 0.6 else rng.uniform(0.4, 0.9)
        length, width = rng.uniform(60, 140), rng.uniform(2.0, 4.5)
        ca, sa = np.cos(angle), np.sin(angle)
        along = (xx - cx) * ca + (yy - cy) * sa
        across = -(xx - cx) * sa + (yy - cy) * ca
        s = np.exp(-(across / width) ** 2) * np.clip(1 - (along / length) ** 2, 0, 1)
        mid = np.exp(-(((xx - w / 2) / (w * 0.22)) ** 2 + ((yy - h * 0.52) / (h * 0.24)) ** 2))  # (not over the creature)
        streak = np.maximum(streak, s * (1 - 0.8 * mid))
    alpha += look["streaks"] * streak
    rgb = rgb + (255 - rgb) * (0.55 * streak * (look["streaks"] > 0))[..., None] + (255 - rgb) * (0.35 * frame)[..., None]
    # cartoon glints at the top left (and a small one at the bottom right)
    glint = np.zeros((h, w))
    for (cx, cy, length, width, angle) in [(62, 92, 70, 7.0, -0.78), (92, 70, 40, 3.8, -0.78), (205, 430, 26, 3.2, -0.78)]:
        ca, sa = np.cos(angle), np.sin(angle)
        along = (xx - cx) * ca + (yy - cy) * sa
        across = -(xx - cx) * sa + (yy - cy) * ca
        glint = np.maximum(glint, smoothstep(1.0, 0.6, np.abs(across) / width) * smoothstep(1.0, 0.7, np.abs(along) / length))
    glint = np.clip(glint * look["glints"], 0, 1)
    alpha = np.maximum(alpha, 0.85 * glint)
    rgb = rgb + (255 - rgb) * glint[..., None]
    return rgb, np.clip(alpha, 0, 1)


def atlas(look):
    rgb = np.zeros((ATLAS, ATLAS, 3))
    alpha = np.zeros((ATLAS, ATLAS))
    s_rgb, s_alpha = side_region(look)
    rgb[:, 0:256], alpha[:, 0:256] = s_rgb, s_alpha
    # G: gradient columns, v = height (row 0 = the top)
    stops, second, white = look["stops"], look["second"], look["white"]
    deep = [(0, tuple(c * 0.75 for c in stops[0][1])), (1, stops[len(stops) // 2][1])]
    columns = [(stops, 0.9), (stops, 0.66), (stops, 0.42), (second, 0.42), (second, 0.88), (stops, 0.42), (deep, 0.88), (white, 0.94)]
    v = 1 - (np.arange(256)[:, None] + 0.5) / 256
    for i, (col_stops, a) in enumerate(columns):
        x0 = 256 + 32 * i
        rgb[0:256, x0:x0 + 32] = gradient(col_stops, np.broadcast_to(v, (256, 32)))
        alpha[0:256, x0:x0 + 32] = a
    # P: swatches
    for i, (name, colour, a) in enumerate(SWATCHES):
        colour, a = look["swatches"].get(name, (colour, a))
        x0, y0 = 256 + 32 * (i % 8), 256 + 32 * (i // 8)
        rgb[y0:y0 + 32, x0:x0 + 32] = colour
        alpha[y0:y0 + 32, x0:x0 + 32] = a
    # K: the crack strip (u across the crack)
    u = (np.arange(256) + 0.5) / 256
    core = smoothstep(0.0, 0.3, u) * smoothstep(1.0, 0.7, u)
    dark, bright = (np.array(c, dtype=float) for c in look["crack"])
    rgb[480:512, 256:512] = (dark[None, :] + (bright - dark)[None, :] * core[:, None])[None, :, :]
    alpha[480:512, 256:512] = 1.0
    image = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
    return Image.fromarray(image, "RGBA")


def white_alpha(a):
    n = a.shape
    return Image.fromarray(np.dstack([np.full(n + (3,), 255), np.clip(a * 255, 0, 255)]).astype(np.uint8), "RGBA")


def radius(n, m=None):
    m = m or n
    yy, xx = np.mgrid[0:m, 0:n]
    return np.hypot((xx - n / 2 + 0.5) / (n / 2), (yy - m / 2 + 0.5) / (m / 2))


def glow():
    r = radius(256)
    return white_alpha(0.95 * (1 - smoothstep(0.15, 1.0, r)) ** 1.5)  # a broad soft body (the creature covers the middle), 0 at the rim


def halo():
    r = radius(256)
    ring = smoothstep(0.42, 0.7, r) * (1 - smoothstep(0.7, 1.0, r)) ** 1.2  # clear inside, a soft bright ring, 0 at the rim
    return white_alpha(0.95 * ring / ring.max())


def ray():
    n, m = 128, 256
    yy, xx = np.mgrid[0:m, 0:n]
    across = np.abs((xx - n / 2 + 0.5) / (n / 2))
    up = 1 - (yy + 0.5) / m  # 0 at the bottom row, 1 at the top
    a = (1 - smoothstep(0.0, 1.0, across)) ** 1.6 * (1 - smoothstep(0.0, 1.0, up)) * smoothstep(0.0, 0.06, up)
    return white_alpha(0.9 * a)


def flame():
    n = 128
    yy, xx = np.mgrid[0:n, 0:n]
    x = (xx - n / 2 + 0.5) / (n / 2)
    y = (yy + 0.5) / n  # 0 at the top (the tip), 1 at the base
    base = np.sqrt(np.clip(1 - ((y - 0.62) / 0.36) ** 2, 0, 1))
    width = 0.02 + 0.62 * np.clip(y, 0, 1) ** 1.5 * np.where(y > 0.62, base, 1.0)  # a teardrop: sharp tip, round base
    a = (1 - smoothstep(0.55, 1.0, np.abs(x) / np.maximum(width, 1e-3))) * smoothstep(0.0, 0.1, y) * (1 - smoothstep(0.95, 1.0, y))
    return white_alpha(0.95 * a)


def shimmer():
    n = 256
    yy, xx = np.mgrid[0:n, 0:n]
    d = ((xx - yy) % n) - n / 2  # one diagonal band through the middle, wrapping cleanly when tiled
    return white_alpha(0.85 * np.exp(-(d / 9.0) ** 2) + 0.35 * np.exp(-((d - 22) / 4.0) ** 2))


def main():
    os.makedirs(OUT, exist_ok=True)
    images = [("Ice%sAtlas" % layer, atlas(look)) for layer, look in LAYERS.items()]
    images += [("IceGlow", glow()), ("IceShimmer", shimmer()), ("IceHalo", halo()), ("IceRay", ray()), ("IceFlame", flame())]
    for name, image in images:
        path = os.path.join(OUT, name + ".png")
        image.save(path, optimize=True)
        print("wrote", os.path.relpath(path, ROOT), image.size)


if __name__ == "__main__":
    main()
