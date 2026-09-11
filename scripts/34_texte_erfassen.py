#!/usr/bin/env python3
"""
34_texte_erfassen.py — Alle sichtbaren Texte der App auflisten
==============================================================
Grundlage für die englische Fassung: Bevor übersetzt werden kann, muss
vollständig bekannt sein, welche Texte es gibt. Das Skript liest die erzeugte
index.html, zieht alles Sichtbare heraus (ohne Code, Daten und Plotly-Innenleben)
und gruppiert es nach Herkunft.

Ausgabe: docs/TEXTE_INVENTAR.md
"""
import json
import pathlib
import re
import collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUELLE = ROOT / "dashboard" / "index.html"
ZIEL = ROOT / "docs" / "TEXTE_INVENTAR.md"


def textknoten(html):
    """Sichtbare Textstellen aus dem HTML ziehen, ohne Code und Daten."""
    # Skript-, Stil- und Datenblöcke entfernen
    for muster in (r"<script.*?</script>", r"<style.*?</style>",
                   r"<svg.*?</svg>", r"<!--.*?-->"):
        html = re.sub(muster, " ", html, flags=re.S | re.I)
    roh = re.sub(r"<[^>]+>", "\n", html)
    zeilen = []
    for z in roh.split("\n"):
        z = " ".join(z.split())
        if len(z) >= 3 and not z.replace(".", "").replace(",", "").isdigit():
            zeilen.append(z)
    return zeilen


def main():
    if not QUELLE.exists():
        print("index.html fehlt — zuerst bauen")
        return 1
    html = QUELLE.read_text(encoding="utf-8")

    # 1) Texte aus dem HTML
    aus_html = textknoten(html)
    einmalig = []
    gesehen = set()
    for z in aus_html:
        if z not in gesehen:
            gesehen.add(z)
            einmalig.append(z)

    # 2) Texte aus den Diagramm-Metadaten (JSON)
    meta = re.search(r'id="figmeta" type="application/json">(.*?)</script>', html, re.S)
    diagramme = json.loads(meta.group(1)) if meta else []

    # 3) Texte aus dem Datenblock, die in der Oberfläche erscheinen
    daten = re.search(r'id="daten" type="application/json">(.*?)</script>', html, re.S)
    d = json.loads(daten.group(1)) if daten else {}

    zeilen = ["# Inventar der Texte", "",
              f"Erfasst am {pathlib.Path(__file__).stat().st_mtime}",
              "Grundlage für die englische Fassung.", ""]

    zeilen.append(f"## Texte im HTML ({len(einmalig)} Einträge)\n")
    for z in einmalig:
        if len(z) < 200:
            zeilen.append(f"- {z}")
        else:
            zeilen.append(f"- {z[:200]} … ({len(z)} Zeichen)")

    zeilen.append("")
    zeilen.append(f"## Diagramme ({len(diagramme)})\n")
    zeilen.append("| Kennung | Titel | Kurztext | Quelle | Langtext |")
    zeilen.append("|---|---|---|---|---|")
    for m in diagramme:
        zeilen.append(
            f"| {m['id']} | {m.get('titel','')[:60]} | "
            f"{len(m.get('unter') or '')} Z. | {len(m.get('quelle') or '')} Z. | "
            f"{len(m.get('langtext') or '')} Z. |")

    # Ländertexte
    laender = d.get("laender", {})
    if laender:
        zeilen.append("")
        zeilen.append(f"## Ländertexte ({len(laender)} Bundesländer)\n")
        bsp = next(iter(laender.values()))
        for schluessel in bsp:
            if isinstance(bsp[schluessel], str) and len(bsp[schluessel]) > 30:
                zeilen.append(f"- Feld `{schluessel}`: Text je Bundesland")

    # Umfang schätzen
    gesamt = sum(len(z) for z in einmalig)
    for m in diagramme:
        gesamt += sum(len(m.get(k) or "") for k in ("titel", "unter", "quelle", "langtext"))
    for l in laender.values():
        gesamt += sum(len(v) for v in l.values() if isinstance(v, str))

    zeilen.append("")
    zeilen.append(f"## Umfang\n\nZu übersetzende Zeichen: rund {gesamt:,}".replace(",", "."))

    ZIEL.parent.mkdir(exist_ok=True)
    ZIEL.write_text("\n".join(zeilen), encoding="utf-8")
    print(f"{len(einmalig)} Textstellen im HTML, {len(diagramme)} Diagramme, "
          f"{len(laender)} Ländertexte")
    print(f"Umfang: rund {gesamt:,} Zeichen".replace(",", "."))
    print(f"-> {ZIEL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
