# Kriminalität und Sicherheit in Deutschland — Bundesland-App

Interaktive Webapp zum Projekt 47: eine Deutschlandkarte als Einstieg, darunter
die republikweiten Auswertungen — und für jedes Bundesland dasselbe im Detail.

## Dateien

| Datei | Größe | Zweck |
|---|---|---|
| `deutschland_app.html` | ~5,0 MB | Vollständige Fassung, Plotly eingebettet, **offline** nutzbar |
| `deutschland_app_cdn.html` | ~0,17 MB | Gleiche App, Plotly per CDN — kleine Datei für die Übertragung aufs Handy |
| `build_app.py` | — | Erzeugt beide Dateien aus den Daten in `../output/` und `data/` |
| `deutschland_app_static.html` | ~1 MB | Nur-Bild-Fassung für Viewer ohne JavaScript (`build_app_static.py`) |

Öffnen: Datei im Browser laden — kein Server, kein Internet nötig (außer CDN-Fassung).
Deep-Links funktionieren: `deutschland_app.html#land=DE1` öffnet direkt
Baden-Württemberg, `#furcht` öffnet den Themenreiter Furcht.

## Aufbau

**Ansicht „Karte"** — Deutschlandkarte (SVG, aus GISCO-Geometrie projiziert).
Die Einfärbung lässt sich umschalten zwischen Kriminalitätsbelastung,
Unsicherheitsgefühl, Aufklärungsquote, BIP je Einwohner, Ausländeranteil und
Bevölkerungsdichte. Auf ein Bundesland tippen → Länderprofil.

**Themenreiter** — Kriminalität, Furcht, **Zusammenhänge**, Wirtschaft,
Strafverfolgung, Daten & Methoden. Der Reiter „Zusammenhänge" enthält die
Korrelations-, Modell-, Moderations- und Mediationsauswertungen
(Dokumentation: ).

**Länderprofil** — Kennzahlen, Kriminalitätstabelle (Fälle, Häufigkeitszahl,
Aufklärungsquote je Delikt), Wirtschaft und Demografie, automatisch erzeugte
Einordnung (Vergleich zum Länderdurchschnitt, ausdrücklich benannte Unsicherheiten).

## Daten

| Inhalt | Quelle | Datei |
|---|---|---|
| Kriminalität je Land 2025 (Fälle, HZ, AQ) | BKA, PKS Länder-Grundtabelle | `../output/pks_laender_2025.csv` |
| Bevölkerung, Fläche, Dichte | Statistikportal der Statistischen Ämter | `../output/laender_indikatoren.csv` |
| Nationalität | Destatis, Basis Zensus 2022 | dito |
| BIP, verfügbares Einkommen je Einwohner | VGR der Länder (Ausgabe 2026) | dito |
| Unsicherheitsgefühl je Land | ESS Runden 5–11, eigene Berechnung | `data/ess_bundeslaender.csv` |
| Kartengeometrie | Eurostat/GISCO NUTS-RG 2021 (CC BY 4.0) | `../output/bundeslaender_svg.json` |
| Zeitreihen, Trichter, EU-Vergleich | PKS T01, Destatis Strafverfolgung, Eurostat | `../output/*.csv` |

Erzeugende Skripte: `../scripts/12_pks_laender.py`, `13_laender_indikatoren.py`,
`14_geo_svg.py`, `15_ess_bundeslaender.py`, `16_manifest_laender.py`.

## Methodische Hinweise (auch in der App unter „Daten & Methoden")

- Registrierte Fälle sind polizeilich bekannt gewordene Vorgänge — kein Nachweis
  einer Straftat und keine Verurteilung.
- Die Häufigkeitszahl bezieht Fälle auf die **Wohnbevölkerung**. In Stadtstaaten
  erhöhen Pendler, Gäste und Mehrfacherfassungen den Wert, ohne dass die
  Wohnbevölkerung diese Fälle verursacht.
- Die Länderwerte zur Furcht beruhen auf gepoolten ESS-Wellen (n = 121 bis 3.332).
  Zu kleine Fallzahlen sind grau dargestellt und als nicht belastbar markiert;
  die Fehlerbalken sind Näherungen ohne Designeffekt.
- Die Furcht-Zeitreihen stammen aus unabhängigen Stichproben, nicht aus einem
  Panel — kausale Aussagen sind damit nicht möglich.
- Verurteilungen sind Personen (nicht Fälle), gezählt nach dem schwersten Delikt
  des Verfahrens, mit Zeitverzug zum Tatjahr.

## Farbwelt

Petrol (#0f766e) als Leitfarbe mit warmem Terrakotta (#c2410c) als Akzent —
bewusst kein Blau. Kartenstufen nach Rang (Quantile), nicht linear, damit die
Stadtstaaten die Skala nicht dominieren.

## Was der erste Versuch noch nicht hat

- Arbeitslosenquote je Bundesland (die amtliche Tabelle war nicht automatisiert
  beschaffbar; die Zuordnung aus Sekundärquellen war nicht eindeutig genug).
- Kreisebene (die PKS liefert Kreisdaten — würde die Stadt-Land-Frage schärfen).
- Zeitliche Entwicklung je Bundesland (die Länder-Zeitreihen liegen vor, sind
  aber noch nicht ausgewertet).
- Kein Deployment: die App ist eine Datei, kein Server.
