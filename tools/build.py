#!/usr/bin/env python3
"""Kompletter Build von [Br]om.

  build.py [--skip-prepare] [--skip-static]

Ablauf: prepare (Quellen) → fontmake (variabel + statisch TTF/OTF) →
Nachbearbeitung (fsType, gasp) → WOFF2 → Lizenz/Changelog nach dist/.
"""
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fontTools.ttLib import TTFont, newTable
from brom import config as C

VENV_BIN = C.ROOT / ".venv" / "bin"
DESIGNSPACES = [C.SOURCES / "Roman" / f"{C.FILE_STEM}.designspace",
                C.SOURCES / "Italic" / f"{C.FILE_STEM}-Italic.designspace"]


def run(cmd):
    t = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    errs = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l or "Error" in l or "Traceback" in l]
    if r.returncode != 0:
        print("\n".join((r.stdout + r.stderr).splitlines()[-30:]))
        raise SystemExit(f"fehlgeschlagen: {' '.join(map(str, cmd))}")
    print(f"  ok ({time.time() - t:.0f}s) {' '.join(str(c) for c in cmd[1:4])} …" + (f" [{len(errs)} Meldungen]" if errs else ""))


def fontmake(ds, fmt, out, interpolate=False):
    cmd = [str(VENV_BIN / "fontmake"), "-m", str(ds), "-o", *fmt, "--output-dir", str(out)]
    if interpolate:
        cmd += ["-i", "--overlaps-backend", "pathops"]
    run(cmd)


def postprocess(path):
    f = TTFont(path)
    f["OS/2"].fsType = 0  # installierbar, frei einbettbar (OFL)
    if "glyf" in f and "gasp" not in f:
        gasp = newTable("gasp")
        gasp.gaspRange = {0xFFFF: 0x000F}  # ungehintet: überall glätten
        f["gasp"] = gasp
    f.save(path)


def autohint(path):
    """Hintet einen statischen TTF mit ttfautohint (für Windows bei kleinen Größen).
    Variable Fonts bleiben ungehintet."""
    import ttfautohint
    tmp = path.with_suffix(".hinted.ttf")
    ttfautohint.ttfautohint(in_file=str(path), out_file=str(tmp), hinting_range_min=8, hinting_range_max=48,
                            increase_x_height=14, windows_compatibility=True, hint_composites=True,
                            no_info=True, default_script="latn", fallback_script="none")
    tmp.replace(path)


def woff2(path, out_dir):
    f = TTFont(path)
    f.flavor = "woff2"
    dst = out_dir / (path.stem + ".woff2")
    f.save(dst)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-prepare", action="store_true")
    ap.add_argument("--skip-static", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    if not a.skip_prepare:
        print("Quellen vorbereiten …")
        run([str(VENV_BIN / "python"), str(C.ROOT / "tools" / "prepare.py")])

    var_dir, ttf_dir, otf_dir, web_dir = (C.DIST / d for d in ("variable", "ttf", "otf", "webfonts"))
    dirs = [var_dir, web_dir] + ([] if a.skip_static else [ttf_dir, otf_dir])
    for d in dirs:
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)

    print("Variable Fonts …")
    for ds in DESIGNSPACES:
        fontmake(ds, ["variable"], var_dir)
    if not a.skip_static:
        print("Statische Schnitte …")
        for ds in DESIGNSPACES:
            fontmake(ds, ["ttf"], ttf_dir, interpolate=True)
            fontmake(ds, ["otf"], otf_dir, interpolate=True)

    if not a.skip_static:
        print("Hinting (ttfautohint) …")
        for p in sorted(ttf_dir.glob("*.ttf")):
            autohint(p)

    print("Nachbearbeitung und WOFF2 …")
    fonts = sorted(var_dir.glob("*.ttf")) + sorted(ttf_dir.glob("*.ttf")) + sorted(otf_dir.glob("*.otf"))
    for p in fonts:
        postprocess(p)
    for p in sorted(var_dir.glob("*.ttf")) + sorted(ttf_dir.glob("*.ttf")):
        woff2(p, web_dir)

    for name in ("LICENSE", "CHANGELOG.md", "README.md", "VERSION"):
        src = C.ROOT / name
        if src.exists():
            shutil.copy(src, C.DIST / name)
    n = sum(1 for _ in C.DIST.rglob("*.*"))
    print(f"Fertig: Version {C.VERSION}, {n} Dateien in {C.DIST} ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
