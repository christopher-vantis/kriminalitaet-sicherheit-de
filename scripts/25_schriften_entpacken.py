#!/usr/bin/env python3
"""
25_schriften_entpacken.py — Webfont-Schnitte als eigene Dateien ablegen
=======================================================================
build_app.py bettet die Schriften als data:-URL direkt in die HTML ein
(damit die App als Einzeldatei offline läuft). Die Übersichtsseite index.html
verlinkt sie dagegen als Datei — dafür müssen die Schnitte einzeln vorliegen.

Dieses Skript liest dashboard/fonts/plex.css, entpackt die base64-Inhalte und
schreibt sie als woff2-Dateien daneben.

Ausgabe: dashboard/fonts/plex-latin-{400,600,700}.woff2
"""
import base64
import pathlib
import re

F = pathlib.Path(__file__).resolve().parent.parent / "dashboard" / "fonts"


def main():
    css = (F / "plex.css").read_text(encoding="utf-8")
    treffer = re.findall(
        r"font-weight:(\d+);[^}]*?base64,([A-Za-z0-9+/=]+)\)", css)
    if not treffer:
        print("Keine eingebetteten Schnitte gefunden.")
        return
    for gewicht, b64 in treffer:
        daten = base64.b64decode(b64)
        ziel = F / f"plex-latin-{gewicht}.woff2"
        ziel.write_bytes(daten)
        print(f"  {ziel.name}: {len(daten)/1024:.0f} KB")
    print(f"\n{len(treffer)} Schnitte entpackt nach {F}")


if __name__ == "__main__":
    main()
