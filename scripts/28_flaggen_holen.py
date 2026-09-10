#!/usr/bin/env python3
"""
28_flaggen_holen.py — Flaggen der Bundesländer als Datei ablegen
================================================================
Lädt die amtlichen Landesflaggen von Wikimedia Commons. Die Auswahl folgt der
Liste der Flaggen deutscher Länder: Landesflagge (ohne Wappen), wo vorhanden —
das ist die Fassung, die die Länder selbst führen.

Die Dateiadressen werden über die API von Wikimedia Commons ermittelt, nicht
aus dem Dateinamen geraten: Ein geratener Name liefert stillschweigend eine
Fehlerseite statt der Flagge.

Amtliche Werke sind nach § 5 UrhG gemeinfrei; die Dateien auf Commons sind
entsprechend gekennzeichnet. Sie werden hier nur zwischengespeichert.

Ausgabe: dashboard/flaggen/<NUTS>.svg
"""
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ZIEL = ROOT / "dashboard" / "flaggen"
ZIEL.mkdir(exist_ok=True)

# NUTS-Code -> Dateiname auf Wikimedia Commons
FLAGGEN = {
    "DE1": "Flag of Baden-Württemberg.svg",
    "DE2": "Flag of Bavaria (lozengy).svg",
    "DE3": "Flag of Berlin.svg",
    "DE4": "Flag of Brandenburg.svg",
    "DE5": "Flag of Bremen.svg",
    "DE6": "Flag of Hamburg.svg",
    "DE7": "Flag of Hesse.svg",
    "DE8": "Flag of Mecklenburg-Western Pomerania.svg",
    "DE9": "Flag of Lower Saxony.svg",
    "DEA": "Flag of North Rhine-Westphalia.svg",
    "DEB": "Flag of Rhineland-Palatinate.svg",
    "DEC": "Flag of Saarland.svg",
    "DED": "Flag of Saxony.svg",
    "DEE": "Flag of Saxony-Anhalt (state).svg",
    "DEF": "Flag of Schleswig-Holstein.svg",
    "DEG": "Flag of Thuringia.svg",
}

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")


def hole(url, rohdaten=False):
    anfrage = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(anfrage, timeout=60) as antwort:
        return antwort.read() if rohdaten else antwort.read().decode("utf-8")


def bild_adressen():
    """Fragt die tatsächlichen Dateiadressen bei Commons ab."""
    titel = "|".join("File:" + n for n in FLAGGEN.values())
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
           "&formatversion=2&prop=imageinfo&iiprop=url&titles="
           + urllib.parse.quote(titel))
    daten = json.loads(hole(url))
    adressen = {}
    for seite in daten.get("query", {}).get("pages", []):
        name = seite.get("title", "").replace("File:", "")
        info = (seite.get("imageinfo") or [{}])[0]
        adressen[name] = info.get("url")
    return adressen


def main():
    adressen = bild_adressen()
    gesamt, fehlend = 0, []
    for nuts, dateiname in FLAGGEN.items():
        adresse = adressen.get(dateiname)
        # Die API hängt Tracking-Parameter an (?utm_source=...). Damit antwortet
        # der Dateiserver mit einem Fehler, deshalb abschneiden.
        if adresse:
            adresse = adresse.split("?")[0]
        if not adresse:
            fehlend.append(dateiname)
            print(f"  {nuts}: keine Adresse gefunden — {dateiname}")
            continue
        try:
            daten = hole(adresse, rohdaten=True)
        except Exception as exc:                                    # noqa: BLE001
            fehlend.append(dateiname)
            print(f"  {nuts}: FEHLER {type(exc).__name__} — {dateiname}")
            continue
        if not daten.lstrip().startswith(b"<"):
            fehlend.append(dateiname)
            print(f"  {nuts}: keine SVG-Datei erhalten — {dateiname}")
            continue
        (ZIEL / f"{nuts}.svg").write_bytes(daten)
        gesamt += len(daten)
        print(f"  {nuts}: {len(daten)/1024:6.1f} KB  {dateiname}")
    print(f"\n{gesamt/1024:.0f} KB in {ZIEL} | fehlend: {len(fehlend)}")
    for f in fehlend:
        print("   fehlt:", f)


if __name__ == "__main__":
    main()
