#!/usr/bin/env python3
"""
build_static.py — statische Variante des Dashboards (ohne JavaScript)
=====================================================================
Erzeugt dashboard/index_static.html: dieselben 18 Diagramme, aber als
eingebettete Bilder (JPEG, base64) statt interaktiver Plotly-Grafiken.

Warum: In manchen mobilen Browsern und in den In-App-Viewern von Messenger-
Apps werden interaktive Diagramme nicht gerendert (JavaScript blockiert oder
Speicherlimit). Eine Version mit Bildern zeigt die Diagramme überall — auch
ohne JavaScript und ohne Internet.

Vorgehen: Die Figur-Daten werden aus index.html gelesen (dort liegen sie als
JSON je Diagramm), je Diagramm wird eine Minimalseite gerendert, mit Chromium
headless fotografiert und als JPEG eingebettet.
"""
import base64
import html as html_mod
import io
import json
import pathlib
import re
import subprocess

from PIL import Image

DASH = pathlib.Path(__file__).resolve().parent

ROOT = pathlib.Path(__file__).resolve().parent.parent
DASH = ROOT / "dashboard"
QUELLE = DASH / "index.html"
ZIEL = DASH / "index_static.html"
# PITFALL: Snap-Chromium kann NICHT nach /tmp schreiben -> Arbeitsordner
# liegt im Projektverzeichnis.
TMP = DASH / "_static_tmp"
TMP.mkdir(exist_ok=True)

PLOTLY_JS = DASH / "_plotly.js"


def plotly_js():
    """Plotly.js einmal aus der Quelldatei extrahieren."""
    if PLOTLY_JS.exists():
        return PLOTLY_JS.read_text(encoding="utf-8")
    text = QUELLE.read_text(encoding="utf-8")
    m = re.search(r"<script charset=\"utf-8\">(.*?)</script>", text, re.S)
    if not m:
        raise SystemExit("Plotly.js nicht in index.html gefunden")
    js = m.group(1)
    PLOTLY_JS.write_text(js, encoding="utf-8")
    return js


def figuren_lesen():
    text = QUELLE.read_text(encoding="utf-8")
    treffer = re.findall(
        r'<div class="chart" data-fig="(fig-[a-z]+)"[^>]*>.*?</div>\s*'
        r'<script type="application/json" id="fig-[a-z]+">(.*?)</script>',
        text, re.S)
    return treffer


def chart_bild(fig_id, fig_json, js):
    """Rendert ein einzelnes Diagramm und gibt ein JPEG als Bytes zurück."""
    hoehe = 420
    try:
        hoehe = int(json.loads(fig_json).get("layout", {}).get("height") or 420)
    except Exception:
        pass
    seite = TMP / f"{fig_id}.html"
    seite.write_text(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>html,body{margin:0;padding:0;background:#fff}"
        ".chart{width:1000px;margin:0 auto}</style></head><body>"
        f"<div class='chart' id='c'></div><script>{js}</script>"
        "<script>(function(){var f=" + fig_json + ";"
        "var l=f.layout||{};l.autosize=false;l.width=1000;l.height=" + str(hoehe) + ";"
        "Plotly.newPlot('c',f.data,l,{displayModeBar:false,staticPlot:true});"
        "})();</script></body></html>", encoding="utf-8")
    png = TMP / f"{fig_id}.png"
    subprocess.run(
        ["chromium", "--headless=new", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", f"--window-size=1000,{hoehe + 12}",
         "--virtual-time-budget=12000", f"--screenshot={png}",
         f"file://{seite}"],
        check=True, capture_output=True, timeout=180)
    im = Image.open(png).convert("RGB")
    puffer = io.BytesIO()
    im.save(puffer, format="JPEG", quality=84, optimize=True, progressive=True)
    return puffer.getvalue()


def main():
    js = plotly_js()
    figuren = figuren_lesen()
    print(f"{len(figuren)} Diagramme gefunden")

    quelltext = QUELLE.read_text(encoding="utf-8")
    # Kopf-/Fußteil und die Textbestandteile aus der interaktiven Fassung nutzen.
    # Das eingebettete Plotly.js (ca. 3,5 MB) wird entfernt — die statische
    # Fassung braucht kein JavaScript.
    kopf = re.sub(r'<script charset="utf-8">.*?</script>', "", quelltext.split("<nav>")[0], flags=re.S)
    kopf = kopf.replace("<title>", "<title>").replace(
        "<style>", "<style>\n.chart img{width:100%;height:auto;display:block;"
                   "border:1px solid #DCE1E8;border-radius:10px;background:#fff}\n")
    nav = re.search(r"<nav>.*?</nav>", quelltext, re.S).group(0)
    fuss_html = quelltext[quelltext.index("<footer>"):quelltext.index("</footer>") + 9]
    # KPI-Block: endet unmittelbar vor der ersten Sektion (sonst würden die
    # Originalsktionen ein zweites Mal eingefügt).
    m_kpi = re.search(r'<div class="kpis">(.*?)</div>\s*<section', quelltext, re.S)
    kpis_html = ('<div class="kpis">' + m_kpi.group(1) + "</div>") if m_kpi else ""

    sektionen = []
    for fig_id, fig_json in figuren:
        fid = fig_id.replace("fig-", "")
        jpeg = chart_bild(fig_id, fig_json, js)
        b64 = base64.b64encode(jpeg).decode("ascii")
        # Textbausteine der Sektion aus der interaktiven Fassung übernehmen
        m = re.search(
            rf'<section id="{fid}">(.*?)<div class="chart".*?</div>\s*<script.*?</script>(.*?)</section>',
            quelltext, re.S)
        titel = re.search(rf'<section id="{fid}"><h2>(.*?)</h2>', quelltext, re.S).group(1)
        lead = re.search(rf'<section id="{fid}">.*?<p class="lead">(.*?)</p>', quelltext, re.S).group(1)
        rest = m.group(2) if m else ""
        sektionen.append(
            f'<section id="{fid}"><h2>{titel}</h2><p class="lead">{lead}</p>'
            f'<div class="chart"><img src="data:image/jpeg;base64,{b64}" '
            f'alt="{html_mod.escape(titel)}" loading="lazy"></div>{rest}</section>')
        print(f"  {fid}: {len(jpeg)//1024} KB")

    html = (kopf.replace("</head>", "</head>").replace("</header>", "</header>") +
            nav + '<div class="wrap">' + kpis_html + "\n".join(sektionen) + fuss_html +
            "</div></body></html>")
    # Hinweis einfügen, dass dies die statische Fassung ist
    html = html.replace("<nav>", "<nav>").replace(
        '<p class="sub">Projekt 47',
        '<p class="sub">Statische Fassung (ohne JavaScript) · Projekt 47')
    ZIEL.write_text(html, encoding="utf-8")
    print(f"\nGeschrieben: {ZIEL} ({ZIEL.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
