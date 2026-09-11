#!/usr/bin/env python3
"""
39_sprachfassungen_bauen.py — Englische Fassungen für alle Seiten
=================================================================
Die Website hat drei Seiten:
    index.html        Startseite (Länderauswahl)
    deutschland.html  Deutschland-Fassung
    schweiz.html      Schweiz-Fassung

Dieses Skript erzeugt zu jeder die englische Fassung und setzt auf beiden
Sprachfassungen einen Umschalter, der zwischen ihnen verlinkt:

    index.html        <-> index-en.html
    deutschland.html  <-> deutschland-en.html
    schweiz.html      <-> schweiz-en.html

Warum als eigener Schritt: Die Seiten entstehen in drei getrennten Skripten
(build_app.py, build_ch.py, build_start.py). Statt in jedes eine eigene
Übersetzungslogik zu schreiben, wird hier einmal gearbeitet — die Fassungen
werden nach dem Bau erzeugt.

Aufruf:  python3 scripts/39_sprachfassungen_bauen.py
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DASH = ROOT / "dashboard"
SPRACHTEXTE = DASH / "sprachtexte.json"

# Seitenpaare: deutsche Datei -> englische Datei
SEITEN = [("index.html", "index-en.html"),
          ("deutschland.html", "deutschland-en.html"),
          ("schweiz.html", "schweiz-en.html")]


def uebersetze(text, tabelle, sprache):
    """Ersetzt deutsche Oberflächentexte durch die englische Fassung.

    Drei Bereiche werden getrennt behandelt, weil sie unterschiedlich
    empfindlich sind:

    - Datenblöcke (JSON in Skripten): vollständig ersetzen. Sie enthalten die
      Diagrammtexte und Deliktnamen und keine Kommentare.
    - Logik-Skripte: nur ersetzen, NICHT die Leerzeichen normalisieren. Im
      JavaScript stehen einzeilige //-Kommentare; ohne Zeilenumbrüche
      kommentiert der erste davon den gesamten Rest des Codes aus. Die Seite
      bliebe dann leer — ohne Fehlermeldung.
    - HTML-Körper: Leerzeichen vereinheitlichen (damit über mehrere Zeilen
      verteilte Sätze gefunden werden) und ersetzen.

    Args:
        text: vollständiges HTML.
        tabelle: Zuordnung deutscher Text -> englischer Text.
        sprache: 'de' oder 'en' — bei 'de' wird unverändert zurückgegeben.

    Returns:
        str: HTML in der gewünschten Sprache.
    """
    if sprache == "de" or not tabelle:
        return text

    def datenblock(m):
        block = m.group(0)
        for dt in sorted(tabelle, key=len, reverse=True):
            if len(dt) > 2:
                block = block.replace(dt, tabelle[dt])
        return block

    text = re.sub(r'<script id="(?:daten|figuren|figmeta|i18n)"[^>]*>.*?</script>',
                  datenblock, text, flags=re.S)

    geschuetzt = {}

    def merken(m):
        schluessel = f"@@SCHUTZ{len(geschuetzt)}@@"
        geschuetzt[schluessel] = m.group(0)
        return schluessel

    text = re.sub(r"<!--PLOTLY-->", merken, text)

    def merken_script(m):
        # Auch hier: Bibliotheksblöcke nur schützen, nicht bearbeiten.
        return merken(m)

    text = re.sub(r"<script\b[^>]*>.*?</script\s*>", merken_script, text, flags=re.S | re.I)

    text = re.sub(r"\s+", " ", text)
    for dt in sorted(tabelle, key=len, reverse=True):
        if len(dt) > 2:
            text = text.replace(dt, tabelle[dt])

    for schluessel, inhalt in geschuetzt.items():
        text = text.replace(schluessel, inhalt)

    def in_skripten(m):
        block = m.group(0)
        # Die Diagramm-Bibliothek (mehrere Megabyte) bleibt unangetastet: Sie
        # enthält Code-Strings wie "csv" oder "date", die keine Oberflächentexte
        # sind. Eine Ersetzung dort zerstört die Bibliothek — die Seite zeigt
        # dann keine Diagramme mehr, mit "Plotly is not defined" als Folgefehler.
        if len(block) > 500_000:
            return block
        for dt in sorted(tabelle, key=len, reverse=True):
            if len(dt) > 3 and "\n" not in dt:
                block = block.replace(dt, tabelle[dt])
        return block

    return re.sub(r"<script\b[^>]*>.*?</script\s*>", in_skripten, text,
                  flags=re.S | re.I)


def umschalter(datei_de, datei_en):
    """Baut den Sprachumschalter als HTML.

    Args:
        datei_de: Dateiname der deutschen Fassung.
        datei_en: Dateiname der englischen Fassung.

    Returns:
        str: HTML des Umschalters (zwei Verweise).
    """
    return (f'<div class="sprachwahl">'
            f'<a href="{datei_de}" data-sprache="de" class="aktiv">DE</a>'
            f'<a href="{datei_en}" data-sprache="en">EN</a></div>')


def setze_umschalter(html, datei_de, datei_en, aktiv):
    """Setzt den Umschalter in eine Seite ein und markiert die aktive Sprache.

    Der Umschalter sitzt oben rechts im Kopfbereich. Fehlt der Kopfbereich,
    wird nichts verändert — das ist ein Hinweis auf eine unerwartete
    Seitenstruktur, keine stille Fehlfunktion.

    Args:
        html: vollständiges HTML.
        datei_de: Dateiname der deutschen Fassung.
        datei_en: Dateiname der englischen Fassung.
        aktiv: 'de' oder 'en'.

    Returns:
        tuple: (HTML, bool) — HTML mit Umschalter, und ob er gesetzt wurde.
    """
    block = umschalter(datei_de, datei_en)
    if aktiv == "en":
        block = block.replace('data-sprache="de" class="aktiv"', 'data-sprache="de"')
        block = block.replace('data-sprache="en"', 'data-sprache="en" class="aktiv"')

    # Bestehenden Umschalter ersetzen
    if re.search(r'<div class="sprachwahl">.*?</div>', html, re.S):
        return re.sub(r'<div class="sprachwahl">.*?</div>', block, html, count=1,
                      flags=re.S), True

    # Sonst hinter dem öffnenden Kopfbereich einfügen
    for muster in (r'(<header[^>]*>)', r'(<div class="kopf"[^>]*>)',
                   r'(<body[^>]*>)'):
        if re.search(muster, html):
            return re.sub(muster, lambda m: m.group(1) + "\n  " + block,
                          html, count=1), True
    return html, False


def main():
    if not SPRACHTEXTE.exists():
        print("sprachtexte.json fehlt")
        return 1
    tabelle = json.loads(SPRACHTEXTE.read_text(encoding="utf-8")).get("en", {})
    print(f"Übersetzungstabelle: {len(tabelle)} Einträge\n")

    fehlend = []
    for de_name, en_name in SEITEN:
        de_pfad = DASH / de_name
        en_pfad = DASH / en_name
        if not de_pfad.exists():
            fehlend.append(de_name)
            print(f"  {de_name}: fehlt — übersprungen")
            continue

        de_html = de_pfad.read_text(encoding="utf-8")

        # Deutsche Fassung mit Umschalter versehen
        de_neu, ok_de = setze_umschalter(de_html, de_name, en_name, "de")
        if ok_de:
            de_pfad.write_text(de_neu, encoding="utf-8")

        # Englische Fassung erzeugen
        en_html = uebersetze(de_html, tabelle, "en")
        en_neu, ok_en = setze_umschalter(en_html, de_name, en_name, "en")
        if not ok_en:
            print(f"  {en_name}: Umschalter konnte nicht gesetzt werden")
            continue
        # Der Seitentitel geht mit
        en_neu = en_neu.replace('<html lang="de"', '<html lang="en"')
        en_pfad.write_text(en_neu, encoding="utf-8")

        print(f"  {de_name} ({de_pfad.stat().st_size/1e6:.2f} MB) "
              f"-> {en_name} ({en_pfad.stat().st_size/1e6:.2f} MB)")

    if fehlend:
        print(f"\nHinweis: {len(fehlend)} Seite(n) fehlen noch — erst bauen: "
              f"build_app.py, build_ch.py, build_start.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
