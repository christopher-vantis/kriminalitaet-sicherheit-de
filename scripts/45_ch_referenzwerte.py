#!/usr/bin/env python3
"""
45_ch_referenzwerte.py — Furcht- und Opferwerte der Schweiz als tidy CSV
=======================================================================
Trägt die veröffentlichten Werte aus den Schweizer Befragungen mit
Seiten-/Tabellenangabe je Wert zusammen. Jeder Wert ist einzeln belegt;
die Datei ist die Grundlage für die Diagramme des Furcht-Reiters.

Quellen:
  CS2022  Crime Survey 2022 (Markwalder/Biberstein/Baier, ZHAW & Uni St.
          Gallen im Auftrag KKPKS, August 2023; n = 15'519, 16- bis unter
          80-jährige Wohnbevölkerung, Online/Telefon)
  CS2015  Schweizerische Sicherheitsbefragung 2015 (Biberstein/Killias u. a.,
          Killias Research & Consulting im Auftrag KKPKS; nationale Stichprobe
          n = 2'004, 16+, Telefon/Online)
  SKP2017 Sekundärquelle für ältere ICVS-Werte: Schweizerische
          Kriminalprävention, SKP-Info 3/2017 "Thema Kriminalitätsfurcht",
          dort zitiert nach van Dijk u. a. 2008 bzw. Biberstein u. a. 2016.
          Diese Werte stammen aus anderen Instrumenten und sind nur als
          grobe Orientierung brauchbar — in der App so gekennzeichnet.

Spalte n: Stichprobe = vom Bericht genannte Befragtenzahl.
         Fälle in der Ausprägung = die im Bericht in Klammern gedruckte
         Anzahl (Zähler), nicht die Zahl der Befragten.

WICHTIG: Die Instrumente sind NICHT identisch. "Unsicher alleine auf der
Strasse nach Einbruch der Dunkelheit" wird in CS2015 mit vier Stufen
(sehr sicher … sehr unsicher) erhoben, in CS2022 werden die zusammengefassten
Kategorien berichtet, im ESS mit derselben vierstufigen Frage. Die Werte sind
deshalb vergleichbar, aber nicht deckungsgleich; der Instrumentenwechsel ist
bei jedem Diagramm ausgewiesen.

Ausgabe: output/ch_wahrnehmung_referenzwerte.csv

Aufruf: python3 scripts/45_ch_referenzwerte.py
"""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

SP = "Stichprobe"
FZ = "Fälle in der Ausprägung"

# quelle, erhebung, jahr, dimension, merkmal, ausprägung, wert, n, n_art, beleg
W = [
    # --- Sicherheitsgefühl nach Einbruch der Dunkelheit --------------------
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "sicherheitsgefuehl", "allein zu Fuss nach Dunkelheit", "sehr sicher", 39.4, 2004, SP, "CS2022 Kap. 2.3, Tabelle 81"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "sicherheitsgefuehl", "allein zu Fuss nach Dunkelheit", "ziemlich sicher", 45.9, 2004, SP, "CS2022 Kap. 2.3, Tabelle 81"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "sicherheitsgefuehl", "allein zu Fuss nach Dunkelheit", "etwas unsicher", 12.6, 2004, SP, "CS2022 Kap. 2.3, Tabelle 81"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "sicherheitsgefuehl", "allein zu Fuss nach Dunkelheit", "sehr unsicher", 2.2, 2004, SP, "CS2022 Kap. 2.3, Tabelle 81"),
    ("CS2022", "Crime Survey 2022", 2022, "sicherheitsgefuehl", "allein zu Fuss nach Dunkelheit", "sehr sicher", 40.8, 15519, SP, "CS2022 Kap. 2.3, Tabelle 81"),
    ("CS2022", "Crime Survey 2022", 2022, "sicherheitsgefuehl", "allein zu Fuss nach Dunkelheit", "ziemlich sicher", 46.8, 15519, SP, "CS2022 Kap. 2.3, Tabelle 81"),
    ("CS2022", "Crime Survey 2022", 2022, "sicherheitsgefuehl", "allein zu Fuss nach Dunkelheit", "etwas unsicher", 10.8, 15519, SP, "CS2022 Kap. 2.3, Tabelle 81"),
    ("CS2022", "Crime Survey 2022", 2022, "sicherheitsgefuehl", "allein zu Fuss nach Dunkelheit", "sehr unsicher", 1.6, 15519, SP, "CS2022 Kap. 2.3, Tabelle 81"),

    # --- Konkrete Angst, Opfer einer Straftat zu werden --------------------
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "angst_12_monate", "auf der Strasse", "ja", 11.3, 2004, SP, "CS2022 Kap. 2.3, Tabelle 82"),
    ("CS2022", "Crime Survey 2022", 2022, "angst_12_monate", "auf der Strasse", "ja", 11.1, 15519, SP, "CS2022 Kap. 2.3, Tabelle 82"),

    # --- Vermeidungsverhalten abends nach 20 Uhr ---------------------------
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "vermeidung", "gewissen Leuten aus dem Weg gehen", "genannt", 27.9, 2004, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2022", "Crime Survey 2022", 2022, "vermeidung", "gewissen Leuten aus dem Weg gehen", "genannt", 25.3, 15519, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "vermeidung", "Unterführungen meiden", "genannt", 25.7, 2004, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2022", "Crime Survey 2022", 2022, "vermeidung", "Unterführungen meiden", "genannt", 23.5, 15519, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "vermeidung", "gewisse Strassen oder Plätze meiden", "genannt", 20.3, 2004, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2022", "Crime Survey 2022", 2022, "vermeidung", "gewisse Strassen oder Plätze meiden", "genannt", 17.0, 15519, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "vermeidung", "Bahnhöfe meiden", "genannt", 14.2, 2004, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2022", "Crime Survey 2022", 2022, "vermeidung", "Bahnhöfe meiden", "genannt", 13.5, 15519, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "vermeidung", "immer vor 20 Uhr zu Hause", "genannt", 4.1, 2004, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2022", "Crime Survey 2022", 2022, "vermeidung", "immer vor 20 Uhr zu Hause", "genannt", 5.5, 15519, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "vermeidung", "keine öffentlichen Verkehrsmittel", "genannt", 5.4, 2004, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2022", "Crime Survey 2022", 2022, "vermeidung", "keine öffentlichen Verkehrsmittel", "genannt", 6.5, 15519, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "vermeidung", "nie allein ausgehen", "genannt", 6.4, 2004, SP, "CS2022 Kap. 2.3, Tabelle 83"),
    ("CS2022", "Crime Survey 2022", 2022, "vermeidung", "nie allein ausgehen", "genannt", 5.8, 15519, SP, "CS2022 Kap. 2.3, Tabelle 83"),

    # --- Vermeidung wegen Terrorangst -------------------------------------
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "vermeidung_terror", "Menschenmengen meiden", "genannt", 6.6, 2004, SP, "CS2022 Kap. 2.3, Tabelle 84"),
    ("CS2022", "Crime Survey 2022", 2022, "vermeidung_terror", "Menschenmengen meiden", "genannt", 7.3, 15519, SP, "CS2022 Kap. 2.3, Tabelle 84"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "vermeidung_terror", "verhält sich wie immer", "genannt", 80.6, 2004, SP, "CS2022 Kap. 2.3, Tabelle 84"),
    ("CS2022", "Crime Survey 2022", 2022, "vermeidung_terror", "verhält sich wie immer", "genannt", 79.1, 15519, SP, "CS2022 Kap. 2.3, Tabelle 84"),

    # --- Vertrauen in die Polizei ------------------------------------------
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "vertrauen_polizei", "allgemein", "ja", 92.9, 2004, SP, "CS2022 Kap. 2.4.1, Tabelle 85"),
    ("CS2022", "Crime Survey 2022", 2022, "vertrauen_polizei", "allgemein", "ja", 92.4, 15519, SP, "CS2022 Kap. 2.4.1, Tabelle 85"),
    ("CS2022", "Crime Survey 2022", 2022, "vertrauen_polizei", "Männer", "ja", 90.8, None, "", "CS2022 Kap. 2.4.1, Tabelle 86"),
    ("CS2022", "Crime Survey 2022", 2022, "vertrauen_polizei", "Frauen", "ja", 94.1, None, "", "CS2022 Kap. 2.4.1, Tabelle 86"),
    ("CS2022", "Crime Survey 2022", 2022, "vertrauen_polizei", "16-36 Jahre", "ja", 87.8, None, "", "CS2022 Kap. 2.4.1, Tabelle 86"),
    ("CS2022", "Crime Survey 2022", 2022, "vertrauen_polizei", "58-80 Jahre", "ja", 95.5, None, "", "CS2022 Kap. 2.4.1, Tabelle 86"),
    ("CS2022", "Crime Survey 2022", 2022, "vertrauen_polizei", "deutschsprachige Schweiz", "ja", 93.0, None, "", "CS2022 Kap. 2.4.1, Tabelle 86"),
    ("CS2022", "Crime Survey 2022", 2022, "vertrauen_polizei", "französischsprachige Schweiz", "ja", 90.7, None, "", "CS2022 Kap. 2.4.1, Tabelle 86"),
    ("CS2022", "Crime Survey 2022", 2022, "vertrauen_polizei", "italienischsprachige Schweiz", "ja", 93.8, None, "", "CS2022 Kap. 2.4.1, Tabelle 86"),

    # --- Opfererfahrungen: Einjahresprävalenz und Anzeigerate -------------
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "praevalenz_1jahr", "Einbruch in die Wohnung", "betroffen", 1.6, 2004, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "praevalenz_1jahr", "Einbruch in die Wohnung", "betroffen", 1.1, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "praevalenz_1jahr", "versuchter Einbruch", "betroffen", 2.3, 2004, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "praevalenz_1jahr", "versuchter Einbruch", "betroffen", 1.4, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "praevalenz_1jahr", "Diebstahl persönlichen Eigentums", "betroffen", 4.4, 2004, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "praevalenz_1jahr", "Diebstahl persönlichen Eigentums", "betroffen", 3.0, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "praevalenz_1jahr", "Fahrraddiebstahl", "betroffen", 5.2, 2004, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "praevalenz_1jahr", "Fahrraddiebstahl", "betroffen", 3.9, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "praevalenz_1jahr", "Raub", "betroffen", 1.1, 2004, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "praevalenz_1jahr", "Raub", "betroffen", 0.4, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "praevalenz_1jahr", "Tätlichkeiten und Körperverletzung", "betroffen", 1.0, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "praevalenz_1jahr", "sexuelle Belästigung", "betroffen", 4.3, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "praevalenz_1jahr", "Stalking", "betroffen", 1.9, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "praevalenz_1jahr", "Betrug", "betroffen", 8.4, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "anzeigerate", "Einbruch in die Wohnung", "angezeigt", 86.6, 2004, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "anzeigerate", "Einbruch in die Wohnung", "angezeigt", 75.1, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "anzeigerate", "versuchter Einbruch", "angezeigt", 38.3, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "anzeigerate", "Diebstahl persönlichen Eigentums", "angezeigt", 41.8, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "anzeigerate", "Raub", "angezeigt", 49.2, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "anzeigerate", "Tätlichkeiten und Körperverletzung", "angezeigt", 30.9, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "anzeigerate", "sexuelle Belästigung", "angezeigt", 6.8, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "anzeigerate", "Stalking", "angezeigt", 17.5, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),
    ("CS2022", "Crime Survey 2022", 2022, "anzeigerate", "Betrug", "angezeigt", 14.8, 15519, SP, "CS2022 Kap. 3, Tabelle 93"),

    # --- Sicherheitsbefragung 2015, Tabelle 87 -----------------------------
    # n ist die im Bericht in Klammern gedruckte Fallzahl der Ausprägung.
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "unsicher_strasse", "Männer", "unsicher", 7.5, 74, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "unsicher_strasse", "Frauen", "unsicher", 22.0, 215, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "unsicher_strasse", "unter 26 Jahre", "unsicher", 14.2, 50, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "unsicher_strasse", "26-39 Jahre", "unsicher", 11.8, 66, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "unsicher_strasse", "über 39 Jahre", "unsicher", 16.4, 173, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "unsicher_strasse", "Schweiz", "unsicher", 14.7, 289, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2011", "Sicherheitsbefragung 2011", 2011, "unsicher_strasse", "Schweiz", "unsicher", 15.4, 310, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "unsicher_strasse", "Familienmitglieder", "unsicher", 21.4, 243, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "angst_verbrechen", "Schweiz", "ja", 11.3, 223, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2011", "Sicherheitsbefragung 2011", 2011, "angst_verbrechen", "Schweiz", "ja", 12.6, 254, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "einbruch_wahrscheinlich", "Schweiz", "ja", 33.1, 345, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2011", "Sicherheitsbefragung 2011", 2011, "einbruch_wahrscheinlich", "Schweiz", "ja", 25.4, 476, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "einbruch_wahrscheinlich", "Männer", "ja", 34.7, 195, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "einbruch_wahrscheinlich", "Frauen", "ja", 31.2, 149, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "einbruch_wahrscheinlich", "unter 26 Jahre", "ja", 22.2, 45, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),
    ("CS2015", "Sicherheitsbefragung 2015", 2015, "einbruch_wahrscheinlich", "über 39 Jahre", "ja", 37.6, 182, FZ, "CS2015 Kap. 4.1.1, Tabelle 87"),

    # --- Ältere Vergleichswerte (Sekundärquelle, anderes Instrument) -------
    ("SKP2017", "SKP-Info 3/2017 (nach van Dijk u. a. 2008)", 1996, "unsicher_strasse", "Schweiz", "unsicher", 17.0, None, "", "SKP-Info 3/2017, S. 5"),
    ("SKP2017", "SKP-Info 3/2017 (nach van Dijk u. a. 2008)", 2000, "unsicher_strasse", "Schweiz", "unsicher", 22.0, None, "", "SKP-Info 3/2017, S. 5"),
    ("SKP2017", "SKP-Info 3/2017 (nach früheren ICVS)", 1989, "einbruch_wahrscheinlich", "Schweiz", "ja", 46.0, None, "", "SKP-Info 3/2017, S. 5"),
    ("SKP2017", "SKP-Info 3/2017 (nach früheren ICVS)", 1996, "einbruch_wahrscheinlich", "Schweiz", "ja", 29.0, None, "", "SKP-Info 3/2017, S. 5"),
]


def main():
    ziel = OUT / "ch_wahrnehmung_referenzwerte.csv"
    with open(ziel, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["quelle", "erhebung", "jahr", "dimension", "merkmal",
                    "auspraegung", "wert_prozent", "n", "n_art", "beleg"])
        for r in W:
            w.writerow(r)
    dims = {}
    for r in W:
        dims.setdefault(r[3], set()).add(r[2])
    print(f"{ziel.name}: {len(W)} Werte, {len(dims)} Dimensionen, "
          f"{len({r[0] for r in W})} Quellen")
    for d, jahre in sorted(dims.items()):
        print(f"  {d:26s} Jahre {sorted(jahre)}  ({len([x for x in W if x[3] == d])} Werte)")


if __name__ == "__main__":
    main()
