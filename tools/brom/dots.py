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


# ---------------------------------------------------------------------------------------
# Ausrufezeichen: Balken so breit wie der Punkt. Abstand Punkt–Strich bei i, j, ! ¡ ? ¿ größer.

BAR_DOT_GLYPHS = re.compile(r"^exclam(down)?(\.ss08)?$")
GAP_BAR_GLYPHS = re.compile(r"^(exclam|question)(down)?(\.ss08)?$")
DOT_ACCENT = re.compile(r"^dotaccentcomb(\.ss08)?$")
DOTLESS_BASE = re.compile(r"^(idotless|jdotless)$")
DIERESIS_ON_I = re.compile(r"^dieresiscomb(\.narrow)?(\.ss08)?$")


def _contour_box(points, tan):
    us = [p[0] - p[1] * tan for p in points]
    ys = [p[1] for p in points]
    return min(us), max(us), min(ys), max(ys)


def _split_dot_bar(font, glyph, tan):
    """Trennt ein ! ? ¡ ¿ in Punkt und Strich.

    Gibt (dot_box, bars) zurück: dot_box ist die entneigte Ausdehnung (umin, umax, ymin, ymax)
    des Punkts, bars die Konturen des Strichs. Der Punkt ist entweder eine period-Komponente
    (auch gespiegelt/gedreht) oder, wie beim kursiven ¡, eine eigene kleine Kontur. (None, [])
    wenn beides fehlt."""
    for comp in glyph.components:
        if comp.baseGlyph.startswith("period"):
            xx, xy, yx, yy, dx, dy = comp.transformation
            pts = [(xx * p.x + yx * p.y + dx, xy * p.x + yy * p.y + dy)
                   for c in font[comp.baseGlyph].contours for p in c.points]
            return _contour_box(pts, tan), [c for c in glyph.contours if len(c.points) >= 4]
    boxes = [(c, _contour_box([(p.x, p.y) for p in c.points], tan)) for c in glyph.contours if c.points]
    dots = [(c, b) for c, b in boxes if (b[3] - b[2]) <= 1.6 * (b[1] - b[0])]
    bars = [c for c, b in boxes if (b[3] - b[2]) > 1.6 * (b[1] - b[0])]
    if len(dots) != 1 or not bars:
        return None, []
    return dots[0][1], bars


def _conform_dot_contour(font, glyph, bars, tan):
    """Das kursive ¡ hat den Punkt als eigene, nicht ganz quadratische Kontur (Thin 59 × 65,
    Black 188 × 173 statt 62 × 62 und 183 × 183 wie beim Punkt). Diese Kontur wird zu genau dem
    Punkt des Punktzeichens (Breite und Höhe), Oberkante und waagrechte Mitte bleiben.
    Nur für vierpunktige Rechtecke, runde Punkte (ss08) bleiben. Gibt die neue Ausdehnung
    (umin, umax, ymin, ymax) zurück oder None."""
    ref_name = "period"
    if ref_name not in font:
        return None
    ref = [(p.x, p.y) for c in font[ref_name].contours for p in c.points]
    ru0, ru1, ry0, ry1 = _contour_box(ref, tan)
    for c in glyph.contours:
        if any(c is b for b in bars) or len(c.points) != 4:
            continue
        u0, u1, y0, y1 = _contour_box([(p.x, p.y) for p in c.points], tan)
        w, h = round(ru1 - ru0), ry1 - ry0
        nu0 = round((u0 + u1) / 2 - w / 2)
        top = y1
        corners = [(nu0, top - h), (nu0 + w, top - h), (nu0 + w, top), (nu0, top)]
        # Punktreihenfolge der Kontur beibehalten: jeden alten Punkt dem nächstgelegenen Eckpunkt zuordnen
        for p in c.points:
            uy = p.y
            ux = p.x - p.y * tan
            tx = nu0 if abs(ux - u0) < abs(ux - u1) else nu0 + w
            ty = top if abs(uy - y1) < abs(uy - y0) else top - h
            p.x, p.y = round(tx + ty * tan), round(ty)
        return nu0, nu0 + w, top - h, top
    return None


def widen_bars_to_dot(font, italic_angle=0.0):
    """Der Balken von ! und ¡ ist genauso breit wie der Punkt und sitzt mittig über ihm
    (vorher war der Punkt breiter als der Balken und lag um einige Einheiten daneben).

    Der Punkt bleibt, wie er ist. Der Balken besteht nach straighten_bars aus vier Geraden;
    seine linke und rechte Kante (entneigt gemessen) rücken auf die des Punkts. Gibt die
    Anzahl der geänderten Glyphen zurück."""
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    n = 0
    for g in font:
        if not BAR_DOT_GLYPHS.match(g.name):
            continue
        box, bars = _split_dot_bar(font, g, tan)
        if box is None:
            continue
        if not any(c.baseGlyph.startswith("period") for c in g.components):
            box = _conform_dot_contour(font, g, bars, tan) or box
        left, right = round(box[0]), round(box[1])
        for c in bars:
            pts = list(c.points)
            us = [(p.x - p.y * tan, p.y) for p in pts]
            cx = (max(u for u, _ in us) + min(u for u, _ in us)) / 2
            for p, (ux, uy) in zip(pts, us):
                nx = left if ux < cx else right
                p.x = round(nx + uy * tan)
            n += 1
    return n


def open_dot_gaps(font, ratio, italic_angle=0.0, top_ratio=None):
    """Mehr Platz zwischen Punkt und Strich bei i, j (und allem mit Punkt auf i/j), ï, ! ¡ ? ¿.

    Der Zuschlag ist ratio × Punktbreite, damit er in jedem Gewicht mitwächst (Black hat
    große Punkte und war am knappsten). Bei i/j steigt der Punkt (die Komponente rückt
    nach oben), bei ! und ? rückt die Strichkante zum Punkt hin zurück, die Grundlinie
    und die Oberkante (Versalhöhe) bleiben. Bei ¡ ¿ umgekehrt. Alle Rückungen laufen
    entlang der Neigung. Gibt die Anzahl der geänderten Glyphen zurück.

    top_ratio: Der Punkt über i/j reicht höchstens bis Oberlänge (Höhe von l) + top_ratio ×
    Punktgröße. Ist er höher, rückt er herunter (der Zuschlag kann dann auch null oder
    negativ werden), sonst stünde er in den schweren Gewichten zu weit über l, k, f."""
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    asc = None
    if top_ratio is not None and "l" in font:
        ls = [p.y for c in font["l"].contours for p in c.points]
        asc = max(ls) if ls else None
    n = 0
    for g in font:
        changed = False
        names = [c.baseGlyph for c in g.components]
        if any(DOTLESS_BASE.match(b) for b in names):
            for comp in g.components:
                if DOT_ACCENT.match(comp.baseGlyph) or DIERESIS_ON_I.match(comp.baseGlyph):
                    base = font[comp.baseGlyph]
                    us = [p.x - p.y * tan for c in base.contours for p in c.points]
                    ys = [p.y for c in base.contours for p in c.points]
                    if not us:
                        continue
                    size = max(ys) - min(ys)  # Punktgröße (Höhe eines Punkts, bei ï nicht die Paarbreite)
                    d = round(ratio * size)
                    t = list(comp.transformation)
                    if asc is not None:
                        top = max(ys) * t[3] + t[5]
                        d = min(d, round(asc + top_ratio * size - top))
                    t[4] = t[4] + d * tan
                    t[5] = t[5] + d
                    comp.transformation = tuple(t)
                    changed = True
        elif GAP_BAR_GLYPHS.match(g.name):
            box, bars = _split_dot_bar(font, g, tan)
            if box is None:
                continue
            d = round(ratio * (box[1] - box[0]))
            down = g.name.startswith(("exclamdown", "questiondown"))
            for c in bars:
                ys = [p.y for p in c.points]
                edge = max(ys) if down else min(ys)
                for p in c.points:
                    if p.y == edge:
                        s = -d if down else d
                        p.x = round(p.x + s * tan)
                        p.y = p.y + s
                changed = True
        if changed:
            n += 1
    return n
