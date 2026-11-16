"""Zentrale Parameter von [Br]om. Designentscheidungen stehen hier, nicht im Code."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = (ROOT / "VERSION").read_text().strip()
_major, _minor, _patch = (int(x) for x in VERSION.split("."))
VERSION_MAJOR = _major
VERSION_MINOR = _minor * 100 + _patch  # 0.1.0 -> 0.100 (head.fontRevision)

FAMILY = "Brom"
PS_FAMILY = "Brom"
FILE_STEM = "Brom"
VENDOR_ID = "TRFX"
DESIGNER = "TRFX"
URL = "https://brom.trfx.de"
COPYRIGHT = (
    "Copyright 2026 TRFX (https://brom.trfx.de), with Reserved Font Name \"Brom\". "
    "Based on Geist, Copyright 2026 The Geist Project Authors (https://github.com/vercel/geist-font), "
    "and Inter, Copyright 2016 The Inter Project Authors (https://github.com/rsms/inter)."
)
LICENSE_DESC = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
    "This license is available with a FAQ at: https://openfontlicense.org"
)
LICENSE_URL = "https://openfontlicense.org"
DESCRIPTION = (
    "Brom – eine technische, eckige Sans für Interfaces und Technik. "
    "Abgeleitet von Geist und Inter, mit superelliptischen Rundungen nach dem Vorbild von IBM Plex."
)

UPSTREAM = ROOT / "work"
GEIST_UFO = UPSTREAM / "geist-ufo"
INTER_UFO = UPSTREAM / "inter-ufo"
SOURCES = ROOT / "sources"
DIST = ROOT / "dist"

# Master-Definition. "geist_black_t": Der Black-Master von Brom ist eine
# Interpolation Regular→Black von Geist. <1.0 macht 900 etwas leichter als Geist,
# damit Punzen und Öffnungen bei hohen Gewichten offen bleiben.
STYLES = {
    "Roman": {
        "geist": {"Thin": "Geist/Geist-Thin.ufo", "Regular": "Geist/Geist-Regular.ufo", "Black": "Geist/Geist-Black.ufo"},
        "inter": {"Thin": "Inter-Roman/Inter-Thin.ufo", "Regular": "Inter-Roman/Inter-Regular.ufo", "Black": "Inter-Roman/Inter-Black.ufo"},
        "italic_angle": 0.0,
        "suffix": "",
    },
    "Italic": {
        "geist": {"Thin": "Geist-Italic/Geist-ThinItalic.ufo", "Regular": "Geist-Italic/Geist-Italic.ufo", "Black": "Geist-Italic/Geist-BlackItalic.ufo"},
        "inter": {"Thin": "Inter-Italic/Inter-ThinItalic.ufo", "Regular": "Inter-Italic/Inter-Italic.ufo", "Black": "Inter-Italic/Inter-BlackItalic.ufo"},
        "italic_angle": -12.0,
        "suffix": "Italic",
    },
}

MASTER_WGHT = {"Thin": 100, "Regular": 400, "Black": 900}
GEIST_BLACK_T = 0.90

# Superellipse: Anteil, um den die Anfasser zur Ecke wandern (0 = Geist, 1 = Ecke).
# Konkav (Punzen) etwas stärker als konvex: offene Punzen, kein Klumpen in der
# Diagonale. Der Abstand ist klein gehalten, sonst werden die Ecken dünn und der
# Strich wirkt ungleichmäßig (Rückmeldung zu 0.1.0).
SQUIRCLE = {
    "Thin": (0.34, 0.37),
    "Regular": (0.34, 0.40),
    "Black": (0.32, 0.42),
}

# Zusätzliche Laufweite je Master (Einheiten pro Glyph, 1000 UPM).
TRACKING = {"Thin": 6, "Regular": 4, "Black": 22}

# Gewichtsinstanzen (Userspace = Designspace, die Master liegen auf 100/400/900).
WEIGHTS = [
    (100, "Thin"), (200, "ExtraLight"), (300, "Light"), (400, "Regular"), (500, "Medium"),
    (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"), (900, "Black"),
]

# Fremde Marken und Vercel-spezifische Features, die nicht in Brom gehören.
DROP_GLYPHS = {"apple"}
DROP_FEATURES = {"ss11"}

# Glyph für die Element-Kachel [Br]. Kein eigener Codepoint, nur über dlig.
ELEMENT_GLYPH = "Br.element"
# Innenabstand zwischen „Br" und Rahmen links/rechts, in Versalhöhen. „Br" selbst
# steht in voller Größe, die Kachel ergibt sich daraus (Black reicht bis -340,
# so tief wie die tiefsten übrigen Zeichen).
ELEMENT_PAD = 0.09
