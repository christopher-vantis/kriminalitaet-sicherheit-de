# Zusammenhänge: Furcht und ihre Korrelate (ESS Deutschland)

Ergebnisse der Analyse vom September 2026. Alle Zahlen aus `scripts/18`–`20`,
Rohdaten in `dashboard/data/ess_de_personen.csv` (28.120 Personen, Runden 1–11;
Deutschland fehlt in Runde 10). Gewichtung: `pspwght`, wo nicht anders vermerkt.

## Vorbemerkung zur Lesart

Das sind **Querschnittsdaten**. Wir sehen, was gleichzeitig mit Furcht auftritt —
nicht, was sie verursacht. Wo unten von „Effekt" die Rede ist, ist ein
Regressionskoeffizient oder ein marginaler Effekt gemeint, kein kausaler Effekt.
Die Modelle erreichen eine AUC von 0,74 bis 0,79 und ein Pseudo-R² (McFadden) von
0,12 bis 0,18 — **der größere Teil der Varianz bleibt unerklärt**.

## 1. Was bivariat zusammenhängt (ohne Kontrolle)

Rangkorrelation mit dem Unsicherheitsgefühl, absteigend; alle genannten Werte
überstehen die FDR-Korrektur nach Benjamini-Hochberg (q < 0,05):

| Merkmal | Korrelation | stabil über die Wellen? |
|---|---|---|
| Frau (vs. Mann) | **+0,276** | ja (+0,24 bis +0,30) |
| Sozialvertrauen | −0,209 | ja (−0,16 bis −0,26) |
| Zuwanderung: gut für das Land | −0,189 | ja |
| Bildung (ISCED) | −0,167 | ja, wird stärker (−0,12 → −0,18) |
| Haushaltseinkommen | −0,164 | ja |
| Gesundheit (schlechter) | +0,162 | ja |
| Vertrauen in die Justiz | −0,155 | ja |
| Demokratiezufriedenheit | −0,153 | ja |
| Wohnort (Land) | −0,093 | ja |
| Viktimisierung | +0,060 | ja, aber schwach |
| Alter | +0,057 | **wechselt das Vorzeichen** (+0,13 → −0,02) |
| Diskriminierungserfahrung | +0,050 | ja |
| Migrationshintergrund | +0,023 | **wechselt das Vorzeichen** |

**Zwei Paradoxien stechen hervor:**

1. **Frauen fürchten sich deutlich mehr, sind aber nicht häufiger betroffen.**
   Geschlecht korreliert mit Furcht zu +0,276 — mit Viktimisierung nur zu −0,008
   (nicht signifikant). Das ist das in der Literatur beschriebene
   Furcht-Viktimisierungs-Paradox.
2. **Furcht und Betroffenheit hängen kaum zusammen.** Viktimisierung korreliert
   nur zu +0,060 mit Furcht — obwohl es die naheliegendste Erklärung wäre.

## 2. Was der Kontrolle standhält

Verschachtelte logistische Regressionen, Standardfehler geclustert nach
Bundesland, Fallzahl 15.440 im Vollmodell. Mittlere marginale Effekte (AME) in
Prozentpunkten, Modell M3:

| Merkmal | AME | 95-%-Intervall |
|---|---|---|
| Frau (vs. Mann) | **+20,7 PP** | +19,5 bis +21,9 |
| Viktimisierung | +6,0 PP | +4,0 bis +8,0 |
| Sozialvertrauen (je SD) | −4,8 PP | −5,5 bis −4,2 |
| Wohnort (je Stufe Richtung Land) | −3,7 PP | −4,3 bis −3,1 |
| Zuwanderungseinstellung (je SD) | −3,6 PP | −4,3 bis −2,9 |
| Bildung (je SD) | −3,1 PP | −3,8 bis −2,5 |
| Gesundheit (je SD, schlechter) | +2,7 PP | +2,1 bis +3,4 |
| Migrationshintergrund | +2,6 PP | +1,0 bis +4,1 |
| Diskriminierungserfahrung | +2,2 PP | −0,5 bis +4,8 (**n.s.**) |
| Vertrauen in die Justiz (je SD) | −1,8 PP | −2,6 bis −1,0 |

**Zwei Verschiebungen gegenüber dem bivariaten Bild:**

- **Diskriminierungserfahrung verliert die Signifikanz.** Der bivariate
  Zusammenhang (+0,050) kam über andere Merkmale zustande.
- **Migrationshintergrund gewinnt sie.** Bivariat fast null (+0,023), unter
  Kontrolle von Bildung, Einkommen und Wohnort +2,6 PP. Der Effekt war verdeckt
  (Suppression).

Die Wellen-Kontrolle (M4) verändert die Koeffizienten kaum; der Zeitgeist erklärt
den Befund also nicht weg.

## 3. Moderation: Wann wirkt was anders?

| Interaktion | LR-χ² | p | Befund |
|---|---|---|---|
| Geschlecht × Viktimisierung | 0,30 | 0,58 | **kein Unterschied** |
| Geschlecht × Alter | 46,6 | <0,001 | signifikant |
| Geschlecht × Sozialvertrauen | 475,9 | <0,001 | signifikant |
| Bildung × Einkommen | 0,12 | 0,73 | kein Unterschied |
| Wohnort × Sozialvertrauen | 484,6 | <0,001 | signifikant |

Der erste Befund ist der inhaltlich wichtigste: **Frauen reagieren auf eigene
Betroffenheit nicht stärker als Männer.** Die Geschlechterlücke lässt sich damit
nicht als „Vulnerabilität durch Viktimisierung" erklären — sie besteht
unabhängig davon.

Bei fünf geprüften Interaktionen ist rein zufällig etwa ein Treffer in 20 Tests zu
erwarten; drei signifikante Treffer bei fünf Tests sind also mehr, als der Zufall
erklärt — aber die Effektstärken sind unterschiedlich groß.

## 4. Mediation: Über welche Wege wirkt ein Merkmal?

Bootstrap-Perzentilintervalle (1.000 Ziehungen), OLS-Pfade:

| Pfad | indirekter Effekt | 95-%-Intervall | Anteil am Gesamteffekt |
|---|---|---|---|
| Diskriminierung → Sozialvertrauen → Furcht | +0,0148 | +0,0099 bis +0,0199 | **30,3 %** |
| Bildung → Sozialvertrauen → Furcht | −0,0113 | −0,0129 bis −0,0099 | 22,5 % |
| Viktimisierung → Justizvertrauen → Furcht | +0,0059 | +0,0036 bis +0,0081 | 8,1 % |
| Zuwanderungseinstellung → Sozialvertrauen → Furcht | −0,0146 | −0,0164 bis −0,0129 | 21,7 % |

**Sozialvertrauen ist der durchgängige Vermittler.** Bei drei der vier geprüften
Pfade laufen 20 bis 30 Prozent des Zusammenhangs über das Vertrauen in andere
Menschen. Wer Diskriminierung erlebt, wer geringer gebildet ist oder wer
Zuwanderung skeptisch sieht, vertraut weniger — und weniger Vertrauen geht mit
mehr Furcht einher.

## Was daraus folgt — und was nicht

**Trägt:**
- Die Geschlechterlücke ist der stärkste und robusteste Einzelbefund. Sie ist
  nicht über Betroffenheit, Alter, Bildung, Einkommen oder Einstellungen
  erklärbar.
- Sozialvertrauen ist ein zentraler Angelpunkt — als Korrelat und als Vermittler.
- Viktimisierung erklärt Furcht erstaunlich schlecht.

**Trägt nicht:**
- Kausale Aussagen. Für jede Aussage „X führt zu Furcht" fehlt ein
  Identifikationsdesign. Panel-Daten (SOEP, PaWaKS) wären der nächste Schritt.
- Der Mediationsbefund setzt voraus, dass die zeitliche Reihenfolge stimmt
  (Diskriminierung → Vertrauen → Furcht). Im Querschnitt ist das eine Annahme,
  keine Beobachtung — die umgekehrte Richtung ist nicht ausgeschlossen.

## 5. Nachtrag: Warum Bootstrap — und war es nötig?

Die Pfadkoeffizienten stammen aus **gewöhnlichen OLS-Regressionen**. Einzig das
Konfidenzintervall des *Produkts* a·b war zu bestimmen: Der Standardfehler eines
Produkts ist nicht aus den Standardfehlern der Faktoren ablesbar, und die
Verteilung von a·b ist bei kleinen Effekten schief — ein symmetrisches
±1,96·SE-Intervall wäre nicht korrekt.

Vier Verfahren für denselben indirekten Effekt (`scripts/21`, `scripts/22`):

| Pfad | Sobel | Delta (mit Kovarianz) | Bootstrap 5.000 | lavaan-SEM |
|---|---|---|---|---|
| Diskriminierung → Furcht | +0,01475<br>[+0,00994, +0,01956] | +0,01475<br>[+0,01010, +0,01940] | +0,01475<br>[+0,00997, +0,01999] | +0,01480<br>[+0,00990, +0,01970] |
| Bildung → Furcht | −0,01126<br>[−0,01274, −0,00978] | −0,01126<br>[−0,01275, −0,00977] | −0,01126<br>[−0,01280, −0,00980] | −0,01155<br>[−0,01307, −0,01004] |
| Viktimisierung → Furcht | +0,00592<br>[+0,00375, +0,00808] | +0,00592<br>[+0,00376, +0,00808] | +0,00592<br>[+0,00376, +0,00824] | +0,00571<br>[+0,00355, +0,00788] |
| Zuwanderung → Furcht | −0,01456<br>[−0,01636, −0,01276] | −0,01456<br>[−0,01633, −0,01279] | −0,01456<br>[−0,01644, −0,01264] | −0,01472<br>[−0,01653, −0,01291] |

**Alle Verfahren kommen auf denselben Punktschätzer und praktisch dieselben
Intervalle.** Die Wahl des Verfahrens verändert den Befund nicht; der Bootstrap
war eine Absicherung, keine Notwendigkeit. Die kleine Abweichung beim
Bildungspfad im SEM erklärt sich aus der Stichprobe (16.237 Fälle im gemeinsamen
Modell gegenüber 16.603 im pfadspezifischen), nicht aus dem Verfahren.

Der Sobel-Test, der als zu konservativ gilt, liefert hier Intervalle derselben
Breite — bei Effekten dieser Größe und Fallzahl fällt der Unterschied nicht ins
Gewicht.

**Offen:**
- Medienkonsum ist nur in den Runden 8–11 erhoben und korreliert kaum mit Furcht
  (−0,023). Eine belastbare Prüfung der Medienhypothese braucht andere Daten
  (Berichterstattungszeitreihen, Panels).
- Die Länder- und Kreisebene ist in dieser Analyse nicht genutzt; bei 16
  Bundesländern wäre ein Länder-Scatter ein ökologischer Fehlschluss.
