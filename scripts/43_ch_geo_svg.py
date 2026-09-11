#!/usr/bin/env python3
"""
43_ch_geo_svg.py — Kantonsgeometrien als SVG-Pfade
==================================================
Wandelt die NUTS-3-Regionen der Schweiz (= Kantone) aus der offiziellen
Eurostat/GISCO-Geometrie in SVG-Pfade um, damit die Webapp eine klickbare
Schweizerkarte ohne externe Kartendienste zeichnen kann.

Quelle: Eurostat/GISCO, NUTS-RG 2021, Maßstab 1:3 Mio, WGS84
        https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/
        NUTS_RG_03M_2021_4326.geojson  (Lizenz: CC BY 4.0)

Projektion: Lambert azimuthal flächentreu (Kugelform), Zentrum 46.8 N / 8.2 E
— bei der Ausdehnung der Schweiz (5.9–10.5 E, 45.8–47.8 N) sind die
Verzerrungen unter 0.5 % und damit unterhalb der Strichstärke. Die amtliche
Schweizer Projektion (CH1903+/LV95, schiefachsige Mercator) wäre genauer,
bringt für eine Choroplethenkarte dieses Maßstabs aber keinen sichtbaren
Unterschied; die Wahl ist hier bewusst dokumentiert.

NUTS-3 der Schweiz = Kantone; die BFS-Kantonscodes 1–26 (PKS) werden über
KT_NUTS zugeordnet.

Ausgabe: output/ch_kantone_svg.json
  { "CH040": {"name": ..., "kanton_nr": 1, "d": "M...", "label": [x, y]}, ...,
    "_viewbox": "0 0 w h" }
"""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUELLE = ROOT / "data/raw/laender_geo/NUTS_RG_03M_2021_4326.geojson"
OUT = ROOT / "output/ch_kantone_svg.json"

# NUTS-3-Code -> (BFS-Kantonsnummer, deutscher Kantonsname)
KT_NUTS = {
    "CH040": (1, "Zürich"), "CH021": (2, "Bern"), "CH061": (3, "Luzern"),
    "CH062": (4, "Uri"), "CH063": (5, "Schwyz"), "CH064": (6, "Obwalden"),
    "CH065": (7, "Nidwalden"), "CH051": (8, "Glarus"), "CH066": (9, "Zug"),
    "CH022": (10, "Freiburg"), "CH023": (11, "Solothurn"),
    "CH031": (12, "Basel-Stadt"), "CH032": (13, "Basel-Landschaft"),
    "CH052": (14, "Schaffhausen"), "CH053": (15, "Appenzell Ausserrhoden"),
    "CH054": (16, "Appenzell Innerrhoden"), "CH055": (17, "St. Gallen"),
    "CH056": (18, "Graubünden"), "CH033": (19, "Aargau"),
    "CH057": (20, "Thurgau"), "CH070": (21, "Tessin"),
    "CH011": (22, "Waadt"), "CH012": (23, "Wallis"),
    "CH024": (24, "Neuenburg"), "CH013": (25, "Genf"), "CH025": (26, "Jura"),
}

LAT0, LON0 = 46.8, 8.2
R = 6371000.0


def projiziere(lon, lat):
    """Lambert azimuthal flächentreu um (LON0, LAT0), Kugelnäherung.

    Args:
        lon: Länge in Grad.
        lat: Breite in Grad.

    Returns:
        tuple[float, float]: x, y in Metern.
    """
    phi1, lam0 = math.radians(LAT0), math.radians(LON0)
    phi, lam = math.radians(lat), math.radians(lon)
    nenner = 1 + math.sin(phi1) * math.sin(phi) + \
        math.cos(phi1) * math.cos(phi) * math.cos(lam - lam0)
    k = math.sqrt(2 / nenner)
    x = R * k * math.cos(phi) * math.sin(lam - lam0)
    y = R * k * (math.cos(phi1) * math.sin(phi) -
                 math.sin(phi1) * math.cos(phi) * math.cos(lam - lam0))
    return x, y


def ring_pfad(punkte, sx, sy, dx, dy):
    """Baut einen SVG-Pfad aus bereits projizierten Punkten."""
    return "".join(f"{'M' if i == 0 else 'L'}{x * sx + dx:.1f},{dy - y * sy:.1f}"
                   for i, (x, y) in enumerate(punkte)) + "Z"


def schwerpunkt(ringe):
    """Flächenschwerpunkt der grössten Teilfläche (für die Beschriftung)."""
    bestes, flaeche = None, 0.0
    for r in ringe:
        a = cx = cy = 0.0
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


def flaeche_km2(ringe):
    """Fläche der Ringe in km² (projizierte Meter, Gauß'sche Trapezformel).

    Args:
        ringe: Liste projizierter Ringe in Metern.

    Returns:
        float: Fläche in Quadratkilometern (Betrag der Summe).
    """
    gesamt = 0.0
    for r in ringe:
        a = 0.0
        for i in range(len(r) - 1):
            a += r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1]
        gesamt += a / 2
    return abs(gesamt) / 1e6


def main():
    geo = json.loads(QUELLE.read_text(encoding="utf-8"))
    roh, xs, ys, flaechen = {}, [], [], {}
    for f in geo["features"]:
        p = f.get("properties", {})
        nid = (p.get("NUTS_ID") or "").strip()
        if nid not in KT_NUTS:
            continue
        g = f.get("geometry") or {}
        koord = g.get("coordinates") or []
        polys = [koord] if g.get("type") == "Polygon" else koord
        ringe = []
        for poly in polys:
            for ring in poly:
                if len(ring) < 4:
                    continue
                pts = [projiziere(c[0], c[1]) for c in ring]
                for x, y in pts:
                    xs.append(x)
                    ys.append(y)
                ringe.append(pts)
        roh[nid] = ringe
        flaechen[nid] = flaeche_km2(ringe)

    if len(roh) != 26:
        raise SystemExit(f"Nur {len(roh)} Kantone gefunden — erwartet: 26")

    breite_ziel = 1000.0
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sx = breite_ziel / (maxx - minx)      # gleiche Skalierung x/y
    hoehe_ziel = (maxy - miny) * sx
    dx, dy = -minx * sx, maxy * sx

    ergebnis = {}
    for nid, ringe in roh.items():
        nr, name = KT_NUTS[nid]
        sp = schwerpunkt(ringe)
        lx, ly = (sp[0] * sx + dx, dy - sp[1] * sx) if sp else (None, None)
        ergebnis[nid] = {
            "name": name, "kanton_nr": nr, "flaeche_km2": round(flaechen[nid], 1),
            "d": " ".join(ring_pfad(r, sx, sx, dx, dy) for r in ringe),
            "label": None if sp is None else [round(lx, 1), round(ly, 1)],
        }
    ergebnis["_viewbox"] = f"0 0 {breite_ziel:.0f} {hoehe_ziel:.0f}"
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(ergebnis, ensure_ascii=False), encoding="utf-8")
    print(f"{len(ergebnis) - 1} Kantone -> {OUT} ({OUT.stat().st_size/1024:.0f} KB)")
    print("Zeichenfläche:", ergebnis["_viewbox"])
    # Kontrolle: Flächensumme gegen die amtliche Gesamtfläche der Schweiz
    print(f"Flächensumme: {sum(flaechen.values()):,.0f} km² "
          "(amtlich 41'291 km² ohne Seen-Anteile)".replace(",", "'"))
    print(f"Kleinster Kanton: {min(flaechen, key=flaechen.get)} "
          f"{min(flaechen.values()):.1f} km² | grösster: "
          f"{max(flaechen, key=flaechen.get)} {max(flaechen.values()):.0f} km²")


if __name__ == "__main__":
    main()
