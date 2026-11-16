#!/usr/bin/env python3
"""Erzeugt die Brom-Quellen (UFO-Master + Designspace) aus Geist und Inter.

  prepare.py [--style Roman|Italic] [--quick]

Ergebnis: sources/<Stil>/Brom-<Master>.ufo und Brom[-Italic].designspace
"""
import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fontTools.designspaceLib import (AxisDescriptor, AxisLabelDescriptor, DesignSpaceDocument,
                                      DiscreteAxisDescriptor, InstanceDescriptor, SourceDescriptor,
                                      VariableFontDescriptor)
from glyphsLib.glyphdata import get_glyph

from brom import config as C
from brom.ufo_ops import load_master, lerp_font, track_font
from brom.squircle import squircle_glyph
from brom.inter_import import select, import_into, add_stack_anchors
from brom.element import build_element, FEATURE as ELEMENT_FEATURE
from brom.dots import find_dots, square_dots
from brom.tips import find_tips, sharpen_tips
from brom.joins import find_steps, smooth_steps
from brom.inter_import import stem_at

INFO_CLEAR = [
    "openTypeNamePreferredFamilyName", "openTypeNamePreferredSubfamilyName",
    "openTypeNameCompatibleFullName", "openTypeNameWWSFamilyName", "openTypeNameWWSSubfamilyName",
    "postscriptFontName", "postscriptFullName", "styleMapFamilyName", "styleMapStyleName",
    "openTypeNameUniqueID", "openTypeNameSampleText", "trademark", "woffMetadataUniqueID",
    "woffMetadataVendor", "woffMetadataCredits", "woffMetadataDescription", "woffMetadataLicense",
    "woffMetadataCopyright", "woffMetadataTrademark", "woffMetadataLicensee", "macintoshFONDName",
    "postscriptUniqueID", "openTypeHeadCreated",
]


EXPORT_KEY = "com.schriftgestaltung.Glyphs.Export"


def drop_unexported(font):
    """Löscht in Geist als nicht exportiert markierte Glyphen (unfertiges Ezh,
    CJK-Platzhalter …), sofern sie nirgends als Komponente dienen. Ihre
    Codepoints übernimmt dann Inter."""
    used = {c.baseGlyph for g in font for c in g.components}
    drop = {g.name for g in font if g.lib.get(EXPORT_KEY) is False and g.name not in used}
    for n in drop:
        del font[n]
    font.glyphOrder = [n for n in font.glyphOrder if n not in drop]
    for g, members in list(font.groups.items()):
        font.groups[g] = [m for m in members if m not in drop]
    for pair in list(font.kerning):
        if any(p in drop for p in pair):
            del font.kerning[pair]
    return sorted(drop)


def set_skip_export(font):
    skip = sorted(g.name for g in font if g.lib.get(EXPORT_KEY) is False)
    font.lib["public.skipExportGlyphs"] = skip
    return skip


def clean_geist(font):
    """Entfernt fremde Marken und Vercel-spezifische Features."""
    drop_unexported(font)
    for n in C.DROP_GLYPHS:
        if n in font:
            del font[n]
    font.glyphOrder = [n for n in font.glyphOrder if n not in C.DROP_GLYPHS]
    for g, members in list(font.groups.items()):
        font.groups[g] = [m for m in members if m not in C.DROP_GLYPHS]
    for pair in list(font.kerning):
        if any(p in C.DROP_GLYPHS for p in pair):
            del font.kerning[pair]
    ps = font.lib.get("public.postscriptNames", {})
    for n in C.DROP_GLYPHS:
        ps.pop(n, None)
    fea = font.features.text
    for tag in C.DROP_FEATURES:
        fea = re.sub(rf"feature {tag} \{{.*?\}} {tag};\n?", "", fea, flags=re.S)
        fea = re.sub(rf"^\s*feature {tag};\n", "", fea, flags=re.M)
    for n in C.DROP_GLYPHS:
        fea = re.sub(rf"(?<![\w.]){re.escape(n)}(?![\w.])", "", fea)
    # Griechisch und Kyrillisch ausdrücklich anmelden, damit Kerning und
    # Akzentpositionierung dort nicht vom DFLT-Fallback der Anwendung abhängen.
    if "languagesystem grek" not in fea:
        fea = fea.replace("languagesystem DFLT dflt;",
                          "languagesystem DFLT dflt;\nlanguagesystem grek dflt;\nlanguagesystem cyrl dflt;", 1)
    font.features.text = fea


def fix_degenerate(font):
    """Rundung kann zwei aufeinanderfolgende On-Curve-Punkte zusammenlegen. Ein
    Nullsegment fällt beim Kompilieren weg, und der Master wird inkompatibel.
    Solche Punkte werden um eine Einheit versetzt."""
    fixed = 0
    for g in font:
        for c in g.contours:
            pts = c.points
            n = len(pts)
            for i, p in enumerate(pts):
                if p.type in ("line", "curve", "qcurve") and pts[i - 1].type is not None:
                    q = pts[i - 1]
                    if (p.x, p.y) == (q.x, q.y) and n > 2:
                        nxt = pts[(i + 1) % n]
                        dx = nxt.x - p.x
                        p.x += 1 if dx >= 0 else -1
                        fixed += 1
    return fixed


def set_categories(font):
    cats = {}
    for g in font:
        if g.width == 0 and any(a.name.startswith("_") for a in g.anchors):
            cats[g.name] = "mark"
            continue
        d = get_glyph(g.name)
        if d.category == "Mark" and d.subCategory == "Nonspacing":
            cats[g.name] = "mark"
        elif d.subCategory == "Ligature" and "_" in g.name.split(".")[0]:
            cats[g.name] = "ligature"
        else:
            cats[g.name] = "base"
    font.lib["public.openTypeCategories"] = cats


def set_info(font, master, style):
    info = font.info
    for attr in INFO_CLEAR:
        setattr(info, attr, None)
    info.openTypeNameRecords = []
    info.familyName = C.FAMILY
    suffix = C.STYLES[style]["suffix"]
    if master == "Regular" and suffix:
        info.styleName = suffix
    else:
        info.styleName = (master + " " + suffix).strip()
    info.versionMajor = C.VERSION_MAJOR
    info.versionMinor = C.VERSION_MINOR
    info.openTypeNameVersion = f"Version {C.VERSION_MAJOR}.{C.VERSION_MINOR:03d}; Brom {C.VERSION}"
    info.copyright = C.COPYRIGHT
    info.openTypeNameDesigner = C.DESIGNER
    info.openTypeNameDesignerURL = C.URL
    info.openTypeNameManufacturer = "TRFX"
    info.openTypeNameManufacturerURL = C.URL
    info.openTypeNameLicense = C.LICENSE_DESC
    info.openTypeNameLicenseURL = C.LICENSE_URL
    info.openTypeNameDescription = C.DESCRIPTION
    info.openTypeOS2VendorID = C.VENDOR_ID
    info.openTypeOS2WeightClass = C.MASTER_WGHT[master]
    info.italicAngle = C.STYLES[style]["italic_angle"] or 0
    info.postscriptSlantAngle = info.italicAngle
    for k in [k for k in font.lib if k.startswith("com.schriftgestaltung.customParameter.GSFont")]:
        del font.lib[k]


def build_designspace(style, paths):
    st = C.STYLES[style]
    italic = bool(st["suffix"])
    doc = DesignSpaceDocument()
    doc.formatVersion = "5.0"
    doc.elidedFallbackName = "Regular"
    wght = AxisDescriptor(tag="wght", name="Weight", minimum=100, default=400, maximum=900)
    wght.axisLabels = [AxisLabelDescriptor(name=n, userValue=v, elidable=(v == 400),
                                           linkedUserValue=700 if v == 400 else None)
                       for v, n in C.WEIGHTS]
    ital = DiscreteAxisDescriptor(tag="ital", name="Italic", values=[1 if italic else 0],
                                  default=1 if italic else 0)
    ital.axisLabels = [AxisLabelDescriptor(name="Italic", userValue=1)] if italic else \
        [AxisLabelDescriptor(name="Roman", userValue=0, elidable=True, linkedUserValue=1)]
    doc.axes = [wght, ital]
    for master, path in paths.items():
        s = SourceDescriptor(filename=path.name, familyName=C.FAMILY,
                             styleName=(master + (" " + st["suffix"] if st["suffix"] else "")).strip(),
                             location={"Weight": C.MASTER_WGHT[master], "Italic": 1 if italic else 0})
        if master == "Regular":
            s.copyLib = s.copyInfo = s.copyGroups = s.copyFeatures = True
        doc.addSource(s)
    for v, n in C.WEIGHTS:
        if italic:
            style_name = "Italic" if n == "Regular" else f"{n} Italic"
            ps = f"{C.PS_FAMILY}-{'Italic' if n == 'Regular' else n + 'Italic'}"
        else:
            style_name, ps = n, f"{C.PS_FAMILY}-{n}"
        if n in ("Regular", "Bold"):
            smf = C.FAMILY
            sms = ("bold " if n == "Bold" else "") + ("italic" if italic else "regular")
            sms = sms.replace("bold regular", "bold")
        else:
            smf, sms = f"{C.FAMILY} {n}", ("italic" if italic else "regular")
        inst = InstanceDescriptor(familyName=C.FAMILY, styleName=style_name, postScriptFontName=ps,
                                  styleMapFamilyName=smf, styleMapStyleName=sms,
                                  filename=f"instances/{ps}.ufo",
                                  location={"Weight": v, "Italic": 1 if italic else 0})
        doc.addInstance(inst)
    vf_name = f"{C.FILE_STEM}{'-Italic' if italic else ''}[wght]"
    doc.addVariableFont(VariableFontDescriptor(name=vf_name, filename=vf_name, axisSubsets=[]))
    from fontTools.designspaceLib import RangeAxisSubsetDescriptor
    doc.variableFonts[0].axisSubsets = [RangeAxisSubsetDescriptor(name="Weight")]
    return doc


def prepare_style(style, log):
    st = C.STYLES[style]
    t0 = time.time()
    gpath = {m: C.GEIST_UFO / p for m, p in st["geist"].items()}
    ipath = {m: C.INTER_UFO / p for m, p in st["inter"].items()}
    masters = {
        "Thin": load_master(gpath["Thin"]),
        "Regular": load_master(gpath["Regular"]),
    }
    black, bad = lerp_font(load_master(gpath["Regular"]), load_master(gpath["Black"]), C.GEIST_BLACK_T)
    if bad:
        log[f"{style}.black_incompatible"] = bad
        src = load_master(gpath["Black"])
        for n in bad:
            if n in src:
                black.layers.defaultLayer.insertGlyph(src[n], name=n, overwrite=True)
    masters["Black"] = black
    for f in masters.values():
        for layer in [l for l in f.layers if l.name.startswith("{")]:
            del f.layers[layer.name]  # Brace-Zwischenmaster passen nicht mehr zum leichteren Black
        clean_geist(f)
        log[f"{style}.stack_anchors_added"] = add_stack_anchors(f)

    inter ={m: load_master(p) for m, p in ipath.items()}
    selection = select(masters["Regular"], inter)
    log[f"{style}.import"] = {"glyphs": len(selection[0]), "renamed": len(selection[1]),
                              "assigned": len(selection[2]), "dropped": sorted(selection[3])}
    inter_angle = inter["Regular"].info.italicAngle or 0.0

    out_dir = C.SOURCES / style
    if out_dir.is_dir() and out_dir.parent == C.SOURCES:
        shutil.rmtree(out_dir)  # nur erzeugte Quellen, werden komplett neu geschrieben
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    # Quadratische Punkte: Auswahl einmal im Regular-Master, Anwendung in allen.
    reg = masters["Regular"]
    reg_stem = stem_at(reg, "I", reg.info.capHeight / 2) or 86
    dot_sel = find_dots(reg, reg_stem, italic_angle=st["italic_angle"])
    log[f"{style}.dots"] = dot_sel
    # Echte Spitzen bei « » ‹ › < > ≤ ≥ ^: Auswahl im Regular, Anwendung in allen Mastern.
    tip_sel = find_tips(reg, reg_stem)
    log[f"{style}.tips"] = {k: len(v) for k, v in tip_sel.items()}
    # y: linke Diagonale ohne Stufe in die Unterlänge führen.
    step_sel = find_steps(reg, reg_stem)
    log[f"{style}.steps"] = step_sel
    for m, f in masters.items():
        tips_done = sharpen_tips(f, tip_sel, reg_stem)
        smooth_steps(f, step_sel)
        rep = import_into(f, inter, selection, st["italic_angle"], inter_angle)
        rep["tips_sharpened"] = tips_done
        rep["dots_squared"] = square_dots(f, dot_sel, st["italic_angle"])
        kc, ki = C.SQUIRCLE[m]
        n = sum(squircle_glyph(g, kc, ki, st["italic_angle"]) for g in f)
        track_font(f, C.TRACKING[m])
        rep["degenerate_fixed"] = fix_degenerate(f)
        # Geists Filter eraseOpenCorners greift bei Inter-Glyphen nur in einzelnen
        # Mastern und macht sie inkompatibel. Für die Importe abschalten.
        imported = sorted({selection[1].get(n, n) for n in selection[0]})
        for flt in f.lib.get("com.github.googlei18n.ufo2ft.filters", []):
            if flt.get("name") == "eraseOpenCorners":
                flt["exclude"] = imported
        build_element(f, st["italic_angle"])
        f.features.text = f.features.text.rstrip() + "\n" + ELEMENT_FEATURE
        set_categories(f)
        skip = set_skip_export(f)
        rep["skip_export"] = len(skip)
        set_info(f, m, style)
        name = f"{C.FILE_STEM}-{m}{st['suffix']}" if not (m == "Regular" and st["suffix"]) else f"{C.FILE_STEM}-{st['suffix']}"
        path = out_dir / f"{name}.ufo"
        f.save(path, overwrite=True)
        paths[m] = path
        rep["squircled_segments"] = n
        rep["glyphs_total"] = len(f)
        log[f"{style}.{m}"] = rep
    doc = build_designspace(style, paths)
    doc.lib["public.skipExportGlyphs"] = masters["Regular"].lib["public.skipExportGlyphs"]
    ds = out_dir / f"{C.FILE_STEM}{'-Italic' if st['suffix'] else ''}.designspace"
    doc.write(ds)
    log[f"{style}.seconds"] = round(time.time() - t0, 1)
    return ds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=list(C.STYLES), action="append")
    a = ap.parse_args()
    log = {}
    for style in a.style or list(C.STYLES):
        print("designspace:", prepare_style(style, log))
    (C.SOURCES / "prepare-log.json").write_text(json.dumps(log, indent=1, ensure_ascii=False))
    for k, v in log.items():
        if k.endswith(".import"):
            v = dict(v, dropped=f"{len(v['dropped'])} {v['dropped'][:12]}")
        print(k, v)


if __name__ == "__main__":
    main()
