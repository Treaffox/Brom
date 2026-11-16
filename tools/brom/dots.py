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


def square_dots(font, selection, italic_angle=0.0, min_side=0):
    """Macht die ausgewählten Rechtecke quadratisch. Gibt die Anzahl zurück.

    min_side: Der Punkt ist nie schmaler als der Stamm (in Black war das i-Punkt-Quadrat
    mit gleicher Fläche schmaler als der Stamm darunter). Die Unterkante bleibt, der Punkt
    wächst nach oben und beidseitig um die Mitte. Beim Interpolieren bleibt der Punkt so
    in jedem Gewicht mindestens so breit wie der Stamm."""
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
            side = max(round(math.sqrt((x1 - x0) * (y1 - y0))), round(min_side))
            nx0 = round((x0 + x1) / 2 - side / 2)
            nx1 = nx0 + side
            ny0, ny1 = y0, y0 + side
            for p, (ux, uy) in zip(c.points, pts):
                nx = nx0 if abs(ux - x0) < abs(ux - x1) else nx1
                ny = ny0 if uy == y0 else ny1
                p.x, p.y = round(nx + ny * tan), round(ny)
            n += 1
    return n


# Runde Punkte (Stilset ss08) und die Punkte der griechischen Dieresis-Tonos-Akzente
# bestehen aus Kurven, nicht aus Rechtecken. Sie werden gleichmäßig vergrößert, falls sie
# schmaler als der Stamm sind.
ROUND_DOT_GLYPHS = re.compile(r"^(dotaccentcomb|dieresiscomb|dotbelowcomb|dotaccent|dieresis)(\.narrow)?\.ss08$"
                              r"|^dieresistonos(_narrow)?$")


def widen_round_dots(font, min_width, italic_angle=0.0):
    """Vergrößert runde Punkte auf mindestens min_width (gleichmäßig, Form bleibt).

    Waagrechte Mitte bleibt. Fest bleibt die Kante, die dem Buchstaben am nächsten ist:
    bei Punkten über der Grundlinie die Unterkante, bei Punkten darunter die Oberkante.
    Die Punktzahl bleibt, die Interpolation also kompatibel. Gibt die Anzahl zurück."""
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    n = 0
    for g in font:
        if not ROUND_DOT_GLYPHS.match(g.name):
            continue
        for c in g.contours:
            if not c.points:
                continue
            pts = [(p.x - p.y * tan, p.y) for p in c.points]
            xs = [x for x, _ in pts]
            ys = [y for _, y in pts]
            w = max(xs) - min(xs)
            if w <= 0 or w >= min_width:
                continue
            k = min_width / w
            cx = (max(xs) + min(xs)) / 2
            ay = min(ys) if min(ys) >= 0 else max(ys)
            for p, (ux, uy) in zip(c.points, pts):
                nx, ny = cx + (ux - cx) * k, ay + (uy - ay) * k
                p.x, p.y = round(nx + ny * tan), round(ny)
            n += 1
    return n


def space_dieresis(font, min_gap, italic_angle=0.0, pattern=r"^dieresiscomb\.narrow$"):
    """Schiebt die zwei Punkte eines schmalen Dieresis-Akzents auseinander, falls der Abstand
    kleiner als min_gap ist (nach dem Vergrößern der Punkte auf Stammbreite sonst verschmolzen).
    Die Mitte des Paars bleibt. Gibt die Anzahl der geänderten Glyphen zurück."""
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    rx = re.compile(pattern)
    n = 0
    for g in font:
        if not rx.match(g.name) or len(g.contours) != 2:
            continue
        spans = []
        for c in g.contours:
            xs = [p.x - p.y * tan for p in c.points]
            spans.append((min(xs), max(xs)))
        left, right = (0, 1) if spans[0][0] <= spans[1][0] else (1, 0)
        gap = spans[right][0] - spans[left][1]
        if gap >= min_gap:
            continue
        d = (min_gap - gap) / 2
        for idx, sign in ((left, -1), (right, 1)):
            for p in g.contours[idx].points:
                ux = p.x - p.y * tan + sign * d
                p.x = round(ux + p.y * tan)
        n += 1
    return n


BAR_GLYPHS = re.compile(r"^exclam(down)?(\.ss08)?$")


def straighten_bars(font, italic_angle=0.0):
    """Der Balken von ! und ¡ hat durchgehend die Breite seines breiten Endes, wie ein
    umgedrehtes i (vorher lief er zum Punkt hin auf rund 65 % der Breite zusammen).

    Alle Punkte der Kontur rücken (entneigt gemessen) auf die linke bzw. rechte Kante des
    breiten Endes, die Kurvenstücke werden zu Geraden. Gilt in allen Mastern gleich, die
    Punktzahl bleibt gleich, die Interpolation also kompatibel. Gibt die Anzahl zurück."""
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    n = 0
    for g in font:
        if not BAR_GLYPHS.match(g.name):
            continue
        for c in g.contours:
            pts = list(c.points)
            if len(pts) < 8:
                continue
            us = [(p.x - p.y * tan, p.y) for p in pts]
            xs = [x for x, _ in us]
            ys = [y for _, y in us]
            if (max(ys) - min(ys)) < 2 * (max(xs) - min(xs)):
                continue  # kein Balken (z. B. der Punkt)
            top = [x for x, y in us if y == max(ys)]
            bot = [x for x, y in us if y == min(ys)]
            ends = [top, bot] if (max(top) - min(top)) >= (max(bot) - min(bot)) else [bot, top]
            left, right = min(ends[0]), max(ends[0])
            cx = (max(xs) + min(xs)) / 2
            new = []
            for p, (ux, uy) in zip(pts, us):
                if p.type is None:
                    continue  # Kurvenhandles entfallen, die Seiten sind jetzt Geraden
                nx = left if ux < cx else right
                p.x, p.y = round(nx + uy * tan), round(uy)
                new.append(p)
            for p in new:
                if p.type == "curve":
                    p.type = "line"
            c.points = new
            n += 1
    return n
