#!/usr/bin/env python3
"""Gezielter Crawl der Bundes-/Laender-Fall- und Opfertabellen 2019-2025.
Diese liegen DIREKT auf den Tabellen-Unterseiten (bundfalltabellen.html etc.)."""
import urllib.request, urllib.parse, re, json, time, html, sys

BASE = "https://www.bka.de"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
DELAY = 1.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/pks_urls4.json"
PKS = "DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik"

# 2025er Tabellen-Seiten direkt (bekannte URLs)
START = [
    f"{BASE}/{PKS}/PKS2025/pksTabellen_Interpretationshilfen/BundFalltabellen/bundfalltabellen.html",
    f"{BASE}/{PKS}/PKS2025/pksTabellen_Interpretationshilfen/LandFalltabellen/landFalltabellen.html",
    f"{BASE}/{PKS}/PKS2025/pksTabellen_Interpretationshilfen/BundOpfertabellen/bundopfertabellen.html",
    f"{BASE}/{PKS}/PKS2025/pksTabellen_Interpretationshilfen/LandOpfertabellen/landOpfertabellen.html",
]
# 2019-2024: pksTabellen_node.html als Einstieg (fuehrt zu ThematischeGliederung -> Tabellen-Seiten)
for y in [2019, 2020, 2021, 2022, 2023, 2024]:
    START.append(f"{BASE}/{PKS}/PKS{y}/PKSTabellen/pksTabellen_node.html")

KEYWORDS = ["bundfalltabelle", "landfalltabelle", "bundopfertabelle", "landopfertabelle",
            "thematischegliederung", "tabellenthema", "raumlichegliederung", "r%C3%A4umlichegliederung",
            "pkstabellen/pkstabellen", "pksTabellen_node"]

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
    for j in range(2019, 2026):
        if f"/{j}/" in p: jahr = str(j); break
    kat = "sonstiges"
    if "zeitreihe" in p: kat = "zeitreihen"
    elif "opfer" in p: kat = "opfer"
    elif "faelle" in p or "falltabelle" in p: kat = "faelle"
    elif "tatverdaecht" in p: kat = "tatverdaechtige"
    elif "belastung" in p: kat = "belastungszahlen"
    raum = ""
    if "/land/" in p or "landfalltabelle" in p or "laender" in p: raum = "laender"
    elif "/bund/" in p or "bundfalltabelle" in p or "bundopfer" in p: raum = "bund"
    return jahr, kat, raum

def is_xlsx(url):
    return urllib.parse.unquote(urllib.parse.urlparse(url).path).lower().endswith(".xlsx")

downloads = {}
queue = list(START)
visited = set()
while queue:
    url = queue.pop(0)
    if url in visited: continue
    visited.add(url)
    try:
        h = get(url)
    except Exception as e:
        print(f"ERR {url} {e}", flush=True); time.sleep(DELAY); continue
    for href, txt in extract_links(h, url):
        if is_xlsx(href):
            if href not in downloads:
                j, k, r = classify(href)
                downloads[href] = {"url": href, "linktext": txt[:100], "jahr": j, "kategorie": k, "raum": r}
        else:
            pl = urllib.parse.unquote(urllib.parse.urlparse(href).path).lower()
            if any(kw in pl for kw in KEYWORDS) and pl.endswith(".html"):
                if href not in visited and href not in queue:
                    queue.append(href)
    print(f"[{len(visited)}] {url.split('/PKS')[-1][:42]} -> {len(downloads)}", flush=True)
    time.sleep(DELAY)

json.dump(list(downloads.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nGESAMT: {len(downloads)} -> {OUT}", flush=True)
