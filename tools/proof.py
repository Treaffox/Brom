#!/usr/bin/env python3
"""Rendert Proof-Bögen als PNG (HarfBuzz-Shaping + FreeType-Rasterung).

  proof.py OUT.png --font PFAD[:wght] [--font ...] --text "..." [--text ...]
           [--size 96] [--weights 100,400,900] [--features ss01,zero] [--glyphs a,a.ss01]

Jede Zeile = Font x Gewicht x Text. --glyphs rendert Glyphen direkt nach Namen
(auch nicht kodierte), getrennt durch Komma.
"""
import argparse
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.basePen import BasePen
from PIL import Image, ImageDraw, ImageFont, ImageOps

_cache = {}


class CubicOut(BasePen):
    """Zerlegt Komponenten und wandelt quadratische Splines exakt in kubische um."""
    def __init__(self, gs, out):
        super().__init__(gs)
        self.out = out
    def _moveTo(self, p): self.out.moveTo(p)
    def _lineTo(self, p): self.out.lineTo(p)
    def _curveToOne(self, a, b, c): self.out.curveTo(a, b, c)
    def _closePath(self): self.out.closePath()
    def _endPath(self): self.out.endPath()


def _load(path):
    if path not in _cache:
        tt = TTFont(path)
        with open(path, "rb") as fh:
            face = hb.Face(fh.read())
        _cache[path] = (tt, face)
    return _cache[path]


def render_line(path, wght, size, text=None, glyphs=None, features=()):
    tt, face = _load(path)
    upm = tt["head"].unitsPerEm
    loc = {}
    if "fvar" in tt and wght is not None:
        loc = {"wght": wght}
    gs = tt.getGlyphSet(location=loc or None)
    order = tt.getGlyphOrder()
    run = []  # (glyphname, x_offset, y_offset, advance)
    if glyphs:
        for name in glyphs:
            if name not in gs:
                continue
            run.append((name, 0, 0, gs[name].width + 60))
    else:
        font = hb.Font(face)
        if loc:
            font.set_variations(loc)
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf, {f: True for f in features})
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            run.append((order[info.codepoint], pos.x_offset, pos.y_offset, pos.x_advance))
    scale = size / upm
    width = int(sum(r[3] for r in run) * scale) + 4
    asc, desc = int(size * 1.0), int(size * 0.32)
    pen = FreeTypePen(gs)
    x = 0
    for name, xo, yo, adv in run:
        tp = TransformPen(pen, (scale, 0, 0, scale, (x + xo) * scale, (yo) * scale + desc))
        gs[name].draw(CubicOut(gs, tp))
        x += adv
    if width < 8:
        width = 8
    img = pen.image(width=width, height=asc + desc, contain=False)
    return img  # RGBA/‘L’ alpha mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--font", action="append", required=True)
    ap.add_argument("--text", action="append", default=[])
    ap.add_argument("--glyphs", action="append", default=[])
    ap.add_argument("--size", type=int, default=96)
    ap.add_argument("--weights", default="")
    ap.add_argument("--features", default="")
    ap.add_argument("--label", action="store_true")
    a = ap.parse_args()
    feats = [f for f in a.features.split(",") if f]

    rows = []
    for spec in a.font:
        path, _, w = spec.rpartition(":") if spec.rsplit(":", 1)[-1].isdigit() else (spec, "", "")
        ws = [int(w)] if w else ([int(x) for x in a.weights.split(",")] if a.weights else [None])
        for wg in ws:
            for t in a.text:
                rows.append((path, wg, render_line(path, wg, a.size, text=t, features=feats)))
            for g in a.glyphs:
                rows.append((path, wg, render_line(path, wg, a.size, glyphs=g.split(","))))

    pad = a.size // 3
    W = max(r[2].size[0] for r in rows) + 2 * pad
    H = sum(r[2].size[1] for r in rows) + 2 * pad
    sheet = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(sheet)
    y = pad
    lab = ImageFont.load_default()
    for path, wg, img in rows:
        alpha = img.split()[-1] if img.mode != "L" else img
        sheet.paste(0, (pad, y), alpha)
        if a.label:
            d.text((4, y + 2), f"{path.split('/')[-1][:20]} {wg or ''}", font=lab, fill=120)
        y += img.size[1]
    sheet.save(a.out)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
