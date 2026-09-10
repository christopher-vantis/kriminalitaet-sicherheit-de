# Kriminalität und Sicherheit in Deutschland

Eine Web-App zur Frage, wie registrierte Kriminalität, Strafverfolgung und das
Sicherheitsgefühl der Bevölkerung in Deutschland zusammenhängen — für die
Republik insgesamt und für jedes Bundesland.

**Zur App:** <https://kriminalitaet-sicherheit-de.onrender.com> *(nach dem ersten Deployment)*

## Was die App zeigt

- **Karte** — Deutschlandkarte als Einstieg. Einfärbbar nach Kriminalitätsbelastung,
  Unsicherheitsgefühl, Aufklärungsquote, Migrationsanteil, Ausländeranteil,
  Bevölkerungsdichte, Arbeitslosenquote, BIP je Einwohner und verfügbarem Einkommen.
  Ein Klick öffnet das Profil des Bundeslandes.
- **Kriminalität** — Häufigkeitszahl und Aufklärungsquote je Bundesland, die
  Zeitreihe ab 1987, der Vergleich mit anderen europäischen Ländern.
- **Furcht** — Unsicherheitsgefühl im Zeitverlauf, welche Delikte die Menschen
  fürchten, und wie sich das nach Altersgruppen verschoben hat.
- **Strafverfolgung** — wie viele registrierte Fälle aufgeklärt werden und wie
  viele davon zu einer Verurteilung führen.
- **Daten und Methoden** — Quellen, Fallzahlen, Grenzen der Aussage.

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
dashboard/     Die fertigen Seiten (das ist das Deployment)
  index.html                     Übersicht
  deutschland_app.html           App, Diagramm-Bibliothek eingebettet (offline nutzbar)
  deutschland_app_cdn.html       kleine Fassung für Mobilgeräte
  deutschland_app_static.html    Tabellenfassung ohne JavaScript
  zeitreihen_*.html              Auswertungen über die Zeit
  build_app.py                   erzeugt die App aus den Auswertungsdateien
  fonts/                         eingebettete Schrift
scripts/       Analyse-Skripte (Python und R), numerisch durchnummeriert
output/        Auswertungsergebnisse als CSV
docs/          Datendokumentation und Methodenhinweise
```

## Selbst bauen

```bash
cd dashboard
python3 build_app.py            # erzeugt deutschland_app.html und _cdn.html
python3 build_app_static.py     # erzeugt die Fassung ohne JavaScript
```

Voraussetzungen: Python 3 mit `plotly` und `numpy`; für die Analyse-Skripte
zusätzlich `pandas`, `statsmodels`, `scipy` sowie R mit `lavaan`.

## Deployment

Als statische Website, kein Server nötig. Für Render ist `render.yaml` enthalten:
Repository verbinden, Render liest die Konfiguration, veröffentlicht wird der
Ordner `dashboard`.

## Grenzen

Alle Angaben sind **registrierte** Kriminalität (Hellfeld) — was nicht angezeigt
wird, erscheint nicht in der Statistik. Das Unsicherheitsgefühl stammt aus
Befragungen mit teils kleinen Fallzahlen je Bundesland; Werte mit weniger als
etwa 300 Befragten sind in der App gekennzeichnet. Alle Zusammenhangsaussagen
beruhen auf Querschnittsdaten und belegen keine Ursachen.
