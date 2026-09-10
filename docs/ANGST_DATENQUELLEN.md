# Datenquellen zur Kriminalitätsfurcht in Deutschland

Bestandsaufnahme vom 10. September 2026. Zweck: Prüfen, welche Daten es zur
Furcht vor Kriminalität in Deutschland gibt, was davon beschaffbar ist und wo
sich mehr Differenzierung gewinnen lässt als mit dem European Social Survey
allein.

## Was derzeit in der Auswertung steckt

| Quelle | Inhalt | Umfang | Zugang |
|---|---|---|---|
| European Social Survey, Runden 1–11 | Unsicherheitsgefühl nachts, Viktimisierung, Diskriminierung, Vertrauen | 16.664 Personen mit Bundesland-Angabe (DE) | offen, Daten liegen vor |
| BKA, PKS | registrierte Fälle, Aufklärungsquote | 1987–2025, Länder und Bund | offen, liegt vor |
| BKA, PMK-Fact-Sheet | politisch motivierte Kriminalität nach Phänomenbereich | 2016–2025 | offen, liegt vor (neu) |
| Eurostat crim_off_cat | Ländervergleich, sechs Delikte | 2009–2024 | offen, liegt vor |

**Grenze der bisherigen Furcht-Daten:** Der ESS erhebt Furcht mit wenigen Items
(ein bis zwei Fragen) und die Länderstichproben sind klein (n = 121 bis 3.332).
Für feinere Aussagen — welche Delikte gefürchtet werden, wie sich Furcht
innerhalb Deutschlands regional verteilt, wie sie mit Mediennutzung
zusammenhängt — reicht das nicht.

## Quellen, die mehr Differenzierung erlauben

### 1. SKiD — Sicherheit und Kriminalität in Deutschland (BKA + Länderpolizeien)

Die wichtigste Quelle. Gemeinsame Dunkelfeldbefragung, zweite Welle 2024 mit
**60.837 auswertbaren Interviews**, repräsentativ für die Wohnbevölkerung ab 16
Jahren. Erhebt ausdrücklich: Sicherheitsgefühl und Kriminalitätsfurcht,
Opfererlebnisse nach Deliktgruppen, Anzeigeverhalten, Bewertung der Polizei,
Soziodemografie. Erste Welle 2020, dritte für 2026 geplant.

- Dashboard mit Ergebnissen: <https://skid.bka.de/>
- Projektseite: <https://www.bka.de/SKiD>
- **Mikrodaten:** Scientific Use Files über das Forschungsdatenzentrum
  (<https://www.forschungsdatenzentrum.de/de/scientific-use-files>), Zugang per
  Antrag. Das ist der Weg zu echten Mehrfachauswertungen.
- Das Dashboard selbst lädt seine Zahlen per JavaScript; ein direkter
  Datenabzug ist nicht vorgesehen. Die Ergebniswerte lassen sich aber über die
  Bedienoberfläche ablesen und einzeln dokumentieren.

**Was das bringen würde:** Furcht nach Delikt, nach Region, nach Alter und
Geschlecht, im Zeitvergleich 2020/2024 — und die Verbindung zu
Opfererfahrungen und Anzeigeverhalten. Genau die Differenzierung, die dem ESS
fehlt.

### 2. Deutscher Viktimisierungssurvey (DVS) 2012 und 2017

Vorläufer von SKiD. Als **Kumulation 2012–2017 über GESIS** verfügbar
(ZA6853, <https://search.gesis.org/research_data/ZA6853>). Zugang je nach
Datensatz offen oder per Antrag; die Studie selbst ist dokumentiert, die
Fragebögen sind einsehbar. Für Zeitvergleiche über Dekaden nützlich, weil DVS
und SKiD ähnlich aufgebaut sind.

### 3. SOEP / DIW

Das Sozio-oekonomische Panel enthält seit 1999 Fragen zur sozialen und
personalen Furcht. DIW Wochenbericht 30/2025 wertet das aus (liegt bereits
vor). **Mikrodaten nur über Datenvertrag / Remote-Zugang**
(<https://www.diw.de/de/diw_01.c.815571.de/edition/soep-core_v36r__daten_1984-2019__remote_edition.html>).
Vorteil: echte Längsschnittdaten, damit lassen sich Furchtverläufe von
Personen statt von Jahrgängen vergleichen.

### 4. PaWaKS — Panel zur Wahrnehmung von Kriminalität und Straftäter:innen

Panelstudie des Zentrums für Kriminologische Forschung Sachsen, laut eigener
Darstellung Open Science orientiert, mit Datenhandbuch
(<https://www.zkfs.de/projekt/pawaks/>). Untersucht, wie Kriminalitätswahrnehmung
entsteht — also den Mechanismus hinter der Furcht, nicht nur ihr Niveau.

**Was das bringen würde:** Wahrnehmung, Medienkonsum und Furcht im
Längsschnitt — die theoretisch interessanteste Quelle für Frage 3.

### 5. Weitere, geprüft und als weniger ergiebig eingeordnet

- **Eurostat** erhebt Furcht gar nicht (nur registrierte Kriminalität).
- **Allbus** enthält einzelne Furcht-Items, aber unregelmäßig.
- **Eurobarometer** fragt Furcht gelegentlich, Länderstichproben sind klein.
- **WISIND** (GESIS ZA7465) untersuchte 2013–2017 den Einfluss von
  Sicherheitswahrnehmung, Datenlage begrenzt.

## Beschaffbarkeit — Kurzfassung

| Quelle | Sofort nutzbar | Antrag nötig |
|---|---|---|
| SKiD-Ergebniswerte (Dashboard) | ja, einzeln ablesbar | — |
| SKiD-Mikrodaten (SUF) | — | ja, Forschungsdatenzentrum |
| DVS-Kumulation (GESIS) | teils | teils |
| SOEP | — | ja, Datenvertrag |
| PaWaKS | Datenhandbuch offen | Datenzugang klären |
| ESS | ja | — |

**Empfehlung für die nächste Runde:** Zuerst die SKiD-Ergebniswerte von der
Oberfläche abnehmen und dokumentieren (Furcht nach Delikt und Region,
2020 gegen 2024). Das liefert sofort neue Differenzierung ohne Antrag. Parallel
den SUF-Antrag beim Forschungsdatenzentrum stellen — das ist der Weg zu
Auswertungen, die es so noch nicht gibt.

## Neu aufgenommen: politisch motivierte Kriminalität

Aufgenommen am 10. September 2026, weil sie eine Dimension abbildet, die in der
Gesamtstatistik untergeht: Die registrierte Kriminalität sinkt langfristig, die
politisch motivierte hat sich seit 2016 mehr als verdoppelt.

| Größe | 2016 | 2025 | Veränderung |
|---|---|---|---|
| Alle PMK-Straftaten | 41.549 | 85.837 | **+107 %** |
| davon rechts | 23.555 | 42.544 | +81 % |
| davon links | 9.389 | 13.490 | +44 % |
| Politisch motivierte Gewalttaten | 4.311 | 4.156 | **−3,6 %** |
| davon rechts | 1.698 | 1.598 | −6 % |
| davon links | 1.702 | 1.087 | −36 % |

Quelle: BKA, Bundesweite Fallzahlen zur politisch motivierten Kriminalität 2025
(Fact Sheet), eigene Aufbereitung in `scripts/31_pmk_aufbereiten.py`; die
Summenkontrolle über alle 20 Jahreswerte ist im Skript eingebaut.

**Zur Vorsicht bei der Deutung:** Der Anstieg steckt überwiegend in
Propagandadelikten (35 % aller PMK-Fälle), nicht in Gewalt. Die Zahl der
Gewalttaten ist über die zehn Jahre praktisch unverändert. Wer von „mehr
politischer Gewalt" spricht, muss diesen Unterschied benennen.

**Noch offen:** Differenzierung nach Bundesland (die Länderberichte liegen
vor, etwa für Berlin, Brandenburg und Sachsen-Anhalt) und die Aufschlüsselung
nach Angriffszielen (Amts- und Mandatsträger, Religionsgemeinschaften,
Polizei) — die Fact Sheets enthalten dazu Tabellen.
