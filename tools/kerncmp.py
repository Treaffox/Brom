#!/usr/bin/env python3
"""Vergleicht Kerning-Werte von Buchstabenpaaren zwischen zwei Fonts.

  kerncmp.py ALT.ttf NEU.ttf [wght] PAAR [PAAR ...]
"""
import sys
import uharfbuzz as hb


def kern(path, pair, wght):
    face = hb.Face(open(path, "rb").read())
    font = hb.Font(face)
    font.set_variations({"wght": wght})
    total = []
    for txt in (pair, pair[0], pair[1]):
        buf = hb.Buffer()
        buf.add_str(txt)
        buf.guess_segment_properties()
        hb.shape(font, buf, {})
        total.append(sum(p.x_advance for p in buf.glyph_positions))
    return total[0] - total[1] - total[2]


def main():
    a, b = sys.argv[1], sys.argv[2]
    rest = sys.argv[3:]
    wght = 400
    if rest and rest[0].isdigit():
        wght = int(rest.pop(0))
    changed = 0
    for p in rest:
        ka, kb = kern(a, p, wght), kern(b, p, wght)
        changed += ka != kb
        print(f"{p}  alt {ka:>5}  neu {kb:>5}" + ("" if ka == kb else "   *"))
    print(f"{changed} von {len(rest)} Paaren geändert")


if __name__ == "__main__":
    main()
