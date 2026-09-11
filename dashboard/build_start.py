#!/usr/bin/env python3
"""
build_start.py — Startseite mit beiden Ländern
==============================================
Baut die Startseite der Website: Titel, kurze Beschreibung und zwei Karten
nebeneinander — Deutschland links, Schweiz rechts. Beide Karten sind anklickbar
und führen auf die jeweilige Länderfassung.

Die Startseite enthält bewusst keine Diagramme und keine Diagramm-Bibliothek:
Sie ist eine Tür, keine Auswertung, und lädt deshalb in Bruchteilen einer
Sekunde.

Reihenfolge beim Bauen (die Deutschland-Fassung entsteht in build_app.py):
    python3 build_app.py     # erzeugt dashboard/index.html  (Deutschland)
    python3 build_ch.py      # erzeugt dashboard/schweiz.html
    python3 build_start.py   # verschiebt Deutschland nach deutschland.html
                             # und legt die Startseite als index.html an

Ablauf von build_start.py:
  1. dashboard/index.html  ->  dashboard/deutschland.html  (nur wenn die Datei
     noch fehlt oder älter ist als index.html; so geht keine neuere Fassung
     verloren)
  2. dashboard/start.html  und  dashboard/index.html  ->  Startseite

Ausgabe: dashboard/index.html (Startseite), dashboard/deutschland.html,
         dashboard/start.html

Aufruf: python3 build_start.py
"""
import csv
import json
import pathlib
import shutil

import build_app as DE          # CSS und Schrift der Länderfassungen

ROOT = pathlib.Path(__file__).resolve().parent.parent
DASH = ROOT / "dashboard"
OUT = ROOT / "output"


def lies(pfad, delim=";"):
    """Liest eine CSV mit Kopfzeile."""
    with open(pfad, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=delim))


def z(x):
    """Wandelt einen Wert in float oder None."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def deutschland_zahlen():
    """Kennzahlen Deutschlands für die Startseite.

    Returns:
        dict: Einwohner, Fälle, Häufigkeitszahl, Unsicherheitsgefühl (2023).
    """
    pks = lies(OUT / "pks_laender_2025.csv")
    ind = lies(OUT / "laender_indikatoren.csv")
    bev = {r["bundesland"]: z(r["bevoelkerung_2025"]) for r in ind}
    faelle = sum(z(r["faelle"]) or 0 for r in pks
                 if r["delikt"] == "Straftaten insgesamt")
    einwohner = sum(v for v in bev.values() if v)
    unsicher = None
    agg = DASH / "data" / "ess_aggregate.csv"
    if agg.exists():
        zeilen = [r for r in lies(agg)
                  if r["ebene"] == "zeitreihe" and int(float(r["jahr"])) == 2023]
        if zeilen:
            unsicher = z(zeilen[0]["anteil"])
    return {"einwohner": einwohner, "faelle": faelle,
            "hz": round(1e5 * faelle / einwohner, 1), "unsicher": unsicher}


def schweiz_zahlen():
    """Kennzahlen der Schweiz für die Startseite.

    Returns:
        dict: Einwohner, Fälle, Häufigkeitszahl, Unsicherheitsgefühl (2023).
    """
    kz = lies(OUT / "ch_kantone_kennzahlen.csv")
    letztes = max(int(r["jahr"]) for r in kz)
    akt = [r for r in kz if int(r["jahr"]) == letztes]
    einwohner = sum(z(r["bevoelkerung"]) or 0 for r in akt)
    faelle = sum(z(r["faelle_stgb"]) or 0 for r in akt)
    unsicher = None
    agg = DASH / "data" / "ch_ess_aggregate.csv"
    if agg.exists():
        zeilen = [r for r in lies(agg)
                  if r["ebene"] == "gesamt" and r["kennzahl"] == "unsicher"
                  and int(float(r["jahr"])) == 2023]
        if zeilen:
            unsicher = z(zeilen[0]["anteil"])
    return {"einwohner": einwohner, "faelle": faelle,
            "hz": round(1e5 * faelle / einwohner, 1), "unsicher": unsicher}


def karte(geometrien, css_klasse):
    """Baut ein ruhiges Übersichtsbild eines Landes als SVG.

    Args:
        geometrien: Geometrien wie in output/*_svg.json (inkl. _viewbox).
        css_klasse: Klassenname für die Flächen (de | ch).

    Returns:
        str: SVG-Markup mit einem Titel je Fläche (native Tooltips).
    """
    teile = [f'<svg class="land {css_klasse}" viewBox="{geometrien["_viewbox"]}" '
             'xmlns="http://www.w3.org/2000/svg" role="img" '
             'aria-hidden="true" focusable="false">']
    for code, v in geometrien.items():
        if code == "_viewbox":
            continue
        teile.append(f'<path d="{v["d"]}"><title>{v["name"]}</title></path>')
    teile.append("</svg>")
    return "".join(teile)


START_CSS = """
/* Kein Hintergrundbild im Kopf: Die Silhouette der Deutschland-Fassung\n   zeigt nur ein Land und wäre auf der Startseite irreführend. */\n.kopf{background-image:none}\n/* Startseite: ruhig, ein Bild pro Land, keine Diagramme. */
.start-kopf{padding:34px 0 26px}
.start-kopf h1{font-size:clamp(1.6rem,4vw,2.5rem);line-height:1.14;
 letter-spacing:-.028em;margin:0 0 14px;max-width:22ch;color:#fff}
.start-kopf p{margin:0;max-width:74ch;font-size:clamp(.9rem,1.6vw,1.02rem);
 color:#d8d3cc;line-height:1.62}
.start-kopf .zahl{color:#fff;font-weight:650}
.laender{display:grid;grid-template-columns:1fr;gap:20px;margin-top:26px}
@media (min-width:820px){.laender{grid-template-columns:1fr 1fr;gap:24px}}
.land-karte{display:flex;flex-direction:column;background:var(--card);
 border:1px solid var(--line);border-radius:var(--radius);padding:20px 20px 18px;
 box-shadow:var(--schatten);text-decoration:none;color:inherit;
 transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease}
.land-karte:hover{transform:translateY(-3px);border-color:#c9ded9;
 box-shadow:0 18px 40px -22px rgba(24,20,16,.34)}
.land-karte:focus-visible{outline:3px solid var(--teal);outline-offset:3px}
.land-karte h2{margin:0 0 2px;font-size:1.22rem;letter-spacing:-.015em;color:var(--ink)}
.land-karte .unter{margin:0 0 12px;font-size:.86rem;color:var(--muted)}
.land-karte .bild{flex:1 1 auto;display:flex;align-items:center;justify-content:center;
 padding:4px 0 10px}
.land-karte svg.land{width:100%;height:auto;max-height:330px;display:block}
.land-karte svg.land path{fill:#c3e2dd;stroke:#ffffff;stroke-width:1.6;
 transition:fill .25s ease}
.land-karte:hover svg.land path{fill:#96cbc4}
.land-karte .kennzahlen{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
 gap:8px;border-top:1px solid var(--line);padding-top:12px;margin-top:auto}
.land-karte .kennzahlen b{display:block;font-size:1.02rem;font-weight:650;
 color:var(--ink);font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.land-karte .kennzahlen span{font-size:.68rem;color:var(--muted);
 text-transform:uppercase;letter-spacing:.05em;line-height:1.3;display:block}
.land-karte .hinweis-zur{display:inline-flex;align-items:center;gap:6px;
 margin-top:14px;font-size:.87rem;font-weight:650;color:var(--teal)}
.land-karte:hover .hinweis-zur{color:var(--teal-dunkel)}
.start-notiz{margin-top:26px;background:var(--soft);border:1px solid var(--line);
 border-radius:var(--radius);padding:18px 20px}
.start-notiz h3{margin:0 0 6px;font-size:.98rem;color:var(--ink)}
.start-notiz p{margin:0 0 8px;font-size:.88rem;color:var(--text);line-height:1.6;
 max-width:88ch}
.start-notiz p:last-child{margin-bottom:0}
"""


def baue_start(de_z, ch_z):
    """Setzt die Startseite zusammen.

    Args:
        de_z: Kennzahlen Deutschlands.
        ch_z: Kennzahlen der Schweiz.

    Returns:
        str: vollständiges HTML der Startseite.
    """
    de_geo = json.loads((OUT / "bundeslaender_svg.json").read_text(encoding="utf-8"))
    ch_geo = json.loads((OUT / "ch_kantone_svg.json").read_text(encoding="utf-8"))

    def nf(v, d=0):
        return "—" if v is None else f"{v:,.{d}f}".replace(",", "'")

    de_pct = "—" if de_z["unsicher"] is None else nf(de_z["unsicher"], 1) + " %"
    ch_pct = "—" if ch_z["unsicher"] is None else nf(ch_z["unsicher"], 1) + " %"

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#12100e">
<title>Kriminalität und Sicherheit in Deutschland und der Schweiz</title>
<meta name="description" content="Registrierte Kriminalität, Strafverfolgung und
das Sicherheitsgefühl der Bevölkerung in Deutschland und in der Schweiz —
für beide Länder und für jede Region.">
<style>{DE.schrift_css()}</style>
<style>{DE.CSS}{START_CSS}</style>
</head>
<body>
<div id="app">
  <header class="kopf start-kopf">
    <div class="kopf-inner">
      <div class="kopf-titel">
        <h1>Kriminalität und Sicherheit in Deutschland und der Schweiz</h1>
        <p>Zwei Länder, dieselben Fragen: Was wird registriert, was wird
        aufgeklärt — und wie sicher fühlen sich die Menschen? Die Auswertungen
        beruhen auf amtlichen Polizeistatistiken, auf den Befragungen des
        European Social Survey und auf den Opferbefragungen beider Länder.
        Jede Zahl ist mit Quelle, Fallzahl und Grenze versehen; Zusammenhänge
        sind als Zusammenhänge gekennzeichnet, nicht als Ursachen.</p>
      </div>
    </div>
  </header>

  <main>
    <div class="laender">
      <a class="land-karte" href="deutschland.html">
        <h2>Deutschland</h2>
        <p class="unter">Die Bundesrepublik und jedes Bundesland</p>
        <div class="bild">{karte(de_geo, "de")}</div>
        <div class="kennzahlen">
          <div><b>{nf(de_z["hz"])}</b><span>Fälle je 100.000 Einwohner</span></div>
          <div><b>{de_pct}</b><span>fühlen sich unsicher</span></div>
          <div><b>{nf(de_z["einwohner"] / 1e6, 1)} Mio</b><span>Einwohner</span></div>
        </div>
        <span class="hinweis-zur">Zur Karte von Deutschland →</span>
      </a>

      <a class="land-karte" href="schweiz.html">
        <h2>Schweiz</h2>
        <p class="unter">Die Eidgenossenschaft und jeder Kanton</p>
        <div class="bild">{karte(ch_geo, "ch")}</div>
        <div class="kennzahlen">
          <div><b>{nf(ch_z["hz"])}</b><span>Fälle je 100.000 Einwohner</span></div>
          <div><b>{ch_pct}</b><span>fühlen sich unsicher</span></div>
          <div><b>{nf(ch_z["einwohner"] / 1e6, 1)} Mio</b><span>Einwohner</span></div>
        </div>
        <span class="hinweis-zur">Zur Karte der Schweiz →</span>
      </a>
    </div>

    <div class="start-notiz">
      <h3>Was die beiden Seiten zeigen</h3>
      <p>In beiden Ländern folgt das Sicherheitsgefühl der registrierten
      Kriminalität nicht. In Deutschland hat sich die Zahl der registrierten
      Straftaten seit 1993 um 18 Prozent verringert, während der Anteil der
      Menschen mit Unsicherheitsgefühl 2023 mit 25,0 Prozent über dem Wert von
      2002 liegt. In der Schweiz ist die registrierte Kriminalität seit 2009
      praktisch unverändert, das Unsicherheitsgefühl aber von 16,1 auf 8,9
      Prozent gefallen. Beide Befunde beruhen auf derselben Frage derselben
      Erhebung — und sie widersprechen der Annahme, dass Furcht einfach der
      Kriminalität folgt.</p>
      <p>Was hier <em>nicht</em> steht: warum das so ist. Die Seiten belegen
      Zusammenhänge, keine Ursachen. Wer eine Erklärung anbietet, sollte
      angeben können, welche Beobachtung sie widerlegen würde.</p>
    </div>
  </main>

  <footer class="fuss">
    <p><strong>Quellen.</strong> Deutschland: BKA (Polizeiliche
    Kriminalstatistik), Statistisches Bundesamt, European Social Survey,
    Eurostat/GISCO. Schweiz: Bundesamt für Statistik (Polizeiliche
    Kriminalstatistik, Wohnbevölkerung), Swiss Crime Survey 2022,
    Schweizerische Sicherheitsbefragung 2015, European Social Survey,
    Eurostat/GISCO.</p>
    <p><strong>Grenzen.</strong> Registrierte Fälle sind polizeilich bekannt
    gewordene Vorgänge — kein Nachweis einer Straftat und keine Verurteilung.
    Die amtlichen Statistiken beider Länder grenzen Delikte unterschiedlich ab
    und sind nur über die harmonisierte Gliederung von Eurostat vergleichbar.
    Befragungswerte beruhen auf Stichproben; kleine Fallzahlen sind in den
    Länderfassungen gekennzeichnet.</p>
    <p class="credit">Erstellt von <strong>Christopher Vantis</strong> mit
    <strong>Hermes</strong> (KI-Assistent). Auswahl der Fragen, Deutung und
    Prüfung der Ergebnisse liegen beim Autor; Recherche, Auswertung und
    Umsetzung entstanden im Dialog mit dem Assistenten.</p>
  </footer>
</div>
</body>
</html>"""


def main():
    """Verschiebt die Deutschland-Fassung und schreibt die Startseite."""
    index = DASH / "index.html"
    de = DASH / "deutschland.html"
    start = DASH / "start.html"
    if not index.exists():
        raise SystemExit("dashboard/index.html fehlt — zuerst build_app.py ausführen.")
    # Schutz gegen Selbstüberschreiben: Läuft dieses Skript ein zweites Mal,
    # enthält index.html bereits die Startseite (wenige hundert Kilobyte).
    # Nur eine grosse Datei ist die Deutschland-Fassung und darf kopiert werden.
    MINDESTGROESSE = 1_000_000
    if start.exists() and index.stat().st_size < MINDESTGROESSE:
        print("index.html enthält schon die Startseite — "
              "Deutschland-Fassung bleibt unangetastet")
    elif (not de.exists()) or de.stat().st_size < index.stat().st_size:
        shutil.copy2(index, de)
        print(f"deutschland.html aus index.html übernommen "
              f"({de.stat().st_size/1e6:.2f} MB)")
    else:
        print(f"deutschland.html ist aktuell ({de.stat().st_size/1e6:.2f} MB) — "
              "nicht überschrieben")

    html = baue_start(deutschland_zahlen(), schweiz_zahlen())
    (DASH / "start.html").write_text(html, encoding="utf-8")
    index.write_text(html, encoding="utf-8")
    print(f"index.html: {index.stat().st_size/1024:.0f} KB (Startseite)")


if __name__ == "__main__":
    main()
