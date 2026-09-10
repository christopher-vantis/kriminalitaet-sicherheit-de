#!/usr/bin/env python3
"""Lädt kaputte (<2KB) BKA-Dateien mit korrigierter URL nach."""
import csv, os, urllib.request, hashlib, time, datetime, html

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
base = os.getcwd()

with open("data/manifest.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter=";")
    fieldnames = reader.fieldnames
    rows = list(reader)

def clean_url(u):
    u = html.unescape(u)
    u = u.replace("&view=render[DownloadAuthentication]", "")
    return u

fixed = []
for r in rows:
    rel = r["relativer_pfad"]
    dest = os.path.join(base, rel)
    if not os.path.exists(dest):
        continue
    size = os.path.getsize(dest)
    if size >= 2000:
        continue
    url = clean_url(r["quell_url"])
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except Exception as e:
        print(f"FEHLER {rel}: {e}")
        continue
    if data[:4] == b"%PDF" or len(data) > 10000:
        with open(dest, "wb") as f:
            f.write(data)
        r["dateigroesse_bytes"] = str(len(data))
        r["sha256"] = hashlib.sha256(data).hexdigest()
        r["quell_url"] = url
        fixed.append((rel, len(data)))
        print(f"  OK {rel} -> {len(data)} B")
    else:
        print(f"  KEINE DATEI {rel}: {data[:80]!r}")
    time.sleep(1.5)

with open("data/manifest.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
    w.writeheader()
    for r in rows:
        w.writerow(r)

with open("docs/fetch_log.txt", "a", encoding="utf-8") as f:
    for rel, sz in fixed:
        f.write(f"{datetime.date.today()} {datetime.datetime.now().strftime('%H:%M:%S')} | 200 (NACHLADUNG) | {rel} | {sz} B\n")

print(f"Behoben: {len(fixed)}")
