# Kriminalität und Sicherheit in Deutschland

Eine Web-App zur Frage, wie registrierte Kriminalität, Strafverfolgung und das
Sicherheitsgefühl der Bevölkerung in Deutschland zusammenhängen — für die
Republik insgesamt und für jedes Bundesland.

**Zur App:** <https://kriminalitaet-sicherheit-de.onrender.com>

Das Repository enthält **eine** Seite. Sie öffnet direkt mit der Deutschlandkarte;
alles Weitere liegt in Reitern darunter. Es gibt keine Unterseiten.

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

Registrierte Kriminalität und Furcht folgen einander **nicht**. Mecklenburg-Vorpommern
hat die niedrigste Kriminalitätsbelastung und das höchste gemessene Unsicherheitsgefühl;
Bayern hat beides niedrig. Über die Zeit ist der stärkste Einzelbefund das Geschlecht:
Frauen fühlen sich deutlich häufiger unsicher, sind aber nicht häufiger betroffen.

## Datenquellen

| Bereich | Quelle |
|---|---|
| Kriminalität | BKA, Polizeiliche Kriminalstatistik 2025 (Länder-Grundtabelle, T01-Zeitreihe) |
| Strafverfolgung | Statistisches Bundesamt, Statistischer Bericht Strafverfolgung 2024 |
| Furcht | European Social Survey, Runden 1–11 (eigene Auswertung) |
| Bevölkerung, Migration | Statistisches Bundesamt / Statistikportal, Zensus 2022, Mikrozensus |
| Wirtschaft | Arbeitskreis VGR der Länder, 2025 |
| Arbeitsmarkt | Statistik der Bundesagentur für Arbeit, 2025 |
| Ländervergleich | Eurostat crim_off_cat |
| Kartengeometrie | Eurostat/GISCO (NUTS-1), CC BY 4.0 |

Rohdaten und Befragungsdaten liegen nicht in diesem Repository (siehe `.gitignore`).

## Aufbau

```
dashboard/
  index.html      Die App — eine eigenständige Datei. Diagramm-Bibliothek und
                  Schrift sind eingebettet, sie läuft also auch ohne Netz.
  build_app.py    erzeugt index.html aus den Auswertungsdateien
  fonts/          die eingebettete Schrift (IBM Plex Sans)
scripts/          Analyse-Skripte (Python und R), numerisch durchnummeriert
output/           Auswertungsergebnisse als CSV
docs/             Datenquellen und Methodenhinweise
```

## Selbst bauen

```bash
cd dashboard
python3 build_app.py
```

Erzeugt `index.html` (rund 5 MB). Voraussetzungen: Python 3 mit `plotly` und
`numpy`; für die Analyse-Skripte zusätzlich `pandas`, `statsmodels`, `scipy`
sowie R mit `lavaan`.

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
