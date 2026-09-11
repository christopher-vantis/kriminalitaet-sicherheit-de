# Kriminalität und Sicherheit in Deutschland und der Schweiz

Eine Web-App zur Frage, wie registrierte Kriminalität, Strafverfolgung und das
Sicherheitsgefühl der Bevölkerung zusammenhängen — für Deutschland und die
Schweiz, jeweils insgesamt und für jede Region.

**Zur App:** <https://kriminalitaet-sicherheit-de.onrender.com>

Das Repository enthält **drei** Seiten:

| Datei | Inhalt |
|---|---|
| `index.html` | Startseite: Titel, kurze Beschreibung, zwei anklickbare Karten (Deutschland links, Schweiz rechts) |
| `deutschland.html` | Deutschland-Fassung — Karte als Einstieg, alles Weitere in Reitern darunter |
| `schweiz.html` | Schweizer Fassung — Karte der 26 Kantone als Einstieg, gleicher Aufbau |

Die Startseite ist bewusst leicht (rund 190 KB, kein JavaScript, keine
Diagramm-Bibliothek): Sie ist eine Tür, keine Auswertung.

## Was die App zeigt

- **Karte** — Deutschlandkarte als Einstieg, einfärbbar nach Kriminalitätsbelastung,
  Unsicherheitsgefühl, Aufklärungsquote, Migrationsanteil, Ausländeranteil,
  Bevölkerungsdichte, Arbeitslosenquote, BIP je Einwohner und verfügbarem Einkommen.
  Der Klick auf ein Bundesland öffnet sein Profil mit allen Kennzahlen.
- **Kriminalität** — Häufigkeitszahl und Aufklärungsquote der Bundesländer, die
  Zeitreihe ab 1987, der Vergleich mit anderen europäischen Ländern über sechs Delikte.
- **Furcht** — Unsicherheitsgefühl im Zeitverlauf, welche Delikte die Menschen
  fürchten, und wie sich das nach Altersgruppen verschoben hat.
- **Strafverfolgung** — wie viele registrierte Fälle aufgeklärt werden und wie
  viele davon zu einer Verurteilung führen.
- **Daten und Methoden** — Quellen, Fallzahlen, Grenzen der Aussage, Rahmendaten
  Deutschlands zum Vergleich.

## Der inhaltliche Kern

Registrierte Kriminalität und Furcht folgen einander **nicht** — in keinem der
beiden Länder.

*Deutschland:* Mecklenburg-Vorpommern hat die niedrigste Kriminalitätsbelastung
und das höchste gemessene Unsicherheitsgefühl; Bayern hat beides niedrig.

*Schweiz:* Die Zentralschweiz fühlt sich am sichersten, die Nordwestschweiz am
unsichersten — im Tessin ist die Betroffenheit am höchsten, die Furcht aber
unterdurchschnittlich. Zwischen 2011 und 2015 fiel die registrierte
Einbruchshäufigkeit um ein Viertel, während die Furcht vor einem Einbruch von
25,4 auf 33,1 Prozent **stieg**.

In beiden Ländern ist der stärkste Einzelbefund das Geschlecht: Frauen fühlen
sich deutlich häufiger unsicher, ohne häufiger betroffen zu sein. Das Niveau
unterscheidet sich allerdings stark — 2023 fühlen sich in Deutschland 25,0
Prozent unsicher, in der Schweiz 8,9 Prozent, bei der gleichen Frage im gleichen
Erhebungsprogramm.


## Datenquellen

| Bereich | Quelle |
|---|---|
| Kriminalität (CH) | Bundesamt für Statistik, Polizeiliche Kriminalstatistik (STAT-TAB, px-x-1903020100_101), 2009–2025; Wohnbevölkerung (px-x-0102020000_101) |
| Furcht (CH) | European Social Survey Runden 1–11 (eigene Auswertung); Swiss Crime Survey 2022 (ZHAW/Uni St. Gallen, KKPKS); Schweizerische Sicherheitsbefragung 2015 |
| Ländervergleich (CH/DE) | Eurostat crim_off_cat, harmonisierte ICCS-Gliederung |
| Kriminalität (DE) | BKA, Polizeiliche Kriminalstatistik 2025 (Länder-Grundtabelle, T01-Zeitreihe) |
| Strafverfolgung | Statistisches Bundesamt, Statistischer Bericht Strafverfolgung 2024 |
| Furcht (DE) | European Social Survey, Runden 1–11 (eigene Auswertung) |
| Bevölkerung, Migration | Statistisches Bundesamt / Statistikportal, Zensus 2022, Mikrozensus |
| Wirtschaft | Arbeitskreis VGR der Länder, 2025 |
| Arbeitsmarkt | Statistik der Bundesagentur für Arbeit, 2025 |
| Ländervergleich | Eurostat crim_off_cat |
| Kartengeometrie | Eurostat/GISCO (NUTS-1), CC BY 4.0 |

Rohdaten und Befragungsdaten liegen nicht in diesem Repository (siehe `.gitignore`).

## Aufbau

```
dashboard/
  index.html        Startseite (aus build_start.py)
  deutschland.html  Deutschland-Fassung (aus build_app.py)
  schweiz.html      Schweizer Fassung (aus build_ch.py)
  start.html        dieselbe Startseite, unter eigenem Namen
  build_app.py      erzeugt deutschland.html aus den Auswertungsdateien
  build_ch.py       erzeugt schweiz.html (nutzt CSS und Schrift von build_app.py)
  build_start.py    verschiebt die Deutschland-Fassung und baut die Startseite
  fonts/            die eingebettete Schrift (IBM Plex Sans)
scripts/          Analyse-Skripte (Python und R), numerisch durchnummeriert
                  (40–46 = Schweizer Datenpipeline)
output/           Auswertungsergebnisse als CSV
docs/             Datenquellen und Methodenhinweise
```

## Selbst bauen

Die Reihenfolge ist wichtig, weil `build_start.py` die Deutschland-Fassung
verschiebt:

```bash
cd dashboard
python3 build_app.py     # -> deutschland.html
python3 build_ch.py      # -> schweiz.html
python3 build_start.py   # -> index.html (Startseite)

# Schweizer Daten neu erheben (vorher, aus dem Projektverzeichnis)
python3 scripts/40_ch_pks_bfs.py
python3 scripts/41_ch_bevoelkerung_bfs.py
python3 scripts/42_ch_ess_extraktion.py
python3 scripts/43_ch_geo_svg.py
python3 scripts/44_ch_kennzahlen.py
python3 scripts/45_ch_referenzwerte.py
python3 scripts/46_ch_eurostat.py
```

Voraussetzungen: Python 3 mit `plotly` und `numpy`; für die Analyse-Skripte
zusätzlich `pandas`, `statsmodels`, `scipy` sowie R mit `lavaan`. `build_ch.py`
liest `build_app.py` als Modul, damit beide Länderfassungen dasselbe CSS und
dieselbe Schrift verwenden.

## Deployment

Statische Website, kein Server nötig. `render.yaml` ist enthalten: Repository bei
Render verbinden, als **Static Site** anlegen (nicht Web Service), Publish
Directory `dashboard`, Build Command leer. Render veröffentlicht bei jedem Push
auf `main` automatisch neu.

## Grenzen

Alle Angaben sind **registrierte** Kriminalität (Hellfeld) — was nicht angezeigt
wird, erscheint nicht in der Statistik. Das Unsicherheitsgefühl stammt aus
Befragungen mit teils kleinen Fallzahlen je Bundesland; Werte unter etwa 300
Befragten sind in der App gekennzeichnet. Die Karte färbt nach Rangstufen, nicht
nach gleichen Wertabständen. Alle Zusammenhangsaussagen beruhen auf
Querschnittsdaten und belegen keine Ursachen.
