"""compose_icons.py - the 2D half of the store and game icons (Python 3, Pillow, numpy).

Takes the transparent 3D layers rendered by tools/icons/render_icons.py (headless Blender) and makes the
finished 512x512 PNGs: a saturated radial background themed per item, a soft glow, a thick dark outline
round the subject (from its alpha), a drop shadow, sparkles, small 2D extras (crown, motion arcs, swirl,
snowflakes) and a chunky outlined text badge. Composited at 1024 and downscaled to 512.

    python tools/icons/compose_icons.py --render              # render every icon in Blender, then compose
    python tools/icons/compose_icons.py --render VIP AutoPick # just these
    python tools/icons/compose_icons.py                       # compose again from the last renders
    options: --work <dir> (render layers; default: <system temp>/rpfi_icons_work), --jobs N (Blender
             processes at once, default 3), --sheet-only (just rebuild the contact sheet)

    python tools/icons/compose_icons.py --ui --render         # the UI icons instead (store-assets/ui-icons/)
    python tools/icons/compose_icons.py --ui --render Pets Home

Writes store-assets/icons/<Name>.png (the 12 Robux items), store-assets/launch/icon_concept_<n>.png (the
three game icon concepts, no text) and store-assets/icons/contact_sheet.png; with --ui, the in-game button and
window icons (256x256, transparent, no text but the pick tiers' numeral badge) to store-assets/ui-icons/<Key>.png and their contact_sheet.png
(each icon on its card colour at 96 and 48 px). Nothing is uploaded.
Blender: the newest C:\\Program Files\\Blender Foundation\\*\\blender.exe, or set BLENDER_EXE.
Fonts: Arial Black (C:\\Windows\\Fonts\\ariblk.ttf) for badges, Segoe UI Bold for the sheet labels.
Game pass icons show as circles on the Roblox site: keep badges inside the circle (they are).
"""
import os, sys, json, math, random, glob, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT_ICONS = os.path.join(REPO, 'store-assets', 'icons')
OUT_LAUNCH = os.path.join(REPO, 'store-assets', 'launch')
FONT = r'C:\Windows\Fonts\ariblk.ttf'
LABEL_FONT = r'C:\Windows\Fonts\segoeuib.ttf'
S = 1024                    # compose size (the output is S / 2)
INK = (22, 24, 52)          # outline colour: a very dark navy

# ------------------------------------------------------------------ the icons
# bg: (inner, outer) colours; box: where the subject goes (x0, y0, x1, y1 on the 1024 canvas);
# glow: halo colour behind the subject ('rainbow' = hue round the subject), or None;
# badges: (text, centre x, centre y, cap height, top colour, bottom colour, angle);
# extras: 2D extras by name (drawn in compose()).
CYAN_TXT = ((255, 255, 255), (130, 235, 255))
GOLD_TXT = ((255, 250, 190), (255, 190, 40))
WHITE_TXT = ((255, 255, 255), (215, 235, 255))
SPECS = {
    'DoubleCrystals': dict(title='2x Crystals', kind='pass', bg=((70, 170, 255), (25, 30, 150)), rays=(200, 250, 255),
                           box=(150, 90, 880, 800), glow=(140, 245, 255),
                           badges=[('2X', 700, 790, 190, CYAN_TXT, -8)], sparkles=7, glints=3),
    'AutoPick': dict(title='Auto Pick', kind='pass', bg=((110, 245, 190), (8, 120, 120)), rays=(220, 255, 240),
                     box=(110, 80, 920, 790), glow=(200, 255, 245), extras=['arcs'],
                     badges=[('AUTO', 512, 830, 150, WHITE_TXT, -5)], sparkles=5),
    'VIP': dict(title='VIP', kind='pass', bg=((200, 110, 255), (60, 14, 120)), rays=(255, 215, 110),
                box=(210, 230, 810, 860), glow=(255, 205, 70), extras=['crown'],
                badges=[('VIP', 512, 815, 170, GOLD_TXT, 0)], sparkles=7, sparkle_colour=(255, 236, 150)),
    'ExtraPetSlot': dict(title='Extra Pet Slot', kind='pass', bg=((140, 220, 255), (30, 110, 220)), rays=(235, 250, 255),
                         box=(170, 110, 790, 860), glow=(230, 248, 255), extras=['platform'],
                         badges=[('+1', 760, 700, 220, ((255, 255, 255), (170, 255, 170)), -8)], sparkles=5),
    'PetSquad': dict(title='Pet Squad', kind='pass', bg=((255, 190, 120), (230, 60, 130)), rays=(255, 240, 200),
                     box=(80, 120, 944, 800), glow=(255, 240, 220),
                     badges=[('+2', 512, 835, 190, ((255, 255, 255), (255, 230, 120)), -6)], sparkles=5),
    'LuckyIce': dict(title='Lucky Ice', kind='pass', bg=((180, 245, 110), (20, 120, 50)), rays=(255, 240, 150),
                     box=(200, 80, 830, 760), glow=(255, 214, 60), glow_radius=70,
                     badges=[('LUCK', 512, 790, 120, GOLD_TXT, -6), ('x2', 790, 640, 150, GOLD_TXT, -10)],
                     sparkles=9, sparkle_colour=(255, 240, 160)),
    'CrystalPouch': dict(title='Crystal Pouch', kind='product', bg=((120, 240, 220), (10, 120, 140)), rays=(220, 255, 250),
                         box=(140, 70, 884, 760), fixed=(1.3, 0, -90), glints=2, glow=(140, 245, 255),
                         badges=[('10 MIN', 512, 830, 125, WHITE_TXT, -4)], sparkles=3),
    'CrystalSack': dict(title='Crystal Sack', kind='product', bg=((110, 200, 255), (20, 60, 190)), rays=(220, 240, 255),
                        box=(140, 70, 884, 760), fixed=(1.15, 0, -70), glints=3, glow=(140, 245, 255),
                        badges=[('1 HOUR', 512, 830, 125, WHITE_TXT, -4)], sparkles=5),
    'CrystalChest': dict(title='Crystal Chest', kind='product', bg=((255, 215, 110), (215, 90, 20)), rays=(255, 245, 200),
                         box=(140, 70, 884, 760), fixed=(1.0, 0, -40), glints=4, glow=(160, 250, 255),
                         badges=[('6 HOURS', 512, 830, 125, WHITE_TXT, -4)], sparkles=8),
    'ShatterNow': dict(title='Shatter Now', kind='product', bg=((255, 180, 70), (205, 30, 30)), rays=(255, 240, 160),
                       box=(70, 60, 954, 780), glow=(255, 250, 210),
                       badges=[('SHATTER!', 512, 845, 125, ((255, 255, 255), (255, 225, 90)), -5)], sparkles=4),
    'ServerFrostRush': dict(title='Server Frost Rush', kind='product', bg=((80, 220, 255), (10, 40, 200)), rays=(200, 240, 255),
                            box=(90, 260, 934, 770), glow=(200, 245, 255), extras=['swirl', 'snowflakes'],
                            badges=[('x2', 512, 170, 170, CYAN_TXT, -6), ('SERVER', 512, 860, 105, WHITE_TXT, -4)],
                            sparkles=4),
    'MythicBlock': dict(title='Mythic Block', kind='product', bg=((150, 70, 230), (35, 8, 80)), rays=(255, 200, 255),
                        box=(200, 70, 830, 780), glow='rainbow', glow_radius=80,
                        badges=[('?', 790, 690, 230, ((255, 255, 255), (255, 170, 255)), 10)], sparkles=8),
    'icon_concept_1': dict(title='Game icon concept 1', kind='launch', bg=((255, 225, 110), (240, 90, 60)), rays=(255, 250, 210),
                           box=(40, 40, 984, 1024), anchor='bottom', glow=(255, 255, 230), sparkles=7),
    'icon_concept_2': dict(title='Game icon concept 2', kind='launch', bg=((255, 150, 230), (70, 30, 170)), rays=(255, 230, 255),
                           box=(30, 60, 994, 1024), anchor='bottom', glow='rainbow', glow_radius=70, sparkles=8,
                           no_outline=['back']),
    'icon_concept_3': dict(title='Game icon concept 3', kind='launch', bg=((120, 225, 255), (15, 80, 200)), rays=(255, 245, 200),
                           box=(50, 50, 974, 974), glow=(255, 225, 120), glow_layer='block', sparkles=7),
}
ORDER = list(SPECS)


# ------------------------------------------------------------------ helpers

def radial_bg(inner, outer, rays=None, centre=(0.5, 0.42)):
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
    d = np.sqrt((xx - centre[0]) ** 2 + (yy - centre[1]) ** 2) / 0.78
    t = np.clip(d, 0, 1) ** 1.15
    a, b = np.array(inner, np.float32), np.array(outer, np.float32)
    img = a[None, None, :] * (1 - t[..., None]) + b[None, None, :] * t[..., None]
    if rays:     # a soft sunburst
        ang = np.arctan2(yy - centre[1], xx - centre[0])
        wedge = (np.sin(ang * 9) > 0.15).astype(np.float32)
        wedge = np.array(Image.fromarray((wedge * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
        fade = np.clip(1 - d * 1.05, 0, 1) ** 0.8 * 0.22
        k = (wedge * fade)[..., None]
        img = img * (1 - k) + np.array(rays, np.float32)[None, None, :] * k
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')


def alpha_of(img):
    return img.getchannel('A')


def solid(mask, thr=24):
    return mask.point(lambda v: 255 if v > thr else 0)


def dilate(mask, r):
    """round dilation by about r px (a blur, then a steep threshold, keeps it anti-aliased)"""
    sigma = max(r / 1.15, 0.5)
    b = mask.filter(ImageFilter.GaussianBlur(sigma))
    return b.point(lambda v: min(255, v * 8))


def outline_ring(mask, r):
    """the outline only (not under the subject, so see-through ice shows the background, not ink)"""
    inner = solid(mask).filter(ImageFilter.MinFilter(3))
    return ImageChops.subtract(dilate(solid(mask), r), inner)


def colour_layer(mask, colour, opacity=1.0):
    layer = Image.new('RGBA', mask.size, tuple(colour) + (255,))
    layer.putalpha(mask.point(lambda v: int(v * opacity)))
    return layer


def rainbow_layer(mask, centre):
    w, h = mask.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    hue = (np.arctan2(yy - centre[1], xx - centre[0]) / (2 * np.pi) + 0.5) * 6
    k = lambda n: np.clip(np.abs(((hue + n) % 6) - 3) - 1, 0, 1)
    rgb = np.stack([k(0), k(4), k(2)], -1)          # hue -> rgb
    rgb = 0.25 + 0.75 * rgb
    layer = Image.fromarray((rgb * 255).astype(np.uint8), 'RGB').convert('RGBA')
    layer.putalpha(mask)
    return layer


def star_points(cx, cy, r, w=0.2, rot=0.0):
    pts = []
    for i in range(8):
        a = rot + i * math.pi / 4
        rr = r if i % 2 == 0 else r * w * 1.4
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts


def sparkle(canvas, cx, cy, r, colour=(255, 255, 255)):
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon(star_points(cx, cy, r, 0.18), fill=colour + (255,))
    glow = layer.filter(ImageFilter.GaussianBlur(r * 0.25))
    canvas.alpha_composite(glow)
    canvas.alpha_composite(layer)
    d2 = ImageDraw.Draw(canvas)
    d2.ellipse((cx - r * 0.16, cy - r * 0.16, cx + r * 0.16, cy + r * 0.16), fill=(255, 255, 255, 255))


def gradient(size, top, bottom, y0=0, y1=None):
    w, h = size
    y1 = h if y1 is None else y1
    t = np.clip((np.arange(h, dtype=np.float32) - y0) / max(1, y1 - y0), 0, 1)[:, None, None]
    a, b = np.array(top, np.float32), np.array(bottom, np.float32)
    g = a * (1 - t) + b * t
    g = np.repeat(g, w, axis=1)
    return Image.fromarray(g.astype(np.uint8), 'RGB').convert('RGBA')


def text_badge(canvas, text, cx, cy, cap, colours, angle=0, stroke=None, ink=INK):
    """chunky text: vertical gradient fill, a heavy dark outline and a dark extrusion under it"""
    size = int(cap * 1.38)
    font = ImageFont.truetype(FONT, size)
    l, t, r, b = font.getbbox(text)
    stroke = stroke or max(8, int(cap * 0.13))
    ext = max(5, int(cap * 0.09))
    pad = stroke + ext + 10
    W, H = r - l + pad * 2, b - t + pad * 2
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = pad - l, pad - t
    for k in range(ext, 0, -1):
        d.text((x, y + k), text, font=font, fill=ink, stroke_width=stroke, stroke_fill=ink)
    d.text((x, y), text, font=font, fill=ink, stroke_width=stroke, stroke_fill=ink)
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).text((x, y), text, font=font, fill=255)
    g = gradient((W, H), colours[0], colours[1], pad, H - pad)
    layer.paste(g, (0, 0), m)
    # a glossy band on the upper half of the letters
    gloss = Image.new('L', (W, H), 0)
    ImageDraw.Draw(gloss).rectangle((0, 0, W, pad + (b - t) * 0.42), fill=70)
    gl = Image.new('RGBA', (W, H), (255, 255, 255, 0))
    gl.putalpha(ImageChops.multiply(gloss, m))
    layer.alpha_composite(gl)
    if angle:
        layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))
    return layer


def ink_shape(canvas, mask, fill_img, ring=12, ink=INK):
    """paste a 2D shape (mask) filled with fill_img, with a dark outline ring"""
    canvas.alpha_composite(colour_layer(dilate(mask, ring), ink))
    f = fill_img.copy()
    f.putalpha(ImageChops.multiply(mask, alpha_of(fill_img)))
    canvas.alpha_composite(f)


# ------------------------------------------------------------------ 2D extras

def draw_crown(canvas, cx, base_y, width, angle=-8):
    w, h = int(width), int(width * 0.78)
    pad = 30
    m = Image.new('L', (w + pad * 2, h + pad * 2), 0)
    d = ImageDraw.Draw(m)
    x0, x1 = pad, pad + w
    yb, yt = pad + h, pad + h * 0.25
    band = h * 0.3
    pts = [(x0, yb), (x0 - w * 0.02, yt + h * 0.12), (x0 + w * 0.27, yt + h * 0.4), (x0 + w * 0.5, yt),
           (x0 + w * 0.73, yt + h * 0.4), (x1 + w * 0.02, yt + h * 0.12), (x1, yb)]
    d.polygon(pts, fill=255)
    for (px, py) in (pts[1], pts[3], pts[5]):
        rr = w * 0.085
        d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=255)
    fill = gradient(m.size, (255, 246, 170), (235, 145, 10), int(yt - w * 0.1), int(yb))
    fd = ImageDraw.Draw(fill)
    fd.rectangle((x0, yb - band, x1, yb), fill=(245, 175, 30, 255))
    fd.line((x0, yb - band, x1, yb - band), fill=(170, 90, 10, 255), width=6)
    for gx, col in ((0.5, (230, 40, 80)), (0.2, (60, 160, 255)), (0.8, (60, 160, 255))):
        rr = w * (0.075 if gx == 0.5 else 0.055)
        px, py = x0 + w * gx, yb - band / 2
        fd.ellipse((px - rr, py - rr, px + rr, py + rr), fill=col + (255,))
        fd.ellipse((px - rr * 0.45, py - rr * 0.6, px, py - rr * 0.15), fill=(255, 255, 255, 200))
    layer = Image.new('RGBA', m.size, (0, 0, 0, 0))
    ink_shape(layer, m, fill, ring=11)
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(base_y - layer.height * 0.78)))


def draw_arcs(canvas, pivot, head, colour=(255, 255, 255)):
    """swing trails behind the pick head, centred on the hand"""
    px, py = pivot
    hx, hy = head
    r = math.hypot(hx - px, hy - py)
    a0 = math.atan2(hy - py, hx - px)
    side = 1 if (py + math.sin(a0 + 0.5) * r) < (py + math.sin(a0 - 0.5) * r) else -1   # trail on the upper side
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for rf, wmax, amax, sweep in ((1.0, 54, 255, 0.8), (0.8, 40, 240, 0.7), (1.17, 30, 215, 0.6)):
        steps = 40
        prev = None
        for i in range(steps + 1):
            t = i / steps
            a = a0 + side * (0.22 + sweep * t)
            p = (px + math.cos(a) * r * rf, py + math.sin(a) * r * rf)
            if prev:
                w = max(2, int(wmax * (1 - t) ** 0.45))
                d.line((prev, p), fill=colour + (int(amax * (1 - t)),), width=w)
                d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=colour + (int(amax * (1 - t)),))
            prev = p
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.0)))


def draw_swirl(canvas, centre, colour=(255, 255, 255)):
    cx, cy = centre
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for k, (r0, r1, a_start, wmax, amax) in enumerate(((120, 480, 0.4, 54, 230), (90, 430, 0.4 + math.pi, 46, 210),
                                                      (60, 340, 1.9, 30, 170))):
        prev = None
        steps = 90
        for i in range(steps + 1):
            t = i / steps
            a = a_start + t * 4.2
            r = r0 + (r1 - r0) * t
            p = (cx + math.cos(a) * r, cy + math.sin(a) * r * 0.62)
            if prev:
                w = max(3, int(wmax * math.sin(math.pi * t) ** 0.7))
                al = int(amax * math.sin(math.pi * t) ** 0.6)
                d.line((prev, p), fill=colour + (al,), width=w)
                d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=colour + (al,))
            prev = p
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(2.5)))


def draw_snowflake(canvas, cx, cy, r, rot=0.0, colour=(255, 255, 255)):
    pad = 20
    size = int(r * 2 + pad * 2)
    m = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(m)
    c = size / 2
    w = max(4, int(r * 0.16))
    for i in range(6):
        a = rot + i * math.pi / 3
        ex, ey = c + math.cos(a) * r, c + math.sin(a) * r
        d.line((c, c, ex, ey), fill=255, width=w)
        d.ellipse((ex - w / 2, ey - w / 2, ex + w / 2, ey + w / 2), fill=255)
        for f in (0.55,):
            bx, by = c + math.cos(a) * r * f, c + math.sin(a) * r * f
            for s in (-1, 1):
                b = a + s * 0.8
                d.line((bx, by, bx + math.cos(b) * r * 0.32, by + math.sin(b) * r * 0.32), fill=255, width=int(w * 0.85))
    d.ellipse((c - w, c - w, c + w, c + w), fill=255)
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ink_shape(layer, m, Image.new('RGBA', (size, size), colour + (255,)), ring=max(5, int(r * 0.09)))
    canvas.alpha_composite(layer, (int(cx - c), int(cy - c)))


def draw_platform(canvas, cx, cy, w):
    """a glowing slot ring on the ground under the pet"""
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    h = w * 0.28
    d.ellipse((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), fill=(255, 255, 255, 110))
    d.ellipse((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), outline=(255, 255, 255, 235), width=14)
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(2)))


# ------------------------------------------------------------------ compose one icon

def load(work, name):
    meta = json.load(open(os.path.join(work, name, 'meta.json')))
    layers = [(n, Image.open(os.path.join(work, name, n + '.png')).convert('RGBA')) for n in meta['layers']]
    return meta, layers


def place(layers, box, anchor='centre', fixed=None):
    """scale + move every layer the same way so the subject fills `box`; fixed = (scale, dx, dy) keeps the
    render's own framing instead (the crystal piles share one camera, so their sizes compare)"""
    union = Image.new('L', (S, S), 0)
    for _, im in layers:
        union = ImageChops.lighter(union, solid(alpha_of(im), 10))
    l, t, r, b = union.getbbox()
    bw, bh = r - l, b - t
    x0, y0, x1, y1 = box
    if fixed:
        k, dx, dy = fixed
        ox, oy = S / 2 + (l - S / 2) * k + dx, S / 2 + (t - S / 2) * k + dy
    else:
        k = min((x1 - x0) / bw, (y1 - y0) / bh)
        nw, nh = bw * k, bh * k
        ox = x0 + ((x1 - x0) - nw) / 2
        oy = y1 - nh if anchor == 'bottom' else y0 + ((y1 - y0) - nh) / 2
    out = []
    for n, im in layers:
        big = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
        c = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        c.paste(big, (int(round(ox - l * k)), int(round(oy - t * k))))     # onto an empty canvas: a plain copy keeps the alpha
        out.append((n, c))
    xf = lambda p: (ox + (p[0] - l) * k, oy + (p[1] - t) * k)
    return out, xf, k


def free_spots(mask, count, seed, avoid=(), radius=0.46):
    """sparkle positions inside the central circle, away from the subject and the badges"""
    rng = random.Random(seed)
    big = dilate(solid(mask), 40)
    px = big.load()
    spots = []
    tries = 0
    while len(spots) < count and tries < 4000:
        tries += 1
        x, y = rng.uniform(60, S - 60), rng.uniform(60, S - 60)
        if math.hypot(x - S / 2, y - S / 2) > S * radius:
            continue
        if px[int(x), int(y)] > 0:
            continue
        if any(abs(x - ax) < aw and abs(y - ay) < ah for ax, ay, aw, ah in avoid):
            continue
        if any(math.hypot(x - sx, y - sy) < 120 for sx, sy, _ in spots):
            continue
        spots.append((x, y, rng.uniform(22, 46)))
    return spots


def glint_spots(mask, count, seed):
    """sparkles on the subject itself (crystals catching the light)"""
    rng = random.Random(seed)
    inside = solid(mask).filter(ImageFilter.MinFilter(31)).load()
    box = solid(mask).getbbox()
    spots, tries = [], 0
    while len(spots) < count and tries < 4000:
        tries += 1
        x, y = rng.uniform(box[0], box[2]), rng.uniform(box[1], box[1] + (box[3] - box[1]) * 0.75)
        if inside[int(x), int(y)] and all(math.hypot(x - sx, y - sy) > 110 for sx, sy, _ in spots):
            spots.append((x, y, rng.uniform(20, 32)))
    return spots


def compose(work, name):
    spec = SPECS[name]
    meta, layers = load(work, name)
    layers, xf, k = place(layers, spec['box'], spec.get('anchor', 'centre'), spec.get('fixed'))
    pts = {n: xf(p) for n, p in meta.get('points', {}).items()}
    canvas = radial_bg(*spec['bg'], rays=spec.get('rays'))
    union = Image.new('L', (S, S), 0)
    for _, im in layers:
        union = ImageChops.lighter(union, alpha_of(im))
    l, t, r, b = solid(union).getbbox()
    centre = ((l + r) / 2, (t + b) / 2)
    extras = spec.get('extras', [])

    # behind the subject: swirl, glow, shadow
    if 'swirl' in extras:
        draw_swirl(canvas, (centre[0], centre[1] + 20))
    glow_src = dict(layers)[spec['glow_layer']] if spec.get('glow_layer') else None
    gmask = alpha_of(glow_src) if glow_src else union
    if spec.get('glow'):
        gr = spec.get('glow_radius', 46)
        halo = dilate(solid(gmask), gr).filter(ImageFilter.GaussianBlur(gr * 0.9))
        if spec['glow'] == 'rainbow':
            canvas.alpha_composite(rainbow_layer(halo.point(lambda v: int(v * 0.95)), centre))
            canvas.alpha_composite(rainbow_layer(halo.point(lambda v: int(v * 0.6)), centre))
        else:
            canvas.alpha_composite(colour_layer(halo, spec['glow'], 0.85))
    if 'platform' in extras:
        draw_platform(canvas, centre[0], b - 18, (r - l) * 1.0)
    if 'arcs' in extras and 'pivot' in pts:
        draw_arcs(canvas, pts['pivot'], pts['head'])
    shadow = dilate(solid(union), 12).filter(ImageFilter.GaussianBlur(16))
    moved = Image.new('L', (S, S), 0)
    moved.paste(shadow, (10, 22))          # (ImageChops.offset would wrap the bottom edge round to the top)
    shadow = moved
    shadow = ImageChops.subtract(shadow, solid(union))
    canvas.alpha_composite(colour_layer(shadow, (10, 10, 40), 0.45))

    # the layers, back to front, each with its own outline
    ring = spec.get('ring', 15)
    for i, (n, im) in enumerate(layers):
        if n not in spec.get('no_outline', ()):
            canvas.alpha_composite(colour_layer(outline_ring(alpha_of(im), ring if i == 0 else ring - 3), INK))
        canvas.alpha_composite(im)

    for x, y, rr in glint_spots(union, spec.get('glints', 0), sum(map(ord, name)) + 7):
        sparkle(canvas, x, y, rr)

    # in front: crown, snowflakes, sparkles, badges
    if 'crown' in extras and 'head_top' in pts:
        hx, hy = pts['head_top']
        draw_crown(canvas, hx + 10, hy + 40, 250, -10)
    if 'snowflakes' in extras:
        for (x, y, rr, rot) in ((150, 300, 62, 0.2), (880, 330, 52, 0.5), (845, 640, 40, 0.1), (190, 650, 44, 0.4)):
            draw_snowflake(canvas, x, y, rr, rot)
    avoid = [(bx, by, cap * len(txt) * 0.55 + 60, cap * 0.8 + 40) for txt, bx, by, cap, _, _ in spec.get('badges', [])]
    for x, y, rr in free_spots(union, spec.get('sparkles', 5), sum(map(ord, name)), avoid):
        sparkle(canvas, x, y, rr, spec.get('sparkle_colour', (255, 255, 255)))
    for txt, bx, by, cap, cols, ang in spec.get('badges', []):
        text_badge(canvas, txt, bx, by, cap, cols, ang)

    out_dir = OUT_LAUNCH if spec['kind'] == 'launch' else OUT_ICONS
    os.makedirs(out_dir, exist_ok=True)
    final = canvas.convert('RGB').resize((S // 2, S // 2), Image.LANCZOS)
    path = os.path.join(out_dir, name + '.png')
    final.save(path, optimize=True)
    return path


# ------------------------------------------------------------------ contact sheet

def contact_sheet():
    cols, tile, lab, gap = 5, 300, 78, 18
    rows = math.ceil(len(ORDER) / cols)
    W = cols * tile + (cols + 1) * gap
    H = 90 + rows * (tile + lab + gap) + gap
    sheet = Image.new('RGB', (W, H), (26, 30, 48))
    d = ImageDraw.Draw(sheet)
    f_title = ImageFont.truetype(LABEL_FONT, 34)
    f_lab = ImageFont.truetype(LABEL_FONT, 22)
    f_small = ImageFont.truetype(LABEL_FONT, 16)
    d.text((gap, 24), 'Rescue Pets From the Ice - icon drafts (passes, products, game icon concepts)', font=f_title, fill=(235, 242, 255))
    for i, name in enumerate(ORDER):
        spec = SPECS[name]
        folder = OUT_LAUNCH if spec['kind'] == 'launch' else OUT_ICONS
        path = os.path.join(folder, name + '.png')
        if not os.path.exists(path):
            continue
        c, rr = i % cols, i // cols
        x = gap + c * (tile + gap)
        y = 90 + rr * (tile + lab + gap)
        im = Image.open(path).convert('RGB').resize((tile, tile), Image.LANCZOS)
        sheet.paste(im, (x, y))
        small = Image.open(path).convert('RGB').resize((64, 64), Image.LANCZOS)   # how it reads small
        sheet.paste(small, (x + tile - 64, y + tile + 6))
        d.text((x, y + tile + 6), spec['title'], font=f_lab, fill=(235, 242, 255))
        d.text((x, y + tile + 36), '%s  -  %s.png' % (spec['kind'], name), font=f_small, fill=(150, 165, 200))
    path = os.path.join(OUT_ICONS, 'contact_sheet.png')
    sheet.save(path, optimize=True)
    return path


# ------------------------------------------------------------------ UI icons (--ui)
# The in-game button and window icons: 256x256, transparent, no text. Composed at 1024 like the store icons,
# with a much thicker outline (UI_RING px at 1024 = about 7 px at 256) so they read at 48 px on a coloured button.
OUT_UI = os.path.join(REPO, 'store-assets', 'ui-icons')
UI_SIZE = 256
UI_RING = 28
UI_BOX = (80, 80, 944, 944)         # the subject fills about 85% of the frame
CARDS = {'Build': (255, 150, 50), 'Upgrades': (80, 200, 100), 'Pets': (255, 120, 180), 'Book': (40, 190, 190),
         'Rebirth': (150, 90, 230), 'Home': (120, 200, 255), 'Shop': (120, 200, 255), 'Codes': (90, 110, 140),
         'Window': (40, 70, 130)}
UI_BUILDINGS = ['IcePickPost', 'ChiselMill', 'IceDrill', 'HeatLamp', 'WreckingCrane', 'FlamethrowerTurret', 'LavaPump', 'SunMirrorTower']
FROST = (215, 245, 255)
# card: the colour it sits on (CARDS); glow: soft halo colour (or None); sparkles / glints: as for the store icons;
# extras: 2D extras (snowflakes, streaks); box: where the subject goes, if not UI_BOX
UI_SPECS = {
    'Build': dict(card='Build', what='The tier-1 Ice Pick Post station with a chunky hammer', glow=(255, 240, 210), sparkles=2),
    'Upgrades': dict(card='Upgrades', what='The gold ice pick in front of a big green up-arrow', glow=(220, 255, 220), sparkles=2),
    'Pets': dict(card='Pets', what='Snow Bunny, cheering', glow=(255, 240, 250), sparkles=2),
    'Book': dict(card='Book', what='A chunky icy-blue book with a gold paw on the cover, Penguin Chick peeking over the top',
                 glow=(220, 255, 255), sparkles=2),
    'Rebirth': dict(card='Rebirth', what='A glowing faceted Frost Core inside two gold circular arrows', glow=(170, 230, 255),
                    glow_layer='core', glow_radius=60, sparkles=2, glints=1),
    'Home': dict(card='Home', what='A cosy ice-brick igloo with a snow cap and a warm glowing doorway', glow=(255, 250, 235), sparkles=2),
    'Shop': dict(card='Shop', what='An open wooden treasure chest heaped with cyan crystals', glow=(200, 250, 255), sparkles=2, glints=2),
    'Codes': dict(card='Codes', what='A gold ticket with a blue snowflake and a tear line', glow=(255, 245, 200), sparkles=2),
}
for _b in UI_BUILDINGS:
    UI_SPECS['Building_' + _b] = dict(card='Window', what='The tier-1 %s station, three-quarter view' % _b, glow=(220, 240, 255), sparkles=0)
# the pick tiers: each head pushed to its own colour (render_icons.PICK_HEADS), a glow of that colour behind the
# head, and a round tier-number badge in the bottom-right corner. tier: (what, head glow, badge top, badge bottom)
PICK_TIERS = {
    1: ('warm brown wooden head', (255, 170, 90), (225, 130, 60), (130, 62, 20)),
    2: ('grey stone head', (225, 228, 235), (165, 168, 176), (84, 86, 94)),
    3: ('dark steel-blue iron head', (185, 215, 255), (120, 160, 220), (40, 66, 130)),
    4: ('gold head', (255, 220, 70), (255, 200, 40), (190, 110, 0)),
    5: ('cyan crystal head', (90, 235, 255), (60, 215, 255), (0, 120, 180)),
    6: ('violet cosmic head', (175, 120, 255), (160, 90, 255), (75, 20, 170)),
}
_PICK_NAMES = ['Wooden', 'Stone', 'Iron', 'Gold', 'Diamond', 'Cosmic']
for _t in range(1, 7):
    UI_SPECS['Pick%d' % _t] = dict(card='Window', what='Ice pick tier %d (%s): %s, tier badge %d' % (_t, _PICK_NAMES[_t - 1], PICK_TIERS[_t][0], _t),
                                   glow=(220, 240, 255), sparkles=0, tier=_t, box=(70, 50, 890, 870))
UI_SPECS.update({
    'FrostTouch': dict(card='Window', what='The iron pick crusted with ice inside a glowing frost swirl, snowflakes',
                       glow=(170, 230, 255), extras=['snowflakes'], sparkles=0),
    'BiggerBurst': dict(card='Window', what='Cyan crystals bursting up out of a shattered ice block', glow=(170, 240, 255), sparkles=1, glints=2),
    'CrystalYield': dict(card='Window', what='A crystal pile with a green 3D plus', glow=(170, 240, 255), sparkles=1, glints=1),
    'FastSled': dict(card='Window', what='A wooden sled on metal runners carrying an ice block (a pet silhouette inside), speed streaks',
                     glow=(220, 240, 255), extras=['streaks'], box=(190, 110, 950, 914), sparkles=0),
    'UpgradeBadge': dict(card='Window', what='A green up-arrow, to overlay on a building icon for building upgrades', glow=None, sparkles=0),
})
UI_ORDER = list(UI_SPECS)


def ui_sparkle(canvas, cx, cy, r, colour=(255, 255, 255)):
    """a four-point sparkle with a dark outline (so it shows on pale cards too)"""
    m = Image.new('L', canvas.size, 0)
    ImageDraw.Draw(m).polygon(star_points(cx, cy, r, 0.22), fill=255)
    canvas.alpha_composite(colour_layer(dilate(m, max(6, r * 0.16)), INK))
    canvas.alpha_composite(colour_layer(m, colour))


def draw_streaks(canvas, union):
    """speed lines trailing off the subject's left side"""
    l, t, r, b = solid(union).getbbox()
    rows = [0.3, 0.52, 0.74]
    lens = [0.8, 1.0, 0.7]
    m = Image.new('L', canvas.size, 0)
    d = ImageDraw.Draw(m)
    w = 34
    for f, k in zip(rows, lens):
        y = t + (b - t) * f
        x1 = l + 40
        x0 = max(40, l - 180 * k)
        d.rounded_rectangle((x0, y - w / 2, x1, y + w / 2), radius=w / 2, fill=255)
    m = ImageChops.subtract(m, dilate(solid(union), UI_RING - 4))
    canvas.alpha_composite(colour_layer(dilate(m, UI_RING * 0.6), INK))
    canvas.alpha_composite(colour_layer(m, (255, 255, 255)))


def tier_badge(canvas, tier, r=182):
    """a round badge in the tier's colour in the bottom-right corner, a bold white numeral with a dark outline"""
    cx = cy = S - r - 34
    disc = Image.new('L', (S, S), 0)
    ImageDraw.Draw(disc).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    _, _, top, bottom = PICK_TIERS[tier]
    canvas.alpha_composite(colour_layer(dilate(disc, 30), INK))
    fill = gradient((S, S), top, bottom, cy - r, cy + r)
    fill.putalpha(disc)
    canvas.alpha_composite(fill)
    shine = Image.new('L', (S, S), 0)                           # a soft highlight on the upper half
    ImageDraw.Draw(shine).ellipse((cx - r * 0.72, cy - r * 0.86, cx + r * 0.72, cy - r * 0.05), fill=60)
    canvas.alpha_composite(colour_layer(shine.filter(ImageFilter.GaussianBlur(8)), (255, 255, 255)))
    font = ImageFont.truetype(FONT, int(r * 1.62))
    text = str(tier)
    l, t, rr, b = font.getbbox(text)
    x, y = cx - (l + rr) / 2, cy - (t + b) / 2 + 4
    d = ImageDraw.Draw(canvas)
    d.text((x, y + 10), text, font=font, fill=INK, stroke_width=26, stroke_fill=INK)     # a dark drop under it
    d.text((x, y), text, font=font, fill=(255, 255, 255), stroke_width=26, stroke_fill=INK)


def edge_fade(margin=70):
    """1 inside, fading to 0 at the frame's edge: the soft glow never ends in a hard line at the border"""
    ramp = np.clip(np.minimum(np.arange(S), S - 1 - np.arange(S)) / margin, 0, 1).astype(np.float32)
    return Image.fromarray((np.minimum(ramp[:, None], ramp[None, :]) * 255).astype(np.uint8), 'L')


def compose_ui(work, key):
    spec = UI_SPECS[key]
    meta, layers = load(os.path.join(work, 'ui'), key)
    layers, xf, k = place(layers, spec.get('box', UI_BOX))
    canvas = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    union = Image.new('L', (S, S), 0)
    for _, im in layers:
        union = ImageChops.lighter(union, alpha_of(im))
    gmask = alpha_of(dict(layers)[spec['glow_layer']]) if spec.get('glow_layer') else union
    if 'streaks' in spec.get('extras', ()):
        draw_streaks(canvas, union)
    if spec.get('glow'):
        gr = spec.get('glow_radius', 40)
        halo = dilate(solid(gmask), UI_RING + gr * 0.5).filter(ImageFilter.GaussianBlur(gr * 0.6))
        canvas.alpha_composite(colour_layer(ImageChops.multiply(halo, edge_fade()), spec['glow'], 0.45))
    if spec.get('tier'):
        hx, hy = xf(meta['points']['head'])
        blob = Image.new('L', (S, S), 0)
        ImageDraw.Draw(blob).ellipse((hx - 260, hy - 200, hx + 260, hy + 200), fill=255)
        blob = blob.filter(ImageFilter.GaussianBlur(90))
        canvas.alpha_composite(colour_layer(ImageChops.multiply(blob, edge_fade()), PICK_TIERS[spec['tier']][1], 0.95))
    shadow = dilate(solid(union), UI_RING).filter(ImageFilter.GaussianBlur(10))
    moved = Image.new('L', (S, S), 0)
    moved.paste(shadow, (0, 14))
    canvas.alpha_composite(colour_layer(moved, (10, 10, 40), 0.35))
    for i, (n, im) in enumerate(layers):
        if n not in spec.get('no_outline', ()):
            canvas.alpha_composite(colour_layer(outline_ring(alpha_of(im), UI_RING if i == 0 else UI_RING - 10), INK))
        canvas.alpha_composite(im)
    for x, y, rr in glint_spots(union, spec.get('glints', 0), sum(map(ord, key)) + 7):
        sparkle(canvas, x, y, rr * 1.3)
    if 'snowflakes' in spec.get('extras', ()):
        l, t, r, b = solid(union).getbbox()
        for (fx, fy, rr, rot) in ((0.12, 0.2, 70, 0.2), (0.88, 0.62, 58, 0.5), (0.2, 0.85, 46, 0.1)):
            draw_snowflake(canvas, l + (r - l) * fx, t + (b - t) * fy, rr, rot, FROST)
    for x, y, rr in free_spots(union, spec.get('sparkles', 0), sum(map(ord, key)), radius=0.44):
        ui_sparkle(canvas, x, y, rr * 1.3)
    if spec.get('tier'):
        tier_badge(canvas, spec['tier'])
    os.makedirs(OUT_UI, exist_ok=True)
    path = os.path.join(OUT_UI, key + '.png')
    canvas.resize((UI_SIZE, UI_SIZE), Image.LANCZOS).save(path, optimize=True)
    return path


def card_tile(colour, size):
    """a rounded colour card like the game's menu buttons: lighter top, darker bottom, a dark rim"""
    big = size * 4
    m = Image.new('L', (big, big), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, big - 1, big - 1), radius=big * 0.22, fill=255)
    top = tuple(min(255, int(c * 1.15 + 20)) for c in colour)
    bottom = tuple(int(c * 0.78) for c in colour)
    tile = Image.new('RGBA', (big, big), INK + (255,))
    inner = Image.new('L', (big, big), 0)
    pad = max(6, big // 26)
    ImageDraw.Draw(inner).rounded_rectangle((pad, pad, big - 1 - pad, big - 1 - pad), radius=big * 0.2, fill=255)
    tile.paste(gradient((big, big), top, bottom), (0, 0), inner)
    tile.putalpha(m)
    return tile.resize((size, size), Image.LANCZOS)


def ui_contact_sheet():
    cols, cell, row = 6, 300, 166
    rows = math.ceil(len(UI_ORDER) / cols)
    W = cols * cell + 30
    H = 80 + rows * row + 10
    sheet = Image.new('RGB', (W, H), (26, 30, 48))
    d = ImageDraw.Draw(sheet)
    f_title = ImageFont.truetype(LABEL_FONT, 30)
    f_lab = ImageFont.truetype(LABEL_FONT, 18)
    d.text((18, 22), 'Rescue Pets From the Ice - UI icons (each at 96 px and 48 px on its card)', font=f_title, fill=(235, 242, 255))
    for i, key in enumerate(UI_ORDER):
        path = os.path.join(OUT_UI, key + '.png')
        if not os.path.exists(path):
            continue
        icon = Image.open(path).convert('RGBA')
        colour = CARDS[UI_SPECS[key]['card']]
        x = 18 + (i % cols) * cell
        y = 80 + (i // cols) * row
        for size, ox, oy in ((96, 0, 0), (48, 116, 48)):
            card = card_tile(colour, int(size * 1.2))
            card.alpha_composite(icon.resize((size, size), Image.LANCZOS), (int(size * 0.1), int(size * 0.1)))
            sheet.paste(card, (x + ox, y + oy), card)
        checker = Image.new('RGBA', (100, 100), (200, 200, 200, 255))
        cd = ImageDraw.Draw(checker)
        for cy in range(0, 100, 10):
            for cx in range(0, 100, 10):
                if (cx + cy) // 10 % 2:
                    cd.rectangle((cx, cy, cx + 9, cy + 9), fill=(160, 160, 160, 255))
        checker.alpha_composite(icon.resize((100, 100), Image.LANCZOS))
        sheet.paste(checker.convert('RGB'), (x + 178, y + 16))
        d.text((x, y + 124 + 8), key, font=f_lab, fill=(235, 242, 255))
    path = os.path.join(OUT_UI, 'contact_sheet.png')
    sheet.save(path, optimize=True)
    return path


# ------------------------------------------------------------------ Blender

def blender_exe():
    exe = os.environ.get('BLENDER_EXE')
    if exe:
        return exe
    found = sorted(glob.glob(r'C:\Program Files\Blender Foundation\*\blender.exe'))
    if not found:
        raise SystemExit('Blender not found: set BLENDER_EXE')
    return found[-1]


def run_blender(args):
    r = subprocess.run([blender_exe(), '-b', '--factory-startup', '--python', os.path.join(HERE, 'render_icons.py'), '--'] + args,
                       capture_output=True, text=True, encoding='utf8', errors='replace')
    text = r.stdout + r.stderr
    if 'Traceback' in text or r.returncode != 0:
        print(text[-3000:])
        raise SystemExit('Blender failed: ' + ' '.join(args))
    return text


def render(work, names, jobs, mode='render'):
    if not os.path.exists(os.path.join(work, 'picks.blend')):
        print('building the ice picks ...')
        run_blender(['picks', work])
    def one(n):
        run_blender([mode, work, n])
        print('rendered', n)
    with ThreadPoolExecutor(jobs) as pool:
        list(pool.map(one, names))


if __name__ == '__main__':
    args = sys.argv[1:]
    work = os.path.join(tempfile.gettempdir(), 'rpfi_icons_work')
    jobs = 3
    if '--work' in args:
        i = args.index('--work')
        work = os.path.abspath(args[i + 1])
        del args[i:i + 2]
    if '--jobs' in args:
        i = args.index('--jobs')
        jobs = int(args[i + 1])
        del args[i:i + 2]
    flags = {a for a in args if a.startswith('--')}
    if '--ui' in flags:          # the UI icons: store-assets/ui-icons/
        names = [a for a in args if not a.startswith('--')] or UI_ORDER
        for n in names:
            if n not in UI_SPECS:
                raise SystemExit('unknown UI icon: %s (known: %s)' % (n, ', '.join(UI_ORDER)))
        if '--sheet-only' not in flags:
            if '--render' in flags:
                render(work, names, jobs, 'ui')
            for n in names:
                print('composed', compose_ui(work, n))
        print('sheet', ui_contact_sheet())
        raise SystemExit(0)
    names = [a for a in args if not a.startswith('--')] or ORDER
    for n in names:
        if n not in SPECS:
            raise SystemExit('unknown icon: %s (known: %s)' % (n, ', '.join(ORDER)))
    if '--sheet-only' not in flags:
        if '--render' in flags:
            render(work, names, jobs)
        for n in names:
            print('composed', compose(work, n))
    print('sheet', contact_sheet())
