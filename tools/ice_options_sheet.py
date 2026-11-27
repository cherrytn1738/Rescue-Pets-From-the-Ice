"""ice_options_sheet.py - the ice block options side by side, one sheet per view (the redesign's part 1).

    python tools/ice_options_sheet.py

Reads store-assets/visual-review/ice-options/<A|B|C>_<view>.jpg (taken by `python tools/visual_review.py ice-options`)
and writes compare_<view>.jpg beside them: A, B and C in a row with their names, so the gallery (index.html, after
`python tools/visual_review.py --index`) shows the three looks next to each other.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(ROOT, "store-assets", "visual-review", "ice-options")
OPTIONS = [("A", "A  faceted iceberg"), ("B", "B  carved block"), ("C", "C  crystal geode")]
VIEWS = ["tapping", "close", "plaza", "crack3"]
TILE = (960, 540)
LABEL = 64


def font(size):
    for name in ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    made = 0
    title_font = font(38)
    for view in VIEWS:
        tiles = []
        for option, label in OPTIONS:
            path = os.path.join(FOLDER, "%s_%s.jpg" % (option, view))
            if not os.path.exists(path):
                print("missing", os.path.relpath(path, ROOT))
                break
            tiles.append((Image.open(path).convert("RGB").resize(TILE, Image.LANCZOS), label))
        else:
            sheet = Image.new("RGB", (TILE[0] * len(tiles) + 8 * (len(tiles) - 1), TILE[1] + LABEL), (24, 36, 56))
            draw = ImageDraw.Draw(sheet)
            for i, (tile, label) in enumerate(tiles):
                x = i * (TILE[0] + 8)
                sheet.paste(tile, (x, LABEL))
                draw.text((x + 18, 12), label, fill=(240, 248, 255), font=title_font)
            out = os.path.join(FOLDER, "compare_%s.jpg" % view)
            sheet.save(out, "JPEG", quality=88)
            print("wrote", os.path.relpath(out, ROOT))
            made += 1
    return 0 if made == len(VIEWS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
