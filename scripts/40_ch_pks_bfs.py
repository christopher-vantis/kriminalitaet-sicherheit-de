#!/usr/bin/env python3
"""
40_ch_pks_bfs.py — Polizeiliche Kriminalstatistik der Schweiz (BFS) abrufen
==========================================================================
Quelle: Bundesamt für Statistik (BFS), STAT-TAB (PxWeb-API).
  Tabelle px-x-1903020100_101
  "Polizeilich registrierte Straftaten gemäss Strafgesetzbuch nach Straftat,
   Kanton, Ausführungsgrad, Aufklärungsgrad und Jahr"
  Jahre 2009–2025, Kantone 1–26 (plus 8100 = Schweiz).

Zweck: Hellfeld-Reihe je Kanton für dieselben Deliktsgruppen, die das
Deutschland-Projekt verwendet (Total, Diebstahl, Einbruchdiebstahl, Raub,
Körperverletzung, Sachbeschädigung, Betrug, Cyber, Gewalt gegen Behörden).

WICHTIG (Operationalisierung):
- Die Tabelle umfasst NUR das Strafgesetzbuch (StGB). Widerhandlungen gegen
  das Betäubungsmittelgesetz (BetmG), das Ausländer- und Integrationsgesetz
  (AIG) sowie weitere Nebengesetze sind NICHT enthalten. Das BFS weist für
  2025 rund 555'000 StGB-Straftaten aus; die Gesamtzahl aller registrierten
  Straftaten (inkl. Nebengesetze) liegt höher. Für Zeitreihen ist StGB die
  konsistente Abgrenzung.
- Erfasst wird nach Tatortprinzip; eine Straftat = ein Fall.
- Aufklärungsgrad ist als eigene Dimension geführt (aufgeklärt/unaufgeklärt),
  der Totalwert beider Stufen entspricht der Gesamtzahl der Fälle.

Ausgabe: data/raw/ch/bfs/px-x-1903020100_101.json (Rohantwort, unverändert)
         data/raw/ch/bfs/px-x-1903020100_101_meta.json (Tabellenmetadaten)
         output/ch_pks_kantone.csv (Langformat)

Aufruf: python3 scripts/40_ch_pks_bfs.py
"""
import csv
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "ch" / "bfs"
OUT = ROOT / "output"
TABELLE = "px-x-1903020100_101"
BASIS = "https://www.pxweb.bfs.admin.ch/api/v1/de"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

# Ausgewählte Straftaten. Schlüssel wie in der BFS-Tabelle (Spalte "Straftat").
# Aggregate (T0 = Total, T1–T20 = Titel des StGB) tragen ein T-Kürzel.
DELIKTE = [
    "311.00.T0",        # Straftat - Total (StGB)
    "311.00.T1",        # Total 1. Titel: Leib und Leben
    "311.00.111.00",    # Tötungsdelikte (Art. 111-113/116)
    "311.00.122.00",    # Schwere Körperverletzung (Art. 122)
    "311.00.123.00",    # Einfache Körperverletzung (Art. 123)
    "311.00.126.00",    # Tätlichkeiten (Art. 126)
    "311.00.129.00",    # Gefährdung des Lebens (Art. 129)
    "311.00.T2",        # Total 2. Titel: Vermögen
    "311.00.139.00",    # Diebstahl (Art. 139)
    "311.00.139.10",    # Einbruchdiebstahl (Art. 139)
    "311.00.139.71",    # Einschleichdiebstahl (Art. 139)
    "311.00.139.74",    # Ladendiebstahl (Art. 139)
    "311.00.139.75",    # Taschendiebstahl (Art. 139)
    "311.00.139.80",    # Fahrzeugeinbruchdiebstahl (Art. 139)
    "311.00.139.81",    # Fahrzeugdiebstahl (Art. 139)
    "311.00.140.00",    # Raub (Art. 140)
    "311.00.144.00",    # Sachbeschädigung (Art. 144)
    "311.00.146.00",    # Betrug (Art. 146)
    "311.00.147.00",    # Betrügerischer Missbrauch einer Datenverarbeitungsanlage
    "311.00.143.00",    # Unbefugte Datenbeschaffung (Art. 143)
    "311.00.143.A0",    # Unbefugtes Eindringen in ein Datenverarbeitungssystem
    "311.00.180.00",    # Drohung (Art. 180)
    "311.00.181.00",    # Nötigung (Art. 181)
    "311.00.186.00",    # Hausfriedensbruch (Art. 186)
    "311.00.187.00",    # Sexuelle Handlungen mit Kindern (Art. 187)
    "311.00.189.00",    # Sexuelle Nötigung (Art. 189)
    "311.00.190.00",    # Vergewaltigung (Art. 190)
    "311.00.198.00",    # Sexuelle Belästigungen (Art. 198)
    "311.00.T12",       # Total 12. Titel: Öffentlicher Frieden
    "311.00.261.A0",    # Diskriminierung und Aufruf zu Hass (Art. 261bis)
    "311.00.285.00",    # Gewalt und Drohung gegen Behörden und Beamte (Art. 285)
    "311.00.T20",       # Total 20. Titel: Bundesrechtliche Bestimmungen
]


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
    OUT.mkdir(parents=True, exist_ok=True)

    meta = json.loads(hole(f"{BASIS}/{TABELLE}/{TABELLE}.px"))
    (RAW / f"{TABELLE}_meta.json").write_bytes(
        json.dumps(meta, ensure_ascii=False, indent=1).encode())
    jahre = [v for v in meta["variables"] if v["code"] == "Jahr"][0]["values"]
    kt_code, kt_text = None, None
    for v in meta["variables"]:
        if v["code"] == "Kanton":
            kt_code, kt_text = v["values"], v["valueTexts"]
    delikt_text = {c: t for v in meta["variables"] if v["code"] == "Straftat"
                   for c, t in zip(v["values"], v["valueTexts"])}

    # Der PxWeb-Server bricht grosse Abfragen mit HTTP 403 ab (getestet:
    # 10 Deliktscodes = rund 41'000 Zellen gehen durch, alle 267 Codes nicht).
    # Deshalb wird in Blöcken von acht Delikten abgefragt und zusammengeführt.
    BLOCK = 8
    roh_zeilen = []
    for i in range(0, len(DELIKTE), BLOCK):
        block = DELIKTE[i:i + BLOCK]
        abfrage = {
            "query": [
                {"code": "Straftat", "selection": {"filter": "item", "values": block}},
                {"code": "Kanton", "selection": {"filter": "item", "values": kt_code}},
                {"code": "Ausführungsgrad", "selection": {"filter": "item", "values": ["0", "1", "2"]}},
                {"code": "Aufklärungsgrad", "selection": {"filter": "item", "values": ["0", "1", "2"]}},
                {"code": "Jahr", "selection": {"filter": "item", "values": jahre}},
            ],
            "response": {"format": "json"},
        }
        # Datenabruf: der POST geht an <dbid>/<tableid>.px (PxWebApi 2.0);
        # die Kürzestform <dbid> liefert nur die Tabellenliste zurück.
        teil = json.loads(hole(f"{BASIS}/{TABELLE}/{TABELLE}.px", abfrage))
        roh_zeilen.extend(teil["data"])
        print(f"  Block {i // BLOCK + 1}: {len(block)} Delikte, {len(teil['data'])} Zeilen")

    spalten = [c["code"] for c in teil["columns"]]
    roh = {"columns": teil["columns"], "data": roh_zeilen}
    (RAW / f"{TABELLE}.json").write_bytes(
        json.dumps(roh, ensure_ascii=False).encode())
    print(f"Rohantwort: {len(roh['data'])} Zeilen, Metadaten in {RAW}")
    zeilen = []
    for d in roh["data"]:
        # Der Wert steht als ein-elementige Liste in "values"; die Spaltencodes
        # der Schlüsseldimensionen entsprechen den Codes aus den Metadaten.
        r = dict(zip(spalten, d["key"]))
        wert = d["values"][0]
        zeilen.append({
            "kanton_code": r["Kanton"],
            "kanton": kt_text[kt_code.index(r["Kanton"])],
            "delikt_code": r["Straftat"],
            "delikt": delikt_text[r["Straftat"]],
            "ausfuehrung": {"0": "total", "1": "vollendet", "2": "versucht"}[r["Ausführungsgrad"]],
            "aufklaerung": {"0": "total", "1": "unaufgeklärt", "2": "aufgeklärt"}[r["Aufklärungsgrad"]],
            "jahr": int(r["Jahr"]),
            "faelle": None if wert in ("", None, "..") else int(wert),
        })
    ziel = OUT / "ch_pks_kantone.csv"
    with open(ziel, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(zeilen[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    print(f"{ziel.name}: {len(zeilen)} Zeilen | {len(DELIKTE)} Delikte | "
          f"{len(kt_code)} Kantone | {len(jahre)} Jahre")

    # Kontrollwerte: StGB-Total je Jahr (Schweiz), Muster gegen BFS-Publikation
    total = [z for z in zeilen if z["kanton_code"] == "8100"
             and z["delikt_code"] == "311.00.T0"
             and z["ausfuehrung"] == "total" and z["aufklaerung"] == "total"]
    for z in sorted(total, key=lambda x: x["jahr"]):
        print(f"  {z['jahr']}: {z['faelle']:>9,} StGB-Straftaten (Schweiz)".replace(",", "'"))


if __name__ == "__main__":
    main()
