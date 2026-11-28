"""Writes the day-night cycle's skyboxes (src/replicated/LightingConfig.luau, one per look) and the aurora's texture.

    python tools/make_skybox.py              # all three looks and the aurora
    python tools/make_skybox.py dusk night   # some

  dusk   assets/textures/sky/Sky{Bk,Dn,Ft,Lf,Rt,Up}.png: the warm winter sunset (the PinkDusk look): deep orange at the
         horizon under the sun, through pink and violet to a dusky blue overhead; the horizon away from the sun cools to
         rose and mauve. A big soft glow round the sun, a few clouds lit gold and pink on the sun's side and violet-grey
         away from it, and a warm haze below the horizon.
  day    assets/textures/sky/day/Sky*.png: a clear winter afternoon (the Day look): pale blue at the horizon to a deep
         clear blue overhead, a soft white-gold glow round the sun, a few white clouds with grey-blue undersides.
  night  assets/textures/sky/night/Sky*.png: a moonlit night (the Night look): a deep blue sky, darker overhead, a faint
         blue glow along the horizon and round the moon, and stars, more and brighter higher up. (The moving northern
         lights are separate: Beams with the aurora texture, DayNight.client.)
  aurora assets/textures/sky/Aurora.png, 256 x 512: one curtain of northern lights for a Beam. A Beam lays a texture's
         y along its length and its x across its width (checked in a play test), so: down the image (y, tiling) the
         soft rays; across it (x) the curtain's height, its bright green bottom edge on the right (x = 255), through teal
         to a touch of violet on the left, fading out. Colours on transparency, so the Beam's Color can tint it.

Every sky pixel is computed from its direction in the world, so the six faces join without seams. Roblox draws the sun
and the moon discs itself: SUN/MOON are where they stand (Lighting:GetSunDirection() / GetMoonDirection() at the look's
ClockTime and GeographicLatitude, measured in Studio), so the baked glow sits round them. Change them when those change.

Roblox's face layout (checked in a play test with labelled faces): looking +X shows SkyboxLf, -X SkyboxRt,
+Z SkyboxBk, -Z SkyboxFt, each upright and not mirrored; on SkyboxUp the image's top points to +X and its left
to +Z. SkyboxDn is one flat colour (the ground hides it).

Then upload the changed PNGs as group 921449746 (python tools/upload_models.py --manifest
assets/textures/sky/upload_manifest.json <files>: a changed picture is a new asset) and put their ids in
src/replicated/LightingConfig.luau (each preset's Sky.Faces; the aurora's id in LightingConfig.Aurora).
"""
import os
import sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKY = os.path.join(ROOT, "assets", "textures", "sky")
SIZE = 1024


def unit(v):
    v = np.array(v, dtype=float)
    return v / np.linalg.norm(v)


# Lighting:GetSunDirection() / GetMoonDirection() at each look's ClockTime, latitude 38 (Roblox axes, Y up)
SUN_DUSK = unit((-0.941, 0.226, 0.250))  # ClockTime 17.1: 13 degrees up
SUN_DAY = unit((-0.685, 0.685, 0.250))  # ClockTime 15: 43 degrees up
MOON_NIGHT = unit((0.685, 0.685, 0.250))  # ClockTime 9: the night draws the moon as its sun, 43 degrees up


def rgb(r, g, b):
    return np.array([r, g, b]) / 255


LOOKS = {
    "dusk": dict(
        out=SKY, sun=SUN_DUSK,
        zenith=rgb(44, 58, 112), high=rgb(92, 84, 150), low=rgb(226, 128, 150),
        horizon_sun=rgb(255, 128, 52), horizon_away=rgb(206, 120, 146), below=rgb(232, 168, 150),
        glow_wide=rgb(255, 168, 84), glow_core=rgb(255, 238, 196), wide=(0.5, 0.7), core=(0.13, 0.95),
        clouds=dict(sunlit=rgb(255, 196, 128), pink=rgb(238, 138, 160), away=rgb(168, 128, 176), under=rgb(120, 92, 140),
                    cover=(0.62, 0.78), alpha=0.9, stretch=(0.42, 0.95)),
        stars=0),
    "day": dict(
        out=os.path.join(SKY, "day"), sun=SUN_DAY,
        zenith=rgb(52, 116, 204), high=rgb(92, 156, 228), low=rgb(156, 198, 240),
        horizon_sun=rgb(228, 236, 246), horizon_away=rgb(196, 220, 244), below=rgb(214, 228, 244),
        glow_wide=rgb(255, 246, 222), glow_core=rgb(255, 253, 244), wide=(0.45, 0.45), core=(0.1, 0.9),
        clouds=dict(sunlit=rgb(255, 255, 255), pink=rgb(246, 249, 255), away=rgb(226, 234, 246), under=rgb(168, 186, 212),
                    cover=(0.64, 0.8), alpha=0.85, stretch=(0.55, 0.8)),
        stars=0),
    "night": dict(
        out=os.path.join(SKY, "night"), sun=MOON_NIGHT,
        zenith=rgb(6, 12, 38), high=rgb(12, 24, 66), low=rgb(22, 44, 98),
        horizon_sun=rgb(40, 70, 128), horizon_away=rgb(30, 56, 112), below=rgb(26, 42, 82),
        glow_wide=rgb(70, 110, 176), glow_core=rgb(196, 214, 246), wide=(0.45, 0.35), core=(0.08, 0.6),
        clouds=None,
        stars=2600),
}

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


# The stars: fixed random directions on the upper half (seeded apart from the cloud noise), brighter higher up.
STAR_RNG = np.random.default_rng(42)
STAR_DIRS = STAR_RNG.normal(size=(4000, 3))
STAR_DIRS[:, 1] = np.abs(STAR_DIRS[:, 1])
STAR_DIRS /= np.linalg.norm(STAR_DIRS, axis=1, keepdims=True)
STAR_POWER = STAR_RNG.random(4000) ** 3  # mostly faint, a few bright
STAR_TINT = STAR_RNG.random(4000)


def stars(d, count):
    """Star light per direction: each star a tiny soft dot (angular radius ~0.0018 rad, ~1.2 px on a face)."""
    light = np.zeros(d.shape[:-1])
    tint = np.zeros(d.shape[:-1])
    flat = d.reshape(-1, 3)
    out = light.reshape(-1)
    tout = tint.reshape(-1)
    for start in range(0, count, 200):
        dirs = STAR_DIRS[start:start + 200]
        cos = flat @ dirs.T  # (pixels, stars)
        near = np.clip((cos - np.cos(0.004)) / (1 - np.cos(0.004)), 0, 1) ** 2
        weight = near * (0.35 + 0.65 * STAR_POWER[start:start + 200])
        out += weight.max(axis=1)
        tout += (weight * STAR_TINT[start:start + 200]).sum(axis=1)
    height = smoothstep(0.02, 0.4, d[..., 1])
    return np.clip(light * height, 0, 1), np.clip(tint, 0, 1)


def sky(d, look):
    """d: (..., 3) unit directions (Roblox axes, Y up) -> (..., 3) RGB in 0..1."""
    L = LOOKS[look]
    SUN = L["sun"]
    y = d[..., 1]
    e = np.clip(y, 0, 1)
    # how much a direction faces the sun round the horizon (azimuth only), and its angle to the sun itself
    flat = d * np.array([1, 0, 1])
    flat = flat / np.maximum(np.linalg.norm(flat, axis=-1, keepdims=True), 1e-6)
    sun_flat = SUN * np.array([1, 0, 1])
    sun_flat = sun_flat / np.linalg.norm(sun_flat)
    toward = np.clip((flat @ sun_flat + 1) / 2, 0, 1)[..., None] ** 1.6  # 1 under the sun, 0 opposite
    angle = np.arccos(np.clip(d @ SUN, -1, 1))[..., None]

    horizon = L["horizon_away"] + (L["horizon_sun"] - L["horizon_away"]) * toward
    low = L["low"] * (0.85 + 0.15 * toward)
    t1 = smoothstep(0.0, 0.24, e)[..., None]
    t2 = smoothstep(0.16, 0.55, e)[..., None]
    t3 = smoothstep(0.35, 0.95, e)[..., None]
    colour = horizon * (1 - t1) + low * t1
    colour = colour * (1 - t2) + L["high"] * t2
    colour = colour * (1 - t3) + L["zenith"] * t3
    # the sun's (or the moon's) soft glow: a wide halo and a bright core round where Roblox draws the disc
    wide = np.exp(-angle / L["wide"][0]) * L["wide"][1]
    core = np.exp(-angle / L["core"][0]) * L["core"][1]
    colour = colour * (1 - wide) + L["glow_wide"] * wide
    colour = colour * (1 - core) + L["glow_core"] * core
    below = smoothstep(0.0, -0.08, y)[..., None]
    colour = colour * (1 - below) + L["below"] * below

    c = L["clouds"]
    if c:
        # a few clouds on a layer overhead: plane coordinates, stretched along X into long banks
        lift = np.maximum(y, 0) + 0.06
        px, pz = d[..., 0] / lift * 1.6, d[..., 2] / lift * 1.6
        sx, sz = c["stretch"]
        n = fbm(px * sx + 3.1, pz * sz - 7.7)
        cover = smoothstep(c["cover"][0], c["cover"][1], n)
        shade = fbm(px * sx + 3.1 + 0.12, pz * sz - 7.7 + 0.08)  # the cloud a little toward the sun: darker undersides
        under = smoothstep(0.5, 0.8, shade)[..., None]
        fade = smoothstep(0.07, 0.22, y) * (1 - 0.5 * smoothstep(0.5, 1.0, y))
        alpha = (cover * fade)[..., None] * c["alpha"]
        lit = c["pink"] + (c["sunlit"] - c["pink"]) * np.exp(-angle / 0.8)  # brightest near the sun
        lit = c["away"] + (lit - c["away"]) * toward ** 0.6
        cloud = lit * (1 - under * 0.7) + c["under"] * under * 0.7
        colour = colour * (1 - alpha) + cloud * alpha
    if L["stars"]:
        light, tint = stars(d, L["stars"])
        star = rgb(214, 226, 255) * (1 - tint[..., None]) + rgb(255, 244, 222) * tint[..., None]
        light = light * (1 - np.clip(core[..., 0] * 3, 0, 1))  # none in the moon's glow
        colour = colour + (star - colour) * light[..., None]
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


def write_look(look):
    out = LOOKS[look]["out"]
    os.makedirs(out, exist_ok=True)
    images = {}
    for name, dirs in FACES.items():
        rgb_ = (sky(dirs, look) * 255 + 0.5).astype(np.uint8)
        images[name] = Image.fromarray(rgb_)
    images["Dn"] = Image.new("RGB", (SIZE, SIZE), tuple(int(c * 255 + 0.5) for c in LOOKS[look]["below"]))
    for name, image in images.items():
        image.save(os.path.join(out, "Sky%s.png" % name))
    # preview: the four sides in the order a turning camera sees them, the top above
    small = {k: v.resize((256, 256)) for k, v in images.items()}
    sheet = Image.new("RGB", (256 * 4, 256 * 2), (40, 40, 40))
    for i, k in enumerate(["Ft", "Lf", "Bk", "Rt"]):
        sheet.paste(small[k], (256 * i, 256))
    sheet.paste(small["Up"], (256 * 1, 0))
    sheet.save(os.path.join(out, "preview.png"))
    print("wrote", look, "->", os.path.relpath(out, ROOT))


def write_aurora():
    w, h = 512, 256
    x = (np.arange(w) + 0.5) / w
    yy = (np.arange(h) + 0.5) / h  # 0 = top of the image (the curtain's top), 1 = its bottom edge
    # vertical rays along the curtain: tileable sums of sines, sharpened
    rays = (0.5 + 0.25 * np.sin(2 * np.pi * 7 * x) + 0.15 * np.sin(2 * np.pi * 19 * x + 1.3) + 0.1 * np.sin(2 * np.pi * 41 * x + 2.1))
    rays = np.clip(rays, 0, 1) ** 1.6
    height = 1 - yy  # 1 at the top
    # bright at the bottom edge (a soft rim), fading up through the curtain
    body = smoothstep(1.0, 0.82, yy) * (0.25 + 0.75 * np.exp(-(1 - yy) / 0.35))
    alpha = np.clip(body[:, None] * (0.35 + 0.65 * rays[None, :]), 0, 1)
    green, teal, violet = rgb(120, 255, 170), rgb(110, 240, 235), rgb(200, 150, 255)
    t = height[:, None, None]
    colour = green * (1 - smoothstep(0.25, 0.6, t)) + teal * smoothstep(0.25, 0.6, t)
    colour = colour * (1 - smoothstep(0.62, 0.95, t)) + violet * smoothstep(0.62, 0.95, t)
    colour = np.broadcast_to(colour, (h, w, 3))
    image = np.dstack([(colour * 255 + 0.5).astype(np.uint8), (alpha * 255 + 0.5).astype(np.uint8)])
    path = os.path.join(SKY, "Aurora.png")
    # (drawn with the rays along x and the height along y, then turned: a Beam's length runs down the image)
    Image.fromarray(image, "RGBA").transpose(Image.Transpose.TRANSPOSE).save(path)
    print("wrote aurora ->", os.path.relpath(path, ROOT))


def main():
    wanted = sys.argv[1:] or ["dusk", "day", "night", "aurora"]
    for look in wanted:
        if look == "aurora":
            write_aurora()
        elif look in LOOKS:
            write_look(look)
        else:
            sys.exit("unknown look " + look)


if __name__ == "__main__":
    main()
