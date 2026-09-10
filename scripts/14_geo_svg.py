#!/usr/bin/env python3
"""
14_geo_svg.py — Bundesland-Geometrien als SVG-Pfade
===================================================
Wandelt die NUTS-1-Regionen Deutschlands (= Bundesländer) aus der offiziellen
Eurostat/GISCO-Geometrie in SVG-Pfade um, damit die Webapp eine klickbare
Deutschlandkarte ohne externe Kartendienste zeichnen kann.

Quelle: Eurostat/GISCO, NUTS-RG 2021, Maßstab 1:20 Mio, WGS84
        https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/
        NUTS_RG_20M_2021_4326.geojson  (Lizenz: CC BY 4.0)

Projektion: Lambert azimuthal flächentreu (EPSG:3035, lat0=52, lon0=10) —
die Standardprojektion für amtliche Karten in Deutschland.

Ausgabe: output/bundeslaender_svg.json
  { "NUTS_ID": {"name": ..., "d": "M..." } , ... , "_viewbox": "0 0 w h" }
"""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUELLE = ROOT / "data/raw/laender_geo/NUTS_RG_20M_2021_4326.geojson"
OUT = ROOT / "output/bundeslaender_svg.json"

# NUTS-1 in Deutschland = Bundesländer
NAMEN = {
    "DE1": "Baden-Württemberg", "DE2": "Bayern", "DE3": "Berlin",
    "DE4": "Brandenburg", "DE5": "Bremen", "DE6": "Hamburg",
    "DE7": "Hessen", "DE8": "Mecklenburg-Vorpommern", "DE9": "Niedersachsen",
    "DEA": "Nordrhein-Westfalen", "DEB": "Rheinland-Pfalz", "DEC": "Saarland",
    "DED": "Sachsen", "DEE": "Sachsen-Anhalt", "DEF": "Schleswig-Holstein",
    "DEG": "Thüringen",
}

LAT0, LON0 = 52.0, 10.0          # Zentrum der Projektion (EPSG:3035)
R = 6378137.0                     # Erdradius in Metern


def projiziere(lon, lat):
    """Lambert azimuthal flächentreu (EPSG:3035), Rückgabe in Metern."""
    phi1 = math.radians(LAT0)
    lam0 = math.radians(LON0)
    phi = math.radians(lat)
    lam = math.radians(lon)

    def q(phi):
        return math.sqrt(2 / (1 + math.sin(phi1) * math.sin(phi) +
                              math.cos(phi1) * math.cos(phi) * math.cos(lam - lam0)))

    # Kugel-Approximation der LAEA (für Kartendarstellung ausreichend)
    k = math.sqrt(2 / (1 + math.sin(phi1) * math.sin(phi) +
                       math.cos(phi1) * math.cos(phi) * math.cos(lam - lam0)))
    x = R * k * math.cos(phi) * math.sin(lam - lam0)
    y = R * k * (math.cos(phi1) * math.sin(phi) -
                 math.sin(phi1) * math.cos(phi) * math.cos(lam - lam0))
    return x, y


def ring_pfad(punkte, sx, sy, dx, dy):
    """Punkte sind bereits projiziert (Meter) — hier nur skalieren."""
    teile = []
    for i, (x, y) in enumerate(punkte):
        px, py = x * sx + dx, dy - y * sy
        teile.append(f"{'M' if i == 0 else 'L'}{px:.1f},{py:.1f}")
    return "".join(teile) + "Z"


def schwerpunkt(ringe):
    """Flächenschwerpunkt (Näherung) für die Beschriftung."""
    bestes, flaeche = None, 0.0
    for r in ringe:
        a = 0.0
        cx = cy = 0.0
        for i in range(len(r) - 1):
            x0, y0 = r[i]
            x1, y1 = r[i + 1]
            kreuz = x0 * y1 - x1 * y0
            a += kreuz
            cx += (x0 + x1) * kreuz
            cy += (y0 + y1) * kreuz
        if abs(a) < 1e-9:
            continue
        a *= 0.5
        if abs(a) > abs(flaeche):
            flaeche = a
            bestes = (cx / (6 * a), cy / (6 * a))
    return bestes


def main():
    geo = json.loads(QUELLE.read_text(encoding="utf-8"))
    features = []
    for f in geo["features"]:
        props = f.get("properties", {})
        nid = (props.get("NUTS_ID") or "").strip()
        if nid not in NAMEN:
            continue
        if props.get("LEVL_CODE") not in (1, "1"):
            continue
        features.append((nid, f.get("geometry") or {}))

    # Alle Koordinaten projizieren, um die Zeichenfläche zu bestimmen
    roh = {}
    xs, ys = [], []
    for nid, g in features:
        ringe = []
        typ = g.get("type")
        koord = g.get("coordinates") or []
        polygons = [koord] if typ == "Polygon" else koord
        for poly in polygons:
            for ring in poly:
                if len(ring) < 4:
                    continue
                pts = []
                for c in ring:
                    x, y = projiziere(c[0], c[1])
                    pts.append((x, y))
                    xs.append(x)
                    ys.append(y)
                ringe.append(pts)
        roh[nid] = ringe

    if not xs:
        raise SystemExit("Keine Geometrien gefunden")

    breite_ziel = 1000.0
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sx = breite_ziel / (maxx - minx)
    sy = sx                      # gleiche Skalierung in x und y (verzerrungsfrei)
    hoehe_ziel = (maxy - miny) * sy
    dx, dy = -minx * sx, maxy * sy

    ergebnis = {}
    for nid, ringe in roh.items():
        pfade = [ring_pfad(r, sx, sy, dx, dy) for r in ringe]
        sp = schwerpunkt(ringe)
        label = None
        if sp:
            lx, ly = sp[0] * sx + dx, dy - sp[1] * sy
            label = [round(lx, 1), round(ly, 1)]
        ergebnis[nid] = {"name": NAMEN[nid], "d": " ".join(pfade), "label": label}
    ergebnis["_viewbox"] = f"0 0 {breite_ziel:.0f} {hoehe_ziel:.0f}"

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(ergebnis, ensure_ascii=False), encoding="utf-8")
    print(f"{len(ergebnis)-1} Bundesländer -> {OUT} ({OUT.stat().st_size/1024:.0f} KB)")
    print("Zeichenfläche:", ergebnis["_viewbox"])
    for nid, v in list(ergebnis.items())[:4]:
        if nid == "_viewbox":
            continue
        print(f"  {nid} {v['name']:24s} Pfadlänge {len(v['d']):7d} Zeichen  "
              f"Label {v.get('label')}")


if __name__ == "__main__":
    main()
