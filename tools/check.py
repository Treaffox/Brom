#!/usr/bin/env python3
"""Prüft die gebauten Fonts in dist/ und gibt eine kompakte Übersicht aus."""
import sys
from pathlib import Path
from fontTools.ttLib import TTFont

DIST = Path(__file__).resolve().parents[1] / "dist"
problems = []


def name(f, i):
    r = f["name"].getName(i, 3, 1, 0x409)
    return r.toUnicode() if r else None


def check(p):
    f = TTFont(p)
    os2, head = f["OS/2"], f["head"]
    italic = "Italic" in p.name
    row = {
        "file": p.name, "fam": name(f, 1), "sub": name(f, 2), "typo": f"{name(f, 16) or ''}/{name(f, 17) or ''}",
        "ps": name(f, 6), "ver": name(f, 5), "wght": os2.usWeightClass, "rev": round(head.fontRevision, 3),
        "glyphs": len(f.getGlyphOrder()), "cps": len(f.getBestCmap()),
    }
    if os2.achVendID != "TRFX":
        problems.append(f"{p.name}: VendorID {os2.achVendID}")
    if os2.fsType != 0:
        problems.append(f"{p.name}: fsType {os2.fsType}")
    if bool(os2.fsSelection & 1) != italic or bool(head.macStyle & 2) != italic:
        problems.append(f"{p.name}: Italic-Bits falsch")
    if italic and f["post"].italicAngle == 0:
        problems.append(f"{p.name}: italicAngle 0")
    for i in (0, 1, 3, 4, 5, 6, 13):
        v = name(f, i) or ""
        for bad in ("Geist", "Vercel", "Inter ", "rsms", "VRCL"):
            if bad in v and i not in (0, 13):
                problems.append(f"{p.name}: name {i} enthält {bad!r}: {v[:60]}")
    if 0xF8FF in f.getBestCmap():
        problems.append(f"{p.name}: U+F8FF (Apple-Logo) vorhanden")
    if any(0xE000 <= u <= 0xF8FF for u in f.getBestCmap()):
        problems.append(f"{p.name}: Codepoint im privaten Bereich (PUA) vorhanden")
    if "Br.element" not in f.getGlyphOrder():
        problems.append(f"{p.name}: [Br]-Element fehlt")
    if "fvar" in f:
        row["axes"] = [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in f["fvar"].axes]
        row["inst"] = len(f["fvar"].instances)
        stat = f["STAT"].table
        row["stat"] = [(a.AxisTag) for a in stat.DesignAxisRecord.Axis]
    feats = sorted({r.FeatureTag for r in f["GSUB"].table.FeatureList.FeatureRecord}) if "GSUB" in f else []
    row["gsub"] = " ".join(feats)
    if "ss11" in feats:
        problems.append(f"{p.name}: ss11 (Vercel) noch vorhanden")
    return row


def main():
    files = sorted(DIST.rglob("*.ttf")) + sorted(DIST.rglob("*.otf"))
    rows = [check(p) for p in files]
    for r in rows:
        if r["file"].endswith("].ttf") or r["file"] in ("Brom-Regular.otf", "Brom-BoldItalic.ttf", "Brom-ThinItalic.otf"):
            print(r)
    print(f"\n{len(files)} Dateien geprüft.")
    print("Probleme:" if problems else "Keine Probleme gefunden.")
    for p in problems:
        print(" -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
