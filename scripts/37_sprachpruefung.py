#!/usr/bin/env python3
"""
37_sprachpruefung.py — Vollständige Prüfung der englischen Fassung
==================================================================
Prüft alle Teile der Seite auf deutsche Reste und auf Mischtexte (halbe
Übersetzungen, wie sie durch wortweises Ersetzen entstehen):
  1. sichtbare Textknoten im HTML
  2. Diagramm-Metadaten (Titel, Kurztexte, Quellen, Langtexte)
  3. Achsen- und LegendenteXte in den Plotly-Figuren
  4. Einordnungstexte und Datenblock

Ausgabe: Befund je Prüfbereich, Exit-Code 1 bei Resten.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard"

# Wörter, die es im Englischen nicht gibt — sichere Anzeichen für Deutsch.
DEUTSCHE_WOERTER = re.compile(
    r"\b(und|oder|für|nicht|sind|wird|werden|wurde|haben|eine|einer|einem|eines|"
    r"auch|aber|sich|dass|wenn|durch|kann|können|muss|müssen|über|zwischen|"
    r"Anteil|Jahre|Fällen|Fälle|Bundesland|Bundesländer|Bundesländern|Straftat|"
    r"Straftaten|aufgeklärt|Verurteilung|Verurteilungen|Bevölkerung|Einwohner|"
    r"Einwohnern|registrierte|registrierten|Phänomenbereich|Gesamtaufkommen|"
    r"Anzeigequote|Körperverletzung|Belastung|Belastbarkeit|Unsicherheitsgefühl|"
    r"Anzeige|Anzeigen|Stadtstaaten|Flächenländer|Migrationshintergrund|"
    r"Verengung|Selektion|Wertschöpfung|Lebenshaltungskosten|Fallzahlen|"
    r"gepoolt|Wellen|Intervalle|ausgewiesen|Dreifache|vorn|liegen|liegt|"
    r"niedrigste|höchste|niedrig|hoch|Häufigkeitszahl|Kriminalitätsbelastung)\b",
    re.I)

BEREICHE = {}


def pruefe(name, text):
    treffer = DEUTSCHE_WOERTER.findall(text or "")
    BEREICHE[name] = sorted(set(t.lower() for t in treffer))
    return not treffer


def main():
    if not (D / "index-en.html").exists():
        print("index-en.html fehlt — zuerst bauen")
        return 1
    h = (D / "index-en.html").read_text(encoding="utf-8")

    # 1) Sichtbare Textknoten
    t = re.sub(r"<script\b[^>]*>.*?</script\s*>", " ", h, flags=re.S | re.I)
    t = re.sub(r"<style\b[^>]*>.*?</style\s*>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<svg\b.*?</svg\s*>", " ", t, flags=re.S | re.I)
    pruefe("sichtbare Texte", re.sub(r"<[^>]+>", " ", t))

    # 2) Metadaten
    m = re.search(r'id="figmeta" type="application/json">(.*?)</script>', h, re.S)
    meta = json.loads(m.group(1))
    pruefe("Diagramm-Metadaten", json.dumps(meta, ensure_ascii=False))

    # 3) Figuren (Achsen, Legenden)
    m = re.search(r'id="figuren" type="application/json">(.*?)</script>', h, re.S)
    pruefe("Achsen und Legenden", json.dumps(json.loads(m.group(1)), ensure_ascii=False))

    # 4) Datenblock (Einordnungstexte)
    m = re.search(r'id="daten" type="application/json">(.*?)</script>', h, re.S)
    daten = json.loads(m.group(1))
    pruefe("Einordnungstexte", json.dumps(daten.get("texte_start", {}), ensure_ascii=False))

    print("Prüfung der englischen Fassung\n" + "=" * 46)
    offen = 0
    for name, reste in BEREICHE.items():
        if reste:
            offen += 1
            print(f"  {name}: {len(reste)} deutsche Wörter — {reste[:8]}")
        else:
            print(f"  {name}: keine deutschen Reste")

    # Mischtext-Heuristik: deutsche Wörter, die in englischem Satz stehen
    print("\nMischtexte (halbe Übersetzungen) sind an deutschen Funktionswörtern"
          "\nin englischen Sätzen erkennbar — die Prüfung oben deckt das ab.")

    print("\nErgebnis:", "englische Fassung vollständig" if not offen
          else f"{offen} Bereiche mit Resten")
    return 1 if offen else 0


if __name__ == "__main__":
    raise SystemExit(main())
