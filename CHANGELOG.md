# Änderungsprotokoll – Brom

Alle nennenswerten Änderungen an der Schrift stehen hier. Versionen folgen
[Semantic Versioning](https://semver.org/lang/de/): MAJOR für Änderungen, die
Satz oder Laufweite bestehender Texte sichtbar verschieben, MINOR für neue
Zeichen und Funktionen, PATCH für Korrekturen.

## [0.3.1] – 2026-11-13

### Korrigiert
- **y:** Die linke Diagonale endete knapp über der Grundlinie mit einer kleinen waagrechten Stufe, bevor die Unterlänge anschloss. Das sah wie ein sichtbares Ende aus. Jetzt läuft sie ohne Absatz in die Unterlänge, in allen Gewichten und kursiv. Gilt auch für ý ÿ ŷ ỳ ỹ, das kyrillische у und alle weiteren Zeichen, die auf dem y aufbauen.

## [0.3.0] – 2026-11-13

### Geändert
- **Neuer Name: Brom.** Die Familie heißt in allen Metadaten nur noch „Brom“ statt „TRFX Brom“, die Dateien `Brom[wght].ttf`, `Brom-Regular.otf` usw., die PostScript-Namen `Brom-Regular` usw. TRFX bleibt Hersteller und Designer. **Wer die Schrift schon eingebunden hat, muss `font-family` auf `"Brom"` umstellen.**
- An den Formen ändert sich gegenüber 0.2.0 nichts.

## [0.2.0] – 2026-11-13

### Geändert
- **Quadratische Punkte:** Die Punkte auf i, j, Umlauten und Akzenten sowie Punkt, Doppelpunkt, Semikolon, Ausrufe- und Fragezeichen sind in allen Gewichten exakte Quadrate. Bei Geist waren sie in Thin hoch und in Black flach. Die Fläche bleibt gleich, der Abstand zum Stamm bzw. zur Grundlinie auch.
- **Echte Spitzen:** « » ‹ › < > ≤ ≥ und ^ laufen in eine Spitze statt in eine abgeschnittene Kante, außen wie innen. Größe, Dickte und Laufweite der Zeichen bleiben gleich.
- **Element-Kachel:** zeigt nur noch „Br“, ohne Ordnungszahl, optisch mittig und etwas größer.

### Entfernt
- Codepoint U+E035 (privater Bereich) für die Element-Kachel. Sie ist nur noch über `dlig` mit der Folge `[Br]` erreichbar.

### Neu
- **Hinting:** Die statischen TTF (und deren WOFF2) sind mit ttfautohint gehintet. Unter Windows und bei kleinen Größen von 8 bis 48 px laufen Buchstaben und Abstände gleichmäßiger. Die Variable Fonts und die OTF bleiben ungehintet.
- **Kerning für Griechisch und weitere Zeichen:** Übernommene Zeichen kernen jetzt wie ihr lateinisches Vorbild nach Inters Gruppierung, zum Beispiel Γ wie T oder Ο wie O (rund 640 Zeichen je Seite). Rein griechische Formen ohne Vorbild bekommen Inters eigenes Kerning, auf Brom skaliert (ΤΩ, Ω und weitere). Lateinisches und kyrillisches Kerning bleibt unverändert.
- Griechisch (`grek`) und Kyrillisch (`cyrl`) sind als Schriftsysteme angemeldet. Kerning und Akzentpositionierung hängen dort nicht mehr vom Fallback der Anwendung ab.

### Korrigiert
- **Knicke und unruhige Kanten bei großen Größen:** Die Straffung der Rundungen griff auch an Übergängen von Bögen in Stämme (oben an b, d, h, unten an a, g) und an schräg auslaufenden Strichenden. Dort entstanden kleine Knicke, die Schrift wirkte wie von Hand gezeichnet. Jetzt werden nur echte Viertelbögen gestrafft, deren beide Enden waagrecht bzw. senkrecht laufen. Übergänge behalten die Form von Geist.
- Innen- und Außenformen werden fast gleich stark gestrafft. Dadurch werden die Ecken der Bögen nicht mehr dünner als der übrige Strich.
- In 0.1.0 stand unter „Bekannte Einschränkungen“, Inters Sonderregeln für Griechisch und Kyrillisch seien noch nicht übernommen. Inter hat solche Regeln nicht. Seine `locl`-Regeln gelten nur Rumänisch und Katalanisch, und die hat Brom über Geist.

## [0.1.0] – 2026-11-13

Erste Version.

### Neu
- Familie **TRFX Brom** mit Gewichtsachse `wght` von 100 (Thin) bis 900 (Black), aufrecht und kursiv (12°).
- Formate: Variable Fonts (TTF), 18 statische Schnitte als OTF und TTF, WOFF2 für das Web.
- **Superelliptische Rundungen:** Bögen sind zur Ecke hin gestrafft, wie ein abgerundetes Rechteck. Punzen werden stärker gestrafft als Außenformen, damit sie offen bleiben.
- **Lesbare fette Schnitte:** Black ist leichter als bei Geist (90 % des Weges von Regular zu Black) und läuft weiter (+22 Einheiten). Dazwischen wird interpoliert.
- **Element-Glyph [Br]:** Kachel wie im Periodensystem mit Ordnungszahl 35. Über die Folge `[Br]` mit `dlig` oder direkt über U+E035.
- **Großer Zeichensatz:** 2131 Zeichen, unter anderem Latein erweitert (inklusive Vietnamesisch), Kyrillisch, Griechisch inklusive Polytonisch, IPA, Währungen, Pfeile, Mathematik und technische Symbole.
- Stilsets aus Geist: ss01–ss10 (Alternativen für a, l, R, I, G, Pfeile, runde Punkte, Ziffern, Klammern), dazu `tnum`, `pnum`, `frac`, `sups`, `subs`, `case`, `ordn`, `locl`.
- Stapelanker für Akzente: Kombinierende Diakritika lassen sich übereinander setzen.

### Herkunft
- Basis ist **Geist** (Vercel, OFL 1.1). **Inter** (rsms, OFL 1.1) ergänzt die Zeichen, die Geist fehlen. Diese sind auf Geists Stammstärke, x-Höhe und Neigung angeglichen.
- Die gestrafften Rundungen sind von **IBM Plex Sans** inspiriert. Outlines aus Plex sind nicht enthalten.

### Entfernt gegenüber Geist
- Apple-Logo (U+F8FF, fremde Marke) und das Vercel-Stilset ss11 („Contextual brand styles“).
- Unfertige, nicht exportierte Glyphen aus Geist. Ezh, ⏎ und weitere Steuerzeichen-Symbole kommen dafür aus Inter.

### Bekannte Einschränkungen
- Keine Hinting-Daten. Bei sehr kleinen Größen unter Windows kann die Darstellung weicher wirken.
- Die aus Inter übernommenen Zeichen haben die gestrafften Rundungen, aber Inters Grundformen. Kerning bekommen nur griechische und kyrillische Doppelgänger lateinischer Buchstaben (Α = A).
- Inters Features für griechische und kyrillische Sonderfälle (zum Beispiel `case` für Tonos) sind noch nicht übernommen.
