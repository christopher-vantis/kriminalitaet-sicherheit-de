#!/usr/bin/env python3
"""
build_ch.py — Kriminalität und Sicherheit in der Schweiz
========================================================
Baut die Schweizer Fassung der App als einzelne HTML-Datei: klickbare
Kantonskarte, Bundes-Zeitreihen, Furcht, Strafverfolgung, Methoden — und für
jeden Kanton ein Profil.

Aufbau und Gestaltung folgen der Deutschland-App (`build_app.py`): dieselbe
Farb- und Typografiesprache, dieselben Bausteine. Das CSS und die eingebettete
Schrift werden von dort übernommen, damit beide Seiten identisch aussehen.

Datenstand: September 2026. Quellen: BFS STAT-TAB (PKS, Wohnbevölkerung),
Eurostat crim_off_cat, ESS Runden 1–11 (eigene Auswertung), Swiss Crime
Survey 2022 und Schweizerische Sicherheitsbefragung 2015 (veröffentlichte
Werte).

Ausgabe: dashboard/schweiz.html

Aufruf: python3 build_ch.py
"""
import csv
import json
import pathlib

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from plotly.offline import get_plotlyjs

import build_app as DE          # CSS, Schrift, gemeinsames Layout

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard" / "data"
OUT = ROOT / "output"

UNTER, UEBER, NEUTRAL = DE.UNTER, DE.UEBER, DE.NEUTRAL
TEAL_H1, TEAL_H2, TEAL_H3 = DE.TEAL_H1, DE.TEAL_H2, DE.TEAL_H3
INK, SLATE, GRID = DE.INK, DE.SLATE, DE.GRID
MUTED = "#6b645e"

# Kantonskürzel, wie sie auf Schweizer Karten üblich sind.
KUERZEL = {
    "Zürich": "ZH", "Bern": "BE", "Luzern": "LU", "Uri": "UR", "Schwyz": "SZ",
    "Obwalden": "OW", "Nidwalden": "NW", "Glarus": "GL", "Zug": "ZG",
    "Freiburg": "FR", "Solothurn": "SO", "Basel-Stadt": "BS",
    "Basel-Landschaft": "BL", "Schaffhausen": "SH",
    "Appenzell Ausserrhoden": "AR", "Appenzell Innerrhoden": "AI",
    "St. Gallen": "SG", "Graubünden": "GR", "Aargau": "AG", "Thurgau": "TG",
    "Tessin": "TI", "Waadt": "VD", "Wallis": "VS", "Neuenburg": "NE",
    "Genf": "GE", "Jura": "JU",
}

# Grossregion (NUTS-2) je Kanton — Grundlage der regionalen Furchtwerte.
REGION_JE_KANTON = {
    "Zürich": "Zürich",
    "Bern": "Espace Mittelland", "Freiburg": "Espace Mittelland",
    "Solothurn": "Espace Mittelland", "Neuenburg": "Espace Mittelland",
    "Jura": "Espace Mittelland",
    "Basel-Stadt": "Nordwestschweiz", "Basel-Landschaft": "Nordwestschweiz",
    "Aargau": "Nordwestschweiz",
    "Luzern": "Zentralschweiz", "Uri": "Zentralschweiz", "Schwyz": "Zentralschweiz",
    "Obwalden": "Zentralschweiz", "Nidwalden": "Zentralschweiz", "Zug": "Zentralschweiz",
    "Glarus": "Ostschweiz", "Schaffhausen": "Ostschweiz",
    "Appenzell Ausserrhoden": "Ostschweiz", "Appenzell Innerrhoden": "Ostschweiz",
    "St. Gallen": "Ostschweiz", "Graubünden": "Ostschweiz", "Thurgau": "Ostschweiz",
    "Genf": "Genferseeregion", "Waadt": "Genferseeregion", "Wallis": "Genferseeregion",
    "Tessin": "Tessin",
}

# Delikte im Kantonsprofil: Anzeigename -> Spaltenpräfix der Kennzahlen.
PROFIL_DELIKTE = [
    ("Straftaten nach StGB insgesamt", "stgb"),
    ("Diebstahl (Art. 139)", "diebstahl"),
    ("Einbruchdiebstahl (Art. 139)", "einbruch"),
    ("Raub (Art. 140)", "raub"),
    ("Sachbeschädigung (Art. 144)", "sachbeschaedigung"),
    ("Betrug und betrügerischer Missbrauch einer Datenanlage", "cyberbetrug"),
    ("Straftaten gegen Leib und Leben (1. Titel)", "leib_leben"),
    ("Vergewaltigung (Art. 190)", "vergewaltigung"),
]


def lies(pfad, delim=";"):
    """Liest eine CSV mit Kopfzeile.

    Args:
        pfad: Dateipfad.
        delim: Trennzeichen.

    Returns:
        list[dict]: Zeilen als Dictionaries.
    """
    with open(pfad, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=delim))


def z(x):
    """Wandelt einen Wert in float oder None."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- Daten
def lade_daten():
    """Lädt Kantonskennzahlen, Zeitreihe, Furcht- und Eurostat-Auswertungen.

    Returns:
        tuple: (kantone, viewbox, zeitreihe, fig_daten)
    """
    kz = lies(OUT / "ch_kantone_kennzahlen.csv")
    geo = json.loads((OUT / "ch_kantone_svg.json").read_text(encoding="utf-8"))
    zr = lies(OUT / "ch_zeitreihe.csv")
    ess = lies(D / "ch_ess_aggregate.csv")
    ref = lies(OUT / "ch_wahrnehmung_referenzwerte.csv")
    eu = lies(OUT / "ch_eurostat_vergleich.csv")

    jahr = max(int(r["jahr"]) for r in kz)
    kantone = {}
    for r in kz:
        if int(r["jahr"]) != jahr:
            continue
        name = r["kanton"]
        eintrag = {
            "name": name,
            "kuerzel": KUERZEL[name],
            "region": REGION_JE_KANTON[name],
            "jahr": jahr,
            "bevoelkerung": z(r["bevoelkerung"]),
            "flaeche": z(r["flaeche_km2"]),
            "dichte": z(r["dichte"]),
            "auslaenderanteil": z(r["auslaenderanteil"]),
            "faelle_stgb": z(r["faelle_stgb"]),
            "hz": z(r["hz"]),
            "aq": z(r["aq"]),
            "aufgeklaert": z(r["aufgeklaert"]),
            "delikte": {},
        }
        for anzeige, praefix in PROFIL_DELIKTE:
            f = z(r.get(f"faelle_{praefix}"))
            h = z(r.get(f"hz_{praefix}"))
            a = z(r.get(f"aufgeklaert_{praefix}"))
            if f is None and h is None:
                continue
            eintrag["delikte"][anzeige] = {
                "faelle": f, "hz": h,
                "aq": None if (a is None or not f) else round(100 * a / f, 1)}
        kantone[name] = eintrag

    # Furchtwerte je Grossregion an die Kantone hängen. Der Wert gilt für die
    # Grossregion, nicht für den einzelnen Kanton — die App weist das aus.
    reg_f = {r["gruppe"]: r for r in ess
             if r["ebene"] == "grossregion" and r["kennzahl"] == "unsicher"}
    reg_v = {r["gruppe"]: r for r in ess
             if r["ebene"] == "grossregion" and r["kennzahl"] == "viktim"}
    for eintrag in kantone.values():
        rf, rv = reg_f.get(eintrag["region"]), reg_v.get(eintrag["region"])
        eintrag["furcht"] = {
            "unsicher": z(rf["anteil"]) if rf else None,
            "ki_lo": z(rf["ki_lo"]) if rf else None,
            "ki_hi": z(rf["ki_hi"]) if rf else None,
            "n": int(rf["n"]) if rf else None,
            "viktim": z(rv["anteil"]) if rv else None,
            "region": eintrag["region"],
        }

    for code, v in geo.items():
        if code == "_viewbox":
            continue
        if v["name"] in kantone:
            kantone[v["name"]]["nuts"] = code

    return kantone, geo["_viewbox"], zr, {"ess": ess, "ref": ref, "eu": eu}


def basis_zahlen(kantone, zr):
    """Rahmendaten der Schweiz für Kopf, Methoden-Reiter und Kantonsprofile.

    Args:
        kantone: Kantonsdaten.
        zr: Bundes-Zeitreihe.

    Returns:
        dict: Kennzahlen der Schweiz.
    """
    letzte = zr[-1]
    bev = sum(k["bevoelkerung"] for k in kantone.values())
    faelle = sum(k["faelle_stgb"] for k in kantone.values())
    aufg = sum(k["aufgeklaert"] for k in kantone.values())
    return {
        "jahr": int(letzte["jahr"]),
        "bevoelkerung": bev,
        "faelle": faelle,
        "hz": round(1e5 * faelle / bev, 1),
        "aq": round(100 * aufg / faelle, 1),
        "einbruch": z(letzte["hz_einbruch"]),
        "diebstahl": z(letzte["hz_diebstahl"]),
        "leib_leben": z(letzte["hz_leib_leben"]),
        "faelle_einbruch": z(letzte["faelle_einbruch"]),
        "faelle_diebstahl": z(letzte["faelle_diebstahl"]),
    }


# ---------------------------------------------------------------- Diagramme
BASE = DE.BASE
FONT = BASE["font"]["family"]


def fig(hoehe=360, **kw):
    """Neue Figur mit dem gemeinsamen Layout der Seite."""
    f = go.Figure()
    f.update_layout(**BASE, height=hoehe)
    if kw:
        f.update_layout(**kw)
    return f


def _fmt(v, nachkomma=0, einheit=""):
    if v is None:
        return "—"
    return f"{v:,.{nachkomma}f}".replace(",", "'") + einheit


def werte_senkrecht(f, x, y, einheit="", nachkomma=0, farbe=None, oben=True):
    """Schreibt die Werte über die senkrechten Balken."""
    f.add_trace(go.Scatter(
        x=list(x), y=list(y), mode="text",
        text=[_fmt(v, nachkomma, einheit) for v in y],
        textposition="top center" if oben else "bottom center",
        textfont=dict(size=11.5, color=farbe or INK, family=FONT),
        showlegend=False, hoverinfo="skip"))


def werte_waagerecht(f, x, y, einheit="", nachkomma=0, farbe=None):
    """Schreibt die Werte rechts neben die waagerechten Balken.

    Args:
        f: Figur.
        x: die Zahlen (bestimmen die Balkenlänge).
        y: die Kategorien.
    """
    f.add_trace(go.Scatter(
        x=list(x), y=list(y), mode="text",
        text=[_fmt(v, nachkomma, einheit) for v in x],
        textposition="middle right",
        textfont=dict(size=11.5, color=farbe or INK, family=FONT),
        showlegend=False, hoverinfo="skip"))


def diagramme(kantone, basis, zr, fd):
    """Alle Diagramme als Liste von (id, titel, untertitel, figur, quelle[, langtext]).

    Args:
        kantone: Kantonsdaten.
        basis: Kennzahlen der Schweiz.
        zr: Bundes-Zeitreihe.
        fd: Zusatzauswertungen (ESS, Referenzwerte, Eurostat).

    Returns:
        list[tuple]: Einträge in der Reihenfolge der Reiter.
    """
    figs = []
    ess, ref, eu = fd["ess"], fd["ref"], fd["eu"]

    def ref_werte(dimension, jahr=None, merkmal=None, auspraegung=None):
        out = []
        for r in ref:
            if r["dimension"] != dimension:
                continue
            if jahr is not None and int(r["jahr"]) != jahr:
                continue
            if merkmal is not None and r["merkmal"] != merkmal:
                continue
            if auspraegung is not None and r["auspraegung"] != auspraegung:
                continue
            out.append(r)
        return out

    # ------------------------------------------------ Kriminalität
    # 1) Häufigkeitszahl je Kanton
    daten = sorted(((k["hz"], k["name"], k["kuerzel"]) for k in kantone.values()),
                   key=lambda t: t[0])
    f = fig(760)
    f.add_trace(go.Bar(
        x=[d[0] for d in daten], y=[f"{d[1]} ({d[2]})" for d in daten],
        orientation="h",
        marker_color=[UEBER if d[0] > basis["hz"] else UNTER for d in daten],
        hovertemplate="%{y}: %{x:,.0f} Fälle je 100.000<extra></extra>"))
    werte_waagerecht(f, [d[0] for d in daten],
                     [f"{d[1]} ({d[2]})" for d in daten])
    f.update_xaxes(title="Fälle je 100.000 Einwohner", range=[0, max(d[0] for d in daten) * 1.16])
    f.update_yaxes(automargin=True, tickfont=dict(size=11.5), ticks="outside", ticklen=6)
    figs.append((
        "ch_hz", "Kriminalitätsbelastung je Kanton",
        f"Registrierte Straftaten nach Strafgesetzbuch je 100.000 Einwohner, {basis['jahr']}. "
        f"Schweizer Mittel: {_fmt(basis['hz'])}. Ocker steht für Kantone über dem Mittel, "
        "Petrol für Kantone darunter. Die Zahlen folgen dem Tatortprinzip: Gezählt wird, "
        "wo die Tat begangen wurde — nicht, wo die beschuldigte Person wohnt.",
        f, "BFS, Polizeiliche Kriminalstatistik (STAT-TAB px-x-1903020100_101), "
           "eigene Berechnung",
        "Einordnung: Basel-Stadt liegt mit Abstand vorn. Das ist zu einem erheblichen "
        "Teil ein Zählartefakt: Der Kanton hat rund 200.000 Einwohner, aber ein "
        "Vielfaches an Einpendlern, Gästen und Grenzgängern, und die Häufigkeitszahl "
        "setzt die Fälle nur ins Verhältnis zur Wohnbevölkerung. Genf und Zürich "
        "zeigen dasselbe Muster. Umgekehrt liegen die ländlichen Kantone der "
        "Zentralschweiz und beide Appenzell am tiefsten. Grenzen: Zwischen den "
        "Kantonen unterscheidet sich auch die Anzeigepraxis und die Kontrolldichte "
        "der Polizei; die Zahl misst daher nicht dasselbe wie ein Dunkelfeldmass."))

    # 2) Aufklärungsquote je Kanton
    daten = sorted(((k["aq"], k["name"], k["kuerzel"]) for k in kantone.values()),
                   key=lambda t: t[0])
    f = fig(760)
    f.add_trace(go.Bar(
        x=[d[0] for d in daten], y=[f"{d[1]} ({d[2]})" for d in daten],
        orientation="h",
        marker_color=[UNTER if d[0] >= basis["aq"] else NEUTRAL for d in daten],
        hovertemplate="%{y}: %{x:.1f} %<extra></extra>"))
    werte_waagerecht(f, [d[0] for d in daten],
                     [f"{d[1]} ({d[2]})" for d in daten], einheit=" %", nachkomma=1)
    f.update_xaxes(title="aufgeklärte Fälle in Prozent", range=[0, 62])
    f.update_yaxes(automargin=True, tickfont=dict(size=11.5), ticks="outside", ticklen=6)
    figs.append((
        "ch_aq", "Aufklärungsquote je Kanton",
        f"Anteil der registrierten Fälle, den die Polizei als aufgeklärt meldet, "
        f"{basis['jahr']}. Schweizer Mittel: {_fmt(basis['aq'], 1, ' %')}.",
        f, "BFS, Polizeiliche Kriminalstatistik (STAT-TAB), eigene Berechnung",
        "Einordnung: Die Quoten streuen zwischen rund 20 und 55 Prozent. Eine hohe "
        "Quote bedeutet nicht wenig Kriminalität — sie kann auch heissen, dass viele "
        "Fälle angezeigt werden, die leicht aufzuklären sind (etwa Ladendiebstahl "
        "mit gestellter Person), oder dass die Polizei viel kontrolliert. Ein "
        "Vergleich mit der deutschen Aufklärungsquote von 57,9 Prozent (2025) wäre "
        "irreführend: Beide Länder grenzen die Delikte unterschiedlich ab, und "
        "Deutschland zählt die Nebengesetze mit, die fast immer aufgeklärt werden."))

    # 3) Zeitreihe: Entwicklung nach Deliktsgruppen, indexiert
    jahre = [int(r["jahr"]) for r in zr]
    start = jahre[0]
    reihen = [
        ("hz_stgb", "Straftaten insgesamt", TEAL_H1),
        ("hz_diebstahl", "Diebstahl", TEAL_H2),
        ("hz_einbruch", "Einbruchdiebstahl", UEBER),
        ("hz_leib_leben", "Leib und Leben", "#6d28d9"),
        ("hz_cyberbetrug", "Betrug mit Datenanlagen", NEUTRAL),
    ]
    f = fig(430)
    for feld, name, farbe in reihen:
        werte = [z(r[feld]) for r in zr]
        basiswert = werte[0]
        f.add_trace(go.Scatter(
            x=jahre, y=[None if v is None else 100 * v / basiswert for v in werte],
            mode="lines+markers", name=name,
            line=dict(color=farbe, width=2.4), marker=dict(size=7, color=farbe),
            hovertemplate=name + " %{x}: Index %{y:.0f}<extra></extra>"))
    f.update_yaxes(title=f"Index ({start} = 100)", ticksuffix="")
    f.update_xaxes(title="Jahr", dtick=2)
    figs.append((
        "ch_gruppen_zr", "Was die Gesamtzahl verdeckt",
        f"Registrierte Fälle je Deliktsgruppe, {start} = 100. Die Summe bewegt sich "
        "kaum, die Teile laufen in verschiedene Richtungen.",
        f, "BFS, Polizeiliche Kriminalstatistik (STAT-TAB), eigene Berechnung",
        "Einordnung: Die Gesamtzahl der registrierten Straftaten liegt 2025 nur "
        "9 Prozent über dem Stand von 2009 — dazwischen lag ein Rückgang um mehr "
        "als ein Drittel und ein Wiederanstieg. Einbruchdiebstahl hat sich in "
        "diesem Zeitraum fast halbiert. Aussagen über «die Kriminalität» ohne "
        "Nennung der Deliktsgruppe sind deshalb nicht interpretierbar."))

    # 4) Häufigkeitszahl und Aufklärungsquote der Schweiz
    f = fig(400)
    f.add_trace(go.Scatter(
        x=jahre, y=[z(r["hz_stgb"]) for r in zr], mode="lines+markers",
        name="Häufigkeitszahl", line=dict(color=TEAL_H1, width=2.6),
        marker=dict(size=7, color=TEAL_H1), yaxis="y",
        hovertemplate="%{x}: %{y:,.0f} Fälle je 100.000<extra></extra>"))
    f.add_trace(go.Scatter(
        x=jahre, y=[z(r["aq_stgb"]) for r in zr], mode="lines+markers",
        name="Aufklärungsquote", line=dict(color=UEBER, width=2.6, dash="dot"),
        marker=dict(size=7, color=UEBER), yaxis="y2",
        hovertemplate="%{x}: %{y:.1f} % aufgeklärt<extra></extra>"))
    f.update_layout(
        yaxis=dict(title="Fälle je 100.000 Einwohner", gridcolor=GRID),
        yaxis2=dict(title="Aufklärungsquote", overlaying="y", side="right",
                    tickformat=".0f", ticksuffix=" %", showgrid=False))
    f.update_xaxes(title="Jahr", dtick=2)
    figs.append((
        "ch_zeitreihe", "Registrierte Straftaten und Aufklärung in der Schweiz",
        "Häufigkeitszahl und Aufklärungsquote nach Strafgesetzbuch, "
        f"{start} bis {jahre[-1]}. Zwei verschiedene Masse auf zwei Achsen.",
        f, "BFS, Polizeiliche Kriminalstatistik (STAT-TAB), eigene Berechnung",
        "Einordnung: Die Belastung stieg bis 2012, fiel dann acht Jahre lang und "
        "steigt seit 2021 wieder. Die Aufklärungsquote stieg über denselben "
        "Zeitraum fast stetig von 27,5 auf 38,7 Prozent. Die beiden Reihen laufen "
        "also nicht parallel — was die Polizei aufklärt, hängt stärker von der "
        "Deliktstruktur ab als vom Aufkommen. Grenzen: Die Reihe beginnt 2009, "
        "weil die BFS-Polizeistatistik erst dann gesamtschweizerisch "
        "vereinheitlicht wurde. Davor sind die Kantonsdaten nicht vergleichbar."))

    # 5) Streuung der Kantone nach Delikt
    felder = [("hz_diebstahl", "Diebstahl"), ("hz_einbruch", "Einbruchdiebstahl"),
              ("hz_leib_leben", "Leib und Leben"), ("hz_raub", "Raub"),
              ("hz_sachbeschaedigung", "Sachbeschädigung"),
              ("hz_cyberbetrug", "Betrug mit Datenanlagen")]
    f = fig(400)
    for i, (feld, name) in enumerate(felder):
        werte = [z(r[feld]) for r in zr if z(r[feld]) is not None]
        if not werte:
            continue
        f.add_trace(go.Box(
            x=[name] * len(werte), y=werte, name=name,
            marker_color=[TEAL_H1, UEBER, "#6d28d9", TEAL_H2, NEUTRAL, "#8b8378"][i],
            boxpoints=False, width=0.5,
            hovertemplate=name + "<br>%{y:,.0f} je 100.000<extra></extra>"))
    f.update_yaxes(title="Fälle je 100.000 Einwohner", type="log")
    f.update_layout(showlegend=False)
    f.update_xaxes(tickangle=-20, automargin=True)
    figs.append((
        "ch_streuung", "Wie weit die Kantone auseinanderliegen",
        "Häufigkeitszahl der Schweiz je Delikt, 2009 bis 2025. Die Boxen zeigen die "
        "Spanne zwischen dem 25. und 75. Prozent der Jahre; logarithmische Skala, "
        "weil die Delikte um mehr als den Faktor 100 auseinanderliegen.",
        f, "BFS, Polizeiliche Kriminalstatistik (STAT-TAB), eigene Berechnung",
        "Einordnung: Diese Darstellung zeigt die Schweiz als Ganzes über die Zeit. "
        "Die Streuung zwischen den Kantonen ist deutlich grösser als die Streuung "
        "zwischen den Jahren: Einzelne Kantone liegen beim Einbruch um ein "
        "Vielfaches über dem Mittel. Regionale Vergleiche sind deshalb "
        "aussagekräftiger als Zeitvergleiche — aber nur mit dem Nenner im Kopf."))

    # 6) Deutschland und Schweiz im harmonisierten Vergleich
    auswahl = ["Wohnungseinbruch", "Diebstahl", "Raub", "Vorsätzliche Tötung (vollendet)"]
    farb_de, farb_ch = NEUTRAL, TEAL_H1
    f = fig(430)
    for name in auswahl:
        reihe = [(int(r["jahr"]), z(r["de_rate"]), z(r["ch_rate"]))
                 for r in eu if r["delikt"] == name]
        reihe = [x for x in reihe if x[1] is not None and x[2] is not None]
        if not reihe:
            continue
        xs = [x[0] for x in reihe]
        f.add_trace(go.Scatter(
            x=xs, y=[x[1] for x in reihe], mode="lines+markers",
            name=name + " — Deutschland", line=dict(color=farb_de, width=2),
            marker=dict(size=6, color=farb_de, symbol="circle-open", line=dict(width=2)),
            legendgroup=name, hovertemplate=name + " DE %{x}: %{y:,.1f}<extra></extra>"))
        f.add_trace(go.Scatter(
            x=xs, y=[x[2] for x in reihe], mode="lines+markers",
            name=name + " — Schweiz", line=dict(color=farb_ch, width=2),
            marker=dict(size=6, color=farb_ch, symbol="circle"),
            legendgroup=name, hovertemplate=name + " CH %{x}: %{y:,.1f}<extra></extra>"))
    f.update_yaxes(title="registrierte Fälle je 100.000 Einwohner", type="log")
    f.update_xaxes(title="Jahr", dtick=2)
    figs.append((
        "ch_eurostat", "Deutschland und die Schweiz, gleich gemessen",
        "Registrierte Fälle je 100.000 Einwohner nach der harmonisierten "
        "Deliktgliederung von Eurostat (ICCS). Punkte mit offenem Rand: Deutschland, "
        "gefüllte Punkte: Schweiz. Logarithmische Skala.",
        f, "Eurostat crim_off_cat (Datenstand 2026), eigene Darstellung",
        "Einordnung: Wohnungseinbruch ist in der Schweiz etwa dreimal so häufig wie "
        "in Deutschland (2024: 308 gegen 94 je 100.000 Einwohner), während Raub und "
        "Tötungsdelikte in Deutschland häufiger registriert werden. Beim Diebstahl "
        "insgesamt liegen beide Länder 2024 nahe beieinander (CH 1'966, DE 1'377). "
        "Grenzen: Die Umlage auf die ICCS-Kategorien bleibt eine Umrechnung der "
        "nationalen Statistiken; die Erfassungspraxis unterscheidet sich weiterhin, "
        "und die Anzeigequote für Einbruch ist in beiden Ländern hoch, die für "
        "Raub und Körperverletzung unterschiedlich. Für «gefährliche "
        "Körperverletzung» sind die Reihen nicht vergleichbar (Deutschland "
        "verbucht dort Fälle, die die Schweiz als einfache Körperverletzung "
        "zählt); die Reihe ist deshalb hier weggelassen."))

    # ------------------------------------------------ Furcht
    # 7) Unsicherheitsgefühl im Zeitverlauf (ESS Schweiz)
    reihe = [r for r in ess if r["ebene"] == "gesamt"
             and r["kennzahl"] == "unsicher"]
    j, w, lo, hi, n = [], [], [], [], []
    for r in sorted(reihe, key=lambda r: float(r["jahr"])):
        j.append(int(float(r["jahr"])))
        w.append(z(r["anteil"]))
        lo.append(z(r["ki_lo"]))
        hi.append(z(r["ki_hi"]))
        n.append(int(float(r["n"])))
    f = fig(400)
    f.add_trace(go.Scatter(x=j + j[::-1], y=hi + lo[::-1], fill="toself",
                           fillcolor="rgba(15,118,110,.13)", line=dict(width=0),
                           name="95-%-Intervall", hoverinfo="skip"))
    f.add_trace(go.Scatter(
        x=j, y=w, mode="lines+markers", name="Schweiz",
        line=dict(color=TEAL_H1, width=2.6), marker=dict(size=8, color=TEAL_H1),
        customdata=n,
        hovertemplate="%{x}: %{y:.1f} % unsicher<br>n = %{customdata:,}<extra></extra>"))
    f.update_yaxes(title="Anteil mit Unsicherheitsgefühl", ticksuffix=" %")
    f.update_xaxes(title="Jahr", dtick=2)
    figs.append((
        "ch_ess", "Unsicherheitsgefühl im Zeitverlauf",
        "«Wie sicher fühlen Sie sich, wenn Sie nach Einbruch der Dunkelheit allein "
        "in Ihrer Wohngegend zu Fuss unterwegs sind?» Anteil «etwas unsicher» und "
        "«sehr unsicher», Schweizer Wohnbevölkerung ab 15 Jahren, gewichtet. "
        "European Social Survey, Runden 1–11.",
        f, "ESS Runden 1–11, eigene Berechnung (Gewichtung pspwght)",
        "Einordnung: Das Unsicherheitsgefühl in der Schweiz ist von 16,1 Prozent "
        "(2002) auf 8,9 Prozent (2023) gefallen — fast eine Halbierung. Das ist der "
        "stärkste Unterschied zur deutschen Entwicklung: In Deutschland liegt der "
        "Wert 2023 mit 25,0 Prozent höher als 2002 (26,2 Prozent), also praktisch "
        "unverändert. Grenzen: Die Balken sind 95-%-Intervalle als "
        "Normalapproximation ohne Designeffekt; das echte Intervall ist wegen der "
        "Klumpung der Stichprobe etwas breiter. Die Runden sind unabhängige "
        "Stichproben, kein Panel — ein Absinken kann daher auch ein "
        "Zusammensetzungseffekt der Befragten sein."))

    # 8) Deutschland und Schweiz im gleichen Instrument
    de_ess = lies(D / "ess_aggregate.csv") if (D / "ess_aggregate.csv").exists() else []
    f = fig(400)
    for name, reihe2, farbe in (("Schweiz", reihe, TEAL_H1),
                                ("Deutschland", [r for r in de_ess
                                                 if r["ebene"] == "zeitreihe"], NEUTRAL)):
        jj = sorted(int(float(r["jahr"])) for r in reihe2 if z(r["anteil"]) is not None)
        ww = [z(r["anteil"]) for r in sorted(
            [r for r in reihe2 if z(r["anteil"]) is not None],
            key=lambda r: float(r["jahr"]))]
        f.add_trace(go.Scatter(
            x=jj, y=ww, mode="lines+markers", name=name,
            line=dict(color=farbe, width=2.6), marker=dict(size=7, color=farbe),
            hovertemplate=name + " %{x}: %{y:.1f} %<extra></extra>"))
    f.update_yaxes(title="Anteil mit Unsicherheitsgefühl", ticksuffix=" %")
    f.update_xaxes(title="Jahr", dtick=2)
    figs.append((
        "ch_vgl", "Zwei Länder, dieselbe Frage",
        "Unsicherheitsgefühl in der Schweiz und in Deutschland, dieselbe Frage, "
        "dasselbe Erhebungsprogramm. Deutschland fehlt in Runde 10 (2020).",
        f, "ESS Runden 1–11, eigene Berechnung (Gewichtung pspwght)",
        "Einordnung: In beiden Ländern sinkt die Unsicherheit zwischen 2002 und "
        "2023, aber das Niveau liegt durchgehend um 12 bis 18 Prozentpunkte "
        "auseinander: 2023 fühlen sich in Deutschland 25,0 Prozent unsicher, in "
        "der Schweiz 8,9 Prozent. Registrierte Kriminalität ist in Deutschland "
        "allerdings auch höher — die Häufigkeitszahl liegt dort bei 6'591, in der "
        "Schweiz bei 6'106 (2025) und damit näher beieinander, als es die "
        "Furchtwerte nahelegen. Der Unterschied in der Furcht wird also nicht "
        "durch die Belastung allein erklärt. Grenzen: Die Frage misst nur die "
        "Einschätzung in der eigenen Wohngegend bei Dunkelheit, nicht Furcht "
        "vor einzelnen Delikten."))

    # 9) Sicherheit in den Befragungen der Schweiz
    f = fig(400)
    punkte = [(1989, 46.0, "frühere Befragungen"), (1996, 29.0, "frühere Befragungen"),
              (2011, 25.4, "Sicherheitsbefragung"), (2015, 33.1, "Sicherheitsbefragung")]
    f.add_trace(go.Scatter(
        x=[p[0] for p in punkte if p[2] == "frühere Befragungen"],
        y=[p[1] for p in punkte if p[2] == "frühere Befragungen"],
        mode="markers+lines", name="Furcht vor Einbruch (andere Instrumente)",
        line=dict(color=NEUTRAL, width=2, dash="dot"),
        marker=dict(size=8, color=NEUTRAL, symbol="circle-open", line=dict(width=2)),
        hovertemplate="%{x}: %{y:.1f} %<extra></extra>"))
    f.add_trace(go.Scatter(
        x=[p[0] for p in punkte if p[2] == "Sicherheitsbefragung"],
        y=[p[1] for p in punkte if p[2] == "Sicherheitsbefragung"],
        mode="markers+lines", name="Furcht vor Einbruch (Sicherheitsbefragung 2011/2015)",
        line=dict(color=UEBER, width=2.6),
        marker=dict(size=9, color=UEBER),
        hovertemplate="%{x}: %{y:.1f} %<extra></extra>"))
    uns = [(1996, 17.0), (2000, 22.0), (2011, 15.4), (2015, 14.7)]
    cs22 = ref_werte("sicherheitsgefuehl", 2022)
    us22 = sum(float(r["wert_prozent"]) for r in cs22
               if r["auspraegung"] in ("etwas unsicher", "sehr unsicher"))
    f.add_trace(go.Scatter(
        x=[1996, 2000, 2011, 2015, 2022], y=[17.0, 22.0, 15.4, 14.7, round(us22, 1)],
        mode="markers+lines", name="Unsicher zu Fuss nach Dunkelheit",
        line=dict(color=TEAL_H1, width=2.6), marker=dict(size=9, color=TEAL_H1),
        hovertemplate="%{x}: %{y:.1f} %<extra></extra>"))
    f.update_yaxes(title="Anteil der Befragten", ticksuffix=" %")
    f.update_xaxes(title="Jahr", dtick=5)
    figs.append((
        "ch_befragungen", "Furcht vor Einbruch und Unsicherheit auf der Strasse",
        "Zwei Masse aus den Schweizer Bevölkerungsbefragungen. Die Furcht vor einem "
        "Einbruch in den nächsten zwölf Monaten wurde 2022 nicht mehr erfragt; der "
        "letzte Punkt stammt von 2015.",
        f, "Swiss Crime Survey 2022 (Kap. 2.3, Tab. 81/82); Schweizerische "
           "Sicherheitsbefragung 2015 (Kap. 4.1.1, Tab. 87); ältere ICVS-Werte nach "
           "SKP-Info 3/2017",
        "Einordnung: Zwischen 2011 und 2015 ist die Furcht vor einem Einbruch von "
        "25,4 auf 33,1 Prozent gestiegen, obwohl die Häufigkeitszahl des "
        "Einbruchdiebstahls im selben Zeitraum um ein Viertel gefallen ist. Genau "
        "diese Gegenläufigkeit ist der Kern der Auswertung. Die Unsicherheit auf "
        "der Strasse blieb dagegen nahezu unverändert und liegt 2022 bei 12,4 "
        "Prozent. Grenzen: Die Werte von 1989, 1996 und 2000 stammen aus einem "
        "anderen Erhebungsprogramm (ICVS) und sind hier nur als grobe Orientierung "
        "eingezeichnet — der Rückgang über vier Jahrzehnte ist aber in allen "
        "Quellen sichtbar."))

    # 10) Einbruchdiebstahl: Fälle und Furcht nebeneinander
    f = fig(400)
    einb = [(int(r["jahr"]), z(r["faelle_einbruch"])) for r in zr]
    f.add_trace(go.Bar(
        x=[e[0] for e in einb], y=[e[1] for e in einb], name="registrierte Fälle",
        marker_color=TEAL_H3,
        hovertemplate="%{x}: %{y:,.0f} registrierte Einbruchdiebstähle<extra></extra>"))
    f.add_trace(go.Scatter(
        x=[2011, 2015], y=[None, None], mode="markers", showlegend=False,
        hoverinfo="skip"))
    f.update_yaxes(title="registrierte Fälle (StGB, Tatort Schweiz)")
    f.update_xaxes(title="Jahr", dtick=2)
    f.update_layout(bargap=0.35)
    figs.append((
        "ch_einbruch", "Einbruchdiebstahl: registrierte Fälle",
        "Polizeilich registrierte Einbruchdiebstähle nach Strafgesetzbuch, "
        "Schweiz, 2009 bis 2025. Zum Vergleich mit der Furcht siehe das "
        "vorhergehende Diagramm.",
        f, "BFS, Polizeiliche Kriminalstatistik (STAT-TAB), eigene Berechnung",
        "Einordnung: Die registrierten Einbruchdiebstähle fielen von 52'000 "
        "(2012) auf rund 21'000 (2021) — ein Rückgang um rund 60 Prozent — und "
        "steigen seither wieder auf 32'000 (2025). Die Furcht vor Einbruch hat "
        "sich in einem Teil dieses Zeitraums in die Gegenrichtung bewegt. "
        "Grenzen: Registrierte Fälle hängen von der Anzeigebereitschaft ab. Im "
        "Crime Survey 2022 geben 75,1 Prozent der Betroffenen an, den Einbruch "
        "angezeigt zu haben, 2015 waren es 86,6 Prozent — die Anzeigebereitschaft "
        "ist also gesunken. Ein Teil des Rückgangs im Hellfeld kann daher auch "
        "ein Rückgang der Anzeigen sein."))

    # 11) Unsicherheit nach Bevölkerungsgruppen (ESS, gepoolt)
    gruppen = [("Geschlecht", "Frau"), ("Geschlecht", "Mann")]
    auswahl_g = []
    for r in ess:
        if r["ebene"] == "geschlecht" and r["kennzahl"] == "unsicher":
            auswahl_g.append((r["gruppe"], z(r["anteil"]), z(r["ki_lo"]),
                              z(r["ki_hi"]), int(float(r["n"]))))
    alter = [(r["gruppe"], z(r["anteil"]), z(r["ki_lo"]), z(r["ki_hi"]),
              int(float(r["n"]))) for r in ess if r["ebene"] == "alter_gr"
             and r["kennzahl"] == "unsicher"]
    stadt = [(r["gruppe"], z(r["anteil"]), z(r["ki_lo"]), z(r["ki_hi"]),
              int(float(r["n"]))) for r in ess if r["ebene"] == "stadt_land"
             and r["kennzahl"] == "unsicher"]
    alle = auswahl_g + alter + stadt
    alle = [a for a in alle if a[1] is not None]
    alle.sort(key=lambda a: a[1])
    f = fig(430)
    f.add_trace(go.Scatter(
        x=[a[1] for a in alle], y=[a[0] for a in alle], mode="markers",
        marker=dict(size=9, color=TEAL_H1),
        error_x=dict(type="data", symmetric=False,
                     array=[a[3] - a[1] for a in alle],
                     arrayminus=[a[1] - a[2] for a in alle],
                     color=SLATE, thickness=1.4, width=0),
        customdata=[a[4] for a in alle],
        hovertemplate="%{y}: %{x:.1f} %<br>n = %{customdata:,}<extra></extra>",
        showlegend=False))
    mittel_alle = float(np.mean([a[1] for a in alle]))
    f.add_vline(x=mittel_alle, line=dict(color=UEBER, width=1.6, dash="dash"))
    f.add_annotation(x=mittel_alle, y=-0.6, yref="paper", text="Mittel der Gruppen",
                     showarrow=False, font=dict(size=11, color=UEBER), xanchor="left")
    f.update_xaxes(title="Anteil mit Unsicherheitsgefühl", ticksuffix=" %")
    f.update_yaxes(automargin=True, ticks="outside", ticklen=6)
    figs.append((
        "ch_gruppen", "Wer sich unsicher fühlt",
        "Unsicherheitsgefühl nach Bevölkerungsgruppen, Runden 1–11 gepoolt "
        "(2002 bis 2023). Strichlein: 95-%-Intervall. Fallzahlen zwischen "
        "831 und 9'633 je Gruppe.",
        f, "ESS Runden 1–11, eigene Berechnung (Gewichtung pspwght)",
        "Einordnung: Der Unterschied zwischen Frauen (21,2 Prozent) und Männern "
        "(5,5 Prozent) ist der grösste Einzelbefund — und er ist grösser als in "
        "Deutschland (dort 37,5 gegen 12,2 Prozent, aber auf höherem Niveau). "
        "Frauen fürchten sich deutlich häufiger, ohne häufiger betroffen zu sein: "
        "Die Viktimisierungsrate liegt bei Frauen mit 17,9 Prozent sogar leicht "
        "unter der der Männer (17,3 Prozent, Unterschied im Rahmen der "
        "Zufallsschwankung). Auch die Altersstruktur ist umgekehrt zur "
        "Opferbelastung: Am unsichersten sind die über 75-Jährigen, am häufigsten "
        "betroffen die 16- bis 29-Jährigen. Grenzen: Die Gruppen sind gepoolt "
        "über alle Runden; Veränderungen über die Zeit sind damit nicht sichtbar. "
        "Bildung, Einkommen und Wohnlage wurden nicht kontrolliert — die "
        "Unterschiede können sich gegenseitig erklären."))

    # 12) Grossregionen
    reg = [(r["gruppe"], z(r["anteil"]), z(r["ki_lo"]), int(float(r["n"])))
           for r in ess if r["ebene"] == "grossregion" and r["kennzahl"] == "unsicher"]
    reg = sorted([r for r in reg if r[1] is not None], key=lambda r: r[1])
    regv = {r["gruppe"]: z(r["anteil"]) for r in ess
            if r["ebene"] == "grossregion" and r["kennzahl"] == "viktim"}
    f = fig(400)
    f.add_trace(go.Bar(
        x=[r[1] for r in reg], y=[r[0] for r in reg], orientation="h",
        name="Unsicherheitsgefühl",
        marker_color=[UEBER if r[1] > np.mean([x[1] for x in reg]) else UNTER
                      for r in reg],
        error_x=dict(type="data", symmetric=False, array=[r[1] - r[2] for r in reg],
                     arrayminus=[0] * len(reg), color=SLATE, thickness=1.4, width=0),
        hovertemplate="%{y}: %{x:.1f} %<extra></extra>"))
    werte_waagerecht(f, [r[1] for r in reg], [r[0] for r in reg],
                     einheit=" %", nachkomma=1)
    f.update_xaxes(title="Anteil mit Unsicherheitsgefühl (ESS 2010–2023, gepoolt)",
                   ticksuffix=" %", range=[0, max(r[1] for r in reg) * 1.3])
    f.update_yaxes(automargin=True, ticks="outside", ticklen=6)
    figs.append((
        "ch_regionen", "Unsicherheitsgefühl nach Grossregion",
        "Sieben Grossregionen, Runden 5–11 gepoolt (2010 bis 2023). Die "
        "Regionalkennung wird erst ab Runde 5 vergeben. Fallzahlen je Region: "
        "362 bis 2'501.",
        f, "ESS Runden 5–11, eigene Berechnung (Gewichtung pspwght)",
        "Einordnung: Die Zentralschweiz liegt mit 8,3 Prozent am tiefsten, die "
        "Nordwestschweiz mit 14,8 Prozent am höchsten — der Abstand entspricht "
        "etwa dem zwischen Bayern und Nordrhein-Westfalen im deutschen Vergleich. "
        "Die Viktimisierungsrate folgt dieser Reihenfolge nicht: Im Tessin liegt "
        f"sie bei {regv.get('Tessin', float('nan')):.1f} Prozent und damit am "
        "höchsten, während das Unsicherheitsgefühl dort mit 9,8 Prozent "
        "unterdurchschnittlich ist. Genau diese Entkopplung zeigt sich auch in "
        "Deutschland. Grenzen: Der Wert gilt für die Grossregion, nicht für den "
        "einzelnen Kanton. Die Karte färbt deshalb alle Kantone einer Region "
        "gleich ein; belastbare Kantonswerte zur Furcht gibt es in der Schweiz "
        "nicht."))

    # 13) Vermeidungsverhalten
    paare = {}
    for r in ref:
        if r["dimension"] != "vermeidung":
            continue
        paare.setdefault(r["merkmal"], {})[int(r["jahr"])] = float(r["wert_prozent"])
    paare = {k: v for k, v in paare.items() if 2015 in v and 2022 in v}
    paare = dict(sorted(paare.items(), key=lambda kv: kv[1][2015]))
    f = fig(430)
    ys = list(paare)
    for x0, x1 in ((2015, 2022),):
        f.add_trace(go.Scatter(
            x=[paare[k][x0] for k in ys], y=ys, mode="markers",
            name=str(x0), marker=dict(size=10, color=TEAL_H3,
                                      line=dict(color="#ffffff", width=1.5)),
            hovertemplate="%{y}<br>" + str(x0) + ": %{x:.1f} %<extra></extra>"))
        f.add_trace(go.Scatter(
            x=[paare[k][x1] for k in ys], y=ys, mode="markers",
            name=str(x1), marker=dict(size=10, color=TEAL_H1,
                                      line=dict(color="#ffffff", width=1.5)),
            hovertemplate="%{y}<br>" + str(x1) + ": %{x:.1f} %<extra></extra>"))
        for i, k in enumerate(ys):
            f.add_shape(type="line", x0=paare[k][x0], x1=paare[k][x1], y0=i, y1=i,
                        line=dict(color="#8B95A5", width=1.6))
    f.update_xaxes(title="Anteil der Befragten, die das Verhalten nennen",
                   ticksuffix=" %")
    f.update_yaxes(automargin=True, ticks="outside", ticklen=6)
    f.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    figs.append((
        "ch_vermeidung", "Was Menschen tun, um nicht Opfer zu werden",
        "Vermeidungsverhalten abends nach 20 Uhr, Schweizer Wohnbevölkerung. "
        "Mehrfachantworten möglich, deshalb summieren sich die Werte nicht auf 100.",
        f, "Swiss Crime Survey 2022, Kap. 2.3, Tabelle 83",
        "Einordnung: Das häufigste Verhalten ist, gewissen Leuten aus dem Weg zu "
        "gehen (25,3 Prozent), gefolgt vom Meiden von Unterführungen (23,5 "
        "Prozent). Gegenüber 2015 sind die meisten Werte leicht gesunken — die "
        "Bevölkerung schränkt sich also weniger ein. Zugenommen hat nur, «immer "
        "vor 20 Uhr zu Hause» zu sein (von 4,1 auf 5,5 Prozent). Grenzen: "
        "Vermeidungsverhalten ist ein indirektes Mass für Furcht und wird von "
        "allen Befragten berichtet, auch von solchen, die sich nicht unsicher "
        "fühlen. Die Anteile sind nicht adjustiert."))

    # 14) Betroffenheit und Anzeigebereitschaft
    praev = {}
    for r in ref:
        if r["dimension"] == "praevalenz_1jahr":
            praev.setdefault(r["merkmal"], {})[int(r["jahr"])] = float(r["wert_prozent"])
    anzeige = {}
    for r in ref:
        if r["dimension"] == "anzeigerate":
            anzeige[r["merkmal"]] = float(r["wert_prozent"])
    gemeinsam = [k for k in anzeige if k in praev and 2022 in praev[k]]
    gemeinsam.sort(key=lambda k: -anzeige[k])
    f = fig(400)
    f.add_trace(go.Bar(
        x=[praev[k][2022] for k in gemeinsam], y=gemeinsam, orientation="h",
        name="im letzten Jahr betroffen", marker_color=TEAL_H3,
        hovertemplate="%{y}: %{x:.1f} %<extra></extra>"))
    f.add_trace(go.Bar(
        x=[anzeige[k] for k in gemeinsam], y=gemeinsam, orientation="h",
        name="davon bei der Polizei angezeigt", marker_color=TEAL_H1,
        hovertemplate="%{y}: %{x:.1f} %<extra></extra>"))
    f.update_xaxes(title="Anteil der Befragten", ticksuffix=" %")
    f.update_yaxes(automargin=True, ticks="outside", ticklen=6)
    f.update_layout(barmode="group", legend=dict(orientation="h", y=1.06, x=0))
    figs.append((
        "ch_anzeige", "Vom Vorfall zur Anzeige",
        "Einjahresprävalenz und Anzeigerate 2022 nach Delikt. Gerechnet auf alle "
        "Befragten, nicht nur auf die Betroffenen.",
        f, "Swiss Crime Survey 2022, Kap. 3, Tabelle 93",
        "Einordnung: Die Anzeigebereitschaft hängt stark vom Delikt ab: Ein "
        "Einbruch wird zu 75 Prozent gemeldet (meist wegen der Versicherung), "
        "eine sexuelle Belästigung zu 7 Prozent. Deshalb bildet die "
        "Polizeistatistik die Delikte sehr unterschiedlich gut ab — beim "
        "Wohnungseinbruch ist der Hellfeldanteil hoch, bei Gewalt im sozialen "
        "Nahraum niedrig. Grenzen: Die Anzeigeraten sind Selbstauskünfte; die "
        "berichteten Opferzahlen beruhen auf 150 bis 1'300 Fällen je Delikt und "
        "schwanken entsprechend."))

    # ------------------------------------------------ Strafverfolgung
    # 15) Aufklärungsquote nach Delikt
    letzte = zr[-1]
    aq_felder = [("aq_stgb", "Straftaten insgesamt"), ("aq_diebstahl", "Diebstahl"),
                 ("aq_einbruch", "Einbruchdiebstahl"), ("aq_leib_leben", "Leib und Leben"),
                 ("aq_raub", "Raub"), ("aq_sachbeschaedigung", "Sachbeschädigung"),
                 ("aq_vergewaltigung", "Vergewaltigung"),
                 ("aq_cyberbetrug", "Betrug mit Datenanlagen")]
    aq = [(name, z(letzte[feld])) for feld, name in aq_felder if z(letzte[feld]) is not None]
    aq.sort(key=lambda t: t[1])
    f = fig(400)
    f.add_trace(go.Bar(
        x=[a[1] for a in aq], y=[a[0] for a in aq], orientation="h",
        marker_color=TEAL_H1,
        hovertemplate="%{y}: %{x:.1f} % aufgeklärt<extra></extra>"))
    werte_waagerecht(f, [a[1] for a in aq], [a[0] for a in aq],
                     einheit=" %", nachkomma=1)
    f.update_xaxes(title="aufgeklärte Fälle in Prozent", ticksuffix=" %",
                   range=[0, max(a[1] for a in aq) * 1.25])
    f.update_yaxes(automargin=True, ticks="outside", ticklen=6)
    figs.append((
        "ch_aq_delikt", "Aufgeklärt wird vor allem, was leicht zu klären ist",
        f"Aufklärungsquote nach Delikt, Schweiz {letzte['jahr']}.",
        f, "BFS, Polizeiliche Kriminalstatistik (STAT-TAB), eigene Berechnung",
        "Einordnung: Zwischen dem Recht gut aufzuklärenden Bereich Leib und Leben "
        "und dem Einbruchdiebstahl liegt ein Faktor von mehr als vier. Das ist "
        "kein Hinweis auf unterschiedlich gute Polizeiarbeit, sondern auf "
        "unterschiedliche Ermittlungsansätze: Bei Körperverletzung ist die "
        "beschuldigte Person oft bekannt, beim Einbruch selten. Grenzen: Die "
        "Quote bezieht sich auf Fälle, nicht auf Personen; ein Fall mit mehreren "
        "Beschuldigten zählt einmal."))

    return figs

# ---------------------------------------------------------------- SVG-Karte
# Beschriftung: die üblichen Kantonskürzel. Für Basel-Stadt ist der Kanton auf
# der Karte nur wenige Pixel breit; das Kürzel steht deshalb daneben und ist
# mit einer Führungslinie an die Fläche gebunden.
KARTE_VERSATZ = {"Basel-Stadt": (-62.0, -26.0)}


def karte_html(geo):
    """Baut die klickbare Kantonskarte als SVG.

    Args:
        geo: Geometrien aus output/ch_kantone_svg.json (inkl. _viewbox).

    Returns:
        str: SVG-Markup. Jede Kantonsfläche trägt den NUTS-3-Code als
            data-nuts, damit das Skript sie einfärben und verlinken kann.
    """
    teile = [f'<svg class="karte" viewBox="{geo["_viewbox"]}" '
             'xmlns="http://www.w3.org/2000/svg" role="img" '
             'aria-label="Karte der Schweiz mit den 26 Kantonen">']
    for code, v in geo.items():
        if code == "_viewbox":
            continue
        teile.append(f'<path class="bl" data-nuts="{code}" d="{v["d"]}" '
                     f'tabindex="0"><title>{v["name"]}</title></path>')
    for code, v in geo.items():
        if code == "_viewbox":
            continue
        lx, ly = v["label"]
        dx, dy = KARTE_VERSATZ.get(v["name"], (0.0, 0.0))
        ku = KUERZEL[v["name"]]
        if (dx, dy) != (0.0, 0.0):
            teile.append(f'<line class="fl" x1="{lx:.1f}" y1="{ly:.1f}" '
                         f'x2="{lx + dx:.1f}" y2="{ly + dy:.1f}"/>')
        teile.append(f'<text class="ks" x="{lx + dx:.1f}" y="{ly + dy:.1f}" '
                     f'text-anchor="middle" dominant-baseline="central">{ku}</text>')
    teile.append("</svg>")
    return "\n".join(teile)


# ---------------------------------------------------------------- Texte
TEXTE_START = {
    "kriminalitaet": (
        "Kriminalität im Vergleich",
        "Die Häufigkeitszahl unterscheidet sich zwischen den Kantonen um mehr als "
        "das Vierfache. Basel-Stadt, Genf und Zürich liegen weit vorn — was auch an "
        "Pendlern, Gästen und Grenzgängern liegt, nicht nur an mehr Straftaten: "
        "Gezählt wird am Tatort, geteilt wird durch die Wohnbevölkerung. Die "
        "Bundesreihe beginnt 2009, weil die Polizeistatistik erst dann "
        "gesamtschweizerisch vereinheitlicht wurde."),
    "furcht": (
        "Furcht im Vergleich",
        "Das Unsicherheitsgefühl folgt der Kriminalitätsbelastung nicht. Die "
        "Zentralschweiz hat die tiefsten Werte, die Nordwestschweiz die höchsten — "
        "und im Tessin ist die Betroffenheit am grössten, die Furcht aber unter dem "
        "Mittel. Kantonswerte zur Furcht gibt es in der Schweiz nicht; ausgewiesen "
        "sind die sieben Grossregionen mit 362 bis 2'501 Befragten je Region."),
    "justiz": (
        "Strafverfolgung",
        "Zwischen einem Vorfall und einer Aufklärung liegen zwei Schritte, die "
        "nichts miteinander zu tun haben müssen: Erst muss jemand Anzeige erstatten, "
        "dann muss die Polizei den Fall klären. Beim Einbruch ist die "
        "Anzeigebereitschaft hoch und die Aufklärungsquote tief, bei "
        "Körperverletzung ist es umgekehrt. Die Aufklärungsquote der Schweiz ist mit "
        "Deutschland nicht vergleichbar — die Deliktgrenzen sind andere."),
}


# ---------------------------------------------------------------- Seite
CH_CSS = """
/* Der Kopfbereich der Deutschland-Fassung trägt eine Deutschland-\n   Silhouette als Hintergrundbild. Auf der Schweizer Seite wäre sie\n   schlicht falsch, deshalb hier ohne Bild. */\n.kopf{background-image:none}\n/* Beschriftung der Kantonskürzel. Bewusst ohne Fettschrift im Randbereich:
   Die kleinen Kantone würden sonst benachbarte Flächen überdecken. */
.karte .ks{font-size:15px;font-weight:650;fill:#12100e;pointer-events:none;
 font-family:var(--font);letter-spacing:.01em}
.karte .bl{cursor:pointer}
@media (max-width:700px){.karte .ks{font-size:19px}}
.kopf-nav{display:flex;gap:14px;font-size:.8rem}
.kopf-nav a{color:#b8b2ab;text-decoration:none;white-space:nowrap}
.kopf-nav a:hover{color:#fff}
.lkopf .lk-kuerzel{display:inline-block;font-size:.72rem;font-weight:650;
 letter-spacing:.08em;color:var(--muted);border:1px solid var(--line);
 border-radius:999px;padding:2px 9px;vertical-align:6px;margin-left:8px}
"""


def baue_html(karte, daten, fig_json, fig_meta):
    """Setzt die vollständige Seite zusammen.

    Args:
        karte: SVG-Markup der Kantonskarte.
        daten: Nutzdaten für das Skript (basis, kantone, texte_start).
        fig_json: Diagramme als Plotly-JSON, nach Kennung.
        fig_meta: Titel, Untertitel, Quelle und Langtext je Diagramm.

    Returns:
        str: HTML der Seite (ohne eingebettete Plotly-Bibliothek).
    """
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#12100e">
<title>Kriminalität und Sicherheit in der Schweiz</title>
<!--PLOTLY-->
<style>{DE.schrift_css()}</style>
<style>{DE.CSS}{CH_CSS}</style>
</head>
<body>
<div id="app">
  <header class="kopf">
    <div class="kopf-inner">
      <div class="kopf-titel">
        <h1>Kriminalität und Sicherheit in der Schweiz</h1>
        <p>Registrierte Straftaten, Strafverfolgung und das Sicherheitsgefühl der
        Bevölkerung — für die Schweiz und für jeden Kanton.</p>
      </div>
      <div class="kopf-nav">
        <a href="index.html">Startseite</a>
        <a href="deutschland.html">Deutschland</a>
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
    <p><strong>Quellen.</strong> Bundesamt für Statistik, Polizeiliche
    Kriminalstatistik und Wohnbevölkerung (STAT-TAB); Swiss Crime Survey 2022
    (ZHAW / Universität St. Gallen im Auftrag der KKPKS) und Schweizerische
    Sicherheitsbefragung 2015 (Killias Research &amp; Consulting); European Social
    Survey, Runden 1–11 (eigene Berechnung, gewichtet); Eurostat crim_off_cat;
    Kartengeometrie von Eurostat/GISCO (CC BY 4.0).</p>
    <p><strong>Grenzen.</strong> Registrierte Fälle sind polizeilich bekannt
    gewordene Vorgänge — kein Nachweis einer Straftat und keine Verurteilung.
    Erfasst ist nur das Strafgesetzbuch; Widerhandlungen gegen das Betäubungsmittel-
    und das Ausländerrecht sind nicht enthalten. Die Häufigkeitszahl bezieht Fälle
    auf die Wohnbevölkerung am Tatort, nicht auf die dort wohnenden Menschen.
    Furchtwerte gelten für die Grossregion, nicht für den einzelnen Kanton.
    Alle Zusammenhangsaussagen beruhen auf Querschnittsdaten und belegen keine
    Ursachen.</p>
    <p class="credit">Erstellt von <strong>Christopher Vantis</strong> mit
    <strong>Hermes</strong> (KI-Assistent). Auswahl der Fragen, Deutung und Prüfung
    der Ergebnisse liegen beim Autor; Recherche, Auswertung und Umsetzung
    entstanden im Dialog mit dem Assistenten.</p>
  </footer>
</div>

<div id="karte-svg" hidden>{karte}</div>

<script id="daten" type="application/json">{json.dumps(daten, ensure_ascii=False)}</script>
<script id="figuren" type="application/json">{json.dumps(fig_json, ensure_ascii=False)}</script>
<script id="figmeta" type="application/json">{json.dumps(fig_meta, ensure_ascii=False)}</script>
{SCRIPT_CH}
</body>
</html>"""


SCRIPT_CH = r"""
<script>
const DATEN = JSON.parse(document.getElementById('daten').textContent);
const FIGS = JSON.parse(document.getElementById('figuren').textContent);
const META = JSON.parse(document.getElementById('figmeta').textContent);
const K = DATEN.kantone;                 /* Kantone, Schlüssel = Kantonsname */
const KN = {};                           /* Zugriff über den NUTS-3-Code */
Object.values(K).forEach(k => { if (k.nuts) KN[k.nuts] = k; });
const B = DATEN.basis;
const KONF = {responsive:true, displaylogo:false, scrollZoom:true,
  displayModeBar:true, modeBarButtonsToRemove:['lasso2d','select2d'],
  toImageButtonOptions:{format:'png', filename:'kriminalitaet-sicherheit-schweiz', scale:2}};

const nf = (v, d = 0) => (v === null || v === undefined || isNaN(v)) ? '—'
  : v.toLocaleString('de-CH', {minimumFractionDigits:d, maximumFractionDigits:d});
const pct = (v, d = 1) => (v === null || v === undefined) ? '—' : nf(v, d) + ' %';

/* ---------- Kennzahlen der Karte ---------- */
/* Jede Kennzahl trägt ihre eigene Einordnung. Ohne sie ist eine farbige Karte
   nicht lesbar: Dieselbe Zahl bedeutet je nach Bezugsgrösse etwas anderes. */
const KENNZAHLEN = {
  hz: {label:'Kriminalitätsbelastung', kurz:'Belastung', einheit:0,
       wert:k => k.hz,
       hinweis:'Registrierte Straftaten nach Strafgesetzbuch je 100.000 Einwohner '
         + '(Häufigkeitszahl), ' + B.jahr + '. Gezählt wird nach Tatortprinzip: '
         + 'Fälle werden dort verbucht, wo die Tat begangen wurde, geteilt wird '
         + 'durch die dort wohnhafte Bevölkerung. Kantone mit vielen Einpendlern '
         + 'und Gästen haben dadurch höhere Werte.'},
  einbruch: {label:'Einbruchdiebstahl', kurz:'Einbruch', einheit:0,
       wert:k => (k.delikte['Einbruchdiebstahl (Art. 139)']||{}).hz,
       hinweis:'Registrierte Einbruchdiebstähle je 100.000 Einwohner '
         + '(Art. 139 StGB), ' + B.jahr + '. Die Anzeigebereitschaft ist bei '
         + 'diesem Delikt hoch (75 Prozent laut Crime Survey 2022), das Hellfeld '
         + 'bildet es also besser ab als die meisten anderen Delikte.'},
  diebstahl: {label:'Diebstahl insgesamt', kurz:'Diebstahl', einheit:0,
       wert:k => (k.delikte['Diebstahl (Art. 139)']||{}).hz,
       hinweis:'Registrierte Diebstähle je 100.000 Einwohner (Art. 139 StGB), '
         + 'einschliesslich Einbruch-, Trick- und Ladendiebstahl, ' + B.jahr + '.'},
  gewalt: {label:'Leib und Leben', kurz:'Gewalt', einheit:0,
       wert:k => (k.delikte['Straftaten gegen Leib und Leben (1. Titel)']||{}).hz,
       hinweis:'Straftaten gegen Leib und Leben je 100.000 Einwohner (1. Titel '
         + 'StGB), einschliesslich Tätlichkeiten, ' + B.jahr + '. Diese Gruppe '
         + 'wird überwiegend angezeigt, wenn die beschuldigte Person bekannt ist.'},
  aq: {label:'Aufklärungsquote', kurz:'Aufklärung', einheit:1,
       wert:k => k.aq,
       hinweis:'Anteil der registrierten Fälle, den die Polizei als aufgeklärt '
         + 'meldet, ' + B.jahr + '. Eine hohe Quote heisst nicht wenig '
         + 'Kriminalität: Sie kann auch bedeuten, dass viele Fälle angezeigt '
         + 'werden, die leicht zu klären sind. Mit Deutschland ist die Quote '
         + 'nicht vergleichbar — die Deliktgrenzen sind andere.'},
  furcht: {label:'Unsicherheitsgefühl', kurz:'Furcht', einheit:1,
       wert:k => k.furcht.unsicher,
       hinweis:'Anteil der Befragten, die sich nach Einbruch der Dunkelheit '
         + 'allein zu Fuss unsicher fühlen. European Social Survey, Runden 5–11 '
         + '(2010–2023), gepoolt. ACHTUNG: Der Wert gilt für die Grossregion '
         + '(7 Regionen), nicht für den Kanton — alle Kantone einer Region sind '
         + 'deshalb gleich eingefärbt. Fallzahlen 362 bis 2\'501.'},
  viktim: {label:'Betroffenheit', kurz:'Betroffenheit', einheit:1,
       wert:k => k.furcht.viktim,
       hinweis:'Anteil der Befragten, die in den letzten zwölf Monaten Opfer '
         + 'einer Straftat wurden (ESS-Frage crmvct), Runden 5–11 gepoolt. Wie '
         + 'beim Unsicherheitsgefühl gilt der Wert für die Grossregion, nicht '
         + 'für den Kanton.'},
  ausland: {label:'Ausländeranteil', kurz:'Ausländeranteil', einheit:1,
       wert:k => k.auslaenderanteil,
       hinweis:'Anteil der ausländischen an der ständigen Wohnbevölkerung, '
         + 'Stand 31. Dezember. Nur die Staatsangehörigkeit, nicht die Herkunft. '
         + 'Die Zahl sagt nichts über die Täterschaft aus: Die Statistik zählt '
         + 'Taten am Tatort, nicht nach Wohnort der beschuldigten Person.'},
  dichte: {label:'Bevölkerungsdichte', kurz:'Dichte', einheit:0,
       wert:k => k.dichte,
       hinweis:'Einwohner je Quadratkilometer, berechnet aus Bevölkerungszahl '
         + 'und Kantonsfläche (Fläche aus der Kartengrundlage GISCO, '
         + 'verallgemeinert).'},
};
/* Fünf Stufen, alle hell genug für schwarze Schrift ohne Rand. */
const STUFEN = ['#f2f8f6', '#d3e9e4', '#a8d5ce', '#74b8af', '#3d9187'];

/* Farbstufen nach Rang statt nach gleichen Wertabständen: sonst zieht
   Basel-Stadt das Maximum so hoch, dass alle übrigen Kantone in den
   hellsten Stufen landen. */
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
  const werte = Object.values(K).map(k.wert).filter(v => v !== null && v !== undefined && !isNaN(v));
  const lo = Math.min(...werte), hi = Math.max(...werte);
  const grenzen = grenzenNachRang(werte);
  rankingZeigen(kennzahl, k, grenzen);
  document.querySelectorAll('.bl').forEach(p => {
    const kt = KN[p.dataset.nuts];
    p.style.fill = kt ? klasseRang(k.wert(kt), grenzen) : '#eee9e3';
  });
  const leg = document.getElementById('legende');
  if (leg){
    leg.innerHTML = '<span>niedrig ' + nf(lo, k.einheit) + '</span><span class="stufen">'
      + STUFEN.map(c => '<i style="background:' + c + '"></i>').join('')
      + '</span><span>hoch ' + nf(hi, k.einheit) + '</span>'
      + '<span style="margin-left:6px">(' + k.kurz + ', Stufen nach Rang)</span>'
      + (k.hinweis ? '<span class="kenn-hinweis">' + k.hinweis + '</span>' : '');
  }
}

function rankingZeigen(key, k, grenzen){
  const box = document.getElementById('ranking');
  if (!box) return;
  const unter = document.getElementById('rank-unter');
  if (unter) unter.textContent = 'Kennzahl: ' + k.kurz;
  const liste = Object.values(K)
    .map(kt => ({name: kt.name, ku: kt.kuerzel, nuts: kt.nuts, wert: k.wert(kt)}))
    .filter(x => x.wert !== null && x.wert !== undefined && !isNaN(x.wert))
    .sort((a, b) => b.wert - a.wert);
  function gruppe(t, eintraege){
    return '<div class="rank-gruppe"><h4>' + t + '</h4>' + eintraege.map(x =>
      '<button class="rank-zeile" data-nuts="' + x.nuts + '">'
      + '<span class="rank-punkt" style="background:' + klasseRang(x.wert, grenzen) + '"></span>'
      + '<span class="rank-name">' + x.name + ' <span style="color:var(--muted)">(' + x.ku + ')</span></span>'
      + '<span class="rank-wert">' + nf(x.wert, k.einheit) + '</span></button>').join('') + '</div>';
  }
  const voll = box.dataset.voll === '1';
  const bez = k.kurz;
  box.innerHTML = voll
    ? gruppe('Alle ' + liste.length + ' Kantone · ' + bez, liste)
    : gruppe('Höchste Werte · ' + bez, liste.slice(0, 5))
      + gruppe('Tiefste Werte · ' + bez, liste.slice(-5).reverse());
  const um = document.createElement('button');
  um.className = 'rank-mehr';
  um.textContent = voll ? 'Nur die Extremwerte zeigen' : 'Alle ' + liste.length + ' anzeigen';
  um.addEventListener('click', () => {
    box.dataset.voll = voll ? '0' : '1';
    karteFaerben(key);
  });
  box.appendChild(um);
}

/* ---------- Diagramme: faul zeichnen und an die Fenstergrösse anpassen --- */
let anpassungsTimer = null;
function diagrammeAnpassen(){
  const schmal = window.innerWidth < 720;
  document.querySelectorAll('.js-plotly-plot').forEach(el => {
    if (!el || !el.layout) return;
    try {
      Plotly.relayout(el, {
        'showlegend': !schmal,
        'font.size': schmal ? 15 : 12.5,
        'xaxis.tickfont.size': schmal ? 14 : 12,
        'yaxis.tickfont.size': schmal ? 14 : 12,
        'legend.orientation': schmal ? 'v' : 'h',
        'legend.x': 0,
        'legend.y': schmal ? -0.42 : 1.05,
        'legend.yanchor': schmal ? 'top' : 'bottom',
        'margin.l': schmal ? 52 : 10,
        'margin.r': schmal ? 26 : 20,
        'margin.b': schmal ? 64 : 50,
        'margin.t': schmal ? 66 : 54,
      });
    } catch (e) { /* noch nicht fertig gezeichnet */ }
  });
}
window.addEventListener('resize', () => {
  clearTimeout(anpassungsTimer);
  anpassungsTimer = setTimeout(() => {
    diagrammeAnpassen();
    document.querySelectorAll('.js-plotly-plot').forEach(el => {
      const figur = FIGS && FIGS[el.dataset.fig] ? FIGS[el.dataset.fig] : null;
      if (figur) htmlLegende(el, figur);
    });
  }, 240);
});

function htmlLegende(el, f){
  const alt = el.parentNode.querySelector('.html-legende');
  if (alt) alt.remove();
  if (window.innerWidth >= 720) return;
  const eintraege = (f.data || []).filter(t => t.showlegend !== false && t.name);
  if (!eintraege.length) return;
  const box = document.createElement('div');
  box.className = 'html-legende';
  box.innerHTML = eintraege.map(t => {
    const farbe = (t.marker && t.marker.color) || (t.line && t.line.color) || '#3f3a35';
    return '<span><i style="background:' + farbe + '"></i>' + t.name + '</span>';
  }).join('');
  el.parentNode.insertBefore(box, el.nextSibling);
}

function zeichne(el){
  if (el.dataset.state) return;
  el.dataset.state = 'laeuft';
  const f = FIGS[el.dataset.fig];
  if (!f){ return; }
  const lay = Object.assign({}, f.layout || {});
  lay.autosize = true;
  if (window.innerWidth < 560 && lay.height) lay.height = Math.min(lay.height, 360);
  Plotly.newPlot(el, f.data, lay, KONF).then(() => {
    el.dataset.state = 'fertig';
    diagrammeAnpassen();
    htmlLegende(el, f);
  }).catch(() => { delete el.dataset.state; });
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
function kartenblock(ids){
  return ids.map(id => {
    const m = META.find(x => x.id === id);
    if (!m) return '';
    let eo = '';
    if (DATEN.texte_start[id]){
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
  document.getElementById('inhalt').innerHTML = `
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
            <h3 id="rank-titel">Höchste und tiefste Werte</h3>
            <p class="rank-unter" id="rank-unter"></p>
            <div id="ranking"></div>
          </aside>
        </div>
      </div>
      <div class="hinweis">
        <strong>Was die Karte zeigt:</strong> Die Kriminalitätsbelastung ist in den
        Stadtkantonen am höchsten, das Unsicherheitsgefühl folgt ihr aber nicht.
        Probieren Sie die Kennzahlen durch — färben Sie die Karte einmal nach
        Belastung, einmal nach Unsicherheitsgefühl und einmal nach Betroffenheit.
        Die drei Bilder sehen verschieden aus.
      </div>
      <div class="karten">__START__</div>
    </div>`.replace('__KARTE__', KARTE_SVG).replace('__START__', '');
  const sel = Object.entries(KENNZAHLEN)
    .map(([k, v]) => '<option value="' + k + '">' + v.label + '</option>').join('');
  document.getElementById('kennzahl').innerHTML = sel;
  document.getElementById('kennzahl').addEventListener('change', e => karteFaerben(e.target.value));
  karteFaerben('hz');
  beobachte();
}

/* ---------- Ansicht: Themen ---------- */
const THEMEN = {
  inhalt:        {ids:[]},
  kriminalitaet: {ids:['ch_hz','ch_gruppen_zr','ch_zeitreihe','ch_streuung','ch_eurostat']},
  furcht:        {ids:['ch_ess','ch_vgl','ch_befragungen','ch_einbruch','ch_regionen',
                       'ch_gruppen','ch_vermeidung']},
  justiz:        {ids:['ch_aq','ch_aq_delikt','ch_anzeige']},
  methodik:      {ids:[]},
};

function ansichtThema(t){
  const cfg = THEMEN[t];
  let html = '<div class="view">';

  if (t === 'inhalt'){
    html += `<section class="card">
      <h3>Worum es geht</h3>
      <p class="unter">Dieselbe Frage wie für Deutschland — nur mit Schweizer Daten.</p>
      <div class="einordnung">
        <p>Die Deutschlandkarte dieser Seite zeigt einen Widerspruch: Die registrierte
        Kriminalität sinkt langfristig, das Unsicherheitsgefühl steigt. Diese Fassung
        stellt dieselben Fragen an die Schweiz — mit denselben Instrumenten, wo es
        sie gibt, und mit den Schweizer Befragungen, wo es sie nicht gibt.</p>
        <h4 class="schritt">1. Wie hat sich die registrierte Kriminalität entwickelt?</h4>
        <p><strong>Kaum verändert, mit einem tiefen Bogen dazwischen.</strong> 2009
        wurden <strong>553'421</strong> Straftaten nach Strafgesetzbuch registriert,
        2025 sind es <strong>554'963</strong> — praktisch derselbe Wert. Dazwischen
        lag ein Rückgang bis <strong>415'008</strong> Fällen (2021) und ein
        Wiederanstieg. Umgerechnet auf die Einwohnerzahl fiel die Häufigkeitszahl
        von 7'147 auf 6'106. Ein Einzeldelikt hat sich dabei fast halbiert:
        Einbruchdiebstahl ging von rund 52'000 Fällen (2012) auf rund 32'000 (2025)
        zurück.</p>
        <h4 class="schritt">2. Wie hat sich die Furcht entwickelt?</h4>
        <p><strong>Ebenfalls nach unten — anders als in Deutschland.</strong> Der
        Anteil der Menschen, die sich nachts allein zu Fuss unsicher fühlen, sank im
        European Social Survey von <strong>16,1 Prozent</strong> (2002) auf
        <strong>8,9 Prozent</strong> (2023). In Deutschland blieb der Wert im
        selben Zeitraum bei rund einem Viertel. Die Schweizer Befragungen zum
        Sicherheitsgefühl bestätigen den Rückgang: 1996 fühlten sich 17 Prozent
        unsicher, 2015 waren es 14,7, 2022 noch 12,4 Prozent.</p>
        <h4 class="schritt">3. Folgt die Furcht der Kriminalität?</h4>
        <p><strong>Nicht durchgehend.</strong> Zwischen 2011 und 2015 ist die
        registrierte Einbruchshäufigkeit um ein Viertel gefallen, während die Furcht
        vor einem Einbruch von 25,4 auf 33,1 Prozent <em>gestiegen</em> ist. Auch
        räumlich passt es nicht: Im Tessin ist die Betroffenheit am höchsten, die
        Furcht aber unterdurchschnittlich. Und Frauen fürchten sich viermal so oft
        wie Männer, obwohl sie nicht häufiger betroffen sind. Das ist derselbe
        Befund wie in Deutschland — nur auf tieferem Niveau.</p>
      </div>
      <div class="note"><h4>Was hier nicht steht</h4><p>Diese Seite belegt
      Zusammenhänge, keine Ursachen. Warum die Furcht in der Schweiz tiefer liegt
      als in Deutschland — oder warum sie in einem Zeitraum stieg, in dem die
      Einbrüche fielen — lässt sich mit diesen Daten nicht entscheiden. Beide
      Länder sind wohlhabend, beide haben eine ähnliche Belastungsziffer, und
      trotzdem unterscheiden sich die Furchtwerte um mehr als das Doppelte. Wer
      dafür eine Erklärung anbietet, sollte sie prüfen können.</p></div>
      <p class="quelle">Zahlen: BFS, Polizeiliche Kriminalstatistik (StGB) und
      Wohnbevölkerung; ESS Runden 1–11; Swiss Crime Survey 2022;
      Schweizerische Sicherheitsbefragung 2015.</p>
    </section>`;
  }

  if (cfg.ids.length && t !== 'inhalt'){
    html += '<div class="karten">' + kartenblock(cfg.ids) + '</div>';
  }

  if (t === 'methodik'){
    html += `<section class="card"><h3>Daten und Methoden</h3>
      <p class="unter">Was in dieser App steckt und wie belastbar es ist.</p>
      <h4 style="margin:14px 0 2px;font-size:.9rem;color:var(--ink)">Die Schweiz im Überblick</h4>
      <p class="unter" style="margin-bottom:12px">Zum Vergleich mit den Kantonen.</p>
      <div class="kk" id="bund-kk"></div>
      <details open><summary>Quellen</summary><ul>
        <li><strong>Kriminalität:</strong> Bundesamt für Statistik (BFS), Polizeiliche
        Kriminalstatistik (PKS), Tabelle px-x-1903020100_101 über die STAT-TAB-Schnittstelle
        abgerufen: registrierte Straftaten nach Strafgesetzbuch, Kanton, Ausführungs-,
        Aufklärungsgrad und Jahr, 2009–2025.</li>
        <li><strong>Wohnbevölkerung:</strong> BFS, Demografische Bilanz nach Kanton
        (px-x-0102020000_101), Stand am 1. Januar und 31. Dezember; die Jahresbevölkerung
        für die Häufigkeitszahl ist das Mittel aus beiden Ständen.</li>
        <li><strong>Furcht:</strong> European Social Survey, Runden 1–11 (2002–2023),
        eigene Berechnung, Gewichtung pspwght. Die Regionalkennung wird erst ab Runde 5
        vergeben; Regionswerte sind deshalb aus den Runden 5–11 gepoolt.</li>
        <li><strong>Deliktbezogene Furcht und Opfererfahrungen:</strong> Swiss Crime
        Survey 2022 (ZHAW, Universität St. Gallen, im Auftrag der KKPKS; n = 15'519)
        und Schweizerische Sicherheitsbefragung 2015 (n = 2'004). Es handelt sich um
        veröffentlichte Berichtswerte, nicht um eigene Auswertungen der Mikrodaten —
        die Mikrodaten sind nicht frei zugänglich.</li>
        <li><strong>Internationaler Vergleich:</strong> Eurostat crim_off_cat,
        harmonisierte Deliktgliederung ICCS, Fälle je 100.000 Einwohner.</li>
        <li><strong>Kartengeometrie:</strong> Eurostat/GISCO, NUTS-RG 2021, Maßstab
        1:3 Mio (CC BY 4.0). Die Kantonsflächen sind daraus abgeleitet und
        verallgemeinert; die Flächensumme liegt mit 41'172 km² rund 0,3 Prozent unter
        der amtlichen Gesamtfläche.</li>
        <li><strong>Karte — wichtig zur Farblesung:</strong> Die fünf Farbstufen werden
        nach <em>Rang</em> vergeben, nicht nach gleichen Wertabständen. Jede Stufe
        enthält etwa gleich viele Kantone. Gleiche Farbunterschiede bedeuten deshalb
        <em>nicht</em> gleiche Zahlenunterschiede. Für genaue Werte die Rangliste
        oder das Kantonsprofil nutzen.</li>
      </ul></details>
      <details><summary>Grenzen und Fallstricke</summary><ul>
        <li>Registrierte Fälle sind polizeilich bekannt gewordene Vorgänge — kein
        Nachweis einer Straftat und keine Verurteilung. Für beschuldigte Personen
        gilt bis zu einer rechtskräftigen Verurteilung die Unschuldsvermutung.</li>
        <li>Erfasst ist nur das Strafgesetzbuch (StGB). Widerhandlungen gegen das
        Betäubungsmittelgesetz und das Ausländer- und Integrationsgesetz — im BFS-Total
        rund ein Fünftel aller registrierten Straftaten — sind nicht enthalten. Das
        macht die Reihe über die Zeit konsistent, aber unvollständig.</li>
        <li>Die PKS zählt nach Tatortprinzip: Fälle werden dort verbucht, wo die Tat
        begangen wurde. Die Häufigkeitszahl teilt durch die dort wohnhafte Bevölkerung.
        In Kantonen mit vielen Einpendlern, Gästen und Grenzgängern fällt der Nenner
        dadurch zu klein aus. Das ist kein Messfehler, aber auch kein Mass für die
        Kriminalität der ansässigen Bevölkerung.</li>
        <li>Die Reihe beginnt 2009. Davor war die kantonale Erfassung nicht
        vereinheitlicht; ein Anschluss an ältere Zahlen wäre nicht zulässig.</li>
        <li>Die Summe der Kantone erreicht das Schweiz-Total nicht ganz: Im Total sind
        auch Straftaten aus dem Zuständigkeitsbereich des Bundes enthalten, die keinem
        Kanton zugeordnet werden. Der Restbetrag liegt 2024/2025 unter 100 Fällen,
        zwischen 2009 und 2023 aber bei bis zu 5'000.</li>
        <li>Die Aufklärungsquote der Schweiz ist mit der deutschen (57,9 Prozent, 2025)
        <em>nicht</em> vergleichbar. Beide Länder grenzen Delikte unterschiedlich ab, und
        Deutschland zählt die Nebengesetze mit, die fast immer aufgeklärt werden.</li>
        <li>Furchtwerte für die Kantone gibt es nicht. Der Crime Survey 2022 ist
        national repräsentativ; kantonale Zusatzstichproben wurden nur für einzelne
        Kantone finanziert. Ausgewiesen sind die sieben Grossregionen aus dem ESS —
        dort gilt der Wert für die Region, nicht für den Kanton.</li>
        <li>Die Zeitreihen der Furcht sind Momentaufnahmen unabhängiger Stichproben,
        kein Panel. Kausale Aussagen sind damit nicht möglich.</li>
        <li>Die Befragungen sind nicht deckungsgleich: Der ESS erhebt telefonisch und
        persönlich, der Crime Survey online. Online-Befragungen ziehen tendenziell
        etwas andere Gruppen an. Vergleiche zwischen den Erhebungen sind deshalb
        nur als Grössenordnung zu lesen.</li>
      </ul></details></section>`;
  }
  html += '</div>';
  document.getElementById('inhalt').innerHTML = html;
  const bk = document.getElementById('bund-kk');
  if (bk){
    bk.innerHTML = [
      ['Einwohner', nf(B.bevoelkerung)],
      ['Straftaten nach StGB', nf(B.faelle)],
      ['je 100.000 Einwohner', nf(B.hz, 0)],
      ['Aufklärungsquote', pct(B.aq, 1)],
      ['Einbruchdiebstahl', nf(B.faelle_einbruch) + ' Fälle'],
    ].map(k => '<div><b>' + k[1] + '</b><span>' + k[0] + '</span></div>').join('');
  }
  beobachte();
}

/* ---------- Ansicht: Kanton ---------- */
function ansichtKanton(nuts){
  const k = KN[nuts];
  if (!k) return;
  const order = ['Straftaten nach StGB insgesamt','Diebstahl (Art. 139)',
    'Einbruchdiebstahl (Art. 139)','Raub (Art. 140)','Sachbeschädigung (Art. 144)',
    'Betrug und betrügerischer Missbrauch einer Datenanlage',
    'Straftaten gegen Leib und Leben (1. Titel)','Vergewaltigung (Art. 190)'];
  const rows = order.filter(d => k.delikte[d]).map(d => {
    const x = k.delikte[d];
    return '<tr><td>' + d + '</td><td class="num">' + nf(x.faelle) + '</td><td class="num">'
      + nf(x.hz, 0) + '</td><td class="num">' + pct(x.aq, 1) + '</td></tr>';
  }).join('');
  const f = k.furcht;
  const dF = (f.unsicher !== null && f.unsicher !== undefined) ? f.unsicher - B.furcht_mittel : null;

  document.getElementById('inhalt').innerHTML = `
  <div class="view">
    <button class="zurueck" id="zurueck">← Zurück zur Schweizerkarte</button>
    <div class="lkopf">
      <h2>${k.name}<span class="lk-kuerzel">${k.kuerzel}</span></h2>
      <p>${nf(k.bevoelkerung)} Einwohner · Grossregion ${k.region}</p>
      ${kacheln([
        ['Straftaten ' + B.jahr, nf(k.faelle_stgb)],
        ['je 100.000 Einwohner', nf(k.hz, 0)],
        ['Aufklärungsquote', pct(k.aq, 1)],
        ['Unsicherheitsgefühl', pct(f.unsicher, 1)],
        ['Betroffenheit', pct(f.viktim, 1)],
      ])}
    </div>

    <div class="hinweis">
      <strong>Unsicherheitsgefühl.</strong> Für ${k.name} liegt kein eigener
      Befragungswert vor. Ausgewiesen ist der Wert der Grossregion
      <strong>${k.region}</strong>: <strong>${pct(f.unsicher, 1)}</strong> fühlen sich
      nach Einbruch der Dunkelheit unsicher (95-%-Intervall ${pct(f.ki_lo, 1)} bis
      ${pct(f.ki_hi, 1)}, n = ${nf(f.n)}).
      ${dF !== null ? 'Das liegt ' + (Math.abs(dF) < 1.5 ? 'nahe am' : dF > 0 ? 'über dem' : 'unter dem')
        + ' Mittel der sieben Regionen (' + pct(B.furcht_mittel, 1) + ').' : ''}
    </div>

    <div class="karten">
      <section class="card">
        <h3>Kriminalität in ${k.name}</h3>
        <p class="unter">Fälle, Häufigkeitszahl (je 100.000 Einwohner) und
        Aufklärungsquote ${B.jahr}.</p>
        <div style="overflow-x:auto">
        <table class="tabelle">
          <thead><tr><th>Delikt</th><th class="num">Fälle</th>
          <th class="num">je 100.000 Einwohner</th><th class="num">aufgeklärt</th></tr></thead>
          <tbody>${rows}</tbody>
        </table></div>
        <p class="quelle">Quelle: BFS, Polizeiliche Kriminalstatistik (STAT-TAB)</p>
      </section>

      <section class="card">
        <h3>Struktur des Kantons</h3>
        <p class="unter">Demografie im schweizerischen Vergleich.</p>
        ${kacheln([
          ['Fläche', nf(k.flaeche, 0) + ' km²'],
          ['Bevölkerungsdichte', nf(k.dichte, 0) + ' Einw./km²'],
          ['Ausländeranteil', pct(k.auslaenderanteil, 1)],
          ['aufgeklärte Fälle', nf(k.aufgeklaert)],
        ])}
        <p class="quelle">Quellen: BFS (Bevölkerung, Nationalität); Fläche aus der
        Kartengrundlage GISCO</p>
      </section>

      <section class="card">
        <h3>Einordnung</h3>
        <p class="unter">Was diese Zahlen für ${k.name} bedeuten — und was nicht.</p>
        <div class="einordnung" id="eo"></div>
      </section>
    </div>
  </div>`;
  document.getElementById('zurueck').addEventListener('click', () => {
    document.querySelector('.tab[data-ansicht="karte"]').click();
  });
  document.getElementById('eo').textContent = einordnung(k, dF);
  window.scrollTo({top: 0, behavior: 'smooth'});
}

function einordnung(k, dF){
  const teile = [];
  if (k.hz){
    const rel = k.hz / B.hz;
    teile.push('Die Kriminalitätsbelastung liegt ' +
      (rel > 1.05 ? 'über' : rel < 0.95 ? 'unter' : 'etwa auf') +
      ' dem Schweizer Mittel (' + nf(k.hz, 0) + ' gegenüber ' + nf(B.hz, 0) +
      ' Fällen je 100.000 Einwohner).');
    if (rel > 1.3){
      teile.push('Ein Teil dieses Abstands ist ein Recheneffekt: Die Häufigkeitszahl ' +
        'teilt die am Tatort registrierten Fälle durch die dort wohnhafte Bevölkerung. ' +
        'Wo viele Menschen zur Arbeit, zum Einkaufen oder in die Ferien hinfahren, ' +
        'steigt der Zähler, ohne dass der Nenner mitwächst.');
    }
  }
  if (k.aq){
    teile.push('Die Aufklärungsquote beträgt ' + pct(k.aq, 1) +
      ' (Schweizer Mittel ' + pct(B.aq, 1) + ').');
  }
  if (k.delikte['Einbruchdiebstahl (Art. 139)']){
    const e = k.delikte['Einbruchdiebstahl (Art. 139)'];
    teile.push('Beim Einbruchdiebstahl wurden ' + nf(e.faelle) + ' Fälle registriert (' +
      nf(e.hz, 0) + ' je 100.000 Einwohner), davon ' + pct(e.aq, 1) + ' aufgeklärt.');
  }
  if (dF !== null){
    teile.push('Das Unsicherheitsgefühl der Grossregion ' + k.region + ' liegt ' +
      (Math.abs(dF) < 1.5 ? 'nahe am' : dF > 0 ? 'über dem' : 'unter dem') +
      ' Mittel der sieben Regionen (' + pct(B.furcht_mittel, 1) + '). Kantonswerte ' +
      'zur Furcht gibt es in der Schweiz nicht — die Befragungen sind national ' +
      'angelegt.');
  }
  if (k.auslaenderanteil !== null && k.auslaenderanteil !== undefined){
    teile.push('Der Ausländeranteil der ständigen Wohnbevölkerung beträgt ' +
      pct(k.auslaenderanteil, 1) + '. Aus dieser Zahl lässt sich nichts über ' +
      'Täterschaft ableiten: Die Statistik erfasst Taten am Tatort, nicht nach ' +
      'Wohnsitz der beschuldigten Person.');
  }
  if (k.dichte !== null && k.dichte !== undefined){
    teile.push('Die Bevölkerungsdichte liegt bei ' + nf(k.dichte, 0) +
      ' Einwohnern je Quadratkilometer.');
  }
  return teile.join(' ');
}

/* ---------- Navigation ---------- */
let AKTIV = 'karte';
function zeige(ansicht, param){
  AKTIV = ansicht;
  try{
    const h = (ansicht === 'kanton' && param) ? ('#kanton=' + param)
            : (ansicht !== 'karte' ? ('#' + ansicht) : '');
    if (location.hash !== h) history.replaceState(null, '', h || location.pathname);
  }catch(e){}
  document.querySelectorAll('.tab').forEach(t =>
    t.classList.toggle('active', t.dataset.ansicht === ansicht));
  if (ansicht === 'karte') ansichtKarte();
  else if (ansicht === 'kanton') ansichtKanton(param);
  else ansichtThema(ansicht);
  if (ansicht === 'kanton') document.querySelector('.tab[data-ansicht="karte"]').classList.add('active');
}

document.addEventListener('click', e => {
  const p = e.target.closest('.bl');
  if (p){ zeige('kanton', p.dataset.nuts); return; }
  const r = e.target.closest('.rank-zeile');
  if (r){ zeige('kanton', r.dataset.nuts); }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.target.classList && e.target.classList.contains('bl')){
    zeige('kanton', e.target.dataset.nuts);
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
  const werte = Object.values(K).map(k => k.furcht.unsicher)
    .filter(v => v !== null && v !== undefined);
  B.furcht_mittel = werte.reduce((a, b) => a + b, 0) / werte.length;

  const h = (location.hash || '').replace('#', '');
  if (h.startsWith('kanton=')){
    const nuts = h.slice(7);
    if (KN[nuts]){ zeige('kanton', nuts); return; }
  }
  if (h && THEMEN[h]){ zeige(h); return; }
  zeige('karte');
})();
window.addEventListener('hashchange', () => {
  const h = (location.hash || '').replace('#', '');
  if (h.startsWith('kanton=') && KN[h.slice(7)]) zeige('kanton', h.slice(7));
  else if (THEMEN[h]) zeige(h);
  else zeige('karte');
});
</script>
"""


def main():
    """Baut dashboard/schweiz.html."""
    kantone, viewbox, zr, fd = lade_daten()
    basis = basis_zahlen(kantone, zr)
    figs = diagramme(kantone, basis, zr, fd)

    daten = {
        "basis": basis,
        "kantone": kantone,
        "texte_start": TEXTE_START,
    }
    fig_json, fig_meta = {}, []
    for eintrag in figs:
        fid, titel, unter, f, quelle = eintrag[:5]
        langtext = eintrag[5] if len(eintrag) > 5 else None
        fig_json[fid] = json.loads(pio.to_json(f))
        fig_meta.append({"id": fid, "titel": titel, "unter": unter,
                         "quelle": quelle, "langtext": langtext})

    karte = karte_html(json.loads(
        (OUT / "ch_kantone_svg.json").read_text(encoding="utf-8")))
    html = baue_html(karte, daten, fig_json, fig_meta)
    ziel = ROOT / "dashboard" / "schweiz.html"
    ziel.write_text(html.replace("<!--PLOTLY-->", "<script>" + get_plotlyjs() + "</script>"),
                    encoding="utf-8")
    print(f"schweiz.html: {ziel.stat().st_size/1e6:.2f} MB | "
          f"{len(kantone)} Kantone | {len(figs)} Diagramme | "
          f"HZ Schweiz {basis['hz']:.0f} | AQ {basis['aq']:.1f} %")
    return kantone, basis


if __name__ == "__main__":
    main()
