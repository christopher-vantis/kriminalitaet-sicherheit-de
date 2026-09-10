#!/usr/bin/env python3
"""
24_schrift_einbetten.py — Webfont lokal einbetten
=================================================
Die App deklarierte bisher "Inter", lud die Schrift aber nie — der Browser fiel
auf Systemschriften zurück, was den uneinheitlichen Eindruck erklärt.

Dieses Skript lädt IBM Plex Sans (latin-Subset, vier Schnitte) von Google Fonts,
kodiert sie als data:-URL und schreibt sie nach dashboard/fonts/plex.css.
Damit bleibt die App vollständig offline nutzbar und hat auf jedem Gerät
dieselbe Typografie. Achtung: Nicht die von Google ausgelieferte CSS-Datei
direkt einbetten — sie verweist auf externe URLs.

Ausgabe: dashboard/fonts/plex.css  (in die App eingebettet via build_app.py)
"""
import base64
import pathlib
import re
import urllib.request

ZIELE = {"400": "normal", "600": "normal", "700": "normal"}
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")

ROOT = pathlib.Path(__file__).resolve().parent.parent
AUS = ROOT / "dashboard/fonts"
AUS.mkdir(parents=True, exist_ok=True)


def hole(url):
    anfrage = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(anfrage, timeout=60) as antwort:
        return antwort.read()


def main():
    bloecke = []
    for weight in ZIELE:
        css_url = (f"https://fonts.googleapis.com/css2?family=IBM+Plex+Sans"
                   f":wght@{weight}&display=swap")
        css = hole(css_url).decode("utf-8")
        # @font-face-Blöcke einzeln durchgehen und den mit dem reinen
        # latin-Bereich wählen (der letzte Block ist üblicherweise latin).
        treffer = re.findall(
            r"@font-face\s*\{(.*?)\}", css, re.S)
        gewaehlt = None
        for block in treffer:
            if "unicode-range" in block and "U+0000-00FF" in block:
                gewaehlt = block
        if not gewaehlt:
            print(f"  {weight}: kein latin-Block gefunden")
            continue
        url = re.search(r"url\((https://[^)]+\.woff2)\)", gewaehlt)
        if not url:
            print(f"  {weight}: keine woff2-URL")
            continue
        daten = hole(url.group(1))
        b64 = base64.b64encode(daten).decode("ascii")
        bloecke.append(
            "@font-face{font-family:'IBM Plex Sans';font-style:normal;"
            f"font-weight:{weight};font-display:swap;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}"
        )
        print(f"  {weight}: {len(daten)/1024:.0f} KB eingebettet")

    css_ausgabe = "\n".join(bloecke)
    (AUS / "plex.css").write_text(css_ausgabe, encoding="utf-8")
    print(f"\n-> {AUS/'plex.css'} ({len(css_ausgabe)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
