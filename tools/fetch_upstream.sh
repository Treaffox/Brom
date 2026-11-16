#!/bin/sh
# Holt die Vorlagen von Brom in genau dem Stand, auf dem die Schrift aufbaut,
# und wandelt sie mit glyphs2ufo (aus glyphsLib, siehe requirements.txt) in UFOs um.
#   sh tools/fetch_upstream.sh
# Ergebnis: upstream/geist, upstream/inter (Git), work/geist-ufo, work/inter-ufo (UFO)
set -eu
cd "$(dirname "$0")/.."
GLYPHS2UFO="${GLYPHS2UFO:-.venv/bin/glyphs2ufo}"

fetch() {  # Ziel, Repository, Commit
  if [ -d "$1/.git" ] && [ "$(git -C "$1" rev-parse HEAD)" = "$3" ]; then
    echo "$1: schon auf $3"; return
  fi
  rm -rf "$1"; mkdir -p "$1"
  git -C "$1" init -q
  git -C "$1" remote add origin "$2"
  git -C "$1" fetch -q --depth 1 origin "$3"
  git -C "$1" checkout -q FETCH_HEAD
  echo "$1: $2 @ $3"
}

# Geist (Vercel und basement.studio, OFL 1.1), Tag v1.9.2
fetch upstream/geist https://github.com/vercel/geist-font.git ef2597cfc42f4797676df105517ccc0a1cfa6569
# Inter (The Inter Project Authors, OFL 1.1)
fetch upstream/inter https://github.com/rsms/inter.git 353b61b9f4430d5f420d56605a6e7993e0941470

rm -rf work/geist-ufo work/inter-ufo
mkdir -p work/geist-ufo work/inter-ufo
for s in Geist Geist-Italic; do
  "$GLYPHS2UFO" -m "work/geist-ufo/$s" "upstream/geist/sources/$s.glyphspackage"
done
# Inter nur mit --minimal (sonst Abbruch wegen doppelter Ebenennamen)
for s in Inter-Roman Inter-Italic; do
  "$GLYPHS2UFO" --minimal -m "work/inter-ufo/$s" "upstream/inter/src/$s.glyphspackage"
done
echo "Vorlagen bereit."
