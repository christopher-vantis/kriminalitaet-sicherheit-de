#!/usr/bin/env python3
"""
wappen_util.py — Landeswappen für die Anzeige aufbereiten
=========================================================
Liest die SVG-Dateien aus dashboard/wappen/ und macht sie für die Einbettung in
die Seite nutzbar.

Wappen statt Flaggen: Die einfachen Streifenflaggen sind teils nicht
unterscheidbar — Nordrhein-Westfalens grün-weiß-rot gleicht der ungarischen
Flagge. Die Wappen sind die bekannteren Landeszeichen und eindeutig.

Zwei Dinge sind beim Aufbereiten entscheidend:

1. Feste Größenangaben (width/height) müssen weg, damit CSS die Darstellung
   steuert. Fehlt dabei eine viewBox, wird sie aus den ursprünglichen Maßen
   gebildet — sonst hat das SVG keinen Größenbezug und wird nicht gezeichnet.

2. Entfernt werden nur XML-Kopf, DOCTYPE, Kommentare und Editor-Metadaten,
   keine Gestaltungselemente. Die Wappen bestehen aus vielen Pfaden; würde man
   in sie hineinschreiben, bliebe das Wappen unvollständig.

Die Dateien stammen von Wikimedia Commons (amtliche Wappen, § 5 UrhG).
"""
import pathlib
import re

WAPPEN_PFAD = pathlib.Path(__file__).resolve().parent / "wappen"

KOPF = (
    (re.compile(r"<\?xml[^>]*\?>"), ""),
    (re.compile(r"<!DOCTYPE[^>]*>", re.I), ""),
    (re.compile(r"<!--.*?-->", re.S), ""),
    (re.compile(r"<metadata.*?</metadata>", re.S), ""),
)

METADATEN_ATTR = re.compile(
    r'\s+(?:inkscape|sodipodi):[\w-]+="[^"]*"'
    r'|\s+xmlns:(?:dc|cc|rdf|svg|inkscape|sodipodi)="[^"]*"')


def praefixe_ids(svg, praefix):
    """Hängt an jede interne ID eines SVGs den NUTS-Code an.

    Nötig, weil die Wappen-Dateien kurze IDs wie `a` bis `g` verwenden. Werden
    mehrere von ihnen in dasselbe Dokument eingebettet, kollidieren diese IDs:
    `<use href="#a">` greift dann auf das Element des zuerst eingefügten Wappens
    zu — Hessen zeigte so die Elemente Bayerns. Der Präfix macht jede ID
    eindeutig.

    Args:
        svg: das SVG-Markup einer Datei.
        praefix: eindeutiges Kürzel, hier der NUTS-Code.

    Returns:
        str: SVG mit eindeutigen IDs und angepassten Verweisen.
    """
    ids = sorted(set(re.findall(r'id="([^"]+)"', svg)), key=len, reverse=True)
    for kennung in ids:
        neu = f"{praefix}-{kennung}"
        svg = svg.replace(f'id="{kennung}"', f'id="{neu}"')
        svg = svg.replace(f'href="#{kennung}"', f'href="#{neu}"')
        svg = svg.replace(f'url(#{kennung})', f'url(#{neu})')
        svg = svg.replace(f"url('#{kennung}')", f"url('#{neu}')")
    return svg


def bereinige(text, praefix=""):
    """Setzt eine Wappen-Datei für die Einbettung instand.

    Returns:
        str: SVG ohne feste Größen, mit gültiger viewBox, oder "" bei Fehler.
    """
    for muster, ersatz in KOPF:
        text = muster.sub(ersatz, text, count=1)

    treffer = re.search(r"<svg\b([^>]*)>(.*)", text, re.S)
    if not treffer:
        return ""
    attrs, rumpf = treffer.group(1), treffer.group(2)

    def wert(name):
        m = re.search(name + r'="([^"]*)"', attrs)
        return m.group(1) if m else None

    breite, hoehe, viewbox = wert("width"), wert("height"), wert("viewBox")
    if not viewbox:
        b = re.sub(r"[^\d.]", "", breite or "") or "1000"
        h = re.sub(r"[^\d.]", "", hoehe or "") or "1000"
        viewbox = f"0 0 {b} {h}"

    rumpf = METADATEN_ATTR.sub("", rumpf)
    if praefix:
        rumpf = praefixe_ids(rumpf, praefix)
    rumpf = re.sub(r"\s+", " ", rumpf).strip()
    return (f'<svg class="wappen" viewBox="{viewbox}" '
            f'preserveAspectRatio="xMidYMid meet" aria-hidden="true" '
            f'xmlns="http://www.w3.org/2000/svg">{rumpf}</svg>')


def wappen_laden():
    """Liefert die aufbereiteten Wappen als Zuordnung NUTS-Code -> SVG."""
    ergebnis = {}
    if not WAPPEN_PFAD.exists():
        return ergebnis
    for datei in sorted(WAPPEN_PFAD.glob("*.svg")):
        roh = datei.read_text(encoding="utf-8", errors="replace")
        aufbereitet = bereinige(roh, praefix=datei.stem)
        if aufbereitet:
            ergebnis[datei.stem] = aufbereitet
    return ergebnis


if __name__ == "__main__":
    wappen = wappen_laden()
    print(f"{len(wappen)} Wappen aufbereitet\n")
    for code, svg in sorted(wappen.items()):
        vb = re.search(r'viewBox="([^"]+)"', svg)
        print(f"  {code}: {len(svg):>7d} Zeichen  viewBox={vb.group(1) if vb else '—'}")
