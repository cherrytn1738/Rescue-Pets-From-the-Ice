"""Writes assets/textures/StudOverlay.png from the lihfolk-stud-voxel skill's Roblox square-stud texture
(8 x 8 studs): transparent where the stud texture is mid grey, white (highlights) and black (shadows) with
alpha where it isn't. On a voxel building's MeshPart (TextureID) the part's Color shows through, so one image
studs every colour.   python tools/make_stud_overlay.py <path to roblox_square_studs.png>"""
import os, sys
import numpy as np
from PIL import Image

src = sys.argv[1]
a = np.asarray(Image.open(src).convert("RGB")).astype(float)
L = a.mean(-1)
mid = float(np.median(L))
alpha = np.clip(np.abs(L - mid) / 128.0 * 1.2, 0, 0.55)
rgb = np.where((L > mid)[..., None], 255.0, 0.0) * np.ones(3)
out = np.dstack([rgb, alpha * 255]).astype(np.uint8)
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "textures", "StudOverlay.png")
Image.fromarray(out, "RGBA").save(path)
print("wrote", path, "mid grey", round(mid, 1))
