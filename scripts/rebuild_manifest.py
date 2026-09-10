#!/usr/bin/env python3
"""Baut manifest.csv sauber neu auf: aus Dateisystem (Groesse, sha256) + fetch-Listen (Metadaten).
Behebt auch das &amp;-Problem (HTML-Entity enthaelt ';', bricht CSV mit ';'-Delimiter)."""
import json, os, urllib.parse, hashlib, html, datetime, csv

base = os.getcwd()
UA = ""

def name_from_url(url):
    return urllib.parse.unquote(urllib.parse.urlparse(url).path).split("/")[-1]

# Alle fetch-Eintraege sammeln
entries = []
for fn in ["scripts/fetch_all.json", "scripts/fetch_eurostat.json"]:
    entries += json.load(open(fn, encoding="utf-8"))

abrufdatum = datetime.date.today().isoformat()

rows = []
matched = 0
missing = []
for e in entries:
    url = html.unescape(e["url"]).replace("&view=render[DownloadAuthentication]", "")
    rel_dir = e["rel_dir"].strip("/")
    fn = e.get("filename") or name_from_url(url)
    rel_path = f"{rel_dir}/{fn}"
    dest = os.path.join(base, rel_path)
    if not os.path.exists(dest):
        # Fallback: Datei im rel_dir suchen (Content-Disposition-Name kann abweichen)
        d = os.path.join(base, rel_dir)
        cands = [f for f in os.listdir(d)] if os.path.isdir(d) else []
        if len(cands) == 1:
            fn = cands[0]
            rel_path = f"{rel_dir}/{fn}"
            dest = os.path.join(base, rel_path)
    if not os.path.exists(dest):
        missing.append(rel_path)
        continue
    size = os.path.getsize(dest)
    with open(dest, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    fmt = e.get("format") or fn.rsplit(".", 1)[-1].lower()
    rows.append({
        "dateiname": fn,
        "relativer_pfad": rel_path,
        "quell_url": url,
        "quelle_institution": e.get("quelle_institution", ""),
        "berichtsjahr": str(e.get("berichtsjahr", "")),
        "version": e.get("version", ""),
        "abrufdatum": abrufdatum,
        "dateigroesse_bytes": str(size),
        "sha256": sha,
        "lizenz": e.get("lizenz", ""),
        "format": fmt,
        "bemerkung": (e.get("bemerkung") or "").replace(";", ",").replace("\n", " "),
    })
    matched += 1

fieldnames = ["dateiname", "relativer_pfad", "quell_url", "quelle_institution",
              "berichtsjahr", "version", "abrufdatum", "dateigroesse_bytes",
              "sha256", "lizenz", "format", "bemerkung"]
with open("data/manifest.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"Geschrieben: {matched} Zeilen (aus {len(entries)} Eintraegen)")
if missing:
    print("Nicht gefunden:", len(missing))
    for m in missing[:20]:
        print("  ", m)
