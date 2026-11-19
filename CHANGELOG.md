# Änderungsprotokoll – Brom

## [0.3.5] – 2026-11-19

### Korrigiert
- **Punkt auf i, j, ï und fi zu hoch:** In den fetten Gewichten stand der Punkt weit über der Oberlänge von l, k und f (Bold 70, Black 106 Einheiten; Geist 12–20, Inter 24–56). Ursache waren die zu Stammbreite vergrößerten quadratischen Punkte, die nach oben wachsen, plus der Zuschlag aus 0.3.4. Die Oberkante des Punkts ist jetzt auf Oberlänge + 30 % der Punktgröße begrenzt (Bold +39, Black +55, Regular und leichter unverändert). ï steht dadurch genauso hoch wie i. Der Abstand zwischen Punkt und Stamm bleibt in Regular wie in 0.3.4 und schrumpft nur dort, wo er sonst zu hoch geworden wäre (Bold 66 statt 98, Black 43 statt 94 Einheiten).

## [0.3.4] – 2026-11-16

### Korrigiert
- **Ausrufezeichen:** Balken und Punkt von ! und ¡ sind jetzt genau gleich breit und liegen exakt übereinander (vorher war der Punkt breiter als der Balken, Regular 113 gegen 86 Einheiten, und saß um bis zu 3 Einheiten daneben). Der Punkt bleibt, der Balken wird so breit wie er. Gilt in allen Gewichten, aufrecht und kursiv, auch für ‼ und die ss08-Variante mit rundem Punkt. In Thin ist der Balken dadurch dicker als der Stamm der übrigen Buchstaben.

### Geändert
- **Mehr Platz zwischen Punkt und Strich** bei i, j, ï und allen Zeichen mit Punkt auf i/j (ĳ, ị, į, kyrillisch і ј ї, fi u. a.), bei ! ¡ ? ¿ und ‼: Der Abstand wächst um 20 % der Punktbreite (Thin +10, Regular +19–23, Black +37 Einheiten), damit er in jedem Gewicht mitwächst. Bei i, j und ï steigt der Punkt, bei ! und ? bleiben Grundlinie und Versalhöhe stehen und der Strich beginnt entsprechend höher bzw. endet bei ¡ ¿ tiefer. Breite, Laufweite und Kerning ändern sich nicht. Nicht betroffen: ‽, ; und die Punkte über anderen Buchstaben (ä, ċ …).

## [0.3.3] – 2026-11-16

### Korrigiert
- **Punkte schmaler als der Stamm:** In den fetten Gewichten (ab etwa 530) war der Punkt auf dem i schmaler als der Stamm darunter (Black: Punkt 158, Stamm 183 Einheiten). Der Punkt ist jetzt in jedem Gewicht mindestens so breit wie der Stamm (Black: 183 × 183, bei Regular und leichter bleibt alles wie vorher, dort war der Punkt schon breiter). Die Unterkante und damit der Abstand zum Stamm bleiben, der Punkt wächst nach oben. Betrifft alle Zeichen mit Punkt: i, j, ï, í, ì, î, ĩ, ị, ĳ, kyrillisch і ї ј, alle Umlaute und Punktakzente (ä ö ü ë ė ż ġ …), Punkt, Doppelpunkt, Semikolon, Ausrufe- und Fragezeichen, Mittelpunkt u. a.
- **Runde Punkte (ss08)** und die Punkte der griechischen Dieresis-Tonos-Akzente (ΐ …): Dasselbe, sie sind nur dann vergrößert, wenn sie schmaler als der Stamm waren (nur Black und die schweren Gewichte).

- **Ausrufezeichen:** Der Balken von ! und ¡ lief zum Punkt hin auf etwa 65 % seiner Breite zusammen. Jetzt hat er von oben bis unten dieselbe Dicke, wie ein umgedrehtes i (Regular 86 Einheiten, Black 184). Gilt in allen Gewichten, aufrecht und kursiv, auch für ‼ ⁈ ⁉ ¿-Kombinationen mit Ausrufezeichen und die ss08-Variante.

## [0.3.2] – 2026-11-16

### Geändert
- **Element-Kachel:** „Br“ steht jetzt in voller Größe auf der Grundlinie, genauso groß wie die folgenden Buchstaben („Brom“). Früher war es auf 60 % verkleinert. Die Kachel wächst entsprechend mit (Innenabstand links und rechts fest, die Höhe ergibt sich aus dem Quadrat). Sie ist damit deutlich größer als bisher und ragt über und unter die Zeile hinaus. Gilt für alle Gewichte, aufrecht und kursiv. In Black reicht sie nach unten nicht tiefer als die tiefsten übrigen Zeichen der Schrift.

### Korrigiert
- **Kerning:** Beim Übernehmen von Inters Kerning entschied bisher der Zufall der Python-Hash-Reihenfolge, welches Paar gewann, wenn mehrere auf dasselbe Brom-Paar fielen. Jetzt gilt das spezifischste Paar (Glyph vor Gruppe), sonst alphabetisch, Builds sind reproduzierbar. Betroffen sind einzelne Paare mit Griechisch und Kyrillisch (z. B. γ vor Komma und Punkt, ҵ vor v w y), höchstens 5 Einheiten Unterschied.

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
