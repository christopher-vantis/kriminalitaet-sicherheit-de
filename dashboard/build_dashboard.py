#!/usr/bin/env python3
"""
build_dashboard.py — Projekt 47 "Kriminalitätsdiskrepanz DE"
============================================================
Baut dashboard/index.html: ein selbst-enthalltenes, mobil-taugliches
Dashboard zu registrierter Kriminalität (PKS), Tatverdächtigen,
Strafverfolgung (Destatis) und Kriminalitätsfurcht (ESS, SKiD/DVS, SOEP/DIW).

Gestaltung:
- Farben nach der Okabe-Ito-Palette (farbenblind-tauglich, hoher Kontrast).
- Titel, Untertitel, Einordnung und Quellen als HTML (Plotly-Titel brechen
  auf schmalen Displays nicht um).
- Achsen mit automargin statt fester Margins.
- Unter jeder Grafik: Einordnung, Interpretation und Theorie/Evidenz.

Datenbasis (lokal, kein Internet nötig):
  dashboard/data/ess_de_personen.csv, ess_aggregate.csv, wahrnehmung_referenzwerte.csv
  output/t01_bund_zeitreihe_clean.csv, pks_hauptgruppen_2002-2025.csv,
  output/pks_aufklaerungsquoten_2025.csv, destatis_verurteilte.csv,
  output/pks_tatverdaechtige.csv, eurostat_vergleich.csv

Ausgabe: dashboard/index.html
"""
import pathlib

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from texte import TEXTE

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard/data"
OUT = ROOT / "dashboard/index.html"

# Okabe-Ito-Palette: farbenblind-tauglich und kontrastreich
BLUE = "#0072B2"      # Hellfeld / registrierte Fälle
VERM = "#D55E00"      # Furcht / Wahrnehmung (orangerot)
GREEN = "#009E73"     # Justiz / Aufklärung
PURPLE = "#CC79A7"    # Zusatzreihe
SAND = "#E69F00"      # Zusatzreihe
SKY = "#56B4E9"       # Zusatzreihe
DARK = "#1F2933"
SLATE = "#52606D"
GRID = "#D9DEE4"
FURCHT_FLAECHE = "rgba(213, 94, 0, 0.16)"
PALETTE = [BLUE, VERM, GREEN, PURPLE, SAND, SKY, "#7B8794"]


def load():
    return dict(
        ess=pd.read_csv(D / "ess_de_personen.csv"),
        agg=pd.read_csv(D / "ess_aggregate.csv", sep=";"),
        ref=pd.read_csv(D / "wahrnehmung_referenzwerte.csv", sep=";"),
        t01=pd.read_csv(ROOT / "output/t01_bund_zeitreihe_clean.csv"),
        hg=pd.read_csv(ROOT / "output/pks_hauptgruppen_2002-2025.csv"),
        aq=pd.read_csv(ROOT / "output/pks_aufklaerungsquoten_2025.csv"),
        ver=pd.read_csv(ROOT / "output/destatis_verurteilte.csv"),
        tv=pd.read_csv(ROOT / "output/pks_tatverdaechtige.csv"),
        eu=pd.read_csv(ROOT / "output/eurostat_vergleich.csv", sep=";"),
    )


DA = load()
pio.templates.default = "plotly_white"

BASE = dict(
    autosize=True,
    font=dict(family='system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
              size=13, color=DARK),
    margin=dict(l=10, r=34, t=44, b=56),
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
                font=dict(size=12), bgcolor="rgba(255,255,255,0)"),
    hoverlabel=dict(font_size=13, bgcolor="white", bordercolor=SLATE),
    plot_bgcolor="white", paper_bgcolor="white",
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=SLATE,
               tickfont=dict(size=12), title_font=dict(size=13)),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=SLATE,
               tickfont=dict(size=12), title_font=dict(size=13)),
)


def fig(height=400, **kw):
    f = go.Figure()
    f.update_layout(**BASE, height=height)
    if kw:
        f.update_layout(**kw)
    return f


def de(x, n=1):
    try:
        return f"{float(x):.{n}f}".replace(".", ",")
    except (TypeError, ValueError):
        return "–"


def tausender(x):
    return f"{int(round(x)):,}".replace(",", ".")


FIGUREN = []


def add(fid, f):
    FIGUREN.append((fid, f))


# ============================================================ 1 Hellfeld
def f_hellfeld_gesamt():
    g = DA["t01"][DA["t01"].schluessel == "------"].sort_values("jahr")
    f = fig(height=430, hovermode="x unified")
    f.add_trace(go.Scatter(x=g.jahr, y=g.faelle / 1e6, mode="lines",
                           name="Erfasste Fälle", line=dict(color=BLUE, width=3),
                           hovertemplate="%{x}: %{y:.2f} Mio Fälle<extra></extra>"))
    for j, lab in [(2011, "2011"), (2016, "2016")]:
        f.add_vline(x=j, line=dict(color="#B0B7C3", width=1, dash="dot"))
        f.add_annotation(x=j, y=7.45, text=lab, showarrow=False, xshift=30,
                         font=dict(size=12, color=SLATE))
    f.add_annotation(x=1993, y=6.75, text="1993: 6,75 Mio", showarrow=True, arrowhead=2,
                     arrowcolor=BLUE, ax=64, ay=-30, font=dict(size=12, color=BLUE))
    f.add_annotation(x=2021, y=5.05, text="2021: 5,05 Mio", showarrow=True, arrowhead=2,
                     arrowcolor=BLUE, ax=-104, ay=52, font=dict(size=12, color=BLUE))
    f.add_annotation(x=2025, y=5.51, text="2025: 5,51 Mio", showarrow=True, arrowhead=2,
                     arrowcolor=BLUE, ax=-74, ay=46, font=dict(size=12, color=BLUE))
    f.update_yaxes(title="Fälle (Mio.)", range=[0, 7.8], automargin=True,
                   tickvals=[0, 2, 4, 6], ticktext=["0", "2", "4", "6"])
    f.update_xaxes(dtick=4, automargin=True)
    return f


def f_hellfeld_gruppen():
    hg = DA["hg"].copy()
    base = hg[hg.jahr == 2002].set_index("gruppe").faelle
    hg["index"] = hg.apply(lambda r: r.faelle / base[r.gruppe] * 100, axis=1)
    order = [("Diebstahl (gesamt)", "Diebstahl", BLUE, "solid"),
             ("Vermögens- & Fälschungsdelikte", "Vermögen/Fälschung", SAND, "solid"),
             ("Rohheitsdelikte & Freiheit", "Rohheitsdelikte", VERM, "solid"),
             ("Sexuelle Selbstbestimmung", "Sexualdelikte", PURPLE, "dot"),
             ("Sonstige StGB", "Sonstige StGB", GREEN, "dash")]
    f = fig(height=490, hovermode="x unified")
    for g, lab, col, dash in order:
        d = hg[hg.gruppe == g].sort_values("jahr")
        f.add_trace(go.Scatter(x=d.jahr, y=d["index"], mode="lines", name=lab,
                               line=dict(color=col, width=2.8, dash=dash),
                               hovertemplate="%{y:.0f}<extra>" + lab + "</extra>"))
    f.add_hline(y=100, line=dict(color=SLATE, width=1, dash="dash"))
    f.add_annotation(x=2016, y=252, text="Ausgangsniveau 2002 = 100 (gestrichelte Linie)",
                     showarrow=False, font=dict(size=12, color=SLATE))
    f.update_yaxes(title="Index (2002 = 100)", automargin=True, rangemode="tozero")
    f.update_xaxes(dtick=2, automargin=True)
    return f


def f_eu():
    eu = DA["eu"][DA["eu"].iccs == "ICCS05012"].sort_values("jahr")
    f = fig(height=400, hovermode="x unified")
    f.add_trace(go.Scatter(x=eu.jahr, y=eu.eu_median, mode="lines+markers",
                           name="EU-Median der Vergleichsländer",
                           line=dict(color=SLATE, width=2.4, dash="dot"),
                           marker=dict(size=6),
                           hovertemplate="EU-Median %{x}: %{y:.1f}<extra></extra>"))
    f.add_trace(go.Scatter(x=eu.jahr, y=eu.de_rate, mode="lines+markers",
                           name="Deutschland",
                           line=dict(color=BLUE, width=3.2), marker=dict(size=7),
                           hovertemplate="DE %{x}: %{y:.1f}<extra></extra>"))
    f.add_annotation(x=2008, y=eu.de_rate.iloc[0], text="2008: 131,7", showarrow=True,
                     arrowhead=2, arrowcolor=BLUE, ax=34, ay=-30,
                     font=dict(size=12, color=BLUE))
    f.add_annotation(x=2024, y=eu.de_rate.iloc[-1], text="Deutschland 2024: 94,0",
                     showarrow=True, arrowhead=2, arrowcolor=BLUE, ax=-64, ay=-40,
                     font=dict(size=12, color=BLUE))
    f.update_yaxes(title="je 100.000 Einwohner", automargin=True, rangemode="tozero")
    f.update_xaxes(dtick=2, automargin=True)
    return f


# ============================================================ 2 Angst
def f_angst_zeitreihe():
    s = DA["agg"][(DA["agg"].ebene == "zeitreihe") &
                  (DA["agg"].gruppe == "gesamt")].sort_values("jahr")
    f = fig(height=430, hovermode="x unified")
    f.add_trace(go.Scatter(x=s.jahr, y=s.ki_hi, mode="lines", line=dict(width=0),
                           showlegend=False, hoverinfo="skip"))
    f.add_trace(go.Scatter(x=s.jahr, y=s.ki_lo, mode="lines", line=dict(width=0),
                           fill="tonexty", fillcolor=FURCHT_FLAECHE,
                           showlegend=False, hoverinfo="skip"))
    f.add_trace(go.Scatter(x=s.jahr, y=s.anteil, mode="lines+markers",
                           name="unsicher / sehr unsicher",
                           line=dict(color=VERM, width=3.2), marker=dict(size=8),
                           hovertemplate="%{x}: %{y:.1f} %<extra></extra>"))
    f.add_annotation(x=2014, y=22.0, text="Tief 2014: 22,0 %", showarrow=True, arrowhead=2,
                     arrowcolor=VERM, ax=-46, ay=56, font=dict(size=12, color=VERM))
    f.add_annotation(x=2016, y=27.2, text="Sprung 2016: 27,2 %", showarrow=True, arrowhead=2,
                     arrowcolor=VERM, ax=40, ay=-44, font=dict(size=12, color=VERM))
    f.update_yaxes(title="Anteil unsicher (%)", range=[16, 33], automargin=True,
                   tickvals=[18, 21, 24, 27, 30, 33],
                   ticktext=["18 %", "21 %", "24 %", "27 %", "30 %", "33 %"])
    f.update_xaxes(tickmode="array", tickvals=list(s.jahr), automargin=True)
    return f


def f_soep():
    """SOEP-Referenz nach DIW 2025: soziale Furcht (im Text genannte Werte) und
    die Korrelation mit den Kriminalitätsraten je Phase."""
    jahre = [2000, 2013, 2023]
    werte = [54, 31, 38]
    f = fig(height=390)
    f.add_trace(go.Bar(x=[f"{j}" for j in jahre], y=werte, marker_color=VERM,
                       width=0.5, name="große Sorgen",
                       text=[f"{w} %" for w in werte], textposition="outside",
                       textfont=dict(size=13, color=VERM),
                       hovertemplate="%{x}: %{y} %<extra></extra>"))
    f.update_yaxes(title="Anteil mit großen Sorgen (%)", range=[0, 66], automargin=True,
                   tickvals=[0, 20, 40, 60], ticktext=["0 %", "20 %", "40 %", "60 %"])
    f.add_annotation(x=0.5, y=1.16, xref="paper", yref="paper", showarrow=False,
                     xanchor="center",
                     text="Korrelation dieser Sorge mit den Kriminalitätsraten:<br>"
                          "2000–2013 r = 0,88 · 2014–2017 r = −0,71 · 2018–2023 r = 0,67",
                     font=dict(size=12, color=SLATE))
    f.update_layout(showlegend=False)
    return f


def f_furcht_anker():
    r = DA["ref"]
    fa = r[(r.kategorie == "furcht_affektiv") & (r.gruppe == "gesamt")]
    reihen = [("Wohnungseinbruch", "Wohnungseinbruch", "Wohnungseinbruchdiebstahl", VERM, "circle"),
              ("Körperverletzung", "Körperverletzung", "Körperverletzung", SAND, "square"),
              ("Raub", "Raub", "Raub", PURPLE, "diamond"),
              ("Terrorismus", "Terroranschlag", "Terroranschlag", GREEN, "triangle-up")]
    f = fig(height=420, hovermode="x unified")
    f.add_vrect(x0=2017.4, x1=2019.6, fillcolor="#EEF1F4", line_width=0)
    f.add_annotation(x=2018.5, y=33.2, text="Instrumentenwechsel DVS → SKiD", showarrow=False,
                     font=dict(size=12, color=SLATE))
    for dvs, label, skid, color, sym in reihen:
        sub = fa[fa.item.isin([dvs, skid])].sort_values("welle_jahr")
        f.add_trace(go.Scatter(x=sub.welle_jahr, y=sub.wert_pct, mode="lines+markers",
                               name=label, line=dict(color=color, width=2, dash="dot"),
                               marker=dict(size=11, symbol=sym, color=color),
                               hovertemplate="%{x}: %{y:.1f} %<extra>" + label + "</extra>"))
    f.update_yaxes(title="Anteil beunruhigt (%)", automargin=True, range=[0, 34],
                   tickvals=[0, 10, 20, 30], ticktext=["0 %", "10 %", "20 %", "30 %"])
    f.update_xaxes(tickmode="array", tickvals=[2012, 2017, 2020, 2024], automargin=True)
    return f


# ============================================================ 3 Deliktprofil
DELIKTE8 = ["Betrug im Internet", "Sachbeschädigung", "Wohnungseinbruch", "Diebstahl",
            "Körperverletzung", "Sexuelle Belästigung", "Terroranschlag",
            "Vorurteilskriminalität"]


def _ref(kategorie, item, jahr, gruppe="gesamt"):
    r = DA["ref"]
    s = r[(r.kategorie == kategorie) & (r.item == item) &
          (r.welle_jahr == jahr) & (r.gruppe == gruppe)]
    return float(s.wert_pct.iloc[0]) if len(s) else None


def f_furcht_delikte():
    items = sorted(DELIKTE8, key=lambda i: _ref("furcht_affektiv", i, 2024))
    v24 = [_ref("furcht_affektiv", i, 2024) for i in items]
    v20 = [_ref("furcht_affektiv", i, 2020) for i in items]
    f = fig(height=480, barmode="group", bargap=0.28, bargroupgap=0.08)
    f.add_trace(go.Bar(y=items, x=v20, orientation="h", name="2020",
                       marker_color=SKY, width=0.34,
                       hovertemplate="%{y}: %{x:.1f} %<extra>2020</extra>"))
    f.add_trace(go.Bar(y=items, x=v24, orientation="h", name="2024",
                       marker_color=VERM, width=0.34,
                       hovertemplate="%{y}: %{x:.1f} %<extra>2024</extra>"))
    f.update_xaxes(range=[0, 58], automargin=True,
                   tickvals=[0, 20, 40], ticktext=["0 %", "20 %", "40 %"])
    f.update_yaxes(automargin=True, tickfont=dict(size=12.5), ticks="outside", ticklen=6)
    return f


def f_furcht_vs_risiko():
    items = sorted(DELIKTE8, key=lambda i: _ref("furcht_affektiv", i, 2024))
    furcht = [_ref("furcht_affektiv", i, 2024) for i in items]
    risiko = [_ref("risiko_kognitiv", i, 2024) for i in items]
    f = fig(height=480)
    for i, it in enumerate(items):
        f.add_trace(go.Scatter(x=[risiko[i], furcht[i]], y=[it, it], mode="lines",
                               line=dict(color="#8B95A5", width=6), showlegend=False,
                               hoverinfo="skip"))
    f.add_trace(go.Scatter(x=risiko, y=items, mode="markers", name="Risikoeinschätzung",
                           marker=dict(color=GREEN, size=14, line=dict(width=1, color="white")),
                           hovertemplate="%{y}: %{x:.1f} %<extra>Risiko</extra>"))
    f.add_trace(go.Scatter(x=furcht, y=items, mode="markers", name="Furcht (Beunruhigung)",
                           marker=dict(color=VERM, size=14, symbol="diamond",
                                       line=dict(width=1, color="white")),
                           hovertemplate="%{y}: %{x:.1f} %<extra>Furcht</extra>"))
    f.update_xaxes(range=[0, 58], automargin=True,
                   tickvals=[0, 20, 40], ticktext=["0 %", "20 %", "40 %"])
    f.update_yaxes(automargin=True, tickfont=dict(size=12.5), ticks="outside", ticklen=6)
    return f


def f_furcht_vs_praevalenz():
    paare = [("Betrug im Internet", "Cyberkriminalität", "Internetbetrug"),
             ("Sachbeschädigung", "Sachbeschädigung", "Sachbeschädigung"),
             ("Wohnungseinbruch", "Wohnungseinbruchdiebstahl", "Einbruch"),
             ("Diebstahl", "Diebstahl", "Diebstahl"),
             ("Körperverletzung", "Körperverletzung", "Körperverletzung"),
             ("Sexuelle Belästigung", "Sexuelle Belästigung", "Sex. Belästigung")]
    furcht, praev, labels = [], [], []
    for a, b, lab in paare:
        furcht.append(_ref("furcht_affektiv", a, 2024))
        praev.append(_ref("praevalenz", b, None) or _ref("praevalenz", b, 2023))
        labels.append(lab)
    f = fig(height=430)
    mx = 62
    f.add_trace(go.Scatter(x=[0, 22], y=[0, 22], mode="lines", name="gleich hoch",
                           line=dict(color=SLATE, dash="dash", width=2), hoverinfo="skip"))
    f.add_annotation(x=20.5, y=50, text="Diagonale:<br>Furcht = Betroffenheit",
                     showarrow=False, font=dict(size=11.5, color=SLATE), align="left")
    f.add_trace(go.Scatter(x=praev, y=furcht, mode="markers+text", text=labels,
                           textposition="top center",
                           textfont=dict(size=12, color=DARK),
                           marker=dict(color=BLUE, size=15, line=dict(width=1, color="white")),
                           name="Delikt",
                           hovertemplate="%{text}<br>Betroffen: %{x:.1f} %<br>Furcht: %{y:.1f} %<extra></extra>"))
    f.update_xaxes(title="Selbst betroffen (letzte 12 Monate)", range=[0, 22], automargin=True,
                   tickvals=[0, 5, 10, 15, 20], ticktext=["0 %", "5 %", "10 %", "15 %", "20 %"])
    f.update_yaxes(title="Furcht (Beunruhigung)", range=[0, mx], automargin=True,
                   tickvals=[0, 20, 40, 60], ticktext=["0 %", "20 %", "40 %", "60 %"])
    return f


# ============================================================ 4 Wer fürchtet sich
def f_geschlecht():
    s = DA["agg"][DA["agg"].ebene == "zeitreihe_geschlecht"]
    f = fig(height=420, hovermode="x unified")
    for g, c, sym in [("Frauen", VERM, "circle"), ("Männer", BLUE, "square")]:
        d = s[s.gruppe == g].sort_values("jahr")
        f.add_trace(go.Scatter(x=d.jahr, y=d.anteil, mode="lines+markers", name=g,
                               line=dict(color=c, width=3), marker=dict(size=7, symbol=sym),
                               hovertemplate="%{x}: %{y:.1f} %<extra>" + g + "</extra>"))
    f.add_annotation(x=2012, y=36, text="Abstand rund 25 Prozentpunkte,<br>über 20 Jahre stabil",
                     showarrow=False, font=dict(size=12, color=SLATE), align="left")
    f.update_yaxes(title="Anteil unsicher (%)", range=[0, 46], automargin=True,
                   tickvals=[0, 10, 20, 30, 40], ticktext=["0 %", "10 %", "20 %", "30 %", "40 %"])
    f.update_xaxes(tickmode="array", tickvals=sorted(s.jahr.unique()), automargin=True)
    return f


def f_alter():
    s = DA["agg"][DA["agg"].ebene == "alter"]
    cols = {"16-29": PURPLE, "30-44": SAND, "45-59": GREEN, "60-74": BLUE, "75+": SLATE}
    f = fig(height=450, hovermode="x unified")
    for g in ["16-29", "30-44", "45-59", "60-74", "75+"]:
        d = s[s.gruppe == g].sort_values("jahr")
        f.add_trace(go.Scatter(x=d.jahr, y=d.anteil, mode="lines+markers", name=g,
                               line=dict(color=cols[g], width=2.4), marker=dict(size=6),
                               hovertemplate="%{x}, " + g + " Jahre: %{y:.1f} %<extra></extra>"))
    f.update_yaxes(title="Anteil unsicher (%)", range=[10, 55], automargin=True,
                   tickvals=[15, 25, 35, 45, 55],
                   ticktext=["15 %", "25 %", "35 %", "45 %", "55 %"])
    f.update_xaxes(tickmode="array", tickvals=sorted(s.jahr.unique()), automargin=True)
    return f


def f_struktur():
    a = DA["agg"]
    ebenen = ["bildung_gepoolt", "migration_gepoolt", "diskriminierung_gepoolt",
              "vertrauen_polizei_gepoolt", "wohnort_gepoolt", "struktur_gepoolt"]
    KURZ = {"nicht tertiär": "Bildung niedrig", "tertiär": "Bildung hoch (tertiär)",
            "mit Migrationshintergrund": "mit Migrationshintergrund",
            "ohne Migrationshintergrund": "ohne Migrationshintergrund",
            "diskriminiert (Selbstauskunft)": "diskriminiert (Selbstauskunft)",
            "nicht diskriminiert": "nicht diskriminiert",
            "hohes Polizeivertrauen": "Polizeivertrauen hoch",
            "niedriges Polizeivertrauen": "Polizeivertrauen niedrig",
            "Grossstadt": "Großstadt", "Kleinstadt": "Kleinstadt", "Vorort": "Vorort",
            "Dorf": "Dorf", "Land": "Land", "arbeitslos": "arbeitslos",
            "nicht arbeitslos": "nicht arbeitslos"}
    rows = []
    for k in ebenen:
        for _, r in a[a.ebene == k].iterrows():
            rows.append((KURZ.get(r.gruppe, r.gruppe), float(r.anteil), int(r.n)))
    rows.sort(key=lambda x: x[1])
    labels, vals, ns = [r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows]
    colors = [VERM if v > 28 else (BLUE if v < 20 else SAND) for v in vals]
    f = fig(height=560)
    f.add_trace(go.Bar(y=labels, x=vals, orientation="h", marker_color=colors,
                       customdata=ns, width=0.7, name="Anteil unsicher",
                       hovertemplate="%{y}: %{x:.1f} % (n = %{customdata})<extra></extra>"))
    f.update_xaxes(range=[0, 44], automargin=True,
                   tickvals=[0, 10, 20, 30, 40],
                   ticktext=["0 %", "10 %", "20 %", "30 %", "40 %"])
    f.update_yaxes(automargin=True, tickfont=dict(size=12.5), ticks="outside", ticklen=6)
    return f


def f_einstellungen():
    a = DA["agg"]
    KURZ = {"Polizeivertrauen": "Polizeivertrauen", "Parlamentsvertrauen": "Parlamentsvertrauen",
            "Sozialvertrauen": "Sozialvertrauen", "Regierungszufriedenheit": "Regierungszufriedenheit",
            "Lebenszufriedenheit": "Lebenszufriedenheit",
            "Demokratiezufriedenheit": "Demokratiezufriedenheit", "Glück": "Glück",
            "Einstellung Zuwanderung": "Zuwanderung (ablehnend/positiv)",
            "Gesundheit": "Gesundheit", "Einkommenslage": "Einkommenslage"}
    sub = a[a.ebene == "einstellung_gepoolt"].copy()
    sub["basis"] = sub.gruppe.str.extract(r"^(.*) \(")[0].map(KURZ)
    sub["lage"] = sub.gruppe.str.extract(r"\((.*)\)")
    piv = sub.pivot_table(index="basis", columns="lage", values="anteil").dropna()
    piv["diff"] = piv["niedrige Ausprägung"] - piv["hohe Ausprägung"]
    piv = piv.sort_values("diff", ascending=False)
    f = fig(height=520)
    for idx, r in piv.iterrows():
        f.add_trace(go.Scatter(x=[r["hohe Ausprägung"], r["niedrige Ausprägung"]], y=[idx, idx],
                               mode="lines", line=dict(color="#8B95A5", width=6),
                               showlegend=False, hoverinfo="skip"))
    f.add_trace(go.Scatter(x=piv["hohe Ausprägung"], y=piv.index, mode="markers",
                           name="hohe Ausprägung", marker=dict(color=GREEN, size=13),
                           hovertemplate="%{y}: %{x:.1f} %<extra>hoch</extra>"))
    f.add_trace(go.Scatter(x=piv["niedrige Ausprägung"], y=piv.index, mode="markers",
                           name="niedrige Ausprägung",
                           marker=dict(color=VERM, size=13, symbol="diamond"),
                           hovertemplate="%{y}: %{x:.1f} %<extra>niedrig</extra>"))
    f.update_xaxes(range=[0, 38], automargin=True,
                   tickvals=[0, 10, 20, 30], ticktext=["0 %", "10 %", "20 %", "30 %"])
    f.update_yaxes(automargin=True, tickfont=dict(size=12.5), ticks="outside", ticklen=6)
    return f


# ============================================================ 5 Verhalten
def f_vermeidung():
    v = DA["ref"][(DA["ref"].kategorie == "vermeidung") & (DA["ref"].welle_jahr == 2024)]
    items = ["Fremden ausweichen", "Wohnung bewohnt wirken lassen", "ÖPNV nachts meiden",
             "Straßen/Plätze/Parks meiden", "Nachts Haus nicht verlassen",
             "Haus nur in Begleitung verlassen", "Wohnung/Haus sichern",
             "Geldgeschäfte im Internet meiden", "Gegenstand zum Aufmerksammachen"]
    KURZ = {"Fremden ausweichen": "weicht Fremden aus",
            "Wohnung bewohnt wirken lassen": "lässt Wohnung bewohnt wirken",
            "ÖPNV nachts meiden": "meidet ÖPNV nachts",
            "Straßen/Plätze/Parks meiden": "meidet bestimmte Orte",
            "Nachts Haus nicht verlassen": "verlässt nachts das Haus nicht",
            "Haus nur in Begleitung verlassen": "geht nur in Begleitung",
            "Wohnung/Haus sichern": "sichert Wohnung/Haus",
            "Geldgeschäfte im Internet meiden": "meidet Online-Geldgeschäfte",
            "Gegenstand zum Aufmerksammachen": "führt Gegenstand mit"}

    def g(item, gruppe):
        s = v[(v.item == item) & (v.gruppe == gruppe)]
        return float(s.wert_pct.iloc[0]) if len(s) else None

    rows = sorted([(KURZ[i], g(i, "gesamt"), g(i, "Frauen")) for i in items], key=lambda x: x[1])
    labels = [r[0] for r in rows]
    ges = [r[1] for r in rows]
    fr = [r[2] for r in rows]
    f = fig(height=540)
    f.add_trace(go.Bar(y=labels, x=ges, orientation="h", name="gesamt", marker_color=BLUE,
                       width=0.62,
                       hovertemplate="%{y}: %{x:.1f} %<extra>gesamt</extra>"))
    f.add_trace(go.Scatter(x=fr, y=labels, mode="markers", name="Frauen",
                           marker=dict(color=VERM, size=13, symbol="diamond",
                                       line=dict(width=1, color="white")),
                           hovertemplate="%{y}: %{x:.1f} %<extra>Frauen</extra>"))
    f.update_xaxes(range=[0, 68], automargin=True,
                   tickvals=[0, 20, 40, 60], ticktext=["0 %", "20 %", "40 %", "60 %"])
    f.update_yaxes(automargin=True, tickfont=dict(size=12.5), ticks="outside", ticklen=6)
    return f


def f_sicherheit_orte():
    s = DA["ref"][(DA["ref"].kategorie == "sicherheit_nachts") & (DA["ref"].welle_jahr == 2024)]
    items = ["Wohngegend", "ÖPNV", "Straßen, Wege, Plätze", "Bahnhöfe", "Parks, Parkanlagen"]
    KURZ = {"Wohngegend": "eigene Wohngegend", "ÖPNV": "ÖPNV",
            "Straßen, Wege, Plätze": "Straßen und Plätze", "Bahnhöfe": "Bahnhöfe",
            "Parks, Parkanlagen": "Parks"}

    def g(item, gruppe):
        z = s[(s.item == item) & (s.gruppe == gruppe)]
        return float(z.wert_pct.iloc[0])

    labels = [KURZ[i] for i in items]
    ges = [g(i, "gesamt") for i in items]
    fr = [g(i, "Frauen") for i in items]
    ma = [g(i, "Männer") for i in items]
    f = fig(height=430)
    for i, it in enumerate(labels):
        f.add_trace(go.Scatter(x=[fr[i], ma[i]], y=[it, it], mode="lines",
                               line=dict(color="#8B95A5", width=6), showlegend=False,
                               hoverinfo="skip"))
    f.add_trace(go.Scatter(x=ges, y=labels, mode="markers", name="gesamt",
                           marker=dict(color=BLUE, size=15, line=dict(width=1, color="white")),
                           hovertemplate="%{y}: %{x:.1f} %<extra>gesamt</extra>"))
    f.add_trace(go.Scatter(x=fr, y=labels, mode="markers", name="Frauen",
                           marker=dict(color=VERM, size=13, symbol="diamond"),
                           hovertemplate="%{y}: %{x:.1f} %<extra>Frauen</extra>"))
    f.add_trace(go.Scatter(x=ma, y=labels, mode="markers", name="Männer",
                           marker=dict(color=GREEN, size=13, symbol="square"),
                           hovertemplate="%{y}: %{x:.1f} %<extra>Männer</extra>"))
    f.update_xaxes(range=[0, 92], automargin=True,
                   tickvals=[0, 25, 50, 75], ticktext=["0 %", "25 %", "50 %", "75 %"])
    f.update_yaxes(automargin=True, tickfont=dict(size=12.5), ticks="outside", ticklen=6)
    return f


# ============================================================ 6 Trichter
def _verurteilte(delikt, jahr=2024):
    v = DA["ver"][(DA["ver"].delikt == delikt) & (DA["ver"].jahr == jahr)]
    return float(v.verurteilte.iloc[0]) if len(v) else None


def f_trichter():
    aq = DA["aq"].set_index("schluessel")
    faelle = {k: float(aq.loc[k, "faelle"]) for k in ("****00", "435*00", "210000", "222000")}
    aufgeklaert = {k: float(aq.loc[k, "aufgeklaert"]) for k in faelle}
    verurteilt = {
        "****00": _verurteilte("Diebstahl (19. Abschnitt)"),
        "435*00": (_verurteilte("Einbruchdiebstahl (§ 243 Abs. 1 S. 2 Nr. 1)") or 0)
                  + (_verurteilte("Wohnungseinbruchdiebstahl (§ 244 Abs. 1 Nr. 3)") or 0)
                  + (_verurteilte("Schwerer Diebstahl/Banden (§ 244a)") or 0),
        "210000": _verurteilte("Raub und räuberische Erpressung (20. Abschnitt)"),
        "222000": _verurteilte("Körperverletzung"),
    }
    LAB = {"****00": "Diebstahl (gesamt)", "435*00": "Wohnungseinbruch",
           "210000": "Raub", "222000": "Körperverletzung"}
    keys = ["435*00", "210000", "222000", "****00"]
    f = fig(height=470, barmode="group", bargap=0.3, bargroupgap=0.06)
    stufen = [("registrierte Fälle (2025)", faelle, BLUE),
              ("davon aufgeklärt (2025)", aufgeklaert, GREEN),
              ("Verurteilungen (2024)", verurteilt, VERM)]
    for name, werte, col in stufen:
        f.add_trace(go.Bar(y=[LAB[k] for k in keys], x=[werte[k] for k in keys],
                           orientation="h", name=name, marker_color=col, width=0.26,
                           hovertemplate="%{y}: %{x:,.0f} (" + name + ")<extra></extra>"))
    f.update_xaxes(title="Fälle bzw. Personen (logarithmische Skala)", type="log",
                   range=[2, 6.6], automargin=True)
    f.update_yaxes(automargin=True, tickfont=dict(size=12.5), ticks="outside", ticklen=6)
    return f


def f_aufklaerung():
    aq = DA["aq"][DA["aq"].schluessel != "------"].copy().sort_values("aq")
    KURZ = {"Gefährliche Körperverletzung": "gefährliche Körperverletzung",
            "Vermögens- & Fälschungsdelikte": "Vermögen/Fälschung",
            "Sexuelle Selbstbestimmung": "Sexualdelikte",
            "Rohheitsdelikte & Freiheit": "Rohheitsdelikte",
            "Wohnungseinbruch (WED)": "Wohnungseinbruch"}
    labels = [KURZ.get(g, g) for g in aq.gruppe]
    colors = [VERM if v < 40 else (SAND if v < 80 else BLUE) for v in aq.aq]
    f = fig(height=490)
    f.add_trace(go.Bar(y=labels, x=aq.aq, orientation="h", marker_color=colors,
                       customdata=aq.faelle, width=0.7, name="Aufklärungsquote",
                       hovertemplate="%{y}: %{x:.1f} % (erfasste Fälle: %{customdata:,.0f})<extra></extra>"))
    f.add_vline(x=57.9, line=dict(color=SLATE, width=1.5, dash="dash"),
                annotation_text="alle Delikte: 57,9 %", annotation_position="top",
                annotation_font_size=12, annotation_font_color=SLATE)
    f.update_xaxes(range=[0, 112], automargin=True,
                   tickvals=[0, 25, 50, 75, 100],
                   ticktext=["0 %", "25 %", "50 %", "75 %", "100 %"])
    f.update_yaxes(automargin=True, tickfont=dict(size=12.5), ticks="outside", ticklen=6)
    return f


# ============================================================ 7 Tatverdächtige
def f_tv():
    tv = DA["tv"].sort_values("jahr")
    from plotly.subplots import make_subplots
    f = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.14,
                      subplot_titles=("Anteil nichtdeutscher Tatverdächtiger an allen Tatverdächtigen",
                                      "Tatverdächtigenbelastungszahl je 100.000 Einwohner der Gruppe"))
    f.add_trace(go.Scatter(x=tv.jahr, y=tv.anteil_nichtdeutsch_pct, mode="lines+markers",
                           name="Anteil nichtdeutsch", line=dict(color=VERM, width=3),
                           marker=dict(size=6),
                           hovertemplate="%{x}: %{y:.1f} %<extra></extra>"), row=1, col=1)
    f.add_trace(go.Scatter(x=tv.jahr, y=tv.tvbz_nichtdeutsch, mode="lines+markers",
                           name="nichtdeutsche Wohnbevölkerung",
                           line=dict(color=VERM, width=3), marker=dict(size=6),
                           hovertemplate="%{x}: %{y:,.0f}<extra></extra>"), row=2, col=1)
    f.add_trace(go.Scatter(x=tv.jahr, y=tv.tvbz_deutsch, mode="lines+markers",
                           name="deutsche Wohnbevölkerung",
                           line=dict(color=BLUE, width=3), marker=dict(size=6),
                           hovertemplate="%{x}: %{y:,.0f}<extra></extra>"), row=2, col=1)
    f.update_yaxes(title_text="Anteil", ticksuffix=" %", range=[15, 46], row=1, col=1)
    f.update_yaxes(title_text="TVBZ", row=2, col=1)
    f.update_xaxes(dtick=4, row=2, col=1)
    f.update_layout(**BASE, height=620)
    f.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.04, x=0, font=dict(size=12)))
    return f


# ============================================================ Aufbau
add("hellfeld", f_hellfeld_gesamt())
add("gruppen", f_hellfeld_gruppen())
add("eu", f_eu())
add("angst", f_angst_zeitreihe())
add("soep", f_soep())
add("anker", f_furcht_anker())
add("delikte", f_furcht_delikte())
add("risiko", f_furcht_vs_risiko())
add("praevalenz", f_furcht_vs_praevalenz())
add("geschlecht", f_geschlecht())
add("alter", f_alter())
add("struktur", f_struktur())
add("einstellungen", f_einstellungen())
add("vermeidung", f_vermeidung())
add("orte", f_sicherheit_orte())
add("trichter", f_trichter())
add("aufklaerung", f_aufklaerung())
add("tv", f_tv())

print(f"{len(FIGUREN)} Figuren gebaut")

# ------------------------------------------------------------------ HTML
CSS = """
:root{
 --blue:#0072B2; --verm:#D55E00; --green:#009E73; --dark:#1F2933; --slate:#52606D;
 --line:#DCE1E8; --bg:#F4F6F8; --card:#FFFFFF; --soft:#F8FAFC;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--dark);font-size:16.5px;line-height:1.62;
 font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:0 18px 64px}
header{background:linear-gradient(135deg,#0F3D5C 0%,#0072B2 100%);color:#fff;padding:34px 18px 30px}
header .inner{max-width:1120px;margin:0 auto}
header h1{margin:0 0 10px;font-size:clamp(1.35rem,4.6vw,2.15rem);line-height:1.2;
 letter-spacing:-0.01em}
header p{margin:0;font-size:clamp(.92rem,2.6vw,1.05rem);opacity:.95;max-width:66ch}
header .sub{margin-top:12px;font-size:.86rem;opacity:.85}
nav{position:sticky;top:0;z-index:50;background:#fff;border-bottom:1px solid var(--line);
 overflow-x:auto;-webkit-overflow-scrolling:touch;box-shadow:0 1px 3px rgba(31,41,51,.06)}
nav ul{display:flex;gap:4px;list-style:none;margin:0;padding:0 10px;white-space:nowrap}
nav a{display:block;padding:13px 10px;color:var(--blue);text-decoration:none;
 font-size:.88rem;font-weight:600}
nav a:hover{background:var(--soft)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(176px,1fr));gap:12px;margin:22px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:15px 16px;
 box-shadow:0 1px 3px rgba(31,41,51,.05)}
.kpi .v{font-size:clamp(1.35rem,5vw,1.85rem);font-weight:750;color:var(--blue);line-height:1.1;
 letter-spacing:-0.02em}
.kpi.warn .v{color:var(--verm)}
.kpi .l{font-size:.8rem;color:var(--slate);margin-top:5px;line-height:1.4}
section{background:var(--card);border:1px solid var(--line);border-radius:16px;
 padding:22px 20px 18px;margin:20px 0;box-shadow:0 1px 3px rgba(31,41,51,.05)}
section h2{font-size:clamp(1.06rem,3.4vw,1.32rem);margin:0 0 8px;line-height:1.3;
 letter-spacing:-0.01em}
section .lead{font-size:.95rem;color:#3E4C59;margin:0 0 18px}
.chart{width:100%;overflow:hidden;margin:4px 0 10px}
.chart .plotly-graph-div{width:100%!important}
.note{background:var(--soft);border-left:4px solid var(--blue);border-radius:0 10px 10px 0;
 padding:16px 18px;margin:22px 0 10px;font-size:.92rem;max-width:92ch}
.note p{margin:0 0 10px}
.note p:last-child{margin-bottom:0}
.note .lab{font-weight:700;color:var(--dark)}
.note .th{border-top:1px dashed var(--line);padding-top:12px;margin-top:12px}
.cite{color:var(--slate);font-size:.84rem}
.src{font-size:.83rem;color:var(--slate);margin:12px 0 2px;border-top:1px solid var(--line);
 padding-top:10px;line-height:1.55;max-width:92ch}
footer{color:var(--slate);font-size:.88rem;margin-top:28px;padding:22px;background:#fff;
 border:1px solid var(--line);border-radius:16px}
footer h3{margin:0 0 10px;color:var(--dark);font-size:1.02rem}
footer p{margin:10px 0}
footer ul{margin:8px 0 12px;padding-left:20px}
footer li{margin:5px 0}
details{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:12px 14px;
 margin:12px 0}
summary{cursor:pointer;font-weight:650;color:var(--blue);font-size:.92rem}
@media (max-width:640px){
 section{padding:17px 14px 14px;border-radius:14px}
 header{padding:26px 15px 22px}
 .note{font-size:.88rem;padding:12px 13px}
}
"""

nav_items = "".join(f'<li><a href="#{fid}">{TEXTE[fid]["titel"].split("·")[0].strip()}</a></li>'
                    for fid, _ in FIGUREN)

CONFIG = {"responsive": True, "displayModeBar": False, "displaylogo": False}
secs = []
for i, (fid, f) in enumerate(FIGUREN):
    t = TEXTE[fid]
    hoehe = int(f.layout.height or 400)
    fig_json = pio.to_json(f)
    teile = []
    if t.get("einordnung"):
        teile.append(f'<p><span class="lab">Einordnung.</span> {t["einordnung"]}</p>')
    if t.get("interpretation"):
        teile.append(f'<p class="th"><span class="lab">Interpretation.</span> {t["interpretation"]}</p>')
    if t.get("theorie"):
        teile.append(f'<p class="th"><span class="lab">Theorie und Evidenz.</span> {t["theorie"]}</p>')
    note = f'<div class="note">{"".join(teile)}</div>' if teile else ""
    src = f'<p class="src">Quellen: {t["quellen"]}</p>' if t.get("quellen") else ""
    secs.append(
        f'<section id="{fid}"><h2>{t["titel"]}</h2>'
        f'<p class="lead">{t["lead"]}</p>'
        f'<div class="chart" data-fig="fig-{fid}" style="min-height:{hoehe}px">'
        f'<noscript>Für dieses Diagramm ist JavaScript erforderlich.</noscript></div>'
        f'<script type="application/json" id="fig-{fid}">{fig_json}</script>'
        f'{note}{src}</section>')
body = "\n".join(secs)

HTML = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0F3D5C">
<title>Kriminalität und Kriminalitätsfurcht in Deutschland — Datenüberblick</title>
{{PLOTLY}}
<style>{CSS}</style>
</head>
<body>
<header><div class="inner">
  <h1>Kriminalität und Kriminalitätsfurcht in Deutschland</h1>
  <p>Die registrierte Kriminalität sinkt seit Jahrzehnten. Die Furcht tut das nicht.
  Dieser Überblick stellt beide Seiten nebeneinander — Hellfeld, Strafverfolgung,
  Befragungsdaten und die soziale Verteilung des Sicherheitsgefühls.</p>
  <p class="sub">Projekt 47 „Kriminalitätsdiskrepanz DE“ · Datenstand September&nbsp;2026 · alle Diagramme interaktiv, offline&nbsp;nutzbar</p>
</div></header>
<nav><ul>{nav_items}</ul></nav>
<div class="wrap">
  <div class="kpis">
    <div class="kpi"><div class="v">−18 %</div><div class="l">registrierte Fälle seit dem Höchststand 1993</div></div>
    <div class="kpi warn"><div class="v">25,0 %</div><div class="l">fühlen sich nachts beim Alleingehen unsicher (ESS 2023)</div></div>
    <div class="kpi warn"><div class="v">52,0 %</div><div class="l">fürchten Betrug im Internet&nbsp;(SKiD&nbsp;2024)</div></div>
    <div class="kpi warn"><div class="v">14,1 %</div><div class="l">Aufklärungsquote bei Wohnungseinbruch (PKS 2025)</div></div>
  </div>
{body}
<footer>
  <h3>Daten, Methodik, Grenzen</h3>
  <p><b>Hellfeld und Strafverfolgung:</b> BKA-Polizeiliche Kriminalstatistik (T01-Zeitreihe „Fälle ab
  1987“, T12 aufgeklärte Fälle, T20/T40/T50 Tatverdächtige, TVBZ ab 2009) und Destatis
  Strafverfolgungsstatistik (Statistische Berichte 2022–2024, Tabelle 24311-05). Registrierte Fälle
  sind polizeilich bekannt gewordene Ermittlungsvorgänge — kein Nachweis einer begangenen Straftat und
  keine Verurteilung. Verurteilte sind Personen, gezählt nach dem schwersten Delikt des Verfahrens,
  mit Zeitverzug zum Tatjahr.</p>
  <p><b>Befragungsdaten:</b> ESS-DE Runden 1–11 (2002–2023; Deutschland fehlt in Runde 10/2020), eigene
  Berechnung, Gewichtung pspwght, Konfidenzintervalle als Normalapproximation ohne Designeffekt.
  SKiD 2020/2024 und DVS 2012/2017 (BKA): Werte aus den Ergebnisberichten. SOEP-Zahlen zur sozialen
  Kriminalitätsfurcht: DIW Weekly Report 30/2025.</p>
  <p><b>Internationaler Vergleich:</b> Eurostat crim_off_cat (harmonisierte ICCS-Kategorien), Rate je
  100.000 Einwohner; Ländervergleichbarkeit durch unterschiedliche Erfassungsregeln begrenzt.</p>
  <details><summary>Bekannte Brüche und Fallstricke</summary>
  <ul>
    <li>PKS: Zählbereichsänderungen 2011 (Diebstahlskatalog), 2014 (Cybercrime), 2016 (Betrugskatalog),
    2017/2022 (Sexualstrafrecht), 2021 (Bedrohung § 241), 2024/25 (Cannabis); HZ-Basis ab 2024 Zensus 2022.</li>
    <li>Tatverdächtige: ab 2009 „echte“ Tatverdächtigenzählung — nicht mit Vorjahren vergleichbar.
    Die TVBZ setzt „ansässige“ Tatverdächtige ins Verhältnis zur jeweiligen Wohnbevölkerung; Touristen
    und Durchreisende fehlen im Nenner.</li>
    <li>DVS → SKiD 2020: Instrumentenwechsel; Werte über die Grenze nicht nahtlos vergleichbar.</li>
    <li>ESS: Item aesfdrk misst allgemeines Sicherheitsgefühl (nachts allein), nicht deliktsspezifische
    Furcht; Runde 11 mit verändertem Erhebungsmodus.</li>
    <li>Gruppenvergleiche im ESS sind bivariat und unadjustiert; die Kategorie „Land“ hat sehr kleine
    Fallzahlen.</li>
    <li>Verurteilungszahlen und PKS-Fälle sind unterschiedliche Einheiten und Jahre — der Trichter zeigt
    Größenordnungen, keine exakten Quoten.</li>
  </ul>
  </details>
  <p>Alle Werte dieses Dashboards sind aus den im Projekt gespeicherten Primärquellen berechnet;
  die Skripte liegen unter <code>scripts/01</code>–<code>09</code>, die Datenbasis unter
  <code>dashboard/data/</code>.</p>
</footer>
</div>
</body>
</html>"""

# ------------------------------------------------------------------ Ausgabe
# Zwei Varianten:
#   index.html      — Plotly.js eingebettet (offline nutzbar, ca. 5 MB)
#   index_cdn.html  — Plotly.js vom CDN (ca. 0,3 MB, für die Zustellung aufs
#                     Handy gedacht; braucht beim Öffnen Internet)
from plotly.offline import get_plotlyjs

import plotly as _plotly
JS_VERSION = _plotly.__version__

PLOTLY_TAGS = {
    "index.html": '<script charset="utf-8">' + get_plotlyjs() + "</script>",
    "index_cdn.html": ('<script charset="utf-8" '
                       f'src="https://cdn.plot.ly/plotly-3.0.1.min.js"></script>'),
}

# Lazy-Rendering: 18 interaktive Plotly-Diagramme gleichzeitig überfordern
# mobile Browser (Speicher, Rendering, Hover-Layer). Deshalb wird jedes
# Diagramm erst gezeichnet, wenn es in den Sichtbereich scrollt.
LAZY_SCRIPT = """
<script>
(function () {
  var CONF = {responsive: true, displayModeBar: false, displaylogo: false,
              scrollZoom: false, doubleClick: false,
              modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d']};

  function render(el) {
    if (el.dataset.state) return;
    el.dataset.state = 'laeuft';
    var quelle = document.getElementById(el.getAttribute('data-fig'));
    if (!quelle || !window.Plotly) { delete el.dataset.state; return; }
    var f;
    try { f = JSON.parse(quelle.textContent); }
    catch (e) { el.innerHTML = '<p style="color:#B22222">Diagramm konnte nicht geladen werden.</p>'; return; }
    var lay = f.layout || {};
    lay.autosize = true;
    if (window.innerWidth < 520) {
      lay.height = Math.min(lay.height || 400, 320);
      if (lay.margin) { lay.margin.l = Math.min(lay.margin.l || 10, 10);
                        lay.margin.r = Math.min(lay.margin.r || 10, 14); }
    }
    window.Plotly.newPlot(el, f.data, lay, CONF).then(function () {
      el.dataset.state = 'fertig';
      el.style.minHeight = '';
    }).catch(function () { delete el.dataset.state; });
  }

  function alle() {
    document.querySelectorAll('.chart[data-fig]').forEach(render);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var charts = document.querySelectorAll('.chart[data-fig]');
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (eintraege) {
        eintraege.forEach(function (e) {
          if (e.isIntersecting) { render(e.target); io.unobserve(e.target); }
        });
      }, {rootMargin: '400px 0px'});
      charts.forEach(function (c) { io.observe(c); });
    } else {
      alle();
    }
    // Nachlauf: falls der Beobachter nichts meldet (z. B. Druck oder alte
    // Browser), spätestens nach 3 Sekunden alles rendern.
    setTimeout(function () {
      document.querySelectorAll('.chart[data-fig]:not([data-state])').forEach(render);
    }, 3000);
  });

  window.addEventListener('resize', function () {
    if (!window.Plotly) return;
    document.querySelectorAll('.js-plotly-plot').forEach(function (d) {
      try { window.Plotly.Plots.resize(d); } catch (e) {}
    });
  });
})();
</script>
"""

for dateiname, tag in PLOTLY_TAGS.items():
    ziel = ROOT / "dashboard" / dateiname
    html = HTML.replace("{PLOTLY}", tag) + LAZY_SCRIPT
    ziel.write_text(html, encoding="utf-8")
    print(f"{dateiname}: {ziel.stat().st_size/1e6:.2f} MB (Plotly.js {JS_VERSION})")
