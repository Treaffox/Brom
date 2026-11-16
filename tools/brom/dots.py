"""Quadratische Punkte (i, j, Umlaute, Satzzeichen …).

Ein Punkt ist eine Kontur aus genau vier geraden Punkten (Rechteck), klein im
Verhältnis zur Stammstärke und annähernd quadratisch. Die Auswahl wird einmal im
Regular-Master getroffen und in allen Mastern gleich angewendet, damit die
Interpolation einheitlich bleibt.

Umformung: Quadrat mit gleicher Fläche, waagrechte Mitte bleibt, Unterkante
bleibt (Abstand zu Stamm bzw. Grundlinie ändert sich nicht).
"""
import math
import re

# Nur echte Punkt-Glyphen. i, j, Umlaute, : ; ! ? … sind Komposita daraus.
DOT_GLYPHS = re.compile(r"^(period|periodcentered|dotaccentcomb|dotbelowcomb|dieresiscomb|dieresisbelowcomb"
                        r"|dotaccent|dieresis)(\..+)?$")


def _rect(contour, tan=0.0):
    pts = contour.points
    if len(pts) != 4 or any(p.type != "line" for p in pts):
        return None
    xs = sorted({round(p.x - p.y * tan) for p in pts})
    ys = sorted({p.y for p in pts})
    if len(ys) != 2 or len(xs) > 2 + (2 if tan else 0):
        return None  # nicht achsparallel
    if tan:
        lo = sorted(round(p.x - p.y * tan) for p in pts)
        if lo[1] - lo[0] > 2 or lo[3] - lo[2] > 2:
            return None
        xs = [lo[0], lo[3]]
    return xs[0], ys[0], xs[-1], ys[1]


def find_dots(font, stem, max_rel=2.3, min_ratio=0.45, max_ratio=2.3, italic_angle=0.0):
    """Gibt {Glyphname: [Konturindex …]} der Punkt-Rechtecke zurück."""
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    found = {}
    for g in font:
        if not DOT_GLYPHS.match(g.name):
            continue
        for i, c in enumerate(g.contours):
            r = _rect(c, tan)
            if r is None:
                continue
            w, h = r[2] - r[0], r[3] - r[1]
            if w <= 0 or h <= 0 or max(w, h) > max_rel * stem:
                continue
            if not (min_ratio <= h / w <= max_ratio):
                continue
            found.setdefault(g.name, []).append(i)
    return found


def square_dots(font, selection, italic_angle=0.0):
    """Macht die ausgewählten Rechtecke quadratisch. Gibt die Anzahl zurück."""
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    n = 0
    for name, idxs in selection.items():
        if name not in font:
            continue
        g = font[name]
        for i in idxs:
            if i >= len(g.contours):
                continue
            c = g.contours[i]
            # Kursive: Rechteck ist geneigt, also entneigt messen
            pts = [(p.x - p.y * tan, p.y) for p in c.points]
            xs = sorted(x for x, _ in pts)
            ys = sorted({y for _, y in pts})
            if len(c.points) != 4 or len(ys) != 2:
                continue
            x0, x1, y0, y1 = (xs[0] + xs[1]) / 2, (xs[2] + xs[3]) / 2, ys[0], ys[1]
            side = round(math.sqrt((x1 - x0) * (y1 - y0)))
            nx0 = round((x0 + x1) / 2 - side / 2)
            nx1 = nx0 + side
            ny0, ny1 = y0, y0 + side
            for p, (ux, uy) in zip(c.points, pts):
                nx = nx0 if abs(ux - x0) < abs(ux - x1) else nx1
                ny = ny0 if uy == y0 else ny1
                p.x, p.y = round(nx + ny * tan), round(ny)
            n += 1
    return n
