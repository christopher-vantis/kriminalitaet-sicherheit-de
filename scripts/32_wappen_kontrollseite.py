#!/usr/bin/env python3
"""
32_wappen_kontrollseite.py — Prüfseite mit allen Wappen
=======================================================
Baut eine einzelne HTML-Seite, die alle 16 Wappen mit ihrem Ländernamen zeigt.
Sie dient der Kontrolle: Ein falsch zugeordnetes Wappen fällt auf, wenn man es
neben dem Namen sieht — bei Flaggen reicht ein Farbvergleich, bei Wappen der
Vergleich mit dem bekannten Landeszeichen.

Ausgabe: dashboard/_verify/wappen_kontrolle.html
"""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "dashboard"))
from wappen_util import wappen_laden                          # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
ZIEL = ROOT / "dashboard" / "_verify" / "wappen_kontrolle.html"

NAMEN = {
    "DE1": "Baden-Württemberg", "DE2": "Bayern", "DE3": "Berlin",
    "DE4": "Brandenburg", "DE5": "Bremen", "DE6": "Hamburg",
    "DE7": "Hessen", "DE8": "Mecklenburg-Vorpommern", "DE9": "Niedersachsen",
    "DEA": "Nordrhein-Westfalen", "DEB": "Rheinland-Pfalz", "DEC": "Saarland",
    "DED": "Sachsen", "DEE": "Sachsen-Anhalt", "DEF": "Schleswig-Holstein",
    "DEG": "Thüringen",
}


def main():
    wappen = wappen_laden()
    fehlend = [n for n in NAMEN if n not in wappen]
    kacheln = []
    for nuts in sorted(NAMEN, key=lambda n: NAMEN[n]):
        svg = wappen.get(nuts, "")
        kacheln.append(
            f'<div class="k"><div class="w">{svg}</div>'
            f'<div class="n">{NAMEN[nuts]}</div>'
            f'<div class="c">{nuts}</div></div>')

    html = f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<title>Wappen-Kontrolle</title>
<style>
body{{font-family:system-ui,sans-serif;background:#faf8f5;color:#12100e;margin:0;padding:24px}}
h1{{font-size:20px;margin:0 0 4px}}
p{{color:#6b645e;margin:0 0 20px;font-size:14px}}
.raster{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;max-width:1100px}}
.k{{background:#fff;border:1px solid #e7e2dc;border-radius:10px;padding:14px;text-align:center}}
.w{{height:96px;display:flex;align-items:center;justify-content:center;margin-bottom:10px}}
.w svg{{height:96px;width:auto;max-width:100%}}
.n{{font-weight:600;font-size:15px}}
.c{{color:#8d8680;font-size:12px;margin-top:2px}}
</style></head><body>
<h1>Wappen-Kontrolle</h1>
<p>Jedes Wappen neben seinem Bundesland. Zu prüfen: Stimmt jedes Wappen mit dem
bekannten Landeswappen überein?</p>
<div class="raster">{''.join(kacheln)}</div>
</body></html>"""

    ZIEL.parent.mkdir(exist_ok=True)
    ZIEL.write_text(html, encoding="utf-8")
    print(f"{len(wappen)} Wappen in der Prüfseite | fehlend: {fehlend or 'keine'}")
    print(f"-> {ZIEL}")

    # Screenshot für die Kontrolle
    bild = ZIEL.with_suffix(".png")
    r = subprocess.run(
        ["chromium", "--headless=new", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=8000", "--window-size=1180,1000",
         f"--screenshot={bild}", ZIEL.as_uri()],
        capture_output=True, text=True, timeout=120)
    print(f"Screenshot: {bild}" if bild.exists() else f"Screenshot fehlgeschlagen: {r.stderr[-200:]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
