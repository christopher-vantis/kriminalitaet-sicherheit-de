#!/usr/bin/env python3
"""
20_ess_moderation_mediation.py — Wann (Moderation) und wie (Mediation) wirken
=============================================================================
Schritt 3 und 4 der Ursachenannäherung.

MODERATION — wirkt ein Merkmal bei verschiedenen Gruppen unterschiedlich stark?
Geprüft werden Interaktionen, die theoriegeleitet plausibel sind:
  - Geschlecht × Viktimisierung   (reagieren Frauen stärker auf eigene Betroffenheit?)
  - Geschlecht × Alter            (kumuliert sich Vulnerabilität?)
  - Geschlecht × Sozialvertrauen  (wirkt Vertrauen bei Frauen anders?)
  - Bildung × Einkommen           (verstärken sich Ressourcen gegenseitig?)
  - Wohnort × Sozialvertrauen     (ist Vertrauen auf dem Land wichtiger?)
Berichtet wird der Interaktionskoeffizient (Logit-Skala) und der Likelihood-
Ratio-Test gegen das Modell ohne Interaktion — plus die Zahl der Modellfreiheits-
grade, damit Mehrfachtestung erkennbar bleibt.

MEDIATION — läuft ein Zusammenhang über eine dritte Größe?
Geprüft werden drei Pfade, jeweils mit Bootstrap-Konfidenzintervall (5000 Züge,
Perzentilmethode) für den indirekten Effekt a·b:
  1) Diskriminierungserfahrung → Sozialvertrauen → Furcht
  2) Bildung                  → Sozialvertrauen → Furcht
  3) Viktimisierung           → Vertrauen in die Justiz → Furcht
Für die Mediation wird ein lineares Wahrscheinlichkeitsmodell geschätzt (OLS);
das ist für die Zerlegung üblich und leichter interpretierbar als Logit-Koeffizienten.

Ausgabe:
  output/moderation.csv
  output/mediation.csv
"""
import pathlib
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
rng = np.random.default_rng(20260910)

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard/data"
OUT = ROOT / "output"

STD = ["agea_c", "eisced_c", "hinc", "ppltrst_c", "trstplc_c", "trstlgl_c",
       "stfdem_c", "imwbcnt_c", "health_c", "stadt_land_num"]

BESCHRIFTUNG = {
    "geschlecht_f": "Frau (vs. Mann)", "agea_c_z": "Alter", "eisced_c_z": "Bildung",
    "hinc_z": "Einkommen", "ppltrst_c_z": "Sozialvertrauen",
    "trstlgl_c_z": "Vertrauen Justiz", "stadt_land_num_z": "Wohnort (Land hoch)",
    "viktim": "Viktimisierung", "diskriminiert": "Diskriminierung",
    "health_c_z": "Gesundheit (schlecht hoch)", "mh": "Migrationshintergrund",
    "hincfel_c": "Einkommenslage", "imwbcnt_c_z": "Zuwanderung gut fürs Land",
}

KONTROLLEN = ("geschlecht_f + agea_c_z + eisced_c_z + hinc_z + hincfel_c + mh + "
              "stadt_land_num_z + health_c_z + uempla_c + viktim + diskriminiert")


def lade():
    df = pd.read_csv(D / "ess_de_personen.csv", low_memory=False)
    df["geschlecht_f"] = (df["geschlecht"].astype(str).str.strip() == "Frau").astype(float)
    df.loc[~df["geschlecht"].astype(str).str.strip().isin(["Frau", "Mann"]), "geschlecht_f"] = np.nan
    df["stadt_land_num"] = df["stadt_land"].map(
        {"Grossstadt": 1, "Vorort": 2, "Kleinstadt": 3, "Dorf": 4, "Land": 5})
    for v in STD:
        if v in df.columns:
            x = pd.to_numeric(df[v], errors="coerce")
            df[v + "_z"] = (x - x.mean()) / x.std()
    for v in ["unsicher", "tertiaer", "mh", "diskriminiert", "uempla_c", "viktim"]:
        df[v] = pd.to_numeric(df[v], errors="coerce")
    return df


def fit(df, formel):
    teile = [t.strip() for t in formel.replace("*", "+").replace("~", "+").split("+")]
    variablen = [t for t in teile if t in df.columns]
    d = df.dropna(subset=list(dict.fromkeys(variablen + ["unsicher"]))).copy()
    m = smf.logit(formel, data=d).fit(disp=0)
    return m, d


def moderation(df):
    print("=== MODERATION: Wirkt der Zusammenhang in Gruppen unterschiedlich? ===\n")
    INTERAKTIONEN = [
        ("geschlecht_f * viktim", "Geschlecht × Viktimisierung"),
        ("geschlecht_f * agea_c_z", "Geschlecht × Alter"),
        ("geschlecht_f * ppltrst_c_z", "Geschlecht × Sozialvertrauen"),
        ("eisced_c_z * hinc_z", "Bildung × Einkommen"),
        ("stadt_land_num_z * ppltrst_c_z", "Wohnort × Sozialvertrauen"),
    ]
    zeilen = []
    for term, name in INTERAKTIONEN:
        basis = KONTROLLEN
        mit = KONTROLLEN + " + " + term
        try:
            m0, d0 = fit(df, "unsicher ~ " + basis)
            m1, d1 = fit(df, "unsicher ~ " + mit)
        except Exception as exc:                                     # noqa: BLE001
            print(f"  {name}: nicht schätzbar ({type(exc).__name__}: {exc})\n")
            continue
        lr = 2 * (m1.llf - m0.llf)
        df_diff = m1.df_model - m0.df_model
        from scipy import stats as st
        p = st.chi2.sf(lr, df_diff) if df_diff > 0 else np.nan
        # Interaktionskoeffizient
        inter = [k for k in m1.params.index if ":" in k]
        k0 = inter[0] if inter else None
        b = m1.params[k0] if k0 else np.nan
        se = m1.bse[k0] if k0 else np.nan
        zeilen.append(dict(interaktion=name, n=int(m1.nobs), lr_chi2=round(lr, 3),
                           df=df_diff, p_wert=p, koeffizient=round(b, 4),
                           se=round(se, 4),
                           signifikant="ja" if p < 0.05 else "nein"))
        print(f"  {name:34s} LR-χ²={lr:7.2f} (df={df_diff})  p={p:.4f}  "
              f"b={b:+.3f}  -> {'SIGNIFIKANT' if p < 0.05 else 'kein Unterschied'}")

    t = pd.DataFrame(zeilen)
    t.to_csv(OUT / "moderation.csv", index=False, sep=";")

    # ---------- Vorhergesagte Wahrscheinlichkeiten für die Darstellung ----------
    # Für jede signifikante Interaktion: P(unsicher) über die Ausprägungen der
    # einen Variable, getrennt nach der anderen.
    kurven = []

    def kurve(formel, xvar, gruppe, werte_x, werte_g):
        try:
            m, d = fit(df, "unsicher ~ " + formel)
        except Exception:                                            # noqa: BLE001
            return
        for g in werte_g:
            for x in werte_x:
                zeile = {v: d[v].mean() for v in d.columns
                         if v.endswith("_z") or v in ("hincfel_c", "mh", "uempla_c",
                                                      "viktim", "diskriminiert")}
                zeile[gruppe] = g
                zeile[xvar] = x
                try:
                    pr = float(m.predict(pd.DataFrame([zeile]))[0]) * 100
                    kurven.append(dict(interaktion=f"{gruppe} x {xvar}", gruppe=str(g),
                                       x=float(x), p_prozent=round(pr, 2)))
                except Exception:                                    # noqa: BLE001
                    continue

    kontrollen = ("agea_c_z + eisced_c_z + hinc_z + hincfel_c + mh + stadt_land_num_z + "
                  "health_c_z + uempla_c + viktim + diskriminiert")
    # Geschlecht x Alter
    kurve("geschlecht_f + " + kontrollen + " + geschlecht_f * agea_c_z",
          "agea_c_z", "geschlecht_f", [-1.5, -0.75, 0, 0.75, 1.5, 2.25], [0.0, 1.0])
    # Geschlecht x Sozialvertrauen
    kurve("geschlecht_f + " + kontrollen + " + geschlecht_f * ppltrst_c_z",
          "ppltrst_c_z", "geschlecht_f", [-2, -1, 0, 1, 2], [0.0, 1.0])
    # Wohnort x Sozialvertrauen
    kurve("stadt_land_num_z + " + kontrollen + " + stadt_land_num_z * ppltrst_c_z",
          "ppltrst_c_z", "stadt_land_num_z", [-2, -1, 0, 1, 2], [1.0, 3.0, 5.0])
    if kurven:
        pd.DataFrame(kurven).to_csv(OUT / "moderation_kurven.csv", index=False, sep=";")
        print(f"  Vorhersagekurven: {len(kurven)} Punkte -> output/moderation_kurven.csv")
    print(f"\n  Hinweis: {len(zeilen)} Interaktionen geprüft — bei 5 % Irrtumswahrscheinlichkeit"
          f" ist rein zufällig etwa ein Treffer in 20 Tests zu erwarten.")
    return t


def mediation(df, x, mediator, name, kontrollen, ziehungen=1000):
    """Indirekter Effekt a·b mit Bootstrap-Perzentilintervall (OLS-Pfade)."""
    variablen = [v for v in [x, mediator] + kontrollen if v in df.columns]
    d = df.dropna(subset=variablen + ["unsicher"]).copy()
    if len(d) < 2000:
        return None
    formel_a = f"{mediator} ~ {x} + " + " + ".join(kontrollen)
    formel_b = f"unsicher ~ {mediator} + {x} + " + " + ".join(kontrollen)
    ma = smf.ols(formel_a, data=d).fit()
    mb = smf.ols(formel_b, data=d).fit()
    a = ma.params[x]
    b = mb.params[mediator]
    c_strich = mb.params[x]
    indirekt = a * b
    total = smf.ols(f"unsicher ~ {x} + " + " + ".join(kontrollen), data=d).fit().params[x]

    # Bootstrap über Zeilen (Perzentilmethode)
    verteilung = []
    n = len(d)
    for _ in range(ziehungen):
        idx = rng.integers(0, n, n)
        s = d.iloc[idx]
        try:
            aa = smf.ols(formel_a, data=s).fit().params[x]
            bb = smf.ols(formel_b, data=s).fit().params[mediator]
            verteilung.append(aa * bb)
        except Exception:                                            # noqa: BLE001
            continue
    lo, hi = np.percentile(verteilung, [2.5, 97.5])
    print(f"  {name}")
    print(f"    a ({x} -> {mediator})            {a:+.4f}")
    print(f"    b ({mediator} -> Furcht)          {b:+.4f}")
    print(f"    totaler Effekt c                 {total:+.4f}")
    print(f"    direkter Effekt c'               {c_strich:+.4f}")
    print(f"    indirekter Effekt a·b            {indirekt:+.5f}  "
          f"[95 %: {lo:+.5f}, {hi:+.5f}]  n={n:,}")
    anteil = indirekt / total * 100 if total else np.nan
    print(f"    Anteil am Gesamteffekt           {anteil:+.1f} %")
    print(f"    -> {'bedeutsam (Intervall ohne 0)' if lo * hi > 0 else 'nicht abgesichert (Intervall enthält 0)'}\n")
    return dict(pfad=name, x=x, mediator=mediator, n=n, a=round(a, 4), b=round(b, 4),
                total=round(total, 4), direkt=round(c_strich, 4),
                indirekt=round(indirekt, 5), ki_lo=round(lo, 5), ki_hi=round(hi, 5),
                anteil_pct=round(anteil, 1) if anteil == anteil else None,
                abgesichert="ja" if lo * hi > 0 else "nein")


def main():
    df = lade()
    print(f"Datenbasis: {len(df):,} Personen\n")
    moderation(df)

    print("=== MEDIATION: Läuft der Zusammenhang über eine dritte Größe? ===\n")
    kontrollen = ["geschlecht_f", "agea_c_z", "eisced_c_z", "hinc_z", "hincfel_c",
                  "mh", "stadt_land_num_z", "health_c_z"]
    zeilen = []
    for x, med, name in [
        ("diskriminiert", "ppltrst_c_z", "Diskriminierung -> Sozialvertrauen -> Furcht"),
        ("eisced_c_z", "ppltrst_c_z", "Bildung -> Sozialvertrauen -> Furcht"),
        ("viktim", "trstlgl_c_z", "Viktimisierung -> Vertrauen Justiz -> Furcht"),
        ("imwbcnt_c_z", "ppltrst_c_z", "Zuwanderungseinstellung -> Sozialvertrauen -> Furcht"),
    ]:
        k = [c for c in kontrollen if c != x]
        r = mediation(df, x, med, name, k)
        if r:
            zeilen.append(r)
    if zeilen:
        pd.DataFrame(zeilen).to_csv(OUT / "mediation.csv", index=False, sep=";")
        print(f"-> {OUT/'mediation.csv'}")


if __name__ == "__main__":
    main()
