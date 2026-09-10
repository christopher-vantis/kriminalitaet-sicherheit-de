#!/usr/bin/env python3
"""
09_eurostat_vergleich.py — Deutschland im EU-Vergleich (polizeilich registrierte
Straftaten, Eurostat crim_off_cat)
==============================================================================
Quelle: data/raw/eurostat/crim_off_cat.tsv (Eurostat, Datenstand siehe Datei).
Einheit: P_HTHAB = registrierte Fälle je 100.000 Einwohner.

Deliktcodes (offiziell, aus der Eurostat-API zu crim_off_cat verifiziert):
  ICCS0101  Intentional homicide (vollendete vorsätzliche Tötung)
  ICCS020111 Serious assault (gefährliche/schwere Körperverletzung)
  ICCS0401  Robbery (Raub)
  ICCS0501  Burglary (Einbruch insgesamt)
  ICCS05012 Burglary of private residential premises (Wohnungseinbruch)
  ICCS0502  Theft (Diebstahl)
  ICCS0701  Fraud (Betrug)
  ICCS0903  Acts against computer systems (Cybercrime)

Ausgabe: output/eurostat_vergleich.csv
  jahr; delikt; de_rate; eu_median; eu_laender_mit_wert
"""
import csv
import pathlib
from collections import defaultdict
from statistics import median

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUELLE = ROOT / "data/raw/eurostat/crim_off_cat.tsv"
OUT = ROOT / "output/eurostat_vergleich.csv"

DELIKTE = {
    "ICCS0101": "Vorsätzliche Tötung (vollendet)",
    "ICCS020111": "Gefährliche Körperverletzung",
    "ICCS0401": "Raub",
    "ICCS0501": "Einbruch (insgesamt)",
    "ICCS05012": "Wohnungseinbruch",
    "ICCS0502": "Diebstahl",
    "ICCS0701": "Betrug",
    "ICCS0903": "Angriffe auf Computersysteme",
}


def main():
    daten = defaultdict(lambda: defaultdict(dict))  # iccs -> geo -> jahr -> rate
    with QUELLE.open(encoding="utf-8") as fh:
        r = csv.reader(fh, delimiter="\t")
        hdr = next(r)
        jahre = [h.strip() for h in hdr[1:]]
        for row in r:
            if len(row) < 5:
                continue
            teile = [x.strip() for x in row[0].split(",")]
            if len(teile) != 4:
                continue
            freq, iccs, unit, geo = teile
            if unit != "P_HTHAB" or iccs not in DELIKTE:
                continue
            for j, v in zip(jahre, row[1:]):
                if not j.isdigit():
                    continue
                v = v.strip()
                if v in ("", ":", "-"):
                    continue
                try:
                    daten[iccs][geo][int(j)] = float(v)
                except ValueError:
                    continue

    zeilen = []
    for iccs, name in DELIKTE.items():
        if iccs not in daten:
            print(f"WARNUNG: {iccs} nicht gefunden")
            continue
        jahre_alle = sorted({j for geo in daten[iccs] for j in daten[iccs][geo]})
        for j in jahre_alle:
            de = daten[iccs].get("DE", {}).get(j)
            andere = [daten[iccs][g][j] for g in daten[iccs]
                      if g != "DE" and j in daten[iccs][g]]
            if de is None and not andere:
                continue
            zeilen.append(dict(
                jahr=j, delikt=name, iccs=iccs,
                de_rate=de,
                eu_median=round(median(andere), 1) if andere else None,
                eu_laender_mit_wert=len(andere),
            ))

    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["jahr", "delikt", "iccs", "de_rate",
                                           "eu_median", "eu_laender_mit_wert"],
                           delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    print(f"{len(zeilen)} Zeilen -> {OUT}")
    for iccs, name in DELIKTE.items():
        d = daten.get(iccs, {}).get("DE", {})
        if not d:
            continue
        jahre = sorted(d)
        print(f"{name:34s} DE: {d[jahre[0]]:7.1f} ({jahre[0]}) -> {d[jahre[-1]]:7.1f} ({jahre[-1]})")


if __name__ == "__main__":
    main()
