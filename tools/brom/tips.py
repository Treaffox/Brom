"""Echte Spitzen statt abgeschnittener Spitzen bei « » ‹ › < > ≤ ≥ ^ und Pfeilen.

Geist schneidet diese Spitzen senkrecht bzw. waagrecht ab. Erkannt wird ein
kurzes gerades Segment zwischen zwei langen geraden Schenkeln, die sich jenseits
des Segments schneiden. Die zwei Punkte des Segments werden durch den Schnittpunkt
der Schenkel ersetzt (ein Punkt weniger). Die Auswahl wird im Regular-Master
getroffen und in allen Mastern gleich angewendet, damit die Master kompatibel bleiben.
"""
import math
import re

TIP_GLYPHS = re.compile(
    r"^(guillemet(left|right)|guilsingl(left|right)|less|greater|lessequal|greaterequal|asciicircum"
    r"|.*[Aa]rrow.*|arrowhead.*|uni219[0-9A-F]|uni21[A-F][0-9A-F]|uni27[F][0-9A-F]|uni2B[0-9A-F]{2})(\..+)?$")


def _intersect(p1, p2, p3, p4):
    """Schnittpunkt der Geraden p1→p2 und p3→p4 (oder None)."""
    d1 = (p2[0] - p1[0], p2[1] - p1[1])
    d2 = (p4[0] - p3[0], p4[1] - p3[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-9:
        return None
    t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den
    return (p1[0] + d1[0] * t, p1[1] + d1[1] * t), t


def _tip_at(pts, i, stem):
    """Prüft, ob Punkte i und i+1 eine abgeschnittene Spitze bilden. Gibt den Schnittpunkt zurück."""
    n = len(pts)
    a, b, c, d = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
    if any(p.type not in ("line",) for p in (a, b, c, d)):
        return None
    A, B, Cc, D = (a.x, a.y), (b.x, b.y), (c.x, c.y), (d.x, d.y)
    flat = math.dist(B, Cc)
    if flat <= 0 or flat > 1.4 * stem:
        return None
    if math.dist(A, B) < 1.5 * flat or math.dist(D, Cc) < 1.5 * flat:
        return None
    r = _intersect(A, B, D, Cc)
    if r is None:
        return None
    X, t = r
    # Schenkel laufen zusammen: Schnittpunkt jenseits von B (äußere Spitze, t > 1)
    # oder knapp davor (innerer Winkel, Schenkel kreuzen sich vor der Abflachung).
    if t <= 0.5:
        return None
    # Spitzer Winkel zwischen den Schenkeln (< 120°)
    v1 = (A[0] - X[0], A[1] - X[1])
    v2 = (D[0] - X[0], D[1] - X[1])
    cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (math.hypot(*v1) * math.hypot(*v2))
    if math.degrees(math.acos(max(-1, min(1, cosang)))) > 120:
        return None
    # Verlängerung darf nicht absurd lang werden
    if math.dist(X, ((B[0] + Cc[0]) / 2, (B[1] + Cc[1]) / 2)) > 1.2 * flat + 0.5 * stem:
        return None
    return X


def find_tips(font, stem):
    """{Glyphname: [(Konturindex, Punktindex) …]} der abgeschnittenen Spitzen."""
    found = {}
    for g in font:
        if not TIP_GLYPHS.match(g.name):
            continue
        for ci, c in enumerate(g.contours):
            pts = c.points
            for i in range(len(pts)):
                if _tip_at(pts, i, stem) is not None:
                    found.setdefault(g.name, []).append((ci, i))
    return found


def sharpen_tips(font, selection, stem):
    """Ersetzt die ausgewählten abgeschnittenen Spitzen durch echte Spitzen und
    staucht die Kontur danach entlang der Spitzenrichtung, bis die Spitze wieder
    genau so weit reicht wie vorher. Abmessungen, Dickte und Laufweite bleiben,
    gespiegelte Komposita (< ‹ «) brauchen keine Anpassung.
    Gibt die Anzahl der geänderten Spitzen zurück."""
    done = 0
    for name, items in selection.items():
        if name not in font:
            continue
        g = font[name]
        by_contour = {}
        for ci, i in items:
            by_contour.setdefault(ci, []).append(i)
        for ci, idxs in by_contour.items():
            c = g.contours[ci]
            pts = c.points
            outer = None  # (Mitte der Abflachung, Spitze)
            for i in sorted(idxs, reverse=True):
                n = len(pts)
                a, b, cc, d = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
                r = _intersect((a.x, a.y), (b.x, b.y), (d.x, d.y), (cc.x, cc.y))
                if r is None:
                    continue
                X, t = r
                M = ((b.x + cc.x) / 2, (b.y + cc.y) / 2)
                if t > 1 and outer is None:
                    outer = (M, X)
                b.x, b.y = X
                del pts[(i + 1) % n]
                done += 1
            if outer:
                M, X = outer
                L = math.dist(M, X)
                if L > 0.5:
                    u = ((X[0] - M[0]) / L, (X[1] - M[1]) / L)
                    proj = [(p.x * u[0] + p.y * u[1]) for p in pts]
                    lo, hi = min(proj), X[0] * u[0] + X[1] * u[1]
                    k = (hi - L - lo) / (hi - lo) if hi > lo else 1.0
                    for p, q in zip(pts, proj):
                        dq = (q - lo) * (k - 1)
                        p.x, p.y = p.x + dq * u[0], p.y + dq * u[1]
            for p in pts:
                p.x, p.y = round(p.x), round(p.y)
    return done
