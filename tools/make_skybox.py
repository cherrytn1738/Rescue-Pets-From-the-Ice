"""Writes the winter skybox: assets/textures/sky/Sky{Bk,Dn,Ft,Lf,Rt,Up}.png (1024 square each) and a preview.

A bright winter day: deep blue overhead fading to a pale icy horizon, soft white clouds on a cloud layer (so they
crowd together and thin out toward the horizon), a cool haze below it. Every pixel is computed from its
direction in the world, so the six faces join without seams. Roblox draws the sun itself.

Roblox's face layout (checked in a play test with labelled faces): looking +X shows SkyboxLf, -X SkyboxRt,
+Z SkyboxBk, -Z SkyboxFt, each upright and not mirrored; on SkyboxUp the image's top points to +X and its left
to +Z. SkyboxDn is one flat colour (the ground hides it).

    python tools/make_skybox.py
Then upload the six PNGs as group 921449746 (tools/upload_models.py) and put their ids in
tools/studio/build_world.luau (SKY).
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "textures", "sky")
SIZE = 1024

ZENITH = np.array([78, 146, 224]) / 255
MIDDLE = np.array([128, 184, 240]) / 255
HORIZON = np.array([214, 232, 248]) / 255
BELOW = np.array([222, 232, 244]) / 255
CLOUD_LIT = np.array([252, 253, 255]) / 255
CLOUD_SHADE = np.array([196, 210, 230]) / 255

rng = np.random.default_rng(7)
PERM = rng.permutation(256)
PERM = np.concatenate([PERM, PERM])
GRAD = rng.random(256)


def value_noise(x, y):
    xi, yi = np.floor(x).astype(int), np.floor(y).astype(int)
    xf, yf = x - xi, y - yi
    xi &= 255
    yi &= 255

    def h(i, j):
        return GRAD[PERM[PERM[i] + j] & 255]

    u = xf * xf * (3 - 2 * xf)
    v = yf * yf * (3 - 2 * yf)
    a, b = h(xi, yi), h(xi + 1, yi)
    c, d = h(xi, yi + 1), h(xi + 1, yi + 1)
    return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v


def fbm(x, y, octaves=6):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total = total + amp * value_noise(x * freq + o * 17.3, y * freq - o * 9.1)
        norm += amp
        amp *= 0.5
        freq *= 2.03
    return total / norm


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def sky(d):
    """d: (..., 3) unit directions (Roblox axes, Y up) -> (..., 3) RGB in 0..1."""
    y = d[..., 1]
    e = np.clip(y, 0, 1)
    t1 = smoothstep(0.0, 0.35, e)[..., None]
    t2 = smoothstep(0.3, 1.0, e)[..., None]
    colour = HORIZON * (1 - t1) + MIDDLE * t1
    colour = colour * (1 - t2) + ZENITH * t2
    below = smoothstep(0.0, -0.08, y)[..., None]
    colour = colour * (1 - below) + BELOW * below

    # clouds on a layer overhead: plane coordinates, stretched a little along X for drifting banks
    lift = np.maximum(y, 0) + 0.06
    px, pz = d[..., 0] / lift * 1.6, d[..., 2] / lift * 1.6
    n = fbm(px * 0.9 + 3.1, pz * 1.3 - 7.7)
    cover = smoothstep(0.52, 0.72, n)
    shade = fbm(px * 0.9 + 3.1 + 0.18, pz * 1.3 - 7.7 + 0.12)  # the cloud a little toward the sun: darker undersides
    lit = 1 - smoothstep(0.5, 0.8, shade) * 0.8
    fade = smoothstep(0.015, 0.14, y) * (1 - 0.35 * smoothstep(0.6, 1.0, y))
    alpha = (cover * fade)[..., None] * 0.92
    cloud = CLOUD_SHADE + (CLOUD_LIT - CLOUD_SHADE) * lit[..., None]
    colour = colour * (1 - alpha) + cloud * alpha
    return np.clip(colour, 0, 1)


def face(forward, right, up):
    """Directions for a face seen from inside: image left->right along `right`, top->bottom against `up`."""
    s = (np.arange(SIZE) + 0.5) / SIZE * 2 - 1
    u, v = np.meshgrid(s, s)  # u: left to right, v: top to bottom
    d = np.array(forward)[None, None, :] + u[..., None] * np.array(right) - v[..., None] * np.array(up)
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


X, Y, Z = np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
FACES = {
    # side faces: looking along `forward` with +Y up; screen right = forward x up (Roblox's camera)
    "Lf": face(X, np.cross(X, Y), Y),
    "Rt": face(-X, np.cross(-X, Y), Y),
    "Bk": face(Z, np.cross(Z, Y), Y),
    "Ft": face(-Z, np.cross(-Z, Y), Y),
    # the top: the image's top edge points to +X and its left edge to +Z (so its right edge to -Z)
    "Up": face(Y, -Z, X),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    images = {}
    for name, dirs in FACES.items():
        rgb = (sky(dirs) * 255 + 0.5).astype(np.uint8)
        images[name] = Image.fromarray(rgb)
    images["Dn"] = Image.new("RGB", (SIZE, SIZE), tuple(int(c * 255 + 0.5) for c in BELOW))
    for name, image in images.items():
        image.save(os.path.join(OUT, "Sky%s.png" % name))
    # preview: a horizontal cross (Lf Ft Rt Bk round the horizon... in the order a turning camera sees them)
    small = {k: v.resize((256, 256)) for k, v in images.items()}
    sheet = Image.new("RGB", (256 * 4, 256 * 2), (40, 40, 40))
    for i, k in enumerate(["Ft", "Lf", "Bk", "Rt"]):
        sheet.paste(small[k], (256 * i, 256))
    sheet.paste(small["Up"].rotate(0), (256 * 1, 0))
    sheet.save(os.path.join(OUT, "preview.png"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
