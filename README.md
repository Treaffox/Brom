# Brom

> **THIS FONT IS VIBE CODED USING CLAUDE CODE**

Technische, eckige Sans für Interfaces und Technik. Modern, sachlich, ruhig,
mit superelliptischen Rundungen. Gewichte von 100 bis 900, aufrecht und kursiv,
über 2100 Zeichen. Website und Testseite: https://brom.trfx.de

Version und Änderungen: `VERSION`, `CHANGELOG.md`. Lizenz: SIL Open Font
License 1.1 (`LICENSE`), Reserved Font Name „Brom“.

## Dateien

Im Download-Paket liegen die Ordner direkt im Hauptverzeichnis, im
Quell-Repository unter `fonts/`.

| Ordner | Inhalt |
|---|---|
| `variable/` | `Brom[wght].ttf`, `Brom-Italic[wght].ttf`: eine Datei je Stil, alle Gewichte |
| `otf/` | 18 statische Schnitte (Desktop, Druck) |
| `ttf/` | 18 statische Schnitte, gehintet (Windows, kleine Größen) |
| `webfonts/` | WOFF2 der Variable Fonts und der statischen Schnitte |

## Im Web einbinden

```css
@font-face {
  font-family: "Brom";
  src: url("Brom[wght].woff2") format("woff2");
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Brom";
  src: url("Brom-Italic[wght].woff2") format("woff2");
  font-weight: 100 900;
  font-style: italic;
  font-display: swap;
}
body { font-family: "Brom", system-ui, sans-serif; }
```

## OpenType-Features

| Feature | Wirkung |
|---|---|
| `dlig` | `[Br]` wird zur Element-Kachel |
| `ss01` | a ohne Fuß |
| `ss02` | einstöckiges a |
| `ss03` | l ohne Fuß |
| `ss04` | R mit schrägem Bein |
| `ss05` | I mit Serifen |
| `ss06` | alternatives G |
| `ss07` | schlanke Pfeile |
| `ss08` | runde statt eckiger Punkte (i, j, Satzzeichen, Akzente) |
| `ss09` | 0 mit Schrägstrich, 1 mit Fuß |
| `ss10` | dekorative Klammerformen (gefüllt, eckig, gewinkelt) |
| `tnum` / `pnum` | Ziffern mit fester bzw. proportionaler Breite |
| `frac`, `sups`, `subs`, `numr`, `dnom`, `ordn`, `case` | Brüche, hoch-/tiefgestellt, Ordinalzeichen, Satzzeichen für Versalien |

## Selbst bauen

Im Quell-Repository. Die Quellen werden aus Geist und Inter abgeleitet
(`tools/prepare.py`) und mit fontmake gebaut. Gebraucht werden Python 3.12 und Git.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sh tools/fetch_upstream.sh           # Geist und Inter in dem Stand, auf dem Brom aufbaut, als UFO → work/
.venv/bin/python tools/build.py      # prepare + fontmake + Hinting + WOFF2 → dist/
.venv/bin/python tools/check.py      # Prüfungen
```

Die Gestaltungsparameter (Rundung, Laufweite, Gewicht von Black) stehen in
`tools/brom/config.py`. Die Website entsteht mit `tools/site.py` in
`site/dist`. Ihre Browsertests in `site/scripts` brauchen Node.js und
`npm install` in `site/`.

## Herkunft und Dank

Brom baut auf zwei freien Schriften auf, beide unter der OFL 1.1:
**Geist** von Vercel und basement.studio (Grundformen, Metriken, Stilsets) und
**Inter** von Rasmus Andersson (Griechisch, Kyrillisch und weitere Zeichen).
Die gestrafften Bögen sind von **IBM Plex Sans** inspiriert.
