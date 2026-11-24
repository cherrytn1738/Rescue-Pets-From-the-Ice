"""The shared particle textures (docs/GAME_DESIGN.md, "Effects and auras"): white on transparent, so the
emitters give them their colour (ParticleEmitter.Color). 256 x 256 PNGs in assets/textures/particles/.

    python tools/make_particle_textures.py

soft_glow, sparkle, snowflake, ember, smoke_puff, star, water_droplet, and rune_1..rune_4 (rune glyphs).
"""
import math
import os
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "textures", "particles")
SIZE = 256
C = SIZE / 2


def canvas():
    return Image.new("L", (SIZE, SIZE), 0)


def save(alpha, name):
    """White everywhere; the shape lives in the alpha channel."""
    image = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 0))
    image.putalpha(alpha)
    image.save(os.path.join(OUT, name + ".png"))
    print("wrote", name)


def radial(falloff=2.0, radius=1.0):
    a = canvas()
    px = a.load()
    for y in range(SIZE):
        for x in range(SIZE):
            d = math.hypot(x - C + 0.5, y - C + 0.5) / (C * radius)
            px[x, y] = int(255 * max(0.0, 1 - d) ** falloff)
    return a


def soft_glow():
    save(radial(2.2), "soft_glow")


def sparkle():
    a = canvas()
    d = ImageDraw.Draw(a)
    for angle, length, width in ((0, 0.95, 9), (90, 0.95, 9), (45, 0.55, 5), (135, 0.55, 5)):
        r = math.radians(angle)
        dx, dy = math.cos(r) * C * length, math.sin(r) * C * length
        d.polygon([(C - dx, C - dy), (C - dy / 10 * width / 9, C + dx / 10 * width / 9), (C + dx, C + dy), (C + dy / 10 * width / 9, C - dx / 10 * width / 9)], fill=255)
    a = a.filter(ImageFilter.GaussianBlur(2))
    save(ImageChops.lighter(a, radial(2.5, 0.4)), "sparkle")


def snowflake():
    a = canvas()
    d = ImageDraw.Draw(a)
    for k in range(6):
        r = math.radians(k * 60)
        ux, uy = math.cos(r), math.sin(r)
        end = (C + ux * C * 0.9, C + uy * C * 0.9)
        d.line([(C, C), end], fill=255, width=12)
        for t, branch in ((0.45, 0.28), (0.7, 0.2)):
            bx, by = C + ux * C * 0.9 * t, C + uy * C * 0.9 * t
            for side in (-1, 1):
                rr = r + side * math.radians(45)
                d.line([(bx, by), (bx + math.cos(rr) * C * branch, by + math.sin(rr) * C * branch)], fill=255, width=9)
    d.ellipse([C - 18, C - 18, C + 18, C + 18], fill=255)
    save(a.filter(ImageFilter.GaussianBlur(1.5)), "snowflake")


def ember():
    streak = canvas()
    ImageDraw.Draw(streak).ellipse([C - 22, C - 90, C + 22, C + 40], fill=200)
    save(ImageChops.lighter(radial(1.4, 0.55), streak.filter(ImageFilter.GaussianBlur(14))), "ember")


def smoke_puff():
    a = canvas()
    d = ImageDraw.Draw(a)
    for cx, cy, r in ((0.5, 0.55, 0.28), (0.35, 0.45, 0.22), (0.65, 0.42, 0.24), (0.5, 0.32, 0.22), (0.38, 0.62, 0.18), (0.63, 0.63, 0.19)):
        d.ellipse([SIZE * (cx - r), SIZE * (cy - r), SIZE * (cx + r), SIZE * (cy + r)], fill=170)
    a = a.filter(ImageFilter.GaussianBlur(16))
    save(a, "smoke_puff")


def star():
    a = canvas()
    points = []
    for k in range(10):
        r = math.radians(-90 + k * 36)
        rad = C * (0.9 if k % 2 == 0 else 0.38)
        points.append((C + math.cos(r) * rad, C + math.sin(r) * rad))
    ImageDraw.Draw(a).polygon(points, fill=255)
    save(a.filter(ImageFilter.GaussianBlur(2)), "star")


def water_droplet():
    a = canvas()
    d = ImageDraw.Draw(a)
    d.ellipse([C - 62, C - 20, C + 62, C + 104], fill=235)
    d.polygon([(C, C - 112), (C - 58, C + 30), (C + 58, C + 30)], fill=235)
    save(a.filter(ImageFilter.GaussianBlur(3)), "water_droplet")


RUNES = [  # simple invented glyphs, strokes in a unit square
    [((0.5, 0.1), (0.5, 0.9)), ((0.2, 0.3), (0.8, 0.3)), ((0.25, 0.75), (0.5, 0.55)), ((0.75, 0.75), (0.5, 0.55))],
    [((0.25, 0.1), (0.25, 0.9)), ((0.25, 0.1), (0.75, 0.35)), ((0.75, 0.35), (0.25, 0.55)), ((0.25, 0.55), (0.75, 0.9))],
    [((0.2, 0.2), (0.8, 0.8)), ((0.8, 0.2), (0.2, 0.8)), ((0.5, 0.05), (0.5, 0.35)), ((0.5, 0.65), (0.5, 0.95))],
    [((0.5, 0.1), (0.15, 0.5)), ((0.15, 0.5), (0.5, 0.9)), ((0.5, 0.9), (0.85, 0.5)), ((0.85, 0.5), (0.5, 0.1)), ((0.5, 0.35), (0.5, 0.65))],
]


def runes():
    for index, strokes in enumerate(RUNES, start=1):
        a = canvas()
        d = ImageDraw.Draw(a)
        for (x0, y0), (x1, y1) in strokes:
            d.line([(x0 * SIZE, y0 * SIZE), (x1 * SIZE, y1 * SIZE)], fill=255, width=18)
        glow = a.filter(ImageFilter.GaussianBlur(10)).point(lambda v: min(255, int(v * 1.6)))
        save(ImageChops.lighter(a, glow), "rune_%d" % index)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for make in (soft_glow, sparkle, snowflake, ember, smoke_puff, star, water_droplet, runes):
        make()
