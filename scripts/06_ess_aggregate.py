#!/usr/bin/env python3
"""
06_ess_aggregate.py — ESS-DE-Aggregate für Dashboard und Prüfung
================================================================
Liest dashboard/data/ess_de_personen.csv und erzeugt gewichtete Anteile
(Gewicht w = pspwght) des Unsicherheitsgefühls (aesfdrk 3/4) sowie
Viktimisierungsanteile. Ausgabe: dashboard/data/ess_aggregate.csv (long).

Polung: Alle hier verwendeten Skalen werden VOR der Auswertung so gedreht,
dass hohe Werte = "mehr des Konstrukts in der Labelsrichtung" bedeuten.
Explizit umgedreht (Originalcodierung in Klammern):
- health_c 1=very good ... 5=very bad  ->  health_pos = 6 - health_c
- hincfel_c 1=comfortable ... 4=very difficult -> hincfel_pos = 5 - hincfel_c
Alle übrigen: 0/1-codiert oder bereits so gepolt, dass höher = besser
im Label (z. B. imwbcnt 0=schlecht fürs Land ... 10=gut fürs Land).

KI: Normalapproximation ohne Designeffekt — als Näherung gekennzeichnet.
"""
import pathlib
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
IN = ROOT / "dashboard/data/ess_de_personen.csv"
OUT = ROOT / "dashboard/data/ess_aggregate.csv"

df = pd.read_csv(IN)
print(f"Personen: {len(df)} | Wellen: {sorted(df.jahr.unique())}")

# --- Polung korrigieren -----------------------------------------------------
df["health_pos"] = 6 - df["health_c"]        # höher = besserer Gesundheitszustand
df["hincfel_pos"] = 5 - df["hincfel_c"]      # höher = leichtere Einkommenslage

rows = []


def wshare(g, var, w="w"):
    d = g.dropna(subset=[var, w])
    if len(d) == 0 or d[w].sum() == 0:
        return dict(anteil=np.nan, n=0, ki_lo=np.nan, ki_hi=np.nan)
    p = float((d[var] * d[w]).sum() / d[w].sum())
    n = len(d)
    se = np.sqrt(p * (1 - p) / n)
    return dict(anteil=100 * p, n=n,
                ki_lo=100 * max(0, p - 1.96 * se),
                ki_hi=100 * min(1, p + 1.96 * se))


def agg(ebene, gruppe, jahr, var="unsicher", subset=None, d=None):
    d = df if d is None else d
    if subset is not None:
        d = d[subset(d)]
    if jahr is not None:
        d = d[d.jahr == jahr]
    if len(d) == 0:
        return
    r = wshare(d, var)
    rows.append(dict(ebene=ebene, gruppe=gruppe, jahr=jahr, kennzahl=var,
                     anteil=round(r["anteil"], 2), n=int(r["n"]),
                     ki_lo=round(r["ki_lo"], 2), ki_hi=round(r["ki_hi"], 2)))


JAHR = sorted(df.jahr.dropna().unique())

# 1) Zeitreihen je Welle -----------------------------------------------------
for j in JAHR:
    agg("zeitreihe", "gesamt", j)
    for g, lab in [("Frau", "Frauen"), ("Mann", "Männer")]:
        agg("zeitreihe_geschlecht", lab, j, subset=lambda d, g=g: d.geschlecht == g)
    agg("zeitreihe", "viktimisiert", j, subset=lambda d: d.viktim == 1)
    agg("zeitreihe", "nicht viktimisiert", j, subset=lambda d: d.viktim == 0)

# 2) Gruppen-Zeitreihen je Welle --------------------------------------------
GRUPPEN = {
    "bildung": ("tertiaer", {1: "tertiär", 0: "nicht tertiär"}),
    "migration": ("mh", {1: "mit Migrationshintergrund", 0: "ohne Migrationshintergrund"}),
    "diskriminierung": ("diskriminiert", {1: "diskriminiert (Selbstauskunft)", 0: "nicht diskriminiert"}),
    "vertrauen_polizei": ("vertrauen_polizei_hoch", {1: "hohes Polizeivertrauen", 0: "niedriges Polizeivertrauen"}),
}
for ebene, (var, codes) in GRUPPEN.items():
    for k, lab in codes.items():
        for j in JAHR:
            agg(ebene, lab, j, subset=lambda d, var=var, k=k: d[var] == k)

for j in JAHR:
    for lab in ["16-29", "30-44", "45-59", "60-74", "75+"]:
        agg("alter", lab, j, subset=lambda d, lab=lab: d.alter_gr == lab)
    for lab in ["Grossstadt", "Vorort", "Kleinstadt", "Dorf", "Land"]:
        agg("wohnort", lab, j, subset=lambda d, lab=lab: d.stadt_land == lab)

# 3) Gepoolte Struktur (alle Wellen) ----------------------------------------
for ebene, (var, codes) in GRUPPEN.items():
    for k, lab in codes.items():
        agg(ebene + "_gepoolt", lab, None, subset=lambda d, var=var, k=k: d[var] == k)
for lab in ["16-29", "30-44", "45-59", "60-74", "75+"]:
    agg("alter_gepoolt", lab, None, subset=lambda d, lab=lab: d.alter_gr == lab)
for lab in ["Grossstadt", "Vorort", "Kleinstadt", "Dorf", "Land"]:
    agg("wohnort_gepoolt", lab, None, subset=lambda d, lab=lab: d.stadt_land == lab)
agg("struktur_gepoolt", "arbeitslos", None, subset=lambda d: d.uempla_c == 1)
agg("struktur_gepoolt", "nicht arbeitslos", None, subset=lambda d: d.uempla_c == 0)

# 4) Einstellungen (Median-Split, gepoolt, gepolte Variablen) ---------------
SKALEN = [
    ("trstplc_c", "Polizeivertrauen", "hoch=nach rechts"),
    ("trstprl_c", "Parlamentsvertrauen", "hoch=mehr Vertrauen"),
    ("ppltrst_c", "Sozialvertrauen", "hoch=mehr Vertrauen"),
    ("stfgov_c", "Regierungszufriedenheit", "hoch=zufriedener"),
    ("stflife_c", "Lebenszufriedenheit", "hoch=zufriedener"),
    ("stfdem_c", "Demokratiezufriedenheit", "hoch=zufriedener"),
    ("happy_c", "Glück", "hoch=glücklicher"),
    ("imwbcnt_c", "Einstellung Zuwanderung", "hoch=positiver"),
    ("health_pos", "Gesundheit", "hoch=besserer Zustand"),
    ("hincfel_pos", "Einkommenslage", "hoch=leichter"),
]
for var, lab, note in SKALEN:
    d = df.dropna(subset=[var])
    if len(d) == 0:
        continue
    med = d[var].median()
    for klab, sub in [("niedrige Ausprägung", d[d[var] <= med]),
                      ("hohe Ausprägung", d[d[var] > med])]:
        r = wshare(sub, "unsicher")
        rows.append(dict(ebene="einstellung_gepoolt", gruppe=f"{lab} ({klab})",
                         jahr=None, kennzahl="unsicher", anteil=round(r["anteil"], 2),
                         n=int(r["n"]), ki_lo=round(r["ki_lo"], 2), ki_hi=round(r["ki_hi"], 2)))

# 5) Politische Selbsteinstufung (links/rechts) ------------------------------
d = df.dropna(subset=["lrscale_c"])
for lo, hi, lab in [(0, 3, "links (0-3)"), (4, 6, "Mitte (4-6)"), (7, 10, "rechts (7-10)")]:
    sub = d[(d.lrscale_c >= lo) & (d.lrscale_c <= hi)]
    r = wshare(sub, "unsicher")
    rows.append(dict(ebene="politisch_gepoolt", gruppe=lab, jahr=None, kennzahl="unsicher",
                     anteil=round(r["anteil"], 2), n=int(r["n"]),
                     ki_lo=round(r["ki_lo"], 2), ki_hi=round(r["ki_hi"], 2)))

out = pd.DataFrame(rows)
out.to_csv(OUT, index=False, sep=";")
print(f"\n{len(out)} Aggregate -> {OUT}\n")
pd.set_option("display.width", 220)

print("--- Zeitreihe gesamt / Geschlecht / Viktimisierung ---")
z = out[out.ebene.isin(["zeitreihe", "zeitreihe_geschlecht"])]
piv = z.pivot_table(index="jahr", columns=["ebene", "gruppe"], values="anteil").round(1)
print(piv.to_string())

print("\n--- Gruppen-Zeitreihen (gebildet) ---")
g = out[out.ebene.isin(["bildung", "migration", "diskriminierung", "vertrauen_polizei"])]
print(g.pivot_table(index="jahr", columns=["ebene", "gruppe"], values="anteil").round(1).to_string())

print("\n--- Alter-Zeitreihe ---")
print(out[out.ebene == "alter"].pivot_table(index="jahr", columns="gruppe", values="anteil").round(1).to_string())

print("\n--- Wohnort-Zeitreihe ---")
print(out[out.ebene == "wohnort"].pivot_table(index="jahr", columns="gruppe", values="anteil").round(1).to_string())

print("\n--- Gepoolte Struktur ---")
print(out[out.ebene.str.endswith("_gepoolt") & (out.ebene != "einstellung_gepoolt")]
      [["ebene", "gruppe", "anteil", "n"]].to_string(index=False))

print("\n--- Einstellungen (Median-Split, gepoolt) ---")
print(out[out.ebene == "einstellung_gepoolt"][["gruppe", "anteil", "n"]].to_string(index=False))

print("\n--- Politische Selbsteinstufung ---")
print(out[out.ebene == "politisch_gepoolt"][["gruppe", "anteil", "n"]].to_string(index=False))
