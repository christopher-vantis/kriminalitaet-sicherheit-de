#!/usr/bin/env python3
"""Fokussierter Nach-Crawl fuer PKS 2019-2024 Tabellen (wurden im Haupt-Crawl
wegen Seiten-Limit verpasst). Nutzt denselben korrekten Resolver."""
import urllib.request, urllib.parse, re, json, time, html, sys

BASE = "https://www.bka.de"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
DELAY = 1.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/pks_urls3.json"
PKS = "DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik"

START = []
for y in [2019, 2020, 2021, 2022, 2023, 2024]:
    START.append(f"{BASE}/{PKS}/PKS{y}/PKSTabellen/pksTabellen_node.html")
    START.append(f"{BASE}/{PKS}/PKS{y}/Interpretationshilfen/interpretationshilfen_node.html")
    START.append(f"{BASE}/{PKS}/PKS{y}/Aenderungsnachweis/aenderungsnachweis_node.html")
START += [f"{BASE}/{PKS}/PKS2021/AusgewaehlteInformationenBund/AusgewaehlteInformationenBund_node.html",
          f"{BASE}/{PKS}/PKS2022/AusgewaehlteInformationenBund/AusgewaehlteInformationenBund_node.html"]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", "replace")

def resolve(href, baseurl):
    if href.startswith("http"): return href
    if href.startswith("#"): return None
    if href.startswith("/"): return BASE + href
    if href.startswith(("DE/", "EN/", "SharedDocs/", "SiteGlobals/", "_config/")):
        return BASE + "/" + href
    return urllib.parse.urljoin(baseurl, href)

def extract_links(h, baseurl):
    out = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h, re.S):
        href = m.group(1).strip()
        if not href or href.startswith(("mailto:", "javascript:")): continue
        txt = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(2)))).strip()
        full = resolve(href, baseurl)
        if full: out.append((full, txt))
    return out

def classify(url):
    p = urllib.parse.unquote(urllib.parse.urlparse(url).path).lower()
    jahr = ""
    for j in range(2015, 2026):
        if f"/{j}/" in p or f"pks{j}" in p: jahr = str(j); break
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
    p = urllib.parse.unquote(urllib.parse.urlparse(url).path).lower()
    return ("__blob=publicationfile" in url.lower() or
            p.endswith((".xlsx", ".csv", ".pdf", ".zip")))

def relevant(url):
    p = urllib.parse.unquote(urllib.parse.urlparse(url).path).lower()
    return "polizeilichekriminalstatistik" in p and (p.endswith(".html") or is_download(url))

downloads = {}
queue = list(START)
visited = set()
MAX = 250
while queue and len(visited) < MAX:
    url = queue.pop(0)
    if url in visited: continue
    visited.add(url)
    try:
        h = get(url)
    except Exception as e:
        print(f"ERR {url} {e}", flush=True); time.sleep(DELAY); continue
    for href, txt in extract_links(h, url):
        if not relevant(href): continue
        if is_download(href):
            if href not in downloads:
                j, k, r = classify(href)
                downloads[href] = {"url": href, "linktext": txt[:110], "jahr": j, "kategorie": k, "raum": r}
        else:
            if href not in visited and href not in queue:
                queue.append(href)
    print(f"[{len(visited)}/{MAX}] {url.split('/PKS')[-1][:45]} -> {len(downloads)}", flush=True)
    time.sleep(DELAY)

json.dump(list(downloads.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nGESAMT: {len(downloads)} -> {OUT}", flush=True)
