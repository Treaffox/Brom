"""Übernimmt Glyphen aus Inter, die Geist nicht hat, und gleicht sie an Brom an.

Ablauf je Stil (aufrecht/kursiv):
  1. Auswahl einmal auf Basis der Regular-Master: alle nicht-PUA-Codepoints von
     Inter, die Geist fehlen, plus die Komponenten, die sie brauchen.
  2. Je Brom-Master: Inter an der Stelle interpolieren, deren Stammstärke dem
     Brom-Master entspricht, auf Geists x-Höhe skalieren, bei Kursiven auf Geists
     Neigung nachneigen und einfügen.
  3. Diakritika in Komposita, die auf Geist-Glyphen aufbauen, über Anker neu setzen.
  4. Griechische/kyrillische Doppelgänger (reine Komponente eines lateinischen
     Glyphs) in dieselben Kerning-Gruppen aufnehmen.
"""
import math
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.basePen import BasePen
from .ufo_ops import compatible, lerp_glyph_into


def _is_pua(u):
    """PUA und CJK/Kana: keine standardisierte Bedeutung bzw. nur Platzhalter."""
    return 0xE000 <= u <= 0xF8FF or u >= 0xF0000 or 0x2E80 <= u <= 0x9FFF


class _Flatten(BasePen):
    """Sammelt Liniensegmente (Kurven fein abgetastet)."""
    def __init__(self, gs):
        super().__init__(gs)
        self.segs = []
        self.cur = None
        self.start = None
    def _moveTo(self, p):
        self.cur = self.start = p
    def _lineTo(self, p):
        self.segs.append((self.cur, p)); self.cur = p
    def _curveToOne(self, a, b, c):
        p0 = self.cur
        prev = p0
        for i in range(1, 17):
            t = i / 16; mt = 1 - t
            x = mt**3*p0[0] + 3*mt*mt*t*a[0] + 3*mt*t*t*b[0] + t**3*c[0]
            y = mt**3*p0[1] + 3*mt*mt*t*a[1] + 3*mt*t*t*b[1] + t**3*c[1]
            self.segs.append((prev, (x, y))); prev = (x, y)
        self.cur = c
    def _closePath(self):
        if self.cur != self.start:
            self.segs.append((self.cur, self.start))


def stem_at(font, name, y):
    """Breite des ersten Strichs eines Glyphs auf Höhe y (horizontaler Schnitt)."""
    rec = DecomposingRecordingPen(font)
    font[name].draw(rec)
    fl = _Flatten(font)
    rec.replay(fl)
    xs = []
    for (x0, y0), (x1, y1) in fl.segs:
        if (y0 - y) * (y1 - y) < 0:
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    xs.sort()
    return xs[1] - xs[0] if len(xs) >= 2 else None


def select(geist_reg, inter_masters):
    """Bestimmt, was übernommen wird. Gibt (imports, rename, assign, dropped) zurück."""
    ireg = inter_masters["Regular"]
    geist_cps = {u for g in geist_reg for u in g.unicodes}
    wanted = {}
    for g in ireg:
        cps = [u for u in g.unicodes if u not in geist_cps and not _is_pua(u)]
        if cps:
            wanted[g.name] = cps
    rename, assign = {}, {}
    for n, cps in wanted.items():
        if n in geist_reg:
            if not geist_reg[n].unicodes:
                assign[n] = cps  # Geist hat die Form schon, nur unkodiert
            else:
                rename[n] = n + ".ix"
    imports = {n for n in wanted if n not in assign}
    # Komponenten-Hülle
    queue = list(imports)
    while queue:
        n = queue.pop()
        for c in ireg[n].components:
            b = c.baseGlyph
            if b in imports or b in rename:
                continue
            if b in geist_reg:
                continue  # Geist-Form verwenden
            imports.add(b)
            queue.append(b)
    # Kompatibilität über alle drei Inter-Master
    dropped = set()
    changed = True
    while changed:
        changed = False
        for n in sorted(imports - dropped):
            gs = [inter_masters[m][n] if n in inter_masters[m] else None for m in ("Thin", "Regular", "Black")]
            ok = all(g is not None for g in gs) and compatible(gs[0], gs[1]) and compatible(gs[1], gs[2])
            if ok:
                for c in gs[1].components:
                    if c.baseGlyph in dropped:
                        ok = False
            if not ok:
                dropped.add(n)
                changed = True
    imports -= dropped
    return imports, rename, assign, dropped


def _transform_glyph(g, s, shear):
    """Skaliert uniform um s und neigt um shear (x += y*shear)."""
    for c in g.contours:
        for p in c.points:
            x, y = p.x * s, p.y * s
            p.x, p.y = round(x + y * shear), round(y)
    for a in g.anchors:
        x, y = a.x * s, a.y * s
        a.x, a.y = round(x + y * shear), round(y)
    for k in g.components:
        t = list(k.transformation)
        x, y = t[4] * s, t[5] * s
        t[4], t[5] = round(x + y * shear), round(y)
        k.transformation = type(k.transformation)(*t)
    g.width = round(g.width * s)


def _inter_location(geist_font, inter_masters, measure_y_geist, measure_y_inter, s):
    """Welche Inter-Interpolation hat dieselbe Stammstärke wie der Geist-Master?"""
    target = stem_at(geist_font, "I", measure_y_geist)
    st = {m: stem_at(inter_masters[m], "I", measure_y_inter) * s for m in ("Thin", "Regular", "Black")}
    if target <= st["Regular"]:
        return "Thin", "Regular", (target - st["Thin"]) / (st["Regular"] - st["Thin"]), target, st
    return "Regular", "Black", (target - st["Regular"]) / (st["Black"] - st["Regular"]), target, st


def import_into(geist_font, inter_masters, selection, geist_italic_angle, inter_italic_angle):
    """Fügt die Auswahl in einen Brom-Master ein. Gibt ein Protokoll zurück."""
    imports, rename, assign, _ = selection
    ireg = inter_masters["Regular"]
    s = geist_font.info.xHeight / ireg.info.xHeight
    shear = 0.0
    if geist_italic_angle or inter_italic_angle:
        shear = math.tan(math.radians(-geist_italic_angle)) - math.tan(math.radians(-inter_italic_angle))
    ma, mb, t, target, stems = _inter_location(
        geist_font, inter_masters, geist_font.info.capHeight / 2, ireg.info.capHeight / 2, s)
    A, B = inter_masters[ma], inter_masters[mb]
    newname = lambda n: rename.get(n, n)
    layer = geist_font.layers.defaultLayer
    order = list(geist_font.glyphOrder)
    ps_names = geist_font.lib.setdefault("public.postscriptNames", {})
    inter_ps = ireg.lib.get("public.postscriptNames", {})

    for n, cps in assign.items():
        geist_font[n].unicodes = list(geist_font[n].unicodes) + cps
    taken = {u for g in geist_font for u in g.unicodes}

    for n in sorted(imports):
        ga, gb = A[n], B[n]
        g = ga.copy()
        lerp_glyph_into(g, ga, gb, t)
        _transform_glyph(g, s, shear)
        for k in g.components:
            k.baseGlyph = newname(k.baseGlyph)
        g.unicodes = [u for u in ireg[n].unicodes if u not in taken and not _is_pua(u)]
        nn = newname(n)
        layer.insertGlyph(g, name=nn, overwrite=False, copy=False)
        order.append(nn)
        if n in inter_ps:
            ps_names[nn] = inter_ps[n]
    geist_font.glyphOrder = order

    imported = {newname(n) for n in imports}
    _reposition_marks(geist_font, imported, ireg, rename, s)
    _extend_kern_groups(geist_font, imported)
    imp_map = {newname(n): n for n in sorted(imports)}  # feste Reihenfolge (reproduzierbarer Build)
    kerned = _kern_by_analogy(geist_font, imp_map, ireg)
    kerned["pairs"] = _import_kerning(geist_font, imp_map, A, B, t, s)
    return {"pair": (ma, mb), "t": round(t, 3), "stem": round(target, 1), "scale": round(s, 4),
            "shear": round(shear, 4), "count": len(imports), "assigned": len(assign),
            "kern_analogy": kerned}


def add_stack_anchors(font, gap=48):
    """Gibt Akzenten mit '_top' ohne 'top' einen Stapelanker, sodass ein zweiter
    Akzent mit `gap` Einheiten Abstand darüber sitzt. Gibt die Anzahl zurück."""
    n = 0
    for g in font:
        names = {a.name: a for a in g.anchors}
        if "_top" not in names or "top" in names or g.width != 0 or not g.contours:
            continue
        b = g.getBounds(font)
        if b is None:
            continue
        rise = b.yMin - names["_top"].y
        g.appendAnchor({"name": "top", "x": names["_top"].x, "y": round(b.yMax + gap - rise)})
        n += 1
    return n


def _apply(t, x, y):
    a, b, c, d, e, f = t
    return (a * x + c * y + e, b * x + d * y + f)


def _anchors(font, name, _depth=0):
    """Anker eines Glyphs. Bei Komposita aus den Komponenten aufgelöst, damit ein
    darüberliegender Akzent den Stapelanker des obersten Akzents findet."""
    g = font[name]
    own = {a.name: (a.x, a.y) for a in g.anchors}
    if not g.components or g.contours or _depth > 6:
        return own
    first = g.components[0]
    ft = tuple(first.transformation)
    acc = {k: _apply(ft, x, y) for k, (x, y) in _anchors(font, first.baseGlyph, _depth + 1).items()}
    for c in g.components[1:]:
        ct = tuple(c.transformation)
        for k, (x, y) in _anchors(font, c.baseGlyph, _depth + 1).items():
            if not k.startswith("_"):
                acc[k] = _apply(ct, x, y)
    for k, v in own.items():
        acc.setdefault(k, v)
    return acc


def _reposition_marks(font, imported, inter_reg, rename, s):
    inv = {v: k for k, v in rename.items()}
    # Basis vor Komposita bearbeiten, damit verschachtelte Akzente stimmen.
    def depth(n, d=0):
        g = font[n]
        return d if not g.components or d > 6 else max(depth(c.baseGlyph, d + 1) for c in g.components)
    memo = {}

    def uses_geist(n):
        """Enthält das Glyph (rekursiv) eine Komponente aus Geist?"""
        if n not in memo:
            memo[n] = False
            memo[n] = any(c.baseGlyph not in imported or uses_geist(c.baseGlyph)
                          for c in font[n].components)
        return memo[n]

    for name in sorted(imported, key=depth):
        g = font[name]
        comps = list(g.components)
        if not comps or not uses_geist(name):
            continue  # reine Inter-Komposita behalten Inters Platzierung
        base = comps[0]
        bt = tuple(base.transformation)
        acc = {k: _apply(bt, x, y) for k, (x, y) in _anchors(font, base.baseGlyph).items()}
        for c in comps[1:]:
            ct = list(c.transformation)
            mk = _anchors(font, c.baseGlyph)
            for an, (mx, my) in mk.items():
                if not an.startswith("_"):
                    continue
                target = acc.get(an[1:])
                if target is None:
                    continue
                lx, ly = _apply((ct[0], ct[1], ct[2], ct[3], 0, 0), mx, my)
                ct[4], ct[5] = round(target[0] - lx), round(target[1] - ly)
                c.transformation = type(c.transformation)(*ct)
                for k, (x, y) in mk.items():
                    if not k.startswith("_"):
                        acc[k] = _apply(tuple(ct), x, y)
                break
        if base.baseGlyph not in imported:
            # Breite vom Geist-Basisglyph übernehmen, wenn das Inter-Original
            # genau so breit war wie seine Basis.
            src = inter_reg[inv.get(name, name)]
            ib = src.components[0].baseGlyph if src.components else None
            if ib in inter_reg and bt[4] == 0 and abs(src.width - inter_reg[ib].width) <= 2:
                g.width = font[base.baseGlyph].width
        for a in g.anchors:
            if a.name in acc:
                a.x, a.y = round(acc[a.name][0]), round(acc[a.name][1])


def _extend_kern_groups(font, imported):
    """Alpha = [A] → Alpha kernt wie A."""
    member_of = {}
    for gname, members in font.groups.items():
        if gname.startswith("public.kern"):
            for m in members:
                member_of.setdefault(m, []).append(gname)
    for name in sorted(imported):  # feste Reihenfolge der Gruppenmitglieder
        g = font[name]
        if g.contours or len(g.components) != 1:
            continue
        b = g.components[0].baseGlyph
        if b in imported or tuple(g.components[0].transformation) != (1, 0, 0, 1, 0, 0):
            continue
        for gname in member_of.get(b, []):
            if name not in font.groups[gname]:
                font.groups[gname] = list(font.groups[gname]) + [name]


def _kern_by_analogy(font, imported, inter_reg):
    """Übernimmt Inters Kerning-Gruppierung für importierte Zeichen: Steht ein
    Zeichen bei Inter in derselben Gruppe wie ein Geist-Glyph (Ο mit O, Г mit T),
    kommt es in Brom in die Gruppe dieses Geist-Glyphs. Je Seite (kern1/kern2)
    höchstens eine Gruppe pro Glyph. Gibt {Seite: Anzahl} zurück."""
    result = {}
    for side in ("public.kern1.", "public.kern2."):
        brom_of = {}
        for gname, members in font.groups.items():
            if gname.startswith(side):
                for m in members:
                    brom_of[m] = gname
        n = 0
        for gname, members in inter_reg.groups.items():
            if not gname.startswith(side):
                continue
            # Vorbild: erstes Geist-Glyph der Inter-Gruppe, das in Brom gruppiert ist
            model = next((m for m in members if m not in imported.values() and m in brom_of
                          and m in font and m not in imported), None)
            if model is None:
                continue
            target = brom_of[model]
            for new, orig in imported.items():
                if orig in members and new not in brom_of:
                    font.groups[target] = list(font.groups[target]) + [new]
                    brom_of[new] = target
                    n += 1
        result[side.split(".")[1]] = n
    return result


def _import_kerning(font, imported, A, B, t, s):
    """Übernimmt Inters Kerning für Paare, an denen nur über Inter abgedeckte
    Zeichen beteiligt sind (ΛΑ, ΤΩ …). Inter-Gruppen ohne Geist-Vorbild werden
    als eigene Gruppen 'ix.*' angelegt. Werte: Inter an derselben Stelle wie die
    Glyphen interpoliert und auf Brom skaliert. Bestehende Paare bleiben."""
    inv = {v: k for k, v in imported.items()}

    def greek_cyr(name):
        return name in font and any(0x370 <= u <= 0x52F or 0x1F00 <= u <= 0x1FFF for u in font[name].unicodes)

    group_map = {}  # Inter-Gruppe -> Brom-Gruppe
    new_groups = set()
    analog = {}  # Seite -> Glyphen, die schon wie ein Geist-Vorbild kernen
    for side in ("public.kern1.", "public.kern2."):
        brom_of = {}
        for gname, members in font.groups.items():
            if gname.startswith(side):
                for m in members:
                    brom_of[m] = gname
        analog[side] = set(brom_of)
        for gname, members in A.groups.items():
            if not gname.startswith(side):
                continue
            targets = {brom_of[inv.get(m, m)] for m in members if inv.get(m, m) in brom_of}
            # Übernommene Zeichen, dazu griechische/kyrillische Geist-Glyphen ohne Gruppe (Ω, µ …)
            imp_members = [inv.get(m, m) for m in members
                           if (m in inv or greek_cyr(m)) and inv.get(m, m) not in brom_of]
            if len(targets) == 1:
                group_map[gname] = targets.pop()
            elif not targets and imp_members:
                ng = side + "ix." + gname[len(side):]
                font.groups[ng] = imp_members
                for m in imp_members:
                    brom_of[m] = ng
                group_map[gname] = ng
                new_groups.add(ng)

    def side_of(x):
        if x.startswith("public.kern"):
            return group_map.get(x)
        if x in inv:
            return inv[x]
        return x if x in font else None

    def own(x, side):
        """Gehört dieser Teil des Paares Inter (eigene Gruppe oder Zeichen ohne Geist-Vorbild)?"""
        if x in new_groups:
            return True
        return (x in imported or greek_cyr(x)) and x not in analog[side]

    # Mehrere Inter-Paare können auf dasselbe Brom-Paar fallen. Dann gilt das
    # spezifischste (Glyph vor Gruppe, wie bei der OpenType-Auswertung), bei
    # Gleichstand das alphabetisch erste. So ist der Build reproduzierbar.
    def groups_in(pair):
        return sum(x.startswith("public.kern") for x in pair)

    added = 0
    decided = set()  # Brom-Paare, über die schon ein Inter-Paar entschieden hat (auch mit Wert 0)
    for pair in sorted(set(A.kerning) | set(B.kerning), key=lambda p: (groups_in(p), p)):
        l, r = side_of(pair[0]), side_of(pair[1])
        if l is None or r is None or not (own(l, "public.kern1.") or own(r, "public.kern2.")):
            continue
        if (l, r) in font.kerning or (l, r) in decided:
            continue
        decided.add((l, r))
        v = A.kerning.get(pair, 0) + (B.kerning.get(pair, 0) - A.kerning.get(pair, 0)) * t
        v = round(v * s)
        if v:
            font.kerning[(l, r)] = v
            added += 1
    return added
