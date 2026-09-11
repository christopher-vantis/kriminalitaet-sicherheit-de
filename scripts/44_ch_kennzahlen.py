#!/usr/bin/env python3
"""
44_ch_kennzahlen.py — Kennzahlen je Kanton und Zeitreihen der Schweiz
=====================================================================
Verrechnet die BFS-Rohdaten zu den Kennzahlen, die die App zeigt, und legt
die Kontrollwerte offen.

Eingang:
  output/ch_pks_kantone.csv     BFS PKS (StGB) nach Kanton/Delikt/Jahr
  output/ch_bevoelkerung.csv    BFS Wohnbevölkerung nach Kanton/Jahr

Kennzahlen:
  faelle_stgb        registrierte Straftaten nach StGB (Total)
  hz                 Häufigkeitszahl: Fälle je 100'000 Einwohner
  aq                 Aufklärungsquote in Prozent (aufgeklärt / alle Fälle)
  hz_diebstahl       Diebstahl Art. 139 (inkl. Einbruch, Trickdiebstahl …)
  hz_einbruch        Einbruchdiebstahl Art. 139
  hz_gewalt          Total 1. Titel StGB (Leib und Leben)
  hz_koerperverl     einfache + schwere Körperverletzung
  hz_raub            Raub Art. 140
  hz_sachbesch       Sachbeschädigung Art. 144
  hz_betrug          Betrug Art. 146 + betrügerischer Missbrauch DV Art. 147
  auslaenderanteil   Ausländer an der ständigen Wohnbevölkerung (Prozent),
                     Stand 31.12.
  dichte             Einwohner je km² (Fläche aus der Kartengrundlage, GISCO)

OPERATIONALISIERUNG (Grenzen):
- Die PKS zählt nach Tatortprinzip. Taten werden dort registriert, wo sie
  begangen wurden, nicht wo die beschuldigte Person wohnt. Kantone mit vielen
  Einpendlern, Touristen und Grenzgängern haben dadurch systematisch höhere
  Häufigkeitszahlen; das ist kein Messfehler, aber auch kein Mass für die
  Kriminalität der ansässigen Bevölkerung.
- Erfasst ist nur das Strafgesetzbuch. Widerhandlungen gegen BetmG, AIG und
  weitere Nebengesetze sind ausgeschlossen (im BFS-Total rund ein Fünftel
  aller registrierten Straftaten).
- Die Häufigkeitszahl wird mit der mittleren ständigen Wohnbevölkerung des
  Jahres gebildet (Mittel aus Bestand 1.1. und 31.12.). Nicht darin enthalten
  sind Kurzaufenthalter, Asylsuchende im Verfahren und Touristen — bei
  Tatorten mit vielen Besucherinnen und Besuchern fällt der Nenner zu klein
  aus.
- Nenner der Aufklärungsquote sind alle registrierten Fälle inkl. Versuche.

Ausgabe: output/ch_kantone_kennzahlen.csv   (Kanton × Jahr, Langformat)
         output/ch_zeitreihe.csv            (Schweiz, Delikt × Jahr)

Aufruf: python3 scripts/44_ch_kennzahlen.py
"""
import csv
import json
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

KANTONE = {
    1: "Zürich", 2: "Bern", 3: "Luzern", 4: "Uri", 5: "Schwyz", 6: "Obwalden",
    7: "Nidwalden", 8: "Glarus", 9: "Zug", 10: "Freiburg", 11: "Solothurn",
    12: "Basel-Stadt", 13: "Basel-Landschaft", 14: "Schaffhausen",
    15: "Appenzell Ausserrhoden", 16: "Appenzell Innerrhoden", 17: "St. Gallen",
    18: "Graubünden", 19: "Aargau", 20: "Thurgau", 21: "Tessin", 22: "Waadt",
    23: "Wallis", 24: "Neuenburg", 25: "Genf", 26: "Jura",
}

# Deliktcodes der BFS-Tabelle -> Kurzname
GESAMT = "311.00.T0"
DELIKTE = {
    "311.00.T0": "stgb_total",
    "311.00.T1": "leib_leben",
    "311.00.123.00": "kv_einfach",
    "311.00.122.00": "kv_schwer",
    "311.00.139.00": "diebstahl",
    "311.00.139.10": "einbruch",
    "311.00.139.75": "taschendiebstahl",
    "311.00.139.74": "ladendiebstahl",
    "311.00.140.00": "raub",
    "311.00.144.00": "sachbeschaedigung",
    "311.00.147.00": "cyberbetrug",
    "311.00.190.00": "vergewaltigung",
    "311.00.261.A0": "diskriminierung",
    "311.00.180.00": "drohung",
}


def lies(pfad, delim=";"):
    """Liest eine CSV mit Kopfzeile.

    Args:
        pfad: Dateipfad.
        delim: Trennzeichen.

    Returns:
        list[dict]: Zeilen als Dictionaries.
    """
    with open(pfad, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=delim))


def main():
    pks = lies(OUT / "ch_pks_kantone.csv")
    bev = lies(OUT / "ch_bevoelkerung.csv")

    # --- Bevölkerung je Kanton/Jahr (Mittel aus 1.1. und 31.12.) -----------
    b11, b31 = {}, {}
    ausl, total31 = {}, {}
    for r in bev:
        k, j = r["kanton_code"], int(r["jahr"])
        if r["staatsangehoerigkeit"] != "total":
            if r["komponente"] == "bestand_31_12":
                ausl[(k, j, r["staatsangehoerigkeit"])] = int(r["personen"])
            continue
        if r["komponente"] == "bestand_1_1":
            b11[(k, j)] = int(r["personen"])
        else:
            b31[(k, j)] = int(r["personen"])
            total31[(k, j)] = int(r["personen"])

    def mittel(k, j):
        """Mittlere Wohnbevölkerung des Jahres (Mittel 1.1./31.12.)."""
        a = b31.get((k, j - 1)) if (k, j) not in b11 else b11[(k, j)]
        b = b31.get((k, j))
        if a is None or b is None:
            return None
        return (a + b) / 2

    # --- Fläche aus der Kartengrundlage (GISCO, verallgemeinert) -----------
    geo = json.loads((OUT / "ch_kantone_svg.json").read_text(encoding="utf-8"))
    flaeche = {str(v["kanton_nr"]): v["flaeche_km2"]
               for k, v in geo.items() if k != "_viewbox"}

    # --- PKS: Fälle je Kanton/Delikt/Jahr ---------------------------------
    # Nur Totalspalten verwenden: Ausführungsgrad "total", Aufklärungsgrad
    # einmal "total" (alle Fälle) und einmal "aufgeklärt" (Zähler der Quote).
    faelle = defaultdict(dict)          # (kanton, delikt, jahr) -> total
    aufgeklaert = defaultdict(dict)
    for r in pks:
        if r["ausfuehrung"] != "total":
            continue
        key = (r["kanton_code"], r["delikt_code"], int(r["jahr"]))
        val = None if r["faelle"] in ("", None) else int(r["faelle"])
        if r["aufklaerung"] == "total":
            faelle[key] = val
        elif r["aufklaerung"] == "aufgeklärt":
            aufgeklaert[key] = val

    # --- Kontrolle 1: Schweiz-Total gegen die BFS-Publikation -------------
    ch25 = faelle[("8100", GESAMT, 2025)]
    print(f"Kontrolle Schweiz 2025: {ch25:,} StGB-Straftaten "
          "(BFS-Publikation: 554'963)".replace(",", "'"))
    assert ch25 == 554963, f"Abweichung vom BFS-Publikationswert: {ch25}"
    ch24 = faelle[("8100", GESAMT, 2024)]
    assert ch24 == 563633
    print("  -> BFS-Werte 2024/2025 stimmen mit der Publikation überein")

    # --- Kontrolle 2: Additivität der Kantone ----------------------------
    # Die Kantonssumme erreicht das Schweiz-Total nicht ganz: Im Total sind
    # auch Straftaten aus dem Zuständigkeitsbereich des Bundes enthalten
    # (fedpol, Bundesanwaltschaft, Bahnpolizei), die keinem Kanton zugeordnet
    # werden. Der Restbetrag ist über die Jahre unterschiedlich gross
    # (2009–2023 zwischen 500 und 5'000 Fällen, 2024/2025 unter 100) und
    # betrifft im aktuellen Jahr fast nur Diebstahl und Straftaten gegen den
    # öffentlichen Frieden.
    print("\nRestbetrag Schweiz-Total minus Summe der Kantone (StGB gesamt):")
    for j in (2009, 2015, 2020, 2024, 2025):
        s = sum(faelle[(str(k), GESAMT, j)] for k in KANTONE)
        rest = faelle[("8100", GESAMT, j)] - s
        assert 0 <= rest < 0.02 * faelle[("8100", GESAMT, j)], (j, rest)
        print(f"  {j}: Kantone {s:>9,} | Schweiz {faelle[('8100', GESAMT, j)]:>9,} "
              f"| Rest {rest:>5,}".replace(",", "'"))
    print("  -> Rest < 2 % des Totals; Kantone sind vollständig enthalten")

    # --- Kontrolle 3: nur Kantone, keine weiteren Aggregatzeilen ----------
    kt_codes = {r["kanton_code"] for r in pks}
    assert kt_codes == {"8100"} | {str(k) for k in KANTONE}, kt_codes

    # --- Kennzahlen je Kanton und Jahr ------------------------------------
    zeilen = []
    for k in KANTONE:
        ks = str(k)
        for j in range(2009, 2026):
            pop = mittel(ks, j)
            if pop is None:
                continue
            def f(delikt, jahr=j, ks=ks):
                return faelle.get((ks, delikt, jahr))
            def hz(delikt):
                v = f(delikt)
                return None if v is None else 1e5 * v / pop

            ges = f(GESAMT)
            auf = aufgeklaert.get((ks, GESAMT, j))
            aq = None if (ges in (None, 0) or auf is None) else 100 * auf / ges
            gewalt = None
            for d in ("311.00.T1",):
                x = f(d)
                gewalt = x if x is not None else gewalt
            kv = sum(x for x in (f("311.00.122.00"), f("311.00.123.00"))
                     if x is not None) or None
            betrug = sum(x for x in (f("311.00.146.00"), f("311.00.147.00"))
                         if x is not None) or None
            a_tot = ausl.get((ks, j, "ausland"))
            a_ch = ausl.get((ks, j, "schweiz"))
            aq_anteil = None
            if a_tot is not None and a_ch:
                aq_anteil = 100 * a_tot / (a_tot + a_ch)

            zeilen.append({
                "kanton_code": ks, "kanton": KANTONE[k], "jahr": j,
                "bevoelkerung": round(pop, 1),
                "flaeche_km2": flaeche.get(ks),
                "dichte": None if not flaeche.get(ks) else round(pop / flaeche[ks], 1),
                "auslaenderanteil": None if aq_anteil is None else round(aq_anteil, 1),
                "faelle_stgb": ges, "hz": None if ges is None else round(hz(GESAMT), 1),
                "aufgeklaert": auf,
                "aq": None if aq is None else round(aq, 1),
                "hz_leib_leben": None if gewalt is None else round(1e5 * gewalt / pop, 1),
                "hz_koerperverletzung": None if kv is None else round(1e5 * kv / pop, 1),
                "hz_diebstahl": None if hz("311.00.139.00") is None
                else round(hz("311.00.139.00"), 1),
                "hz_einbruch": None if hz("311.00.139.10") is None
                else round(hz("311.00.139.10"), 1),
                "hz_raub": None if hz("311.00.140.00") is None
                else round(hz("311.00.140.00"), 1),
                "hz_sachbeschaedigung": None if hz("311.00.144.00") is None
                else round(hz("311.00.144.00"), 1),
                "hz_cyberbetrug": None if hz("311.00.147.00") is None
                else round(hz("311.00.147.00"), 1),
                "hz_vergewaltigung": None if hz("311.00.190.00") is None
                else round(hz("311.00.190.00"), 1),
                "faelle_diebstahl": f("311.00.139.00"),
                "faelle_einbruch": f("311.00.139.10"),
                "faelle_leib_leben": gewalt,
                "faelle_raub": f("311.00.140.00"),
                "faelle_sachbeschaedigung": f("311.00.144.00"),
                "faelle_cyberbetrug": f("311.00.147.00"),
                "faelle_vergewaltigung": f("311.00.190.00"),
                "faelle_diskriminierung": f("311.00.261.A0"),
                "aufgeklaert_diebstahl": aufgeklaert.get((ks, "311.00.139.00", j)),
                "aufgeklaert_einbruch": aufgeklaert.get((ks, "311.00.139.10", j)),
            })
    ziel = OUT / "ch_kantone_kennzahlen.csv"
    with open(ziel, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(zeilen[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    print(f"\n{ziel.name}: {len(zeilen)} Zeilen "
          f"({len(KANTONE)} Kantone × {len(set(z['jahr'] for z in zeilen))} Jahre)")

    # --- Zeitreihe Schweiz (Delikt × Jahr) --------------------------------
    zr = []
    for j in range(2009, 2026):
        pop = mittel("0", j)
        auf = aufgeklaert.get(("8100", GESAMT, j))
        ges = faelle.get(("8100", GESAMT, j))
        daten = {
            "jahr": j, "bevoelkerung": round(pop, 1),
            "faelle_stgb": ges,
            "hz_stgb": round(1e5 * ges / pop, 1),
            "aq_stgb": round(100 * auf / ges, 1) if auf and ges else None,
        }
        for code, name in DELIKTE.items():
            if name == "stgb_total":
                continue
            v = faelle.get(("8100", code, j))
            daten[f"faelle_{name}"] = v
            daten[f"hz_{name}"] = None if v is None else round(1e5 * v / pop, 1)
            a = aufgeklaert.get(("8100", code, j))
            daten[f"aq_{name}"] = round(100 * a / v, 1) if a and v else None
        zr.append(daten)
    ziel2 = OUT / "ch_zeitreihe.csv"
    with open(ziel2, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(zr[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(zr)
    print(f"{ziel2.name}: {len(zr)} Jahre")
    for r in zr:
        print(f"  {r['jahr']}: HZ {r['hz_stgb']:>7.1f} | AQ {r['aq_stgb']:>4.1f} % | "
              f"Diebstahl-HZ {r['hz_diebstahl']:>7.1f} | Einbruch-HZ "
              f"{r['hz_einbruch']:>6.1f} | Leib-und-Leben-HZ {r['hz_leib_leben']:>6.1f}")


if __name__ == "__main__":
    main()
