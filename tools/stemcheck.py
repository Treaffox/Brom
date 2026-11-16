#!/usr/bin/env python3
"""Sucht kleine Stufen an waagrechten/senkrechten Kanten: On-Curve-Nachbarn,
die fast, aber nicht ganz auf gleicher Höhe (bzw. gleicher x) liegen.

  stemcheck.py FONT.ttf [Glyphen …] [--wght 100,400,…] [--tol 6]
"""
import argparse
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen


def edges(gs, name):
    rec = DecomposingRecordingPen(gs)
    gs[name].draw(rec)
    out = []
    start = cur = None
    for op, args in rec.value:
        if op == "moveTo":
            start = cur = args[0]
        elif op == "lineTo":
            out.append((cur, args[0])); cur = args[0]
        elif op in ("curveTo", "qCurveTo"):
            cur = args[-1]
        elif op == "closePath":
            if cur != start:
                out.append((cur, start))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--wght", default="100,250,400,500,600,700,800,900")
    ap.add_argument("--tol", type=float, default=8)
    a = ap.parse_args()
    f = TTFont(a.font)
    cmap = f.getBestCmap()
    names = [cmap.get(ord(g), g) if len(g) == 1 else g for g in (a.glyphs or list("bdhilfnmkt"))]
    total = 0
    for w in [int(x) for x in a.wght.split(",")]:
        gs = f.getGlyphSet(location={"wght": w}) if "fvar" in f else f.getGlyphSet()
        for n in names:
            hits = []
            for (x0, y0), (x1, y1) in edges(gs, n):
                dx, dy = abs(x1 - x0), abs(y1 - y0)
                # fast waagrecht/senkrecht, aber nicht exakt: Schräge von < tol Einheiten über eine lange Kante
                if 0 < dy <= a.tol and dx > 4 * dy and dx > 20:
                    hits.append(f"waagrecht {round(y0,1)}→{round(y1,1)} über {round(dx)}")
                if 0 < dx <= a.tol and dy > 4 * dx and dy > 20:
                    hits.append(f"senkrecht {round(x0,1)}→{round(x1,1)} über {round(dy)}")
            if hits:
                total += len(hits)
                print(f"wght {w} {n}: " + "; ".join(hits[:4]) + (" …" if len(hits) > 4 else ""))
    print(f"{total} schiefe Kanten")


if __name__ == "__main__":
    main()
