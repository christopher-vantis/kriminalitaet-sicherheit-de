#!/usr/bin/env python3
"""
05_referenzwerte.py — Projekt 47, Referenzwerte aus Dunkelfeld-Berichten
=======================================================================
Erzeugt dashboard/data/wahrnehmung_referenzwerte.csv (tidy/long) aus den
verifizierten Werten der Primärquellen. Alle Werte wurden direkt aus den
Berichts-PDFs gelesen (Text + grafische Auslesung der Abbildungen), nicht
aus Sekundärliteratur.

Quellen:
- BKA (2026): Sicherheit und Kriminalität in Deutschland 2024 (SKiD 2024),
  Ergebnisbericht V1.0. Datei: data/raw/skid/Ergebnisbericht.pdf
- BKA (2020): SKiD 2020. Datei: data/raw/skid/SKiD2020_Ergebnisse_V1.4.pdf
- BKA (2018): DVS 2017, erste Ergebnisse. Datei:
  data/raw/dvs/2018ersteErgebnisseDVS2017.pdf
- BKA (2014): DVS 2012. Datei: data/raw/dvs/2014DeutscherViktimisierungssurvey2012.pdf

Wichtig:
- SKiD-Furcht/Risiko = Anteile "sehr stark beunruhigt"/"ziemlich beunruhigt"
  bzw. "sehr wahrscheinlich"/"eher wahrscheinlich"; Vermeidung = "sehr oft"/"häufig".
- DVS-Furchtitems wurden nur einem Splitsample gestellt:
  n = 11.643 (2012), n = 6.079 (2017); Gesamtstichproben waren größer.
- Terrorismus wurde 2012 nicht erhoben (kein Klammerwert).
- Prävalenzen SKiD 2024 beziehen sich auf 12 Monate (Bezugsjahr 2023).
"""
import csv
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "dashboard/data/wahrnehmung_referenzwerte.csv"

# Spalten: quelle, quelle_detail, welle_jahr, kategorie, item, gruppe, wert_pct, n_hinweis
R = []

def add(quelle, detail, jahr, kategorie, item, gruppe, wert, n=""):
    R.append(dict(quelle=quelle, quelle_detail=detail, welle_jahr=jahr,
                  kategorie=kategorie, item=item, gruppe=gruppe,
                  wert_pct=wert, n_hinweis=n))

SKID24 = "SKiD 2024 (BKA, Ergebnisbericht V1.0)"
SKID20 = "SKiD 2020 (BKA)"
DVS17 = "DVS 2017 (BKA, erste Ergebnisse)"

# ---------------------------------------------------------------- Furcht affektiv
FRUCHT = [  # (Item, 2024, 2020)
    ("Betrug im Internet", 52.0, 42.0),
    ("Sachbeschädigung", 30.9, 24.2),
    ("Wohnungseinbruch", 28.6, 27.1),   # 2020->2024 nicht signifikant
    ("Diebstahl", 27.5, 22.1),
    ("Körperverletzung", 26.8, 18.5),
    ("Sexuelle Belästigung", 24.0, 16.4),
    ("Terroranschlag", 23.0, 18.6),
    ("Vorurteilskriminalität", 17.2, 14.0),
]
for item, w24, w20 in FRUCHT:
    add(SKID24, "Kapitel 6.3, Abb. 26 (S. 64)", 2024, "furcht_affektiv", item, "gesamt", w24)
    add(SKID20, "Kapitel 6.3", 2020, "furcht_affektiv", item, "gesamt", w20)
# Geschlecht 2024 (Tabelle 17)
add(SKID24, "Kap. 6.3, Tab. 17 (S. 65)", 2024, "furcht_affektiv", "Sexuelle Belästigung", "Frauen", 34.9)
add(SKID24, "Kap. 6.3, Tab. 17 (S. 65)", 2024, "furcht_affektiv", "Sexuelle Belästigung", "Männer", 12.6)
add(SKID24, "Kap. 6.3, Tab. 17 (S. 65)", 2024, "furcht_affektiv", "Betrug im Internet", "Männer", 52.4)
add(SKID24, "Kap. 6.3 (S. 66)", 2024, "furcht_affektiv", "Körperverletzung", "Männer", 26.8)
add(SKID24, "Kap. 6.3 (S. 66)", 2024, "furcht_affektiv", "Betrug im Internet", "Frauen", 51.9)
add(SKID24, "Kap. 6.3 (S. 66)", 2024, "furcht_affektiv", "Körperverletzung", "Frauen", 26.6)

# ---------------------------------------------------- Risikoeinschätzung (kognitiv)
RISIKO24 = [  # (Item, 2024)
    ("Betrug im Internet", 40.9), ("Sachbeschädigung", 24.7), ("Diebstahl", 21.1),
    ("Wohnungseinbruch", 17.2), ("Terroranschlag", 13.4), ("Körperverletzung", 13.1),
    ("Sexuelle Belästigung", 11.9), ("Vorurteilskriminalität", 11.3),
]
for item, w in RISIKO24:
    add(SKID24, "Kapitel 6.4, Abb. 27 (S. 67)", 2024, "risiko_kognitiv", item, "gesamt", w)
# 2020er-Werte aus Abb. 27 (Auslesung der Grafik, Dokumentseite 67).
# Signifikanz (Chi², 5 %): Anstieg signifikant bei Betrug im Internet,
# Sachbeschädigung, Terroranschlag, Körperverletzung, sex. Belästigung und
# Vorurteilskriminalität; NICHT signifikant bei Diebstahl und Wohnungseinbruch
# (letzterer ist der einzige Rückgang: 18,0 -> 17,2).
RISIKO20 = {
    "Betrug im Internet": 34.2, "Sachbeschädigung": 22.2, "Diebstahl": 19.6,
    "Wohnungseinbruch": 18.0, "Terroranschlag": 12.2, "Körperverletzung": 9.7,
    "Sexuelle Belästigung": 8.2, "Vorurteilskriminalität": 10.0,
}
for item, w in RISIKO20.items():
    add(SKID20, "Kapitel 6.4, Abb. 27 (S. 67)", 2020, "risiko_kognitiv", item, "gesamt", w)
add(SKID24, "Kap. 6.4, Tab. 18 (S. 68)", 2024, "risiko_kognitiv", "Sexuelle Belästigung", "Frauen", 18.5)
add(SKID24, "Kap. 6.4, Tab. 18 (S. 68)", 2024, "risiko_kognitiv", "Sexuelle Belästigung", "Männer", 5.0)

# --------------------------------------------------- Sicherheitsgefühl nach Orten
ORTE = [  # (Ort, gesamt, Männer, Frauen)
    ("Wohngegend", 74.0, 82.7, 66.1),
    ("ÖPNV", 44.8, 57.2, 33.2),
    ("Straßen, Wege, Plätze", 40.1, 54.1, 26.9),
    ("Bahnhöfe", 27.0, 38.5, 16.0),
    ("Parks, Parkanlagen", 22.8, 34.8, 11.1),
]
for ort, g, m, f in ORTE:
    add(SKID24, "Kapitel 6.2, Abb. 23/25 (S. 60-62)", 2024, "sicherheit_nachts", ort, "gesamt", g)
    add(SKID24, "Kapitel 6.2, Abb. 25 (S. 62)", 2024, "sicherheit_nachts", ort, "Männer", m)
    add(SKID24, "Kapitel 6.2, Abb. 25 (S. 62)", 2024, "sicherheit_nachts", ort, "Frauen", f)
# tagsüber (Vergleich)
add(SKID24, "Kapitel 6.2 (S. 59-61)", 2024, "sicherheit_tags", "ÖPNV", "gesamt", 86.8)
add(SKID24, "Kapitel 6.2 (S. 59-61)", 2024, "sicherheit_tags", "Parks, Parkanlagen", "gesamt", 77.7)
add(SKID24, "Kapitel 6.2 (S. 61)", 2024, "sicherheit_tags", "Bahnhöfe", "Männer", 74.2)
add(SKID24, "Kapitel 6.2 (S. 61)", 2024, "sicherheit_tags", "Bahnhöfe", "Frauen", 68.3)

# ------------------------------------------------------- Schutz-/Vermeideverhalten
VERMEIDUNG = [  # (Maßnahme, gesamt, Männer, Frauen)
    ("Fremden ausweichen", 41.7, 25.7, 60.0),
    ("Wohnung bewohnt wirken lassen", 38.9, None, None),
    ("ÖPNV nachts meiden", 35.4, 22.9, 50.0),
    ("Straßen/Plätze/Parks meiden", 30.6, 22.7, 37.7),
    ("Nachts Haus nicht verlassen", 28.6, 16.0, 40.0),
    ("Haus nur in Begleitung verlassen", 25.6, 11.7, 39.0),
    ("Wohnung/Haus sichern", 23.9, None, None),
    ("Geldgeschäfte im Internet meiden", 17.4, None, None),
    ("Gegenstand zum Aufmerksammachen", 15.1, 10.7, 19.2),
    ("Selbstverteidigungstraining", 3.6, 4.3, 2.8),
    ("Reizgas mitführen", 3.3, 2.4, 4.2),
    ("Messer mitführen", 1.4, 1.9, 0.7),
    ("Andere Waffe mitführen", 1.2, 1.5, 0.9),
]
for item, g, m, f in VERMEIDUNG:
    add(SKID24, "Kapitel 6.5, Abb. 28/29 (S. 69-72)", 2024, "vermeidung", item, "gesamt", g)
    if m is not None:
        add(SKID24, "Kapitel 6.5, Abb. 29 (S. 72)", 2024, "vermeidung", item, "Männer", m)
    if f is not None:
        add(SKID24, "Kapitel 6.5, Abb. 29 (S. 72)", 2024, "vermeidung", item, "Frauen", f)
add(SKID20, "Kapitel 6.5", 2020, "vermeidung", "Straßen/Plätze/Parks meiden", "gesamt", 43.6)
add(SKID20, "Kapitel 6.5", 2020, "vermeidung", "Wohnung/Haus sichern", "gesamt", 21.6)

# ------------------------------------------------------------------- Anzeigequoten
ANZEIGE = [
    ("Kfz-Diebstahl", 92.8), ("Wohnungseinbruchdiebstahl (vollendet)", 87.4),
    ("Wohnungseinbruchdiebstahl (gesamt)", 56.7), ("Diebstahl (gesamt)", 49.3),
    ("Wohnungseinbruchdiebstahl (versucht)", 47.9), ("Sachbeschädigung", 34.2),
    ("Körperverletzung", 29.1), ("Betrug", 25.0), ("Cyberkriminalität", 19.7),
    ("Sexualdelikte", 6.2), ("Verbale Gewalt im Internet", 1.7),
]
for item, w in ANZEIGE:
    add(SKID24, "Kapitel 5 / Executive Summary (S. 2, 44 ff.)", 2024, "anzeigequote", item, "gesamt", w)
add(SKID20, "Kapitel 5", 2020, "anzeigequote", "Wohnungseinbruchdiebstahl (versucht)", "gesamt", 57.9)

# ---------------------------------------------------------------- Prävalenz (12 Mon.)
PRAEV = [
    ("Cyberkriminalität", 18.0), ("Verbale Gewalt (offline)", 14.0),
    ("Diebstahl", 12.7), ("Betrug", 12.6), ("Vorurteilsgeleitete Gewalt", 11.9),
    ("Sachbeschädigung", 10.0), ("Sexuelle Belästigung", 7.1),
    ("Verbale Gewalt (online)", 6.1), ("Körperverletzung", 2.6),
    ("Partnerschaftsgewalt", 1.4), ("Wohnungseinbruchdiebstahl", 5.0),
]
for item, w in PRAEV:
    add(SKID24, "Kapitel 4 / Executive Summary (S. 1-2, 16 ff.)", 2024, "praevalenz", item, "gesamt", w)
add(SKID24, "Executive Summary (S. 2)", 2024, "praevalenz", "Partnerschaftsgewalt", "Frauen", 2.0)
add(SKID24, "Executive Summary (S. 2)", 2024, "praevalenz", "Partnerschaftsgewalt", "Männer", 0.8)

# ------------------------------------------------------------------- DVS 2012/2017
DVS = [  # (Item, 2017, 2012, signifikant, Gruppe)
    ("Körperverletzung", 18.2, 16.6, False, "gesamt"),
    ("Wohnungseinbruch", 24.0, 18.8, True, "gesamt"),
    ("Raub", 20.9, 18.6, True, "gesamt"),
    ("Sexuelle Belästigung", 22.2, 20.6, False, "Frauen"),
    ("Sexuelle Belästigung", 6.6, 7.5, False, "Männer"),
]
for item, w17, w12, sig, grp in DVS:
    add(DVS17, "Abbildung 23 (S. 47), Splitsample n=6.079", 2017, "furcht_affektiv", item, grp, w17)
    add("DVS 2012 (BKA, Bericht 2014)", "Abb. Furcht (Splitsample n=11.643)", 2012, "furcht_affektiv", item, grp, w12)
add(DVS17, "Abbildung 23 (S. 47)", 2017, "furcht_affektiv", "Terrorismus", "gesamt", 21.6)

with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["quelle", "quelle_detail", "welle_jahr", "kategorie",
                                      "item", "gruppe", "wert_pct", "n_hinweis"],
                       delimiter=";")
    w.writeheader()
    w.writerows(R)

print(f"{len(R)} Referenzwerte -> {OUT}")
from collections import Counter
print("Kategorien:", dict(Counter(r["kategorie"] for r in R)))
