# Manuell zu beschaffende Daten

Projekt: Kriminalitätsdiskrepanz DE (registrierte Kriminalität vs. subjektive
Kriminalitätswahrnehmung, 2002–2025).

Diese Datei listet alles, was NICHT automatisiert beschafft werden konnte oder
darf (Login, Registrierung, Nutzungsvertrag, JavaScript/Captcha), mit URL,
Grund und Schritt-für-Schritt-Anleitung.

Stand: wird im Verlauf der Beschaffung fortgeschrieben.

---

## 1. ESS — European Social Survey (Mikrodaten)

- URL: https://www.europeansocialsurvey.org/ (Data Portal + Cumulative Data Wizard)
- Grund: Download erfordert Registrierung (einfach, kostenlos, not-for-profit).
  Automatisierter Login ist nicht zulässig.
- Was exportieren: Variablen `aesfdrk` (Gefühl der Sicherheit beim Alleingehen
  nach Einbruch der Dunkelheit) und `crmvct` (Viktimisierung Einbruch/Überfall
  in Haushalt in letzten 5 Jahren). Beides Core-Variablen, in den Runden R1 (2002/03)
  bis R11 (2023/24) enthalten; genaue Verfügbarkeit pro Runde im Cumulative Data
  Wizard prüfen.
- Länder: Deutschland (DE); für Kontext optional alle Länder.
- Runden: R1 bis R11 (R12 = 2025/26, Mixed-Mode, ggf. noch nicht vollständig).
- Moduswechsel beachten: R1–R9 face-to-face; R10 (2020–22) Mixed-Mode wegen
  Corona (8–9 Länder self-completion); R11 (2023/24) wieder face-to-face
  (inkl. Video-Interviewing, Ausnahme Tschechien self-completion); R12 (2025/26)
  Mixed-Mode (halbe Stichprobe self-completion); R13 (2027/28) vollständig
  self-completion geplant. Der echte Moduswechsel liegt bei R12/R13. Dieser
  Wechsel ist ein dokumentierter Bruch für Längsschnittvergleiche.
- Anleitung:
  1. Auf europeansocialsurvey.org registrieren (Email).
  2. "Data Portal" öffnen, "Cumulative Data Wizard" wählen.
  3. Variablen aesfdrk, crmvct auswählen; Länder DE; Runden 1–11.
  4. Format CSV oder DTA/SAV; Download + Codebook (wird mitgeliefert).

## 2. GESIS — DVS-Mikrodaten (ZA6853)

- URL: https://search.gesis.org/research_data/ZA6853 (DOI 10.4232/1.13672)
- Studie: Deutscher Viktimisierungssurvey — Kumulation 2012–2017, Version 1.0.0,
  66.695 Fälle, 2.018 Variablen, SPSS/Stata.
- Grund: Mikrodaten (Scientific Use File) erfordern einen Nutzungsvertrag mit GESIS.
  Automatisierter Zugriff auf die GESIS-Suche ist technisch blockiert (Cloudflare)
  und die Daten selbst sind vertragsgebunden.
- Frei verfügbare Dokumente (bereits anderweitig bezogen bzw. verlinkt):
  ZA6853_fb_2012.pdf (Fragebogen 2012), ZA6853_fb_2017.pdf (Fragebogen 2017),
  ZA6853_mb.pdf (Methodenbericht). Diese liegen auch auf der BKA-Seite
  (Dunkelfeldforschung / Viktimisierungssurveys).
- Anleitung:
  1. Auf search.gesis.org die Studie ZA6853 öffnen.
  2. "Datenbestellung / Data access" → Nutzungsvertrag (GESIS SUF) beantragen.
  3. Nach Freischaltung die Kumulation 2012–2017 (SPSS/Stata) herunterladen.
  Hinweis: für rein wissenschaftliche Zwecke; Weitergabe nicht gestattet.

## 3. GESIS — SKiD-Scientific-Use-File (prüfen)

- Grund: B-Auftrag verlangt Prüfung, ob SKiD 2020/2024 als SUF bei GESIS vorliegt.
- Stand: Bei der Web-Recherche wurde KEIN GESIS-SUF zu SKiD gefunden; die
  Erhebungsdaten liegen beim BKA (Kooperationsstudie Bund/Länder). Vor einem
  Download auf search.gesis.org nach "SKiD" suchen; falls SUF vorhanden,
  Studiennummer + Zugangsbedingungen hier ergänzen. (Automatisiert nicht prüfbar,
  da search.gesis.org Cloudflare-geschützt ist.)

## 4. Destatis GENESIS-Online — Tabelle 12411 (Bevölkerungsstand)

- URL: https://genesis.destatis.de/datenbank/online
  Tabelle 12411-0010 "Bevölkerung: Bundesländer, Stichtag" (Fortschreibung des
  Bevölkerungsstandes). Weitere Gliederungen unter 12411-* (z. B. Deutschland,
  Stichtag, Altersjahre: 12411-0005).
- Grund: Der Webservice (RESTful API) erfordert seit 14.05.2025 eine einmalige
  kostenlose Registrierung; die SOAP/GET-Schnittstelle wurde 27.11.2025 abgeschaltet.
  Die Web-App erlaubt Gast-Export (CSV/XLSX), ist aber JavaScript-basiert und
  nicht robust automatisierbar.
- Was exportieren: Jahresendstände (31.12.) der Bevölkerung 2001–2025,
  Bundesgebiet gesamt UND nach Bundesländern.
- Zensus-Basis dokumentieren (wichtig für die Normierung):
  - bis 2010: Fortschreibung auf Basis Volkszählung 1987 (alte Länder) bzw.
    Einwohnerregister DDR 03.10.1990 (neue Länder).
  - ab 2011: Basis Zensus 2011 (Revision der Jahre 2011–2013).
  - ab 2022: Basis Zensus 2022 (Rückrechnung 2012–2021 auf Zensus-2022-Basis).
  - Sprungjahre in der Reihe: 2011 und 2022.
- Anleitung:
  1. https://genesis.destatis.de/datenbank/online öffnen.
  2. Suchbegriff "12411" oder Code "12411-0010" eingeben.
  3. Filter: Stichtag 31.12., Jahre 2001–2025, Regionen: Deutschland + alle Bundesländer.
  4. Export als CSV (oder XLSX). Lizenz: Datenlizenz Deutschland – Namensnennung 2.0
     (dl-de/by-2-0), Quellenangabe "Statistisches Bundesamt (Destatis), GENESIS-Online".

## 5. SKiD-Dashboard (BKA)

- URL: https://skid.bka.de/
- Grund: Prüfen, ob ein CSV/JSON-Export existiert. Falls rein interaktiv:
  Kennzahlen manuell extrahieren (Prävalenzraten nach Delikt, Anzeigequote,
  Kriminalitätsfurcht-Indikatoren nach Geschlecht/Alter/Migrationshintergrund,
  Wellen 2020 und 2024).
- Stand: geprüft — skid.bka.de ist ein rein interaktives JavaScript-Dashboard
  (Auswertungen nach Geschlecht/Alter/Migrationshintergrund, Wellen 2020 und 2024);
  ein CSV/JSON-Export ist NICHT vorhanden. Manuell zu extrahierende Kennzahlen:
  Prävalenzraten (12-Monats-Prävalenz je Delikt), Anzeigequote, Kriminalitätsfurcht-/
  Sicherheitsgefühl-Indikatoren, jeweils nach Geschlecht, Altersgruppe und
  Migrationshintergrund, für beide Wellen.

---

## 6. NACHBESCHAFFT 09/2026 (nicht mehr offen)

Automatisiert beschafft und im Manifest dokumentiert:

- **Destatis Strafverfolgungsstatistik** (Verurteilungen): Statistische Berichte
  2022, 2023, 2024 (xlsx) → `data/raw/destatis/`. Damit ist das Trichter-Ende
  (Fälle → aufgeklärt → verurteilt) berechenbar.
  OFFEN bleibt nur die lange Zeitreihe 1976–2024 (GENESIS 24311-0001): Die
  Web-App ist rein JavaScript-basiert, die REST-API verlangt seit 2025 eine
  kostenlose Registrierung. Wer die Zeitreihe braucht: GENESIS-Konto anlegen
  und 24311-0001 als CSV exportieren.
- **BKA PKS-Zeitreihen Tatverdächtige/Belastungszahlen** (T20/T40/T50, TVBZ
  ab 2009) → `data/raw/pks/zeitreihen/2025/`. Damit ist die
  Staatsangehörigkeits-Dimension im Hellfeld auswertbar.
- **Eurostat crim_off_cat**: lag bereits vor (`data/raw/eurostat/`); die
  ICCS-Deliktcodes wurden über die Eurostat-API verifiziert und in
  `scripts/09_eurostat_vergleich.py` dokumentiert.
- **SOEP/DIW**: DIW Weekly Report 30/2025 (PDF) → `data/raw/soep_diw/`.
  Die Jahreswerte der Abbildungen sind im Bericht nicht beschriftet; für eine
  eigene Zeitreihe der sozialen Kriminalitätsfurcht ist weiterhin ein
  SOEP-Datenvertrag nötig (DIW/SOEP-SUF).

## 7. ESS-Mikrodaten — erledigt

Die für dieses Projekt relevanten ESS-Rohdaten (Runden 1–11, Deutschland)
liegen im Nachbarprojekt `43_human_values_project/data/raw/ess/` und wurden
von dort eingebunden (`scripts/03_ess_extraktion.R`). Kein separater Download
nötig.
