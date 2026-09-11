#!/usr/bin/env python3
"""
41_ch_bevoelkerung_bfs.py — Wohnbevölkerung der Kantone (BFS) abrufen
====================================================================
Quelle: Bundesamt für Statistik (BFS), STAT-TAB (PxWeb-API).
  Tabelle px-x-0102020000_101 "Demografische Bilanz nach Kanton"
  Jahre 1971–2025, Kantone 1–26 (plus 0 = Schweiz).

Verwendet werden zwei Komponenten:
  0  = Bestand am 1. Januar
  14 = Bestand am 31. Dezember

Die Jahresbevölkerung für die Häufigkeitszahl wird als Mittel aus beiden
Ständen gebildet (Näherung an die mittlere Wohnbevölkerung des Jahres) und
zusätzlich einzeln ausgewiesen.

WICHTIG: Die Bestände umfassen die ständige Wohnbevölkerung; Ausländerinnen
und Ausländer mit Wohnsitz in der Schweiz sind enthalten, Asylsuchende im
laufenden Verfahren je nach Aufenthaltsdauer nur teilweise. Die PKS
registriert Taten nach Tatortprinzip, also auch Taten von Personen ohne
Wohnsitz in der Schweiz (Touristen, Grenzgänger, Pendler).

Ausgabe: data/raw/ch/bfs/px-x-0102020000_101.json (Rohantwort)
         output/ch_bevoelkerung.csv (Langformat)

Aufruf: python3 scripts/41_ch_bevoelkerung_bfs.py
"""
import csv
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "ch" / "bfs"
OUT = ROOT / "output"
TABELLE = "px-x-0102020000_101"
BASIS = "https://www.pxweb.bfs.admin.ch/api/v1/de"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

KOMPONENTEN = {"0": "bestand_1_1", "14": "bestand_31_12"}


def hole(url, daten=None):
    """HTTP-Abruf mit User-Agent.

    Args:
        url: vollständige URL.
        daten: optionaler dict-Body (POST) — sonst GET.

    Returns:
        bytes: Antwortkörper.
    """
    kopf = {"User-Agent": UA, "Accept": "application/json"}
    if daten is not None:
        kopf["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=json.dumps(daten).encode(), headers=kopf)
    else:
        req = urllib.request.Request(url, headers=kopf)
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    meta = json.loads(hole(f"{BASIS}/{TABELLE}/{TABELLE}.px"))
    (RAW / f"{TABELLE}_meta.json").write_bytes(
        json.dumps(meta, ensure_ascii=False, indent=1).encode())

    V = {v["code"]: v for v in meta["variables"]}
    kt_code, kt_text = V["Kanton"]["values"], V["Kanton"]["valueTexts"]
    # Nur die Jahre, die die PKS abdeckt (2009–2025), plus Vorjahr für den
    # 1.-Januar-Stand 2009.
    jahre = [j for j in V["Jahr"]["values"] if 2008 <= int(j) <= 2025]

    abfrage = {
        "query": [
            {"code": "Jahr", "selection": {"filter": "item", "values": jahre}},
            {"code": "Kanton", "selection": {"filter": "item", "values": kt_code}},
            {"code": "Staatsangehörigkeit (Kategorie)",
             "selection": {"filter": "item", "values": ["0"]}},
            {"code": "Geschlecht", "selection": {"filter": "item", "values": ["0"]}},
            {"code": "Demografische Komponente",
             "selection": {"filter": "item", "values": list(KOMPONENTEN)}},
        ],
        "response": {"format": "json"},
    }
    roh = json.loads(hole(f"{BASIS}/{TABELLE}/{TABELLE}.px", abfrage))
    (RAW / f"{TABELLE}.json").write_bytes(
        json.dumps(roh, ensure_ascii=False).encode())

    spalten = [c["code"] for c in roh["columns"]]
    zeilen = []
    for d in roh["data"]:
        r = dict(zip(spalten, d["key"]))
        wert = d["values"][0]
        zeilen.append({
            "kanton_code": r["Kanton"],
            "kanton": kt_text[kt_code.index(r["Kanton"])],
            "jahr": int(r["Jahr"]),
            "komponente": KOMPONENTEN[r["Demografische Komponente"]],
            "personen": None if wert in ("", None, "..") else int(wert),
        })
    ziel = OUT / "ch_bevoelkerung.csv"
    with open(ziel, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(zeilen[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    print(f"{ziel.name}: {len(zeilen)} Zeilen")

    # Kontrolle: Gesamtschweiz am 31.12. je Jahr
    ch = sorted((z for z in zeilen if z["kanton_code"] == "0"
                 and z["komponente"] == "bestand_31_12"), key=lambda x: x["jahr"])
    for z in ch:
        print(f"  Schweiz 31.12.{z['jahr']}: {z['personen']:>9,}".replace(",", "'"))


if __name__ == "__main__":
    main()
