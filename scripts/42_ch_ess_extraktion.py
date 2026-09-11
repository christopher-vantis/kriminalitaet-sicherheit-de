#!/usr/bin/env python3
"""
42_ch_ess_extraktion.py — ESS-Schweiz-Extraktion (Runden 1–11)
==============================================================
Erzeugt die Personenebene der Schweizer ESS-Daten für dieselben Variablen,
die das Deutschland-Projekt verwendet. Damit sind Furcht (aesfdrk) und
Viktimisierung (crmvct) zwischen DE und CH mit identischem Instrument
vergleichbar.

Quelle: ESS-Rohdaten (Data Portal). Die Dateien liegen im 43er-Projekt:
  ~/jd/40_projects/43_human_values_project/data/raw/ess/ESS<r>/*.csv
Kodierungen (gegen die mitgelieferten Codebooks geprüft, identisch zu DE):
  aesfdrk 1=very safe..4=very unsafe; crmvct 1=ja/2=nein;
  brncntr/facntr/mocntr 1=ja/2=nein; eisced 1-7; hinctnta 1-10;
  domicil 1=Grossstadt..5=Haus/Land; nwspol Minuten; trst*/stf* 0-10.

Polung: wie im DE-Projekt werden alle Skalen VOR der Auswertung so gedreht,
dass höhere Werte "mehr in Labelrichtung" bedeuten:
  health_pos = 6 - health ; hincfel_pos = 5 - hincfel
  unsicher   = 1, wenn aesfdrk 3 oder 4 (etwas/sehr unsicher)

Ausgabe: dashboard/data/ch_ess_personen.csv     (Personenebene)
         dashboard/data/ch_ess_aggregate.csv    (gewichtete Anteile)
         output/ch_ess_fallzahlen.csv           (Fallzahlen je Runde, Prüfung)

Aufruf: python3 scripts/42_ch_ess_extraktion.py
"""
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
ESS_DIR = pathlib.Path("/home/c-vantis/jd/40_projects/43_human_values_project/data/raw/ess")
OUT = ROOT / "dashboard" / "data"
OUT.mkdir(parents=True, exist_ok=True)

RUNDEN = {1: 2002, 2: 2004, 3: 2006, 4: 2008, 5: 2010, 6: 2012, 7: 2014,
          8: 2016, 9: 2018, 10: 2020, 11: 2023}

VARS = ["cntry", "pspwght", "aesfdrk", "crmvct",
        "gndr", "agea", "eisced", "hinctnta", "brncntr", "facntr", "mocntr",
        "domicil", "uempla", "health", "hincfel", "dscrgrp", "nwspol",
        "ppltrst", "trstplc", "trstprl", "trstlgl", "trstplt",
        "stfgov", "stfdem", "stflife", "happy", "lrscale", "imwbcnt",
        "imsmetn", "impcntr", "region", "clsprty", "vote"]

# Fehlcodes je Variable (ESS-Standard: 7/8/9 bzw. 77/88/99 usw.)
FEHL = {"aesfdrk": (7, 8, 9), "crmvct": (7, 8, 9), "gndr": (7, 8, 9),
        "agea": (999,), "eisced": (0, 55, 77, 88, 99), "hinctnta": (77, 88, 99),
        "brncntr": (7, 8, 9), "facntr": (7, 8, 9), "mocntr": (7, 8, 9),
        "domicil": (7, 8, 9), "uempla": (7, 8, 9), "health": (7, 8, 9),
        "hincfel": (7, 8, 9), "dscrgrp": (7, 8, 9), "nwspol": (7777, 8888, 9999),
        "ppltrst": (77, 88, 99), "trstplc": (77, 88, 99), "trstprl": (77, 88, 99),
        "trstlgl": (77, 88, 99), "trstplt": (77, 88, 99),
        "stfgov": (77, 88, 99), "stfdem": (77, 88, 99), "stflife": (77, 88, 99),
        "happy": (77, 88, 99), "lrscale": (77, 88, 99), "imwbcnt": (77, 88, 99),
        "imsmetn": (7, 8, 9), "impcntr": (7, 8, 9),
        "clsprty": (7, 8, 9), "vote": (7, 8, 9)}


def lese_runde(r):
    """Liest eine ESS-Runde auf Personenebene ein, gefiltert auf die Schweiz.

    Args:
        r: ESS-Rundennummer (1–11).

    Returns:
        pandas.DataFrame: Personen der Schweiz mit vorhandenen Zielvariablen
            und neuem Feld essround.
    """
    treffer = sorted(ESS_DIR.glob(f"ESS{r}/*.csv"))
    if not treffer:
        raise FileNotFoundError(f"Keine CSV für Runde {r} unter {ESS_DIR}")
    kopf = pd.read_csv(treffer[0], nrows=1)
    nutzbar = [v for v in VARS if v in kopf.columns]
    d = pd.read_csv(treffer[0], usecols=nutzbar, low_memory=False)
    d = d[d["cntry"] == "CH"].copy()
    d["essround"] = r
    return d


def bereinige(d):
    """Setzt Fehlcodes auf NaN und leitet die Auswertungsvariablen ab.

    Args:
        d: rohe Personenebene.

    Returns:
        pandas.DataFrame: bereinigte Personenebene mit den abgeleiteten
            Merkmalen (unsicher, viktim, mh, tertiaer, alter_gr, stadt_land,
            geschlecht, vertrauen_polizei_hoch, health_pos, hincfel_pos, w).
    """
    for v, codes in FEHL.items():
        if v in d.columns:
            d[v] = pd.to_numeric(d[v], errors="coerce")
            d.loc[d[v].isin(codes), v] = np.nan
    d["w"] = pd.to_numeric(d.get("pspwght"), errors="coerce")
    d.loc[~(d["w"] > 0), "w"] = np.nan

    d["unsicher"] = np.where(d["aesfdrk"].isin([3, 4]), 1,
                             np.where(d["aesfdrk"].isin([1, 2]), 0, np.nan))
    d["unsicher_hoch"] = np.where(d["aesfdrk"] == 4, 1,
                                  np.where(d["aesfdrk"].isin([1, 2, 3]), 0, np.nan))
    d["viktim"] = np.where(d["crmvct"] == 1, 1,
                           np.where(d["crmvct"] == 2, 0, np.nan))
    d["mh"] = np.where(
        d["brncntr"] == 2, 1,
        np.where((d["brncntr"] == 1) & ((d["facntr"] == 2) | (d["mocntr"] == 2)), 1,
                 np.where(d["brncntr"] == 1, 0, np.nan)))
    d["tertiaer"] = np.where(d["eisced"].isin([5, 6, 7]), 1,
                             np.where(d["eisced"].isin([1, 2, 3, 4]), 0, np.nan))
    d["alter_gr"] = pd.cut(d["agea"], [15, 29, 44, 59, 74, 200],
                           labels=["16-29", "30-44", "45-59", "60-74", "75+"])
    d["stadt_land"] = d["domicil"].map({1: "Grossstadt", 2: "Vorort",
                                        3: "Kleinstadt", 4: "Dorf", 5: "Land"})
    d["diskriminiert"] = np.where(d["dscrgrp"] == 1, 1,
                                  np.where(d["dscrgrp"] == 2, 0, np.nan))
    d["geschlecht"] = d["gndr"].map({1: "Mann", 2: "Frau"})
    d["vertrauen_polizei_hoch"] = np.where(
        d["trstplc"] >= 7, 1, np.where(d["trstplc"] <= 5, 0, np.nan))
    d["health_pos"] = 6 - d["health"] if "health" in d.columns else np.nan
    d["hincfel_pos"] = 5 - d["hincfel"] if "hincfel" in d.columns else np.nan
    d["jahr"] = d["essround"].map(RUNDEN)
    return d


def wshare(d, var, gew="w"):
    """Gewichteter Anteil mit Normalapproximations-Intervall (ohne Designeffekt).

    Args:
        d: Teildatensatz.
        var: 0/1-Variable.
        gew: Gewichtungsspalte.

    Returns:
        dict: anteil (Prozent), n, ki_lo, ki_hi (Prozent) — nicht gewichtete
            Fallzahl, Konfidenzintervall als Näherung gekennzeichnet.
    """
    t = d.dropna(subset=[var, gew])
    if len(t) == 0 or t[gew].sum() == 0:
        return dict(anteil=np.nan, n=0, ki_lo=np.nan, ki_hi=np.nan)
    p = float((t[var] * t[gew]).sum() / t[gew].sum())
    n = len(t)
    se = np.sqrt(p * (1 - p) / n)
    return dict(anteil=100 * p, n=n,
                ki_lo=100 * max(0, p - 1.96 * se),
                ki_hi=100 * min(1, p + 1.96 * se))


def main():
    roh = []
    for r in RUNDEN:
        try:
            roh.append(lese_runde(r))
        except FileNotFoundError as e:
            print(f"  Runde {r}: {e}")
    d = pd.concat(roh, ignore_index=True)
    d = bereinige(d)

    kont = (d.groupby(["essround", "jahr"])
              .agg(n=("cntry", "size"),
                   n_unsicher=("unsicher", "count"),
                   n_viktim=("viktim", "count"),
                   n_gew=("w", "count"))
              .reset_index())
    kont.to_csv(ROOT / "output" / "ch_ess_fallzahlen.csv", sep=";", index=False)
    print("Fallzahlen ESS Schweiz je Runde:")
    print(kont.to_string(index=False))

    # Regionale Kennung: ESS-Code (CH01–CH07, NUTS-2) nur in Runde 11 vergeben.
    if "region" in d.columns:
        reg = d.dropna(subset=["region"]).groupby(["essround", "region"]).size()
        print("\nRegionale Kennung 'region' je Runde:")
        print(reg.to_string())

    spalten = ["essround", "jahr", "region", "w", "unsicher", "unsicher_hoch",
               "viktim", "aesfdrk", "crmvct", "geschlecht", "agea", "alter_gr",
               "eisced", "tertiaer", "hinctnta", "hincfel", "hincfel_pos",
               "mh", "brncntr", "stadt_land", "diskriminiert", "uempla",
               "health", "health_pos", "ppltrst", "trstplc", "trstprl",
               "trstlgl", "trstplt", "stfgov", "stfdem", "stflife", "happy",
               "lrscale", "imwbcnt", "imsmetn", "impcntr", "nwspol",
               "vertrauen_polizei_hoch", "clsprty", "vote"]
    spalten = [s for s in spalten if s in d.columns]
    d[spalten].to_csv(OUT / "ch_ess_personen.csv", index=False, encoding="utf-8")
    print(f"\nPersonendatei: {len(d)} Zeilen -> {OUT / 'ch_ess_personen.csv'}")

    # --- Aggregate: Unsicherheit und Viktimisierung über die Zeit ----------
    zeilen = []
    for jahr, g in d.groupby("jahr"):
        for var in ("unsicher", "unsicher_hoch", "viktim"):
            r = wshare(g, var)
            zeilen.append(dict(ebene="gesamt", gruppe="Schweiz", jahr=jahr,
                               kennzahl=var, anteil=round(r["anteil"], 2),
                               n=int(r["n"]), ki_lo=round(r["ki_lo"], 2),
                               ki_hi=round(r["ki_hi"], 2)))

    # Untergruppen über alle Wellen gepoolt (Fallzahlen je Welle zu klein)
    def gruppen(var_name, werte):
        for wert in werte:
            g = d[d[var_name] == wert]
            if g["unsicher"].count() < 50:
                continue
            for kz in ("unsicher", "viktim"):
                r = wshare(g, kz)
                zeilen.append(dict(ebene=var_name, gruppe=str(wert),
                                   jahr=None, kennzahl=kz,
                                   anteil=round(r["anteil"], 2), n=int(r["n"]),
                                   ki_lo=round(r["ki_lo"], 2),
                                   ki_hi=round(r["ki_hi"], 2)))

    gruppen("geschlecht", ["Mann", "Frau"])
    gruppen("alter_gr", ["16-29", "30-44", "45-59", "60-74", "75+"])
    gruppen("stadt_land", ["Grossstadt", "Vorort", "Kleinstadt", "Dorf", "Land"])
    gruppen("tertiaer", [1, 0])
    gruppen("mh", [1, 0])
    gruppen("vertrauen_polizei_hoch", [1, 0])

    # --- Grossregionen (NUTS-2): Furcht nach Region ------------------------
    # Die Regionalkennung "region" wird erst ab Runde 5 (2010) vergeben.
    # Einzelne Wellen haben je Region nur rund 200 Befragte; deshalb werden
    # die Wellen ab 2010 gepoolt. Der Wert gilt für die Grossregion, nicht für
    # den einzelnen Kanton — das ist in der App so ausgewiesen.
    REGIONEN = {
        "CH01": "Genferseeregion", "CH02": "Espace Mittelland",
        "CH03": "Nordwestschweiz", "CH04": "Zürich",
        "CH05": "Ostschweiz", "CH06": "Zentralschweiz", "CH07": "Tessin",
    }
    if "region" in d.columns:
        dr = d.dropna(subset=["region"])
        for code, name in REGIONEN.items():
            g = dr[dr["region"] == code]
            for kz in ("unsicher", "unsicher_hoch", "viktim"):
                r = wshare(g, kz)
                zeilen.append(dict(ebene="grossregion", gruppe=name,
                                   jahr=None, kennzahl=kz,
                                   anteil=round(r["anteil"], 2), n=int(r["n"]),
                                   ki_lo=round(r["ki_lo"], 2),
                                   ki_hi=round(r["ki_hi"], 2)))
        # Fallzahl je Region und Welle zur Dokumentation
        zk = (dr.groupby(["region", "jahr"]).agg(n=("region", "size"),
                                                 n_unsicher=("unsicher", "count"))
              .reset_index())
        zk["region_name"] = zk["region"].map(REGIONEN)
        zk.to_csv(ROOT / "output" / "ch_ess_grossregionen_fallzahlen.csv",
                  sep=";", index=False)
        print(f"Grossregionen: {len(zk)} Zeilen Fallzahlen je Welle "
              f"-> output/ch_ess_grossregionen_fallzahlen.csv")

    agg = pd.DataFrame(zeilen)
    agg.to_csv(OUT / "ch_ess_aggregate.csv", sep=";", index=False,
               encoding="utf-8")
    print(f"Aggregat: {len(agg)} Zeilen -> {OUT / 'ch_ess_aggregate.csv'}")
    print(agg.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
