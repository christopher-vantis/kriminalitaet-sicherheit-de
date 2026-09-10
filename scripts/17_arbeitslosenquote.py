#!/usr/bin/env python3
"""
17_arbeitslosenquote.py — Arbeitslosenquote je Bundesland (2025)
================================================================
Die amtliche Tabelle der Bundesagentur für Arbeit war nicht automatisiert
beschaffbar (die Download-Pfade antworten mit 404, GENESIS ist JavaScript-
basiert). Die Werte stammen daher aus dem Datenblatt von sozialpolitik-aktuell.de,
das die Statistik der Bundesagentur für Arbeit zitiert; sie wurden anhand der
Beschriftung der Abbildung Land für Land einzeln gelesen und gegengeprüft.

Kontrollen, die die Werte stützen:
  - Deutschland 6,3 % deckt sich exakt mit der Langzeitreihe des Statistischen
    Bundesamtes (lrarb002ga: 2 948 092 Arbeitslose, Quote 6,3 % für 2025).
  - Der in derselben Veröffentlichung genannte Wert "Bremen 11,0 %" betrifft die
    Stadt Bremen (Agenturbezirk), nicht das Land Bremen. Für das Land Bremen
    nennen IHK-Jahresbericht und Statistik übereinstimmend 11,5 %.

Bezugsgröße: Arbeitslosenquote bezogen auf alle zivilen Erwerbspersonen,
Jahresdurchschnitt 2025. Quelle der Zahlen: Statistik der Bundesagentur für
Arbeit (2026): Arbeitslose und Arbeitslosenquote, Tabellenblatt „Gesamt";
Stand der Bearbeitung 30.03.2026.

Ausgabe: ergänzt die Spalte alq_2025 in output/laender_indikatoren.csv
"""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDIKATOREN = ROOT / "output/laender_indikatoren.csv"
QUELLE_PDF = ROOT / "data/raw/arbeitsmarkt/arbeitslosenquoten_laender_2025.pdf"

# Jahresdurchschnitt 2025, in Prozent, bezogen auf alle zivilen Erwerbspersonen
ALQ_2025 = {
    "Baden-Württemberg": 4.6, "Bayern": 4.0, "Berlin": 10.3, "Brandenburg": 6.4,
    "Bremen": 11.5, "Hamburg": 8.3, "Hessen": 5.8, "Mecklenburg-Vorpommern": 8.0,
    "Niedersachsen": 6.1, "Nordrhein-Westfalen": 7.8, "Rheinland-Pfalz": 5.5,
    "Saarland": 7.4, "Sachsen": 6.9, "Sachsen-Anhalt": 8.0,
    "Schleswig-Holstein": 5.9, "Thüringen": 6.4,
}


def main():
    zeilen = list(csv.DictReader(open(INDIKATOREN, encoding="utf-8"), delimiter=";"))
    felder = list(zeilen[0].keys())
    if "alq_2025" not in felder:
        felder.append("alq_2025")
    fehlend = []
    for r in zeilen:
        wert = ALQ_2025.get(r["bundesland"])
        if wert is None:
            fehlend.append(r["bundesland"])
        r["alq_2025"] = wert if wert is not None else ""
    if fehlend:
        print("WARNUNG: kein Wert für:", ", ".join(fehlend))

    with open(INDIKATOREN, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=felder, delimiter=";")
        w.writeheader()
        w.writerows(zeilen)

    werte = sorted(ALQ_2025.items(), key=lambda kv: kv[1])
    print(f"-> {INDIKATOREN.name}: Spalte alq_2025 ergänzt ({len(ALQ_2025)} Länder)")
    print(f"niedrigste: {werte[0][0]} {werte[0][1]:.1f} % | "
          f"höchste: {werte[-1][0]} {werte[-1][1]:.1f} % | "
          f"Spanne {werte[-1][1] - werte[0][1]:.1f} PP")
    if QUELLE_PDF.exists():
        print(f"Quelldokument im Projekt: {QUELLE_PDF.relative_to(ROOT)}")
    else:
        print("Hinweis: Quelldokument nicht im Projekt hinterlegt")


if __name__ == "__main__":
    main()
