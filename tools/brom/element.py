"""Das Element-Glyph [Br]: eine Kachel wie im Periodensystem mit „Br".
Nur über dlig für die Folge [Br] erreichbar, ohne eigenen Codepoint."""
import math
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from .config import ELEMENT_GLYPH
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


def build_element(font, italic_angle=0.0):
    shear = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    cap = font.info.capHeight
    stem = stem_at(font, "I", cap / 2) or 80
    side = round(cap * 1.24)
    y0 = -round((side - cap) / 2)
    y1 = y0 + side
    lsb = 50
    x0, x1 = lsb, lsb + side
    frame = round(10 + stem * 0.42)

    if ELEMENT_GLYPH in font:
        del font[ELEMENT_GLYPH]
    g = font.newGlyph(ELEMENT_GLYPH)
    g.width = side + 2 * lsb
    g.unicodes = []
    pen = g.getPen()
    _rect(pen, x0, y0, x1, y1, False, shear)
    _rect(pen, x0 + frame, y0 + frame, x1 - frame, y1 - frame, True, shear)

    # „Br" optisch mittig (nach der tatsächlichen Kontur, nicht nach den Dickten).
    bb, rb = font["B"].getBounds(font), font["r"].getBounds(font)
    content = font["B"].width - bb.xMin + rb.xMax  # Breite von „Br" ungeskaliert
    room = side - 2 * frame - 2 * round(side * 0.11)  # Innenraum mit Mindestabstand
    k = min(0.60, room / content)
    wb = font["B"].width * k
    left = bb.xMin * k
    right = wb + rb.xMax * k
    bx = x0 + (side - (right - left)) / 2 - left
    by = y0 + side / 2 - cap * k / 2
    _place(font, pen, "B", k, bx + by * shear, by)
    _place(font, pen, "r", k, bx + wb + by * shear, by)

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
