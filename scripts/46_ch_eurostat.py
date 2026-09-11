#!/usr/bin/env python3
"""
46_ch_eurostat.py — Schweiz und Deutschland im harmonisierten EU-Vergleich
=========================================================================
Quelle: Eurostat crim_off_cat (Datenstand siehe Datei), Einheit P_HTHAB =
registrierte Fälle je 100'000 Einwohner. Rohdatei aus dem Deutschland-Projekt
(data/raw/eurostat/crim_off_cat.tsv), sie enthält die Schweiz.

Warum diese Quelle zusätzlich zur BFS-Statistik:
Die BFS-PKS und die deutsche PKS zählen unterschiedlich (Abgrenzung der
Delikte, Erfassung der Nebengesetze, Aufklärungsbegriff). Ein direkter
Zahlenvergleich der beiden nationalen Statistiken wäre deshalb irreführend.
Eurostat stellt beide Länder auf dieselben ICCS-Kategorien um; die Reihen
sind untereinander vergleichbar — mit zwei Einschränkungen, die im Text
genannt werden: (1) Die Umlage auf ICCS bleibt eine Umrechnung der nationalen
Daten, (2) bei gefährlicher Körperverletzung hat Deutschland 2009–2013
nachgemeldet, was als Reihenbruch gilt.

Ausgabe: output/ch_eurostat_vergleich.csv
  jahr; delikt; iccs; de_rate; ch_rate; eu_median; eu_laender_mit_wert
"""
import csv
import pathlib
from collections import defaultdict
from statistics import median

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUELLE = ROOT / "data/raw/eurostat/crim_off_cat.tsv"
OUT = ROOT / "output/ch_eurostat_vergleich.csv"

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


def lies_roh():
    """Liest die Eurostat-Rohdatei.

    Returns:
        dict: iccs -> geo -> jahr -> Rate (Fälle je 100'000 Einwohner).
    """
    daten = defaultdict(lambda: defaultdict(dict))
    with QUELLE.open(encoding="utf-8") as fh:
        r = csv.reader(fh, delimiter="\t")
        kopf = next(r)
        jahre = [h.strip() for h in kopf[1:]]
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
                if v in ("", ":", "-", ":"):
                    continue
                try:
                    daten[iccs][geo][int(j)] = float(v)
                except ValueError:
                    continue
    return daten


def main():
    daten = lies_roh()
    zeilen = []
    for iccs, name in DELIKTE.items():
        if iccs not in daten:
            print(f"WARNUNG: {iccs} nicht gefunden")
            continue
        jahre = sorted({j for geo in daten[iccs] for j in daten[iccs][geo]})
        for j in jahre:
            de = daten[iccs].get("DE", {}).get(j)
            ch = daten[iccs].get("CH", {}).get(j)
            andere = [daten[iccs][g][j] for g in daten[iccs]
                      if g not in ("DE", "CH") and j in daten[iccs][g]]
            if de is None and ch is None and not andere:
                continue
            zeilen.append(dict(jahr=j, delikt=name, iccs=iccs,
                               de_rate=de, ch_rate=ch,
                               eu_median=round(median(andere), 1) if andere else None,
                               eu_laender_mit_wert=len(andere)))

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["jahr", "delikt", "iccs", "de_rate",
                                           "ch_rate", "eu_median",
                                           "eu_laender_mit_wert"], delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    print(f"{len(zeilen)} Zeilen -> {OUT.name}")

    # Kontrollausgabe: erster und letzter gemeinsamer Wert je Delikt
    for iccs, name in DELIKTE.items():
        paare = [(z["jahr"], z["de_rate"], z["ch_rate"]) for z in zeilen
                 if z["iccs"] == iccs and z["de_rate"] is not None
                 and z["ch_rate"] is not None]
        if not paare:
            print(f"{name:34s} keine gemeinsamen Jahre")
            continue
        a, b = paare[0], paare[-1]
        print(f"{name:34s} {a[0]}: DE {a[1]:7.1f} / CH {a[2]:7.1f}   "
              f"{b[0]}: DE {b[1]:7.1f} / CH {b[2]:7.1f}   ({len(paare)} Jahre)")


if __name__ == "__main__":
    main()
