#!/usr/bin/env python3
"""Prüft, welche Delikte und Länder die Eurostat-Datei enthält."""
import csv
import pathlib
from collections import defaultdict

P = pathlib.Path("/home/c-vantis/jd/40_projects/47_kriminalitaetsdiskrepanz_de"
                 "/data/raw/eurostat/crim_off_cat.tsv")

with open(P, encoding="utf-8") as fh:
    zeilen = list(csv.reader(fh, delimiter="\t"))

kopf = zeilen[0]
# Die erste Spalte enthält die zusammengefassten Dimensionen
spalten = [kopf[0]] + kopf[1:]
jahre = [s.strip() for s in spalten[1:]]
print("Jahre:", jahre[0], "-", jahre[-1], f"({len(jahre)} Spalten)")
print()

delikte = defaultdict(lambda: {"laender": set(), "werte": 0})
unit_pro_code = defaultdict(set)

for z in zeilen[1:]:
    if not z or not z[0]:
        continue
    felder = z[0].split(",")
    if len(felder) < 4:
        continue
    freq, iccs, unit, geo = felder[0], felder[1], felder[2], felder[3]
    werte = [x for x in z[1:] if x.strip() and x.strip() != ":"]
    if werte:
        delikte[iccs]["laender"].add(geo)
        delikte[iccs]["werte"] += len(werte)
        unit_pro_code[iccs].add(unit)

print(f"{'ICCS-Code':12s} {'Länder':>7s} {'Werte':>7s}  Einheit")
for code, d in sorted(delikte.items(), key=lambda kv: -len(kv[1]["laender"])):
    print(f"{code:12s} {len(d['laender']):7d} {d['werte']:7d}  {','.join(sorted(unit_pro_code[code]))}")

# Deutschland: welche Delikte haben Werte?
print("\nDelikte mit Deutschland-Werten:")
for code, d in sorted(delikte.items()):
    if "DE" in d["laender"]:
        de_werte = 0
        for z in zeilen[1:]:
            if z and z[0].startswith(f"A,{code},") and ",DE" in z[0]:
                de_werte = len([x for x in z[1:] if x.strip() and x.strip() != ":"])
        print(f"  {code:12s} {de_werte} Jahreswerte für DE")
