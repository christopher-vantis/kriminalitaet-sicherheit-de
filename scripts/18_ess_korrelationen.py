#!/usr/bin/env python3
"""
18_ess_korrelationen.py — Explorative Zusammenhangsanalyse (ESS Deutschland)
============================================================================
Schritt 1 der Ursachenannäherung: Welche Merkmale hängen überhaupt mit
Kriminalitätsfurcht und Viktimisierung zusammen? Bivariat, ohne Kontrolle —
das Ergebnis ist eine Landkarte möglicher Spuren, kein Wirkungsnachweis.

Daten: dashboard/data/ess_de_personen.csv (ESS Deutschland, Runden 1-11)
Ausgabe:
  output/korrelationen_unsicher.csv     — Rangkorrelation mit der Furcht
  output/korrelationen_matrix.csv       — vollständige Matrix (Spearman)
  output/korrelationen_stabilitaet.csv  — Korrelation je Welle (Stabilitätsprüfung)

Methodik:
  - Spearman-Rangkorrelation (robust gegen Ausreißer, verlangt keine
    Normalverteilung, erlaubt ordinale Merkmale).
  - Paarweiser Fallausschluss; Fallzahlen werden mitberichtet.
  - Zusätzlich je Welle gerechnet, um zu prüfen, ob ein Zusammenhang stabil ist
    oder nur durch eine einzelne Erhebung zustande kommt.
  - Hinweis: Korrelation ist keine Kausalität; ohne Kontrolle von Drittvariablen
    ist jede dieser Zahlen eine Vermutung mit Adresse (Schritt 2 prüft nach).
"""
import pathlib

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard/data"
OUT = ROOT / "output"

# Lesbare Beschriftungen und Rollen der Variablen
VARIABLEN = {
    # Zielgrößen
    "unsicher": ("Unsicherheitsgefühl (Furcht)", "ziel"),
    "viktim": ("Viktimisierung (Haushalt, 12 Mon.)", "ziel"),
    # Soziodemografie
    "geschlecht_f": ("Frau (vs. Mann)", "struktur"),
    "agea_c": ("Alter (Jahre)", "struktur"),
    "tertiaer": ("tertiäre Bildung", "struktur"),
    "eisced_c": ("Bildungsjahre/Stufe (ISCED)", "struktur"),
    "hinc": ("Haushaltseinkommen (Dezile)", "struktur"),
    "hincfel_c": ("Einkommenslage (Selbsteinschätzung)", "struktur"),
    "mh": ("Migrationshintergrund", "struktur"),
    "stadt_land_num": ("Wohnort: Stadt (1) bis Land (5)", "struktur"),
    "diskriminiert": ("Diskriminierungserfahrung", "struktur"),
    "uempla_c": ("Arbeitslosigkeit (12 Mon.)", "struktur"),
    "health_c": ("Gesundheitszustand", "struktur"),
    # Einstellungen und Vertrauen
    "ppltrst_c": ("Sozialvertrauen", "einstellung"),
    "trstplc_c": ("Vertrauen in die Polizei", "einstellung"),
    "trstprl_c": ("Vertrauen in das Parlament", "einstellung"),
    "trstlgl_c": ("Vertrauen in die Justiz", "einstellung"),
    "trstplt_c": ("Vertrauen in Politiker", "einstellung"),
    "stfgov_c": ("Zufriedenheit mit der Regierung", "einstellung"),
    "stfdem_c": ("Zufriedenheit mit der Demokratie", "einstellung"),
    "stflife_c": ("Lebenszufriedenheit", "einstellung"),
    "happy_c": ("Glück", "einstellung"),
    "lrscale_c": ("politische Orientierung (rechts hoch)", "einstellung"),
    "imwbcnt_c": ("Zuwanderung: gut für das Land", "einstellung"),
    "imsmetn_c": ("Zuwanderung: kulturelle Bereicherung", "einstellung"),
    "impcntr_c": ("Zuwanderung: schlecht für die Wirtschaft (umgepolt)", "einstellung"),
    "clsprty": ("Parteibindung", "einstellung"),
    "polintr_c": ("politisches Interesse", "einstellung"),
    "news_min": ("Nachrichtenminuten (nur R8-R11)", "medien"),
}

MIN_N = 300          # Mindestfallzahl für eine berichtete Korrelation


def lade():
    df = pd.read_csv(D / "ess_de_personen.csv", low_memory=False)
    # Frau als 0/1 (Referenz Mann), Wohnort ordinalskaliert 1=Stadt .. 5=Land
    df["geschlecht_f"] = (df["geschlecht"].astype(str).str.strip() == "Frau").astype(float)
    df.loc[~df["geschlecht"].astype(str).str.strip().isin(["Frau", "Mann"]), "geschlecht_f"] = np.nan
    ordnung = {"Grossstadt": 1, "Vorort": 2, "Kleinstadt": 3, "Dorf": 4, "Land": 5}
    df["stadt_land_num"] = df["stadt_land"].map(ordnung)
    return df


def korr(df, a, b):
    """Spearman-Korrelation mit Fallzahl und p-Wert (paarweiser Ausschluss)."""
    d = df[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(d) < MIN_N or d[a].nunique() < 2 or d[b].nunique() < 2:
        return None
    r, p = stats.spearmanr(d[a], d[b])
    return len(d), r, p


def main():
    df = lade()
    print(f"Datenbasis: {len(df):,} Personen, Runden {sorted(df['essround'].unique())}")
    print(f"Variablen im Modell: {len(VARIABLEN)}\n")

    # ---------- 1) Korrelation aller Merkmale mit der Furcht ----------
    zeilen = []
    for var, (label, rolle) in VARIABLEN.items():
        if var == "unsicher" or var not in df.columns:
            continue
        for ziel in ("unsicher", "viktim"):
            if ziel == var:
                continue
            r = korr(df, var, ziel)
            if not r:
                continue
            n, rho, p = r
            zeilen.append(dict(ziel=ziel, variable=var, label=label, rolle=rolle,
                               n=n, spearman=round(rho, 4), p_wert=p,
                               abs_r=abs(rho)))
    kor = pd.DataFrame(zeilen).sort_values(["ziel", "abs_r"], ascending=[True, False])
    # Mehrfachtestung: Bei ~60 Tests je Zielgröße ist ein p < 0,05 allein wenig wert.
    # Benjamini-Hochberg kontrolliert die erwartete Quote falscher Treffer (FDR).
    for ziel in kor.ziel.unique():
        m = kor.ziel == ziel
        kor.loc[m, "q_wert"] = multipletests(kor.loc[m, "p_wert"], method="fdr_bh")[1]
    kor["signifikant_fdr"] = np.where(kor.q_wert < 0.05, "ja", "nein")
    kor.to_csv(OUT / "korrelationen_unsicher.csv", index=False, sep=";")

    for ziel, name in [("unsicher", "UNSICHERHEITSGEFÜHL (Furcht)"),
                       ("viktim", "VIKTIMISIERUNG (Haushalt)")]:
        print(f"=== Zusammenhänge mit: {name} ===  (Sterne ab FDR-korrigiertem q < 0,05)")
        t = kor[kor.ziel == ziel]
        for _, r in t.iterrows():
            stern = "***" if r.q_wert < 0.001 else "**" if r.q_wert < 0.01 else "*" if r.q_wert < 0.05 else "n.s."
            print(f"  {r['label']:48s} {r.spearman:+6.3f} {stern:5s} "
                  f"(n={int(r.n):>5d}, q={r.q_wert:.1e}) [{r.rolle}]")
        print()

    # ---------- 2) Vollständige Matrix (für die Heatmap) ----------
    spalten = [v for v in VARIABLEN if v in df.columns]
    m = df[spalten].apply(pd.to_numeric, errors="coerce")
    mat = m.corr(method="spearman", min_periods=MIN_N)
    mat.round(4).to_csv(OUT / "korrelationen_matrix.csv", sep=";")
    # Fallzahlen zur Matrix (für die Bewertung kleiner Zellen)
    n_mat = m.notna().astype(int).T.dot(m.notna().astype(int))
    n_mat.to_csv(OUT / "korrelationen_matrix_n.csv", sep=";")
    print(f"Matrix geschrieben: {mat.shape[0]}x{mat.shape[1]} Variablen")

    # ---------- 3) Stabilität über die Wellen ----------
    stab = []
    for var, (label, rolle) in VARIABLEN.items():
        if var in ("unsicher", "viktim") or var not in df.columns:
            continue
        for runde, g in df.groupby("essround"):
            r = korr(g, var, "unsicher")
            if r:
                stab.append(dict(variable=var, label=label, runde=int(runde),
                                 jahr=int(g["jahr"].iloc[0]), n=r[0],
                                 spearman=round(r[1], 4)))
    st = pd.DataFrame(stab)
    st.to_csv(OUT / "korrelationen_stabilitaet.csv", index=False, sep=";")

    print("\n=== Stabilität: Zusammenhänge mit der Furcht über die Wellen ===")
    for var in ["viktim", "diskriminiert", "ppltrst_c", "trstplc_c", "mh", "tertiaer",
                "stadt_land_num", "agea_c", "geschlecht_f", "hincfel_c"]:
        t = st[st.variable == var]
        if t.empty:
            continue
        label = VARIABLEN[var][0]
        werte = " ".join(f"{r.spearman:+.2f}" for _, r in t.iterrows())
        vorzeichen = set(np.sign(t.spearman.dropna()))
        urteil = "stabil" if len(vorzeichen) == 1 else "wechselt das Vorzeichen"
        print(f"  {label:44s} {werte}   -> {urteil}")
    print("\nVorzeichenfolge je Welle ist die eigentliche Prüfung: Ein nur in einer "
          "Welle auftretender Zusammenhang ist eine Spur, kein Befund.")


if __name__ == "__main__":
    main()
