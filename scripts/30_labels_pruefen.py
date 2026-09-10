#!/usr/bin/env python3
"""
30_labels_pruefen.py — Passen die Landesnamen in ihre Fläche?
=============================================================
Rechnet für jedes Bundesland die Ausdehnung im Kartenraster aus und vergleicht
sie mit der Breite der Beschriftung. Die Textbreite wird geschätzt: bei IBM Plex
Sans entspricht ein Zeichen im Schnitt etwa 0,52 der Schriftgröße. Die Schätzung
dient dem Aufspüren von Ausreißern, nicht der Gestaltung.

Ausgabe: Liste der Länder, bei denen die Beschriftung breiter ist als das Land.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHRIFTGROESSE = 23          # muss zum CSS in build_app.py passen
ZEICHENBREITE = 0.52         # grobe Schätzung für IBM Plex Sans

# Stadtstaaten: Ihr Name steht absichtlich neben der Fläche an einer
# Führungslinie, weil das Gebiet selbst zu klein für eine Beschriftung ist.
# Die Flächenbreite ist deshalb kein Maßstab.
STADTSTAATEN = {"DE3", "DE5", "DE6"}


def ausdehnung(pfad_daten):
    """Liefert (breite, hoehe) eines SVG-Pfads aus seinen Koordinaten."""
    zahlen = [float(x) for x in re.findall(r"-?\d+\.?\d*", pfad_daten)]
    xs, ys = zahlen[0::2], zahlen[1::2]
    if not xs or not ys:
        return 0.0, 0.0
    return max(xs) - min(xs), max(ys) - min(ys)


def labels_lesen(html):
    """Liest die Beschriftungen mit Position und Inhalt aus dem HTML."""
    ergebnis = []
    for treffer in re.finditer(
            r'<text class="kl" data-nuts="(\w+)"[^>]*>(.*?)</text>', html, re.S):
        nuts, inhalt = treffer.group(1), treffer.group(2)
        zeilen = re.findall(r">([^<>]+)<", inhalt) or [inhalt]
        zeilen = [z.strip() for z in zeilen if z.strip()]
        ergebnis.append({"nuts": nuts, "zeilen": zeilen})
    return ergebnis


def main():
    html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
    pfade = re.findall(r'<path class="bl" id="p-(\w+)"[^>]*d="([^"]+)"', html)
    labels = labels_lesen(html)

    # Landbreite je NUTS-Code
    breiten = {}
    for nuts, d in pfade:
        zahlen = [float(x) for x in re.findall(r"-?\d+\.?\d*", d)]
        xs = zahlen[0::2]
        breiten[nuts] = max(xs) - min(xs) if xs else 0.0

    print(f"{'Beschriftung':<26} {'Landbreite':>11} {'Textbreite':>11}  Bewertung")
    print("-" * 68)
    auffaellig = []
    for lab in labels:
        nuts = lab["nuts"]
        breite = breiten.get(nuts, 0.0)
        laengste = max(len(z) for z in lab["zeilen"])
        text = " / ".join(lab["zeilen"])
        textbreite = laengste * SCHRIFTGROESSE * ZEICHENBREITE
        verhaeltnis = textbreite / breite if breite else 99
        if nuts in STADTSTAATEN:
            bewertung = "außerhalb (Stadtstaat)"
        elif verhaeltnis > 1.0:
            bewertung = "ZU BREIT"
            auffaellig.append((text, nuts, breite, textbreite, verhaeltnis))
        elif verhaeltnis > 0.85:
            bewertung = "knapp"
        else:
            bewertung = "passt"
        print(f"{text:<26} {breite:>11.0f} {textbreite:>11.0f}  {bewertung} "
              f"({verhaeltnis*100:.0f} %)")

    print()
    if auffaellig:
        print(f"{len(auffaellig)} Beschriftung(en) breiter als ihr Land:")
        for text, nuts, b, t, v in sorted(auffaellig, key=lambda r: -r[4]):
            print(f"  {text} ({nuts}): Text {t:.0f} px gegen Land {b:.0f} px → {v*100:.0f} %")
    else:
        print("Alle Beschriftungen passen in die Fläche ihres Landes.")


if __name__ == "__main__":
    main()
