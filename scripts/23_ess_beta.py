#!/usr/bin/env python3
"""
23_ess_beta.py — Effektgrößen in Standardabweichungen (β)
=========================================================
Die bisherigen Tabellen berichteten mittlere marginale Effekte in Prozentpunkten.
Das ist korrekt, aber ungewohnt und schwer zu vergleichen. Hier wird dasselbe
Modell in der vertrauten Einheit gerechnet: standardisierte Koeffizienten β.

Was β bedeutet:
  β = 0,30 heißt: Steigt ein Merkmal um eine Standardabweichung, verschiebt sich
  die vorhergesagte Größe um 0,30 Standardabweichungen. β ist damit unabhängig
  von der Maßeinheit des Merkmals (Euro, Jahre, Skalenpunkte) und erlaubt den
  direkten Vergleich der Merkmale untereinander.

Zwei Wege zum selben Ziel:
  (a) Lineares Wahrscheinlichkeitsmodell (OLS auf die 0/1-Variable): Die
      Koeffizienten sind direkt in Anteilen der Standardabweichung lesbar.
      Nachteil: Die Gerade kann vorhergesagte Werte unter 0 oder über 1 erzeugen.
  (b) Logistische Regression mit standardisierten Koeffizienten. Da die Logit-
      Skala keine natürliche Streuung hat, wird sie über die logistische
      Verteilung normiert (SD = π/√3 ≈ 1,8138).
Beide werden berichtet. Weichen sie stark voneinander ab, ist das ein Zeichen
dafür, dass die Linearitätsannahme des linearen Modells nicht trägt.

Achtung bei binären Merkmalen (Frau, Migrationshintergrund, Viktimisierung):
Ihre Standardabweichung ist √(p(1−p)), also klein bei seltenen Merkmalen. Ein
kleines β heißt dort nicht „unwichtig", sondern „kommt selten vor". Für solche
Merkmale sind die Prozentpunkt-Angaben aus Skript 19 die bessere Sprache.

Ausgabe: output/beta_koeffizienten.csv
"""
import pathlib

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard/data"
OUT = ROOT / "output"

SD_LOGISTISCH = np.pi / np.sqrt(3)          # ≈ 1,8138

BESCHRIFTUNG = {
    "geschlecht_f": "Frau (statt Mann)",
    "agea_c": "Alter",
    "eisced_c": "Bildung (ISCED)",
    "hinc": "Haushaltseinkommen",
    "hincfel_c": "Einkommenslage (schwierig hoch)",
    "mh": "Migrationshintergrund",
    "stadt_land_num": "Wohnort (Stadt bis Land)",
    "health_c": "Gesundheit (schlechter hoch)",
    "uempla_c": "Arbeitslosigkeit (12 Monate)",
    "diskriminiert": "Diskriminierungserfahrung",
    "viktim": "Viktimisierung (Haushalt)",
    "ppltrst_c": "Sozialvertrauen",
    "trstplc_c": "Vertrauen in die Polizei",
    "trstlgl_c": "Vertrauen in die Justiz",
    "trstprl_c": "Vertrauen in das Parlament",
    "stfdem_c": "Zufriedenheit mit der Demokratie",
    "imwbcnt_c": "Zuwanderung: gut für das Land",
    "imsmetn_c": "Zuwanderung: kulturell bereichernd",
    "lrscale_c": "politische Orientierung (rechts hoch)",
    "stflife_c": "Lebenszufriedenheit",
}

# Gruppen in der Reihenfolge der Modelle (wie Skript 19)
MODELLE = {
    "M1": ["geschlecht_f", "agea_c", "eisced_c", "hinc", "hincfel_c", "mh", "stadt_land_num"],
    "M2": ["health_c", "uempla_c", "diskriminiert", "viktim"],
    "M3": ["ppltrst_c", "trstplc_c", "trstlgl_c", "trstprl_c", "stfdem_c",
           "imwbcnt_c", "imsmetn_c", "lrscale_c"],
}
BINÄR = {"geschlecht_f", "mh", "diskriminiert", "viktim", "uempla_c"}


def lade():
    df = pd.read_csv(D / "ess_de_personen.csv", low_memory=False)
    df["geschlecht_f"] = (df["geschlecht"].astype(str).str.strip() == "Frau").astype(float)
    df.loc[~df["geschlecht"].astype(str).str.strip().isin(["Frau", "Mann"]), "geschlecht_f"] = np.nan
    df["stadt_land_num"] = df["stadt_land"].map(
        {"Grossstadt": 1, "Vorort": 2, "Kleinstadt": 3, "Dorf": 4, "Land": 5})
    for v in ["unsicher", "tertiaer", "mh", "diskriminiert", "uempla_c", "viktim"]:
        df[v] = pd.to_numeric(df[v], errors="coerce")
    return df


def z(df, v):
    x = pd.to_numeric(df[v], errors="coerce")
    return (x - x.mean()) / x.std()


def main():
    df = lade()
    basis = MODELLE["M1"]
    ergebnisse = []

    print("β = Änderung in Standardabweichungen der Furcht je Standardabweichung des Merkmals")
    print("(bzw. je Wechsel 0→1 bei Merkmalen, die nur ja/nein kennen)\n")

    for modellname, zusatzliste in [("M1", []),
                                    ("M2", MODELLE["M2"]),
                                    ("M3", MODELLE["M2"] + MODELLE["M3"])]:
        variablen = basis + zusatzliste
        d = df[["unsicher"] + variablen].dropna().copy()
        for v in variablen:
            d[v + "_z"] = z(d, v)
        d["unsicher_z"] = z(d, "unsicher")

        formel = "unsicher_z ~ " + " + ".join(v + "_z" for v in variablen)
        m_lpm = smf.ols(formel, data=d).fit()
        formel_logit = "unsicher ~ " + " + ".join(v + "_z" for v in variablen)
        m_logit = smf.logit(formel_logit, data=d).fit(disp=0)

        print(f"--- {modellname} (n = {len(d):,}) ---")
        for v in variablen:
            beta_lpm = m_lpm.params[v + "_z"]
            b_logit = m_logit.params[v + "_z"]
            beta_logit = b_logit / SD_LOGISTISCH
            art = "binär" if v in BINÄR else "stetig"
            ergebnisse.append(dict(modell=modellname, variable=v,
                                   label=BESCHRIFTUNG.get(v, v), art=art,
                                   beta_lpm=round(beta_lpm, 4),
                                   beta_logit=round(beta_logit, 4),
                                   b_logit=round(b_logit, 4),
                                   sd_x=round(float(d[v + "_z"].std()), 4),
                                   n=len(d)))
        r2 = m_lpm.rsquared
        print(f"    R² (linear) = {r2:.3f} | Pseudo-R² (logistisch) = "
              f"{1 - m_logit.llf / m_logit.llnull:.3f}")
        for _, r in pd.DataFrame(ergebnisse).query("modell == @modellname") \
                .reindex(pd.DataFrame(ergebnisse).query("modell == @modellname")
                         .beta_lpm.abs().sort_values(ascending=False).index).iterrows():
            stern = "" if r.art == "binär" else ""
            print(f"      {r.label:40s} β = {r.beta_lpm:+.3f}  "
                  f"(logistisch {r.beta_logit:+.3f}){stern}")
        print()

    pd.DataFrame(ergebnisse).to_csv(OUT / "beta_koeffizienten.csv", index=False, sep=";")
    print(f"-> {OUT/'beta_koeffizienten.csv'}")
    print("\nHinweis: Bei den als 'binär' gekennzeichneten Merkmalen bedeutet β den")
    print("Unterschied zwischen den beiden Gruppen, gemessen in Standardabweichungen")
    print("der Furcht. Da ihre Streuung klein ist, fällt β dort kleiner aus als die")
    print("tatsächliche Bedeutung — die Prozentpunkt-Angaben aus Skript 19 sind für")
    print("solche Merkmale die anschaulichere Sprache.")


if __name__ == "__main__":
    main()
