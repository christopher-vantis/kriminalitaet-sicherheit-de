#!/usr/bin/env python3
"""Ergänzt das Projekt-Manifest um die Quellen der Bundesland-App."""
import csv
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAN = ROOT / "data/manifest.csv"
heute = "2026-09-10"

NEU = [
    ("statistikportal_flaeche_bevoelkerung.html", "data/raw/laender_indikatoren/statistikportal_flaeche_bevoelkerung.html",
     "https://www.statistikportal.de/de/bevoelkerung/flaeche-und-bevoelkerung",
     "Statistische Ämter des Bundes und der Länder", "2025", "Abruf 09/2026",
     "dl-de/by-2-0", "HTML", "Bevölkerungsstand, Gebietsfläche, Bevölkerungsdichte je Bundesland"),
    ("destatis_nationalitaet.html", "data/raw/laender_indikatoren/destatis_nationalitaet.html",
     "https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Bevoelkerungsstand/Tabellen/bevoelkerung-nichtdeutsch-laender-basis-2022.html",
     "Statistisches Bundesamt (Destatis)", "2023", "Basis Zensus 2022",
     "dl-de/by-2-0", "HTML", "Bevölkerung nach Nationalität je Bundesland"),
    ("vgrdl_faltblatt_bs2025_0.pdf", "data/raw/laender_indikatoren/vgrdl_faltblatt_2025.pdf",
     "https://www.statistikportal.de/sites/default/files/2026-08/vgrdl_faltblatt_bs2025_0.pdf",
     "Arbeitskreis VGR der Länder", "2024", "Ausgabe 2026",
     "dl-de/by-2-0", "PDF", "BIP und verfügbares Einkommen je Einwohner nach Bundesland"),
    ("NUTS_RG_20M_2021_4326.geojson", "data/raw/laender_geo/NUTS_RG_20M_2021_4326.geojson",
     "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2021_4326.geojson",
     "Eurostat/GISCO", "2021", "Auflösung 1:20 Mio.",
     "CC BY 4.0", "GeoJSON", "Kartengeometrie der NUTS-1-Regionen (= Bundesländer)"),
]


def main():
    zeilen = list(csv.DictReader(open(MAN, encoding="utf-8"), delimiter=";"))
    felder = list(zeilen[0].keys())
    vorhanden = {r["relativer_pfad"] for r in zeilen}
    neu = 0
    for name, rel, url, inst, bj, version, lizenz, fmt, bem in NEU:
        p = ROOT / rel
        if not p.exists():
            print("FEHLT (nicht eingetragen):", rel)
            continue
        if rel in vorhanden:
            continue
        zeilen.append(dict(dateiname=name, relativer_pfad=rel, quell_url=url,
                           quelle_institution=inst, berichtsjahr=bj, version=version,
                           abrufdatum=heute, dateigroesse_bytes=p.stat().st_size,
                           sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                           lizenz=lizenz, format=fmt, bemerkung=bem))
        neu += 1
    with open(MAN, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=felder, delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    print(f"{neu} Einträge ergänzt; manifest.csv enthält jetzt {len(zeilen)} Zeilen")


if __name__ == "__main__":
    main()
