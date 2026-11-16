"""Glatte Einmündung der linken y-Diagonale in die Unterlänge.

Geist lässt die linke Diagonale des y kurz über der Grundlinie mit einer kleinen
waagrechten Stufe enden, bevor die Unterlänge anschließt. Diese Stufe wirkt wie
ein sichtbares Ende. Hier werden die zwei Punkte der Stufe durch den Schnittpunkt
der Diagonalkante mit der Unterlängenkante ersetzt.

Erkennung (im Regular-Master, Anwendung in allen Mastern):
  P(i-1) → P(i): lange Diagonale von der x-Höhe nach rechts unten
  P(i)  → P(i+1): kurzes waagrechtes Stück knapp über/unter der Grundlinie
  P(i+1) → P(i+2): Kante, die weiter nach unten (in die Unterlänge) läuft
"""
import math
from .tips import _intersect


def _step_at(pts, i, stem, xheight):
    n = len(pts)
    a, b, c, d = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
    if any(p.type != "line" for p in (a, b, c, d)):
        return None
    if b.y != c.y or not (-0.12 * xheight <= b.y <= 0.12 * xheight):
        return None
    flat = abs(c.x - b.x)
    if flat == 0 or flat > 0.9 * stem:
        return None
    # Diagonale kommt von oben (nahe x-Höhe) und läuft nach rechts unten
    if not (a.y > 0.7 * xheight and a.x < b.x):
        return None
    # danach geht es weiter nach unten
    if not d.y < c.y - 0.03 * xheight:
        return None
    r = _intersect((a.x, a.y), (b.x, b.y), (d.x, d.y), (c.x, c.y))
    if r is None:
        return None
    X, t = r
    if t < 1.0 or X[1] > b.y or X[1] < d.y:  # Schnittpunkt zwischen Stufe und nächstem Punkt
        return None
    return X


def find_steps(font, stem, names=None):
    xh = font.info.xHeight or 530
    found = {}
    for g in font:
        if names is not None and g.name not in names:
            continue
        for ci, c in enumerate(g.contours):
            for i in range(len(c.points)):
                if _step_at(c.points, i, stem, xh) is not None:
                    found.setdefault(g.name, []).append((ci, i))
    return found


def smooth_steps(font, selection):
    n = 0
    for name, items in selection.items():
        if name not in font:
            continue
        g = font[name]
        for ci, i in sorted(items, key=lambda x: (x[0], -x[1])):
            pts = g.contours[ci].points
            k = len(pts)
            a, b, c, d = pts[(i - 1) % k], pts[i], pts[(i + 1) % k], pts[(i + 2) % k]
            r = _intersect((a.x, a.y), (b.x, b.y), (d.x, d.y), (c.x, c.y))
            if r is None:
                continue
            X, _ = r
            b.x, b.y = round(X[0]), round(X[1])
            del pts[(i + 1) % k]
            n += 1
    return n
