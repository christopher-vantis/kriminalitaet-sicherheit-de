#!/usr/bin/env python3
"""
Fetch-Skript für Projekt "Kriminalitätsdiskrepanz DE".

Lädt Dateien aus einer JSON-URL-Liste herunter, hält Rate-Limiting ein,
schreibt manifest.csv und fetch_log.txt fort. Rohdaten werden 1:1 gespeichert
(keine Umbenennung des vom Server gelieferten Dateinamens, kein Inhaltseingriff).

Aufruf:  python3 scripts/fetch.py <url_liste.json> [--base ABS_PFAD]
"""
import json, sys, os, time, hashlib, urllib.request, urllib.parse, datetime, argparse

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
DELAY = 1.5          # Sekunden zwischen Requests (Auftrags-Obergrenze 1 req/s)
MANIFEST_HEADER = ["dateiname", "relativer_pfad", "quell_url", "quelle_institution",
                   "berichtsjahr", "version", "abrufdatum", "dateigroesse_bytes",
                   "sha256", "lizenz", "format", "bemerkung"]


def parse_content_disposition(cd):
    """Dateiname aus Content-Disposition (auch filename*=UTF-8''...)."""
    if not cd:
        return None
    # filename*=UTF-8''name
    for part in cd.split(";"):
        part = part.strip()
        if part.lower().startswith("filename*=utf-8''"):
            return urllib.parse.unquote(part.split("''", 1)[1].strip().strip('"'))
    for part in cd.split(";"):
        part = part.strip()
        if part.lower().startswith("filename="):
            v = part.split("=", 1)[1].strip().strip('"')
            return urllib.parse.unquote(v)
    return None


def name_from_url(url):
    path = urllib.parse.urlparse(url).path
    name = os.path.basename(path)
    name = urllib.parse.unquote(name)
    return name or "download"


def fetch_one(entry, base):
    url = entry["url"]
    rel_dir = entry.get("rel_dir", "data/raw").strip("/")
    abs_dir = os.path.join(base, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)

    status = None
    final_url = url
    size = 0
    sha = ""
    filename = entry.get("filename") or ""
    abrufdatum = datetime.date.today().isoformat()

    log_line = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            status = resp.status
            final_url = resp.geturl()
            cd = resp.headers.get("Content-Disposition")
            if not filename:
                filename = parse_content_disposition(cd) or name_from_url(final_url)
            filename = os.path.basename(filename)  # kein Pfad-Traversal
            data = resp.read()
        size = len(data)
        sha = hashlib.sha256(data).hexdigest()
        dest = os.path.join(abs_dir, filename)
        with open(dest, "wb") as f:
            f.write(data)
        log_line = f"{abrufdatum} {datetime.datetime.now().strftime('%H:%M:%S')} | {status} | {url} | -> {os.path.join(rel_dir, filename)} | {size} B | sha256={sha}"
    except urllib.error.HTTPError as e:
        status = e.code
        log_line = f"{abrufdatum} {datetime.datetime.now().strftime('%H:%M:%S')} | {status} FEHLER | {url} | {e.reason}"
    except Exception as e:
        status = "ERR"
        log_line = f"{abrufdatum} {datetime.datetime.now().strftime('%H:%M:%S')} | ERR | {url} | {type(e).__name__}: {e}"

    # fetch_log
    with open(os.path.join(base, "docs", "fetch_log.txt"), "a", encoding="utf-8") as f:
        f.write((log_line or "") + "\n")

    # manifest (nur bei Erfolg)
    if status == 200 and size > 0:
        version = entry.get("version", "")
        rel_path = os.path.join(rel_dir, filename)
        row = [filename, rel_path, url, entry.get("quelle_institution", ""),
               str(entry.get("berichtsjahr", "")), version, abrufdatum,
               str(size), sha, entry.get("lizenz", ""), entry.get("format", ""),
               (entry.get("bemerkung", "") or "").replace(";", ",").replace("\n", " ")]
        with open(os.path.join(base, "data", "manifest.csv"), "a", encoding="utf-8") as f:
            f.write(";".join(row) + "\n")
        return (True, status, size, rel_path)
    return (False, status, 0, url)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url_liste")
    ap.add_argument("--base", default=None)
    args = ap.parse_args()
    base = args.base or os.getcwd()
    entries = json.load(open(args.url_liste, encoding="utf-8"))
    ok = fail = 0
    total = 0
    for i, e in enumerate(entries):
        success, status, size, where = fetch_one(e, base)
        if success:
            ok += 1
            total += size
            print(f"[{i+1}/{len(entries)}] OK   {where} ({size} B)")
        else:
            fail += 1
            print(f"[{i+1}/{len(entries)}] FAIL {status} {where}")
        time.sleep(DELAY)
    print(f"\nFERTIG: {ok} ok, {fail} fehlgeschlagen, {total/1e6:.2f} MB gesamt")


if __name__ == "__main__":
    main()
