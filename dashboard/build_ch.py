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
from plotly.offline import get_plotlyjs

import build_app as DE          # CSS, Schrift, geteilte Bausteine

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard" / "data"
OUT = ROOT / "output"

UNTER, UEBER, NEUTRAL = DE.UNTER, DE.UEBER, DE.NEUTRAL
TEAL_H1, TEAL_H2, TEAL_H3 = DE.TEAL_H1, DE.TEAL_H2, DE.TEAL_H3
INK, SLATE, GRID = DE.INK, DE.SLATE, DE.GRID

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

# Delikte im Kantonsprofil: Anzeigename -> Spaltenpräfix in den Kennzahlen.
PROFIL_DELIKTE = [
    ("Straftaten nach StGB insgesamt", "stgb", True),
    ("Diebstahl (Art. 139)", "diebstahl", False),
    ("Einbruchdiebstahl (Art. 139)", "einbruch", False),
    ("Raub (Art. 140)", "raub", False),
    ("Sachbeschädigung (Art. 144)", "sachbeschaedigung", False),
    ("Betrug, betrügerischer Missbrauch einer Datenanlage", "cyberbetrug", False),
    ("Straftaten gegen Leib und Leben (1. Titel)", "leib_leben", False),
    ("Vergewaltigung (Art. 190)", "vergewaltigung", False),
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
        tuple: (kantone, viewbox, zeitreihe, fig_daten) — Kantonsdaten als
            Dictionary, SVG-Zeichenfläche, Bundes-Zeitreihe und die
            Zusatzauswertungen für die Diagramme.
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
        for anzeige, praefix, _ in PROFIL_DELIKTE:
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

    # NUTS-3-Code ergänzen (für Kartenpfade und Verlinkung)
    for code, v in geo.items():
        if code == "_viewbox":
            continue
        if v["name"] in kantone:
            kantone[v["name"]]["nuts"] = code

    fig_daten = {
        "ess": ess, "ref": ref, "eu": eu,
        "ess_personen": str(D / "ch_ess_personen.csv"),
    }
    return kantone, geo["_viewbox"], zr, fig_daten


def basis_zahlen(kantone, zr):
    """Rahmendaten der Schweiz für Kopf, Methoden-Reiter und Kantonsprofile.

    Args:
        kantone: Kantonsdaten.
        zr: Bundes-Zeitreihe (eine Zeile je Jahr).

    Returns:
        dict: Kennzahlen der Schweiz.
    """
    letzte = zr[-1]
    bev = sum(k["bevoelkerung"] for k in kantone.values())
    faelle = sum(k["faelle_stgb"] for k in kantone.values())
    aufg = sum(k["aufgeklaert"] for k in kantone.values())
    return {
        "jahr": int(letzte["jahr"]),
        "bevoelkerung_kantone": bev,
        "faelle": faelle,
        "hz": 1e5 * faelle / bev,
        "aq": 100 * aufg / faelle,
        "einbruch": z(letzte["hz_einbruch"]),
        "diebstahl": z(letzte["hz_diebstahl"]),
        "leib_leben": z(letzte["hz_leib_leben"]),
        "faelle_einbruch": z(letzte["faelle_einbruch"]),
        "faelle_diebstahl": z(letzte["faelle_diebstahl"]),
    }


# ---------------------------------------------------------------- Diagramme
BASE = DE.BASE


def fig(hoehe=360, **kw):
    """Neue Figur mit dem gemeinsamen Layout der Seite."""
    f = go.Figure()
    f.update_layout(**BASE, height=hoehe)
    if kw:
        f.update_layout(**kw)
    return f


def _werte_an_balken(f, x=None, y=None, einheit="", nachkomma=0, waagerecht=False,
                     farbe=None):
    """Schreibt die Werte an die Balken (statt Gitternetzlinien abzulesen).

    Args:
        f: Plotly-Figur.
        x: x-Werte (bei senkrechten Balken die Kategorien).
        y: y-Werte (bei senkrechten Balken die Zahlen).
        einheit: Suffix hinter dem Wert.
        nachkomma: Nachkommastellen.
        waagerecht: True bei horizontalen Balken (x = Zahl, y = Kategorie).
        farbe: Schriftfarbe der Werte.

    Returns:
        None: die Figur wird an Ort und Stelle ergänzt.
    """
    def fmt(v):
        if v is None:
            return "—"
        s = f"{v:,.{nachkomma}f}".replace(",", "'")
        return s + einheit
    if waagerecht:
        f.add_trace(go.Scatter(
            x=list(x), y=list(y), mode="text",
            text=[fmt(v) for v in x], textposition="middle right",
            textfont=dict(size=11.5, color=farbe or INK, family=BASE["font"]["family"]),
            showlegend=False, hoverinfo="skip"))
    else:
        f.add_trace(go.Scatter(
            x=list(x), y=list(y), mode="text",
            text=[fmt(v) for v in y], textposition="top center",
            textfont=dict(size=11.5, color=farbe or INK, family=BASE["font"]["family"]),
            showlegend=False, hoverinfo="skip"))


def _serie(rows, jahr_feld="jahr", wert_feld="unsicher"):
    """Zieht eine Zeitreihe aus den ESS-Aggregaten."""
    j, w, lo, hi, n = [], [], [], [], []
    for r in rows:
        if r.get(jahr_feld) in ("", None):
            continue
        j.append(int(float(r[jahr_feld])))
        w.append(z(r[wert_feld]))
        lo.append(z(r["ki_lo"]))
        hi.append(z(r["ki_hi"]))
        n.append(int(float(r["n"])))
    return j, w, lo, hi, n
