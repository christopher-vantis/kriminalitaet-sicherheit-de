#!/usr/bin/env python3
"""
build_app.py — Kriminalität und Sicherheit in Deutschland (Bundesland-App)
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
                     "Median der Vergleichsländer (rund 40 Staaten). Achtung: Jedes Feld hat "
                     "eine <em>eigene</em> Werteskala — die Höhe der Linien ist nur innerhalb "
                     "eines Feldes vergleichbar, nicht zwischen den Feldern. Der senkrechte "
                     "Abstand zwischen beiden Linien zeigt, ob Deutschland über oder unter "
                     "dem europäischen Mittelfeld liegt. Bei Körperverletzung und Diebstahl "
                     "liegt Deutschland um ein Mehrfaches darüber, bei Wohnungseinbruch "
                     "nahezu auf Augenhöhe. Die Reihe beginnt 2009: Für 2008 weist "
                     "Eurostat bei Körperverletzung und Diebstahl ein Mehrfaches des "
                     "Folgejahres aus — das ist ein Bruch in der Datenreihe, kein "
                     "tatsächlicher Rückgang. Die Polizeiliche Kriminalstatistik zeigt für "
                     "dieselben Jahre nur wenige Prozent Unterschied.",
                     f, "Eurostat crim_off_cat, Datenstand 08/2025"))
    return figs




# ---------------------------------------------------------------- Zusammenhänge
def diagramm_pmk():
    """Politisch motivierte Kriminalität: Gesamtaufkommen und Gewalttaten.

    Zwei Felder nebeneinander, weil der Unterschied die eigentliche Aussage ist:
    Das Gesamtaufkommen hat sich seit 2016 mehr als verdoppelt, die Zahl der
    Gewalttaten blieb im selben Zeitraum praktisch unverändert.

    Returns:
        plotly.graph_objects.Figure: Figur mit zwei Feldern.
    """
    pfad = OUT / "pmk_zeitreihe.csv"
    if not pfad.exists():
        return None
    daten = lies(pfad, delim=";")
    namen = {
        "rechts": "rechts",
        "links": "links",
        "sonstige_zuordnung": "sonstige Zuordnung",
        "auslaendische_ideologie": "ausländische Ideologie",
        "religioese_ideologie": "religiöse Ideologie",
    }
    farben = {
        "rechts": "#0b4f49",
        "links": "#3d9a92",
        "sonstige_zuordnung": "#9fd3ce",
        "auslaendische_ideologie": "#c9a86a",
        "religioese_ideologie": "#e0cdab",
    }

    f = make_subplots(
        rows=1, cols=2, horizontal_spacing=0.1,
        subplot_titles=("Alle politisch motivierten Straftaten",
                        "Davon Gewalttaten"),
    )
    for spalte, art in ((1, "gesamt"), (2, "gewalt")):
        for feld in ("rechts", "links", "sonstige_zuordnung",
                     "auslaendische_ideologie", "religioese_ideologie"):
            klein = feld in ("auslaendische_ideologie", "religioese_ideologie")
            reihe = sorted(
                (int(float(r["jahr"])), z(r["faelle"]))
                for r in daten
                if r["art"] == art and r["bereich"] == feld and r["faelle"])
            if not reihe:
                continue
            f.add_trace(go.Scatter(
                x=[j for j, _ in reihe], y=[w for _, w in reihe],
                mode="lines+markers", name=namen[feld],
                line=dict(color=farben[feld], width=1.8 if klein else 2.6,
                          dash="dot" if klein else "solid"),
                marker=dict(size=4 if klein else 5.5, color=farben[feld]),
                legendgroup=feld, showlegend=(spalte == 1),
                hovertemplate="%{y:,.0f} Fälle im Jahr %{x}<extra>"
                              + namen[feld] + "</extra>",
            ), row=1, col=spalte)

    # Beide Felder haben eine eigene Skala (links bis rund 86.000, rechts bis
    # rund 4.200 Fälle). Das steht im Untertitel, damit die Höhen nicht
    # fälschlich miteinander verglichen werden.
    f.update_yaxes(rangemode="tozero", automargin=True, title="", row=1, col=1)
    f.update_yaxes(rangemode="tozero", automargin=True, title="", row=1, col=2)
    f.update_xaxes(automargin=True, dtick=2)
    # Grundlayout übernehmen und die abweichenden Werte einzeln ersetzen —
    # sonst kollidieren Schlüssel wie "margin" aus BASE mit den eigenen.
    layout = dict(BASE)
    layout.update(
        height=420,
        margin=dict(l=10, r=20, t=64, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.15, x=0,
                    xanchor="left", font=dict(size=12)),
        hovermode="x unified",
    )
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
    for fid, titel, unter, f, quelle in figs:
        fig_json[fid] = json.loads(pio.to_json(f))
        fig_meta.append({"id": fid, "titel": titel, "unter": unter, "quelle": quelle})

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
<title>Kriminalität und Sicherheit in Deutschland — Bundesländer</title>
<!--PLOTLY-->
<style>{schrift_css()}</style>
<style>{css}</style>
</head>
<body>
<div id="app">
  <header class="kopf">
    <div class="kopf-inner">
      <div class="kopf-titel">
        <h1>Kriminalität und Sicherheit in Deutschland</h1>
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
.kopf{background:#12100e;color:#fff;padding:20px 0 18px;
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
.chart{min-height:200px}
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
const KONF = {responsive:true, displayModeBar:false, displaylogo:false, scrollZoom:false};

/* ---------- Hilfsfunktionen ---------- */
const nf = (v, d = 0) => (v === null || v === undefined || isNaN(v)) ? '—'
  : v.toLocaleString('de-DE', {minimumFractionDigits:d, maximumFractionDigits:d});
const pct = (v, d = 1) => (v === null || v === undefined) ? '—' : nf(v, d) + ' %';

/* ---------- Karte einfärben ---------- */
const KENNZAHLEN = {
  hz:      {label:'Kriminalitätsbelastung', kurz:'Belastung', einheit:0,
            wert:l => ((l.kriminalitaet['Straftaten insgesamt']||{}).hz)},
  furcht:  {label:'Unsicherheitsgefühl', kurz:'Furcht', einheit:1,
            wert:l => l.furcht.unsicher},
  aq:      {label:'Aufklärungsquote', kurz:'Aufklärung', einheit:1,
            wert:l => ((l.kriminalitaet['Straftaten insgesamt']||{}).aq)},
  bip:     {label:'BIP je Einwohner', kurz:'Wirtschaftskraft', einheit:0,
            wert:l => l.bip_je_ew},
  alq:     {label:'Arbeitslosenquote', kurz:'Arbeitslosigkeit', einheit:1,
            wert:l => l.alq},
  mh:      {label:'Migrationshintergrund', kurz:'Migrationsanteil',
            einheit:1, wert:l => l.mh_anteil},
  ausland: {label:'Ausländeranteil', kurz:'Ausländeranteil', einheit:1,
            wert:l => l.auslaenderanteil},
  dichte:  {label:'Bevölkerungsdichte', kurz:'Dichte', einheit:0,
            wert:l => l.dichte},
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
      + '<span style="margin-left:6px">(' + k.kurz + ', Stufen nach Rang)</span>';
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
function zeichne(el){
  if (el.dataset.state) return;
  el.dataset.state = 'laeuft';
  const id = el.dataset.fig;
  const f = FIGS[id];
  if (!f){ return; }
  const lay = Object.assign({}, f.layout || {});
  lay.autosize = true;
  if (window.innerWidth < 560 && lay.height) lay.height = Math.min(lay.height, 330);
  Plotly.newPlot(el, f.data, lay, KONF).then(() => el.dataset.state = 'fertig')
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
      + eo + '<p class="quelle">Quelle: ' + m.quelle + '</p></section>';
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
  furcht:          {ids:['furcht','furcht_zr','delikte'], text:'furcht'},
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
