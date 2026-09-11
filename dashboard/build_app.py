#!/usr/bin/env python3
"""
build_app.py — Die (un)berechtigte Furcht vor Kriminalität in Deutschland
============================================================================
Baut eine Webapp als einzelne HTML-Datei: Deutschlandkarte (klickbar),
Bundes-Kennzahlen, Kriminalität, Furcht, Demografie und Wirtschaft — und für
jedes Bundesland dieselben Angaben im Detail.

Aufbau:
  Ansicht Deutschland   — Karte + republikweite Auswertungen
  Ansicht Bundesland    — erscheint beim Klick auf ein Land (sanfter Wechsel)

ausgabe: dashboard/index.html — die App selbst; die Karte ist der Einstieg.
         Alle Diagramme und die Schrift sind eingebettet, die Datei ist also
         eigenständig lauffähig.
"""
import csv
import math
import json
import pathlib
import re

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.nonparametric.smoothers_lowess import lowess

from wappen_util import wappen_laden
import plotly.io as pio
from plotly.offline import get_plotlyjs

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard/data"
OUT = ROOT / "output"

# ---------------------------------------------------------------- Farben
# Farbsemantik, bewusst auf drei Bedeutungen begrenzt:
#   Petrol  = die Leitfarbe, steht für den Hauptwert bzw. "unter der Referenz"
#   Ocker   = die Gegenrichtung "über der Referenz" — warm, aber kein Alarmrot
#   Grau    = neutral, keine Angabe, Kontextlinie
# Rot und Signalgrün werden als Datenfarben vermieden: Beide kommunizieren
# unabhängig vom Inhalt "schlecht" bzw. "gut". Verläufe innerhalb eines
# Diagramms nutzen Abstufungen der Leitfarbe (TEAL_H1→H3).
UNTER, UEBER, NEUTRAL = "#0f766e", "#a16207", "#a8a29e"
TEAL_H1, TEAL_H2, TEAL_H3 = "#0f766e", "#3d9a92", "#9fd3ce"
BLUE, VERM, GREEN, PURPLE, SAND, SKY = UNTER, UEBER, UNTER, "#6d28d9", NEUTRAL, TEAL_H2
INK, SLATE, GRID = "#12100e", "#78716c", "#ece7e1"
BG, SURFACE = "#faf8f5", "#ffffff"

FARBEN_KARTE = ["#e8f3f1", "#c3e2dd", "#96cbc4", "#5fada4", "#2d8c82", "#0f5f58"]


def lies(pfad, delim=","):
    with open(pfad, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=delim))


def z(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- Daten
def lade_daten():
    pks = lies(OUT / "pks_laender_2025.csv", ";")
    ind = lies(OUT / "laender_indikatoren.csv", ";")
    ess = lies(D / "ess_bundeslaender.csv", ";")
    svg = json.loads((OUT / "bundeslaender_svg.json").read_text(encoding="utf-8"))

    laender = {}
    for r in ind:
        laender[r["bundesland"]] = {
            "name": r["bundesland"],
            "bevoelkerung": z(r["bevoelkerung_2025"]),
            "flaeche": z(r["flaeche_km2"]),
            "dichte": z(r["dichte"]),
            "auslaenderanteil": z(r["auslaenderanteil_pct"]),
            "mh_anteil": z(r["mh_pct"]),
            "alq": z(r["alq_2025"]),
            "mit_mh": z(r["mit_mh"]),
            "ohne_mh": z(r["ohne_mh"]),
            "bip_je_ew": z(r["bip_je_ew_2024"]),
            "verfuegbares_einkommen": z(r["verfuegbares_einkommen_2024"]),
            "kriminalitaet": {},
            "furcht": {},
        }
    for r in pks:
        if r["bundesland"] in laender:
            laender[r["bundesland"]]["kriminalitaet"][r["delikt"]] = {
                "faelle": z(r["faelle"]), "hz": z(r["hz"]),
                "aq": z(r["aq"]), "aufgeklaert": z(r["aufgeklaert"]),
            }
    for r in ess:
        if r["bundesland"] in laender:
            laender[r["bundesland"]]["furcht"] = {
                "n": int(r["n"]) if r["n"] else None,
                "unsicher": z(r["unsicher_pct"]),
                "ki_lo": z(r["ki_lo"]), "ki_hi": z(r["ki_hi"]),
                "belastbar": r["unsicher_belastbar"].startswith("ja"),
                "polizeivertrauen": z(r["polizeivertrauen"]),
                "sozialvertrauen": z(r["sozialvertrauen"]),
                "viktimisierung": z(r["viktim_pct"]),
                "hochschule": z(r["hochschule_pct"]),
                "alter_mittel": z(r["alter_mittel"]),
                "nuts": r["nuts"],
            }
    # SVG-Pfade den Ländern zuordnen
    for nuts, v in svg.items():
        if nuts == "_viewbox":
            continue
        for l in laender.values():
            if l["name"] == v["name"]:
                l["svg"] = v["d"]
                l["nuts"] = nuts
                l["label"] = v.get("label")
    return laender, svg["_viewbox"]


def basis_zahlen(laender):
    """Republikweite Größen aus den Länderdaten (Summen/Mittel)."""
    n = len(laender)
    einwohner = sum(l["bevoelkerung"] or 0 for l in laender.values())
    faelle = sum((l["kriminalitaet"].get("Straftaten insgesamt") or {}).get("faelle") or 0
                 for l in laender.values())
    aufgeklaert = sum((l["kriminalitaet"].get("Straftaten insgesamt") or {}).get("aufgeklaert") or 0
                      for l in laender.values())
    bip_gew = sum((l["bip_je_ew"] or 0) * (l["bevoelkerung"] or 0) for l in laender.values()) / einwohner
    aussl_gew = sum((l["auslaenderanteil"] or 0) * (l["bevoelkerung"] or 0)
                    for l in laender.values()) / einwohner
    return dict(
        laender=n, einwohner=einwohner, faelle=faelle,
        hz=round(faelle / einwohner * 100000, 1),
        aq=round(aufgeklaert / faelle * 100, 1),
        bip_je_ew=round(bip_gew), auslaenderanteil=round(aussl_gew, 1),
    )


# ---------------------------------------------------------------- Diagramme
BASE = dict(
    font=dict(family='IBM Plex Sans, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
              size=13, color=INK),
    margin=dict(l=10, r=20, t=30, b=50), autosize=True,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=12)),
    hoverlabel=dict(font_size=13, bordercolor=SLATE),
    xaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=12)),
    yaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=12)),
)


def fig(hoehe=360, **kw):
    f = go.Figure()
    f.update_layout(**BASE, height=hoehe)
    if kw:
        f.update_layout(**kw)
    return f


def diagramme(laender, basis):
    """Alle Diagramme als Liste von (id, titel, untertitel, fig, quelle)."""
    figs = []
    namen = sorted(laender)

    # 1) Ländervergleich: Kriminalitätsbelastung (HZ)
    daten = sorted(((l["kriminalitaet"].get("Straftaten insgesamt") or {}).get("hz") or 0, n)
                   for n, l in laender.items())
    f = fig(400)
    f.add_trace(go.Bar(x=[d[1] for d in daten], y=[d[0] for d in daten],
                       marker_color=[VERM if d[0] > basis["hz"] else BLUE for d in daten],
                       hovertemplate="%{x}: %{y:,.0f} Fälle je 100.000<extra></extra>"))
    f.update_yaxes(title="Häufigkeitszahl 2025")
    f.update_xaxes(tickangle=-40)
    figs.append(("hz", "Kriminalitätsbelastung je Bundesland",
                 "Registrierte Fälle je 100.000 Einwohner (Häufigkeitszahl), 2025. "
                 f"Bundesdurchschnitt: {basis['hz']:,.0f}.".replace(",", "."),
                 f, "BKA, PKS 2025, Länder-Grundtabelle"))

    # 2) Aufklärungsquote
    daten = sorted((((l["kriminalitaet"].get("Straftaten insgesamt") or {}).get("aq") or 0), n)
                   for n, l in laender.items())
    f = fig(400)
    f.add_trace(go.Bar(x=[d[1] for d in daten], y=[d[0] for d in daten],
                       marker_color=[UNTER if d[0] > basis["aq"] else NEUTRAL for d in daten],
                       hovertemplate="%{x}: %{y:.1f} %<extra></extra>"))
    f.update_yaxes(title="Aufklärungsquote", ticksuffix=" %")
    f.update_xaxes(tickangle=-40)
    figs.append(("aq", "Aufklärungsquote je Bundesland",
                 "Anteil der Fälle, in denen mindestens ein Tatverdächtiger ermittelt wurde, 2025. "
                 f"Bundesdurchschnitt: {basis['aq']:.1f} %.".replace(".", ","),
                 f, "BKA, PKS 2025, Länder-Grundtabelle"))

    # 3) Unsicherheitsgefühl (ESS)
    daten = sorted(((l["furcht"].get("unsicher") or 0), n, l["furcht"].get("ki_lo"),
                    l["furcht"].get("ki_hi"), l["furcht"].get("belastbar"))
                   for n, l in laender.items())
    f = fig(420)
    f.add_trace(go.Bar(
        x=[d[1] for d in daten], y=[d[0] for d in daten],
        marker_color=[VERM if d[4] else "#d6d0c8" for d in daten],
        error_y=dict(type="data", symmetric=False,
                     array=[(d[3] - d[0]) if d[3] else 0 for d in daten],
                     arrayminus=[(d[0] - d[2]) if d[2] else 0 for d in daten],
                     color=SLATE, thickness=1.2, width=3),
        hovertemplate="%{x}: %{y:.1f} % (95-%-Intervall als Fehlerbalken)<extra></extra>"))
    f.update_yaxes(title="Anteil unsicher", ticksuffix=" %")
    f.update_xaxes(tickangle=-40)
    figs.append(("furcht", "Unsicherheitsgefühl je Bundesland",
                 "Anteil, der sich nachts beim Alleingehen unsicher fühlt (ESS, Runden 5–11 gepoolt). "
                 "Graue Balken: Fallzahl zu klein für belastbare Aussagen.",
                 f, "European Social Survey, eigene Berechnung, gewichtet"))


    # 5) Zeitreihe: erfasste Fälle Deutschland
    t01 = lies(OUT / "t01_bund_zeitreihe_clean.csv")
    ges = sorted([r for r in t01 if r["schluessel"] == "------"], key=lambda r: int(float(r["jahr"])))
    f = fig(380, hovermode="x unified")
    f.add_trace(go.Scatter(x=[int(float(r["jahr"])) for r in ges], y=[z(r["faelle"]) / 1e6 for r in ges],
                           mode="lines", name="Erfasste Fälle",
                           line=dict(color=BLUE, width=3),
                           hovertemplate="%{x}: %{y:.2f} Mio<extra></extra>"))
    f.update_yaxes(title="Fälle (Mio.)", rangemode="tozero")
    f.update_xaxes(dtick=4)
    figs.append(("zeitreihe", "Registrierte Kriminalität in Deutschland",
                 "Erfasste Fälle 1987–2025. Langfristig rückläufig, kurzfristig volatil.",
                 f, "BKA, PKS, T01-Zeitreihe"))

    # 6) Furcht-Zeitreihe (ESS)
    agg = lies(D / "ess_aggregate.csv", ";")
    zr = sorted([r for r in agg if r["ebene"] == "zeitreihe" and r["gruppe"] == "gesamt"],
                key=lambda r: int(float(r["jahr"])))
    f = fig(380, hovermode="x unified")
    f.add_trace(go.Scatter(x=[int(float(r["jahr"])) for r in zr], y=[z(r["ki_hi"]) for r in zr],
                           mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    f.add_trace(go.Scatter(x=[int(float(r["jahr"])) for r in zr], y=[z(r["ki_lo"]) for r in zr],
                           mode="lines", line=dict(width=0), fill="tonexty",
                           fillcolor="rgba(220,38,38,0.14)", showlegend=False, hoverinfo="skip"))
    f.add_trace(go.Scatter(x=[int(float(r["jahr"])) for r in zr], y=[z(r["anteil"]) for r in zr],
                           mode="lines+markers", name="unsicher",
                           line=dict(color=VERM, width=3), marker=dict(size=7),
                           hovertemplate="%{x}: %{y:.1f} %<extra></extra>"))
    f.update_yaxes(title="Anteil unsicher", ticksuffix=" %")
    figs.append(("furcht_zr", "Unsicherheitsgefühl in Deutschland",
                 "ESS 2002–2023 (Deutschland fehlt in Runde 10/2020; gepunktet interpoliert).",
                 f, "European Social Survey, eigene Berechnung"))

    # 7) Deliktprofil der Furcht (SKiD)
    ref = lies(D / "wahrnehmung_referenzwerte.csv", ";")
    fa20 = {r["item"]: z(r["wert_pct"]) for r in ref
            if r["kategorie"] == "furcht_affektiv" and r["welle_jahr"] == "2020" and r["gruppe"] == "gesamt"}
    fa24 = {r["item"]: z(r["wert_pct"]) for r in ref
            if r["kategorie"] == "furcht_affektiv" and r["welle_jahr"] == "2024" and r["gruppe"] == "gesamt"}
    items = sorted(fa24, key=lambda i: fa24[i])
    f = fig(430, barmode="group", bargap=0.3)
    f.add_trace(go.Bar(y=items, x=[fa20.get(i) for i in items], orientation="h",
                       name="2020", marker_color="#cfc7bb",
                       hovertemplate="%{y}: %{x:.1f} %<extra>2020</extra>"))
    f.add_trace(go.Bar(y=items, x=[fa24.get(i) for i in items], orientation="h",
                       name="2024", marker_color=TEAL_H1,
                       hovertemplate="%{y}: %{x:.1f} %<extra>2024</extra>"))
    f.update_xaxes(ticksuffix=" %")
    _pmk = diagramm_pmk()
    if _pmk is not None:
        figs.append(("pmk", "Politisch motivierte Kriminalität",
                     "Zwei Zahlen, die weit auseinanderlaufen: Das Gesamtaufkommen hat "
                     "sich seit 2016 mehr als verdoppelt, die Gewalttaten blieben "
                     "praktisch unverändert. Ein großer Teil der Fälle sind "
                     "Propagandadelikte. Beide Felder haben eine eigene Skala "
                     "(links bis rund 86.000, rechts bis rund 4.200 Fälle) — die "
                     "Linienhöhen sind nur innerhalb eines Feldes vergleichbar.",
                     _pmk,
                     "BKA, Bundesweite Fallzahlen zur politisch motivierten "
                     "Kriminalität 2025 (Fact Sheet); eigene Aufbereitung."))
    _alter = diagramm_alter_furcht()
    if _alter is not None:
        figs.append(("alter_furcht", "Furcht über die Altersspanne",
                     "Anteil mit Unsicherheitsgefühl je Altersgruppe. Symbol ♀/♂ "
                     "steht für das Geschlecht, die Farbe für den "
                     "Migrationshintergrund. Die blasse Linie ist eine gleitende "
                     "Regression über alle Einzelpersonen, nicht über die sieben "
                     "Punkte. Jede Gruppe beruht auf mindestens 88 Befragten "
                     "(Median 975); die Fallzahl steht beim Überfahren des Punktes.",
                     _alter,
                     "European Social Survey, Runden 1–11, Deutschland; eigene "
                     "Berechnung, gewichtet."))
    _skid1 = diagramm_skid_delikte()
    if _skid1 is not None:
        figs.append(("skid_delikte", "Wovor sich Deutschland fürchtet",
                     "Die Furcht vor einem Delikt (dunkel) und die Einschätzung, "
                     "selbst Opfer zu werden (gold). Betrug im Internet führt "
                     "deutlich, und bei jedem Delikt ist die Furcht größer als die "
                     "angenommene Wahrscheinlichkeit.",
                     _skid1,
                     "BKA/Destatis, Sicherheit und Kriminalität in Deutschland "
                     "(SKiD) 2024, Ergebnisbericht, Kapitel 6.3/6.4 — 60.837 "
                     "auswertbare Interviews."))
    _skid2 = diagramm_skid_orte()
    if _skid2 is not None:
        figs.append(("skid_orte", "Sicherheitsgefühl nach Situation",
                     "Anteil der Menschen, die sich an einem Ort sicher fühlen — "
                     "tagsüber und nachts. Nachts bricht das Sicherheitsgefühl "
                     "überall ein, an Bahnhöfen und in Parks am stärksten.",
                     _skid2,
                     "BKA/Destatis, SKiD 2024, Ergebnisbericht, Kapitel 6.2."))
    figs.append(("delikte", "Wovor Deutschland sich fürchtet",
                 "Anteil „beunruhigt“ je Delikt, SKiD 2020 und 2024.",
                 f, "BKA, SKiD 2024/2020"))

    # 8) Trichter (Justiz)
    aq = {r["schluessel"]: r for r in lies(OUT / "pks_aufklaerungsquoten_2025.csv")}
    ver = {(r["delikt"], r["jahr"]): z(r["verurteilte"])
           for r in lies(OUT / "destatis_verurteilte.csv")}
    gruppen = [("****00", "Diebstahl (gesamt)", "Diebstahl (19. Abschnitt)"),
               ("435*00", "Wohnungseinbruch", None),
               ("210000", "Raub", "Raub und räuberische Erpressung (20. Abschnitt)"),
               ("222000", "Gefährliche Körperverletzung", "Körperverletzung")]
    labels, faelle, aufgeklaert, verurteilt = [], [], [], []
    for sch, lab, verlab in gruppen:
        a = aq.get(sch)
        if not a:
            continue
        labels.append(lab)
        faelle.append(z(a["faelle"]))
        aufgeklaert.append(z(a["aufgeklaert"]))
        if verlab:
            verurteilt.append(ver.get((verlab, "2024")))
        else:
            v = sum(ver.get((k, "2024")) or 0 for k in
                    ["Einbruchdiebstahl (§ 243 Abs. 1 S. 2 Nr. 1)",
                     "Wohnungseinbruchdiebstahl (§ 244 Abs. 1 Nr. 3)",
                     "Schwerer Diebstahl/Banden (§ 244a)"])
            verurteilt.append(v)
    # Farbfamilien trennen die beiden Ebenen: Polizei (Petrol) und Justiz (Ocker).
    # Die drei Serien sind zusaetzlich direkt beschriftet — die Farbe muss die
    # Zuordnung also nicht allein tragen.
    f = fig(430, barmode="group", bargap=0.32)
    f.add_trace(go.Bar(y=labels, x=faelle, orientation="h", name="registrierte Fälle (Polizei, 2025)",
                       marker_color="#0b4f49", width=0.25,
                       text=[f"{v:,.0f}".replace(",", ".") for v in faelle],
                       textposition="outside", textfont=dict(size=11, color="#3d3833"),
                       hovertemplate="%{y}: %{x:,.0f}<extra>registriert</extra>"))
    f.add_trace(go.Bar(y=labels, x=aufgeklaert, orientation="h", name="davon aufgeklärt (Polizei, 2025)",
                       marker_color="#2d8c82", width=0.25,
                       text=[f"{v:,.0f}".replace(",", ".") for v in aufgeklaert],
                       textposition="outside", textfont=dict(size=11, color="#3d3833"),
                       hovertemplate="%{y}: %{x:,.0f}<extra>aufgeklärt</extra>"))
    f.add_trace(go.Bar(y=labels, x=verurteilt, orientation="h", name="Verurteilungen (Justiz, 2024)",
                       marker_color="#7d5108", width=0.25,
                       text=[f"{v:,.0f}".replace(",", ".") if v else "" for v in verurteilt],
                       textposition="outside", textfont=dict(size=11, color="#3d3833"),
                       hovertemplate="%{y}: %{x:,.0f}<extra>verurteilt</extra>"))
    f.update_xaxes(type="log", title="Anzahl (logarithmische Skala)")
    # Die Serien werden von oben nach unten in umgekehrter Reihenfolge gezeichnet;
    # die Legende wird angeglichen, damit beide dieselbe Ordnung zeigen.
    # Achtung: Bei einer log-Achse erwartet Plotly den Bereich in Zehnerpotenzen
    # (log10), nicht in Rohwerten — sonst wird die Achse ungültig.
    _max = max([v for v in verurteilt if v] + [v for v in faelle if v] + [1])
    f.update_xaxes(range=[0, math.log10(_max) + 0.6],
                   tickvals=[1e2, 1e3, 1e4, 1e5, 1e6, 1e7],
                   ticktext=["100", "1.000", "10.000", "100.000", "1 Mio.", "10 Mio."])
    f.update_layout(legend=dict(traceorder="reversed", orientation="h",
                                y=-0.28, x=0, xanchor="left"))
    figs.append(("trichter", "Von der Anzeige zur Verurteilung",
                 "Registrierte Fälle, aufgeklärte Fälle und Verurteilungen im Vergleich "
                 "(unterschiedliche Einheiten und Jahre — bitte als Größenordnung lesen).",
                 f, "BKA PKS 2025; Destatis Strafverfolgungsstatistik 2024"))

    # 9) EU-Vergleich: mehrere Delikte als kleine Vielfache
    # Jedes Feld hat eine eigene Werteskala — sonst wären Tötungsdelikte
    # (unter 1 je 100.000) neben Diebstahl (über 2.000) unsichtbar.
    eu = lies(OUT / "eurostat_vergleich.csv", ";")
    if eu:
        je_delikt = {}
        for r in eu:
            # 2008 ausschliessen: Der Eurostat-Wert liegt dort bei
            # gefaehrlicher Koerperverletzung und Diebstahl um ein Mehrfaches
            # ueber dem Folgejahr — ein Bruch in der Datenreihe. Gegenprobe mit
            # der Polizeilichen Kriminalstatistik: Dort liegen Diebstahl 2008
            # und 2009 nur rund vier Prozent auseinander.
            if int(float(r["jahr"])) < 2009:
                continue
            if r["de_rate"] and r["eu_median"]:
                je_delikt.setdefault(r["iccs"], {"name": r["delikt"], "j": [], "de": [], "eu": []})
                e = je_delikt[r["iccs"]]
                e["j"].append(int(float(r["jahr"])))
                e["de"].append(float(r["de_rate"]))
                e["eu"].append(float(r["eu_median"]))
        # Reihenfolge: von der schwersten zur häufigsten Deliktart
        reihenfolge = ["ICCS0101", "ICCS0401", "ICCS05012", "ICCS0501",
                       "ICCS020111", "ICCS0502"]
        namen = [k for k in reihenfolge if k in je_delikt]
        f = make_subplots(rows=3, cols=2, subplot_titles=[
            f"{je_delikt[k]['name']}" for k in namen],
            vertical_spacing=0.13, horizontal_spacing=0.11)
        for i, k in enumerate(namen):
            zeile, spalte = i // 2 + 1, i % 2 + 1
            e = je_delikt[k]
            f.add_trace(go.Scatter(x=e["j"], y=e["eu"], mode="lines", name="EU-Median",
                                   line=dict(color=NEUTRAL, width=2, dash="dot"),
                                   legendgroup="eu", showlegend=(i == 0),
                                   hovertemplate="EU-Median %{y:.1f}<extra></extra>"),
                        row=zeile, col=spalte)
            f.add_trace(go.Scatter(x=e["j"], y=e["de"], mode="lines", name="Deutschland",
                                   line=dict(color=UNTER, width=2.6),
                                   legendgroup="de", showlegend=(i == 0),
                                   hovertemplate="Deutschland %{y:.1f}<extra></extra>"),
                        row=zeile, col=spalte)
        f.update_layout(height=760, hovermode="x unified",
                        margin=dict(l=8, r=16, t=42, b=8),
                        legend=dict(orientation="h", y=1.07, x=0, xanchor="left"))
        f.update_yaxes(ticksuffix="", automargin=True)
        f.update_xaxes(automargin=True)
        # Subplot-Titel kleiner setzen
        for an in f.layout.annotations:
            an.font.size = 12.5
        figs.append(("eu", "Deutschland im EU-Vergleich",
                     "Registrierte Fälle je 100.000 Einwohner, Deutschland gegenüber dem "
                     "Median der Vergleichsländer (rund 40 Staaten). Der senkrechte "
                     "Abstand zwischen beiden Linien zeigt, ob Deutschland über oder "
                     "unter dem europäischen Mittelfeld liegt. Bei Körperverletzung "
                     "und Diebstahl liegt Deutschland um ein Mehrfaches darüber, bei "
                     "Wohnungseinbruch nahezu auf Augenhöhe. Die Reihe beginnt 2009: "
                     "Für 2008 weist Eurostat bei Körperverletzung und Diebstahl ein "
                     "Mehrfaches des Folgejahres aus — ein Bruch in der Datenreihe, "
                     "kein tatsächlicher Rückgang. Jedes Feld hat eine <em>eigene</em> "
                     "Werteskala.",
                     f, "Eurostat crim_off_cat, Datenstand 08/2025",
                     # Ausführliche Einordnung: Warum diese Zahlen nicht die
                     # Kriminalität der Länder vergleichen. Belege im Text.
                     "Warum die Abstände nicht die Wirklichkeit abbilden: "
                     "Die Daten zeigen nur, was der Polizei gemeldet wurde — und wie "
                     "sie es zählt. Eurostat weist selbst darauf hin, dass jedes Land "
                     "eigene Strafgesetze, eigene Deliktdefinitionen und eigene "
                     "Zählregeln hat und die Zahlen ausschließlich polizeilich bekannt "
                     "gewordene Fälle abbilden. Die Anzeigebereitschaft unterscheidet "
                     "sich erheblich: In Deutschland liegt die Anzeigequote bei Gewalt "
                     "nach der Dunkelfeldstudie LeSuBiA des BKA meist unter zehn "
                     "Prozent. Beim Körperverletzungsvergleich kommt eine deutsche "
                     "Besonderheit hinzu: Die gefährliche Körperverletzung nach § 224 "
                     "StGB fasst Fälle zusammen, die in anderen Ländern teils als "
                     "einfache Körperverletzung gezählt werden. Der Abstand von "
                     "Deutschland zum Mittelfeld ist deshalb vor allem ein Abbild "
                     "der Erfassungspraxis, nicht der Gewaltrate."))
    return figs




# ---------------------------------------------------------------- Zusammenhänge
def diagramm_alter_furcht():
    """Furcht über die Altersspanne, getrennt nach Geschlecht und Herkunft.

    Warum aggregiert und nicht als Rohpunktwolke: Die Furcht ist im ESS eine
    Ja/Nein-Angabe. Trägt man 16.000 Einzelpersonen auf, liegen alle Punkte auf
    zwei Linien (0 und 1) — man sieht kein Muster, nur zwei Streifen. Deshalb
    wird je Altersgruppe der Anteil berechnet. Das ist dieselbe Information,
    nur lesbar.

    Codierung:
        Symbol  ♀ / ♂  — Geschlecht
        Farbe          — mit / ohne Migrationshintergrund
        Fallzahl       — im Tooltip beim Überfahren des Punktes

    Returns:
        plotly.graph_objects.Figure | None
    """
    pfad = pathlib.Path(__file__).resolve().parent / "data" / "ess_de_personen.csv"
    if not pfad.exists():
        return None
    personen = lies(pfad)
    if not personen:
        return None

    def zahl(wert):
        try:
            return float(str(wert).replace(",", "."))
        except (TypeError, ValueError):
            return None

    # Altersgruppen bilden: 15-24, 25-34 ... 75+
    gruppen = [(15, 24), (25, 34), (35, 44), (45, 54), (55, 64), (65, 74), (75, 110)]

    def gruppe_von(alter):
        for von, bis in gruppen:
            if von <= alter <= bis:
                return von
        return None

    # Codierung in der Datei: Geschlecht als "Frau"/"Mann", Migrationshintergrund
    # und Unsicherheit als 0/1, fehlende Werte als "NA".
    zellen = {}
    rohdaten = {}          # (Geschlecht, Herkunft) -> ([Alter], [unsicher 0/1])
    for r in personen:
        alter = zahl(r.get("agea_c"))
        unsicher = str(r.get("unsicher", "")).strip()
        geschlecht = str(r.get("geschlecht", "")).strip()
        mh = str(r.get("mh", "")).strip()
        if alter is None or unsicher not in ("0", "1") or mh not in ("0", "1"):
            continue
        if geschlecht not in ("Frau", "Mann"):
            continue
        g = gruppe_von(alter)
        if g is None:
            continue
        schluessel = (g, geschlecht, mh)
        z = zellen.setdefault(schluessel, [0, 0])
        z[0] += int(unsicher)
        z[1] += 1
        roh = rohdaten.setdefault((geschlecht, mh), ([], []))
        roh[0].append(alter)
        roh[1].append(int(unsicher))

    f = fig(460)
    # Frauen zuerst, damit sie beim Überlagern oben liegen
    for geschlecht, symbol, name_sex in (("Frau", "♀", "Frauen"),
                                         ("Mann", "♂", "Männer")):
        for mh, farbe, name_mh in (("1", "#0b4f49", "mit Migrationshintergrund"),
                                   ("0", "#b8860b", "ohne Migrationshintergrund")):
            punkte = []
            for (g, sex, herkunft), (treffer, n) in zellen.items():
                if sex != geschlecht or herkunft != mh:
                    continue
                # Leichter Versatz: ohne ihn liegen "mit MH" und "ohne MH"
                # bei gleichem Alter genau übereinander und der hintere Punkt
                # ist nur als Sichel zu sehen.
                versatz = -3.0 if mh == "1" else 3.0
                punkte.append((g + 5 + versatz, 100 * treffer / n, n))
            if not punkte:
                continue
            punkte.sort()
            # Kurze Legendenbeschriftung: Die ausgeschriebene Fassung ist
            # breiter als ein Handybildschirm und wird dort abgeschnitten.
            # In der Legende nur die Farbbedeutung: Das Geschlecht zeigen die
            # Symbole ♀/♂ in den Punkten selbst, es zweimal zu nennen wäre
            # doppelt. Der Hovertext nennt weiterhin beides.
            legendenname = ("mit Migrationshintergrund" if mh == "1"
                            else "ohne Migrationshintergrund")
            f.add_trace(go.Scatter(
                x=[p[0] for p in punkte], y=[p[1] for p in punkte],
                mode="markers+text", name=legendenname,
                showlegend=(geschlecht == "Frau"),
                marker=dict(size=27, color=farbe, opacity=0.95,
                            line=dict(width=2, color="#ffffff")),
                text=[symbol] * len(punkte), textposition="middle center",
                textfont=dict(size=19, color="#ffffff"),
                customdata=[[p[2]] for p in punkte],
                hovertemplate=("Alter %{x}<br>%{y:.1f} % unsicher"
                               "<br>n = %{customdata[0]}<extra>" +
                               f"{name_sex}, {name_mh}" + "</extra>"),
            ))
            # Trendkurve: gleitende Regression über die Einzelpersonen, nicht
            # über die sieben Gruppenpunkte — sonst würde eine Kurve aus sieben
            # Werten gezeichnet und als Verlauf gelesen.
            xs, ys = rohdaten.get((geschlecht, mh), ([], []))
            if len(xs) >= 200:
                # it=0: keine robuste Iteration. Die Voreinstellung (it=3)
                # gewichtet Ausreißer ab — bei einer Ja/Nein-Variable mit
                # überwiegend Nullen verwirft sie damit sämtliche Einsen, und
                # die Kurve läuft gegen null. Genau das war bei den Männern
                # (88 % ohne Unsicherheitsgefühl) der Fall.
                glatt = lowess(ys, xs, frac=0.65, it=0, return_sorted=True)
                # Ausdünnen: Die geglättete Kurve hat so viele Stützstellen wie
                # Befragte; für die Zeichnung genügen wenige. Das hält die
                # Seitengröße klein, ohne dass man einen Unterschied sieht.
                schritt = max(1, len(glatt) // 120)
                glatt = glatt[::schritt]
                f.add_trace(go.Scatter(
                    x=glatt[:, 0], y=glatt[:, 1] * 100,
                    mode="lines", name=legendenname,
                    line=dict(color=farbe, width=2.4), opacity=0.5,
                    showlegend=False, hoverinfo="skip",
                ))

    f.update_xaxes(title="Alter in Jahren", dtick=10, range=[2, 98],
                   automargin=True)
    f.update_yaxes(title="Anteil mit Unsicherheitsgefühl", ticksuffix=" %",
                   rangemode="tozero", range=[0, 62], automargin=True)
    layout = dict(BASE)
    layout.update(height=460, margin=dict(l=10, r=20, t=54, b=50),
                  legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0,
                              xanchor="left", font=dict(size=13),
                              itemsizing="constant", itemwidth=30),
                  hovermode="closest")
    f.update_layout(**layout)
    return f


def diagramm_skid_delikte():
    """Wovor sich Deutschland fürchtet (SKiD 2024).

    Gegenübergestellt: die Furcht vor einem Delikt und die Einschätzung, selbst
    Opfer zu werden. Die Lücke zwischen beiden ist die eigentliche Aussage —
    gefürchtet wird mehr, als für wahrscheinlich gehalten wird.

    Returns:
        plotly.graph_objects.Figure | None
    """
    pfad = OUT / "skid_furcht.csv"
    if not pfad.exists():
        return None
    daten = [r for r in lies(pfad, delim=";") if r["art"] == "delikt"]
    daten.sort(key=lambda r: float(r["wert_1"]))
    namen = [r["bezeichnung"] for r in daten]
    furcht = [float(r["wert_1"]) for r in daten]
    risiko = [float(r["wert_2"]) for r in daten]

    f = fig(430)
    f.add_trace(go.Bar(y=namen, x=furcht, orientation="h", name="Furcht",
                       marker_color="#0b4f49",
                       text=[f"{w:.1f}" for w in furcht], textposition="outside",
                       textfont=dict(size=12, color="#12100e"),
                       cliponaxis=False,
                       hovertemplate="%{y}: %{x:.1f} %<extra>Furcht</extra>"))
    f.add_trace(go.Bar(y=namen, x=risiko, orientation="h",
                       name="Einschätzung, selbst Opfer zu werden",
                       marker_color="#b8860b",
                       text=[f"{w:.1f}" for w in risiko], textposition="outside",
                       textfont=dict(size=12, color="#12100e"),
                       cliponaxis=False,
                       hovertemplate="%{y}: %{x:.1f} %<extra>Risikoeinschätzung</extra>"))
    f.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08)
    f.update_xaxes(title="Anteil der Befragten", ticksuffix=" %", range=[0, 60])
    f.update_yaxes(automargin=True, tickfont=dict(size=13, color="#12100e"))
    layout = dict(BASE)
    layout.update(height=430, margin=dict(l=10, r=20, t=54, b=50),
                  legend=dict(orientation="h", yanchor="bottom", y=1.06, x=0,
                              xanchor="left", font=dict(size=14),
                              itemsizing="constant"))
    f.update_layout(**layout)
    return f


def diagramm_skid_orte():
    """Sicherheitsgefühl nach Situation, tagsüber und nachts (SKiD 2024)."""
    pfad = OUT / "skid_furcht.csv"
    if not pfad.exists():
        return None
    daten = [r for r in lies(pfad, delim=";") if r["art"] == "ort"]
    daten.sort(key=lambda r: float(r["wert_2"]))
    namen = [r["bezeichnung"] for r in daten]
    tag = [float(r["wert_1"]) for r in daten]
    nacht = [float(r["wert_2"]) for r in daten]

    f = fig(430)
    f.add_trace(go.Bar(y=namen, x=tag, orientation="h", name="tagsüber",
                       marker_color="#0b4f49",
                       text=[f"{w:.1f}" for w in tag], textposition="outside",
                       textfont=dict(size=12, color="#12100e"), cliponaxis=False,
                       hovertemplate="%{y}: %{x:.1f} %<extra>tagsüber</extra>"))
    f.add_trace(go.Bar(y=namen, x=nacht, orientation="h", name="nachts",
                       marker_color="#b8860b",
                       text=[f"{w:.1f}" for w in nacht], textposition="outside",
                       textfont=dict(size=12, color="#12100e"), cliponaxis=False,
                       hovertemplate="%{y}: %{x:.1f} %<extra>nachts</extra>"))
    f.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08)
    f.update_xaxes(title="Anteil, der sich sicher fühlt", ticksuffix=" %",
                   range=[0, 105])
    f.update_yaxes(automargin=True, tickfont=dict(size=13, color="#12100e"))
    layout = dict(BASE)
    layout.update(height=430, margin=dict(l=10, r=20, t=54, b=50),
                  legend=dict(orientation="h", yanchor="bottom", y=1.06, x=0,
                              xanchor="left", font=dict(size=14),
                              itemsizing="constant"))
    f.update_layout(**layout)
    return f


def diagramm_pmk():
    """Politisch motivierte Kriminalität nach Phänomenbereich.

    Warum je Bereich ein eigenes Feld: Die Bereiche unterscheiden sich um mehr
    als das Zwanzigfache (rechts 42.544 Fälle, religiöse Ideologie 1.983). In
    einem gemeinsamen Maßstab sind die kleinen Bereiche unsichtbar, auf einer
    logarithmischen Achse kann sie niemand lesen. Deshalb sechs kleine Felder
    mit je eigener linearer Skala — der Vergleich läuft innerhalb eines Feldes
    (Verlauf) und nicht über die Felder hinweg.

    Returns:
        plotly.graph_objects.Figure | None
    """
    pfad = OUT / "pmk_zeitreihe.csv"
    if not pfad.exists():
        return None
    daten = lies(pfad, delim=";")

    bereiche = [
        ("gesamt", "Alle Bereiche zusammen"),
        ("rechts", "rechts"),
        ("links", "links"),
        ("sonstige_zuordnung", "sonstige Zuordnung"),
        ("auslaendische_ideologie", "ausländische Ideologie"),
        ("religioese_ideologie", "religiöse Ideologie"),
    ]

    # Zwei Achsen je Feld: Die Gewalttaten liegen um ein Vielfaches unter den
    # Gesamtfallzahlen (4.156 gegen 85.837) und verschwinden in deren Maßstab
    # auf der Nulllinie. Sie bekommen deshalb eine eigene Skala, rechts am Rand.
    f = make_subplots(
        rows=2, cols=3, horizontal_spacing=0.12, vertical_spacing=0.21,
        specs=[[{"secondary_y": True}] * 3, [{"secondary_y": True}] * 3],
        subplot_titles=[t for _, t in bereiche],
    )
    for i, (feld, titel) in enumerate(bereiche):
        zeile, spalte = divmod(i, 3)
        for art, name, farbe, strich in (("gesamt", "alle Straftaten", "#0b4f49", "solid"),
                                         ("gewalt", "davon Gewalttaten", "#b8860b", "dot")):
            reihe = sorted(
                (int(float(r["jahr"])), z(r["faelle"]))
                for r in daten
                if r["art"] == art and r["bereich"] == feld and r["faelle"])
            if not reihe:
                continue
            f.add_trace(go.Scatter(
                x=[j for j, _ in reihe], y=[w for _, w in reihe],
                mode="lines+markers", name=name,
                line=dict(color=farbe, width=2.4, dash=strich),
                # Kleine Marker: Bei 10 Werten je Linie reicht ein Punkt als
                # Hinweis auf den Messwert, große Punkte verdecken die Linie.
                marker=dict(size=3.0, color=farbe),
                legendgroup=name, showlegend=(i == 0),
                hovertemplate="%{y:,.0f} Fälle im Jahr %{x}<extra>" + name + "</extra>",
            ), row=zeile + 1, col=spalte + 1, secondary_y=(art == "gewalt"))
        f.update_yaxes(rangemode="tozero", automargin=True, tickformat=",.0f",
                       row=zeile + 1, col=spalte + 1, secondary_y=False)
        f.update_yaxes(rangemode="tozero", automargin=True, tickformat=",.0f",
                       showgrid=False, tickfont=dict(size=10,
                       color="#8a5305"), row=zeile + 1, col=spalte + 1,
                       secondary_y=True)
        f.update_xaxes(automargin=True, dtick=4, tickfont=dict(size=11),
                       row=zeile + 1, col=spalte + 1)

    layout = dict(BASE)
    f.update_layout(yaxis_title=None, yaxis2_title=None)
    layout.update(height=600, showlegend=True,
                  margin=dict(l=10, r=18, t=76, b=42),
                  legend=dict(orientation="h", yanchor="bottom", y=1.075, x=0,
                              xanchor="left", font=dict(size=14),
                              itemsizing="constant", itemwidth=30),
                  hovermode="closest")
    f.update_layout(**layout)
    return f


def diagramm_skid_delikte():
    """Wovor sich Deutschland fürchtet (SKiD 2024).

    Gegenübergestellt: die Furcht vor einem Delikt und die Einschätzung, selbst
    Opfer zu werden. Die Lücke zwischen beiden ist die eigentliche Aussage —
    gefürchtet wird mehr, als für wahrscheinlich gehalten wird.

    Returns:
        plotly.graph_objects.Figure | None
    """
    pfad = OUT / "skid_furcht.csv"
    if not pfad.exists():
        return None
    daten = [r for r in lies(pfad, delim=";") if r["art"] == "delikt"]
    daten.sort(key=lambda r: float(r["wert_1"]))
    namen = [r["bezeichnung"] for r in daten]
    furcht = [float(r["wert_1"]) for r in daten]
    risiko = [float(r["wert_2"]) for r in daten]

    f = fig(430)
    f.add_trace(go.Bar(y=namen, x=furcht, orientation="h", name="Furcht",
                       marker_color="#0b4f49",
                       text=[f"{w:.1f}" for w in furcht], textposition="outside",
                       textfont=dict(size=12, color="#12100e"),
                       cliponaxis=False,
                       hovertemplate="%{y}: %{x:.1f} %<extra>Furcht</extra>"))
    f.add_trace(go.Bar(y=namen, x=risiko, orientation="h",
                       name="Einschätzung, selbst Opfer zu werden",
                       marker_color="#b8860b",
                       text=[f"{w:.1f}" for w in risiko], textposition="outside",
                       textfont=dict(size=12, color="#12100e"),
                       cliponaxis=False,
                       hovertemplate="%{y}: %{x:.1f} %<extra>Risikoeinschätzung</extra>"))
    f.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08)
    f.update_xaxes(title="Anteil der Befragten", ticksuffix=" %", range=[0, 60])
    f.update_yaxes(automargin=True, tickfont=dict(size=13, color="#12100e"))
    layout = dict(BASE)
    layout.update(height=430, margin=dict(l=10, r=20, t=54, b=50),
                  legend=dict(orientation="h", yanchor="bottom", y=1.06, x=0,
                              xanchor="left", font=dict(size=14),
                              itemsizing="constant"))
    f.update_layout(**layout)
    return f


def diagramm_skid_orte():
    """Sicherheitsgefühl nach Situation, tagsüber und nachts (SKiD 2024)."""
    pfad = OUT / "skid_furcht.csv"
    if not pfad.exists():
        return None
    daten = [r for r in lies(pfad, delim=";") if r["art"] == "ort"]
    daten.sort(key=lambda r: float(r["wert_2"]))
    namen = [r["bezeichnung"] for r in daten]
    tag = [float(r["wert_1"]) for r in daten]
    nacht = [float(r["wert_2"]) for r in daten]

    f = fig(430)
    f.add_trace(go.Bar(y=namen, x=tag, orientation="h", name="tagsüber",
                       marker_color="#0b4f49",
                       text=[f"{w:.1f}" for w in tag], textposition="outside",
                       textfont=dict(size=12, color="#12100e"), cliponaxis=False,
                       hovertemplate="%{y}: %{x:.1f} %<extra>tagsüber</extra>"))
    f.add_trace(go.Bar(y=namen, x=nacht, orientation="h", name="nachts",
                       marker_color="#b8860b",
                       text=[f"{w:.1f}" for w in nacht], textposition="outside",
                       textfont=dict(size=12, color="#12100e"), cliponaxis=False,
                       hovertemplate="%{y}: %{x:.1f} %<extra>nachts</extra>"))
    f.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08)
    f.update_xaxes(title="Anteil, der sich sicher fühlt", ticksuffix=" %",
                   range=[0, 105])
    f.update_yaxes(automargin=True, tickfont=dict(size=13, color="#12100e"))
    layout = dict(BASE)
    layout.update(height=430, margin=dict(l=10, r=20, t=54, b=50),
                  legend=dict(orientation="h", yanchor="bottom", y=1.06, x=0,
                              xanchor="left", font=dict(size=14),
                              itemsizing="constant"))
    f.update_layout(**layout)
    return f


def diagramme_zusammenhaenge():
    """Diagramme aus den Analyseergebnissen (Skripte 18-20)."""
    figs = []
    TEAL, WARM, GRAU = UNTER, UEBER, NEUTRAL

    def lies(pfad, delim=";"):
        import csv as _csv
        with open(pfad, encoding="utf-8") as fh:
            return list(_csv.DictReader(fh, delimiter=delim))

    def f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None


    # 0) Standardisierte Koeffizienten — die vertraute Einheit
    pfad = OUT / "beta_koeffizienten.csv"
    if pfad.exists():
        b = [r for r in lies(pfad) if r["modell"] == "M3"]
        b = sorted(b, key=lambda r: abs(f(r["beta_lpm"])), reverse=True)
        b = b[::-1]
        farben = [TEAL if f(r["beta_lpm"]) < 0 else WARM for r in b]
        fg = fig(540)
        fg.add_trace(go.Bar(
            y=[("● " if r["art"] == "binär" else "") + r["label"] for r in b],
            x=[f(r["beta_lpm"]) for r in b], orientation="h", marker_color=farben,
            customdata=[[f(r["beta_logit"]), r["art"]] for r in b],
            hovertemplate="%{y}<br>β = %{x:+.3f} Standardabweichungen"
                          "<br>logistisch gerechnet: %{customdata[0]:+.3f}"
                          "<br>Art: %{customdata[1]}<extra></extra>"))
        rmax = max(abs(f(r["beta_lpm"])) for r in b) * 1.15
        fg.update_xaxes(title="Zusammenhang mit der Furcht"
                        + "<br><span style='font-size:11px'>umgerechnet auf eine einheitliche Skala — größere Werte heißen stärkerer Zusammenhang</span>",
                        range=[-rmax, rmax])
        fg.add_vline(x=0, line=dict(color="#12100e", width=1.2))
        for name, farbe in [("senkt die Furcht", TEAL), ("erhöht die Furcht", WARM)]:
            fg.add_trace(go.Bar(x=[None], y=[None], orientation="h", name=name,
                                marker_color=farbe, hoverinfo="skip", showlegend=True))
        figs.append(("beta",
                     "Wie stark hängt jedes Merkmal zusammen? (in Standardabweichungen)",
                     "Alle Merkmale werden hier auf eine gemeinsame Skala umgerechnet, damit "
                     "sie sich vergleichen lassen — Jahre, Euro und Skalenpunkte kann man "
                     "sonst nicht nebeneinanderstellen. Längerer Balken heißt stärkerer "
                     "Zusammenhang, Petrol heißt \"geht mit weniger Furcht einher\", Orange "
                     "heißt \"mit mehr Furcht\". Beispiel: Beim Sozialvertrauen liegt der "
                     "Wert bei −0,13 — wer deutlich mehr Vertrauen hat als der Durchschnitt, "
                     "ist tendenziell weniger unsicher. Merkmale mit nur zwei "
                     "Ausprägungen (ja/nein), etwa Frau oder Mann; dort steht der Balken "
                     "für den Unterschied zwischen den beiden Gruppen.",
                     fg, "ESS 1–11, eigene Schätzung (n = 15.440), alle Merkmale gemeinsam"))

    # 2) Verschiebt sich das Bild unter Kontrolle? (AME je Modell)
    pfad = OUT / "modelle_ame.csv"
    if pfad.exists():
        ame = lies(pfad)
        wichtig = ["Frau (vs. Mann)", "Sozialvertrauen (je SD)", "Bildung ISCED (je SD)",
                   "Viktimisierung (Haushalt)", "Vertrauen Justiz (je SD)",
                   "Gesundheit (schlecht hoch)", "Migrationshintergrund",
                   "Wohnort (Land hoch)", "Diskriminierungserfahrung"]
        modelle = ["M1 Soziodemografie", "M2 + Vulnerabilität", "M3 + Einstellungen",
                   "M4 + Wellen"]
        # Hinweis: Merkmale, die erst in einem späteren Modell auftreten, haben
        # in den früheren Modellen keinen Balken.
        farben = {"M1 Soziodemografie": "#d6d3d1", "M2 + Vulnerabilität": "#8f8a85",
                  "M3 + Einstellungen": "#3d9a92", "M4 + Wellen": "#0f766e"}
        fg = fig(560, barmode="group", bargap=0.22)
        for m in modelle:
            werte = []
            for w in wichtig:
                treffer = [r for r in ame if r["modell"] == m and r["label"] == w]
                werte.append(f(treffer[0]["ame_pp"]) if treffer else None)
            fg.add_trace(go.Bar(y=wichtig, x=werte, orientation="h", name=m,
                                marker_color=farben[m],
                                hovertemplate="%{y}<br>" + m + ": %{x:+.2f} PP<extra></extra>"))
        fg.update_xaxes(title="mittlerer marginaler Effekt in Prozentpunkten")
        fg.add_vline(x=0, line=dict(color="#12100e", width=1.2))
        figs.append(("ame",
                     "Was bleibt unter Kontrolle übrig?",
                     "Dieselbe Sache in der anschaulicheren Einheit: um wie viele Prozentpunkte "
                     "steigt die Wahrscheinlichkeit, sich unsicher zu fühlen. Die vier "
                     "Balken je Merkmal sind vier Modelle, die schrittweise mehr Merkmale "
                     "gleichzeitig berücksichtigen — von links (nur Soziodemografie) nach "
                     "rechts (zusätzlich Einstellungen und Erhebungsjahr). Entscheidend ist "
                     "nicht der einzelne Balken, sondern die Frage: Bleibt der Balken "
                     "stehen, wenn man alles andere dazunimmt? Merkmale mit nur einem "
                     "Balken waren im Modell M1 noch nicht enthalten.",
                     fg, "eigene Schätzung (logistische Regression, geclustert nach Bundesland)"))

    # 3) Moderation: Frauen und Männer über die Altersspanne
    pfad = OUT / "moderation_kurven.csv"
    if pfad.exists():
        kr = lies(pfad)
        fg = fig(420)
        alters = [r for r in kr if r["interaktion"] == "geschlecht_f x agea_c_z"]
        if alters:
            xs = sorted({f(r["x"]) for r in alters})
            for gruppe, name, farbe in [(1.0, "Frauen", WARM), (0.0, "Männer", TEAL)]:
                werte = {f(r["x"]): f(r["p_prozent"]) for r in alters if r["gruppe"] == str(gruppe)}
                fg.add_trace(go.Scatter(x=xs, y=[werte.get(x) for x in xs], mode="lines+markers",
                                        name=name, line=dict(color=farbe, width=3),
                                        hovertemplate=name + ": %{y:.1f} %<extra></extra>"))
            fg.update_xaxes(title="Alter (Standardabweichungen vom Mittelwert)",
                            tickvals=[-1.5, 0, 1.5, 2.25],
                            ticktext=["jünger", "Durchschnitt", "älter", "sehr alt"])
            fg.update_yaxes(title="unsicher (vorhergesagt)", ticksuffix=" %")
            figs.append(("moderation_alter",
                         "Frauen und Männer über die Altersspanne",
                         "Vorhergesagte Wahrscheinlichkeit, sich unsicher zu fühlen, bei sonst "
                         "durchschnittlichen Merkmalen. Die Altersabhängigkeit verläuft bei "
                         "Frauen und Männern unterschiedlich — der formale Test dieser "
                         "Interaktion ist signifikant (LR-χ² = 46,6; p < 0,001).",
                         fg, "eigene Schätzung"))

    # 4) Moderation: Wohnort und Sozialvertrauen
    if pfad.exists():
        kr = lies(pfad)
        wohn = [r for r in kr if r["interaktion"] == "stadt_land_num_z x ppltrst_c_z"]
        if wohn:
            fg = fig(420)
            xs = sorted({f(r["x"]) for r in wohn})
            namen = {1.0: "Großstadt", 3.0: "Kleinstadt", 5.0: "Land"}
            farben = {1.0: WARM, 3.0: "#a8a29e", 5.0: TEAL}
            for g, name in namen.items():
                werte = {f(r["x"]): f(r["p_prozent"]) for r in wohn if r["gruppe"] == str(g)}
                fg.add_trace(go.Scatter(x=xs, y=[werte.get(x) for x in xs], mode="lines+markers",
                                        name=name, line=dict(color=farben[g], width=3),
                                        hovertemplate=name + ": %{y:.1f} %<extra></extra>"))
            fg.update_xaxes(title="Sozialvertrauen (Standardabweichungen)",
                            tickvals=[-2, -1, 0, 1, 2],
                            ticktext=["sehr gering", "gering", "mittel", "hoch", "sehr hoch"])
            fg.update_yaxes(title="unsicher (vorhergesagt)", ticksuffix=" %")
            figs.append(("moderation_wohnort",
                         "Sozialvertrauen wirkt je nach Wohnort anders",
                         "Auf dem Land geht ein hohes Sozialvertrauen mit einer deutlich "
                         "niedrigeren vorhergesagten Furcht einher als in der Großstadt; "
                         "in der Großstadt verläuft die Kurve flacher. Der Interaktionstest "
                         "ist signifikant (LR-χ² = 484,6; p < 0,001), die Kurven sind "
                         "Modellvorhersagen bei sonst durchschnittlichen Merkmalen.",
                         fg, "eigene Schätzung"))

    # 5) Mediation: indirekte Effekte
    pfad = OUT / "mediation.csv"
    if pfad.exists():
        med = lies(pfad)
        labels = [r["pfad"] for r in med][::-1]
        ind = [f(r["indirekt"]) for r in med][::-1]
        lo = [f(r["ki_lo"]) for r in med][::-1]
        hi = [f(r["ki_hi"]) for r in med][::-1]
        anteil = [f(r["anteil_pct"]) for r in med][::-1]
        farben = [TEAL if (l is not None and h is not None and l * h > 0) else GRAU
                  for l, h in zip(lo, hi)]
        fg = fig(400)
        fg.add_trace(go.Bar(
            y=labels, x=ind, orientation="h", marker_color=farben,
            error_x=dict(type="data", symmetric=False,
                         array=[(h - i) if h and i else 0 for h, i in zip(hi, ind)],
                         arrayminus=[(i - l) if l and i else 0 for l, i in zip(lo, ind)],
                         color="#78716c", thickness=1.3, width=4),
            customdata=[[a] for a in anteil],
            hovertemplate="%{y}<br>indirekter Effekt %{x:+.4f}<br>"
                          "Anteil am Gesamteffekt %{customdata[0]:.0f} %<extra></extra>"))
        fg.update_xaxes(title="indirekter Effekt (Bootstrap-Perzentilintervall)")
        fg.add_vline(x=0, line=dict(color="#12100e", width=1.2))
        figs.append(("mediation",
                     "Welche Wege führen zur Furcht?",
                     "Zerlegung: Ein Teil des Zusammenhangs zwischen einem Merkmal und der "
                     "Furcht läuft über eine dritte Größe (den Mediator). Beispiel: "
                     "Diskriminierungserfahrung senkt das Sozialvertrauen, und ein geringeres "
                     "Sozialvertrauen geht mit mehr Furcht einher — rund 30 % des "
                     "Gesamtzusammenhangs. Intervalle aus 5.000 Bootstrap-Ziehungen; graue "
                     "Balken schließen die Null ein und sind damit nicht abgesichert.",
                     fg, "eigene Schätzung (OLS-Pfade, Bootstrap)"))

    return figs


def diagramme_zusammenhaenge_texte():
    """Einordnungen zu den Zusammenhang-Diagrammen."""
    return {
        "ame": (
            "Was der Kontrolle standhält",
            "Die Modelle nehmen schrittweise weitere Merkmalsgruppen auf. Wichtig ist die "
            "Bewegung der Balken: Der Geschlechterunterschied und das Sozialvertrauen bleiben "
            "in allen Modellen bestehen, ebenso Bildung, Gesundheit und Wohnort. Zwei "
            "Verschiebungen sind aufschlussreich: Der Zusammenhang mit Diskriminierungserfahrung "
            "verschwindet unter Kontrolle, und der Migrationshintergrund gewinnt an Bedeutung, "
            "der bivariate Zusammenhang war durch andere Merkmale verdeckt."),
        "moderation_alter": (
            "Die Altersabhängigkeit ist geschlechtsspezifisch",
            "Für Männer verläuft die Kurve über die Altersspanne flacher, für Frauen steigt sie "
            "deutlich an. Der formale Test der Interaktion ist signifikant. Damit ist die "
            "Altersumkehr, die wir in der Zeitreihe gesehen haben, auch strukturell sichtbar: "
            "Furcht ist keine Funktion des Alters, sondern des Alters in Verbindung mit dem "
            "Geschlecht."),
        "moderation_wohnort": (
            "Sozialvertrauen wirkt in der Stadt und auf dem Land unterschiedlich",
            "Zwischen Sozialvertrauen und Furcht besteht in allen Wohnorten ein Zusammenhang — "
            "aber auf dem Land ist er deutlich steiler. Zwei Lesarten sind möglich: Auf dem Land "
            "ist die Nachbarschaft relevanter, weil man die Menschen kennt; oder das Vertrauen "
            "in einer Umgebung ohne Anonymität anders gelagert ist. Die Daten können die beiden "
            "nicht trennen."),
        "mediation": (
            "Über welche Wege wirkt ein Merkmal?",
            "Die Zerlegung zeigt, dass Diskriminierungserfahrung zum Teil *über* das "
            "Sozialvertrauen auf die Furcht wirkt: Betroffene vertrauen weniger, und weniger "
            "Vertrauen geht mit mehr Furcht einher. Rund 30 % des Gesamtzusammenhangs laufen "
            "über diesen Pfad. Für die anderen geprüften Wege fällt der Anteil kleiner oder "
            "die Intervalle schließen die Null ein. Methodisch bleibt es eine Zerlegung von "
            "Korrelationen in einem Querschnitt."),
    }


# ---------------------------------------------------------------- SVG-Karte
# Versatz der Kürzel für die Stadtstaaten (Führungslinie vom Marker zum Text)
FUEHRUNG = {"DE3": (74, -40), "DE6": (-80, -44), "DE5": (-84, 30)}

# Beschriftung der Karte: ausgeschriebene Ländernamen. Für die drei Stadtstaaten
# bleibt die Kurzform, weil ihr Gebiet zu klein für den vollen Namen ist — dort
# zeigt das Länderprofil den Namen ohnehin ausgeschrieben.
KUERZEL = {
    "DE1": "Baden-Württemberg", "DE2": "Bayern", "DE3": "Berlin",
    "DE4": "Brandenburg", "DE5": "Bremen", "DE6": "Hamburg",
    "DE7": "Hessen", "DE8": "Mecklenburg-Vorpommern", "DE9": "Niedersachsen",
    "DEA": "Nordrhein-Westfalen", "DEB": "Rheinland-Pfalz", "DEC": "Saarland",
    "DED": "Sachsen", "DEE": "Sachsen-Anhalt", "DEF": "Schleswig-Holstein",
    "DEG": "Thüringen",
}


# Namen, die für eine Zeile zu lang sind, werden getrennt. Getrennt wird am
# Bindestrich oder am Leerzeichen, das der Mitte am nächsten liegt — so bleibt
# jede Hälfte etwa gleich breit.
ZWEIZEILIG = {
    "Baden-Württemberg": ("Baden-", "Württemberg"),
    "Mecklenburg-Vorpommern": ("Mecklenburg-", "Vorpommern"),
    "Nordrhein-Westfalen": ("Nordrhein-", "Westfalen"),
    "Rheinland-Pfalz": ("Rheinland-", "Pfalz"),
    "Sachsen-Anhalt": ("Sachsen-", "Anhalt"),
    "Schleswig-Holstein": ("Schleswig-", "Holstein"),
}


def karte_html(laender, viewbox):
    """Karte mit klickbaren Flächen und ausgeschriebener Beschriftung."""
    flaechen, labels, marken = [], [], []
    # Staffelung: von Norden nach Sueden aufbauen (y-Position der Beschriftung).
    # Die Verzoegerung steht in Sekunden im style-Attribut, die Animation selbst
    # im CSS — so bleibt die Staffelung auch beim Neuzeichnen erhalten.
    reihenfolge = sorted(laender.items(), key=lambda kv: (kv[1].get("label") or [0, 0])[1])
    for i, (_name, l) in enumerate(reihenfolge):
        if "svg" not in l or not l.get("nuts"):
            continue
        nuts = l["nuts"]
        verzug = i * 0.045
        flaechen.append(
            f'<path class="bl" id="p-{nuts}" data-nuts="{nuts}" d="{l["svg"]}" '
            f'style="animation-delay:{verzug:.3f}s" '
            f'tabindex="0" role="button" aria-label="{l["name"]}"><title>{l["name"]}</title></path>')
        lab = l.get("label")
        # Stadtstaaten sind flächenmäßig winzig — zusätzlich ein Marker, damit
        # sie in der Choropleth überhaupt auffallen.
        if lab and nuts in ("DE3", "DE5", "DE6"):
            lx, ly = lab[0] + FUEHRUNG[nuts][0], lab[1] + FUEHRUNG[nuts][1]
            marken.append(
                f'<line class="fl" x1="{lab[0]}" y1="{lab[1]}" x2="{lx}" y2="{ly}"/>'
                f'<circle class="mk" data-nuts="{nuts}" cx="{lab[0]}" cy="{lab[1]}" '
                f'r="15" aria-hidden="true"></circle>')
        if lab:
            # Stadtstaaten liegen dicht beieinander: kleine Kürzel, heller Halo
            # Labelpositionen: Brandenburg nach Osten (sonst liegt der Text in
            # Berlin), Stadtstaaten-Kürzel neben den Marker.
            VERSATZ = {"DE4": (40, 34), "DE3": 76, "DE6": None, "DE5": None, "DEE": (0, 12)}
            klein = nuts in ("DE3", "DE5", "DE6", "DEC")
            v = VERSATZ.get(nuts, (0, 0))
            if v is None:                      # Stadtstaaten: Text am Ende der Führung
                dx, dy = FUEHRUNG[nuts]
            elif isinstance(v, (int, float)):  # Berlin: nur horizontal
                dx, dy = v, -40
            else:
                dx, dy = v
            anker = "middle"
            if nuts in ("DE6", "DE5"):
                anker = "end"
            name = KUERZEL[nuts]
            x, y = lab[0] + dx, lab[1] + dy
            if name in ZWEIZEILIG:
                oben, unten = ZWEIZEILIG[name]
                inhalt = (f'<tspan x="{x}" dy="-15">{oben}</tspan>'
                          f'<tspan x="{x}" dy="31">{unten}</tspan>')
            else:
                inhalt = name
            labels.append(
                f'<text class="kl" data-nuts="{nuts}" x="{x}" y="{y}" '
                f'text-anchor="{anker}" dominant-baseline="middle" '
                f'style="animation-delay:{verzug + 0.14:.3f}s">{inhalt}</text>')
    return (f'<svg class="karte" viewBox="{viewbox}" role="group" '
            f'aria-label="Deutschlandkarte nach Bundesländern">'
            f'<g>{"".join(flaechen)}</g><g class="mk-g">{"".join(marken)}</g>'
            f'<g class="lbl">{"".join(labels)}</g></svg>')


# ---------------------------------------------------------------- Texte
TEXTE_START = {
    "kriminalitaet": ("Kriminalität im Vergleich",
                      "Die Häufigkeitszahl (Fälle je 100.000 Einwohner) unterscheidet sich "
                      "zwischen den Bundesländern um mehr als das Dreifache. Stadtstaaten liegen "
                      "weit vorn — was auch an Pendlern, Touristen und einer anderen Anzeigepraxis "
                      "liegt, nicht nur an mehr Straftaten."),
    "furcht": ("Furcht im Vergleich",
               "Das Unsicherheitsgefühl folgt der Kriminalitätsbelastung nicht. Mecklenburg-"
               "Vorpommern hat die niedrigste Belastung, aber die höchste gemessene Furcht; "
               "Bayern hat beides niedrig. Die Fallzahlen je Land sind klein — gepoolt über "
               "sechs Wellen, mit Intervallen ausgewiesen."),
    "wirtschaft": ("Wirtschaft und Demografie",
                   "BIP je Einwohner und verfügbares Einkommen streuen erheblich. Die Stadtstaaten "
                   "führen beim BIP, beim verfügbaren Einkommen liegen sie näher am Mittelfeld — "
                   "weil dort viel Wertschöpfung entsteht, aber auch die Lebenshaltungskosten höher sind."),
    "justiz": ("Strafverfolgung",
               "Zwischen registrierten Fällen und Verurteilungen liegt eine doppelte Selektion: "
               "Nicht jede Anzeige wird aufgeklärt, nicht jeder aufgeklärte Fall führt zu einer "
               "Verurteilung. Bei Einbruch und Diebstahl ist die Verengung am stärksten."),
}


def main():
    laender, viewbox = lade_daten()
    basis = basis_zahlen(laender)
    figs = diagramme(laender, basis)
    # Die Zusammenhangs-Auswertungen sind vorerst aus der App genommen
    # (Überarbeitung geplant). Funktion und Texte bleiben im Code, damit die
    # Auswertung ohne Nacharbeit wieder eingebunden werden kann:
    #   zusatz = diagramme_zusammenhaenge()
    #   figs.extend(zusatz)
    #   TEXTE_START.update(diagramme_zusammenhaenge_texte())

    modellguete = []
    mg_pfad = OUT / "modelle_guete.csv"
    if mg_pfad.exists():
        with open(mg_pfad, encoding="utf-8") as fh:
            modellguete = list(csv.DictReader(fh, delimiter=";"))
        for r in modellguete:
            for k in ("n",):
                r[k] = int(float(r[k]))
            for k in ("pseudo_r2_mcfadden", "auc", "aic"):
                r[k] = float(r[k]) if r.get(k) else None

    daten = {
        "basis": basis,
        "laender": laender,
        "texte_start": TEXTE_START,
        "modellguete": modellguete,
        "wappen": wappen_laden(),
    }

    # Diagramme als JSON (Lazy-Rendering)
    fig_json = {}
    fig_meta = []
    for eintrag in figs:
        # Ältere Diagramme liefern fünf Felder, neuere mit ausführlicher
        # Einordnung sechs (id, Titel, Kurztext, Figur, Quelle, Langtext).
        fid, titel, unter, f, quelle = eintrag[:5]
        langtext = eintrag[5] if len(eintrag) > 5 else None
        fig_json[fid] = json.loads(pio.to_json(f))
        fig_meta.append({"id": fid, "titel": titel, "unter": unter,
                         "quelle": quelle, "langtext": langtext})

    karte = karte_html(laender, viewbox)
    html = baue_html(karte, daten, fig_json, fig_meta)

    # Eine einzige Datei: Sie ist die Startseite, und die Karte ist der Einstieg.
    # Die Diagramm-Bibliothek wird eingebettet, damit die Seite ohne weitere
    # Abrufe und ohne Internet-Bindung vollständig funktioniert.
    ziel = ROOT / "dashboard" / "index.html"
    ziel.write_text(html.replace("<!--PLOTLY-->", "<script>" + get_plotlyjs() + "</script>"),
                    encoding="utf-8")
    print(f"index.html: {ziel.stat().st_size/1e6:.2f} MB")
    return laender, basis



SCHRIFT_PFAD = pathlib.Path(__file__).resolve().parent / "fonts" / "plex.css"


def schrift_css():
    """Eingebettete Webfont-Schnitte.

    Die Schnitte liegen als data:-URL im CSS, damit die App offline lauffaehig
    bleibt und auf jedem Geraet dieselbe Typografie zeigt.

    Returns:
        str: CSS-Text mit den @font-face-Regeln (leer, wenn nicht erzeugt).
    """
    if SCHRIFT_PFAD.exists():
        return SCHRIFT_PFAD.read_text(encoding="utf-8")
    return ""


def baue_html(karte, daten, fig_json, fig_meta):
    css = CSS
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#12100e">
<title>Die (un)berechtigte Furcht vor Kriminalität in Deutschland</title>
<!--PLOTLY-->
<style>{schrift_css()}</style>
<style>{css}</style>
</head>
<body>
<div id="app">
  <header class="kopf">
    <div class="kopf-inner">
      <div class="kopf-titel">
        <h1>Die (un)berechtigte Furcht vor Kriminalität in Deutschland</h1>
        <p>Registrierte Kriminalität, Strafverfolgung und das Sicherheitsgefühl der
        Bevölkerung — für die Republik und für jedes Bundesland.</p>
      </div>
    </div>
  </header>

  <nav class="tabs" id="tabs">
    <button class="tab" data-ansicht="inhalt">Inhalt</button>
    <button class="tab active" data-ansicht="karte">Karte</button>
    <button class="tab" data-ansicht="kriminalitaet">Kriminalität</button>
    <button class="tab" data-ansicht="furcht">Furcht</button>
    <button class="tab" data-ansicht="justiz">Strafverfolgung</button>
    <button class="tab" data-ansicht="methodik">Daten &amp; Methoden</button>
  </nav>

  <main id="inhalt"></main>

  <footer class="fuss">
    <p><strong>Quellen.</strong> BKA Polizeiliche Kriminalstatistik (Länder-Grundtabelle 2025,
    T01-Zeitreihe, T12 aufgeklärte Fälle, SKiD 2024/2020); Destatis (Bevölkerung, Nationalität)
    und Arbeitskreis VGR der Länder (BIP, verfügbares Einkommen); European Social Survey
    (Runden 1–11, eigene Berechnung, gewichtet); Eurostat (crim_off_cat); GISCO/Eurostat
    für die Kartengeometrie (CC BY 4.0).</p>
    <p><strong>Grenzen.</strong> Registrierte Fälle sind polizeilich bekannt gewordene Vorgänge —
    kein Nachweis einer Straftat und keine Verurteilung. Länderwerte zur Furcht stammen aus
    gepoolten Befragungswellen mit kleinen Fallzahlen je Land; belastbare und unsichere Werte
    sind getrennt gekennzeichnet. Gruppenvergleiche sind bivariat und unadjustiert.</p>
    <p class="credit">Kartenillustration im Kopfbereich: <strong>Vecteezy</strong>
    (vecteezy.com), Namensnennung nach der Vecteezy-Free-Lizenz.</p>
    <p class="credit">Erstellt von <strong>Christopher Vantis</strong> mit <strong>Hermes</strong>
    (KI-Assistent). Auswahl der Fragen, Deutung und Prüfung der Ergebnisse liegen beim Autor;
    Recherche, Auswertung und Umsetzung entstanden im Dialog mit dem Assistenten. Fehler wären
    ärgerlich — Hinweise sind willkommen.</p>
  </footer>
</div>

<div id="karte-svg" hidden>{karte}</div>

<script id="daten" type="application/json">{json.dumps(daten, ensure_ascii=False)}</script>
<script id="figuren" type="application/json">{json.dumps(fig_json, ensure_ascii=False)}</script>
<script id="figmeta" type="application/json">{json.dumps(fig_meta, ensure_ascii=False)}</script>
{SCRIPT}
</body>
</html>"""


CSS = """
:root{
 /* Petrol als Leitfarbe, warmes Terrakotta als Akzent — bewusst kein Blau. */
 --teal:#0f766e; --teal-dunkel:#115e59; --teal-hell:#14b8a6;
 --akzent:#a16207; --akzent-hell:#ca8a04;
 --ink:#12100e; --text:#3d3833; --muted:#6b645e; --line:#e7e2dc;
 --bg:#faf8f5; --card:#ffffff; --soft:#f5f2ee; --radius:20px;
 --rail:1180px; --gutter:20px;
 --font:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
 --schatten:0 1px 2px rgba(24,20,16,.04), 0 12px 32px -18px rgba(24,20,16,.22);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-size:16px;line-height:1.6;
 font-family:var(--font);font-variant-numeric:tabular-nums;
 -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}

/* ---------- Kopfbereich: flach, damit die Karte früh sichtbar ist ---------- */
.kopf{color:#fff;padding:20px 0 18px;
 background-color:#16403b;
 background-image:url("data:image/png;base64,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");
 background-size:auto 100%;background-position:right center;background-repeat:no-repeat;
 border-radius:0 0 20px 20px}
.kopf-inner{max-width:var(--rail);margin-inline:auto;padding-inline:var(--gutter);
 display:flex;flex-wrap:wrap;gap:18px 28px;align-items:center;justify-content:space-between}
.kopf-titel{min-width:260px;flex:1 1 340px}
.kopf h1{margin:0;font-size:clamp(1.22rem,2.2vw,1.58rem);line-height:1.2;letter-spacing:-.022em}
.kopf p{margin:3px 0 0;font-size:.82rem;color:#b8b2ab;max-width:72ch}
.kpi-leiste{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;
 flex:0 1 640px}
.kpi-leiste div{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);
 border-radius:11px;padding:6px 11px;min-width:0}
.kpi-leiste b{display:block;font-size:1.16rem;font-weight:600;letter-spacing:-.015em;
 font-variant-numeric:tabular-nums;color:#fff}
.kpi-leiste span{font-size:.67rem;color:#b8b2ab;text-transform:uppercase;
 letter-spacing:.04em;white-space:nowrap;display:block}

.tabs{position:sticky;top:0;z-index:30;display:flex;gap:4px;overflow-x:auto;
 padding:8px max(var(--gutter),calc((100% - var(--rail))/2 + var(--gutter)));
 background:rgba(250,248,245,.93);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);
 -webkit-overflow-scrolling:touch;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:0 0 auto;border:0;background:transparent;color:var(--text);padding:9px 16px;
 border-radius:999px;font-size:.91rem;font-weight:600;cursor:pointer;transition:all .2s ease;
 white-space:nowrap}
.tab:hover{background:#ece7e1;color:var(--ink)}
.tab.active{background:var(--teal);color:#fff;box-shadow:0 6px 16px -8px rgba(15,118,110,.7)}
main{max-width:var(--rail);margin-inline:auto;padding:22px var(--gutter) 64px}
.view{animation:fade .35s ease both}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}

/* ---------- Karte ---------- */
.karte-wrap{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
 padding:14px 16px 10px;box-shadow:var(--schatten)}
.karte-kopf{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
.karte-kopf h2{margin:0 0 3px;font-size:clamp(1rem,2.6vw,1.22rem);color:var(--ink);letter-spacing:-.01em}
.karte-kopf p{margin:0;font-size:.85rem;color:var(--muted);max-width:44ch}
.karte-titel{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.karte-titel .kl{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.09em}
.karte-titel select{padding:8px 34px 8px 12px;border-radius:11px;border:1px solid var(--line);
 background:#fff;font:inherit;font-size:.88rem;color:var(--ink);cursor:pointer;
 appearance:none;-webkit-appearance:none;transition:border-color .2s ease;
 background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8'><path d='M1 1l5 5 5-5' fill='none' stroke='%2378716c' stroke-width='1.6' stroke-linecap='round'/></svg>");
 background-repeat:no-repeat;background-position:right 12px center}
.karte-titel select:hover{border-color:var(--teal)}
.karte-grid{display:grid;grid-template-columns:1fr;gap:16px;align-items:start;margin-top:6px}
.karte-rechts h3{margin:2px 0 10px;font-size:.95rem;color:var(--ink)}
.karte{width:100%;height:auto;display:block;margin:10px auto 0;max-height:min(84vh,1000px)}
.bl{fill:#eee9e3;stroke:#ffffff;stroke-width:1.8;cursor:pointer;
 transition:fill .35s ease,filter .3s ease;
 transform-box:fill-box;transform-origin:center;
 animation:einsetzen .5s cubic-bezier(.22,.9,.3,1) both}
@keyframes einsetzen{
 from{opacity:0;transform:scale(.82)}
 to{opacity:1;transform:scale(1)}
}
.karte text{animation:einblenden .55s ease both}
@keyframes einblenden{from{opacity:0}to{opacity:1}}
/* Wer Bewegung ablehnt, bekommt die Karte sofort und unbewegt. */
@media (prefers-reduced-motion:reduce){
 .bl,.karte text{animation:none}
 .bl{transition:none}
}
.bl:hover{filter:brightness(.94) drop-shadow(0 6px 12px rgba(24,20,16,.28))}
.bl:focus{outline:3px solid var(--teal);outline-offset:1px}
.fl{stroke:#12100e;stroke-width:1.2;stroke-dasharray:4 3;pointer-events:none}
.mk{stroke:#12100e;stroke-width:1.4;cursor:pointer;transition:fill .3s ease}
.mk-g{pointer-events:all}
.lbl text{font-size:23px;font-weight:600;fill:#12100e;pointer-events:none}
.legende{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:.8rem;color:var(--muted)}
.legende .kenn-hinweis{flex-basis:100%;margin-top:9px;padding-top:9px;
 border-top:1px solid var(--line);color:var(--text);font-size:.83rem;line-height:1.5}
.legende .stufen{display:flex;gap:3px}
.legende .stufen i{width:26px;height:11px;border-radius:3px;display:block}
.rank-gruppe{margin-bottom:12px}
.rank-unter{margin:-4px 0 10px;font-size:.79rem;color:var(--muted)}
#ranking{max-height:600px;overflow-y:auto;padding-right:4px}
#ranking::-webkit-scrollbar{width:7px}
#ranking::-webkit-scrollbar-thumb{background:#d6d0c8;border-radius:4px}
.rank-mehr{display:block;width:auto;border:0;background:transparent;padding:8px 2px;
 font:inherit;font-size:.83rem;font-weight:600;color:var(--teal);cursor:pointer;
 text-decoration:underline;text-underline-offset:3px;margin-top:6px}
.rank-mehr:hover{color:var(--teal-dunkel)}
#ranking h4{margin:0 0 6px;font-size:.7rem;text-transform:uppercase;letter-spacing:.09em;
 color:var(--muted);font-weight:650}
.rank-zeile{display:flex;align-items:center;gap:9px;width:100%;text-align:left;border:0;
 background:var(--soft);border-radius:11px;padding:7px 10px;margin-bottom:4px;font:inherit;
 font-size:.87rem;color:var(--text);cursor:pointer;transition:background .18s ease,transform .18s ease}
.rank-zeile:hover{background:#ece7e1;transform:translateX(2px)}
.rank-punkt{width:11px;height:11px;border-radius:3px;flex:0 0 auto;border:1px solid rgba(18,16,14,.35)}
.wappen{height:27px;width:auto;flex:0 0 auto;display:inline-block;vertical-align:-4px;
 margin-right:8px}
.lkopf h2 .wappen{height:40px;vertical-align:-6px;margin-right:12px}
.rank-name{flex:1 1 auto;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rank-wert{font-variant-numeric:tabular-nums;font-weight:650;color:var(--ink);white-space:nowrap}
@media (min-width:1040px){
 .karte-grid{grid-template-columns:minmax(0,1.6fr) minmax(268px,1fr)}
 .karte-rechts{border-left:1px solid var(--line);padding-left:16px}
}

/* ---------- Karten und Kennzahlen ---------- */
.karten{display:grid;gap:18px;margin-top:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
 padding:20px 20px 14px;box-shadow:var(--schatten);animation:auf .45s ease both}
@keyframes auf{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.card h3{margin:0 0 6px;font-size:clamp(1.05rem,2.4vw,1.28rem);color:var(--ink);
 letter-spacing:-.018em;font-weight:600}
.card .unter{margin:0 0 16px;font-size:.9rem;color:var(--muted);max-width:78ch;line-height:1.55}
.html-legende{display:flex;flex-wrap:wrap;gap:6px 16px;margin:2px 0 4px;
 font-size:.83rem;color:var(--text)}
.html-legende span{display:inline-flex;align-items:center;gap:7px}
.html-legende i{width:13px;height:13px;border-radius:3px;display:block;flex:0 0 auto}
.chart{overflow:hidden;min-height:200px}
.quelle{margin:12px 0 0;padding-top:11px;border-top:1px solid var(--line);
 font-size:.78rem;color:var(--muted);line-height:1.5}
.hinweis{background:#faf7f2;border:1px solid #e8e0d5;border-left:4px solid #c9bdae;
 border-radius:0 16px 16px 0;padding:14px 17px;font-size:.92rem;color:#4a443d;
 margin:18px 0;line-height:1.6}
.kk{display:grid;grid-template-columns:repeat(auto-fit,minmax(188px,1fr));gap:10px;margin-top:16px}
.kk div{background:var(--soft);border-radius:14px;padding:11px 13px;min-height:72px;
 display:flex;flex-direction:column;justify-content:flex-start}
.kk b{display:block;color:var(--ink);font-size:1.3rem;font-weight:600;letter-spacing:-.02em;
 font-variant-numeric:tabular-nums;white-space:nowrap;line-height:1.25}
.kk .einheit{font-weight:400;color:var(--muted)}
.kk span{font-size:.78rem;color:var(--muted);line-height:1.3;margin-top:1px}
.tabelle{width:100%;border-collapse:collapse;font-size:.9rem;margin:4px 0 6px}
.tabelle th{text-align:left;font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;
 color:var(--muted);font-weight:650;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
.tabelle td{padding:9px 10px;border-bottom:1px solid #f3efea}
.tabelle tbody tr{transition:background .18s ease}
.tabelle tbody tr:hover{background:#f7f2ec}
.tabelle .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.glossar{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
 padding:16px 20px;margin:18px 0;box-shadow:var(--schatten)}
.glossar summary{cursor:pointer;font-weight:600;color:var(--teal);font-size:1.02rem;
 display:flex;align-items:center;gap:9px;list-style:none}
.glossar summary::-webkit-details-marker{display:none}
.glossar summary::marker{content:""}
.glossar summary::before{content:"";width:9px;height:9px;flex:0 0 auto;
 border-right:2px solid var(--teal);border-bottom:2px solid var(--teal);
 transform:rotate(-45deg);transition:transform .2s ease;margin-left:2px}
.glossar[open] summary::before{transform:rotate(45deg)}
.glossar-inhalt{margin-top:14px;display:grid;gap:14px}
.glossar-punkt h4{margin:0 0 3px;font-size:.9rem;color:var(--ink)}
.glossar-punkt p{margin:0;font-size:.89rem;color:var(--text);line-height:1.6}
.klein{font-size:.85rem;color:var(--muted)}
.schritt{margin:16px 0 4px;font-size:.95rem;color:var(--ink);font-weight:600}
.einordnung > h4.schritt:first-of-type{margin-top:4px}
.note{background:var(--soft);border-radius:14px;padding:12px 14px;margin-top:14px}
.note h4{margin:0 0 5px;font-size:.88rem;color:var(--ink)}
.note p{margin:0;font-size:.88rem;color:var(--text)}
.einordnung{font-size:.94rem;color:var(--text);line-height:1.7}
.zurueck{display:inline-flex;align-items:center;gap:8px;background:#fff;border:1px solid var(--line);
 border-radius:999px;padding:10px 18px;font:inherit;font-weight:600;color:var(--teal);cursor:pointer;
 transition:all .2s ease;margin-bottom:14px;box-shadow:var(--schatten)}
.zurueck:hover{background:var(--teal);color:#fff;border-color:var(--teal)}
.lkopf{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
 padding:22px 20px;box-shadow:var(--schatten)}
.lkopf h2{margin:0 0 4px;font-size:clamp(1.5rem,4.2vw,2.1rem);color:var(--ink);
 letter-spacing:-.03em;font-weight:600}
.lkopf p{margin:0;color:var(--muted);font-size:.93rem}
details{background:var(--card);border:1px solid var(--line);border-radius:16px;
 padding:14px 16px;margin:12px 0}
details summary{list-style:none}
summary{cursor:pointer;font-weight:650;color:var(--teal)}
details ul{margin:10px 0 0;padding-left:20px}
details li{margin:6px 0;font-size:.89rem}
.fuss{max-width:var(--rail);margin-inline:auto;padding:30px var(--gutter) 56px;
 color:var(--muted);font-size:.86rem}
.fuss p{margin:10px 0}
.fuss .credit{margin-top:22px;padding-top:16px;border-top:1px solid var(--line);
 font-size:.83rem;color:var(--muted)}
@media (max-width:640px){
 .kopf{padding:16px 14px}
 .kpi-leiste{width:100%}
 .kpi-leiste div{flex:1 1 96px;min-width:88px}
 .tab{padding:8px 13px;font-size:.84rem}
 main{padding:14px 12px 46px}
 .card,.karte-wrap,.lkopf{border-radius:16px;padding:16px 14px}
 .karte{max-height:none}
}
"""

SCRIPT = """
<script>
const DATEN = JSON.parse(document.getElementById('daten').textContent);
const FIGS = JSON.parse(document.getElementById('figuren').textContent);
const META = JSON.parse(document.getElementById('figmeta').textContent);
const L = DATEN.laender;
const LN = {};                       /* Zugriff über den NUTS-Code (DE1 … DEG) */
Object.values(L).forEach(l => { if (l.nuts) LN[l.nuts] = l; });
const B = DATEN.basis;
// Werkzeugleiste an: Zoomen, Verschieben, als Bild speichern. Ohne sie
// fehlen genau die Funktionen, die man von Dash kennt.
const KONF = {responsive:true, displaylogo:false, scrollZoom:true,
  displayModeBar:true, modeBarButtonsToRemove:['lasso2d','select2d'],
  toImageButtonOptions:{format:'png', filename:'kriminalitaet-sicherheit', scale:2}};

/* ---------- Hilfsfunktionen ---------- */
const nf = (v, d = 0) => (v === null || v === undefined || isNaN(v)) ? '—'
  : v.toLocaleString('de-DE', {minimumFractionDigits:d, maximumFractionDigits:d});
const pct = (v, d = 1) => (v === null || v === undefined) ? '—' : nf(v, d) + ' %';

/* ---------- Karte einfärben ---------- */
// Jede Kennzahl mit einer Einordnung: was der Wert bedeutet, worauf er sich
// bezieht und woher er stammt. Ohne diese Angabe ist eine farbige Karte nicht
// lesbar — dieselbe Zahl bedeutet je nach Bezugsgröße etwas anderes.
const KENNZAHLEN = {
  hz:      {label:'Kriminalitätsbelastung', kurz:'Belastung', einheit:0,
            wert:l => ((l.kriminalitaet['Straftaten insgesamt']||{}).hz),
            hinweis:'Registrierte Straftaten je 100.000 Einwohner im Jahr 2025. '
              + 'Die Umrechnung auf die Einwohnerzahl macht Länder '
              + 'unterschiedlicher Größe vergleichbar. Gezählt wird, was der '
              + 'Polizei bekannt geworden ist — nicht, was tatsächlich passiert ist.'},
  furcht:  {label:'Unsicherheitsgefühl', kurz:'Furcht', einheit:1,
            wert:l => l.furcht.unsicher,
            hinweis:'Anteil der Befragten, die sich nachts im eigenen Wohngebiet '
              + 'unsicher fühlen. Aus dem European Social Survey (Runden 1–11, '
              + '2002–2023, Deutschland, gewichtet). Je Bundesland 121 bis 3.332 '
              + 'Befragte; Länder mit weniger als 300 sind in der Karte grau.'},
  aq:      {label:'Aufklärungsquote', kurz:'Aufklärung', einheit:1,
            wert:l => ((l.kriminalitaet['Straftaten insgesamt']||{}).aq),
            hinweis:'Anteil der registrierten Fälle, die die Polizei als '
              + 'aufgeklärt meldet (2025). Eine hohe Quote heißt nicht wenig '
              + 'Kriminalität: Sie kann auch bedeuten, dass mehr Fälle angezeigt '
              + 'werden, die leicht aufzuklären sind.'},
  bip:     {label:'BIP je Einwohner', kurz:'Wirtschaftskraft', einheit:0,
            wert:l => l.bip_je_ew,
            hinweis:'Bruttoinlandsprodukt je Einwohner in Euro (2024), '
              + 'Arbeitskreis Volkswirtschaftliche Gesamtrechnungen der Länder. '
              + 'Ein Maß für die Wirtschaftsleistung, nicht für das Einkommen '
              + 'der Haushalte.'},
  alq:     {label:'Arbeitslosenquote', kurz:'Arbeitslosigkeit', einheit:1,
            wert:l => l.alq,
            hinweis:'Anteil der registrierten Arbeitslosen an allen '
              + 'Erwerbspersonen (2025), Statistik der Bundesagentur für Arbeit. '
              + 'Bezogen auf alle zivilen Erwerbspersonen.'},
  mh:      {label:'Migrationshintergrund', kurz:'Migrationsanteil',
            einheit:1, wert:l => l.mh_anteil,
            hinweis:'Anteil der Bevölkerung mit Migrationshintergrund '
              + '(Mikrozensus). Schließt eingebürgerte Deutsche, Spätaussiedler '
              + 'und ihre Nachkommen ein — deshalb höher als der '
              + 'Ausländeranteil.'},
  ausland: {label:'Ausländeranteil', kurz:'Ausländeranteil', einheit:1,
            wert:l => l.auslaenderanteil,
            hinweis:'Anteil der Personen ohne deutsche Staatsangehörigkeit '
              + '(Zensus 2022). Nur die Staatsangehörigkeit, nicht die Herkunft. '
              + 'Liegt deutlich unter dem Migrationsanteil.'},
  dichte:  {label:'Bevölkerungsdichte', kurz:'Dichte', einheit:0,
            wert:l => l.dichte,
            hinweis:'Einwohner je Quadratkilometer, berechnet aus '
              + 'Bevölkerungszahl und Fläche (2025). Ein Maß für die '
              + 'Besiedlung — Stadtstaaten liegen um ein Vielfaches höher als '
              + 'Flächenländer.'},
};
const // Fünf Stufen, alle hell genug für schwarze Schrift ohne Rand.
// Die dunkelste Stufe hat gegen Schwarz noch 5,1:1 Kontrast.
STUFEN = ['#f2f8f6', '#d3e9e4', '#a8d5ce', '#74b8af', '#3d9187'];

/* Farbstufen nach Rang (Quantile), nicht linear: sonst ziehen die Stadtstaaten
   das Maximum so hoch, dass alle Flächenländer in den hellsten Stufen landen. */
function grenzenNachRang(werte){
  const w = werte.slice().sort((a, b) => a - b);
  const g = [];
  for (let i = 1; i < STUFEN.length; i++){
    g.push(w[Math.floor(i * w.length / STUFEN.length)]);
  }
  return g;
}
function klasseRang(v, grenzen){
  if (v === null || v === undefined || isNaN(v)) return '#eee9e3';
  let i = 0;
  while (i < grenzen.length && v >= grenzen[i]) i++;
  return STUFEN[i];
}

function karteFaerben(kennzahl){
  const k = KENNZAHLEN[kennzahl];
  const werte = Object.values(L).map(l => k.wert(l)).filter(v => v !== null && v !== undefined && !isNaN(v));
  const lo = Math.min(...werte), hi = Math.max(...werte);
  const grenzen = grenzenNachRang(werte);
  rankingZeigen(k, grenzen);
  document.querySelectorAll('.bl, .mk').forEach(p => {
    const l = LN[p.dataset.nuts];
    const farbe = l ? klasseRang(k.wert(l), grenzen) : '#eee9e3';
    if (p.classList.contains('mk')){ p.style.fill = farbe; p.style.stroke = '#12100e'; }
    else { p.style.fill = farbe; }
  });
  // Legende
  const leg = document.getElementById('legende');
  if (leg){
    leg.innerHTML = '<span>niedrig ' + nf(lo, k.einheit) + '</span><span class="stufen">'
      + STUFEN.map(c => '<i style="background:' + c + '"></i>').join('')
      + '</span><span>hoch ' + nf(hi, k.einheit) + '</span>'
      + '<span style="margin-left:6px">(' + k.kurz + ', Stufen nach Rang)</span>'
      // Einordnung der Kennzahl: was der Wert bedeutet und woher er stammt.
      + (k.hinweis ? '<span class="kenn-hinweis">' + k.hinweis + '</span>' : '');
  }
}

function rankingZeigen(k, grenzen){
  const box = document.getElementById('ranking');
  if (!box) return;
  const titel = document.getElementById('rank-titel');
  const unter = document.getElementById('rank-unter');
  if (unter) unter.textContent = 'Kennzahl: ' + k.kurz;
  const liste = Object.values(L)
    .map(l => ({name: l.name, nuts: l.nuts, wert: k.wert(l)}))
    .filter(x => x.wert !== null && x.wert !== undefined && !isNaN(x.wert))
    .sort((a, b) => b.wert - a.wert);
  function gruppe(t, eintraege){
    return '<div class="rank-gruppe"><h4>' + t + '</h4>' + eintraege.map(x =>
      '<button class="rank-zeile" data-nuts="' + x.nuts + '">'
      + '<span class="rank-punkt" style="background:' + klasseRang(x.wert, grenzen) + '"></span>'
      + (DATEN.wappen[x.nuts] || '')
      + '<span class="rank-name">' + x.name + '</span>'
      + '<span class="rank-wert">' + nf(x.wert, k.einheit) + '</span></button>').join('') + '</div>';
  }
  const voll = box.dataset.voll === '1';
  const bez = (KENNZAHLEN[kennzahl] || {}).kurz || '';
  box.innerHTML = voll
    ? gruppe('Alle ' + liste.length + ' Bundesländer · ' + bez, liste)
    : gruppe('Höchste Werte · ' + bez, liste.slice(0, 5))
      + gruppe('Niedrigste Werte · ' + bez, liste.slice(-5).reverse());
  const um = document.createElement('button');
  um.className = 'rank-mehr';
  um.textContent = voll ? 'Nur die Extremwerte zeigen' : 'Alle ' + liste.length + ' anzeigen';
  um.addEventListener('click', () => {
    box.dataset.voll = voll ? '0' : '1';
    rankingZeigen(k, grenzen);
  });
  box.appendChild(um);
}

/* ---------- Diagramme faul zeichnen ---------- */
// Diagramme an die Fenstergröße anpassen. Plotly skaliert die Fläche mit,
// aber nicht die Schrift: In einem schmalen Fenster — und auf dem Handy —
// werden Achsen und Legende sonst zu klein zum Lesen.
let anpassungsTimer = null;
function diagrammeAnpassen(){
  const schmal = window.innerWidth < 720;
  document.querySelectorAll('.js-plotly-plot').forEach(el => {
    if (!el || !el.layout) return;
    try {
      // Marker auf schmalen Fenstern verkleinern; sonst stoßen die beiden
      // Herkunftsgruppen trotz seitlichem Versatz aneinander.
      if (el.data) {
        el.data.forEach(t => { if (t.marker && t.mode && t.mode.indexOf('markers') >= 0) {
          Plotly.restyle(el, {'marker.size': schmal ? 19 : 27}, [el.data.indexOf(t)]);
          if (t.textfont) Plotly.restyle(el, {'textfont.size': schmal ? 14 : 19},
                                          [el.data.indexOf(t)]);
        }});
      }
      // Auf schmalen Fenstern die Legende unter das Diagramm: Sie bricht
      // waagerecht nicht um und lief sonst über den Rand hinaus.
      // Legende auf schmalen Fenstern aus dem Diagramm herausnehmen: Als
      // Plotly-Legende überdeckt sie dort Achsentitel und Punkte, weil sie
      // weder umbricht noch in die Randberechnung eingeht.
      Plotly.relayout(el, {
        'showlegend': !schmal,
        'font.size': schmal ? 15 : 12.5,
        // Marker sind im Layout fest gesetzt; auf schmalen Fenstern brauchen
        // sie weniger Durchmesser, sonst stoßen die beiden Herkunftsgruppen
        // trotz Versatz aneinander.
        'xaxis.tickfont.size': schmal ? 14 : 12,
        'yaxis.tickfont.size': schmal ? 14 : 12,
        'legend.font.size': schmal ? 14 : 14,
        'legend.orientation': schmal ? 'v' : 'h',
        'legend.x': 0,
        'legend.y': schmal ? -0.42 : 1.05,
        'legend.yanchor': schmal ? 'top' : 'bottom',
        // Links und rechts genug Platz für die Achsentitel: Bei 8 Pixeln
        // wurde „Anteil mit Unsicherheitsgefühl" abgeschnitten und der
        // äußerste x-Wert nur halb beschriftet.
        'margin.l': schmal ? 52 : 10,
        'margin.r': schmal ? 26 : 20,
        'margin.b': schmal ? 64 : 50,
        'margin.t': schmal ? 66 : 54,
      });
    } catch (e) { /* Diagramm noch nicht fertig gezeichnet */ }
  });
}
window.addEventListener('resize', () => {
  clearTimeout(anpassungsTimer);
  anpassungsTimer = setTimeout(() => {
    diagrammeAnpassen();
    // Legende mitziehen: Beim Drehen des Geräts wechselt sie zwischen
    // Diagramm und eigener Zeile.
    document.querySelectorAll('.js-plotly-plot').forEach((el, i) => {
      const figur = FIGS && FIGS[el.dataset.fig] ? FIGS[el.dataset.fig] : null;
      if (figur) htmlLegende(el, figur);
    });
  }, 240);
});

// Ersatzlegende unter dem Diagramm für schmale Fenster.
function htmlLegende(el, f){
  const alt = el.parentNode.querySelector('.html-legende');
  if (alt) alt.remove();
  if (window.innerWidth >= 720) return;
  const eintraege = (f.data || []).filter(t => t.showlegend !== false && t.name);
  if (!eintraege.length) return;
  const box = document.createElement('div');
  box.className = 'html-legende';
  // Das Geschlechtszeichen gehört in die Legende: Frauen und Männer teilen
  // sich die Farben, unterscheidbar sind sie nur über das Symbol.
  box.innerHTML = eintraege.map(t => {
    const farbe = (t.marker && t.marker.color) || (t.line && t.line.color) || '#3f3a35';
    return '<span><i style="background:' + farbe + '"></i>' + t.name + '</span>';
  }).join('');
  el.parentNode.insertBefore(box, el.nextSibling);
}

function zeichne(el){
  if (el.dataset.state) return;
  el.dataset.state = 'laeuft';
  const id = el.dataset.fig;
  const f = FIGS[id];
  if (!f){ return; }
  const lay = Object.assign({}, f.layout || {});
  lay.autosize = true;
  if (window.innerWidth < 560 && lay.height) lay.height = Math.min(lay.height, 330);
  Plotly.newPlot(el, f.data, lay, KONF).then(() => {
    el.dataset.state = 'fertig';
    diagrammeAnpassen();
    htmlLegende(el, f);
  })
    .catch(() => { delete el.dataset.state; });
}
function beobachte(){
  const ziele = document.querySelectorAll('.chart[data-fig]');
  if (!('IntersectionObserver' in window)){ ziele.forEach(zeichne); return; }
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting){ zeichne(e.target); io.unobserve(e.target); }
  }), {rootMargin:'300px 0px'});
  ziele.forEach(z => io.observe(z));
  setTimeout(() => document.querySelectorAll('.chart[data-fig]:not([data-state])').forEach(zeichne), 2500);
}

/* ---------- Bausteine ---------- */
function glossarEintrag(begriff, text){
  return '<div class="glossar-punkt"><h4>' + begriff + '</h4><p>' + text + '</p></div>';
}

function kartenblock(ids, mitEinordnung){
  return ids.map(id => {
    const m = META.find(x => x.id === id);
    if (!m) return '';
    let eo = '';
    if (mitEinordnung && DATEN.texte_start[id]){
      const [h, t] = DATEN.texte_start[id];
      eo = '<div class="note"><h4>' + h + '</h4><p>' + t + '</p></div>';
    }
    return '<section class="card"><h3>' + m.titel + '</h3><p class="unter">' + m.unter
      + '</p><div class="chart" data-fig="' + id + '"></div>'
      + eo + '<p class="quelle">Quelle: ' + m.quelle + '</p>'
      + (m.langtext ? '<p class="langtext">' + m.langtext + '</p>' : '')
      + '</section>';
  }).join('');
}

function kacheln(items){
  return '<div class="kk">' + items.map(i =>
    '<div><b>' + i[1] + '</b><span>' + i[0] + '</span></div>').join('') + '</div>';
}

/* ---------- Ansicht: Karte ---------- */
function ansichtKarte(){
  const tmpl = `
    <div class="view">
      <div class="karte-wrap">
        <div class="karte-kopf">
          <div class="karte-titel">
            <span class="kl">Kennzahl</span>
            <select id="kennzahl"></select>
          </div>
          <div class="legende" id="legende"></div>
        </div>
        <div class="karte-grid">
          <div>__KARTE__</div>
          <aside class="karte-rechts">
            <h3 id="rank-titel">Höchste und niedrigste Werte</h3>
        <p class="rank-unter" id="rank-unter"></p>
            <div id="ranking"></div>
          </aside>
        </div>
      </div>
      <div class="hinweis">
        <strong>Was die Karte zeigt:</strong> Die Kriminalitätsbelastung ist in den Stadtstaaten
        am höchsten, die Aufklärungsquote dort am niedrigsten. Das Unsicherheitsgefühl folgt
        diesem Muster <em>nicht</em> — vergleichen Sie die Einfärbung der drei Kennzahlen.
      </div>
      <div class="karten">__START__</div>
    </div>`;
  const sel = Object.entries(KENNZAHLEN)
    .map(([k, v]) => '<option value="' + k + '">' + v.label + '</option>').join('');
  document.getElementById('inhalt').innerHTML =
    tmpl.replace('__KARTE__', KARTE_SVG).replace('__START__',
      '');
  document.getElementById('kennzahl').innerHTML = sel;
  document.getElementById('kennzahl').addEventListener('change', e => karteFaerben(e.target.value));
  karteFaerben('hz');
  beobachte();
}

/* ---------- Ansicht: Themen ---------- */
const THEMEN = {
  inhalt:          {ids:[], text:null},
  kriminalitaet:   {ids:['hz','aq','zeitreihe','eu','pmk'], text:'kriminalitaet'},
  furcht:          {ids:['alter_furcht','furcht','furcht_zr','delikte','skid_delikte','skid_orte'], text:'furcht'},
  justiz:          {ids:['trichter'], text:'justiz'},
  methodik:        {ids:[], text:null},
};
function ansichtThema(t){
  const cfg = THEMEN[t];
  let html = '<div class="view">';

  if (t === 'inhalt'){
    html += `<section class="card">
      <h3>Warum diese Seite</h3>
      <p class="unter">Der Anlass und die drei Fragen, um die es geht.</p>
      <div class="einordnung">
        <p>In Gesprächen höre ich immer wieder, die Kriminalität nehme zu. Das wollte ich
        nicht einfach glauben und auch nicht einfach bestreiten — ich wollte nachsehen, was
        die Zahlen dazu sagen. Daraus ist diese Auswertung entstanden.</p>
        <p>Drei Fragen stehen am Anfang:</p>
        <h4 class="schritt">1. Steigt die Kriminalität in Deutschland?</h4>
        <p><strong>Langfristig nein, kurzfristig ja — und beides wird oft verwechselt.</strong>
        1993 wurden <strong>6,75 Millionen</strong> Straftaten registriert, im Jahr 2025 sind es
        <strong>5,51 Millionen</strong>: ein Rückgang um <strong>18 Prozent</strong>. Umgerechnet
        auf die Einwohnerzahl — damit man die Jahre überhaupt vergleichen kann — fiel die Zahl
        von 8.337 auf 6.591 je 100.000 Einwohner, also um <strong>21 Prozent</strong>. Seit dem
        Tiefststand 2021 (5,05 Millionen) ist die Zahl allerdings wieder gestiegen, 2025 aber
        erneut gesunken (5,6 Prozent weniger als 2024). Der langjährige Trend zeigt nach unten.
        Die Wahrnehmung „es wird immer mehr" trifft diese Entwicklung nicht.</p>
        <h4 class="schritt">2. Steigt die Angst vor Kriminalität?</h4>
        <p><strong>Ja, und zwar unabhängig von der Kriminalität.</strong> Der Anteil der
        Menschen, die sich nachts unsicher fühlen, lag 2014 bei <strong>22 Prozent</strong>,
        stieg bis 2016 auf <strong>27 Prozent</strong> und liegt 2023 bei
        <strong>25 Prozent</strong>. Dieser Anstieg fiel in eine Zeit, in der die registrierte
        Kriminalität weiter zurückging. Angst und Kriminalität verlaufen also nicht im
        Gleichschritt — das ist der eigentliche Befund dieser Arbeit.</p>
        <h4 class="schritt">3. Wodurch wird die Angst beeinflusst?</h4>
        <p><strong>Noch offen.</strong> Diese Frage lässt sich mit den hier versammelten Daten
        nicht abschließen beantworten — vermutlich überhaupt nicht, weil Angst von vielen
        Dingen abhängt, die keine Statistik erfasst. Ein erster Hinweis: Frauen fürchten sich
        deutlich häufiger als Männer, ohne häufiger betroffen zu sein. Wie diese Frage genauer
        zu beantworten wäre, ist noch in Arbeit.</p>
      </div>
      <div class="hinweis"><strong>Zum Stand dieser Arbeit.</strong> Die Seite ist in früher
      Entwicklung. Zahlen und Darstellungen können sich noch ändern, und nicht jede Auswertung
      ist fertig. Wo etwas unsicher ist, steht es dabeit — Quellen, Fallzahlen und die Grenzen
      der Aussage finden sich unter „Daten &amp; Methoden".</div>
      <div class="note"><h4>Und die Gegenrichtung</h4><p>Die Frage lässt sich auch umdrehen:
      Wenn die Kriminalität langfristig sinkt und die Angst trotzdem steigt, sagt das weniger
      über die Kriminalität als über die Art, wie wir über sie sprechen. Genau dort setzt der
      zweite Teil der Auswertung an.</p></div>
      <p class="quelle">Zahlen: BKA, Polizeiliche Kriminalstatistik (registrierte Fälle
      insgesamt, ab 1987) und European Social Survey (Anteil der Befragten, die sich nachts
      unsicher fühlen; Deutschland, Erhebung 2014/2016/2023).</p>
    </section>`;
  }

  if (cfg.text){
    const [h, p] = DATEN.texte_start[cfg.text];
    html += '<section class="card"><h3>' + h + '</h3><p class="unter">' + p + '</p></section>';
  }
  if (t === 'zusammenhaenge' && DATEN.modellguete && DATEN.modellguete.length){
    const g = DATEN.modellguete;
    html += '<section class="card"><h3>Wie viel erklären die Modelle?</h3>'
      + '<p class="unter">Güte der schrittweise erweiterten Modelle. Pseudo-R² (McFadden) '
      + 'und AUC zeigen, wie gut die Merkmale das Unsicherheitsgefühl vorhersagen.</p>'
      + '<div style="overflow-x:auto"><table class="tabelle"><thead><tr>'
      + '<th>Modell</th><th class="num">Fälle</th><th class="num">Pseudo-R²</th>'
      + '<th class="num">AUC</th></tr></thead><tbody>'
      + g.map(r => '<tr><td>' + r.modell + '</td><td class="num">' + nf(r.n)
          + '</td><td class="num">' + nf(r.pseudo_r2_mcfadden, 4)
          + '</td><td class="num">' + nf(r.auc, 4) + '</td></tr>').join('')
      + '</tbody></table></div>'
      + '<div class="note"><h4>Was das bedeutet</h4><p>Die Modelle erreichen eine AUC von '
      + 'rund 0,74 bis 0,79 — sie trennen unsichere von sicheren Personen also deutlich '
      + 'besser als der Zufall (0,5), aber längst nicht fehlerfrei. Ein Pseudo-R² von rund '
      + '0,18 heißt: Der größere Teil der Unterschiede in der Furcht bleibt durch die hier '
      + 'erhobenen Merkmale <em>unerklärt</em>. Wer behauptet, die Ursachen der Furcht zu '
      + 'kennen, müsste mehr erklären können als das.</p></div>'
      + '<p class="quelle">Quelle: eigene Schätzung (logistische Regression, '
      + 'Standardfehler geclustert nach Bundesland)</p></section>';
  }
  html += '<div class="karten">' + kartenblock(cfg.ids, cfg.einordnungen) + '</div>';
  if (t === 'methodik'){
    html += `<section class="card"><h3>Daten und Methoden</h3>
      <p class="unter">Was in dieser App steckt und wie belastbar es ist.</p>
      <h4 style="margin:14px 0 2px;font-size:.9rem;color:var(--ink)">Deutschland insgesamt</h4>
      <p class="unter" style="margin-bottom:12px">Zum Vergleich mit den Bundesländern.</p>
      <div class="kk" id="bund-kk"></div>
      <details open><summary>Quellen</summary><ul>
        <li><strong>Kriminalität:</strong> BKA, Polizeiliche Kriminalstatistik 2025,
        Länder-Grundtabelle (Fälle, Häufigkeitszahl auf Basis Zensus 2022, Aufklärungsquote);
        T01-Zeitreihe ab 1987; T12 (aufgeklärte Fälle).</li>
        <li><strong>Strafverfolgung:</strong> Destatis, Statistischer Bericht Strafverfolgung 2024
        (Tabelle 24311-05, Verurteilte nach Art der Straftat).</li>
        <li><strong>Bevölkerung:</strong> Destatis/Statistikportal, Bevölkerungsstand 2025 und
        Bevölkerungsdichte; Nationalität auf Basis Zensus 2022; Migrationshintergrund
        nach Mikrozensus.</li>
        <li><strong>Karte — wichtig zur Farblesung:</strong> Die sechs Farbstufen werden
        nach <em>Rang</em> vergeben, nicht nach gleichen Wertabständen. Jede Stufe enthält
        also etwa gleich viele Bundesländer. Vorteil: Auch bei schiefer Verteilung bleiben
        alle Stufen unterscheidbar. Nachteil, der dazugehört: Gleiche Farbunterschiede
        bedeuten dann <em>nicht</em> gleiche Zahlenunterschiede. Nordrhein-Westfalen (7.524)
        und Sachsen-Anhalt (8.090) liegen 566 auseinander und erhalten verschiedene Farben;
        Bremen und Berlin trennen 249 und sie erhalten ebenfalls verschiedene Farben. Für
        genaue Werte die Rangliste, das Länderprofil oder die Beschriftung nutzen — die
        Farbe dient dem Überblick, nicht dem Zahlenvergleich.</li>
        <li><strong>Wirtschaft:</strong> Arbeitskreis Volkswirtschaftliche Gesamtrechnungen der
        Länder, BIP und verfügbares Einkommen je Einwohner 2024.</li>
        <li><strong>Arbeitsmarkt:</strong> Statistik der Bundesagentur für Arbeit,
        Arbeitslosenquote 2025 (Jahresdurchschnitt, bezogen auf alle zivilen Erwerbspersonen);
        Werte über das Datenblatt von sozialpolitik-aktuell.de, Stand 30.03.2026.
        Kontrolle: Der Bundeswert 6,3 % deckt sich mit der Langzeitreihe des Statistischen
        Bundesamtes (lrarb002ga).</li>
        <li><strong>Furcht:</strong> European Social Survey, Runden 1–11 (Deutschland fehlt in
        Runde 10); eigene Berechnung, Gewichtung pspwght. Länderwerte aus den Runden 5–11 gepoolt.
        Deliktprofile aus SKiD 2024/2020 (BKA).</li>
        <li><strong>Internationaler Vergleich:</strong> Eurostat crim_off_cat (harmonisierte
        ICCS-Kategorien); Kartengeometrie von GISCO/Eurostat (CC BY 4.0).</li>
      </ul></details>
      <details><summary>Grenzen und Fallstricke</summary><ul>
        <li>Registrierte Fälle sind polizeilich bekannt gewordene Vorgänge — kein Nachweis einer
        Straftat und keine Verurteilung.</li>
        <li>Die Häufigkeitszahl bezieht Fälle auf die Wohnbevölkerung. In Stadtstaaten und
        Ballungsräumen erhöhen Pendler, Touristen und Eine-Tat-mehrere-Fälle die Zahl, ohne dass
        die Wohnbevölkerung sie „verursacht“.</li>
        <li>Länderwerte zur Furcht beruhen auf kleinen Stichproben (n = 121 bis 3.332). Wo die
        Fallzahl zu klein ist, ist der Balken grau dargestellt; die Fehlerbalken sind
        Näherungen ohne Designeffekt.</li>
        <li>Die Zeitreihen der Furcht sind Momentaufnahmen unabhängiger Stichproben, kein Panel —
        kausale Aussagen sind damit nicht möglich.</li>
        <li>Verurteilungen sind Personen (nicht Fälle), gezählt nach dem schwersten Delikt des
        Verfahrens und mit Zeitverzug zum Tatjahr.</li>
      </ul></details></section>`;
  }
  html += '</div>';
  document.getElementById('inhalt').innerHTML = html;
  /* Rahmendaten Deutschlands stehen im Methodik-Reiter, nicht im Kopf —
     der Container entsteht erst beim Öffnen dieses Reiters. */
  const bk = document.getElementById('bund-kk');
  if (bk){
    bk.innerHTML = [
      ['Einwohner', nf(B.einwohner)],
      ['Straftaten', nf(B.faelle)],
      ['je 100.000 Einwohner', nf(B.hz, 0)],
      ['Aufklärungsquote', pct(B.aq, 1)],
      ['Unsicherheitsgefühl', pct(B.furcht_schnitt, 1)],
    ].map(k => '<div><b>' + k[1] + '</b><span>' + k[0] + '</span></div>').join('');
  }
  beobachte();
}

/* ---------- Ansicht: Bundesland ---------- */
function ansichtLand(nuts){
  const l = LN[nuts] || L[nuts];
  if (!l) return;
  document.body.classList.add('land-ansicht');
  const k = l.kriminalitaet || {};
  const ges = k['Straftaten insgesamt'] || {};
  const f = l.furcht || {};
  const delikte = ['Straftaten insgesamt','Diebstahl (gesamt)','Wohnungseinbruchdiebstahl',
                   'Raub','Gefährliche Körperverletzung','Straftaten gegen die sexuelle Selbstbestimmung',
                   'Vermögens- und Fälschungsdelikte','Sachbeschädigung']
    .filter(d => k[d]);
  const rows = delikte.map(d => {
    const x = k[d];
    const bund = (d === 'Straftaten insgesamt') ? B.hz : null;
    return '<tr><td>' + d + '</td><td class="num">' + nf(x.faelle) + '</td><td class="num">'
      + nf(x.hz, 0) + '</td><td class="num">' + pct(x.aq, 1) + '</td></tr>';
  }).join('');

  const furchtVergleich = (f.unsicher !== null && f.unsicher !== undefined)
    ? (f.unsicher - (B.furcht_schnitt || 0)) : null;

  document.getElementById('inhalt').innerHTML = `
  <div class="view">
    <button class="zurueck" id="zurueck">← Zurück zur Deutschlandkarte</button>
    <div class="lkopf">
      <h2>${DATEN.wappen[l.nuts] || ''}${l.name}</h2>
      <p>${nf(l.bevoelkerung)} Einwohner</p>
      ${kacheln([
        ['Straftaten 2025', nf(ges.faelle)],
        ['je 100.000 Einwohner', nf(ges.hz, 0)],
        ['Aufklärungsquote', pct(ges.aq, 1)],
        ['Unsicherheitsgefühl', pct(f.unsicher, 1)],
        ['BIP je Einwohner', nf(l.bip_je_ew) + ' €'],
      ])}
    </div>

    ${(f.unsicher !== null && f.unsicher !== undefined) ? `
    <div class="hinweis">
      <strong>Sicherheitsgefühl.</strong> In ${l.name} fühlen sich nachts
      <strong>${pct(f.unsicher, 1)}</strong> unsicher
      (95-%-Intervall ${pct(f.ki_lo, 1)} bis ${pct(f.ki_hi, 1)}, n = ${nf(f.n)}).
      ${f.belastbar ? '' : '<em>Die Fallzahl ist klein — der Wert ist nur eingeschränkt belastbar.</em>'}
      ${furchtVergleich !== null ? ` Der Wert liegt ${furchtVergleich >= 0 ? 'über' : 'unter'} dem
      Bundesmittel der Länder (${pct(B.furcht_schnitt, 1)}).` : ''}
    </div>` : ''}

    <div class="karten">
      <section class="card">
        <h3>Kriminalität in ${l.name}</h3>
        <p class="unter">Fälle, Häufigkeitszahl (je 100.000 Einwohner) und Aufklärungsquote 2025.</p>
        <div style="overflow-x:auto">
        <table class="tabelle">
          <thead><tr><th>Delikt</th><th class="num">Fälle</th><th class="num">je 100.000 Einwohner</th><th class="num">aufgeklärt</th></tr></thead>
          <tbody>${rows}</tbody>
        </table></div>
        <p class="quelle">Quelle: BKA, PKS 2025, Länder-Grundtabelle</p>
      </section>

      <section class="card">
        <h3>Struktur des Landes</h3>
        <p class="unter">Demografie und Wirtschaftskraft im Bundesvergleich. Die
        wirtschaftlichen Kennzahlen lassen sich auch als Kartenfarbe wählen.</p>
        ${kacheln([
          ['Fläche', nf(l.flaeche) + ' km²'],
          ['Bevölkerungsdichte', nf(l.dichte, 1) + ' Einw./km²'],
          ['Arbeitslosenquote (2025)', pct(l.alq, 1)],
          ['mit Migrationshintergrund', pct(l.mh_anteil, 1)],
          ['Ausländeranteil (Zensus 2022)', pct(l.auslaenderanteil, 1)],
          ['Verfügbares Einkommen (2024)', nf(l.verfuegbares_einkommen) + ' €'],
          ['Personen mit Migrationshintergrund', nf(l.mit_mh)],
        ])}
        <p class="quelle">Quellen: Destatis/Statistikportal (Bevölkerung, Nationalität);
        VGR der Länder (Wirtschaft)</p>
      </section>

      <section class="card">
        <h3>Einordnung</h3>
        <p class="unter">Was diese Zahlen für ${l.name} bedeuten — und was nicht.</p>
        <div class="einordnung" id="eo"></div>
      </section>
    </div>
  </div>`;

  document.getElementById('zurueck').addEventListener('click', () => {
    document.querySelector('.tab[data-ansicht="karte"]').click();
  });
  document.getElementById('eo').textContent = einordnung(l);
  window.scrollTo({top: 0, behavior: 'smooth'});
}

function einordnung(l){
  const k = l.kriminalitaet || {};
  const ges = k['Straftaten insgesamt'] || {};
  const f = l.furcht || {};
  const teile = [];
  if (ges.hz){
    const rel = ges.hz / B.hz;
    teile.push('Die Kriminalitätsbelastung liegt ' + (rel > 1.05 ? 'über' : rel < 0.95 ? 'unter' : 'etwa auf') +
      ' dem Durchschnitt der Länder (' + nf(ges.hz, 0) + ' gegenüber ' + nf(B.hz, 0) +
      ' Fällen je 100.000 Einwohner).');
  }
  if (ges.aq){
    teile.push('Die Aufklärungsquote beträgt ' + pct(ges.aq, 1) + ' (Bundesdurchschnitt ' + pct(B.aq, 1) + ').');
  }
  if (f.unsicher !== null && f.unsicher !== undefined){
    const d = f.unsicher - (B.furcht_schnitt || 0);
    teile.push('Das Unsicherheitsgefühl ist mit ' + pct(f.unsicher, 1) + ' ' +
      (Math.abs(d) < 1.5 ? 'nahe am' : d > 0 ? 'über dem' : 'unter dem') +
      ' Länderdurchschnitt (' + pct(B.furcht_schnitt, 1) + '). ' +
      (f.belastbar ? '' : 'Wegen der kleinen Stichprobe ist dieser Wert mit Vorsicht zu lesen. '));
  }
  if (ges.hz && f.unsicher !== null && f.unsicher !== undefined){
    const hochBelastet = ges.hz > B.hz, hochFurcht = f.unsicher > (B.furcht_schnitt || 0);
    teile.push(hochBelastet && !hochFurcht
      ? 'Bemerkenswert: vergleichsweise hohe registrierte Kriminalität bei unterdurchschnittlicher Furcht.'
      : !hochBelastet && hochFurcht
      ? 'Bemerkenswert: vergleichsweise niedrige registrierte Kriminalität bei überdurchschnittlicher Furcht — genau das Muster, das die Forschung als Entkopplung von Hellfeld und Wahrnehmung beschreibt.'
      : 'Belastung und Furcht zeigen hier in dieselbe Richtung.');
  }
  if (l.dichte !== null && l.dichte !== undefined){
    teile.push('Die Bevölkerungsdichte liegt bei ' + nf(l.dichte, 0) + ' Einwohnern je Quadratkilometer.');
  }
  if (l.alq !== null && l.alq !== undefined){
    teile.push('Die Arbeitslosenquote liegt bei ' + pct(l.alq, 1) + ' (Bundesdurchschnitt 6,3 %).');
  }
  if (l.mh_anteil !== null && l.mh_anteil !== undefined){
    teile.push(pct(l.mh_anteil, 1) + ' der Bevölkerung haben einen Migrationshintergrund ' +
      '(Ausländeranteil ' + pct(l.auslaenderanteil, 1) + '). Migrationshintergrund und ' +
      'Staatsangehörigkeit sind verschiedene Merkmale: zu den Menschen mit Migrationshintergrund ' +
      'zählen auch Deutsche, etwa Eingebürgerte und Spätaussiedler.');
  }
  teile.push('Die Häufigkeitszahl bezieht Fälle auf die Wohnbevölkerung; in Städten mit vielen ' +
    'Pendlern und Gästen fällt sie dadurch höher aus, ohne dass die Wohnbevölkerung die Fälle verursacht.');
  return teile.join(' ');
}

/* ---------- Navigation ---------- */
let AKTIV = 'karte';
function zeige(ansicht, param){
  AKTIV = ansicht;
  try{
    const h = (ansicht === 'land' && param) ? ('#land=' + param)
            : (ansicht !== 'karte' ? ('#' + ansicht) : '');
    if (location.hash !== h) history.replaceState(null, '', h || location.pathname);
  }catch(e){}
  document.querySelectorAll('.tab').forEach(t =>
    t.classList.toggle('active', t.dataset.ansicht === ansicht));
  if (ansicht !== 'land') document.body.classList.remove('land-ansicht');
  if (ansicht === 'karte') ansichtKarte();
  else if (ansicht === 'land') ansichtLand(param);
  else ansichtThema(ansicht);
  if (ansicht === 'land') document.querySelector('.tab[data-ansicht="karte"]').classList.add('active');
}

document.addEventListener('click', e => {
  const p = e.target.closest('.bl');
  if (p){ zeige('land', p.dataset.nuts); return; }
  const r = e.target.closest('.rank-zeile');
  if (r){ zeige('land', r.dataset.nuts); }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.target.classList && e.target.classList.contains('bl')){
    zeige('land', e.target.dataset.nuts);
  }
});
document.getElementById('tabs').addEventListener('click', e => {
  const b = e.target.closest('.tab');
  if (b) zeige(b.dataset.ansicht);
});

/* ---------- Start ---------- */
let KARTE_SVG = '';
(function initKarte(){
  const el = document.getElementById('karte-svg');
  KARTE_SVG = el.innerHTML;
  el.remove();
})();
(function start(){
  const werte = Object.values(L).map(l => l.furcht.unsicher).filter(v => v !== null && v !== undefined);
  B.furcht_schnitt = werte.reduce((a, b) => a + b, 0) / werte.length;

  /* Deep-Link aus der Adresse lesen (#land=DE1 bzw. #furcht) */
  const h = (location.hash || '').replace('#', '');
  if (h.startsWith('land=')){
    const nuts = h.slice(5);
    if (LN[nuts]) { zeige('land', nuts); return; }
  }
  if (h && THEMEN[h]) { zeige(h); return; }
  zeige('karte');
})();
window.addEventListener('hashchange', () => {
  const h = (location.hash || '').replace('#', '');
  if (h.startsWith('land=') && LN[h.slice(5)]) zeige('land', h.slice(5));
  else if (THEMEN[h]) zeige(h);
  else zeige('karte');
});
</script>
"""


if __name__ == "__main__":
    laender, basis = main()
    print(f"Länder: {len(laender)} | Bundesdurchschnitt HZ {basis['hz']} | AQ {basis['aq']} %")
