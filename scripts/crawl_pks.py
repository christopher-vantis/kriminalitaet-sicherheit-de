#!/usr/bin/env python3
"""Crawlt die BKA-PKS-Unterseiten und sammelt alle Download-URLs (xlsx/csv/pdf)
samt Klassifikation (Jahr, Kategorie, Raum) in eine JSON-Datei.
Nur Pfade unter .../PolizeilicheKriminalstatistik/ bzw. .../SharedDocs/.../PolizeilicheKriminalstatistik/."""
import urllib.request, urllib.parse, re, json, time, html, sys, os

BASE = "https://www.bka.de"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
DELAY = 1.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/pks_urls.json"

START = [
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2025/pks2025_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2024/pks2024_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2023/pks2023_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2022/pks2022_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2021/pks2021_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2020/pks2020_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2019/pks2019_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2018/pks2018_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2017/pks2017_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2016/pks2016_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2015/pks2015_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2014/pks2014_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2013/pks2013_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2012/pks2012_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/AeltereAusgaben/aeltereAusgaben_node.html",
    # 2025er Tabellen-Unterseiten direkt (schneller)
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2025/pksTabellen_Interpretationshilfen/BundFalltabellen/bundfalltabellen.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2025/pksTabellen_Interpretationshilfen/LandFalltabellen/landFalltabellen.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2025/pksTabellen_Interpretationshilfen/BundOpfertabellen/bundopfertabellen.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2025/pksTabellen_Interpretationshilfen/LandOpfertabellen/landOpfertabellen.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2025/pksTabellen_Interpretationshilfen/PKS-Ausland/PKS-AuslandFalltabellen/PKS-AuslandFalltabellen_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2025/pksTabellen_Interpretationshilfen/PKS-Ausland/PKS-AuslandTV/PKS-AuslandFalltabellenTV_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2025/pksTabellen_Interpretationshilfen/Zeitreihen/zeitreihen_node.html",
    "https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2025/pksTabellen_Interpretationshilfen/pksTabellen_Interpretationshilfen_node.html",
]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", "replace")

def extract_links(htmltext, baseurl):
    out = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', htmltext, re.S):
        href = m.group(1)
        txt = re.sub(r'<[^>]+>', '', m.group(2))
        txt = html.unescape(re.sub(r'\s+', ' ', txt)).strip()
        full = href
        if href.startswith("http"):
            pass
        elif href.startswith("/"):
            full = BASE + href
        else:
            full = urllib.parse.urljoin(baseurl, href)
        out.append((full, txt))
    return out

def classify(url):
    u = urllib.parse.urlparse(url)
    p = urllib.parse.unquote(u.path).lower()
    jahr = ""
    for j in range(2002, 2026):
        if f"/{j}/" in p or f"pks{j}" in p:
            jahr = str(j)
            break
    kat = "sonstiges"
    if "zeitreihe" in p: kat = "zeitreihen"
    elif "faelle" in p or "falltabelle" in p: kat = "faelle"
    elif "opfer" in p: kat = "opfer"
    elif "tatverdaecht" in p: kat = "tatverdaechtige"
    elif "belastung" in p: kat = "belastungszahlen"
    elif "interpretation" in p or "straftatenkatalog" in p or "summenschluessel" in p or "tabellenbeschreibung" in p or "hinweis" in p: kat = "interpretation"
    elif "aenderungsnachweis" in p or "nderungsnachweis" in p: kat = "aenderungsnachweis"
    elif "jahrbuch" in p or "jahrbuecher" in p or "imkbericht" in p or "imk" in p: kat = "jahrbuch"
    elif "ausland" in p: kat = "ausland"
    elif "richtlinien" in p or "rili" in p: kat = "richtlinien"
    elif "bevoelkerung" in p or "wohnbev" in p: kat = "bevoelkerung"
    raum = ""
    if "landfalltabelle" in p or "/land/" in p or "laender" in p or "land_": raum = "laender"
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

def is_relevant(url):
    u = urllib.parse.urlparse(url)
    p = urllib.parse.unquote(u.path)
    return ("polizeilichekriminalstatistik" in p.lower())

downloads = {}
queue = list(START)
visited = set()
max_pages = 220

while queue and len(visited) < max_pages:
    url = queue.pop(0)
    if url in visited:
        continue
    visited.add(url)
    try:
        h = get(url)
    except Exception as e:
        print(f"FEHLER {url}: {e}", flush=True)
        time.sleep(DELAY)
        continue
    for href, txt in extract_links(h, url):
        if not is_relevant(href):
            continue
        if is_download(href):
            if href not in downloads:
                jahr, kat, raum = classify(href)
                downloads[href] = {"url": href, "linktext": txt[:120], "jahr": jahr,
                                   "kategorie": kat, "raum": raum, "von_seite": url}
        else:
            # html-Unterseite: nur verfolgen wenn unter PKS-Pfad und noch nicht besucht
            if href not in visited and href not in queue and ".html" in urllib.parse.urlparse(href).path.lower():
                queue.append(href)
    print(f"[{len(visited)}/{max_pages}] {url} -> {len(downloads)} Dateien gefunden", flush=True)
    time.sleep(DELAY)

json.dump(list(downloads.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nGESAMT: {len(downloads)} Download-URLs -> {OUT}", flush=True)
