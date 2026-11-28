"""Writes the sunset skybox: assets/textures/sky/Sky{Bk,Dn,Ft,Lf,Rt,Up}.png (1024 square each) and a preview.

A warm, cinematic winter sunset (src/replicated/LightingConfig.luau): deep orange at the horizon under the sun, through
pink and violet to a dusky blue overhead; the horizon away from the sun cools to rose and mauve. A big soft glow round
the sun, a few clouds on a cloud layer lit gold and pink on the sun's side and violet-grey away from it, and a warm
haze below the horizon. Every pixel is computed from its direction in the world, so the six faces join without seams.
Roblox draws the sun disc itself: SUN is where it stands (Lighting:GetSunDirection() at LightingConfig's ClockTime and
GeographicLatitude, measured in Studio), so the baked glow sits round it. Change SUN when those change.

Roblox's face layout (checked in a play test with labelled faces): looking +X shows SkyboxLf, -X SkyboxRt,
+Z SkyboxBk, -Z SkyboxFt, each upright and not mirrored; on SkyboxUp the image's top points to +X and its left
to +Z. SkyboxDn is one flat colour (the ground hides it).

    python tools/make_skybox.py
Then upload the six PNGs as group 921449746 (python tools/upload_models.py assets/textures/sky/Sky*.png: a changed
picture is a new asset) and put their ids in src/replicated/LightingConfig.luau (Sky.Faces).
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "textures", "sky")
SIZE = 1024

# Lighting:GetSunDirection() at LightingConfig's ClockTime and latitude (Roblox axes, Y up)
SUN_DIRECTION = (-0.941, 0.226, 0.250)  # ClockTime 17.1, latitude 38: 13 degrees up (Lighting:GetSunDirection())
SUN = np.array(SUN_DIRECTION)
SUN = SUN / np.linalg.norm(SUN)

ZENITH = np.array([44, 58, 112]) / 255        # dusky blue overhead
HIGH = np.array([92, 84, 150]) / 255          # violet
LOW = np.array([226, 128, 150]) / 255         # pink
HORIZON_SUN = np.array([255, 128, 52]) / 255  # deep orange under the sun
HORIZON_AWAY = np.array([206, 120, 146]) / 255  # rose-mauve away from it
BELOW = np.array([232, 168, 150]) / 255       # the warm haze under the horizon
GLOW_WIDE = np.array([255, 168, 84]) / 255
GLOW_CORE = np.array([255, 238, 196]) / 255
CLOUD_SUNLIT = np.array([255, 196, 128]) / 255
CLOUD_PINK = np.array([238, 138, 160]) / 255
CLOUD_AWAY = np.array([168, 128, 176]) / 255
CLOUD_UNDER = np.array([120, 92, 140]) / 255

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
    # how much a direction faces the sun round the horizon (azimuth only), and its angle to the sun itself
    flat = d * np.array([1, 0, 1])
    flat = flat / np.maximum(np.linalg.norm(flat, axis=-1, keepdims=True), 1e-6)
    sun_flat = SUN * np.array([1, 0, 1])
    sun_flat = sun_flat / np.linalg.norm(sun_flat)
    toward = np.clip((flat @ sun_flat + 1) / 2, 0, 1)[..., None] ** 1.6  # 1 under the sun, 0 opposite
    angle = np.arccos(np.clip(d @ SUN, -1, 1))[..., None]

    horizon = HORIZON_AWAY + (HORIZON_SUN - HORIZON_AWAY) * toward
    low = LOW * (0.85 + 0.15 * toward)
    t1 = smoothstep(0.0, 0.24, e)[..., None]
    t2 = smoothstep(0.16, 0.55, e)[..., None]
    t3 = smoothstep(0.35, 0.95, e)[..., None]
    colour = horizon * (1 - t1) + low * t1
    colour = colour * (1 - t2) + HIGH * t2
    colour = colour * (1 - t3) + ZENITH * t3
    # the sun's soft glow: a wide warm halo and a bright core round where Roblox draws the disc
    wide = np.exp(-angle / 0.5) * 0.7
    core = np.exp(-angle / 0.13) * 0.95
    colour = colour * (1 - wide) + GLOW_WIDE * wide
    colour = colour * (1 - core) + GLOW_CORE * core
    below = smoothstep(0.0, -0.08, y)[..., None]
    colour = colour * (1 - below) + BELOW * below

    # a few clouds on a layer overhead: plane coordinates, stretched along X into long sunset banks
    lift = np.maximum(y, 0) + 0.06
    px, pz = d[..., 0] / lift * 1.6, d[..., 2] / lift * 1.6
    n = fbm(px * 0.42 + 3.1, pz * 0.95 - 7.7)
    cover = smoothstep(0.62, 0.78, n)
    shade = fbm(px * 0.42 + 3.1 + 0.12, pz * 0.95 - 7.7 + 0.08)  # the cloud a little toward the sun: darker undersides
    under = smoothstep(0.5, 0.8, shade)[..., None]
    fade = smoothstep(0.07, 0.22, y) * (1 - 0.5 * smoothstep(0.5, 1.0, y))
    alpha = (cover * fade)[..., None] * 0.9
    lit = CLOUD_PINK + (CLOUD_SUNLIT - CLOUD_PINK) * np.exp(-angle / 0.8)  # gold near the sun, pink further off
    lit = CLOUD_AWAY + (lit - CLOUD_AWAY) * toward ** 0.6
    cloud = lit * (1 - under * 0.7) + CLOUD_UNDER * under * 0.7
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
