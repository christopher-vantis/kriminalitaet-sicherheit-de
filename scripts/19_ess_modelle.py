#!/usr/bin/env python3
"""
19_ess_modelle.py — Multivariate Modelle mit Kontrollvariablen (ESS Deutschland)
================================================================================
Schritt 2: Halten die bivariaten Zusammenhänge der Kontrolle stand?

Vorgehen: verschachtelte logistische Regressionen auf das Unsicherheitsgefühl.
Jedes Modell nimmt eine Gruppe von Erklärungen hinzu; beobachtet wird, welche
Koeffizienten stabil bleiben und welche verschwinden. Zusätzlich werden mittlere
marginale Effekte (AME) berichtet — sie sind in Prozentpunkten lesbar und
hängen nicht von der Skalierung der Prädiktoren ab.

  M1  Soziodemografie        (Frau, Alter, Bildung, Einkommen, Migrationshintergrund, Wohnort)
  M2  + Vulnerabilität       (Gesundheit, Arbeitslosigkeit, Diskriminierung, Viktimisierung)
  M3  + Einstellungen        (Sozialvertrauen, Institutionen, Zuwanderung, Politik, Medien)
  M4  + Wellen-Kontrolle     (Dummy je Erhebungswelle — nimmt den Zeitgeist heraus)
  M5  + Länder-Kontrolle     (Bundesland, sofern erhoben; Cluster für die Standardfehler)

Ausgabe:
  output/modelle_ame.csv        — mittlere marginale Effekte je Modell
  output/modelle_guete.csv      — Fallzahl, Pseudo-R², AUC je Modell

Methodik und Grenzen:
  - Standardfehler cluster-robust nach Bundesland (die Furcht ist räumlich
    korreliert; ohne Clusterung werden die Fehler zu klein).
  - Listenweiser Ausschluss fehlender Werte; die Fallzahl sinkt dadurch deutlich.
    Das ist keine Missing-at-random-Annahme — sie wird ausgewiesen, nicht versteckt.
  - Es wird ausdrücklich KEINE Kausalität behauptet: Die Modelle zeigen, welche
    Zusammenhänge unter Kontrolle anderer Merkmale bestehen bleiben.
"""
import pathlib
import re
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard/data"
OUT = ROOT / "output"

# Standardisierung: kontinuierliche Prädiktoren auf Mittelwert 0, SD 1,
# damit die Koeffizienten vergleichbar groß werden.
STD = ["agea_c", "eisced_c", "hinc", "ppltrst_c", "trstplc_c", "trstprl_c",
       "trstlgl_c", "stfdem_c", "stflife_c", "lrscale_c", "imwbcnt_c",
       "imsmetn_c", "health_c", "news_min", "stadt_land_num"]

BESCHRIFTUNG = {
    "geschlecht_f": "Frau (vs. Mann)",
    "agea_c_z": "Alter (je SD)",
    "eisced_c_z": "Bildung ISCED (je SD)",
    "tertiaer": "tertiäre Bildung",
    "hinc_z": "Haushaltseinkommen (je SD)",
    "hincfel_c": "Einkommenslage (schwierig hoch)",
    "mh": "Migrationshintergrund",
    "stadt_land_num_z": "Wohnort (Land hoch)",
    "diskriminiert": "Diskriminierungserfahrung",
    "uempla_c": "Arbeitslosigkeit (12 Mon.)",
    "health_c_z": "Gesundheit (schlecht hoch)",
    "viktim": "Viktimisierung (Haushalt)",
    "ppltrst_c_z": "Sozialvertrauen (je SD)",
    "trstplc_c_z": "Vertrauen Polizei (je SD)",
    "trstlgl_c_z": "Vertrauen Justiz (je SD)",
    "trstprl_c_z": "Vertrauen Parlament (je SD)",
    "stfdem_c_z": "Demokratiezufriedenheit (je SD)",
    "imwbcnt_c_z": "Zuwanderung gut fürs Land (je SD)",
    "imsmetn_c_z": "Zuwanderung kulturell bereichernd (je SD)",
    "lrscale_c_z": "politisch rechts (je SD)",
    "news_min_z": "Nachrichtenminuten (je SD)",
}


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
    df["welle_f"] = df["essround"].astype("category")
    df["land_f"] = df["region"].astype("category")
    for v in ["unsicher", "tertiaer", "mh", "diskriminiert", "uempla_c", "viktim"]:
        df[v] = pd.to_numeric(df[v], errors="coerce")
    df["gew"] = pd.to_numeric(df["w"], errors="coerce")
    return df


MODELLE = {
    "M1 Soziodemografie": [
        "geschlecht_f", "agea_c_z", "eisced_c_z", "hinc_z", "hincfel_c", "mh",
        "stadt_land_num_z"],
    "M2 + Vulnerabilität": [
        "geschlecht_f", "agea_c_z", "eisced_c_z", "hinc_z", "hincfel_c", "mh",
        "stadt_land_num_z", "health_c_z", "uempla_c", "diskriminiert", "viktim"],
    "M3 + Einstellungen": [
        "geschlecht_f", "agea_c_z", "eisced_c_z", "hinc_z", "hincfel_c", "mh",
        "stadt_land_num_z", "health_c_z", "uempla_c", "diskriminiert", "viktim",
        "ppltrst_c_z", "trstplc_c_z", "trstlgl_c_z", "trstprl_c_z", "stfdem_c_z",
        "imwbcnt_c_z", "imsmetn_c_z", "lrscale_c_z"],
    "M4 + Wellen": None,       # M3 + Wellen-Dummies
    "M5 + Bundesland": None,   # Länder-Festeffekte, Cluster nach Bundesland
}


def schaetze(df, formel, cluster=None):
    """GLM-Logit; Standardfehler cluster-robust, wenn ein Cluster angegeben ist.

    Listenweiser Ausschluss über ALLE Modellvariablen — sonst bleiben Zeilen mit
    fehlenden Prädiktoren im Datensatz und die Vorhersagen enthalten NaN.
    """
    variablen = [t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formel) if t in df.columns]
    d = df.dropna(subset=variablen).copy()
    if cluster:
        d = d[d[cluster].notna()]
    modell = smf.glm(formel, data=d, family=sm.families.Binomial())
    if cluster:
        m = modell.fit(cov_type="cluster", cov_kwds={"groups": d[cluster].astype(str)})
    else:
        m = modell.fit()
    return m, d


def ame_tabelle(m, d):
    """Mittlere marginale Effekte (in Prozentpunkten) je Regressor."""
    try:
        marge = m.get_margeff(at="overall", dummy=True)
    except Exception as exc:                       # noqa: BLE001
        print("   AME nicht berechenbar (", type(exc).__name__, ")")
        return pd.DataFrame()
    # Spaltennamen dynamisch auflösen — sie unterscheiden sich zwischen
    # statsmodels-Versionen ("dy/dx", "Std. Err.", "P>|z|").
    sf = marge.summary_frame()

    def spalte(*teile):
        for c in sf.columns:
            klein = str(c).lower()
            if all(t in klein for t in teile):
                return c
        return None

    c_ame = spalte("dy/dx") or spalte("dy")
    c_se = spalte("err")
    c_p = spalte("p>") or spalte("p>|z|")
    c_z = spalte("z")
    if c_ame is None or c_se is None:
        print("   AME-Spalten nicht gefunden:", list(sf.columns))
        return pd.DataFrame()

    idx = [str(i) for i in sf.index]
    t = pd.DataFrame({
        "variable": [i.split("[")[0] for i in idx],
        "detail": idx,
        "ame_pp": np.asarray(sf[c_ame].values, dtype=float) * 100,
        "se_pp": np.asarray(sf[c_se].values, dtype=float) * 100,
        "z": np.asarray(sf[c_z].values, dtype=float) if c_z else np.nan,
        "p": np.asarray(sf[c_p].values, dtype=float) if c_p else np.nan,
    })
    # Dummy-Variablen tauchen je Ausprägung auf und werden zusammengefasst
    t = (t.groupby(["variable", "detail"], as_index=False)
           .agg(ame_pp=("ame_pp", "first"), se_pp=("se_pp", "first"),
                z=("z", "first"), p=("p", "first")))
    t["label"] = t["variable"].map(BESCHRIFTUNG).fillna(t["variable"])
    t["ki_lo"] = t["ame_pp"] - 1.96 * t["se_pp"]
    t["ki_hi"] = t["ame_pp"] + 1.96 * t["se_pp"]
    return t[["label", "variable", "detail", "ame_pp", "se_pp", "z", "p", "ki_lo", "ki_hi"]]


def main():
    df = lade()
    print(f"Datenbasis: {len(df):,} Personen\n")

    alle_ame, guete = [], []
    basis = MODELLE["M1 Soziodemografie"]

    for name, extra in MODELLE.items():
        if name.startswith("M4"):
            regressoren = MODELLE["M3 + Einstellungen"] + ["C(welle_f)"]
            cluster = None
        elif name.startswith("M5"):
            # Länder-Festeffekte: nur Variation INNERHALB der Länder zählt.
            # Wellen-Dummies entfallen hier, sonst ist die Matrix singulär.
            regressoren = MODELLE["M3 + Einstellungen"] + ["C(land_f)"]
            cluster = "land_f"
            df = df[df["region"].notna()] if "region" in df.columns else df
        else:
            regressoren = extra
            cluster = "land_f" if name.startswith("M5") else None

        formel = "unsicher ~ " + " + ".join(regressoren)
        try:
            m, d = schaetze(df, formel, cluster=cluster)
        except Exception as exc:                                     # noqa: BLE001
            print(f"{name}: Schätzung fehlgeschlagen — {exc}\n")
            continue

        pr = m.predict(d)
        auc = roc_auc_score(d["unsicher"], pr) if d["unsicher"].nunique() == 2 else float("nan")
        # McFadden-Pseudo-R²: 1 - logLik / logLik(Nullmodell)
        try:
            r2 = 1 - m.llf / m.llnull
        except Exception:                                    # noqa: BLE001
            r2 = float("nan")
        guete.append(dict(modell=name, n=int(m.nobs), ereignisse=int(d["unsicher"].sum()),
                          pseudo_r2_mcfadden=round(r2, 4), auc=round(auc, 4),
                          aic=round(m.aic, 1)))
        print(f"{name}: n={int(m.nobs):,} | Pseudo-R²={r2:.4f} | AUC={auc:.4f}")

        t = ame_tabelle(m, d)
        if not t.empty:
            t["modell"] = name
            alle_ame.append(t)

            if name.startswith("M3"):
                print("   (AME in Prozentpunkten, sortiert)")
                for _, r in t.reindex(t.ame_pp.abs().sort_values(ascending=False).index).head(10).iterrows():
                    stern = "***" if r.p < 0.001 else "**" if r.p < 0.01 else "*" if r.p < 0.05 else ""
                    print(f"     {r.label:42s} {r.ame_pp:+6.2f} PP {stern:3s} "
                          f"[{r.ki_lo:+5.2f}, {r.ki_hi:+5.2f}]")
        print()

    # ---------- Robustheit: dasselbe Modell mit ESS-Gewichten ----------
    print("=== Robustheitsprüfung: Modell M3 mit Stichprobengewichten ===")
    formel = "unsicher ~ " + " + ".join(MODELLE["M3 + Einstellungen"])
    try:
        d = df.dropna(subset=[t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formel)
                              if t in df.columns]).copy()
        d = d[d["gew"].notna() & (d["gew"] > 0)]
        m_gew = smf.glm(formel, data=d, family=sm.families.Binomial(),
                        freq_weights=d["gew"]).fit(cov_type="cluster",
                                                   cov_kwds={"groups": d["land_f"].astype(str)}
                                                   if d["land_f"].notna().any() else None)
        ungew = [t for t in alle_ame if t["modell"].str.startswith("M3")]
        print(f"  gewichtete Schätzung: n={int(m_gew.nobs):,}, "
              f"Pseudo-R²={1 - m_gew.llf / m_gew.llnull:.4f}")
        print("  Vorzeichenvergleich der Koeffizienten (gewichtet vs. ungewichtet):")
        k_gew = m_gew.params
        for var in MODELLE["M3 + Einstellungen"]:
            if var in k_gew.index:
                print(f"    {BESCHRIFTUNG.get(var.replace('_z','')+'_z', var):42s} "
                      f"{k_gew[var]:+.4f}")
    except Exception as exc:                                          # noqa: BLE001
        print("  gewichtete Schätzung nicht möglich:", type(exc).__name__, exc)
    print()

    if alle_ame:
        pd.concat(alle_ame).to_csv(OUT / "modelle_ame.csv", index=False, sep=";")
    pd.DataFrame(guete).to_csv(OUT / "modelle_guete.csv", index=False, sep=";")
    print(f"-> {OUT/'modelle_ame.csv'}\n-> {OUT/'modelle_guete.csv'}")


if __name__ == "__main__":
    main()
