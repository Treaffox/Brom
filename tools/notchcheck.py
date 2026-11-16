#!/usr/bin/env python3
"""Findet winzige Segmente (Macken) in Umrissen bei einem Gewicht.

  notchcheck.py FONT.ttf WGHT [Glyphen …] [--max 12]
Listet je Glyph On-Curve-Segmente kürzer als --max Einheiten.
"""
import argparse
import math
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("wght", type=float)
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--max", type=float, default=12)
    a = ap.parse_args()
    f = TTFont(a.font)
    cmap = f.getBestCmap()
    gs = f.getGlyphSet(location={"wght": a.wght})
    names = [cmap.get(ord(g), g) if len(g) == 1 else g for g in (a.glyphs or list("bdhilfn"))]
    for n in names:
        rec = DecomposingRecordingPen(gs)
        gs[n].draw(rec)
        cur = start = None
        short = []
        for op, args in rec.value:
            if op == "moveTo":
                cur = start = args[0]
                continue
            if op == "closePath":
                end = start
            elif op in ("lineTo", "curveTo", "qCurveTo"):
                end = args[-1]
            else:
                continue
            d = math.dist(cur, end)
            if 0 < d < a.max:
                short.append(f"{op[:4]} ({cur[0]:.1f},{cur[1]:.1f})→({end[0]:.1f},{end[1]:.1f}) {d:.1f}")
            cur = end
        print(f"{n}: {len(short)} kurze Segmente" + ("".join("\n   " + s for s in short[:8])))


if __name__ == "__main__":
    main()
