#!/usr/bin/env python3
"""
33_skid_furcht.py — Kriminalitätsfurcht aus dem SKiD-Ergebnisbericht 2024
=========================================================================
Legt die Kennwerte zu Sicherheitsgefühl und Kriminalitätsfurcht als CSV ab.

Quelle: BKA/Destatis, "Sicherheit und Kriminalität in Deutschland 2024",
Ergebnisbericht (data/raw/skid/SKiD2024_Ergebnisbericht.pdf). Die Zahlen stehen
im Fließtext von Kapitel 6; die zugehörigen Tabellen sind im PDF als
Abbildungen gesetzt und lassen sich nicht automatisch auslesen. Sie sind
deshalb hier als Werte hinterlegt — mit Angabe des Berichtsteils, damit jede
Zahl nachprüfbar bleibt.

Erhebung: 60.837 auswertbare Interviews, repräsentativ für die in
Privathaushalten lebende Wohnbevölkerung ab 16 Jahren. Vergleichswelle 2020.

Ausgabe: output/skid_furcht.csv
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ZIEL = ROOT / "output" / "skid_furcht.csv"

# Delikt -> (Furcht 2024, Risikoeinschätzung 2024, Furcht Frauen, Furcht Männer)
# Quelle: Kapitel 6.3 und 6.4 des Ergebnisberichts. Wo der Bericht nur einen
# Wert für Frauen oder Männer nennt, bleibt der andere leer.
DELIKTE = {
    "Betrug im Internet":            (52.0, 40.9, 51.9, 52.4),
    "Sachbeschädigung":              (30.9, 24.7, None, None),
    "Wohnungseinbruch":              (28.6, 17.2, None, None),
    "Diebstahl":                     (27.5, 21.1, None, None),
    "Körperverletzung":              (26.8, 13.1, 26.6, 26.8),
    "Sexuelle Belästigung":          (24.0, 11.9, 34.9, 12.6),
    "Terroranschlag":                (23.0, 13.4, None, None),
    "Vorurteilskriminalität":        (17.2, 11.3, None, None),
}

# Ort -> (sicher tagsüber, sicher nachts, Frauen nachts, Männer nachts)
ORTE = {
    "In der eigenen Wohngegend":     (97.4, 74.0, 66.1, 82.7),
    "Auf Straßen und Plätzen":       (88.7, 40.1, 26.9, 54.1),
    "Im öffentlichen Nahverkehr":    (86.8, 44.8, 33.2, 57.2),
    "In Parks und Grünanlagen":      (77.7, 22.8, 11.1, 34.8),
    "An Bahnhöfen":                  (70.9, 27.0, 16.0, 38.5),
}

# Vermeideverhalten (Kapitel 6.5)
VERMEIDEN = {
    "Weicht nachts fremden Personen aus":              41.7,
    "Lässt Wohnung bewohnt wirken":                    38.9,
    "Meidet den Nahverkehr bei Nacht":                 35.1,
    "Meidet bestimmte Straßen, Plätze, Parks":         30.3,
}


def main():
    zeilen = []
    for delikt, (furcht, risiko, frauen, maenner) in DELIKTE.items():
        zeilen.append(("delikt", delikt, furcht, risiko, frauen, maenner))
    for ort, (tag, nacht, frauen, maenner) in ORTE.items():
        zeilen.append(("ort", ort, tag, nacht, frauen, maenner))
    for massnahme, wert in VERMEIDEN.items():
        zeilen.append(("vermeiden", massnahme, wert, None, None, None))

    ZIEL.parent.mkdir(exist_ok=True)
    with ZIEL.open("w", encoding="utf-8", newline="") as fh:
        fh.write("art;bezeichnung;wert_1;wert_2;frauen;maenner\n")
        for art, bez, w1, w2, f, m in zeilen:
            fh.write(f"{art};{bez};{w1 if w1 is not None else ''};"
                     f"{w2 if w2 is not None else ''};"
                     f"{f if f is not None else ''};"
                     f"{m if m is not None else ''}\n")

    print(f"{len(zeilen)} Einträge -> {ZIEL.name}\n")
    print("--- Deliktspezifische Furcht 2024 (Furcht | Risiko) ---")
    for d, (a, b, f, m) in DELIKTE.items():
        zu = f" | Frauen {f} / Männer {m}" if f and m else ""
        print(f"  {d:<26} {a:>5.1f} % | {b:>5.1f} %{zu}")
    print("\n--- Sicherheitsgefühl (tagsüber | nachts) ---")
    for o, (a, b, f, m) in ORTE.items():
        print(f"  {o:<30} {a:>5.1f} % | {b:>5.1f} %   (Frauen nachts {f} / Männer {m})")
    print("\n--- Vermeideverhalten ---")
    for k, v in VERMEIDEN.items():
        print(f"  {k:<42} {v:>5.1f} %")

    # Kontrolle: Furcht liegt bei jedem Delikt über der Risikoeinschätzung?
    fehler = [d for d, (a, b, _f, _m) in DELIKTE.items() if b > a]
    print("\nKontrolle: Furcht über Risikoeinschätzung bei allen Delikten:",
          "ja" if not fehler else f"NEIN — {fehler}")
    # Kontrolle: Sicherheitsgefühl nachts nie höher als tagsüber?
    fehler2 = [o for o, (a, b, _f, _m) in ORTE.items() if b > a]
    print("Kontrolle: nachts nie sicherer als tagsüber:",
          "ja" if not fehler2 else f"NEIN — {fehler2}")
    # Kontrolle: Frauen fühlen sich nachts nie sicherer als Männer?
    fehler3 = [o for o, (_a, _b, f, m) in ORTE.items() if f > m]
    print("Kontrolle: Frauen nachts nie sicherer als Männer:",
          "ja" if not fehler3 else f"NEIN — {fehler3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
