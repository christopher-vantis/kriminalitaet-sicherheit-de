#!/usr/bin/env python3
"""
40_uebersetzungsluecken.py — Fehlende Einträge in der Übersetzungstabelle
========================================================================
Vergleicht die deutschen Seiten mit ihren englischen Fassungen und listet die
Textstellen, die dort noch deutsch sind. Damit lässt sich die Tabelle gezielt
ergänzen, statt Mischtexte (halbe Übersetzungen) zu erzeugen.

Aufruf:  python3 scripts/40_uebersetzungsluecken.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DASH = ROOT / "dashboard"

PAARE = [("index.html", "index-en.html"),
         ("deutschland.html", "deutschland-en.html"),
         ("schweiz.html", "schweiz-en.html")]

# Wörter, die im Englischen nicht vorkommen
DEUTSCH = re.compile(
    r"\b(und|oder|für|nicht|sind|wird|werden|wurde|haben|eine|einer|einem|eines|"
    r"auch|aber|sich|dass|wenn|durch|kann|können|muss|müssen|über|zwischen|"
    r"Anteil|Jahre|Fälle|Bundesland|Bundesländer|Straftat|Straftaten|"
    r"aufgeklärt|Verurteilung|Bevölkerung|Einwohner|registrierte|Kriminalität|"
    r"Angst|Schweiz|Kantone|Kanton|Furcht|Sicherheitsgefühl|Strafverfolgung|"
    r"Karte|Startseite|Datengrundlage|Methoden|Quellen|Grenzen)\b")


def sichtbar(html):
    """Sichtbare Textknoten ohne Skripte, Stile und SVG."""
    t = re.sub(r"<script\b[^>]*>.*?</script\s*>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<style\b[^>]*>.*?</style\s*>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<svg\b.*?</svg\s*>", " ", t, flags=re.S | re.I)
    roh = re.sub(r"<[^>]+>", "\n", t)
    stellen = []
    for z in roh.split("\n"):
        z = " ".join(z.split())
        if len(z) > 10 and not any(k in z for k in (";", "{", "}", "=>", "function")):
            stellen.append(z)
    return stellen


def main():
    tabelle = json.loads((DASH / "sprachtexte.json").read_text(encoding="utf-8")).get("en", {})
    schluessel = {" ".join(k.split()) for k in tabelle}
    print(f"Tabelle: {len(schluessel)} Einträge\n")

    for de_name, en_name in PAARE:
        de_pfad, en_pfad = DASH / de_name, DASH / en_name
        if not (de_pfad.exists() and en_pfad.exists()):
            print(f"{de_name}: fehlt — übersprungen\n")
            continue
        en_html = en_pfad.read_text(encoding="utf-8")
        offen = []
        for stelle in sichtbar(en_html):
            if DEUTSCH.search(stelle) and stelle not in schluessel:
                offen.append(stelle)
        print(f"=== {en_name}: {len(offen)} offene Stelle(n) ===")
        for s in offen[:14]:
            print(f"  [{len(s):>4}] {s[:150]}")
        if len(offen) > 14:
            print(f"  … und {len(offen)-14} weitere")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
