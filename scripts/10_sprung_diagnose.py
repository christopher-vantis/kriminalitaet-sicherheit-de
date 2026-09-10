#!/usr/bin/env python3
"""Diagnose: War der Furcht-Sprung 2014->2016 ein gemeinsamer Schock oder
gruppenspezifisch? Rechnet die Veränderung des Unsicherheitsanteils je Gruppe
(ESS-DE, gewichtet) für zwei Wellen."""
import csv
from collections import defaultdict


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


d = list(csv.DictReader(open("dashboard/data/ess_de_personen.csv", encoding="utf-8")))


def anteil(zeilen):
    num = den = 0.0
    for r in zeilen:
        u = f(r.get("unsicher"))
        w = f(r.get("w")) or 0
        if u is None or w <= 0:
            continue
        num += u * w
        den += w
    return (num / den * 100 if den else None), int(den)


def verlauf(feld, wert):
    out = {}
    for j in ("2014", "2016"):
        z = [r for r in d if str(r.get("jahr")) == j and r.get(feld) == wert]
        out[j] = anteil(z)
    if out["2014"][0] is None or out["2016"][0] is None:
        return None
    return out["2016"][0] - out["2014"][0], out["2014"], out["2016"]


GRUPPEN = [
    ("geschlecht", ["Frau", "Mann"]),
    ("alter_gr", ["16-29", "30-44", "45-59", "60-74", "75+"]),
    ("tertiaer", ["0", "1"]),
    ("mh", ["0", "1"]),
    ("stadt_land", ["Grossstadt", "Kleinstadt", "Vorort", "Dorf", "Land"]),
]

print("Unsicherheitsanteil 2014 -> 2016 je Gruppe (Prozentpunkte, gewichtet)")
print("Ein gemeinsamer Schock müsste in allen Gruppen ähnlich groß sein.\n")
for feld, werte in GRUPPEN:
    print(f"--- {feld} ---")
    for w in werte:
        r = verlauf(feld, w)
        if r is None:
            continue
        delta, a14, a16 = r
        print(f"  {str(w):12s} 2014: {a14[0]:5.1f} % (n={a14[1]:4d}) -> "
              f"2016: {a16[0]:5.1f} % (n={a16[1]:4d})   Delta {delta:+5.1f} PP")
    print()

# Streuung der Deltas als Streuungsmaß: enge Spanne = gemeinsamer Schock
alle_deltas = []
for feld, werte in GRUPPEN:
    for w in werte:
        r = verlauf(feld, w)
        if r:
            alle_deltas.append(r[0])
if alle_deltas:
    print(f"Spanne der Gruppenveränderungen: {min(alle_deltas):+.1f} bis {max(alle_deltas):+.1f} PP "
          f"(Mittel {sum(alle_deltas)/len(alle_deltas):+.1f})")
