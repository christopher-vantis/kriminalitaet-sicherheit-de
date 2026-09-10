#!/usr/bin/env python3
"""
15_ess_bundeslaender.py — Wahrnehmung je Bundesland (ESS-DE, NUTS-1)
====================================================================
Aggregiert die ESS-Daten (Runden 5–11, in denen die Region erhoben ist) auf
die 16 Bundesländer und berechnet gewichtete Anteile mit Fallzahlen und
Konfidenzintervallen.

NUTS-1 = Bundesland in Deutschland:
  DE1 Baden-Württemberg, DE2 Bayern, DE3 Berlin, DE4 Brandenburg, DE5 Bremen,
  DE6 Hamburg, DE7 Hessen, DE8 Mecklenburg-Vorpommern, DE9 Niedersachsen,
  DEA Nordrhein-Westfalen, DEB Rheinland-Pfalz, DEC Saarland, DED Sachsen,
  DEE Sachsen-Anhalt, DEF Schleswig-Holstein, DEG Thüringen.

WICHTIG: Die ESS-Stichproben je Bundesland sind klein (n = 15–430 je Welle).
Für belastbare Länderwerte werden alle Wellen ab R5 gepoolt (n ≈ 240–2.900 je
Land). Länder mit sehr kleinen Fallzahlen werden als unsicher markiert.

Ausgabe: dashboard/data/ess_bundeslaender.csv
  nuts; bundesland; n; unsicher_pct; ki_lo; ki_hi; viktim_pct; sozialvertrauen;
  polizeivertrauen; zuwanderung_negativ_pct; hochschule_pct; alter_mittel
"""
import csv
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "dashboard/data"
OUT = D / "ess_bundeslaender.csv"

NUTS = {
    "DE1": "Baden-Württemberg", "DE2": "Bayern", "DE3": "Berlin",
    "DE4": "Brandenburg", "DE5": "Bremen", "DE6": "Hamburg", "DE7": "Hessen",
    "DE8": "Mecklenburg-Vorpommern", "DE9": "Niedersachsen",
    "DEA": "Nordrhein-Westfalen", "DEB": "Rheinland-Pfalz", "DEC": "Saarland",
    "DED": "Sachsen", "DEE": "Sachsen-Anhalt", "DEF": "Schleswig-Holstein",
    "DEG": "Thüringen",
}

# Mindestfallzahl, ab der ein Länderwert als belastbar gilt
MIN_N = 300


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    zeilen = list(csv.DictReader(open(D / "ess_de_personen.csv", encoding="utf-8")))
    gepoolt = [r for r in zeilen if str(r.get("region", "")).startswith("DE")
               and str(r.get("region", "")) in NUTS]
    print(f"Personen mit Bundesland-Angabe: {len(gepoolt)} von {len(zeilen)}")
    wellen = sorted({r["essround"] for r in gepoolt})
    print(f"Runden: {wellen}")

    ergebnis = []
    for nuts, name in NUTS.items():
        gruppe = [r for r in gepoolt if r.get("region") == nuts]

        def anteil(feld, wert=None):
            """Gewichteter Anteil; wert=None -> Mittelwert der Variablen."""
            num = den = 0.0
            for r in gruppe:
                v = f(r.get(feld))
                w = f(r.get("w")) or 0
                if v is None or w <= 0:
                    continue
                if wert is not None:
                    v = 1.0 if int(v) == wert else 0.0
                num += v * w
                den += w
            return (num / den, den) if den else (None, 0)

        unsicher, n_u = anteil("unsicher", 1)
        viktim, _ = anteil("viktim", 1)
        sozial, _ = anteil("ppltrst_c")
        polizei, _ = anteil("trstplc_c")
        alter, _ = anteil("agea_c")
        bildung, _ = anteil("tertiaer", 1)
        # Zuwanderung: imwbcnt 0 = schlecht für das Land, 10 = gut
        zuw, _ = anteil("imwbcnt_c")

        se = (math.sqrt(unsicher * (1 - unsicher) / n_u) * 100
              if unsicher is not None and n_u else None)
        ki_lo = round((unsicher * 100) - 1.96 * se, 1) if se else None
        ki_hi = round((unsicher * 100) + 1.96 * se, 1) if se else None

        ergebnis.append(dict(
            nuts=nuts, bundesland=name, n=int(n_u),
            unsicher_pct=round(unsicher * 100, 1) if unsicher is not None else None,
            ki_lo=ki_lo, ki_hi=ki_hi,
            unsicher_belastbar="ja" if n_u >= MIN_N else "nein (kleines n)",
            viktim_pct=round(viktim * 100, 1) if viktim is not None else None,
            sozialvertrauen=round(sozial, 2) if sozial is not None else None,
            polizeivertrauen=round(polizei, 2) if polizei is not None else None,
            zuwanderung_positiv=round(zuw, 2) if zuw is not None else None,
            hochschule_pct=round(bildung * 100, 1) if bildung is not None else None,
            alter_mittel=round(alter, 1) if alter is not None else None,
        ))

    ergebnis.sort(key=lambda r: -(r["unsicher_pct"] or 0))
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ergebnis[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(ergebnis)
    print(f"\n-> {OUT}")
    print(f"{'Bundesland':26s} {'n':>5s} {'unsicher':>9s} {'95-%-KI':>16s} {'polizei':>8s}")
    for r in ergebnis:
        ki = f"[{r['ki_lo']}, {r['ki_hi']}]" if r["ki_lo"] is not None else "—"
        pol = f"{r['polizeivertrauen']:.2f}" if r["polizeivertrauen"] is not None else "—"
        uns = f"{r['unsicher_pct']:.1f}%" if r["unsicher_pct"] is not None else "—"
        print(f"{r['bundesland']:26s} {r['n']:>5d} {uns:>8s} {ki:>16s} {pol:>8s}  "
              f"{r['unsicher_belastbar']}")


if __name__ == "__main__":
    main()
