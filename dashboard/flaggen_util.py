#!/usr/bin/env python3
"""
flaggen_util.py — Landesflaggen für die Anzeige aufbereiten
===========================================================
Liest die SVG-Dateien aus dashboard/flaggen/ und macht sie für die Einbettung
in die Seite nutzbar.

Zwei Dinge sind dabei entscheidend:

1. Feste Größenangaben (width/height) müssen weg, damit CSS die Darstellung
   steuert. Dabei darf aber keine Datei ohne Größenbezug zurückbleiben: Fehlt
   eine viewBox, wird sie aus den ursprünglichen Angaben gebildet. Ohne diesen
   Schritt zeichnet der Browser die Flagge nicht (weißes oder schwarzes Feld).

2. Entfernt werden nur XML-Kopf, DOCTYPE, Kommentare und Editor-Metadaten —
   keine Gestaltungselemente. Bei der bayerischen Flagge etwa liegen die Rauten
   in einem <pattern>; würde man dort hineinschreiben, bliebe die Flagge leer.

Die Dateien stammen von Wikimedia Commons (amtliche Werke, § 5 UrhG).
"""
import pathlib
import re

FLAGGEN_PFAD = pathlib.Path(__file__).resolve().parent / "flaggen"

KOPF = (
    (re.compile(r"<\?xml[^>]*\?>"), ""),
    (re.compile(r"<!DOCTYPE[^>]*>", re.I), ""),
    (re.compile(r"<!--.*?-->", re.S), ""),
    (re.compile(r"<metadata.*?</metadata>", re.S), ""),
)

# Attribute, die nur Ballast sind (Editor-Spuren)
METADATEN_ATTR = re.compile(
    r'\s+(?:inkscape|sodipodi):[\w-]+="[^"]*"'
    r'|\s+xmlns:(?:dc|cc|rdf|svg|inkscape|sodipodi)="[^"]*"')


def _svg_kopf(text):
    """Zerlegt den öffnenden svg-Tag und liefert (Attribute, Rumpf)."""
    treffer = re.search(r"<svg\b([^>]*)>(.*)", text, re.S)
    if not treffer:
        return None, None
    return treffer.group(1), treffer.group(2)


def _attribut(attrs, name):
    treffer = re.search(name + r'="([^"]*)"', attrs)
    return treffer.group(1) if treffer else None


def bereinige(text):
    """Setzt eine Flaggen-Datei für die Einbettung instand.

    Returns:
        str: SVG ohne feste Größen, mit gültiger viewBox und Klasse, oder ""
             wenn sich die Datei nicht auswerten lässt.
    """
    for muster, ersatz in KOPF:
        text = muster.sub(ersatz, text, count=1)
    attrs, rumpf = _svg_kopf(text)
    if attrs is None:
        return ""

    breite, hoehe = _attribut(attrs, "width"), _attribut(attrs, "height")
    viewbox = _attribut(attrs, "viewBox")

    # Fehlt die viewBox, aus den ursprünglichen Maßen bilden — sonst hat das
    # SVG nach dem Entfernen von width/height keinerlei Größenbezug.
    if not viewbox:
        if breite and hoehe:
            b = re.sub(r"[^\d.]", "", breite) or "1000"
            h = re.sub(r"[^\d.]", "", hoehe) or "600"
            viewbox = f"0 0 {b} {h}"
        else:
            viewbox = "0 0 1000 600"

    rumpf = METADATEN_ATTR.sub("", rumpf)
    rumpf = re.sub(r"\s+", " ", rumpf).strip()
    return (f'<svg class="flagge" viewBox="{viewbox}" '
            f'preserveAspectRatio="none" aria-hidden="true" '
            f'xmlns="http://www.w3.org/2000/svg">{rumpf}</svg>')


def flaggen_laden():
    """Liefert die aufbereiteten Flaggen als Zuordnung NUTS-Code -> SVG."""
    ergebnis = {}
    if not FLAGGEN_PFAD.exists():
        return ergebnis
    for datei in sorted(FLAGGEN_PFAD.glob("*.svg")):
        roh = datei.read_text(encoding="utf-8", errors="replace")
        aufbereitet = bereinige(roh)
        if aufbereitet:
            ergebnis[datei.stem] = aufbereitet
    return ergebnis


if __name__ == "__main__":
    for code, svg in sorted(flaggen_laden().items()):
        hat_viewbox = 'viewBox="' in svg
        print(f"  {code}: {len(svg):>7d} Zeichen | viewBox: {hat_viewbox} "
              f"| Inhalt: {len(svg) > 200}")
