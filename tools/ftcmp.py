#!/usr/bin/env python3
"""Rendert Text mit FreeType: ohne Hinting vs. Autohinter (light/normal), bei einem Gewicht.

  ftcmp.py FONT.ttf WGHT PX TEXT OUT.png
"""
import sys
import freetype
from PIL import Image

path, wght, px, text, out = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
MODES = [
    ("ohne Hinting", freetype.FT_LOAD_NO_HINTING),
    ("Autohint light", freetype.FT_LOAD_FORCE_AUTOHINT | freetype.FT_LOAD_TARGET_LIGHT),
    ("Autohint normal", freetype.FT_LOAD_FORCE_AUTOHINT),
]
rows = []
for label, flags in MODES:
    face = freetype.Face(path)
    face.set_char_size(px * 64)
    try:
        face.set_var_design_coords((wght,))
    except Exception:
        pass
    W = int(px * len(text) * 0.75) + 40
    H = int(px * 1.25)
    img = Image.new("L", (W, H), 0)
    x = 20
    for ch in text:
        face.load_char(ch, flags | freetype.FT_LOAD_RENDER)
        g = face.glyph
        bm = g.bitmap
        if bm.width and bm.rows:
            gi = Image.frombytes("L", (bm.width, bm.rows), bytes(bm.buffer))
            img.paste(255, (x + g.bitmap_left, int(px * 0.95) - g.bitmap_top), gi)
        x += g.advance.x >> 6
    rows.append(img.crop((0, 0, x + 20, H)))
sheet = Image.new("L", (max(r.width for r in rows), sum(r.height for r in rows)), 0)
y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height
sheet.save(out)
print(out, sheet.size, [m[0] for m in MODES])
