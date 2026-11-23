"""Roster sheet: every creature's 3/4 view with its dark silhouette (the shape inside the ice) and its
Golden version, in CreatureConfig order, labelled with name and rarity.

    python tools/pets/roster_sheet.py   ->  store-assets/creatures/RosterSheet.png
"""
import os, re
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'store-assets', 'creatures')
config = open(os.path.join(ROOT, 'src', 'replicated', 'CreatureConfig.luau'), encoding='utf8').read()
creatures = re.findall(r'Id = "(\w+)", Name = "([^"]+)", Rarity = "(\w+)"', config)
RARITY = {'Common': (190, 200, 215), 'Uncommon': (120, 220, 140), 'Rare': (90, 170, 255),
          'Epic': (190, 120, 255), 'Legendary': (255, 200, 60), 'Mythic': (255, 120, 200)}
CELL, SMALL, COLS = 420, 200, 3
try:
    font = ImageFont.truetype('arialbd.ttf', 30)
    small = ImageFont.truetype('arial.ttf', 22)
except OSError:
    font = small = ImageFont.load_default()
tile_w, tile_h = CELL + SMALL + 30, CELL + 70
rows = (len(creatures) + COLS - 1) // COLS
sheet = Image.new('RGB', (COLS * tile_w + 20, rows * tile_h + 90), (24, 34, 52))
draw = ImageDraw.Draw(sheet)
draw.text((20, 22), 'Rescue Pets From the Ice: the 18 launch creatures (3/4 view, the silhouette in the ice, Golden)', font=font, fill=(235, 245, 255))
for i, (cid, name, rarity) in enumerate(creatures):
    x0, y0 = 10 + (i % COLS) * tile_w, 80 + (i // COLS) * tile_h
    r = os.path.join(OUT, cid, 'render')
    draw.rounded_rectangle((x0, y0, x0 + tile_w - 10, y0 + tile_h - 10), 16, fill=(36, 52, 78), outline=RARITY[rarity], width=4)
    main = Image.open(os.path.join(r, 'view_q34_ol.png')).convert('RGB').resize((CELL, CELL))
    sheet.paste(main, (x0 + 8, y0 + 8))
    for j, v in enumerate(('variant_silhouette_ol.png', 'variant_golden_ol.png')):
        im = Image.open(os.path.join(r, v)).convert('RGB').resize((SMALL, SMALL))
        sheet.paste(im, (x0 + CELL + 14, y0 + 8 + j * (SMALL + 10)))
    draw.text((x0 + 14, y0 + CELL + 14), name, font=font, fill=(255, 255, 255))
    draw.text((x0 + CELL + 14, y0 + CELL + 20), rarity, font=small, fill=RARITY[rarity])
path = os.path.join(OUT, 'RosterSheet.png')
sheet.save(path)
print(path, sheet.size)
