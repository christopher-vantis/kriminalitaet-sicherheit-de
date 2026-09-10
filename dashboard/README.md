# Dashboard: Kriminalität und Kriminalitätsfurcht in Deutschland

Mobil-taugliches, offline nutzbares HTML-Dashboard zum Projekt
47 „Kriminalitätsdiskrepanz DE“. Eine Datei, keine Server-Abhängigkeit:
`index.html` im Browser öffnen (Plotly ist eingebettet).

## Aufbau

### Drei Fassungen derselben Seite

| Datei | Größe | Wofür |
|---|---|---|
| `index_static.html` | 0,9 MB | **Für das Handy und zum Verschicken.** Diagramme als eingebettete Bilder, kein JavaScript, kein Internet nötig — funktioniert auch in Messenger-Viewern |
| `index_cdn.html` | 0,2 MB | Kleinste interaktive Fassung; lädt Plotly.js beim Öffnen aus dem Netz (braucht Internet) |
| `index.html` | 5,0 MB | Interaktiv mit eingebettetem Plotly.js — offline nutzbar (Desktop) |

| Datei | Inhalt |
|---|---|
| `build_dashboard.py` | Erzeugt `index.html` und `index_cdn.html` aus den CSV-Daten (Charts + Layout) |
| `build_static.py` | Erzeugt `index_static.html` (Bilder statt JavaScript) |
| `texte.py` | Einordnungen, Interpretationen und Theoriebezüge je Diagramm |
| `texte.py` | Einordnungen, Interpretationen und Theoriebezüge je Diagramm |
| `data/ess_de_personen.csv` | ESS-DE Runden 1–11, Personenebene, bereinigt (28.120 Zeilen) |
| `data/ess_aggregate.csv` | Gewichtete Anteile (Unsicherheitsgefühl) nach Gruppe/Welle |
| `data/wahrnehmung_referenzwerte.csv` | SKiD-/DVS-Werte mit Quellenangabe je Wert (130 Einträge) |

Weitere Datenquellen liegen in `../output/` (PKS-Zeitreihen, Aufklärungsquoten,
Verurteilte, Tatverdächtige, Eurostat-Vergleich).

## Diagramme

**Hellfeld:** Registrierte Fälle 1987–2025 · Deliktshauptgruppen im Vergleich ·
Deutschland im EU-Vergleich
**Wahrnehmung:** Unsicherheitsgefühl 2002–2023 (ESS) · Soziale und personale Furcht
(SOEP/DIW) · Deliktsspezifische Furcht in vier Messpunkten
**Deliktprofil:** Furcht nach Delikt 2020/2024 · Furcht vs. Risikoeinschätzung ·
Furcht vs. tatsächliche Betroffenheit
**Soziale Struktur:** Geschlecht · Alterswandel · soziale Lage · Einstellungen
**Verhalten:** Vermeide- und Schutzverhalten · Sicherheitsgefühl nach Orten
**Justiz:** Der Trichter (Fälle → aufgeklärt → verurteilt) · Aufklärungsquoten ·
Tatverdächtige nach Staatsangehörigkeit und Belastungszahl

Jede Sektion trägt unter dem Diagramm einen Kasten mit **Einordnung**,
**Interpretation** und **Theorie und Evidenz** sowie eine Quellenzeile.

## Neu erzeugen

```bash
# 1) Hellfeld und Aufklärungsquoten (R)
Rscript ../scripts/01_erste_uebersichten.R
Rscript ../scripts/02_deliktsgruppen_aufklaerung_ess.R

# 2) Befragungsdaten
Rscript ../scripts/03_ess_extraktion.R
python3 ../scripts/06_ess_aggregate.py
python3 ../scripts/05_referenzwerte.py

# 3) Justiz und Tatverdächtige (neu 09/2026)
python3 ../scripts/07_destatis_verurteilte.py
python3 ../scripts/08_bka_tv_zeitreihen.py
python3 ../scripts/09_eurostat_vergleich.py

# 4) Dashboard bauen (interaktive Fassungen)
python3 build_dashboard.py

# 5) Statische Fassung für Handy/Messenger
python3 build_static.py
```

Hinweis: `build_dashboard.py` legt die Diagramme als JSON ab und rendert sie erst
beim Scrollen (Lazy-Rendering). 18 gleichzeitig gerenderte Plotly-Diagramme
überfordern mobile Browser; die gestaffelte Darstellung behebt das.

## Technische Hinweise

- **Farben:** Okabe-Ito-Palette (farbenblind-tauglich, hoher Kontrast).
- **Mobil:** Titel/Untertitel/Einordnung als HTML (Plotly-Titel brechen nicht um);
  Achsen mit `automargin`, Kategorielabels mit `ticks="outside"`.
- **Handy:** Wenn Diagramme auf dem Handy leer bleiben, die statische Fassung
  verwenden (`index_static.html`). In-App-Browser von Messenger-Apps führen
  JavaScript oft nicht aus.
- **Skalen:** Anteile in Prozent mit `%`-Suffix in `ticktext` (Plotly ignoriert
  `ticksuffix` bei gesetzten `tickvals`); Trichter auf logarithmischer Skala.
- **Gewichtung:** ESS-Anteile mit `pspwght`; Konfidenzintervalle als
  Normalapproximation ohne Designeffekt (Näherung).
- **Datenstand:** September 2026. Brüche und Einschränkungen stehen im
  Fußbereich des Dashboards ("Bekannte Brüche und Fallstricke").
