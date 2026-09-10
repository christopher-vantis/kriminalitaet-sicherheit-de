#!/usr/bin/env python3
"""Wandelt die gecrawlten PKS-URLs in eine fetch.py-Download-Liste um.
Filtert nach Auftragskriterien und weist Zielverzeichnis + Metadaten zu."""
import json, urllib.parse, collections, sys, os

SRC = sys.argv[1] if len(sys.argv) > 1 else "/tmp/pks_urls2.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "scripts/fetch_pks.json"

raw = json.load(open(SRC, encoding="utf-8"))

def fname(url):
    p = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    return os.path.basename(p)

def fmt(url):
    p = urllib.parse.unquote(urllib.parse.urlparse(url).path).lower()
    if p.endswith(".xlsx"): return "xlsx"
    if p.endswith(".csv"): return "csv"
    if p.endswith(".pdf"): return "pdf"
    if p.endswith(".zip"): return "zip"
    return "xlsx"

def target_dir(e):
    kat = e["kategorie"]
    raum = e["raum"]
    jahr = e["jahr"]
    if kat == "zeitreihen": base = "data/raw/pks/zeitreihen"
    elif kat == "ausland": base = "data/raw/pks/ausland"
    elif kat in ("interpretation", "aenderungsnachweis", "richtlinien"): base = "data/raw/pks/interpretationshilfen"
    elif kat == "jahrbuch": base = "data/raw/pks/jahresberichte"
    elif kat == "bevoelkerung": base = "data/raw/pks/zeitreihen"
    elif kat == "faelle":
        base = "data/raw/pks/laender" if raum == "laender" else "data/raw/pks/bund"
    elif kat == "opfer":
        base = "data/raw/pks/bund"
    else:
        base = "data/raw/pks/bund"
    # Jahr-Unterordner, um Dateinamen-Kollisionen ueber Berichtsjahre hinweg zu vermeiden
    if jahr:
        return f"{base}/{jahr}"
    return base

def wanted(e):
    kat = e["kategorie"]
    raum = e["raum"]
    jahr = e["jahr"]
    if not jahr:
        return False
    try:
        j = int(jahr)
    except ValueError:
        return False
    # Interpretationshilfen + Aenderungsnachweis + Richtlinien: 2015-2025
    if kat in ("interpretation", "aenderungsnachweis", "richtlinien"):
        return 2015 <= j <= 2025
    # Zeitreihen: nur 2015, 2020, 2025 (Kontrolljahre + aktuell)
    if kat == "zeitreihen":
        return jahr in ("2015", "2020", "2025")
    # Bevoelkerungsdaten (Referenz): 2015, 2020, 2025
    if kat == "bevoelkerung":
        return jahr in ("2015", "2020", "2025")
    # Jahrbuecher: 2002-2014 (Belegquelle)
    if kat == "jahrbuch":
        return 2002 <= j <= 2014
    # Ausland: 2024-2025
    if kat == "ausland":
        return jahr in ("2024", "2025")
    # Bundes- und Laender-Falltabellen 2015-2025
    if kat == "faelle":
        return 2015 <= j <= 2025 and raum in ("bund", "laender", "standard", "")
    # Bundes-Opfertabellen 2015-2025
    if kat == "opfer":
        return 2015 <= j <= 2025 and raum in ("bund", "standard", "")
    # Tatverdaechtigen-/Belastungszahlen-Jahrestabellen NICHT gefordert (nur als Zeitreihen)
    return False

# dedupe nach URL
seen = {}
for e in raw:
    u = e["url"]
    if u not in seen:
        seen[u] = e
entries = list(seen.values())

# Analyse
print("Gesamt eindeutig:", len(entries))
by = collections.Counter((e["jahr"], e["kategorie"], e["raum"]) for e in entries)
for k in sorted(by, key=lambda x: (x[0], x[1], x[2])):
    print(f"  {k[0]:5s} {k[1]:18s} {k[2]:10s} : {by[k]}")

sel = [e for e in entries if wanted(e)]
print("\nAUSGEWÄHLT:", len(sel))

out = []
for e in sel:
    out.append({
        "url": e["url"],
        "rel_dir": target_dir(e),
        "berichtsjahr": e["jahr"],
        "quelle_institution": "Bundeskriminalamt",
        "lizenz": "dl-de/by-2-0",
        "format": fmt(e["url"]),
        "bemerkung": f"{e['kategorie']} {e['raum']}".strip()
    })
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Geschrieben:", OUT, f"({len(out)} Einträge)")
