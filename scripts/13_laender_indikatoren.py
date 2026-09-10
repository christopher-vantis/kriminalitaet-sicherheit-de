#!/usr/bin/env python3
"""
13_laender_indikatoren.py — Demografie und Wirtschaft je Bundesland
===================================================================
Liest die amtlichen Internettabellen (serverseitig gerendert) und legt die
Länderindikatoren als eine Tabelle ab.

Quellen:
  A) Statistikportal der Statistischen Ämter des Bundes und der Länder,
     „Fläche und Bevölkerung": Bevölkerungsstand 2025, Gebietsfläche 2023,
     Bevölkerungsdichte 2023.
     https://www.statistikportal.de/de/bevoelkerung/flaeche-und-bevoelkerung
  B) Destatis, „Bevölkerung nach Nationalität und Bundesländern"
     (Basis Zensus 2022): Einwohner, Deutsche, Nichtdeutsche, Anteil.
     https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/
     Bevoelkerungsstand/Tabellen/bevoelkerung-nichtdeutsch-laender-basis-2022.html
  C) Destatis, Bruttoinlandsprodukt je Einwohner nach Bundesländern.
  D) Statistik der Bundesagentur für Arbeit, Arbeitslosenquote nach Ländern.

Ausgabe: output/laender_indikatoren.csv
"""
import csv
import html
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output/laender_indikatoren.csv"
CACHE = ROOT / "data/raw/laender_indikatoren"
CACHE.mkdir(parents=True, exist_ok=True)

LAENDER = ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg",
           "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen",
           "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt",
           "Schleswig-Holstein", "Thüringen"]

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

QUELLEN = {
    "statistikportal_flaeche_bevoelkerung.html":
        "https://www.statistikportal.de/de/bevoelkerung/flaeche-und-bevoelkerung",
    "destatis_nationalitaet.html":
        "https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/"
        "Bevoelkerungsstand/Tabellen/bevoelkerung-nichtdeutsch-laender-basis-2022.html",
    "destatis_migrationshintergrund.html":
        "https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/"
        "Migration-Integration/Tabellen/migrationshintergrund-laender.html",
}
VGR_PDF = CACHE / "vgrdl_faltblatt_2025.pdf"
VGR_URL = "https://www.statistikportal.de/sites/default/files/2026-08/vgrdl_faltblatt_bs2025_0.pdf"


def vgr_tabelle():
    """Liest BIP und verfügbares Einkommen je Einwohner aus dem VGR-Faltblatt.

    Die Tabelle „Wirtschaftskraft und Einkommen 2024" steht als Text vor
    (Spalten: BIP/EW 2025, BIP/EW 2024, Index, Verfügbares Einkommen 2024,
    Index). Ländernamen können über zwei Zeilen gebrochen sein.
    """
    if not VGR_PDF.exists():
        subprocess.run(["curl", "-sL", "--max-time", "90", "-A", UA, VGR_URL,
                        "-o", str(VGR_PDF)], check=True, timeout=150)
    txt = subprocess.run(["pdftotext", "-layout", str(VGR_PDF), "-"],
                         capture_output=True, text=True, check=True).stdout
    # Nur den Abschnitt der Tabelle auswerten — sonst greifen Zahlen aus
    # anderen Grafiken desselben Dokuments.
    start = txt.find("Wirtschaftskraft und Einkommen")
    ende = txt.find("der privaten Haushalte", start)
    if start >= 0 and ende > start:
        txt = txt[start:ende]
    ergebnis = {}
    aktuell = None
    # Längste Namen zuerst prüfen, sonst verschluckt "Sachsen" das Land
    # "Sachsen-Anhalt".
    namen_sortiert = sorted(LAENDER, key=len, reverse=True)
    for zeile in txt.splitlines():
        z = zeile.strip()
        if not z:
            continue
        for land in namen_sortiert:
            if z.startswith(land):
                aktuell = land
                break
            teil = land.split("-")[0]          # "Mecklenburg-" / "Sachsen-"
            if z.startswith(teil + "-"):
                aktuell = land
                break
        # Nur Zahlen im Tausenderpunkt-Format zählen — damit fallen die
        # Achsenwerte der Grafiken (0, 10, 20, ...) heraus.
        zahlen = [zahl(x) for x in re.findall(r"\d{1,3}\.\d{3}", z)]
        if len(zahlen) >= 3 and aktuell and aktuell not in ergebnis:
            ergebnis[aktuell] = {
                "bip_je_ew_2025": zahlen[0],
                "bip_je_ew_2024": zahlen[1],
                "verfuegbares_einkommen_2024": zahlen[2],
            }
    return ergebnis


def hole(name, url):
    ziel = CACHE / name
    if not ziel.exists() or ziel.stat().st_size < 5000:
        subprocess.run(["curl", "-sL", "--max-time", "60", "-A", UA, url, "-o", str(ziel)],
                       check=True, timeout=120)
    return ziel.read_text(encoding="utf-8", errors="replace")


def tabellenzeilen(text):
    for z in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S):
        zellen = [html.unescape(re.sub(r"<[^>]+>", " ", c)) for c in
                  re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", z, re.S)]
        zellen = [re.sub(r"\s+", " ", c).strip() for c in zellen]
        zellen = [c for c in zellen if c]
        if zellen:
            yield zellen


def zahl(s):
    s = s.replace("\xa0", " ").strip()
    s = re.sub(r"\s", "", s)
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def main():
    daten = {l: {} for l in LAENDER}

    # A) Statistikportal: Bevölkerung 2025, Fläche 2023, Dichte 2023
    t = hole("statistikportal_flaeche_bevoelkerung.html", QUELLEN["statistikportal_flaeche_bevoelkerung.html"])
    for z in tabellenzeilen(t):
        if z[0] in LAENDER:
            werte = [zahl(x) for x in z[1:]]
            werte = [w for w in werte if w is not None]
            if not werte:
                continue
            haupt = werte[0]
            # Zuordnung über die Größenordnung: Bevölkerung (>100.000),
            # Fläche (<100.000), Dichte (<5000)
            for w in werte:
                if w > 100000 and "bevoelkerung_2025" not in daten[z[0]]:
                    daten[z[0]]["bevoelkerung_2025"] = w
                elif 100 < w < 100000 and "flaeche_km2" not in daten[z[0]]:
                    daten[z[0]]["flaeche_km2"] = w
                elif w <= 5000 and "dichte" not in daten[z[0]]:
                    daten[z[0]]["dichte"] = w

    # B) Destatis: Nationalität
    t = hole("destatis_nationalitaet.html", QUELLEN["destatis_nationalitaet.html"])
    for z in tabellenzeilen(t):
        if z[0] in LAENDER and len(z) >= 5:
            werte = [zahl(x) for x in z[1:]]
            if werte[0] is None:
                continue
            daten[z[0]]["einwohner_zensus22"] = werte[0]
            daten[z[0]]["deutsche"] = werte[1]
            daten[z[0]]["nichtdeutsche"] = werte[2]
            daten[z[0]]["auslaenderanteil_pct"] = werte[3]

    # B2) Destatis: Bevölkerung mit Migrationshintergrund (Mikrozensus)
    #     Spalten: Insgesamt | ohne MH | mit MH | darunter: ...
    #     Werte in Tausend.
    t = hole("destatis_migrationshintergrund.html", QUELLEN["destatis_migrationshintergrund.html"])
    for z in tabellenzeilen(t):
        if z[0] in LAENDER and len(z) >= 4:
            werte = [zahl(x) for x in z[1:4]]
            if not all(werte) or werte[0] <= 0:
                continue
            if "mh_pct" not in daten[z[0]]:
                daten[z[0]]["bevoelkerung_privathaushalte"] = werte[0] * 1000
                daten[z[0]]["ohne_mh"] = werte[1] * 1000
                daten[z[0]]["mit_mh"] = werte[2] * 1000
                daten[z[0]]["mh_pct"] = round(werte[2] / werte[0] * 100, 1)

    # Bevölkerungsdichte einheitlich aus Bevölkerung und Fläche berechnen
    # (die geparsten Werte stammen aus verschiedenen Berichtsjahren).
    for l in LAENDER:
        ew, fl = daten[l].get("bevoelkerung_2025"), daten[l].get("flaeche_km2")
        if ew and fl:
            daten[l]["dichte"] = round(ew / fl, 1)

    # C) VGR der Länder: BIP und verfügbares Einkommen je Einwohner
    for land, werte in vgr_tabelle().items():
        daten[land].update(werte)

    felder = ["bundesland", "bevoelkerung_2025", "flaeche_km2", "dichte",
              "einwohner_zensus22", "deutsche", "nichtdeutsche", "auslaenderanteil_pct",
              "bip_je_ew_2024", "bip_je_ew_2025", "bip_index_de100",
              "verfuegbares_einkommen_2024",
              "bevoelkerung_privathaushalte", "ohne_mh", "mit_mh", "mh_pct"]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=felder, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for l in LAENDER:
            w.writerow({"bundesland": l, **daten[l]})

    fehlend = [l for l in LAENDER if "bip_je_ew_2024" not in daten[l]]
    if fehlend:
        print("WARNUNG: ohne BIP-Wert:", ", ".join(fehlend))
    print(f"-> {OUT}")
    for l in LAENDER:
        d = daten[l]
        def fmt(v, n=0):
            return f"{v:,.{n}f}" if isinstance(v, (int, float)) else "—"
        print(f"  {l:26s} EW {fmt(d.get('bevoelkerung_2025')):>12s}  "
              f"BIP/EW {fmt(d.get('bip_je_ew_2024')):>7s} EUR  "
              f"verf. Eink. {fmt(d.get('verfuegbares_einkommen_2024')):>7s} EUR  "
              f"nichtdeutsch {fmt(d.get('auslaenderanteil_pct'), 1):>5s} %  "
              f"mit Migrationshintergrund {fmt(d.get('mh_pct'), 1):>5s} %")


if __name__ == "__main__":
    main()
