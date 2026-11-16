"""Das Element-Glyph [Br]: eine Kachel wie im Periodensystem mit „Br".
Nur über dlig für die Folge [Br] erreichbar, ohne eigenen Codepoint."""
import math
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from .config import ELEMENT_GLYPH, ELEMENT_PAD
from .inter_import import stem_at


def _rect(pen, x0, y0, x1, y1, clockwise, shear):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if clockwise:
        pts.reverse()
    pts = [(round(x + y * shear), y) for x, y in pts]
    pen.moveTo(pts[0])
    for p in pts[1:]:
        pen.lineTo(p)
    pen.closePath()


def _place(font, pen, name, k, dx, dy):
    rec = DecomposingRecordingPen(font)
    font[name].draw(rec)
    rec.replay(TransformPen(pen, (k, 0, 0, k, dx, dy)))


def _upright_bounds(font, name, shear):
    """Konturgrenzen in x ohne Neigung (bei Kursiven sonst zu breit durch den Überhang)."""
    rec = DecomposingRecordingPen(font)
    font[name].draw(rec)
    bp = BoundsPen(font)
    rec.replay(TransformPen(bp, (1, 0, -shear, 1, 0, 0)))
    return bp.bounds[0], bp.bounds[2]


def build_element(font, italic_angle=0.0):
    shear = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    cap = font.info.capHeight
    stem = stem_at(font, "I", cap / 2) or 80
    frame = round(10 + stem * 0.42)
    # „Br" in voller Größe (wie die folgenden Buchstaben), die Kachel wächst mit:
    # Innenabstand links/rechts fest, oben/unten ergibt sich aus dem Quadrat.
    bx_min, _ = _upright_bounds(font, "B", shear)
    _, rx_max = _upright_bounds(font, "r", shear)
    wb = font["B"].width
    ink = wb - bx_min + rx_max  # Breite von „Br" von Kontur zu Kontur
    pad = round(cap * ELEMENT_PAD)
    side = round(ink + 2 * frame + 2 * pad)
    y0 = -round((side - cap) / 2)
    y1 = y0 + side
    lsb = 50
    x0, x1 = lsb, lsb + side

    if ELEMENT_GLYPH in font:
        del font[ELEMENT_GLYPH]
    g = font.newGlyph(ELEMENT_GLYPH)
    g.width = side + 2 * lsb
    g.unicodes = []
    pen = g.getPen()
    _rect(pen, x0, y0, x1, y1, False, shear)
    _rect(pen, x0 + frame, y0 + frame, x1 - frame, y1 - frame, True, shear)

    # „Br" mittig nach der tatsächlichen Kontur, auf der Grundlinie wie der Text daneben.
    bx = x0 + frame + pad - bx_min
    by = 0
    _place(font, pen, "B", 1, bx, by)
    _place(font, pen, "r", 1, bx + wb, by)

    order = list(font.glyphOrder)
    if ELEMENT_GLYPH not in order:
        order.append(ELEMENT_GLYPH)
        font.glyphOrder = order
    return g


FEATURE = f"""
feature dlig {{
  # [Br]om: Element-Kachel
  sub bracketleft B r bracketright by {ELEMENT_GLYPH};
}} dlig;
"""
