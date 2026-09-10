#!/usr/bin/env python3
"""
31_pmk_aufbereiten.py — Politisch motivierte Kriminalität auswerten
===================================================================
Liest die Fallzahlen aus dem amtlichen Fact Sheet des BKA ("Bundesweite
Fallzahlen 2025 — Politisch motivierte Kriminalität", data/raw/pmk/) und legt
sie als CSV ab.

Zur Methode: Die Werte stehen in zwei Balkendiagrammen. Ihre Datenzeilen liegen
als Text vor (pdftotext -layout) und sind mit Leerzeichen ausgerichtet. Eine
Zuordnung über die Spaltenposition scheitert, weil die Zahlen am jeweiligen
Balken sitzen und die Spalten daher nicht mit der Jahresüberschrift fluchten.
Deshalb wird der Reihe nach zugeordnet — mit zwei belegten Sonderfällen:

  * Die Bereiche "ausländische Ideologie" und "religiöse Ideologie" entstanden
    erst 2017 (vorher zusammengefasst als PMAK). Ihre Zeilen haben neun Werte
    und beginnen 2017.
  * PMAK selbst hat nur den Wert für 2016.

Damit ein Übertragungsfehler nicht unbemerkt bleibt, prüft das Skript nach dem
Einlesen, ob die Summe der Phänomenbereiche die Gesamtzahl ergibt. Weicht sie
ab, bricht es ab.

Ausgabe: output/pmk_zeitreihe.csv
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUELLE = ROOT / "data" / "raw" / "pmk" / "bka_pmk_2025.txt"
ZIEL = ROOT / "output" / "pmk_zeitreihe.csv"

JAHRE = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

# Bereich -> Rubrik im Text. "ab2017" markiert die erst 2017 entstandenen.
FELDER = {
    "links": ("PMK -links-", False),
    "rechts": ("PMK -rechts-", False),
    "auslaendische_ideologie": ("PMK -ausl. Ideologie-", True),
    "religioese_ideologie": ("PMK -rel. Ideologie-", True),
    "sonstige_zuordnung": ("PMK -sonst. Zuord.-", False),
}
GESAMT_MARKE = "PMK gesamt"


def zeile_zu(block, marke, mindest_zahlen=5):
    """Datenzeile einer Rubrik.

    Gesucht wird die Zeile mit der Rubrikbezeichnung und mindestens fünf
    Zahlen. Die Bedingung ist nötig, weil dieselben Bezeichnungen auch im
    Fließtext vorkommen ("Im Bereich PMK -links- machten sie ... aus") — eine
    einzelne Zahl in einer Textzeile würde sonst als Datenzeile gelten.
    """
    for zeile in block.split("\n"):
        if marke in zeile:
            rest = zeile.split(marke, 1)[1]
            if len(zahlen(rest)) >= mindest_zahlen:
                return rest
    return None


def zahlen(rest):
    """Alle Zahlen einer Zeile als ganze Zahlen (Punkt = Tausendertrennung)."""
    ergebnis = []
    for stueck in rest.replace(".", "").split():
        if stueck.isdigit():
            ergebnis.append(int(stueck))
    return ergebnis


def abschnitt(text, von, bis):
    a = text.find(von)
    b = text.find(bis, a + 1) if a >= 0 else -1
    return text[a:b] if a >= 0 and b > a else ""


def einlesen(block, art):
    """Liest einen Diagrammabschnitt aus und liefert die Werteliste."""
    werte = {}
    for feld, (marke, ab2017) in FELDER.items():
        rest = zeile_zu(block, marke)
        if rest is None:
            continue
        z = zahlen(rest)
        jahre = JAHRE[1:] if ab2017 else JAHRE
        if len(z) != len(jahre):
            print(f"  HINWEIS {art}/{feld}: {len(z)} Werte für {len(jahre)} Jahre")
            if len(z) > len(jahre):
                jahre = jahre[-len(z):]
            else:
                z = z + [None] * (len(jahre) - len(z))
        for jahr, wert in zip(jahre, z):
            werte[(feld, jahr)] = wert

    # PMAK ("Ausländer") wurde 2017 aufgeteilt und hat nur den Wert für 2016.
    # Die Zeile enthält eine einzige Zahl, deshalb hier die Ausnahme.
    rest = zeile_zu(block, "PMAK", mindest_zahlen=1)
    if rest is not None:
        z = zahlen(rest)
        if z:
            werte[("pmak_2016", 2016)] = z[0]

    # Gesamtzahl
    rest = zeile_zu(block, GESAMT_MARKE)
    if rest is not None:
        z = zahlen(rest)
        if len(z) == len(JAHRE):
            for jahr, wert in zip(JAHRE, z):
                werte[("gesamt", jahr)] = wert
        else:
            print(f"  WARNUNG {art}: Gesamtzeile hat {len(z)} statt {len(JAHRE)} Werte")

    # --- Kontrolle: Summe der Bereiche gegen die Gesamtzahl ---
    print(f"\n  Kontrolle {art}: Summe der Phänomenbereiche gegen Gesamtzahl")
    fehler = 0
    for jahr in JAHRE:
        einzel = [werte.get((f, jahr)) for f in FELDER]
        einzel = [w for w in einzel if w is not None]
        if jahr == 2016 and ("pmak_2016", 2016) in werte:
            einzel.append(werte[("pmak_2016", 2016)])
        summe = sum(einzel)
        genannt = werte.get(("gesamt", jahr))
        if genannt is None:
            continue
        abweichung = summe - genannt
        zeichen = "OK " if abweichung == 0 else "ABW"
        if abweichung != 0:
            fehler += 1
        print(f"    {jahr}: Summe {summe:>7,} | genannt {genannt:>7,} | {zeichen}".replace(",", "."))
    return werte, fehler


def main():
    text = QUELLE.read_text(encoding="utf-8", errors="replace")
    # Die Abschnitte werden an den Diagramm-Überschriften verankert. Die
    # Rubriknamen kommen auch im Inhaltsverzeichnis und im Fließtext vor —
    # ein Schneiden an diesen Stellen liefert den falschen Abschnitt.
    zeilen = text.split("\n")
    start1 = next((i for i, z in enumerate(zeilen)
                   if "Diagramm 1: Entwicklung des Gesamtstraftatenaufkommens" in z), -1)
    start2 = next((i for i, z in enumerate(zeilen)
                   if "Diagramm 2: Entwicklung der Fallzahlen" in z), -1)
    if start1 < 0 or start2 < 0:
        print("FEHLER: Diagramm-Überschriften nicht gefunden")
        return 1
    # Ende des ersten Abschnitts: die Überschrift der Gewalttaten-Tabelle
    ende1 = next((i for i, z in enumerate(zeilen)
                  if "Politisch motivierte Gewalttaten" in z and i > start1 + 10), len(zeilen))
    bloecke = {
        "gesamt": "\n".join(zeilen[start1:ende1]),
        "gewalt": "\n".join(zeilen[start2:start2 + 40]),
    }
    for name, block in bloecke.items():
        if not block:
            print(f"FEHLER: Abschnitt '{name}' nicht gefunden")
            return 1

    alle, fehler_gesamt = {}, 0
    for art, block in bloecke.items():
        werte, fehler = einlesen(block, art)
        fehler_gesamt += fehler
        for (feld, jahr), wert in werte.items():
            alle[(art, feld, jahr)] = wert

    if fehler_gesamt:
        print(f"\nABBRUCH: {fehler_gesamt} Abweichung(en) zwischen Summe und Gesamtzahl.")
        print("Ein Wert wurde vermutlich falsch zugeordnet. Bitte prüfen.")
        return 1

    ZIEL.parent.mkdir(exist_ok=True)
    with ZIEL.open("w", encoding="utf-8", newline="") as fh:
        fh.write("art;bereich;jahr;faelle\n")
        for (art, feld, jahr), wert in sorted(alle.items()):
            fh.write(f"{art};{feld};{jahr};{wert}\n")
    print(f"\n{len(alle)} Werte -> {ZIEL.name} (alle Kontrollen bestanden)")

    for art in ("gesamt", "gewalt"):
        print(f"\n--- {art} (2016 zu 2025) ---")
        for feld in list(FELDER) + ["gesamt"]:
            a, b = alle.get((art, feld, 2016)), alle.get((art, feld, 2025))
            if a and b:
                print(f"  {feld:<24} {a:>7,} -> {b:>7,}  ({100*(b-a)/a:+6.1f} %)".replace(",", "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
