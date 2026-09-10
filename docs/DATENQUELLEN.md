# Datenquellen — Projekt „Kriminalitätsdiskrepanz DE"

Ziel: Diskrepanz zwischen registrierter Kriminalität (Hellfeld, PKS) und
subjektiver Kriminalitätswahrnehmung (Kriminalitätsfurcht, Risikoeinschätzung),
Zeitraum 2002–2025.

Diese Datei dokumentiert pro Quelle: Gegenstand, Erheber, Grundgesamtheit,
beschaffte Dateien, Lizenz/Zitation und bekannte Zeitreihenbrüche. Die
vollständige Dateiliste mit SHA-256-Hashes steht in `../data/manifest.csv`.

Stand: wird nach Abschluss der Beschaffung finalisiert.

---

## A) Polizeiliche Kriminalstatistik (PKS) — Bundeskriminalamt

- Was: Vollerhebung der polizeilich registrierten Straftaten („Hellfeld"),
  Ausgangsstatistik (Tatzeitpunkt-Prinzip), erfasst durch die Polizeien der
  16 Länder, zusammengeführt vom BKA.
- Grundgesamtheit: alle der Polizei bekannt gewordenen und registrierten
  Straftaten inkl. Versuche; Tatverdächtige, Opfer und Belastungszahlen.
- Erheber: BKA auf Basis der Landeskriminalämter (Ausgangsstatistik).
- Beschafft (Ziel 2002–2025):
  - Zeitreihen Berichtsjahr 2025 (T01 „Fälle ab 1987", Tatverdächtige, Opfer,
    Belastungszahlen) — decken den Zielzeitraum in einer Datei ab.
  - Kontroll-Zeitreihen der Berichtsjahre 2020 und 2015 (Revisionen sichtbar).
  - Bundes-Falltabellen und Bundes-Opfertabellen 2015–2025.
  - Länder-Falltabellen 2015–2025.
  - Interpretationshilfen 2015–2025 (Straftatenkatalog aktuell + Historie,
    Summenschlüssel, Tabellenbeschreibung, Hinweise zu den Zeitreihen,
    Wichtige Hinweise zur Interpretation, Änderungsnachweis, Richtlinien).
  - Jahresberichte/Jahrbücher 2002–2014 (PDF, Beleg-/Kontrollquelle).
  - PKS-Ausland (ab Berichtsjahr 2024), sofern vorhanden.
- Lizenz/Zitation: Datenlizenz Deutschland – Namensnennung 2.0
  (dl-de/by-2-0, https://www.govdata.de/dl-de/by-2-0). Nutzungshinweis BKA:
  Quellenangabe „PKS Bundeskriminalamt", Berichtsjahr und Version.
- Alternative Bezugsquelle (nicht doppelt geladen): Auf GovData
  (https://www.govdata.de) sind einzelne PKS-Tabellen auch als CSV-Datensätze
  veröffentlicht (Bereitsteller Bundesministerium des Innern und Heimat,
  veröffentlichende Stelle Bundeskriminalamt, Lizenz dl-de/by-2-0). Inhaltlich
  identisch mit den hier bezogenen BKA-Downloads, daher nur als Referenz notiert.
- Bekannte Brüche: siehe docs/GEBIETSSTAND.md und
  data/raw/pks/zeitreihenbrueche.csv (A2-Bruchdokumentation). Wichtige
  strukturelle Brüche: Erfassungsrichtlinienwechsel, Umstellung des
  Straftatenkatalogs, Zensus-Basis der Belastungszahlen, Sonderfälle
  (z. B. ausländerrechtliche Verstöße 2016 ff., Aufnahme von Cybercrime-Delikten).

## B) SKiD — Sicherheit und Kriminalität in Deutschland (BKA)

- Was: bundesweite Dunkelfeld-/Opferbefragung (Viktimisierungssurvey),
  Wellen 2020 und 2024 (2026 in Vorbereitung).
- Grundgesamtheit: deutschsprachige Wohnbevölkerung ab 16 Jahren in
  Privathaushalten; Zufallsstichprobe aus Einwohnermelderegistern;
  SKiD 2020 ≈ 47.000 Befragte (bundesweit, mit Länderaufstockungen).
- Erheber: BKA (Kriminalistisches Institut) in Kooperation mit den Polizeien
  der Länder; Erhebungsinstitut infas (2020/2024); Auftraggeber BMI.
- Beschafft: Ergebnisbericht SKiD 2020, Ergebnisbericht SKiD 2024,
  Factsheet Polizei (SKiD 2024). Methodenberichte/Fragebögen/Codebücher:
  sofern auf der SKiD-Seite frei verlinkt, sonst in MANUELL_ZU_BESCHAFFEN.md.
  Dashboard (https://skid.bka.de/): rein interaktives JavaScript-Dashboard,
  kein CSV/JSON-Export (siehe MANUELL_ZU_BESCHAFFEN.md).
- GESIS-SUF: bei der Recherche kein Scientific-Use-File zu SKiD gefunden
  (siehe MANUELL_ZU_BESCHAFFEN.md).
- Lizenz/Zitation: BKA-Publikation; Quellenangabe „Bundeskriminalamt", Jahr.

## C) DVS — Deutscher Viktimisierungssurvey (Vorgängerstudie)

- Was: bundesweite Opferbefragungen 2012 und 2017; Kumulation 2012–2017
  als GESIS-SUF ZA6853.
- Grundgesamtheit: deutschsprachige Wohnbevölkerung ab 16 Jahren;
  Kumulation 66.695 Fälle, 2.018 Variablen (SPSS/Stata).
- Erheber: BKA (2012) bzw. BKA mit EU-Förderung (2017).
- Beschafft: Ergebnisberichte DVS 2012 und DVS 2017 (BKA-PDF), Fragebogen
  und Methodenbericht DVS 2017, Änderungsnachweis, englische Kurzfassung.
- Mikrodaten: NICHT heruntergeladen (Nutzungsvertrag GESIS) — Zugang in
  MANUELL_ZU_BESCHAFFEN.md. DOI 10.4232/1.13672.
- Lizenz/Zitation: Berichte BKA (dl-de/by-2-0); Mikrodaten GESIS SUF
  (Nutzungsvertrag).

## D) Destatis — Bevölkerungsfortschreibung (Normierung)

- Was: amtliche Einwohnerzahlen (Bevölkerungsstand), Jahresendstände,
  Bund und Länder; GENESIS-Online Tabelle 12411.
- Erheber: Statistisches Bundesamt (Destatis) / Statistische Ämter der Länder.
- Beschafft: manuell über GENESIS-Online (Registrierung für API nötig) —
  exakte Filter in MANUELL_ZU_BESCHAFFEN.md.
- Zensus-Basis (Sprungjahre!):
  - bis 2010: Fortschreibung auf Basis Volkszählung 1987 (alte Länder) bzw.
    Einwohnerregister DDR 03.10.1990 (neue Länder).
  - ab 2011: Basis Zensus 2011 (Revision 2011–2013; Rückrechnung bis 31.12.2010).
  - ab 2022: Basis Zensus 2022 (Rückrechnung 2012–2021 auf Zensus-2022-Basis;
    GENESIS führt Zensus-2011-Basis bis Berichtsjahr 2021, Zensus-2022-Basis
    ab 2022).
  - Sprungjahre: 2011 und 2022. Für bruchfreie HZ-Berechnung sind die
    Zensus-Basen je Jahr explizit zu dokumentieren.
- Lizenz/Zitation: dl-de/by-2-0; „Statistisches Bundesamt (Destatis),
  GENESIS-Online".

## E) Eurostat — Kriminalitätsstatistik (internationaler Zweig)

- Was: polizeilich registrierte Straftaten nach Deliktkategorie, EU/EFTA.
- Tabellen: `crim_off_cat` (Recorded offences by offence category – police
  data, 2008–2024) und historisch `crim_gen` (1993–2007). Tabellen-ID
  verifiziert über die ESMS-Metadaten „Crime and criminal justice (crim)".
- Beschafft: crim_off_cat.tsv und crim_gen.tsv (SDMX-API, alle Länder/Jahre).
- Hinweis: internationale Vergleichbarkeit eingeschränkt (unterschiedliche
  Rechtsdefinitionen, Erfassungspraktiken, Anzeigequoten) — nur als
  Kontext, nicht als 1:1-Vergleich mit PKS.
- Lizenz/Zitation: Eurostat, freie Nutzung mit Quellenangabe (CC BY 4.0).

## F) ESS — European Social Survey (Wahrnehmungs-/Furcht-Indikatoren)

- Was: ländervergleichende Bevölkerungsumfrage (biennal, seit 2001).
- Relevante Variablen (Core-Modul): `aesfdrk` (Gefühl der Sicherheit beim
  Alleingehen nach Einbruch der Dunkelheit), `crmvct` (Viktimisierung
  Einbruch/Überfall im Haushalt, letzte 5 Jahre). Enthalten in R1 (2002/03)
  bis R11 (2023/24); genaue Rundenverfügbarkeit im Cumulative Data Wizard.
- Moduswechsel (dokumentierter Bruch!): R1–R9 face-to-face; R10 (2020–22)
  Mixed-Mode wegen Corona (8–9 Länder self-completion); R11 (2023/24) wieder
  face-to-face (inkl. Video-Interviewing; Ausnahme Tschechien self-completion);
  R12 (2025/26) Mixed-Mode (halbe Stichprobe self-completion, halbe face-to-face);
  R13 (2027/28) vollständig self-completion geplant. Der echte Moduswechsel
  liegt also bei R12/R13, nicht bei R11.
- Beschafft: Mikrodaten manuell (Registrierung, not-for-profit) —
  Anleitung in MANUELL_ZU_BESCHAFFEN.md. Codebücher/Fragebögen frei auf der
  ESS-Seite (Source Questionnaires); URL-Muster der frei verfügbaren
  Fragebögen (PDF, Azure-Blob):
  https://stessrelpubprodwe.blob.core.windows.net/data/round{N}/fieldwork/source/ESS{N}%20Source%20Questionnaires.pdf
  (Beispiel R11: .../round11/fieldwork/source/ESS11%20Source%20Questionnaires.pdf).
- Lizenz/Zitation: ESS ERIC / Sikt; Daten frei für nicht-kommerzielle Zwecke,
  Registrierung erforderlich; Zitation „European Social Survey, Round N".

## G) Destatis — Strafverfolgungsstatistik (Verurteilungen) — NEU 09/2026

- Was: rechtskräftig Abgeurteilte und Verurteilte, gegliedert nach Art der
  Straftat (Tabelle 24311-05 des Statistischen Berichts „Strafverfolgung").
  Schließt die Kette unterhalb der PKS: registrierte Fälle → aufgeklärt →
  verurteilt.
- Beschafft: Statistische Berichte 2022, 2023, 2024 (xlsx, je 25–35 MB) →
  `data/raw/destatis/`. Achtung: Die Berichte enthalten NUR das jeweilige
  Berichtsjahr; die lange Zeitreihe (1976–2024) liegt in GENESIS-Tabelle
  24311-0001, deren Web-App rein JavaScript-basiert ist und deren
  REST-API seit 2025 eine Registrierung verlangt.
- Struktur: Blatt 24311-05, je Rechtsschlüssel drei Zeilen (Geschlecht M/F/I),
  Bezeichnung nur in der ersten Zeile (carry-forward nötig). Spalte E =
  Abgeurteilte, Spalte J = Verurteilte insgesamt.
- Auswertung: `scripts/07_destatis_verurteilte.py` → `output/destatis_verurteilte.csv`
- Wichtig: Verurteilte sind Personen (nicht Fälle), gezählt nach dem schwersten
  Delikt des Verfahrens, mit Zeitverzug zum Tatjahr. Kein 1:1-Vergleich mit PKS-Fällen.
- Lizenz: dl-de/by-2-0.

## H) BKA — PKS-Zeitreihen Tatverdächtige und Belastungszahlen — NEU 09/2026

- Was: Zeitreihen T20 (Tatverdächtige insgesamt), T40 (deutsche TV),
  T50 (nichtdeutsche TV), jeweils ab 1987, sowie Tatverdächtigenbelastungszahlen
  (TVBZ) ab 2009 für insgesamt / deutsche / nichtdeutsche Wohnbevölkerung.
- Beschafft: 6 xlsx aus der BKA-Seite „PKS 2025 – Zeitreihen" →
  `data/raw/pks/zeitreihen/2025/`.
- Auswertung: `scripts/08_bka_tv_zeitreihen.py` → `output/pks_tatverdaechtige.csv`
- Wichtige Einschränkungen (aus den BKA-Hinweisen): ab 2009 „echte"
  Tatverdächtigenzählung, nicht mit Vorjahren vergleichbar; TVBZ = ansässige
  Tatverdächtige je 100.000 Einwohner der jeweiligen Gruppe (Nenner:
  Wohnbevölkerung, ohne Kinder unter 8 Jahren; Touristen/Durchreisende fehlen
  im Nenner); Bevölkerungsbasis 2013–2023 Zensus 2011, ab 2024 Zensus 2022.
- Lizenz: dl-de/by-2-0.

## I) DIW/SOEP — soziale und personale Kriminalitätsfurcht — NEU 09/2026

- Was: DIW Weekly Report 30/2025 (Bindler/Walther), Auswertung des SOEP v40 und
  des Gleichwertigkeitsberichts 2024 zur Kriminalitätsfurcht.
- Beschafft: PDF → `data/raw/soep_diw/`; Text via pdftotext.
- Kernbefunde (im Text belegt): soziale Furcht (Sorge über die
  Kriminalitätsentwicklung) 2000 ≈ 54 %, 2013 ≈ 31 %, 2023 38 %; Korrelation
  mit den Kriminalitätsraten 2000–2013 r = 0,88, 2014–2017 r = −0,71,
  2018–2023 r = 0,67. Personale Furcht 2023 im Mittel 0,72 auf einer 0–1-Skala.
- WICHTIG: Die Jahreswerte der Abbildungen sind im PDF nicht beschriftet und
  damit nicht ablesbar; ein Abbildungs-Datenanhang ist nicht frei verfügbar.
  Eine eigene Zeitreihe würde SOEP-Mikrodaten erfordern (Datenvertrag).
- Lizenz: DIW Berlin; wissenschaftliche Nutzung mit Quellenangabe.
