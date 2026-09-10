#!/usr/bin/env python3
"""
build_app_static.py — JavaScript-freie Fassung der Bundesland-App
=================================================================
Erzeugt dashboard/deutschland_app_static.html: die Deutschlandkarte als Bild
(damit auch in Viewern ohne JavaScript sichtbar), darunter alle Kennzahlen als
reine HTML-Tabellen. Klein, robust, für das Handy.

Die Karte wird aus derselben SVG-Geometrie gerendert, die auch die interaktive
App nutzt (GISCO NUTS-1).
"""
import csv
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
D = ROOT / "dashboard/data"
ZIEL = ROOT / "dashboard/deutschland_app_static.html"
TMP = ROOT / "dashboard/_static_tmp"


def lies(p, delim=";"):
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=delim))


def z(v, d=0):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    s = f"{f:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def karte_als_bild(svg_json):
    """Rendert die SVG-Karte mit Chromium und gibt Pfad zum JPEG zurück."""
    TMP.mkdir(exist_ok=True)
    teile = []
    KUERZEL = {"DE1": "BW", "DE2": "BY", "DE3": "BE", "DE4": "BB", "DE5": "HB",
               "DE6": "HH", "DE7": "HE", "DE8": "MV", "DE9": "NI", "DEA": "NW",
               "DEB": "RP", "DEC": "SL", "DED": "SN", "DEE": "ST", "DEF": "SH", "DEG": "TH"}
    for nuts, v in svg_json.items():
        if nuts == "_viewbox":
            continue
        teile.append(f'<path d="{v["d"]}" fill="#c3e2dd" stroke="#ffffff" stroke-width="1.8"/>')
        if v.get("label"):
            gross = nuts in ("DE3", "DE5", "DE6", "DEC")
            teile.append(
                f'<text x="{v["label"][0]}" y="{v["label"][1]}" text-anchor="middle" '
                f'dominant-baseline="middle" font-family="sans-serif" font-weight="700" '
                f'font-size="{11 if gross else 15}" fill="#12100e" stroke="#ffffff" '
                f'stroke-width="3" paint-order="stroke">{KUERZEL[nuts]}</text>')
    html = (f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
            f'body{{margin:0;background:#fff;font-family:sans-serif}}'
            f'svg{{width:1000px;height:auto;display:block}}</style></head><body>'
            f'<svg viewBox="{svg_json["_viewbox"]}">{"".join(teile)}</svg></body></html>')
    quelle = TMP / "karte.html"
    quelle.write_text(html, encoding="utf-8")
    png = TMP / "karte.png"
    subprocess.run(["chromium", "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--virtual-time-budget=6000",
                    "--window-size=1000,1360", f"--screenshot={png}",
                    f"file://{quelle}"], check=True, capture_output=True, timeout=180)
    jpg = TMP / "karte.jpg"
    from PIL import Image
    im = Image.open(png).convert("RGB")
    im.thumbnail((900, 1300))
    im.save(jpg, "JPEG", quality=82, optimize=True)
    return jpg


def main():
    svg = json.loads((OUT / "bundeslaender_svg.json").read_text(encoding="utf-8"))
    ind = {r["bundesland"]: r for r in lies(OUT / "laender_indikatoren.csv")}
    pks = {}
    for r in lies(OUT / "pks_laender_2025.csv"):
        pks.setdefault(r["bundesland"], {})[r["delikt"]] = r
    ess = {r["bundesland"]: r for r in lies(D / "ess_bundeslaender.csv")}
    namen = sorted(ind)

    import base64
    bild = karte_als_bild(svg)
    b64 = base64.b64encode(bild.read_bytes()).decode()

    # Gesamtzeilen
    ges_faelle = sum(float(pks[n]["Straftaten insgesamt"]["faelle"]) for n in namen)
    ges_ew = sum(float(ind[n]["bevoelkerung_2025"]) for n in namen)
    ges_aufg = sum(float(pks[n]["Straftaten insgesamt"]["aufgeklaert"]) for n in namen)

    def zeile_land(n):
        r = ind[n]
        k = pks[n].get("Straftaten insgesamt", {})
        e = ess.get(n, {})
        uns = e.get("unsicher_pct", "")
        bel = "grau" if e.get("unsicher_belastbar", "").startswith("nein") else ""
        return (f'<tr><td class="land">{n}</td>'
                f'<td class="num">{z(r["bevoelkerung_2025"])}</td>'
                f'<td class="num">{z(r["bip_je_ew_2024"])}</td>'
                f'<td class="num">{z(r["verfuegbares_einkommen_2024"])}</td>'
                f'<td class="num">{z(r["auslaenderanteil_pct"], 1)}</td>'
                f'<td class="num">{z(k.get("faelle"))}</td>'
                f'<td class="num">{z(k.get("hz"))}</td>'
                f'<td class="num">{z(k.get("aq"), 1)}</td>'
                f'<td class="num {bel}">{z(uns, 1)}</td></tr>')

    def zeile_delikte(n):
        rows = []
        for d, v in pks[n].items():
            if d == "Straftaten insgesamt":
                continue
            rows.append(f'<tr><td>{d}</td><td class="num">{z(v["faelle"])}</td>'
                        f'<td class="num">{z(v["hz"])}</td><td class="num">{z(v["aq"], 1)}</td></tr>')
        return "".join(rows)

    bloecke = []
    for n in namen:
        e = ess.get(n, {})
        bloecke.append(f"""
<details class="land-box">
  <summary>{n}</summary>
  <div class="land-inhalt">
    <p class="kennzahlen">
      <b>{z(ind[n]['bevoelkerung_2025'])}</b> Einwohner ·
      <b>{z(ind[n]['flaeche_km2'])}</b> km² ·
      <b>{z(ind[n]['dichte'], 1)}</b> Einw./km² ·
      <b>{z(ind[n]['bip_je_ew_2024'])}</b> € BIP je Einw. ·
      <b>{z(ind[n]['mh_pct'], 1)} %</b> mit Migrationshintergrund ·
      <b>{z(ind[n]['auslaenderanteil_pct'], 1)} %</b> Ausländer ·
      <b>{z(ind[n]['alq_2025'], 1)} %</b> Arbeitslosenquote
    </p>
    <p class="kennzahlen">
      Unsicherheitsgefühl: <b>{z(e.get('unsicher_pct'), 1)} %</b>
      (95-%-Intervall {z(e.get('ki_lo'), 1)}–{z(e.get('ki_hi'), 1)} %, n = {e.get('n','—')})
      {'<em> — kleine Stichprobe, nur eingeschränkt belastbar</em>' if str(e.get('unsicher_belastbar','')).startswith('nein') else ''}
    </p>
    <table class="tabelle">
      <thead><tr><th>Delikt (2025)</th><th class="num">Fälle</th><th class="num">je 100.000</th><th class="num">aufgeklärt</th></tr></thead>
      <tbody>{zeile_delikte(n)}</tbody>
    </table>
  </div>
</details>""")

    schrift_css = ""
    _sp = pathlib.Path(__file__).resolve().parent / "fonts" / "plex.css"
    if _sp.exists():
        schrift_css = _sp.read_text(encoding="utf-8")

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kriminalität und Sicherheit in Deutschland — Zahlen je Bundesland</title>
<style>{schrift_css}
:root{{--teal:#0f766e;--teal-hell:#3d9a92;--akzent:#a16207;--ink:#12100e;--text:#3d3833;--muted:#6b645e;--line:#e7e2dc;--bg:#faf8f5}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font-size:16px;line-height:1.6;
 font-family:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}}
header{{background:#12100e;color:#fff;
 padding:34px 18px 28px}}
h1{{margin:0 0 8px;font-size:clamp(1.35rem,4.6vw,2rem);line-height:1.2}}
header p{{margin:0;opacity:.94;max-width:60ch;font-size:.95rem}}
main{{max-width:1000px;margin:0 auto;padding:20px 14px 60px}}
.karte{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:14px;text-align:center;
 box-shadow:0 10px 30px -24px rgba(15,23,42,.4)}}
.karte img{{width:100%;max-width:720px;height:auto;display:block;margin:0 auto}}
.karte figcaption{{font-size:.85rem;color:var(--muted);margin-top:8px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);
 border-radius:16px;overflow:hidden;font-size:.9rem;margin:14px 0;border:1px solid var(--line)}}
th{{background:#f5f2ee;text-align:left;padding:10px 8px;font-size:.72rem;text-transform:uppercase;
 letter-spacing:.06em;color:var(--muted);font-weight:650}}
td{{padding:10px 8px;border-top:1px solid #f3efea}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
td.land{{font-weight:600;color:var(--ink)}}
td.grau{{color:var(--muted)}}
.huelle{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
details.land-box{{background:#fff;border:1px solid var(--line);border-radius:14px;
 padding:12px 14px;margin:10px 0}}
details.land-box summary{{cursor:pointer;font-weight:650;color:var(--teal);font-size:1rem}}
details.land-box[open] summary{{margin-bottom:8px}}
.land-inhalt p{{margin:6px 0}}
.land-inhalt .kennzahlen{{font-size:.9rem}}
.land-inhalt .tabelle{{margin:8px 0 2px}}
footer{{max-width:1000px;margin:0 auto;padding:10px 16px 50px;color:var(--muted);font-size:.82rem}}
h2{{font-size:1.15rem;color:var(--ink);margin:26px 0 6px}}
.hinweis{{background:#fdf6f1;border-left:4px solid var(--akzent);border-radius:0 14px 14px 0;
 padding:12px 14px;font-size:.91rem;color:#7c2d12;margin:16px 0}}
@media (max-width:620px){{ table{{font-size:.82rem}} th,td{{padding:8px 6px}} }}
</style>
</head>
<body>
<header>
  <h1>Kriminalität und Sicherheit in Deutschland</h1>
  <p>Zahlen für die Republik und für jedes Bundesland — als Tabelle, ohne JavaScript,
  in jedem Browser lesbar. Die interaktive Fassung mit Klick-Karte ist
  <code>deutschland_app.html</code>.</p>
</header>
<main>
  <figure class="karte">
    <img src="data:image/jpeg;base64,{b64}" alt="Deutschlandkarte mit den 16 Bundesländern">
    <figcaption>Die 16 Bundesländer als Kartenbild (Geometrie: Eurostat/GISCO, CC BY 4.0).</figcaption>
  </figure>

  <div class="hinweis">
    <strong>Republik 2025:</strong> {z(ges_ew)} Einwohner,
    {z(ges_faelle)} erfasste Straftaten ({z(ges_faelle/ges_ew*100000)} je 100.000 Einwohner),
    Aufklärungsquote {z(ges_aufg/ges_faelle*100, 1)} %.
  </div>

  <h2>Alle Bundesländer im Vergleich</h2>
  <div class="huelle">
  <table>
    <thead><tr><th>Bundesland</th><th class="num">Einwohner</th><th class="num">BIP/EW (€)</th>
    <th class="num">verf. Eink. (€)</th><th class="num">Ausländer (%)</th>
    <th class="num">mit Migrations&shy;hintergrund (%)</th><th class="num">Arbeitslose (%)</th>
    <th class="num">Fälle 2025</th><th class="num">je 100.000</th><th class="num">aufgeklärt (%)</th>
    <th class="num">unsicher (%)</th></tr></thead>
    <tbody>{"".join(zeile_land(n) for n in namen)}</tbody>
  </table>
  </div>
  <p style="font-size:.85rem;color:var(--muted)">Quellen: BKA PKS 2025 (Länder-Grundtabelle);
  Destatis/Statistikportal; VGR der Länder; ESS Runden 5–11 (eigene Berechnung, gewichtet).
  Graue Werte beim Unsicherheitsgefühl: Fallzahl zu klein für belastbare Aussagen.</p>

  <h2>Die einzelnen Bundesländer</h2>
  {"".join(bloecke)}
</main>
<footer>
  <p><strong>Zur Einordnung.</strong> Registrierte Fälle sind polizeilich bekannt gewordene
  Vorgänge — kein Nachweis einer Straftat und keine Verurteilung. Die Häufigkeitszahl bezieht
  Fälle auf die Wohnbevölkerung; in Stadtstaaten erhöhen Pendler, Gäste und
  Mehrfacherfassungen den Wert, ohne dass die Wohnbevölkerung diese Fälle verursacht.
  Die Länderwerte zum Sicherheitsgefühl stammen aus gepoolten Befragungswellen mit kleinen
  Fallzahlen; die Intervalle sind Näherungen ohne Designeffekt. Zusammenhänge sind bivariat
  und nicht um Drittvariablen bereinigt — sie belegen keine Ursachen.</p>
</footer>
</body>
</html>"""
    ZIEL.write_text(html, encoding="utf-8")
    print(f"-> {ZIEL} ({ZIEL.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
