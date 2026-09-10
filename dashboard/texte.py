# -*- coding: utf-8 -*-
"""
texte.py — Einordnungen, Interpretationen und Theoriebezüge je Diagramm
=======================================================================
Pro Diagramm-ID: Titel, Kurzzeile (lead), Einordnung (was man sieht),
Interpretation (was es bedeuten kann) und Theorie/Evidenz (Bezug zur
Forschung).

Zu den Literaturangaben: Genannt sind nur Arbeiten, die entweder in den
gesichteten Primärquellen dieses Projekts belegt sind (DIW Weekly Report
30/2025, SKiD 2024, DVS 2017) oder zum etablierten Lehrbuchstand der
Kriminalsoziologie gehören (Klassiker). Die Klassiker sind zur Orientierung
genannt, nicht als Beleg für die hier gezeigten Zahlen.
"""

TEXTE = {
"hellfeld": dict(
 titel="1 · Sinkt die Kriminalität?",
 lead="Registrierte Fälle in Deutschland, 1987–2025. Langfristig klar rückläufig, "
      "kurzfristig volatil — und ein Teil der Ausschläge ist Zählbereich, nicht Kriminalität.",
 einordnung="Dargestellt sind alle von der Polizei erfassten Fälle. Der Höchststand lag 1993 bei "
            "6,75 Mio, der bislang tiefste Wert 2021 bei 5,05 Mio; 2025 sind es 5,51 Mio. "
            "Gestrichelt markiert sind die großen Katalogänderungen 2011 und 2016, die den Zählbereich "
            "veränderten, ohne dass sich das Verhalten geändert hätte.",
 interpretation="Über drei Jahrzehnte ist der Trend fallend (–18 % seit 1993), aber nicht gleichmäßig: "
                "Auf den Tiefpunkt 2021 folgte ein Anstieg bis 2023 und seither wieder ein Rückgang. "
                "Wer kurze Zeitfenster vergleicht, kann daraus 'steigende' oder 'sinkende' Kriminalität "
                "ableiten — beides ist mit derselben Reihe möglich. Das ist der klassische Fehler "
                "willkürlich gewählter Startjahre.",
 theorie="Die PKS ist eine Eingangsstatistik: Erfasst wird, was der Polizei bekannt wird und was sie "
         "als Fall führt — nicht die begangene Kriminalität (Dunkelfeld) und nicht die bestätigte "
         "(Verurteilungen). Zur Selektionskette siehe Diagramm 6.",
 quellen="BKA, PKS, T01-Zeitreihe „Fälle ab 1987“, V1.1 (08.04.2026)"),
"gruppen": dict(
 titel="1b · Was steigt, was sinkt?",
 lead="Sieben Deliktshauptgruppen, indexiert auf 2002 = 100. Die Gesamtzahl verdeckt gegenläufige Bewegungen.",
 einordnung="Diebstahl fällt auf 59 % des Ausgangswerts (–41 %), Rohheitsdelikte steigen auf 146 %, "
            "Sexualdelikte auf 244 %. Vermögens-/Fälschungsdelikte, sonstige StGB-Tatbestände und "
            "Nebengesetze bewegen sich dazwischen.",
 interpretation="„Die Kriminalität“ gibt es nicht: Was sinkt, ist vor allem der Massendelikt Diebstahl. "
                "Der Anstieg bei Sexualdelikten ist überwiegend ein Zählbereichseffekt der "
                "Strafrechtsreformen 2017 und 2022 (Erweiterung des erfassten Verhaltens), der Anstieg "
                "bei Rohheitsdelikten enthält die 2021 neu erfasste Bedrohung (§ 241 StGB). "
                "Objektive Entwicklungen und Änderungen des Zählbereichs sind hier nicht trennbar.",
 theorie="Für die Furcht-Forschung ist das relevant, weil sich die Furcht an den Delikten orientiert, "
         "die medial präsent sind — nicht an den Delikten, die mengenmäßig dominieren.",
 quellen="BKA, PKS, T01-Zeitreihe; Zählbereichsänderungen laut PKS-Änderungsnachweisen"),
"eu": dict(
 titel="1c · Deutschland im EU-Vergleich",
 lead="Registrierte Wohnungseinbrüche je 100.000 Einwohner: Deutschland gegenüber dem Median der "
      "europäischen Länder mit übereinstimmender Definition.",
 einordnung="Deutschland: 131,7 (2008) → 94,0 (2024), ein Rückgang um 29 %. Der EU-Median liegt "
            "durchweg höher und bewegt sich weniger stark (rund 150–200 je 100.000).",
 interpretation="Der deutsche Einbruchsrückgang ist kein Messartefakt einer einzelnen nationalen "
                "Statistik — er zeigt sich auch in der harmonisierten Eurostat-Reihe und liegt über "
                "dem Durchschnitt der Vergleichsländer. Gleichzeitig bleibt die deutsche Belastung "
                "im Mittelfeld; Länder wie Dänemark, die Niederlande oder Belgien liegen teils deutlich "
                "höher.",
 theorie="Als Erklärung für den europaweiten Rückgang werden vor allem technische Sicherung "
         "(Verriegelungen, Alarmanlagen) und die Verlagerung auf andere Deliktsfelder diskutiert "
         "(Situative Kriminalprävention, „target hardening“). Die Ländervergleichbarkeit bleibt "
         "eingeschränkt: Meldewege, Versicherungspflichten und Erfassungsregeln unterscheiden sich.",
 quellen="Eurostat, crim_off_cat (ICCS 05012 «Burglary of private residential premises», Rate je "
         "100.000 Einwohner); eigene Berechnung des Länder-Medians"),
"angst": dict(
 titel="2 · Die Angst über zwei Jahrzehnte",
 lead="Anteil der Befragten, die sich nachts beim Alleingehen in ihrer Wohngegend unsicher fühlen "
      "(ESS Deutschland, 2002–2023).",
 einordnung="Der Wert fiel von 26,2 % (2002) auf 22,0 % (2014), sprang 2016 auf 27,2 % und liegt "
            "2023 bei 25,0 %. Deutschland fehlt in Runde 10 (2020) — die Linie hat dort eine Lücke.",
 interpretation="Die Furcht folgt nicht dem Hellfeld: Dieses fiel im selben Zeitraum deutlich. "
                "Bemerkenswert ist der Sprung zwischen 2014 und 2016 — also in den Jahren, in denen "
                "Migration und Sicherheit die öffentliche Debatte dominierten, während die "
                "registrierte Gewaltkriminalität nur moderat zunahm. Ob der Sprung ein "
                "Stimmungseffekt, ein Kohorteneffekt oder ein tatsächlicher Erfahrungswandel war, "
                "lässt sich mit diesen Daten nicht entscheiden.",
 theorie="Erklärt wird solche Entkopplung über Verfügbarkeits- und Medienwirkungseffekte: Je "
         "präsenter ein Thema in der Berichterstattung ist, desto häufiger und bedrohlicher wird es "
         "eingeschätzt (Verfügbarkeitsheuristik, Tversky/Kahneman 1973; Kultivierungshypothese, "
         "Gerbner/Gross 1976). Die DIW-Analyse auf SOEP-Basis zeigt für dieselben Jahre, dass sich "
         "die Korrelation zwischen Furcht und Kriminalität nach 2013 umkehrt.",
 quellen="European Social Survey, Runden 1–11 (DE), eigene Berechnung; gewichtet (pspwght), "
         "95-%-Intervall als Näherung ohne Designeffekt"),
"soep": dict(
 titel="2b · Soziale und personale Furcht",
 lead="Zwei verschiedene Dinge: die Sorge um die Kriminalitätsentwicklung im Land (soziale Furcht) "
      "und die Furcht, selbst betroffen zu sein (personale Furcht).",
 einordnung="Nach der SOEP-Auswertung des DIW lag der Anteil mit großen Sorgen über die "
            "Kriminalitätsentwicklung im Jahr 2000 bei rund 54 %, fiel bis 2013 auf rund 31 % und "
            "stieg danach wieder auf 38 % (2023). Die Korrelation dieser sozialen Furcht mit den "
            "Kriminalitätsraten war 2000–2013 stark positiv (r = 0,88), 2014–2017 stark negativ "
            "(r = −0,71) und 2018–2023 wieder positiv (r = 0,67).",
 interpretation="Die Umkehr des Vorzeichens 2014–2017 ist der präziseste Beleg für die Entkopplung: "
                "Die Furcht stieg, während die Kriminalität fiel. Gleichzeitig zeigt der Befund, dass "
                "soziale und personale Furcht auseinanderlaufen können — wer die Kriminalitätsentwicklung "
                "im Land für bedrohlich hält, muss sich nicht persönlich bedroht fühlen.",
 theorie="Die Unterscheidung geht auf die Furcht-Forschung der 1990er Jahre zurück (affektive, "
         "kognitive und konative Dimension; Boers 1994). Der DIW-Report führt die Phase ab 2014 auf "
         "eine Veränderung der öffentlichen Debatte und der Berichterstattung zurück und nennt "
         "ausdrücklich die Ereignisse 2015/2016 (Paris, Köln, Berlin) als Zäsur.",
 quellen="DIW Weekly Report 30/2025 (Bindler/Walther, SOEP v40 + PKS), DOI 10.18723/diw_dwr:2025-30-1. "
         "Die Jahreswerte der Abbildungen sind im Bericht nicht beschriftet; zitiert sind hier die "
         "im Text genannten Werte und Korrelationen. Eine eigene Nachrechnung würde SOEP-Mikrodaten "
         "erfordern (Datenvertrag)"),
"anker": dict(
 titel="2c · Wovor genau? Die vier Messpunkte",
 lead="Deliktsspezifische Furcht in den deutschen Viktimisierungssurveys: DVS 2012/2017 und "
      "SKiD 2020/2024.",
 einordnung="Furcht vor Wohnungseinbruch: 18,8 % (2012) → 24,0 % (2017) → 27,1 % (2020) → 28,6 % "
            "(2024). Ähnlich verlaufen Körperverletzung und Raub. Die graue Fläche markiert den "
            "Instrumentenwechsel von der DVS zur SKiD zwischen 2017 und 2020.",
 interpretation="Mehr als vier Messpunkte gibt es für die deliktsspezifische Furcht in Deutschland "
                "nicht — jede Linie zwischen ihnen ist Interpolation, keine Messung. Der Anstieg "
                "zwischen 2012 und 2017 ist überwiegend innerhalb desselben Instruments gemessen und "
                "damit belastbar; der weitere Anstieg bis 2024 fällt in den Bereich des neuen "
                "Instruments und ist deutlich kleiner.",
 theorie="Die DVS wurde nach zwei Wellen eingestellt und durch die SKiD ersetzt. Solche "
         "Instrumentenwechsel sind ein Standardproblem der Furchtforschung: Schon geringe "
         "Änderungen von Frageformulierung, Antwortskala und Erhebungsmodus verschieben das "
         "Antwortniveau. Wer die Reihe über 2017 hinaus als „Anstieg“ liest, muss diesen Bruch "
         "benennen.",
 quellen="BKA: DVS 2012 und 2017 (Abb. 23; Splitsample n = 11.643 bzw. 6.079), SKiD 2020 "
         "(n = 45.351) und 2024 (n = 54.392), Abb. 26"),
"delikte": dict(
 titel="3 · Das Deliktprofil der Furcht",
 lead="Wovor die Menschen sich fürchten (SKiD 2020 und 2024): Internetbetrug führt deutlich, "
      "Einbruch und Körperverletzung folgen.",
 einordnung="Betrug im Internet: 52,0 % (2020: 42,0 %). Danach Sachbeschädigung 30,9, Einbruch 28,6, "
            "Diebstahl 27,5, Körperverletzung 26,8, sexuelle Belästigung 24,0, Terroranschlag 23,0, "
            "Vorurteilskriminalität 17,2 %. Der Anstieg ist bei allen Delikten außer Einbruch "
            "statistisch signifikant.",
 interpretation="Die Rangfolge der Furcht folgt nicht der Schwere der Delikte (Terrorismus steht "
                "hinten, Mord wird gar nicht abgefragt) und nicht ihrer Häufigkeit im Hellfeld "
                "(Internetbetrug ist dort kein eigenes Massendelikt). Sie folgt eher dem, was als "
                "alltäglich erfahrbar und schwer kontrollierbar gilt.",
 theorie="Für die Deliktsabhängigkeit der Furcht sind wahrgenommene Kontrollierbarkeit und "
         "Vorstellbarkeit zentral: Betrug im Internet gilt als unvermeidbar und wird mit Kontrollverlust "
         "verbunden. Die starke Zunahme 2020→2024 fällt in die Zeit, in der Online-Banking und "
         "Onlinehandel weiter zunahmen.",
 quellen="BKA, SKiD 2024, Kapitel 6.3, Abb. 26 (n = 54.392) und SKiD 2020 (n = 45.351)"),
"risiko": dict(
 titel="3b · Furcht und Risikoeinschätzung",
 lead="Beunruhigung (affektiv) gegenüber der Einschätzung, selbst betroffen zu werden (kognitiv), "
      "SKiD 2024.",
 einordnung="Bei allen acht Delikten liegt die Beunruhigung über der eigenen Risikoeinschätzung. "
            "Am größten ist die Lücke bei Körperverletzung (26,8 % gegenüber 13,1 %), sexueller "
            "Belästigung und Einbruch; am kleinsten bei Vorurteilskriminalität.",
 interpretation="Gefühlt wird mehr gefürchtet, als für wahrscheinlich gehalten wird — die emotionale "
                "Bewertung ist also nicht bloß eine Folge der kognitiven. Das ist konsistent mit der "
                "Beobachtung, dass Aufklärung über Risiken die affektive Furcht nur begrenzt senkt.",
 theorie="Die Trennung zwischen affektiver und kognitiver Furchtkomponente ist Standard der "
         "Furcht-Forschung. In der Risikowahrnehmungsforschung gilt zudem: Risiken, die als "
         "unfreiwillig, unbekannt und katastrophal eingestuft werden, erzeugen mehr Furcht als ihre "
         "Häufigkeit nahelegt (Slovic 1987).",
 quellen="BKA, SKiD 2024, Kapitel 6.3 und 6.4 (Abb. 26 und 27)"),
"praevalenz": dict(
 titel="3c · Furcht und tatsächliche Betroffenheit",
 lead="Selbst berichtete Betroffenheit (letzte 12 Monate) gegenüber der Furcht vor dem Delikt, "
      "SKiD 2024.",
 einordnung="Körperverletzung: 2,6 % berichten, betroffen gewesen zu sein — 26,8 % fürchten sich. "
            "Internetbetrug: 18 % Betroffenheit, 52 % Furcht. Die Punkte liegen bei allen Delikten "
            "weit über der Diagonalen (Gleichstand).",
 interpretation="Furcht ist keine Abbildung persönlicher Erfahrung. Die Mehrheit der Furchtsamen hat "
                "keine eigene Betroffenheit — und ein erheblicher Teil der Betroffenen entwickelt keine "
                "dauerhafte Furcht. Für Präventionskommunikation heißt das: Betroffenheit allein "
                "erklärt die Furcht nicht.",
 theorie="Das Muster ist in der Literatur als Gegenstück zum „Viktimisierungs-Furcht-Paradox“ "
         "bekannt: Nicht die Erfahrung, sondern wahrgenommene Verletzlichkeit und die Situation im "
         "Wohnumfeld erklären Furcht am besten (Vulnerabilitätsansatz; Skogan/Maxfield 1981, "
         "Überblick bei Hale 1996). Neuere Paneldaten aus Köln und Essen zeigen zudem, dass eine "
         "Viktimisierung die Furcht vor allem dort erhöht, wo Kriminalität selten ist (Justice "
         "Quarterly 2024).",
 quellen="BKA, SKiD 2024: Furcht (Kap. 6.3) und 12-Monats-Prävalenz (Kap. 4)"),
"geschlecht": dict(
 titel="4 · Die stabilste Lücke: Geschlecht",
 lead="Unsicherheitsgefühl nachts beim Alleingehen, Frauen und Männer, 2002–2023.",
 einordnung="Frauen liegen durchgängig rund 25 Prozentpunkte über Männern: 39,2 % gegenüber 12,3 % "
            "(2002), 37,5 % gegenüber 12,2 % (2023). Die Lücke ist über zwei Jahrzehnte nahezu "
            "unverändert — trotz aller Veränderungen im Hellfeld.",
 interpretation="Diese Konstanz spricht dafür, dass die Geschlechterdifferenz nicht auf aktuelle "
                "Kriminalitätsentwicklung reagiert, sondern auf eine stabile, sozialisierte "
                "Risikowahrnehmung. Entscheidend ist: Frauen sind bei den Delikten, die sie am "
                "stärksten fürchten (sexualisierte Gewalt), tatsächlich überproportional betroffen — "
                "gemessen an objektiven Risiken ist die Differenz bei anderen Delikten jedoch größer "
                "als die Belastungsunterschiede.",
 theorie="Erklärt wird das überwiegend mit dem „Schatten der sexualisierten Gewalt“ (shadow of "
         "sexual assault): Die Furcht vor Vergewaltigung und sexueller Belästigung färbt die Furcht "
         "vor allen anderen Situationen ein. Für Deutschland zeigen Hirtenlehner, Farrall und Groß "
         "(2023), dass dieser Effekt über alle Altersgruppen wirkt und mit dem Alter sogar zunimmt.",
 quellen="ESS-DE Runden 1–11, eigene Berechnung, gewichtet"),
"alter": dict(
 titel="4b · Der Alterswandel",
 lead="Unsicherheitsgefühl nach Altersgruppe, 2002–2023. Die Rangfolge hat sich umgedreht.",
 einordnung="2002 waren die über 75-Jährigen mit 41,0 % die ängstlichste Gruppe, die 16- bis "
            "29-Jährigen mit 22,3 % die gelassenste. 2023 liegen die 16- bis 29-Jährigen mit 32,3 % "
            "vorn, die über 75-Jährigen bei 27,6 %.",
 interpretation="Der klassische Befund „ältere Menschen fürchten sich mehr“ gilt für Deutschland nicht "
                "mehr. Der Wandel könnte drei Ursachen haben: eine Kohortenabfolge (jüngere Generationen "
                "sind mit anderen Sicherheitsdiskursen aufgewachsen), eine Veränderung der Lebenslagen "
                "Jüngerer, oder eine veränderte Zusammensetzung der Ängste. Mit Querschnittsdaten "
                "lassen sich diese Erklärungen nicht trennen — dafür bräuchte es Paneldaten, die "
                "dieselben Personen über die Zeit begleiten.",
 theorie="Die Vulnerabilitätstheorie sagt höhere Furcht für Gruppen mit geringerer Bewältigungsfähigkeit "
         "voraus (alte Menschen, Frauen, sozial Schwache). Der Befund widerspricht dem für die "
         "Altersdimension — und ist ein Argument dafür, den Vulnerabilitätsbegriff nicht rein körperlich "
         "zu fassen, sondern sozial und lebenslagenspezifisch (Hale 1996 zur Diskussion).",
 quellen="ESS-DE Runden 1–11, eigene Berechnung, gewichtet"),
"struktur": dict(
 titel="4c · Furcht folgt der sozialen Lage",
 lead="Anteil mit Unsicherheitsgefühl nach sozialen Merkmalen (ESS-DE, alle Wellen gepoolt).",
 einordnung="Die höchsten Werte zeigen Menschen mit Diskriminierungserfahrung (34,5 %), Arbeitslose "
            "(31,1 %) und Personen mit niedriger Bildung (28,3 % gegenüber 15,2 % bei tertiärer "
            "Bildung). Großstadtbewohner fürchten sich häufiger als Landbewohner, Menschen mit "
            "Migrationshintergrund häufiger als ohne (26,8 gegenüber 23,7 %).",
 interpretation="Furcht ist sozial ungleich verteilt und folgt nicht dem Muster der objektiven "
                "Viktimisierungswahrscheinlichkeit in jeder Dimension. Die Unterschiede sind bivariat, "
                "also unbereinigt — Bildungs- und Migrationsmerkmal, Einkommen und Wohnort sind "
                "miteinander verschränkt. Eine belastbare Zuschreibung einzelner Effekte bräuchte "
                "multivariate Modelle.",
 theorie="Vulnerabilitäts- und Sozialkapitalansätze erklären das Muster gemeinsam: Furcht ist höher "
         "bei geringeren Bewältigungsressourcen und schwächeren sozialen Netzwerken. Auf "
         "Nachbarschaftsebene zeigt der Collective-Efficacy-Ansatz (Sampson, Raudenbush und Earls "
         "1997), dass nicht Kriminalität allein, sondern die soziale Kohäsion das Sicherheitsgefühl "
         "prägt.",
 quellen="ESS-DE Runden 1–11, gepoolt, gewichtet; n je Gruppe im Tooltip"),
"einstellungen": dict(
 titel="4d · Furcht und Einstellungen",
 lead="Unsicherheitsgefühl nach Ausprägung von Vertrauen, Zufriedenheit und Einschätzungen "
      "(Median-Split, ESS-DE gepoolt).",
 einordnung="Die größten Abstände zeigen sich beim Sozialvertrauen (30,5 % bei niedrigem, 15,0 % bei "
            "hohem Vertrauen), bei der Gesundheit (26,2 gegenüber 14,9 %), der Demokratiezufriedenheit "
            "(29,1 gegenüber 17,5 %) und der Einstellung zur Zuwanderung (28,6 gegenüber 16,2 %). "
            "Auch beim Polizeivertrauen zeigt sich ein deutlicher Abstand.",
 interpretation="Furcht hängt eng mit einer allgemeinen Haltung zu Gesellschaft und Institutionen "
                "zusammen. Die Richtung ist mit diesen Daten nicht bestimmbar: Ob geringes Vertrauen "
                "die Furcht erhöht, ob die Furcht das Vertrauen erodiert, oder ob beide von derselben "
                "dritten Größe (etwa soziale Lage) getrieben werden, bleibt offen.",
 theorie="In der Forschung wird dieses Bündel als „generalized insecurity“ diskutiert: Kriminalitäts"
         "furcht als Teil eines umfassenderen Unsicherheitsgefühls gegenüber sozialem Wandel. Für "
         "Deutschland berichtet der DIW-Report, dass die Sorge um die Kriminalitätsentwicklung mit "
         "der allgemeinen gesellschaftlichen Unzufriedenheit einhergeht.",
 quellen="ESS-DE Runden 1–11, Median-Split je Item, gepoolt, gewichtet"),
"vermeidung": dict(
 titel="5 · Was die Menschen tun",
 lead="Vermeide- und Schutzverhalten (SKiD 2024), gesamt und für Frauen.",
 einordnung="41,7 % weichen Fremden aus, 38,9 % lassen die Wohnung bewohnt wirken, 35,4 % meiden den "
            "ÖPNV nachts, 28,6 % verlassen nachts das Haus nicht. Bei Frauen liegen die Werte deutlich "
            "höher (nachts Haus nicht verlassen über 40 %, nur in Begleitung 39,0 %), bei Männern "
            "entsprechend niedriger.",
 interpretation="Furcht ist nicht nur ein Gefühl, sondern hat messbare Verhaltensfolgen — und diese "
                "sind ungleich verteilt. Einschränkungen der Bewegungsfreiheit betreffen überwiegend "
                "Frauen. In der Bewertung solcher Zahlen ist zu beachten, dass Vermeidung auch "
                "wirksam sein kann: Wer Situationen meidet, sinkt sein Risiko — und taucht dann "
                "seltener in Viktimisierungsstatistiken auf.",
 theorie="Die konative Dimension der Furcht (Verhaltensanpassung) wird in der Forschung als "
         "eigenständige Größe geführt (Boers 1994). Sie ist für die Wohlfahrtswirkung von Furcht "
         "entscheidend: Der Schaden entsteht nicht nur durch Kriminalität, sondern auch durch "
         "vermiedene Lebensaktivitäten.",
 quellen="BKA, SKiD 2024, Kapitel 6.5 (Abb. 28/29)"),
"orte": dict(
 titel="5b · Wo die Angst sitzt",
 lead="Anteil derer, die sich nachts an verschiedenen Orten sicher fühlen (SKiD 2024).",
 einordnung="In der eigenen Wohngegend fühlen sich 74,0 % sicher, im ÖPNV 44,8 %, auf Straßen und "
            "Plätzen 40,1 %, an Bahnhöfen 27,0 % und in Parks 22,8 %. Frauen liegen an allen Orten "
            "darunter — in Parks bei 11,1 %.",
 interpretation="Furcht ist situativ: Dasselbe Deliktrisiko erzeugt an vertrauten Orten (Wohngegend) "
                "kaum Furcht, an unübersichtlichen und fremdbestimmten Orten (Park, Bahnhof, ÖPNV) "
                "dagegen viel. Die Muster entsprechen räumlichen Kontroll- und Sichtbarkeitsbedingungen "
                "— nicht der Deliktverteilung.",
 theorie="Die Umweltkriminologie führt das auf situative Merkmale zurück: Überschaubarkeit, "
         "Fluchtmöglichkeiten, soziale Kontrolle, Anwesenheit anderer (Routine-Activity-Ansatz, "
         "Cohen/Felson 1979; „incivilities“-Forschung zum Wohnumfeld).",
 quellen="BKA, SKiD 2024, Kapitel 6.2 (Abb. 23/25)"),
"trichter": dict(
 titel="6 · Der Trichter: von der Erfahrung zur Verurteilung",
 lead="Vier Stufen für vier Deliktsbereiche: polizeilich registrierte Fälle, davon aufgeklärt, "
      "davon zu einer Verurteilung führend.",
 einordnung="Beispiel Wohnungseinbruch: 82.920 registrierte Fälle (2025), 11.672 aufgeklärt (14,1 %), "
            "5.844 Verurteilungen nach den einschlägigen Diebstahlstatbeständen (§§ 243, 244, 244a "
            "StGB im Jahr 2024). Bei Diebstahl insgesamt stehen 1,81 Mio registrierten Fällen 75.740 "
            "Verurteilungen gegenüber (4,2 %).",
 interpretation="Die registrierte Fallzahl ist weder die Zahl der begangenen Taten noch die der "
                "bestätigten. Zwischen beiden liegt eine doppelte Selektion: Nur ein Teil des "
                "Dunkelfelds wird angezeigt, und nur ein Teil der angezeigten Fälle führt zu einer "
                "Verurteilung. Die Verurteilungszahlen sind zudem eine andere Einheit (verurteilte "
                "Personen, nach dem schwersten Delikt des Verfahrens, mit Zeitverzug zum Tatjahr) — "
                "der Vergleich zeigt die Größenordnung, nicht eine exakte Quote.",
 theorie="Diese Selektionskette ist das Kernstück der Hellfeld-Interpretation. Die Anzeigequote ist "
         "deliktsabhängig und selbst veränderlich: Für Einbruchdiebstahl liegt sie laut SKiD bei "
         "rund 87 % (vollendete Taten), für Sexualdelikte bei 6 %. Fällt die Anzeigequote, sinkt die "
         "PKS-Zahl, ohne dass sich die Kriminalität ändert.",
 quellen="BKA PKS 2025 (T01 Fälle, T12 aufgeklärte Fälle); Destatis, Statistischer Bericht "
         "Strafverfolgung 2024 (Tabelle 24311-05); BKA SKiD 2024 (Anzeigequoten)"),
"aufklaerung": dict(
 titel="6b · Aufklärungsquoten 2025",
 lead="Anteil der Fälle mit mindestens einem ermittelten Tatverdächtigen, nach Deliktsgruppe.",
 einordnung="Nebengesetze 92,2 %, Tötungsdelikte 91,0 %, Rohheitsdelikte 86,5 % — aber Diebstahl "
            "31,9 % und Wohnungseinbruch 14,1 %. Über alle Delikte: 57,9 %.",
 interpretation="„Aufgeklärt“ heißt nur, dass ein Tatverdächtiger ermittelt wurde — nicht, dass ein "
                "Gericht die Tat bestätigt hat. Genau die Delikte, die das Furchtprofil prägen "
                "(Einbruch, Diebstahl), haben die niedrigsten Aufklärungsquoten: Die Furcht "
                "konzentriert sich auf Bereiche, in denen das Strafverfolgungssystem am wenigsten "
                "sichtbare Erfolge erzielt.",
 theorie="Für die Beurteilung der Strafverfolgungswirkung ist die Unterscheidung von Aufklärung, "
         "Anklage und Verurteilung zentral. Hohe Aufklärungsquoten bei Tötungsdelikten erklären sich "
         "aus der Ermittlungsintensität bei wenigen Fällen und der engen Beziehung zwischen Täter und "
         "Opfer; Einbruchdelikte haben hohe Fallzahlen, geringe Spurenlagen und keine Beziehung.",
 quellen="BKA PKS 2025: T01 (erfasste Fälle) und T12 (aufgeklärte Fälle), eigene Berechnung"),
"tv": dict(
 titel="7 · Tatverdächtige: Staatsangehörigkeit und Belastungszahl",
 lead="Links: Anteil nichtdeutscher Tatverdächtiger an allen Tatverdächtigen. Rechts: "
      "Tatverdächtigenbelastungszahl je 100.000 Einwohner der jeweiligen Bevölkerungsgruppe. "
      "Ab 2009 gilt die „echte“ Tatverdächtigenzählung — Werte vor und nach 2009 sind nicht "
      "direkt vergleichbar.",
 einordnung="Der Anteil nichtdeutscher Tatverdächtiger steigt von 20,0 % (1987) über 33,6 % (1993) "
            "auf 40,1 % (2025). Die Belastungszahl (ab 2009 verfügbar) liegt für die nichtdeutsche "
            "Wohnbevölkerung rund zwei- bis dreimal höher als für die deutsche: 2025 etwa 5.131 "
            "gegenüber 1.814 je 100.000.",
 interpretation="Beide Zahlen sind ausdrücklich keine Kriminalitätsraten im Sinne eines "
                "Verursachungsmaßes. Der Anteilswert ist stark von der Größe und Zusammensetzung der "
                "nichtdeutschen Wohnbevölkerung abhängig: 1993 (Asylzuwanderung) und nach 2015 "
                "(Fluchtmigration) erreicht er Spitzen, weil der Zähler schneller wächst als der "
                "Nenner. Die Belastungszahl korrigiert das teilweise, unterliegt aber weiterhin "
                "Verzerrungen: Touristen, Durchreisende und Menschen ohne Wohnsitz erscheinen im "
                "Zähler, nicht im Nenner; die Kontrolldichte der Polizei ist unterschiedlich; das "
                "Anzeigeverhalten unterscheidet sich.",
 theorie="Die Forschungslage spricht dafür, Gruppenunterschiede nicht als Gruppenmerkmal zu lesen: "
         "Eine Analyse von PKS-Kreisdaten (2018–2023) findet keinen Zusammenhang zwischen der "
         "Änderung des regionalen Ausländeranteils und der Kriminalitätsrate, sondern erklärt die "
         "Überrepräsentation überwiegend durch ortsspezifische Faktoren (Altersstruktur, "
         "Sozialstruktur, Aufenthaltsstatus). Eurostat- und PKS-Kommentare weisen zusätzlich darauf "
         "hin, dass die Bevölkerungsbasis in den Nennern lückenhaft ist.",
 quellen="BKA PKS-Zeitreihen T20/T40/T50 und TVBZ ab 2009 (Tatverdächtigenbelastungszahlen, "
         "V1.0/12.03.2026); Fußnoten und Hinweise der BKA-Zeitreihen"),
"methodik": dict(
 titel="8 · Daten, Methodik, Grenzen",
 lead="Was hier zusammengeführt wurde, wie es erhoben wurde und was es nicht hergibt.",
 einordnung="",
 interpretation="",
 theorie="",
 quellen=""),
}
