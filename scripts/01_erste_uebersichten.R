#!/usr/bin/env Rscript
# ============================================================
# 01_erste_uebersichten.R
# Projekt: 47_kriminalitaetsdiskrepanz_de
# Erste Übersichten: Entwicklung der registrierten Kriminalität
# (PKS-Hellfeld) und der Kriminalitätsfurcht (DVS/SKiD-Dunkelfeld).
#
# Datenquellen:
#  - BKA PKS, T01-Zeitreihe "Fälle ab 1987" (bund/2025/T01-ZR-Bund-Fälle_xls.xlsx,
#    V1.1 vom 08.04.2026) -> data/raw/pks/bund/2025/
#  - DVS 2012/2017, SKiD 2020/2024 Ergebnisberichte (data/raw/dvs, data/raw/skid)
#
# Ausgabe: output/ (PNG-Charts + bereinigte Langdaten als CSV)
# Reproduzierbar: von beliebigem Arbeitsverzeichnis ausführbar.
# ============================================================

suppressMessages({
  library(readxl)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(patchwork)
})

# --- Pfade ---------------------------------------------------
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
if (length(file_arg) > 0) {
  script_dir <- dirname(normalizePath(sub("^--file=", "", file_arg[1])))
} else {
  script_dir <- getwd()
}
ROOT <- normalizePath(file.path(script_dir, ".."))
RAW_PKS <- file.path(ROOT, "data/raw/pks/bund/2025/T01-ZR-Bund-Fälle_xls.xlsx")
OUT_DIR <- file.path(ROOT, "output")
dir.create(OUT_DIR, showWarnings = FALSE)

# --- Furcht-Ankerpunkte (aus Primärquellen verifiziert) ------
# Definition: Anteil "ziemlich oder sehr beunruhigt", Opfer des
# Delikts zu werden (affektive Kriminalitätsfurcht), Bevölkerung ab 16 J.
# Quellen: DVS-2012 (2014er-Bericht, Abb. "Furcht vor Wohnungseinbruch");
#          DVS-2017 (2018er-Ergebnisbericht, Abb. 23, n=6079);
#          SKiD-2020 (Ergebnisbericht V1.4); SKiD-2024 (Ergebnisbericht, Abb. 26, n=54392).
# Instrumentenwechsel DVS -> SKiD zwischen 2017 und 2020 -> kein
# durchgezogener Linienzug über die Instrumentengrenze.
FURCHT_WED <- tibble(
  jahr       = c(2012, 2017, 2020, 2024),
  prozent    = c(18.8, 24.0, 27.1, 28.6),
  instrument = c("DVS", "DVS", "SKiD", "SKiD"),
  n          = c("n = 11.643", "n = 6.079", "n = 45.351", "n = 54.392")
)
FURCHT_DIEBSTAHL <- tibble(
  jahr       = c(2020, 2024),
  prozent    = c(22.1, 27.5),
  instrument = c("SKiD", "SKiD"),
  n          = c("n = 45.351", "n = 54.392")
)
# Signifikanz laut Quellen: DVS 2012->2017 WED +5,2 PP signifikant;
# SKiD 2020->2024 WED +1,5 PP NICHT signifikant; Diebstahl +5,4 PP signifikant.

# --- Belegwerte (Verifikation gegen Landkarte/Skill) ---------
# Wenn diese nicht reproduzierbar sind, bricht das Skript ab.
BELEG <- list(
  wed_2002 = c(130055, 157.8),
  wed_2015 = c(167136, 205.8),
  wed_2020 = c(75023, 90.20797),
  wed_2025 = c(82920, 99.21373),
  dieb_2002 = c(3090154, NA),
  dieb_2025 = c(1813141, NA)
)

# ============================================================
# 1) T01-Zeitreihe einlesen
# ============================================================
cat("Lese T01-Zeitreihe:", RAW_PKS, "\n")
t01 <- read_excel(RAW_PKS, skip = 15, col_names = FALSE)
t01 <- t01[, 1:5]
names(t01) <- c("schluessel", "straftat", "jahr", "faelle", "hz")
t01 <- t01 %>%
  mutate(
    jahr   = as.integer(.data$jahr),
    faelle = as.numeric(.data$faelle),
    hz     = as.numeric(.data$hz)
  ) %>%
  filter(!is.na(.data$jahr))

# --- Verifikation gegen Belegwerte --------------------------
check_value <- function(d, sch, j, spalte, erwartet, tol = 1e-4) {
  wert <- d %>% filter(.data$schluessel == sch, .data$jahr == j) %>% pull({{ spalte }})
  stopifnot(length(wert) == 1, abs(wert - erwartet) <= tol)
}
check_value(t01, "435*00", 2002, faelle, BELEG$wed_2002[1], 0.5)
check_value(t01, "435*00", 2015, faelle, BELEG$wed_2015[1], 0.5)
check_value(t01, "435*00", 2020, faelle, BELEG$wed_2020[1], 0.5)
check_value(t01, "435*00", 2025, faelle, BELEG$wed_2025[1], 0.5)
check_value(t01, "435*00", 2015, hz, BELEG$wed_2015[2])
check_value(t01, "435*00", 2025, hz, BELEG$wed_2025[2])
check_value(t01, "****00", 2002, faelle, BELEG$dieb_2002[1], 0.5)
check_value(t01, "****00", 2025, faelle, BELEG$dieb_2025[1], 0.5)
cat("Belegwerte verifiziert: WED 2002/2015/2020/2025 und Diebstahl 2002/2025 OK.\n")

# --- Reihen selektieren --------------------------------------
DELIKTE <- c(
  "------" = "Straftaten insgesamt",
  "****00" = "Diebstahl insgesamt",
  "3***00" = "Einfacher Diebstahl",
  "4***00" = "Schwerer Diebstahl",
  "435*00" = "Wohnungseinbruchdiebstahl",
  "436*00" = "Tageswohnungseinbruch (darunter)"
)
reihen <- t01 %>%
  filter(.data$schluessel %in% names(DELIKTE)) %>%
  mutate(delikt = factor(DELIKTE[.data$schluessel],
                         levels = unname(DELIKTE)))

# Langdaten exportieren (Wiederverwendung in R/Positron)
reihen %>%
  select(schluessel, delikt, jahr, faelle, hz) %>%
  arrange(schluessel, jahr) %>%
  readr::write_csv(file.path(OUT_DIR, "t01_bund_zeitreihe_clean.csv"))
cat("Langdaten exportiert: output/t01_bund_zeitreihe_clean.csv\n")

# ============================================================
# Plot-Stil
# ============================================================
THEME <- theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 13),
    plot.subtitle = element_text(color = "grey35", size = 10),
    plot.caption = element_text(color = "grey50", size = 8, hjust = 0),
    panel.grid.minor = element_blank(),
    legend.position = "bottom"
  )
FARBE_HELLFELD <- "#1f4e79"   # dunkles Blau
FARBE_FURCHT    <- "#b22222"  # dunkles Rot
FARBE_ZWEIT     <- "#6baed6"

dez <- function(x) format(x, big.mark = ".", decimal.mark = ",")
# Eine Nachkommastelle, deutsche Formate (für HZ-/Prozent-Beschriftungen)
dez1 <- function(x) formatC(x, format = "f", digits = 1,
                            big.mark = ".", decimal.mark = ",")
# Achsen: ",0" nur zeigen, wenn tatsächlich Nachkommastellen nötig
dez_achse <- function(x) {
  ifelse(x == round(x),
         formatC(x, format = "d", big.mark = ".", decimal.mark = ","),
         formatC(x, format = "f", digits = 1, big.mark = ".", decimal.mark = ","))
}

# ============================================================
# Figur 1: Straftaten insgesamt, 1987-2025
# ============================================================
ges <- reihen %>% filter(.data$schluessel == "------")

p_ges_faelle <- ggplot(ges, aes(x = .data$jahr, y = .data$faelle / 1e6)) +
  geom_vline(xintercept = c(2011, 2016), color = "grey70", linetype = "dashed") +
  annotate("text", x = 2011.35, y = 7.15, label = "Kat. 2011",
           hjust = 0, size = 2.6, color = "grey45") +
  annotate("text", x = 2016.35, y = 7.15, label = "Kat. 2016",
           hjust = 0, size = 2.6, color = "grey45") +
  geom_line(linewidth = 0.9, color = FARBE_HELLFELD) +
  scale_x_continuous(breaks = seq(1987, 2025, by = 4)) +
  scale_y_continuous(labels = dez1, limits = c(4, 7.4),
                     breaks = seq(4, 7, by = 0.5)) +
  labs(
    title = "Registrierte Straftaten in Deutschland (PKS, Hellfeld)",
    subtitle = "Straftaten insgesamt, 1987\u20132025; Fälle in Mio.",
    x = NULL, y = "Erfasste Fälle (Mio.)",
    caption = "Quelle: BKA PKS, T01-Zeitreihe 'Fälle ab 1987', Stand V1.1 (08.04.2026).\nGestrichelt: Katalogänderungen 2011 (Diebstahlskatalog) und 2016 (Betrugskatalog) \u2013 Reihen nur eingeschränkt vergleichbar."
  ) +
  THEME

p_ges_hz <- ggplot(ges, aes(x = .data$jahr, y = .data$hz)) +
  geom_vline(xintercept = c(2011, 2016), color = "grey70", linetype = "dashed") +
  geom_vline(xintercept = 2024, color = "grey70", linetype = "dotted") +
  annotate("text", x = 2011.35, y = 8800, label = "Kat. 2011",
           hjust = 0, size = 2.6, color = "grey45") +
  annotate("text", x = 2016.35, y = 8800, label = "Kat. 2016",
           hjust = 0, size = 2.6, color = "grey45") +
  geom_line(linewidth = 0.9, color = FARBE_HELLFELD) +
  scale_x_continuous(breaks = seq(1987, 2025, by = 4)) +
  scale_y_continuous(labels = dez_achse, limits = c(5000, 9200),
                     breaks = seq(5500, 9000, by = 500)) +
  labs(
    title = "Häufigkeitszahl (Fälle je 100.000 Einwohner)",
    subtitle = "HZ-Basis: bis 2012 alte Basis, 2013\u20132023 Zensus 2011, ab 2024 Zensus 2022 (punktiert).",
    x = "Berichtsjahr", y = "HZ je 100.000 Einwohner",
    caption = "Quelle: BKA PKS, T01-Zeitreihe 'Fälle ab 1987', Stand V1.1 (08.04.2026)."
  ) +
  THEME

ggsave(file.path(OUT_DIR, "fig01_gesamtkriminalitaet_1987-2025.png"),
       p_ges_faelle, width = 9, height = 5.2, dpi = 150)
ggsave(file.path(OUT_DIR, "fig01b_hz_1987-2025.png"),
       p_ges_hz, width = 9, height = 5.2, dpi = 150)

# ============================================================
# Figur 2: Diebstahlsdelikte indexiert (2002 = 100)
# ============================================================
idx <- reihen %>%
  filter(.data$jahr >= 2002,
         .data$schluessel %in% c("****00", "3***00", "4***00", "435*00", "436*00")) %>%
  group_by(.data$schluessel) %>%
  mutate(basis = .data$faelle[.data$jahr == 2002],
         index = .data$faelle / .data$basis * 100) %>%
  ungroup()

p_index <- ggplot(idx, aes(x = .data$jahr, y = .data$index, color = .data$delikt)) +
  geom_vline(xintercept = 2011, color = "grey70", linetype = "dashed") +
  annotate("text", x = 2011, y = 185, label = "Katalogverkleinerung\nDiebstahl 2011",
           hjust = 1.05, vjust = 1, size = 2.6, color = "grey45") +
  geom_hline(yintercept = 100, color = "grey85") +
  geom_line(linewidth = 0.85) +
  scale_x_continuous(breaks = seq(2002, 2025, by = 2)) +
  scale_y_continuous(limits = c(0, 200), breaks = seq(0, 200, by = 20)) +
  scale_color_manual(values = c(
    "Diebstahl insgesamt" = FARBE_HELLFELD,
    "Einfacher Diebstahl" = "#9ecae1",
    "Schwerer Diebstahl" = FARBE_ZWEIT,
    "Wohnungseinbruchdiebstahl" = FARBE_FURCHT,
    "Tageswohnungseinbruch (darunter)" = "#fc9272"
  )) +
  guides(colour = guide_legend(nrow = 2)) +
  labs(
    title = "Entwicklung der Diebstahlsdelikte, indexiert (2002 = 100)",
    subtitle = "Erfasste Fälle im Jahresvergleich; 2002 = 100. Wohnungseinbruch: Anstieg bis 2015, danach starker Rückgang.",
    x = "Berichtsjahr", y = "Index (2002 = 100)",
    color = NULL,
    caption = "Quelle: BKA PKS, T01-Zeitreihe. Katalogverkleinerung 2011 betrifft v. a. einfachen Diebstahl \u2013 Indexsprung 2010\u21922011 teils artefaktisch."
  ) +
  THEME

ggsave(file.path(OUT_DIR, "fig02_diebstahlsdelikte_index_2002-2025.png"),
       p_index, width = 9.5, height = 5.8, dpi = 150)

# ============================================================
# Figur 3: Wohnungseinbruch \u2013 Hellfeld vs. Furcht (Kernstück)
# ============================================================
wed <- reihen %>% filter(.data$schluessel == "435*00", .data$jahr >= 2002)

p_wed_hz <- ggplot(wed, aes(x = .data$jahr, y = .data$hz)) +
  geom_line(linewidth = 1, color = FARBE_HELLFELD) +
  geom_point(data = wed %>% filter(.data$jahr %in% c(2002, 2015, 2020, 2025)),
             size = 2, color = FARBE_HELLFELD) +
  geom_text(data = wed %>% filter(.data$jahr %in% c(2002, 2015, 2020, 2025)),
            aes(label = dez1(.data$hz)), vjust = -0.9, size = 3, color = FARBE_HELLFELD) +
  scale_x_continuous(breaks = seq(2002, 2025, by = 2), limits = c(2002, 2026)) +
  scale_y_continuous(labels = dez_achse, limits = c(0, 230),
                     breaks = seq(0, 200, by = 50), expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = "Wohnungseinbruchdiebstahl: registrierte Fälle vs. Einbruch-Furcht",
    subtitle = "Oben: PKS-Häufigkeitszahl (Hellfeld). Unten: Anteil 'ziemlich/sehr beunruhigt' (Dunkelfeld, DVS/SKiD).",
    x = NULL, y = "HZ je 100.000 Einwohner"
  ) +
  THEME +
  theme(axis.text.x = element_blank())

p_wed_furcht <- ggplot(FURCHT_WED, aes(x = .data$jahr, y = .data$prozent)) +
  annotate("rect", xmin = 2017, xmax = 2020, ymin = -Inf, ymax = Inf,
           fill = "grey92", alpha = 0.6) +
  annotate("text", x = 2018.5, y = 38, label = "Instrumenten-\nwechsel\nDVS \u2192 SKiD",
           hjust = 0.5, vjust = 1, size = 2.4, color = "grey45") +
  geom_line(data = FURCHT_WED %>% filter(.data$instrument == "DVS"),
            linewidth = 0.9, color = FARBE_FURCHT) +
  geom_line(data = FURCHT_WED %>% filter(.data$instrument == "SKiD"),
            linewidth = 0.9, color = FARBE_FURCHT) +
  geom_point(aes(shape = .data$instrument), size = 3, color = FARBE_FURCHT) +
  geom_text(aes(label = paste0(dez1(.data$prozent), " %")),
            vjust = -1, size = 3, color = FARBE_FURCHT) +
  geom_text(aes(label = .data$n), vjust = 2.8, size = 2.4, color = "grey40") +
  scale_x_continuous(breaks = seq(2002, 2025, by = 2), limits = c(2002, 2026)) +
  scale_y_continuous(labels = function(x) paste0(dez1(x), " %"),
                     limits = c(0, 42), expand = expansion(mult = c(0, 0.05))) +
  scale_shape_manual(values = c(DVS = 17, SKiD = 16), name = NULL) +
  annotate("text", x = 2002.5, y = 41.2, label = "\u25B2 DVS   \u25CF SKiD",
           hjust = 0, size = 3, color = "grey30") +
  labs(
    x = "Erhebungsjahr", y = "Anteil beunruhigt (%)",
    caption = paste0(
      "Quellen: BKA PKS T01 (V1.1, 08.04.2026); DVS 2012/2017 (BKA, Abb. 23, n = 11.643 / 6.079); ",
      "SKiD 2020/2024 (BKA, Ergebnisberichte, n = 45.351 / 54.392).\n",
      "DVS \u2192 SKiD 2020: Instrumentenwechsel, Werte nicht nahtlos vergleichbar. ",
      "2012\u21922017-Anstieg signifikant, 2020\u21922024-Veränderung nicht signifikant."
    )
  ) +
  THEME +
  theme(legend.position = "none")

ggsave(file.path(OUT_DIR, "fig03_wed_diskrepanz.png"),
       p_wed_hz / p_wed_furcht,
       width = 9.5, height = 8, dpi = 150)

# ============================================================
# Figur 4: Diebstahl \u2013 Hellfeld vs. Furcht
# ============================================================
dieb <- reihen %>% filter(.data$schluessel == "****00", .data$jahr >= 2002)

p_dieb_hz <- ggplot(dieb, aes(x = .data$jahr, y = .data$hz)) +
  geom_vline(xintercept = 2011, color = "grey70", linetype = "dashed") +
  geom_line(linewidth = 1, color = FARBE_HELLFELD) +
  geom_point(data = dieb %>% filter(.data$jahr %in% c(2002, 2015, 2020, 2025)),
             size = 2, color = FARBE_HELLFELD) +
  # Alle 4 Eckjahre beschriften; Position je nach freiem Raum.
  # Weisse Box (geom_label) verhindert sichtbare Schnitte mit der Kurve.
  geom_label(data = dieb %>% filter(.data$jahr == 2002),
             aes(label = dez1(.data$hz)), hjust = 0, nudge_x = 0.2,
             vjust = -0.6, size = 3, color = FARBE_HELLFELD,
             fill = "white", linewidth = 0,
             label.padding = unit(0.15, "lines")) +
  geom_label(data = dieb %>% filter(.data$jahr %in% c(2015, 2020)),
             aes(label = dez1(.data$hz)), hjust = 0.5,
             vjust = -0.6, size = 3, color = FARBE_HELLFELD,
             fill = "white", linewidth = 0,
             label.padding = unit(0.15, "lines")) +
  geom_label(data = dieb %>% filter(.data$jahr == 2025),
             aes(label = dez1(.data$hz)), hjust = 1, nudge_x = -0.2,
             vjust = 1.6, size = 3, color = FARBE_HELLFELD,
             fill = "white", linewidth = 0,
             label.padding = unit(0.15, "lines")) +
  scale_x_continuous(breaks = seq(2002, 2025, by = 2), limits = c(2002, 2026)) +
  scale_y_continuous(labels = dez_achse, limits = c(0, 4000),
                     breaks = seq(0, 4000, by = 500),
                     expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = "Diebstahl insgesamt: registrierte Fälle vs. Diebstahl-Furcht",
    subtitle = "Oben: PKS-HZ (Hellfeld; Katalogbruch 2011 gestrichelt). Unten: Furcht \u2013 nur SKiD 2020/2024 (DVS ohne Diebstahl-Item).",
    x = NULL, y = "HZ je 100.000 Einwohner"
  ) +
  THEME +
  theme(axis.text.x = element_blank())

p_dieb_furcht <- ggplot(FURCHT_DIEBSTAHL, aes(x = .data$jahr, y = .data$prozent)) +
  geom_line(linewidth = 0.9, color = FARBE_FURCHT) +
  geom_point(size = 3, color = FARBE_FURCHT) +
  geom_label(aes(label = paste0(dez1(.data$prozent), " %")),
             vjust = -0.6, size = 3, color = FARBE_FURCHT,
             fill = "white", linewidth = 0,
             label.padding = unit(0.15, "lines")) +
  geom_label(aes(label = .data$n), vjust = 2.4, size = 2.4, color = "grey40",
             fill = "white", linewidth = 0,
             label.padding = unit(0.15, "lines")) +
  scale_x_continuous(breaks = seq(2002, 2025, by = 2), limits = c(2002, 2026)) +
  scale_y_continuous(labels = function(x) paste0(dez1(x), " %"),
                     limits = c(0, 42), breaks = seq(0, 40, by = 5),
                     expand = expansion(mult = c(0, 0.05))) +
  labs(
    x = "Erhebungsjahr", y = "Anteil beunruhigt (%)",
    caption = "Quellen: BKA PKS T01 (V1.1); SKiD 2020/2024 (BKA, Abb. 26). Anstieg 2020\u21922024 (+5,4 PP) signifikant."
  ) +
  THEME

ggsave(file.path(OUT_DIR, "fig04_diebstahl_diskrepanz.png"),
       p_dieb_hz / p_dieb_furcht,
       width = 9.5, height = 8, dpi = 150)

cat("\nCharts geschrieben nach:", OUT_DIR, "\n")
cat("fig01_gesamtkriminalitaet_1987-2025.png\n")
cat("fig01b_hz_1987-2025.png\n")
cat("fig02_diebstahlsdelikte_index_2002-2025.png\n")
cat("fig03_wed_diskrepanz.png\n")
cat("fig04_diebstahl_diskrepanz.png\n")

# ============================================================
# Zusammenfassung der Kernzahlen
# ============================================================
cat("\n=== Kernzahlen (gemessen aus T01, V1.1) ===\n")
kz <- function(sch, j) {
  r <- t01 %>% filter(.data$schluessel == sch, .data$jahr == j)
  paste0(dez(r$faelle), " Fälle (HZ ", dez(r$hz), ")")
}
cat("Gesamt 1993 (Höchststand):", kz("------", 1993), "\n")
cat("Gesamt 2002:", kz("------", 2002), "\n")
cat("Gesamt 2015:", kz("------", 2015), "\n")
cat("Gesamt 2025:", kz("------", 2025), "\n")
cat("WED 2002:", kz("435*00", 2002), "\n")
cat("WED 2015 (Hochpunkt):", kz("435*00", 2015), "\n")
cat("WED 2025:", kz("435*00", 2025), "\n")
cat("Diebstahl 2002:", kz("****00", 2002), "\n")
cat("Diebstahl 2025:", kz("****00", 2025), "\n")

cat("\nsessionInfo():\n")
print(sessionInfo())
