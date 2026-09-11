#!/usr/bin/env python3
"""
36_uebersetzungsstand.py — Was ist in der englischen Fassung noch deutsch?
==========================================================================
Vergleicht index.html und index-en.html: findet alle sichtbaren Textstellen,
die in beiden Fassungen gleich lauten und daher noch nicht übersetzt sind.

Ausgabe: Liste der offenen Stellen, gruppiert nach Länge.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard"

# Deutsche Funktionswörter — ein Text gilt als unübersetzt, wenn er sie enthält
# Nur Wörter, die im Englischen nicht vorkommen. Funktionswörter wie "in",
# "der" oder "die" wären Fehlalarme — englische Sätze enthalten sie ebenfalls.
DEUTSCH = re.compile(
    r"\b(und|oder|für|nicht|sind|wird|werden|wurde|haben|eine|einer|einem|eines|"
    r"auch|aber|sich|dass|wenn|durch|kann|können|muss|müssen|"
    r"Anteil|Jahre|Fälle|Bundesland|Bundesländer|Straftat|Straftaten|"
    r"aufgeklärt|Verurteilung|Bevölkerung|Einwohner|registrierte|"
    r"Phänomenbereich|Gesamtaufkommen|Anzeigequote|Körperverletzung|"
    r"Halluzination)\b")


def textstellen(html):
    """Sichtbare Textknoten aus dem HTML ziehen (ohne Code und Stile).

    Wichtig: Der Plotly-Code ist mehrere hundert Kilobyte groß und enthält
    deutsche Wörter als Variablennamen. Er wird zuerst entfernt — über die
    Länge der Blöcke, nicht über den Inhalt, damit kein Text verloren geht.
    """
    # Alles zwischen <script> und </script> entfernen (auch sehr lange Blöcke)
    t = re.sub(r"<script\b[^>]*>.*?</script\s*>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<style\b[^>]*>.*?</style\s*>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<svg\b.*?</svg\s*>", " ", t, flags=re.S | re.I)
    roh = re.sub(r"<[^>]+>", "\n", t)
    stellen = []
    for z in roh.split("\n"):
        z = " ".join(z.split())
        # Code-Fragmente ausschließen: sie enthalten Klammern oder Semikola
        if len(z) > 12 and not any(k in z for k in (";", "{", "}", "=>", "function")):
            stellen.append(z)
    return stellen


def main():
    de = (D / "index.html").read_text(encoding="utf-8")
    en = (D / "index-en.html").read_text(encoding="utf-8")
    if not (D / "index-en.html").exists():
        print("Englische Fassung fehlt")
        return 1

    de_stellen = {s for s in textstellen(de)}
    en_stellen = {s for s in textstellen(en)}

    # In der englischen Fassung noch deutsch?
    offen = sorted(s for s in en_stellen if DEUTSCH.search(s))

    print(f"Textstellen deutsch: {len(de_stellen)}")
    print(f"Textstellen englisch: {len(en_stellen)}")
    print(f"In der englischen Fassung noch deutsch: {len(offen)}\n")

    for s in offen:
        print(f"  [{len(s):>4} Z.] {s[:150]}")

    # Auch die Diagramm-Metadaten prüfen
    print("\n--- Diagramme ---")
    for fassung, name in ((de, "deutsch"), (en, "englisch")):
        m = re.search(r'id="figmeta" type="application/json">(.*?)</script>', fassung, re.S)
        meta = json.loads(m.group(1))
        offene = [x["id"] for x in meta
                  if DEUTSCH.search((x.get("unter") or "") + (x.get("langtext") or "")
                                    + (x.get("quelle") or ""))]
        print(f"  {name}: {len(offene)} Diagramme mit deutschen Texten — {offene}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
