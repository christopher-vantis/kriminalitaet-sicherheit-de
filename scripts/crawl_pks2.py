#!/usr/bin/env python3
"""Überarbeiteter BKA-PKS-Crawler mit korrektem Link-Resolver.
BKA schreibt site-root-relative Links OHNE führenden Slash (DE/..., SharedDocs/...).
Nur relevante PKS-Pfade werden verfolgt; alle Download-URLs gesammelt."""
import urllib.request, urllib.parse, re, json, time, html, sys

BASE = "https://www.bka.de"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
DELAY = 1.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/pks_urls2.json"
MAXPAGES = int(sys.argv[2]) if len(sys.argv) > 2 else 600

YEARS = [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012]
PKS = "DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik"
START = [f"{BASE}/{PKS}/PKS{y}/pks{y}_node.html" for y in YEARS]
START += [f"{BASE}/{PKS}/AeltereAusgaben/aeltereAusgaben_node.html"]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", "replace")

def resolve(href, baseurl):
    if href.startswith("http"):
        return href
    if href.startswith("#"):
        return None
    if href.startswith("/"):
        return BASE + href
    # site-root-relativ (BKA-Eigenheit)
    if href.startswith(("DE/", "EN/", "SharedDocs/", "SiteGlobals/", "_config/")):
        return BASE + "/" + href
    # echt relativ zur aktuellen Seite
    return urllib.parse.urljoin(baseurl, href)

def extract_links(htmltext, baseurl):
    out = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', htmltext, re.S):
        href = m.group(1).strip()
        if not href or href.startswith(("mailto:", "javascript:")):
            continue
        txt = re.sub(r'<[^>]+>', '', m.group(2))
        txt = html.unescape(re.sub(r'\s+', ' ', txt)).strip()
        full = resolve(href, baseurl)
        if full:
            out.append((full, txt))
    return out

def classify(url):
    u = urllib.parse.urlparse(url)
    p = urllib.parse.unquote(u.path).lower()
    jahr = ""
    for j in range(2002, 2026):
        if f"/{j}/" in p or f"pks{j}" in p or f"{j}ergebnisse" in p:
            jahr = str(j)
            break
    kat = "sonstiges"
    if "zeitreihe" in p: kat = "zeitreihen"
    elif "faelle" in p or "falltabelle" in p: kat = "faelle"
    elif "opfer" in p: kat = "opfer"
    elif "tatverdaecht" in p: kat = "tatverdaechtige"
    elif "belastung" in p: kat = "belastungszahlen"
    elif "interpretation" in p or "straftatenkatalog" in p or "summenschluessel" in p or "tabellenbeschreibung" in p: kat = "interpretation"
    elif "aenderungsnachweis" in p or "nderungsnachweis" in p: kat = "aenderungsnachweis"
    elif "jahrbuch" in p or "jahrbuecher" in p or "imk" in p: kat = "jahrbuch"
    elif "ausland" in p: kat = "ausland"
    elif "richtlinien" in p or "rili" in p: kat = "richtlinien"
    elif "bevoelkerung" in p or "wohnbev" in p: kat = "bevoelkerung"
    raum = ""
    if "landfalltabelle" in p or "/land/" in p or "laenderkreise" in p: raum = "laender"
    elif "bundfalltabelle" in p or "bundopfer" in p or "bundtv" in p or "bundbelastung" in p or "bkatabellen" in p: raum = "bund"
    elif "kreis" in p: raum = "kreise"
    elif "stadt" in p or "staedte" in p: raum = "staedte"
    elif "standardtabellen" in p: raum = "standard"
    return jahr, kat, raum

def is_download(url):
    u = urllib.parse.urlparse(url)
    p = urllib.parse.unquote(u.path).lower()
    return ("__blob=publicationfile" in url.lower() or
            p.endswith(".xlsx") or p.endswith(".csv") or p.endswith(".pdf") or p.endswith(".zip"))

def relevant(url):
    u = urllib.parse.urlparse(url)
    p = urllib.parse.unquote(u.path).lower()
    return ("polizeilichekriminalstatistik" in p) and (
        p.endswith(".html") or is_download(url))

downloads = {}
queue = list(START)
visited = set()

while queue and len(visited) < MAXPAGES:
    url = queue.pop(0)
    if url in visited:
        continue
    visited.add(url)
    try:
        h = get(url)
    except Exception as e:
        print(f"ERR {url} {e}", flush=True)
        time.sleep(DELAY)
        continue
    for href, txt in extract_links(h, url):
        if not relevant(href):
            continue
        if is_download(href):
            if href not in downloads:
                j, k, r = classify(href)
                downloads[href] = {"url": href, "linktext": txt[:110], "jahr": j,
                                   "kategorie": k, "raum": r}
        else:
            if href not in visited and href not in queue:
                queue.append(href)
    print(f"[{len(visited)}/{MAXPAGES}] {url.split('/PKS')[-1][:40]} -> {len(downloads)} Dateien", flush=True)
    time.sleep(DELAY)

json.dump(list(downloads.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nGESAMT: {len(downloads)} Download-URLs -> {OUT}", flush=True)
