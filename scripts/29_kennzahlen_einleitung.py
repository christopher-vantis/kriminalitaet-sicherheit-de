#!/usr/bin/env python3
"""Holt die Kennzahlen für den einführenden Reiter zusammen."""
import csv
import pathlib

ROOT = pathlib.Path("/home/c-vantis/jd/40_projects/47_kriminalitaetsdiskrepanz_de")

print("=== Registrierte Straftaten insgesamt (PKS) ===")
rows = list(csv.DictReader(open(ROOT / "output/t01_bund_zeitreihe_clean.csv", encoding="utf-8")))
gesamt = [r for r in rows if "insgesamt" in r["delikt"].lower()]
if not gesamt:
    gesamt = [r for r in rows if r["delikt"] == rows[0]["delikt"]]
d = {int(float(r["jahr"])): r for r in gesamt}
for j in [1987, 1993, 2002, 2014, 2019, 2021, 2022, 2023, 2024, 2025]:
    if j in d:
        r = d[j]
        hz = f", {float(r['hz']):.0f} je 100.000" if r.get("hz") else ""
        print(f"  {j}: {int(float(r['faelle'])):>9,} Faelle{hz}".replace(",", "."))

print()
print("=== Unsicherheitsgefuehl (ESS, Anteil der Befragten) ===")
ess = list(csv.DictReader(open(ROOT / "output/ess_de_unsicher_zeitreihe.csv", encoding="utf-8")))
print("  Felder:", list(ess[0].keys()))
for r in ess:
    if r.get("jahr") in ("2002", "2012", "2014", "2016", "2018", "2023"):
        wert = r.get("anteil") or r.get("unsicher") or r.get("wert")
        n = r.get("n") or r.get("faelle")
        print(f"  {r['jahr']}: {wert} (n={n})")

print()
print("=== Bundeslaender: Spannweite der Kriminalitaetsbelastung (2025) ===")
laender = list(csv.DictReader(open(ROOT / "output/pks_laender_2025.csv", encoding="utf-8")))
ges = [r for r in laender if "insgesamt" in r.get("delikt", "").lower()]
if ges:
    werte = sorted(((float(r["hz"]), r["bundesland"]) for r in ges if r.get("hz")))
    print(f"  niedrigste: {werte[0][1]} {werte[0][0]:.0f}")
    print(f"  hoechste:   {werte[-1][1]} {werte[-1][0]:.0f}")
