#!/usr/bin/env python3
"""Baut die öffentliche Seite brom.trfx.de nach site/dist/.

  site.py

Voraussetzung: tools/build.py ist gelaufen (dist/ enthält die Fonts).
Alles, was hier landet, ist öffentlich: keine Host-Pfade, Server, Ports oder
internen Namen in Texte schreiben.
"""
import html
import json
import re
import shutil
import sys
import unicodedata
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fontTools.ttLib import TTFont
from PIL import Image
from brom import config as C

SITE = C.ROOT / "site"
STATIC = SITE / "static"
OUT = SITE / "dist"
V = C.VERSION
# Cache-Schlüssel für CSS/JS: Version plus Inhalts-Hash, damit Änderungen an der
# Seite ohne neue Schriftversion sofort ankommen (Assets werden 7 Tage gecacht).
import hashlib
ASSET_REV = V + "-" + hashlib.sha256(b"".join((SITE / "src" / n).read_bytes() for n in ("brom.css", "brom.js"))).hexdigest()[:8]
VF_ROMAN = C.DIST / "variable" / f"{C.FILE_STEM}[wght].ttf"
VF_ITALIC = C.DIST / "variable" / f"{C.FILE_STEM}-Italic[wght].ttf"

FOOTER_LINKS = [
    ("Datenschutz", "https://www.trfx.de/dsb"), ("AGB", "https://www.trfx.de/agb"),
    ("Impressum", "https://www.trfx.de/impressum"), ("Kontakt", "https://www.trfx.de/contact"),
    ("Sache des Tages", "https://www.trfx.de/sdt"), ("Server Status", "https://status.trfx.de/"),
    ("Socials", "https://www.trfx.de/socials"), ("SSO", "https://github.com/Treaffox/selfhosted-sso"),
    ("SAINT", "https://github.com/Treaffox/saint-monitoring"), ("TPN", "https://push.trfx.de/"),
    ("Twitch Logs", "https://logs.trfx.de/"),
]

WEIGHTS = [(100, "Thin"), (200, "ExtraLight"), (300, "Light"), (400, "Regular"), (500, "Medium"),
           (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"), (900, "Black")]

# Unicode-Blöcke für die Zeichenübersicht (Bereich, Name, Filtergruppe)
BLOCKS = [
    (0x0020, 0x007F, "Basis-Latein", "latein"), (0x00A0, 0x00FF, "Latein-1, Ergänzung", "latein"),
    (0x0100, 0x017F, "Latein, erweitert A", "latein"), (0x0180, 0x024F, "Latein, erweitert B", "latein"),
    (0x0250, 0x02AF, "IPA", "latein"), (0x02B0, 0x02FF, "Modifikatoren", "symbole"),
    (0x0300, 0x036F, "Kombinierende Diakritika", "latein"), (0x0370, 0x03FF, "Griechisch", "griechisch"),
    (0x0400, 0x04FF, "Kyrillisch", "kyrillisch"), (0x0500, 0x052F, "Kyrillisch, Ergänzung", "kyrillisch"),
    (0x1AB0, 0x1AFF, "Kombinierende Diakritika, erweitert", "latein"),
    (0x1D00, 0x1DBF, "Phonetische Erweiterungen", "latein"),
    (0x1DC0, 0x1DFF, "Kombinierende Diakritika, Ergänzung", "latein"),
    (0x1E00, 0x1EFF, "Latein, erweitert zusätzlich", "latein"), (0x1F00, 0x1FFF, "Griechisch, erweitert", "griechisch"),
    (0x2000, 0x206F, "Interpunktion", "symbole"), (0x2070, 0x209F, "Hoch- und Tiefstellung", "ziffern"),
    (0x20A0, 0x20CF, "Währungen", "symbole"), (0x2100, 0x214F, "Buchstabenartige Symbole", "symbole"),
    (0x2150, 0x218F, "Zahlzeichen", "ziffern"), (0x2190, 0x21FF, "Pfeile", "symbole"),
    (0x2200, 0x22FF, "Mathematische Operatoren", "symbole"), (0x2300, 0x23FF, "Technische Zeichen", "symbole"),
    (0x2400, 0x243F, "Steuerzeichen-Symbole", "symbole"), (0x2460, 0x24FF, "Umschlossene Zeichen", "ziffern"),
    (0x2500, 0x257F, "Rahmen", "symbole"), (0x2580, 0x259F, "Blockelemente", "symbole"),
    (0x25A0, 0x25FF, "Geometrische Formen", "symbole"), (0x2600, 0x27BF, "Verschiedene Symbole", "symbole"),
    (0x27C0, 0x2BFF, "Weitere Pfeile und Symbole", "symbole"),
    (0x2C60, 0x2C7F, "Latein, erweitert C", "latein"), (0x2DE0, 0x2DFF, "Kyrillisch, erweitert A", "kyrillisch"),
    (0x2E00, 0x2E7F, "Ergänzende Interpunktion", "symbole"), (0xA640, 0xA69F, "Kyrillisch, erweitert B", "kyrillisch"),
    (0xA700, 0xA7FF, "Latein, erweitert D", "latein"), (0xAB30, 0xAB6F, "Latein, erweitert E", "latein"),
    (0xFB00, 0xFB4F, "Ligaturen", "latein"),
    (0xFE20, 0xFE2F, "Kombinierende Halbzeichen", "latein"), (0xFFF0, 0xFFFF, "Sonderzeichen", "symbole"),
]
GROUPS = [("alle", "Alle"), ("latein", "Latein"), ("griechisch", "Griechisch"), ("kyrillisch", "Kyrillisch"),
          ("ziffern", "Ziffern"), ("symbole", "Symbole")]

FEATURES = [
    ("dlig", "Element-Kachel für die Folge [Br]", "Brom [Br]"),
    ("ss01", "a ohne Fuß", "Datenblatt"),
    ("ss02", "Einstöckiges a", "Datenblatt"),
    ("ss03", "l ohne Fuß", "Ventil 11 l"),
    ("ss04", "R mit schrägem Bein", "RADAR"),
    ("ss05", "I mit Serifen", "Il1 IIoT"),
    ("ss06", "Alternatives G", "GIGABIT"),
    ("ss07", "Schlanke Pfeile", "A → B ↗ C"),
    ("ss08", "Runde statt eckiger Punkte", "Ölmühle: jäh, ïj."),
    ("ss09", "0 mit Schrägstrich, 1 mit Fuß", "0O 1Il 10:01"),
    ("ss10", "Dekorative Klammerformen", "[x] (y) {z} <w>"),
    ("tnum", "Ziffern mit fester Breite", "1.111,11 / 8.888,88"),
    ("frac", "Echte Brüche", "1/2 3/4 7/8"),
    ("sups", "Hochgestellt", "m2 x3"),
    ("case", "Satzzeichen für Versalien", "(HALLO)-[WELT]"),
]

TEXTS = {
    "de": "Brom ist ein chemisches Element mit dem Symbol Br und der Ordnungszahl 35. Bei Raumtemperatur ist es eine rotbraune, flüchtige Flüssigkeit.",
    "en": "Bromine is a chemical element with the symbol Br and atomic number 35. It is a volatile red-brown liquid at room temperature.",
    "el": "Το βρώμιο είναι χημικό στοιχείο με σύμβολο Br και ατομικό αριθμό 35.",
    "ru": "Бром — химический элемент с символом Br и атомным номером 35.",
    "vi": "Brom là một nguyên tố hóa học có ký hiệu Br và số nguyên tử 35.",
    "tech": "0123456789 ±×÷=≠≈≤≥ ∑∏∫√∞ → ← ↑ ↓ ⏎ ⌘ ⌥ ⇧ €$£¥₿ 10 µm · 35 °C · 79,904 u",
}
TEXT_LABELS = [("de", "Deutsch"), ("en", "Englisch"), ("el", "Griechisch"), ("ru", "Russisch"),
               ("vi", "Vietnamesisch"), ("tech", "Technik")]


# Stylesheet unter der festen URL /latest/brom.css (Schriftdateien liegen daneben, ohne Version).
LATEST_CSS = """/* Brom, immer die neueste Version. https://brom.trfx.de */
@font-face {
  font-family: "Brom";
  src: url("Brom-VF.woff2") format("woff2");
  font-weight: 100 900; font-style: normal; font-display: swap;
}
@font-face {
  font-family: "Brom";
  src: url("Brom-Italic-VF.woff2") format("woff2");
  font-weight: 100 900; font-style: italic; font-display: swap;
}
"""


def esc(s):
    return html.escape(s, quote=True)


def md_inline(s):
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
               r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', s)
    return s


def md_to_html(text, skip_title=True):
    out, in_list, para = [], False, []

    def flush():
        nonlocal para
        if para:
            out.append("<p>" + md_inline(" ".join(para)) + "</p>")
            para = []

    for line in text.splitlines():
        if line.startswith("# "):
            flush()
            if not skip_title:
                out.append(f"<h2>{md_inline(line[2:])}</h2>")
            continue
        if line.startswith("## ") or line.startswith("### "):
            flush()
            if in_list:
                out.append("</ul>"); in_list = False
            lvl = 3 if line.startswith("## ") else 4
            out.append(f"<h{lvl}>{md_inline(line.split(' ', 1)[1])}</h{lvl}>")
        elif line.startswith("- "):
            flush()
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{md_inline(line[2:])}</li>")
        elif not line.strip():
            flush()
            if in_list:
                out.append("</ul>"); in_list = False
        else:
            if in_list:
                out.append("</ul>"); in_list = False
            para.append(line.strip())
    flush()
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def block_of(cp):
    for a, z, name, grp in BLOCKS:
        if a <= cp <= z:
            return name, grp
    return "Weitere", "symbole"


def glyph_grid(font):
    cmap = font.getBestCmap()
    has_dotted = 0x25CC in cmap
    blocks = {}
    for cp in sorted(cmap):
        if cp < 0x20 or (0x7F <= cp < 0xA0):
            continue
        name, grp = block_of(cp)
        blocks.setdefault((name, grp), []).append(cp)
    parts = []
    for (name, grp), cps in blocks.items():
        cells = []
        for cp in cps:
            ch = chr(cp)
            uname = unicodedata.name(ch, "")
            cat = unicodedata.category(ch)
            shown = ch
            if cat.startswith("M"):
                shown = ("◌" if has_dotted else " ") + ch
            elif cat.startswith("Z") or cat == "Cf":
                shown = " "
            label = f"U+{cp:04X} {uname}".strip()
            cells.append(f'<button type="button" class="g" data-cp="{cp:04X}" data-n="{esc(uname)}" '
                         f'aria-label="{esc(label)}">{esc(shown)}</button>')
        parts.append(f'<section class="gblock" data-group="{grp}"><h3>{esc(name)} '
                     f'<span class="count">{len(cps)}</span></h3><div class="ggrid">{"".join(cells)}</div></section>')
    return "\n".join(parts), sum(1 for cp in cmap if cp >= 0x20 and not (0x7F <= cp < 0xA0))


def build_zip(dst):
    stem = f"{C.FILE_STEM}-{V}"
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for sub in ("variable", "otf", "ttf", "webfonts"):
            for p in sorted((C.DIST / sub).iterdir()):
                z.write(p, f"{stem}/{sub}/{p.name}")
        for name in ("LICENSE", "README.md", "CHANGELOG.md", "VERSION"):
            z.write(C.ROOT / name, f"{stem}/{name if name != 'LICENSE' else 'LICENSE.txt'}")


def human(n):
    return f"{n / 1024 / 1024:.1f} MB" if n > 1024 * 1024 else f"{round(n / 1024)} KB"


def page(title, body, desc, extra_head=""):
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<base href="/">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="assets/brand/favicon-64.png?v={V}" type="image/png">
<link rel="preload" href="assets/fonts/Brom-Roman-VF.woff2?v={V}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/brom.css?v={ASSET_REV}">
{extra_head}</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
<header class="top">
  <div class="wrap top__inner">
    <a class="brand" href="/" aria-label="Brom, Startseite">
      <img class="brand__logo" src="assets/brand/trfx-logo.svg?v={V}" alt="TRFX.DE" width="122" height="18">
      <span class="brand__name"><span class="dlig">[Br]</span>om</span>
    </a>
    <nav class="nav" aria-label="Hauptnavigation">
      <a href="/#tester">Tester</a><a href="/#gewichte">Gewichte</a><a href="/#prinzip">Prinzip</a>
      <a href="/#zeichen">Zeichen</a><a href="/#features">Features</a><a href="/#festerlink">Einbinden</a><a href="/#download">Download</a>
      <a href="/#aenderungen">Änderungen</a>
    </nav>
    <span class="ver" title="Aktuelle Version">v{V}</span>
  </div>
</header>
<main id="inhalt">
{body}
</main>
<footer class="foot">
  <div class="wrap foot__inner">
    <p class="foot__copy">© <span data-year>{date.today().year}</span> TRFX.DE - Alle Rechte vorbehalten.</p>
    <ul class="foot__links">
      {"".join(f'<li><a href="{u}" target="_blank" rel="noopener noreferrer">{esc(t)}</a></li>' for t, u in FOOTER_LINKS)}
    </ul>
  </div>
</footer>
<script src="assets/brom.js?v={ASSET_REV}" defer></script>
</body>
</html>
"""


def section(num, sid, title, lead, inner, cls=""):
    lead_html = f'<p class="lead">{lead}</p>' if lead else ""
    return f"""<section class="sec {cls}" id="{sid}" aria-labelledby="{sid}-t">
  <div class="wrap">
    <header class="sec__head"><span class="sec__num">{num}</span><h2 id="{sid}-t">{title}</h2>{lead_html}</header>
    {inner}
  </div>
</section>"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets" / "fonts").mkdir(parents=True)
    (OUT / "assets" / "brand").mkdir(parents=True)
    (OUT / "downloads").mkdir(parents=True)

    # Schriften für die Seite
    web = C.DIST / "webfonts"
    shutil.copy(web / f"{C.FILE_STEM}[wght].woff2", OUT / "assets/fonts/Brom-Roman-VF.woff2")
    shutil.copy(web / f"{C.FILE_STEM}-Italic[wght].woff2", OUT / "assets/fonts/Brom-Italic-VF.woff2")
    # Marke
    shutil.copy(STATIC / "brand" / "trfx-logo.svg", OUT / "assets/brand" / "trfx-logo.svg")
    fav = Image.open(STATIC / "brand/favicon.png").convert("RGBA")
    fav.resize((64, 64), Image.LANCZOS).save(OUT / "assets/brand/favicon-64.png", optimize=True)
    fav.resize((180, 180), Image.LANCZOS).save(OUT / "assets/brand/apple-touch-icon.png", optimize=True)
    # Downloads
    zip_name = f"{C.FILE_STEM}-{V}.zip"
    build_zip(OUT / "downloads" / zip_name)
    shutil.copy(C.ROOT / "LICENSE", OUT / "downloads/LICENSE.txt")
    for p in sorted((C.DIST / "variable").glob("*.ttf")) + sorted(web.glob("*[[]wght[]].woff2")):
        shutil.copy(p, OUT / "downloads" / p.name)
    # Feste URLs ohne Version im Pfad: hier liegt immer die neueste Fassung (Apps binden diese ein).
    (OUT / "latest").mkdir()
    shutil.copy(web / f"{C.FILE_STEM}[wght].woff2", OUT / "latest/Brom-VF.woff2")
    shutil.copy(web / f"{C.FILE_STEM}-Italic[wght].woff2", OUT / "latest/Brom-Italic-VF.woff2")
    shutil.copy(OUT / "downloads" / zip_name, OUT / "latest/Brom-latest.zip")
    shutil.copy(C.ROOT / "LICENSE", OUT / "latest/LICENSE.txt")
    (OUT / "latest/brom.css").write_text(LATEST_CSS)
    for name in ("brom.css", "brom.js"):
        (OUT / "assets" / name).write_text((SITE / "src" / name).read_text().replace("{{V}}", V))

    font = TTFont(VF_ROMAN)
    grid_html, n_chars = glyph_grid(font)
    n_glyphs = len(font.getGlyphOrder())
    sizes = {p.name: p.stat().st_size for p in (OUT / "downloads").iterdir()}

    def dl(name):
        return "downloads/" + name.replace("[", "%5B").replace("]", "%5D")

    # ---------- Inhalt ----------
    # (Tausendertrennzeichen deutsch)
    fmt = lambda n: f"{n:,}".replace(",", ".")
    hero = f"""<section class="hero" aria-labelledby="hero-t">
  <div class="wrap">
    <p class="kicker">Eine Schrift von TRFX.DE · Version {V} · Open Font License</p>
    <h1 id="hero-t" class="hero__title" aria-label="Brom"><span class="dlig">[Br]</span>om</h1>
    <p class="hero__lead">Eine technische Sans für Interfaces und Technik. Eckig, sachlich und ruhig, mit straffen Rundungen. Von Thin bis Black lesbar.</p>
    <div class="hero__cta">
      <a class="btn btn--solid" href="{dl(zip_name)}" download>Herunterladen <span class="btn__meta">ZIP · {human(sizes[zip_name])}</span></a>
      <a class="btn" href="/#tester">Ausprobieren</a>
    </div>
    <dl class="facts">
      <div><dt>Gewichte</dt><dd>100–900</dd></div>
      <div><dt>Stile</dt><dd>Aufrecht, Kursiv</dd></div>
      <div><dt>Zeichen</dt><dd>{fmt(n_chars)}</dd></div>
      <div><dt>Glyphen</dt><dd>{fmt(n_glyphs)}</dd></div>
      <div><dt>Formate</dt><dd>Variabel, OTF, TTF, WOFF2</dd></div>
    </dl>
  </div>
</section>"""

    feat_chips = "".join(
        f'<label class="chip"><input type="checkbox" data-feature="{t}"><span>{t}</span></label>'
        for t, _, _ in FEATURES)
    text_opts = "".join(f'<option value="{k}">{esc(l)}</option>' for k, l in TEXT_LABELS)
    tester = section("01", "tester", "Tester", "Text anklicken und eigenen Text schreiben.", f"""
<div class="tester" data-texts='{esc(json.dumps(TEXTS, ensure_ascii=False))}'>
  <div class="tester__controls">
    <label class="ctl"><span class="ctl__l">Gewicht <output data-out="wght">400</output></span>
      <input type="range" min="100" max="900" step="1" value="400" data-ctl="wght"></label>
    <label class="ctl"><span class="ctl__l">Größe <span><output data-out="size">64</output> px</span></span>
      <input type="range" min="12" max="200" step="1" value="64" data-ctl="size"></label>
    <label class="ctl"><span class="ctl__l">Laufweite <output data-out="track">0</output></span>
      <input type="range" min="-6" max="20" step="1" value="0" data-ctl="track"></label>
    <label class="ctl"><span class="ctl__l">Zeilenabstand <output data-out="lh">1,15</output></span>
      <input type="range" min="90" max="180" step="5" value="115" data-ctl="lh"></label>
    <label class="ctl ctl--inline"><input type="checkbox" data-ctl="italic"> Kursiv</label>
    <label class="ctl"><span class="ctl__l">Text</span>
      <select data-ctl="text">{text_opts}</select></label>
    <fieldset class="chips"><legend>OpenType-Features</legend>{feat_chips}</fieldset>
  </div>
  <div class="tester__stage">
    <div class="tester__text" contenteditable="true" spellcheck="false" role="textbox" aria-multiline="true" aria-label="Testtext">{esc(TEXTS["de"])}</div>
  </div>
</div>""")

    rows = "".join(
        f'<li class="wf__row w{w}"><span class="wf__meta"><b>{w}</b> {n}</span>'
        f'<span class="wf__text" contenteditable="true" spellcheck="false">Brom · Ordnungszahl 35 · 79,904 u</span></li>'
        for w, n in WEIGHTS)
    weights = section("02", "gewichte", "Gewichte",
                      "Neun Schnitte, stufenlos als Variable Font. Auch Black bleibt offen und lesbar.", f"""
<div class="wf-tools"><label class="ctl ctl--inline"><input type="checkbox" data-wf-italic> Kursiv</label></div>
<ul class="wf">{rows}</ul>
<div class="legib">
  <article class="legib__col w400"><h3>Regular 400</h3><p>{esc(TEXTS["de"])} Das Element gehört zu den Halogenen und ist neben Quecksilber das einzige bei Normalbedingungen flüssige Element.</p></article>
  <article class="legib__col w700"><h3>Bold 700</h3><p>{esc(TEXTS["de"])} Das Element gehört zu den Halogenen und ist neben Quecksilber das einzige bei Normalbedingungen flüssige Element.</p></article>
  <article class="legib__col w900"><h3>Black 900</h3><p>{esc(TEXTS["de"])} Das Element gehört zu den Halogenen und ist neben Quecksilber das einzige bei Normalbedingungen flüssige Element.</p></article>
</div>""")

    principle = section("03", "prinzip", "Prinzip", "", f"""
<div class="prin">
  <div class="prin__show" aria-hidden="true"><span class="w200">o</span><span class="w500">O</span><span class="w900">0</span><span class="w900 dlig">[Br]</span></div>
  <ul class="prin__list">
    <li><h3>Straffe Rundungen</h3><p>Bögen sind zur Ecke hin gestrafft, wie ein abgerundetes Rechteck. Innenformen stärker als Außenformen: So bleiben Punzen offen, und Diagonalen werden nicht klumpig.</p></li>
    <li><h3>Lesbar bis Black</h3><p>Der schwerste Schnitt ist bewusst etwas leichter und läuft weiter. Bei 900 bleiben a, e, s und g offen.</p></li>
    <li><h3>Schweizer Grundform</h3><p>Neutrale Proportionen, waagrechte Strichenden, wenig Kontrast. Kühl und sachlich, ohne tot zu wirken.</p></li>
    <li><h3>Technisch eindeutig</h3><p>Ziffern mit fester Breite, 0 mit Schrägstrich, I mit Serifen und andere Alternativen über OpenType. Il1 und 0O lassen sich unterscheiden, wo es darauf ankommt.</p></li>
    <li><h3>[Br] als Zeichen</h3><p>Die Element-Kachel ist Teil der Schrift: Mit <code>dlig</code> wird aus <code>[Br]</code> die Kachel.</p></li>
    <li><h3>Herkunft</h3><p>Basis ist Geist, ergänzt um Zeichen aus Inter, beide unter der Open Font License. Die gestrafften Bögen sind von IBM Plex Sans inspiriert.</p></li>
  </ul>
</div>""")

    group_btns = "".join(f'<button type="button" class="seg__b{" is-on" if k == "alle" else ""}" data-filter="{k}">{esc(l)}</button>'
                         for k, l in GROUPS)
    glyphs = section("04", "zeichen", "Zeichen",
                     f"{fmt(n_chars)} Zeichen. Klick auf ein Zeichen kopiert es.", f"""
<div class="gtools"><div class="seg" role="group" aria-label="Schriftsystem filtern">{group_btns}</div>
  <label class="ctl ctl--inline"><input type="range" min="100" max="900" value="400" data-g-wght aria-label="Gewicht der Zeichenübersicht"> <output data-out="gwght">400</output></label></div>
<div class="gwrap">
  <aside class="ginfo" aria-live="polite"><div class="ginfo__ch" data-ginfo-ch>ß</div><p class="ginfo__cp" data-ginfo-cp>U+00DF</p><p class="ginfo__n" data-ginfo-n>Zeichen auswählen</p></aside>
  <div class="gblocks">{grid_html}</div>
</div>""")

    feat_rows = "".join(
        f'<tr><th scope="row"><code>{t}</code></th><td>{esc(d)}</td>'
        f'<td class="fx">{esc(s)}</td><td class="fx ff-{t}">{esc(s)}</td></tr>'
        for t, d, s in FEATURES)
    features = section("05", "features", "Features", "Jeweils ohne und mit Feature.", f"""
<div class="tablewrap"><table class="ftable"><thead><tr><th scope="col">Tag</th><th scope="col">Wirkung</th><th scope="col">Aus</th><th scope="col">An</th></tr></thead>
<tbody>{feat_rows}</tbody></table></div>""")

    link_snip = """<link rel="preconnect" href="https://brom.trfx.de" crossorigin>
<link rel="stylesheet" href="https://brom.trfx.de/latest/brom.css">

/* im eigenen CSS */
body { font-family: "Brom", system-ui, sans-serif; }"""
    css_snip = """/* Zuerst der feste Link, dann die eigene Kopie (Fallback). */
@font-face {
  font-family: "Brom";
  src: url("https://brom.trfx.de/latest/Brom-VF.woff2") format("woff2"),
       url("/fonts/Brom-VF.woff2") format("woff2");
  font-weight: 100 900; font-style: normal; font-display: swap;
}
@font-face {
  font-family: "Brom";
  src: url("https://brom.trfx.de/latest/Brom-Italic-VF.woff2") format("woff2"),
       url("/fonts/Brom-Italic-VF.woff2") format("woff2");
  font-weight: 100 900; font-style: italic; font-display: swap;
}
body { font-family: "Brom", system-ui, sans-serif; }"""
    sync_snip = """mkdir -p public/fonts
curl -fsSL https://brom.trfx.de/latest/Brom-VF.woff2        -o public/fonts/Brom-VF.woff2
curl -fsSL https://brom.trfx.de/latest/Brom-Italic-VF.woff2 -o public/fonts/Brom-Italic-VF.woff2
curl -fsSL https://brom.trfx.de/latest/version.json         -o public/fonts/brom-version.json"""
    files = [
        (f"{C.FILE_STEM}[wght].woff2", "Variable Font, aufrecht, Web"),
        (f"{C.FILE_STEM}-Italic[wght].woff2", "Variable Font, kursiv, Web"),
        (f"{C.FILE_STEM}[wght].ttf", "Variable Font, aufrecht, Desktop"),
        (f"{C.FILE_STEM}-Italic[wght].ttf", "Variable Font, kursiv, Desktop"),
    ]
    file_rows = "".join(
        f'<li><a href="{dl(n)}" download><span class="dl__n">{esc(n)}</span><span class="dl__d">{esc(d)}</span>'
        f'<span class="dl__s">{human(sizes[n])}</span></a></li>' for n, d in files)
    embed = section("06", "festerlink", "Per festem Link einbinden",
                    "Empfohlen für alle Apps: Die Schrift wird immer über denselben Link geladen. Ändert sich Brom, muss keine App angepasst werden.", f"""
<div class="tablewrap"><table class="ftable"><thead><tr><th scope="col">Adresse</th><th scope="col">Inhalt</th></tr></thead>
<tbody><tr><th scope="row"><code>https://brom.trfx.de/latest/brom.css</code></th><td>fertiges CSS mit <code>@font-face</code> für Brom (aufrecht und kursiv, Gewicht 100–900)</td></tr><tr><th scope="row"><code>https://brom.trfx.de/latest/Brom-VF.woff2</code></th><td>Variable Font, aufrecht</td></tr><tr><th scope="row"><code>https://brom.trfx.de/latest/Brom-Italic-VF.woff2</code></th><td>Variable Font, kursiv</td></tr><tr><th scope="row"><code>https://brom.trfx.de/latest/Brom-latest.zip</code></th><td>komplettes Paket (alle Formate, Lizenz, Änderungsprotokoll)</td></tr><tr><th scope="row"><code>https://brom.trfx.de/latest/version.json</code></th><td>aktuelle Versionsnummer und Dateiliste</td></tr></tbody></table></div>
<div class="license"><h3>In die Seite einbauen</h3>
<p>Die Adressen antworten mit <code>Cache-Control: no-cache</code> und erlauben fremde Seiten (CORS). Der Browser fragt bei jedem Aufruf kurz nach (ETag) und lädt nur bei einer neuen Version neu. Wenn die App eine Content-Security-Policy setzt, müssen <code>style-src</code> und <code>font-src</code> <code>https://brom.trfx.de</code> erlauben.</p></div>
<div class="code"><div class="code__bar"><span>HTML</span><button type="button" class="code__copy" data-copy="#link-snippet">Kopieren</button></div>
<pre id="link-snippet"><code>{esc(link_snip)}</code></pre></div>
<div class="license"><h3>Fallback: neueste Version herunterladen und selbst hosten</h3>
<p>Jede App liefert zusätzlich eine eigene Kopie der <strong>neuesten</strong> Version aus. Sie springt ein, wenn der feste Link nicht erreichbar ist (Ausfall, Firmennetz, Offline). Die Kopie wird beim Bauen oder Ausrollen der App frisch geholt, nicht von Hand gepflegt:</p></div>
<div class="code"><div class="code__bar"><span>Eigene Kopie holen</span><button type="button" class="code__copy" data-copy="#sync-snippet">Kopieren</button></div>
<pre id="sync-snippet"><code>{esc(sync_snip)}</code></pre></div>
<div class="license"><p>Im CSS steht der feste Link zuerst, die eigene Kopie danach. Der Browser nimmt die zweite Quelle nur, wenn die erste nicht lädt:</p></div>
<div class="code"><div class="code__bar"><span>CSS mit Fallback</span><button type="button" class="code__copy" data-copy="#css-snippet">Kopieren</button></div>
<pre id="css-snippet"><code>{esc(css_snip)}</code></pre></div>
<div class="license"><p>Ohne eigenen <code>@font-face</code> genügt <code>brom.css</code> allein. Die Kopie lässt sich auch über das Paket <code>Brom-latest.zip</code> holen. Feste Versionen bleiben unter <code>downloads/Brom-&lt;Version&gt;.zip</code> erhalten.</p>
<p class="license__more">Änderungen, die den Satz bestehender Texte sichtbar verschieben (Breiten, Zeilenhöhe), erhöhen die Hauptversion und stehen vorher im Änderungsprotokoll. Gewohnte Korrekturen kommen ohne Ankündigung über den festen Link.</p></div>""")

    download = section("07", "download", "Download",
                       "Frei nutzbar unter der SIL Open Font License 1.1, auch kommerziell.", f"""
<div class="dl">
  <a class="dl__main" href="{dl(zip_name)}" download>
    <span class="dl__title">Komplettpaket {V}</span>
    <span class="dl__sub">Variable Fonts, 18 OTF, 18 TTF, WOFF2, Lizenz, Änderungsprotokoll</span>
    <span class="dl__size">ZIP · {human(sizes[zip_name])}</span>
  </a>
  <ul class="dl__files">{file_rows}</ul>
</div>
<div class="license"><h3>Lizenz</h3>
<p>Brom steht unter der <a href="downloads/LICENSE.txt">SIL Open Font License 1.1</a>. Die Schrift darf frei benutzt, eingebettet, weitergegeben und verändert werden, auch kommerziell. Nur der Verkauf der Schriftdateien allein ist nicht erlaubt. Veränderte Fassungen dürfen nicht „Brom“ heißen (Reserved Font Name). Brom enthält Teile von Geist (© The Geist Project Authors) und Inter (© The Inter Project Authors), beide unter der Open Font License.</p></div>""")

    changelog = section("08", "aenderungen", "Änderungen", "",
                        f'<div class="log">{md_to_html((C.ROOT / "CHANGELOG.md").read_text())}</div>')

    body = "\n".join([hero, tester, weights, principle, glyphs, features, embed, download, changelog])
    desc = ("Brom: technische, eckige Sans-Serif. Gewichte 100 bis 900, aufrecht und kursiv, "
            "über 2000 Zeichen. Frei unter der Open Font License.")
    (OUT / "index.html").write_text(page(f"Brom – Schrift {V}", body, desc), encoding="utf-8")

    nf = f"""<section class="hero hero--404"><div class="wrap">
<p class="kicker">Fehler 404</p><h1 class="hero__title">Nicht gefunden</h1>
<p class="hero__lead">Diese Seite gibt es nicht. Zur <a href="/">Startseite</a>.</p></div></section>"""
    (OUT / "404.html").write_text(page("Nicht gefunden – Brom", nf, "Seite nicht gefunden."), encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    (OUT / "version.json").write_text(json.dumps(
        {"name": "Brom", "version": V, "characters": n_chars, "glyphs": n_glyphs,
         "license": "OFL-1.1", "download": "/" + dl(zip_name)}, ensure_ascii=False, indent=1) + "\n")
    (OUT / "latest/version.json").write_text(json.dumps(
        {"name": "Brom", "version": V, "css": "https://brom.trfx.de/latest/brom.css",
         "files": {"upright": "https://brom.trfx.de/latest/Brom-VF.woff2",
                   "italic": "https://brom.trfx.de/latest/Brom-Italic-VF.woff2",
                   "package": "https://brom.trfx.de/latest/Brom-latest.zip"}}, indent=1) + "\n")
    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"site/dist: {sum(1 for p in OUT.rglob('*') if p.is_file())} Dateien, {human(total)}; "
          f"{n_chars} Zeichen, ZIP {human(sizes[zip_name])}")


if __name__ == "__main__":
    build()
