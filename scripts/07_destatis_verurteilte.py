#!/usr/bin/env python3
"""
07_destatis_verurteilte.py — Verurteilte nach Delikt (Strafverfolgungsstatistik)
================================================================================
Liest die Statistischen Berichte "Strafverfolgung" (Destatis, xlsx) für die
Berichtsjahre 2022-2024 und extrahiert die Zahl der Verurteilten je
Deliktsgruppe.

Struktur der Tabelle 24311-05 ("Abgeurteilte und Verurteilte nach Art der
Straftat"): mehrzeiliger Vorspann (Zeilen 1-9), dann je Rechtsschlüssel DREI
Zeilen mit den Geschlechtern M / F / I. Die Bezeichnung des Rechtsschlüssels
steht nur in der ersten (M-)Zeile; für F und I ist sie leer und muss
fortgeschrieben werden (carry-forward).

Ausgabe: output/destatis_verurteilte.csv  (delikt; jahr; verurteilte)
"""
import csv
import pathlib
import re
import unicodedata

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/destatis"
OUT = ROOT / "output/destatis_verurteilte.csv"

DATEIEN = {
    2022: "2100300227005_SB_Strafverfolgung_2022.xlsx",
    2023: "2100300237005_SB_Strafverfolgung_2023.xlsx",
    2024: "2100300247005_SBb_Strafverfolgung_2024.xlsx",
}

# Zielgruppen: (Ausgabe-Label, Regex auf die Abschnitts-/Paragrafenbezeichnung)
ZIELE = [
    ("Tötungsdelikte", r"16\. Abschnitt"),
    ("Körperverletzung", r"17\. Abschnitt"),
    ("Sexualdelikte", r"13\. Abschnitt"),
    ("Diebstahl (19. Abschnitt)", r"19\. Abschnitt"),
    ("Einbruchdiebstahl (§ 243 Abs. 1 S. 2 Nr. 1)", r"§ 243 Abs\. 1 Satz 2 Nr\. 1"),
    ("Wohnungseinbruchdiebstahl (§ 244 Abs. 1 Nr. 3)", r"§ 244 Abs\. 1 Nr\. 3"),
    ("Schwerer Diebstahl/Banden (§ 244a)", r"§ 244 a\b"),
    ("Raub und räuberische Erpressung (20. Abschnitt)", r"20\. Abschnitt"),
    ("Betrug und Untreue (22. Abschnitt)", r"22\. Abschnitt"),
    ("Sachbeschädigung (27. Abschnitt)", r"27\. Abschnitt"),
    ("Straftaten im Straßenverkehr", r"Straftaten im Straßenverkehr"),
    ("Straftaten ohne Straßenverkehr (Summe)", r"Summe 1012 bis 1690"),
]


def norm(s):
    """Whitespace normalisieren, Bindestrich-Umbrüche aus Excel zusammenführen."""
    s = unicodedata.normalize("NFC", str(s))
    s = s.replace("\u00ad", "").replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", s).strip()


def lies_tabelle(pfad):
    """Gibt Liste (label, geschlecht, abgeurteilte, verurteilte) zurück."""
    wb = openpyxl.load_workbook(pfad, read_only=True)
    name = [s for s in wb.sheetnames if s == "24311-05"][0]
    ws = wb[name]
    zeilen = []
    label = None
    for row in ws.iter_rows(min_row=10, max_row=ws.max_row, max_col=11, values_only=True):
        r = list(row) + [None] * 11
        c = r[2]
        if c is not None and norm(c):
            label = norm(c)          # carry-forward nur bei neuem Label
        g = r[3]
        if g not in ("M", "F", "I"):
            continue
        zeilen.append((label, g, r[4], r[9]))
    return zeilen


def zahl(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s in ("-", "", "leer", "."):
        return 0.0
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def main():
    ergebnis = []
    for jahr, datei in DATEIEN.items():
        pfad = RAW / datei
        if not pfad.exists():
            print(f"FEHLT: {pfad.name}")
            continue
        zeilen = lies_tabelle(pfad)
        for name, muster in ZIELE:
            rx = re.compile(muster)
            treffer = [(lab, g, abg, ver) for lab, g, abg, ver in zeilen if lab and rx.search(lab)]
            # Gesamtzeile (Geschlecht I) bevorzugen, sonst M+F
            gesamt = [z for z in treffer if z[1] == "I"]
            if gesamt:
                _, _, abg, ver = gesamt[0]
            else:
                m = [z for z in treffer if z[1] == "M"]
                f = [z for z in treffer if z[1] == "F"]
                if not m:
                    continue
                abg = (zahl(m[0][2]) or 0) + (zahl(f[0][2]) if f else 0)
                ver = (zahl(m[0][3]) or 0) + (zahl(f[0][3]) if f else 0)
            ver = zahl(ver)
            abg = zahl(abg)
            if ver is None:
                continue
            quelle = treffer[0][0][:90]
            ergebnis.append(dict(delikt=name, jahr=jahr, abgeurteilte=abg,
                                 verurteilte=ver, quelle_label=quelle))
            print(f"{jahr} | {name:48s} | {ver:>9,.0f} Verurteilte")
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["delikt", "jahr", "abgeurteilte", "verurteilte", "quelle_label"])
        w.writeheader()
        w.writerows(ergebnis)
    print(f"\n{len(ergebnis)} Zeilen -> {OUT}")


if __name__ == "__main__":
    main()
