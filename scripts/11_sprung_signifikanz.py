#!/usr/bin/env python3
"""Signifikanzprüfung der Gruppenveränderungen 2014 -> 2016 (ESS-DE).

Für jede Gruppenausprägung wird die Veränderung des Unsicherheitsanteils mit
einem Standardfehler versehen. Die Konfidenzintervalle sind als untere Grenze
zu lesen: Der Designeffekt der ESS-Stichprobe (Klumpung, Gewichtung) ist NICHT
eingerechnet, die echten Intervalle sind also breiter.

Ausgabe: Veränderung je Gruppe mit 95-%-Intervall und Kennzeichnung, ob die
Veränderung gegenüber 0 abgesichert ist.
"""
import csv
import math


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


D = list(csv.DictReader(open("dashboard/data/ess_de_personen.csv", encoding="utf-8")))


def kennwert(jahr, feld, wert):
    """Gewichteter Anteil, ungewichtetes n, Standardfehler (Näherung)."""
    num = den = 0.0
    n = 0
    for r in D:
        if str(r.get("jahr")) != jahr or r.get(feld) != wert:
            continue
        u = f(r.get("unsicher"))
        w = f(r.get("w")) or 0
        if u is None or w <= 0:
            continue
        num += u * w
        den += w
        n += 1
    if not den or not n:
        return None
    p = num / den
    se = math.sqrt(p * (1 - p) / n) * 100          # in Prozentpunkten
    return p * 100, n, se


def block(feld, werte, label):
    print(f"--- {label} ---")
    for w in werte:
        a = kennwert("2014", feld, w)
        b = kennwert("2016", feld, w)
        if not a or not b:
            continue
        delta = b[0] - a[0]
        se = math.sqrt(a[2] ** 2 + b[2] ** 2)
        lo, hi = delta - 1.96 * se, delta + 1.96 * se
        stern = "  *" if (lo > 0 or hi < 0) else "   "
        print(f"  {str(w):12s} Δ {delta:+5.1f} PP  [95 %: {lo:+5.1f} bis {hi:+5.1f}]"
              f"  n {a[1]:4d}/{b[1]:4d}{stern}")
    print()


block("geschlecht", ["Frau", "Mann"], "Geschlecht")
block("alter_gr", ["16-29", "30-44", "45-59", "60-74", "75+"], "Altersgruppe")
block("tertiaer", ["0", "1"], "Bildung (1 = tertiär)")
block("mh", ["0", "1"], "Migrationshintergrund")
block("stadt_land", ["Grossstadt", "Kleinstadt", "Vorort", "Dorf", "Land"], "Wohnort")

# Direkter Vergleich der wichtigsten Gegenüberstellung: Grossstadt vs. Dorf
a1, b1 = kennwert("2014", "stadt_land", "Grossstadt"), kennwert("2016", "stadt_land", "Grossstadt")
a2, b2 = kennwert("2014", "stadt_land", "Dorf"), kennwert("2016", "stadt_land", "Dorf")
if all([a1, b1, a2, b2]):
    d1 = b1[0] - a1[0]
    d2 = b2[0] - a2[0]
    diff = d2 - d1
    se = math.sqrt(a1[2] ** 2 + b1[2] ** 2 + a2[2] ** 2 + b2[2] ** 2)
    print(f"Interaktion Dorf vs. Großstadt: ΔΔ = {diff:+.1f} PP "
          f"[95 %: {diff-1.96*se:+.1f} bis {diff+1.96*se:+.1f}]")
    print("  -> schließt die 0 ein, wenn die Spanne beide Vorzeichen hat."
          if (diff - 1.96 * se) * (diff + 1.96 * se) < 0 else
          "  -> von 0 verschieden.")
print("\nHinweis: Standardfehler ohne Designeffekt; die echten Intervalle sind weiter.")
