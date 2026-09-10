#!/usr/bin/env python3
"""
28_wappen_holen.py — Landeswappen der Bundesländer als Datei ablegen
====================================================================
Lädt die Wappen der 16 Bundesländer von Wikimedia Commons.

Wappen statt Flaggen: Die einfachen Streifenflaggen sind teils nicht
unterscheidbar — Nordrhein-Westfalens grün-weiß-rot etwa gleicht der
ungarischen Flagge. Die Wappen sind die bekannteren Landeszeichen und
eindeutig zuzuordnen.

Die Dateiadressen werden über die API von Wikimedia Commons ermittelt, nicht
aus dem Dateinamen geraten. Die API wird gebündelt abgefragt und mit Pausen:
Einzelabfragen in kurzer Folge beantwortet sie mit HTTP 429.

Amtliche Wappen sind nach § 5 UrhG gemeinfrei; die Dateien auf Commons sind
entsprechend gekennzeichnet. Sie werden hier nur für die Anzeige
zwischengespeichert.

Ausgabe: dashboard/wappen/<NUTS>.svg
"""
import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ZIEL = ROOT / "dashboard" / "wappen"

# NUTS-Code -> Dateiname auf Wikimedia Commons
WAPPEN = {
    "DE1": "Coat of arms of Baden-Württemberg (lesser).svg",
    "DE2": "Bayern Wappen.svg",
    "DE3": "Coat of arms of Berlin.svg",
    "DE4": "Brandenburg Wappen.svg",
    "DE5": "Bremen Wappen(Mittel).svg",
    "DE6": "Coat of arms of Hamburg.svg",
    "DE7": "Coat of arms of Hesse.svg",
    "DE8": "Coat of arms of Mecklenburg-Western Pomerania (great).svg",
    "DE9": "Coat of arms of Lower Saxony.svg",
    "DEA": "Coat of arms of North Rhine-Westphalia.svg",
    "DEB": "Coat of arms of Rhineland-Palatinate.svg",
    "DEC": "Coat of arms of Saarland.svg",
    "DED": "Coat of arms of Saxony.svg",
    "DEE": "Coat of arms of Saxony-Anhalt.svg",
    "DEF": "Coat of arms of Schleswig-Holstein.svg",
    "DEG": "Coat of arms of Thuringia.svg",
}

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")


def hole(url, rohdaten=False, versuche=3):
    for versuch in range(versuche):
        try:
            anfrage = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(anfrage, timeout=60) as antwort:
                return antwort.read() if rohdaten else antwort.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and versuch < versuche - 1:
                time.sleep(8 * (versuch + 1))
                continue
            raise
        except Exception:                                           # noqa: BLE001
            if versuch < versuche - 1:
                time.sleep(4)
                continue
            raise
    return None


def adressen_ermitteln():
    """Holt die Dateiadressen gebündelt (eine Abfrage für alle 16)."""
    titel = "|".join("File:" + n for n in WAPPEN.values())
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
           "&formatversion=2&prop=imageinfo&iiprop=url&titles="
           + urllib.parse.quote(titel))
    daten = json.loads(hole(url))
    ergebnis = {}
    for seite in daten.get("query", {}).get("pages", []):
        name = seite.get("title", "").replace("File:", "")
        info = (seite.get("imageinfo") or [{}])[0]
        adresse = info.get("url")
        if adresse:
            ergebnis[name] = adresse.split("?")[0]
    return ergebnis


def main():
    ZIEL.mkdir(exist_ok=True)
    adressen = adressen_ermitteln()
    print(f"{len(adressen)} von {len(WAPPEN)} Adressen ermittelt\n")
    gesamt, fehlend = 0, []
    for nuts, dateiname in WAPPEN.items():
        adresse = adressen.get(dateiname)
        if not adresse:
            fehlend.append((nuts, dateiname, "Adresse nicht gefunden"))
            print(f"  {nuts}: Adresse fehlt — {dateiname}")
            continue
        try:
            daten = hole(adresse, rohdaten=True)
        except Exception as exc:                                    # noqa: BLE001
            fehlend.append((nuts, dateiname, type(exc).__name__))
            print(f"  {nuts}: FEHLER {type(exc).__name__} — {dateiname}")
            continue
        if not daten or not daten.lstrip().startswith(b"<"):
            fehlend.append((nuts, dateiname, "keine SVG-Datei"))
            print(f"  {nuts}: keine SVG-Datei — {dateiname}")
            continue
        (ZIEL / f"{nuts}.svg").write_bytes(daten)
        gesamt += len(daten)
        print(f"  {nuts}: {len(daten)/1024:7.1f} KB  {dateiname}")
        time.sleep(1.0)

    print(f"\n{gesamt/1024:.0f} KB in {ZIEL} | fehlend: {len(fehlend)}")
    return 1 if fehlend else 0


if __name__ == "__main__":
    raise SystemExit(main())
