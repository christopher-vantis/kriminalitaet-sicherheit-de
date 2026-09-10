#!/usr/bin/env python3
"""
21_mediation_vergleich.py — Drei Verfahren für denselben indirekten Effekt
==========================================================================
Die Pfadkoeffizienten (a, b, c, c') stammen aus gewöhnlichen OLS-Regressionen.
Erklärungsbedürftig ist allein das KONFIDENZINTERVALL des Produkts a·b: Der
Standardfehler eines Produkts ist nicht aus den Einzelfehlern ablesbar, und die
Verteilung von a·b ist bei kleinen Effekten schief — ein symmetrisches
±1,96·SE-Intervall wäre falsch.

Deshalb wird hier dasselbe Ergebnis auf drei Wegen berechnet:
  1) Sobel-Test          — Delta-Methode ohne Kovarianz (das alte Standardverfahren,
                           bekannt dafür, zu konservativ zu sein)
  2) Delta-Methode       — mit Kovarianz, wie sie Strukturgleichungsmodelle liefern
  3) Bootstrap           — nichtparametrisch, 5000 Ziehungen (Referenz)

Die Gegenüberstellung zeigt, ob die Wahl des Verfahrens den Schluss verändert.

Datenvorbereitung schreibt den Analyse-Datensatz für das lavaan-Skript (R).
Ausgabe: output/mediation_vergleich.csv, output/analyse_datensatz.csv
"""
import pathlib

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard/data"
OUT = ROOT / "output"
rng = np.random.default_rng(20260910)

STD = ["agea_c", "eisced_c", "hinc", "ppltrst_c", "trstlgl_c", "imwbcnt_c",
       "health_c", "stadt_land_num"]
KONTROLLEN = ["geschlecht_f", "agea_c_z", "eisced_c_z", "hinc_z", "hincfel_c", "mh",
              "stadt_land_num_z", "health_c_z"]

def lade_und_exportiere():
    df = pd.read_csv(D / "ess_de_personen.csv", low_memory=False)
    df["geschlecht_f"] = (df["geschlecht"].astype(str).str.strip() == "Frau").astype(float)
    df.loc[~df["geschlecht"].astype(str).str.strip().isin(["Frau", "Mann"]), "geschlecht_f"] = np.nan
    df["stadt_land_num"] = df["stadt_land"].map(
        {"Grossstadt": 1, "Vorort": 2, "Kleinstadt": 3, "Dorf": 4, "Land": 5})
    for v in STD:
        x = pd.to_numeric(df[v], errors="coerce")
        df[v + "_z"] = (x - x.mean()) / x.std()
    for v in ["unsicher", "mh", "diskriminiert", "uempla_c", "viktim"]:
        df[v] = pd.to_numeric(df[v], errors="coerce")
    spalten = ["unsicher", "diskriminiert", "viktim", "eisced_c_z", "imwbcnt_c_z",
               "ppltrst_c_z", "trstlgl_c_z"] + KONTROLLEN
    spalten = list(dict.fromkeys(spalten))
    d = df[spalten].dropna()
    d.to_csv(OUT / "analyse_datensatz.csv", index=False)
    print(f"Analyse-Datensatz: {len(d):,} Fälle -> output/analyse_datensatz.csv")
    return df


def sobel(a, sa, b, sb):
    """Delta-Methode ohne Kovarianz (klassischer Sobel-Test)."""
    se = np.sqrt(a ** 2 * sb ** 2 + b ** 2 * sa ** 2)
    z = (a * b) / se
    from scipy import stats as st
    p = 2 * (1 - st.norm.cdf(abs(z)))
    return a * b, se, z, p


def delta_mit_kovarianz(a, sa, b, sb, cov):
    """Delta-Methode mit Kovarianz der beiden Pfade (SEM-Variante)."""
    se = np.sqrt(a ** 2 * sb ** 2 + b ** 2 * sa ** 2 + 2 * a * b * cov)
    z = (a * b) / se
    from scipy import stats as st
    p = 2 * (1 - st.norm.cdf(abs(z)))
    return a * b, se, z, p


def bootstrap(d, formel_a, formel_b, x, mediator, ziehungen=5000):
    werte = []
    n = len(d)
    for _ in range(ziehungen):
        s = d.iloc[rng.integers(0, n, n)]
        try:
            a = smf.ols(formel_a, data=s).fit().params[x]
            b = smf.ols(formel_b, data=s).fit().params[mediator]
            werte.append(a * b)
        except Exception:                                            # noqa: BLE001
            continue
    return np.percentile(werte, [2.5, 97.5])


def main():
    df = lade_und_exportiere()

    PFADE = [
        ("diskriminiert", "ppltrst_c_z", "Diskriminierung -> Sozialvertrauen -> Furcht"),
        ("eisced_c_z", "ppltrst_c_z", "Bildung -> Sozialvertrauen -> Furcht"),
        ("viktim", "trstlgl_c_z", "Viktimisierung -> Vertrauen Justiz -> Furcht"),
        ("imwbcnt_c_z", "ppltrst_c_z", "Zuwanderungseinstellung -> Sozialvertrauen -> Furcht"),
    ]

    print(f"\n{'Pfad':44s} {'Verfahren':12s} {'Effekt':>9s} {'SE':>8s} {'95-%-Intervall':>22s}")
    print("-" * 100)
    zeilen = []
    for x, med, name in PFADE:
        kontrollen = [k for k in KONTROLLEN if k != x]
        ka = " + ".join(kontrollen)
        formel_a = f"{med} ~ {x} + {ka}"
        formel_b = f"unsicher ~ {med} + {x} + {ka}"

        teile = [x, med] + kontrollen + ["unsicher"]
        d = df[teile].dropna()
        ma = smf.ols(formel_a, data=d).fit()
        mb = smf.ols(formel_b, data=d).fit()
        a, sa = ma.params[x], ma.bse[x]
        b, sb = mb.params[med], mb.bse[med]

        # Kovarianz der beiden Koeffizienten: über Bootstrap-Samples schätzen
        n = len(d)
        paare = []
        for _ in range(400):
            s = d.iloc[rng.integers(0, n, n)]
            try:
                paare.append((smf.ols(formel_a, data=s).fit().params[x],
                              smf.ols(formel_b, data=s).fit().params[med]))
            except Exception:                                        # noqa: BLE001
                continue
        pp = np.array(paare)
        cov = float(np.cov(pp[:, 0], pp[:, 1])[0, 1]) if len(pp) > 10 else 0.0

        eff_s, se_s, z_s, p_s = sobel(a, sa, b, sb)
        eff_d, se_d, z_d, p_d = delta_mit_kovarianz(a, sa, b, sb, cov)
        lo_b, hi_b = bootstrap(d, formel_a, formel_b, x, med)

        for verfahren, eff, se, lo, hi, p in [
            ("Sobel", eff_s, se_s, eff_s - 1.96 * se_s, eff_s + 1.96 * se_s, p_s),
            ("Delta", eff_d, se_d, eff_d - 1.96 * se_d, eff_d + 1.96 * se_d, p_d),
            ("Bootstrap", eff_s, np.nan, lo_b, hi_b, np.nan),
        ]:
            print(f"{name[:43]:44s} {verfahren:12s} {eff:+9.5f} "
                  f"{('%.5f' % se) if se == se else '    —  ':>8s} "
                  f"[{lo:+.5f}, {hi:+.5f}]")
            zeilen.append(dict(pfad=name, verfahren=verfahren, n=len(d),
                               effekt=round(eff, 5),
                               se=round(se, 5) if se == se else None,
                               ki_lo=round(lo, 5), ki_hi=round(hi, 5),
                               p_wert=round(p, 6) if p == p else None,
                               abgesichert="ja" if lo * hi > 0 else "nein"))
        print()

    pd.DataFrame(zeilen).to_csv(OUT / "mediation_vergleich.csv", index=False, sep=";")
    print(f"-> {OUT/'mediation_vergleich.csv'}")
    print("\nLesart: Kommen alle drei Verfahren zum gleichen Schluss, hängt das "
          "Ergebnis nicht an der Methode. Der Sobel-Test ist bekannt dafür, "
          "konservativer zu sein (kleinere Teststärke).")


if __name__ == "__main__":
    main()
