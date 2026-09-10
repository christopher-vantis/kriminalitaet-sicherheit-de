#!/usr/bin/env python3
"""
08_bka_tv_zeitreihen.py — Tatverdächtige und Belastungszahlen (BKA-Zeitreihen)
==============================================================================
Liest die BKA-PKS-Zeitreihen 2025 (Tatverdächtige T20/T40/T50 und
Tatverdächtigenbelastungszahlen ab 2009) und stellt sie als eine Tabelle
zusammen: Jahr, Tatverdächtige insgesamt / deutsch / nichtdeutsch sowie die
TVBZ (Tatverdächtige je 100.000 Einwohner der jeweiligen Bevölkerungsgruppe).

Struktur der xlsx: mehrzeiliger Vorspann, dann Langformat mit den Spalten
Schlüssel | Straftat | Jahr | Wert | ... Für die Zeitreihe wird nur die Zeile
mit dem Aggregatschlüssel "------" (Straftaten insgesamt) verwendet.

Wichtige Definitionen (aus den Datei-Hinweisen):
- TVBZ = ansässige Tatverdächtige pro 100.000 Einwohner der jeweiligen
  Altersklasse (ohne Kinder unter 8 Jahren). Bei der TVBZ der nichtdeutschen
  Wohnbevölkerung ist der Nenner die nichtdeutsche Wohnbevölkerung.
- Ab 2009 "echte" Tatverdächtigenzählung -> nicht mit Vorjahren vergleichbar.
- Bevölkerungsbasis: bis 2012 vor Zensus 2011; 2013-2023 Zensus 2011;
  2024 Zensus 2022 (Vergleich nur eingeschränkt möglich).

Ausgabe: output/pks_tatverdaechtige.csv
"""
import csv
import pathlib
import unicodedata

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parent.parent
ZR = ROOT / "data/raw/pks/zeitreihen/2025"
OUT = ROOT / "output/pks_tatverdaechtige.csv"

TV_DATEIEN = {
    "tv_insgesamt": "ZR-TV-01-T20-TV-insg_xls.xlsx",
    "tv_deutsch": "ZR-TV-04-T40-TV-insg-deutsch_xls.xlsx",
    "tv_nichtdeutsch": "ZR-TV-07-T50-TV-insg-nichtdeutsch_xls.xlsx",
}
TVBZ_DATEIEN = {
    "tvbz_insgesamt": "ZR-BZ-01-T20-TVBZinsgesamt2009_xls.xlsx",
    "tvbz_deutsch": "ZR-BZ-01-T40-TVBZ-insg-deutsch_xls.xlsx",
    "tvbz_nichtdeutsch": "ZR-BZ-01-T50-TVBZgesamtnichtdeutsch2009_xls.xlsx",
}


def norm(s):
    s = unicodedata.normalize("NFC", str(s))
    return s.replace("\u00ad", "").replace("\n", " ").replace("\r", " ").strip()


def lies_zeitreihe(pfad, label_filter="Straftaten insgesamt"):
    """Liest Langformat-Zeitreihe. Gibt {jahr: wert} für die Aggregatzeile zurück."""
    wb = openpyxl.load_workbook(pfad, read_only=True)
    ws = wb[wb.sheetnames[0]]
    ergebnis = {}
    gesehen_kopf = False
    letzter_schluessel = None
    letzte_straftat = None

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=5, values_only=True):
        r = list(row) + [None] * 5
        a = norm(r[0]) if r[0] is not None else ""
        b = norm(r[1]) if r[1] is not None else ""
        # Kopfzeile erkennen
        if a == "Schlüssel" and "Straftat" in b:
            gesehen_kopf = True
            continue
        if not gesehen_kopf:
            continue
        if a:
            letzter_schluessel = a
        if b:
            letzte_straftat = b
        # Datenzeile: Spalte C = Jahr, Spalte D = Wert
        jahr, wert = r[2], r[3]
        if letzte_straftat != label_filter or not isinstance(jahr, (int, float)):
            continue
        try:
            ergebnis[int(jahr)] = float(wert) if wert is not None else None
        except (TypeError, ValueError):
            ergebnis[int(jahr)] = None
    return ergebnis


def main():
    daten = {}
    for feld, datei in TV_DATEIEN.items():
        pfad = ZR / datei
        daten[feld] = lies_zeitreihe(pfad)
        n = len(daten[feld])
        jahre = sorted(daten[feld]) if n else []
        print(f"{feld:18s}: {n:3d} Jahre" + (f" ({jahre[0]}-{jahre[-1]})" if n else " LEER"))
    for feld, datei in TVBZ_DATEIEN.items():
        pfad = ZR / datei
        daten[feld] = lies_zeitreihe(pfad)
        n = len(daten[feld])
        jahre = sorted(daten[feld]) if n else []
        print(f"{feld:18s}: {n:3d} Jahre" + (f" ({jahre[0]}-{jahre[-1]})" if n else " LEER"))

    alle_jahre = sorted(set().union(*[set(d) for d in daten.values()]))
    felder = list(TV_DATEIEN) + list(TVBZ_DATEIEN)
    zeilen = []
    for j in alle_jahre:
        z = {"jahr": j}
        for f in felder:
            z[f] = daten[f].get(j)
        tv_i, tv_d, tv_n = z.get("tv_insgesamt"), z.get("tv_deutsch"), z.get("tv_nichtdeutsch")
        z["anteil_nichtdeutsch_pct"] = (round(tv_n / tv_i * 100, 2)
                                        if tv_i and tv_n is not None else None)
        tvbz_d, tvbz_n = z.get("tvbz_deutsch"), z.get("tvbz_nichtdeutsch")
        z["tvbz_verhaeltnis"] = (round(tvbz_n / tvbz_d, 2)
                                 if tvbz_d and tvbz_n else None)
        zeilen.append(z)

    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["jahr"] + felder +
                           ["anteil_nichtdeutsch_pct", "tvbz_verhaeltnis"])
        w.writeheader()
        w.writerows(zeilen)
    print(f"\n{len(zeilen)} Jahre -> {OUT}")
    # Kontrollausgabe ausgewählter Jahre
    for j in (1987, 1993, 2005, 2015, 2020, 2024, 2025):
        z = next((x for x in zeilen if x["jahr"] == j), None)
        if z:
            print(f"  {j}: TV gesamt {z['tv_insgesamt']:>10,.0f} | nichtdeutsch "
                  f"{z['tv_nichtdeutsch']:>9,.0f} ({z['anteil_nichtdeutsch_pct']} %) | "
                  f"TVBZ D {z['tvbz_deutsch']} / ND {z['tvbz_nichtdeutsch']}")


if __name__ == "__main__":
    main()
