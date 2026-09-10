#!/usr/bin/env Rscript
# ============================================================
# 02_deliktsgruppen_aufklaerung_ess.R
# Projekt: 47_kriminalitaetsdiskrepanz_de
# Ergänzende Übersichten:
#  (A) PKS-Hauptdeliktsgruppen 2002-2025 (T01) + Aufklärungsquoten 2025 (T12)
#  (B) ESS-DE 2002-2023: Sicherheitsgefühl (aesfdrk), Haushalts-Viktimisierung
#      (crmvct) als Zeitreihe + Aufschlüsselung nach Migrationshintergrund,
#      Bildung (eisced) und Haushaltseinkommen (hinctnta).
#
# Datenquellen:
#  - BKA PKS T01-ZR (bund/2025/T01-ZR-Bund-Fälle_xls.xlsx, V1.1)
#  - BKA PKS T12 aufgeklärte Fälle 2025 (bund/2025/BU-F-06-T12-aufgeklaert_xls.xlsx)
#  - ESS-Rohdaten ESS1-ESS11 (CSV, Data Portal): liegen im 43er-Projekt
#    ~/jd/40_projects/43_human_values_project/data/raw/ess/ (vollständige
#    Surveys inkl. Core-Variablen; Deutschland fehlt nur in Runde 10).
#    Quelle 47er-Bestand data/raw/ess/ ist leer (manuelle Beschaffung geplant) —
#    deshalb Querverweis auf 43er-Rohdaten, kein Duplikat.
#
# Ausgabe: output/ (PNGs + CSV)
# ============================================================

suppressMessages({
  library(readxl)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(patchwork)
  library(readr)
  library(stringr)
})

# --- Pfade ---------------------------------------------------
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
script_dir <- if (length(file_arg) > 0) dirname(normalizePath(sub("^--file=", "", file_arg[1]))) else getwd()
ROOT <- normalizePath(file.path(script_dir, ".."))
OUT_DIR <- file.path(ROOT, "output")
dir.create(OUT_DIR, showWarnings = FALSE)
RAW <- file.path(ROOT, "data/raw/pks/bund/2025")
ESS_DIR <- "/home/c-vantis/jd/40_projects/43_human_values_project/data/raw/ess"

# --- Stil / Helfer -------------------------------------------
THEME <- theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 13),
    plot.subtitle = element_text(color = "grey35", size = 10),
    plot.caption = element_text(color = "grey50", size = 8, hjust = 0),
    panel.grid.minor = element_blank(),
    legend.position = "bottom"
  )
dez1 <- function(x) formatC(x, format = "f", digits = 1,
                            big.mark = ".", decimal.mark = ",")
pct1 <- function(x) paste0(dez1(x), " %")

# ============================================================
# (A) PKS Hauptgruppen
# ============================================================
t01 <- read_excel(file.path(RAW, "T01-ZR-Bund-Fälle_xls.xlsx"),
                  skip = 15, col_names = FALSE)[, 1:5]
names(t01) <- c("schluessel", "straftat", "jahr", "faelle", "hz")
t01 <- t01 %>%
  mutate(jahr = as.integer(.data$jahr), faelle = as.numeric(.data$faelle),
         hz = as.numeric(.data$hz)) %>%
  filter(!is.na(.data$jahr))

# Hauptgruppen (8 Gruppen; Diebstahl-Gruppen 3/4 als Summenschlüssel ****00)
HAUPTGRUPPEN <- c(
  "000000" = "Gegen das Leben",
  "100000" = "Sexuelle Selbstbestimmung",
  "200000" = "Rohheitsdelikte & Freiheit",
  "****00" = "Diebstahl (gesamt)",
  "500000" = "Vermögens- & Fälschungsdelikte",
  "600000" = "Sonstige StGB",
  "700000" = "Nebengesetze"
)

hg <- t01 %>%
  filter(.data$schluessel %in% names(HAUPTGRUPPEN), .data$jahr >= 2002) %>%
  mutate(gruppe = factor(HAUPTGRUPPEN[.data$schluessel],
                         levels = unname(HAUPTGRUPPEN)))

# Vollständigkeit prüfen: 2002-2025 = 24 Jahre je Gruppe
voll <- hg %>% count(.data$gruppe)
stopifnot(all(voll$n == 24))
cat("Hauptgruppen 2002-2025 vollständig (24 Jahre x 7 Gruppen).\n")

# Export
hg %>% select(gruppe, schluessel, jahr, faelle, hz) %>%
  arrange(gruppe, jahr) %>%
  write_csv(file.path(OUT_DIR, "pks_hauptgruppen_2002-2025.csv"))

# fig05: HZ je Hauptgruppe, kleine Multiples mit freien Skalen
fig05 <- ggplot(hg, aes(x = .data$jahr, y = .data$hz)) +
  geom_line(linewidth = 0.8, color = "#1f4e79") +
  facet_wrap(~ .data$gruppe, scales = "free_y", ncol = 2) +
  scale_x_continuous(breaks = seq(2002, 2025, by = 4)) +
  scale_y_continuous(labels = function(x) {
    ifelse(x == round(x),
           formatC(x, format = "d", big.mark = ".", decimal.mark = ","),
           formatC(x, format = "f", digits = 1, big.mark = ".", decimal.mark = ","))
  }) +
  labs(
    title = "Registrierte Kriminalität nach Deliktshauptgruppen (PKS-Hellfeld)",
    subtitle = str_wrap("Häufigkeitszahl (Fälle je 100.000 Einwohner), 2002\u20132025. Freie y-Skalen je Gruppe \u2013 Niveaus nicht vergleichbar, nur Verläufe.", 90),
    x = "Berichtsjahr", y = "HZ je 100.000 Einwohner",
    caption = str_wrap(paste0(
      "Quelle: BKA PKS T01-ZR (V1.1, 08.04.2026). ",
      "Achtung Zählbereichsbrüche: 2011 Diebstahlskatalog; 2014 Cybercrime; 2016 Betrugskatalog; ",
      "2017/2022 Sexualstrafrecht; 2021 Bedrohung \u00a7241; 2024/25 Cannabis."), 110)
  ) +
  THEME

ggsave(file.path(OUT_DIR, "fig05_hauptgruppen_hz_2002-2025.png"),
       fig05, width = 10, height = 10, dpi = 150)

# --- Aufklärungsquoten 2025 (T12) ----------------------------
t12 <- read_excel(file.path(RAW, "BU-F-06-T12-aufgeklaert_xls.xlsx"),
                  skip = 8, col_names = FALSE)[, 1:3]
names(t12) <- c("schluessel", "straftat", "aufgeklaert")
t12 <- t12 %>% mutate(aufgeklaert = as.numeric(.data$aufgeklaert))

aq <- t01 %>%
  filter(.data$jahr == 2025) %>%
  inner_join(t12, by = "schluessel") %>%
  mutate(aq = .data$aufgeklaert / .data$faelle * 100) %>%
  filter(.data$schluessel %in% c("------", names(HAUPTGRUPPEN), "435*00", "210000", "222000"))

# 210000 = Raub insgesamt? Label prüfen; 222000 = gefährliche KV prüfen
lab <- function(s) unique(t01$straftat[t01$schluessel == s & t01$jahr == 2025])
for (s in c("435*00", "210000", "222000", "020000")) cat(s, "->", lab(s), "\n")

AQ_LABELS <- c(
  "------" = "Alle Delikte",
  "000000" = "Gegen das Leben", "100000" = "Sexuelle Selbstbestimmung",
  "200000" = "Rohheitsdelikte & Freiheit", "****00" = "Diebstahl (gesamt)",
  "500000" = "Vermögens- & Fälschungsdelikte", "600000" = "Sonstige StGB",
  "700000" = "Nebengesetze", "435*00" = "Wohnungseinbruch (WED)",
  "222000" = "Gefährliche Körperverletzung", "210000" = "Raub"
)
aq <- aq %>% filter(.data$schluessel %in% names(AQ_LABELS)) %>%
  mutate(gruppe = factor(AQ_LABELS[.data$schluessel],
                         levels = AQ_LABELS[names(AQ_LABELS) %in% .data$schluessel]))

aq_tabelle <- aq %>%
  select(gruppe, schluessel, faelle, aufgeklaert, aq) %>%
  arrange(desc(.data$aq))
print(as.data.frame(aq_tabelle), right = FALSE)
write_csv(aq_tabelle, file.path(OUT_DIR, "pks_aufklaerungsquoten_2025.csv"))

# WED in T12: Achtung 435*00-Zeile existiert? prüfen
cat("\nWED AQ 2025:\n")
wed_aq <- aq %>% filter(.data$schluessel == "435*00")
if (nrow(wed_aq) > 0) {
  cat(sprintf("  erfasst %s, aufgeklärt %s -> AQ %.1f %%\n",
              format(wed_aq$faelle, big.mark = "."),
              format(wed_aq$aufgeklaert, big.mark = "."), wed_aq$aq))
}

fig06 <- ggplot(aq, aes(x = reorder(.data$gruppe, .data$aq),
                        y = .data$aq)) +
  geom_col(fill = "#1f4e79", width = 0.7) +
  geom_text(aes(label = pct1(.data$aq)), hjust = -0.1, size = 3) +
  coord_flip() +
  scale_y_continuous(labels = function(x) paste0(dez1(x), " %"),
                     limits = c(0, 100), expand = expansion(mult = c(0, 0.08))) +
  labs(
    title = "Aufklärungsquoten 2025 nach Deliktsgruppen",
    subtitle = str_wrap("Anteil der Fälle mit ermitteltem Tatverdächtigen (T12 geteilt durch T01). Aufklärung heißt nur: ein TV wurde ermittelt \u2013 nicht: verurteilt.", 95),
    x = NULL, y = "Aufklärungsquote (%)",
    caption = "Quelle: BKA PKS 2025 (T01 V1.1, T12 V1.0)."
  ) +
  THEME

ggsave(file.path(OUT_DIR, "fig06_aufklaerungsquoten_2025.png"),
       fig06, width = 8.5, height = 5.5, dpi = 150)

# ============================================================
# (B) ESS-DE
# ============================================================
# Codierung: aesfdrk 1=very safe ... 4=very unsafe; 8=weiss nicht.
# Unsicher = 3 oder 4. crmvct 1 = Haushalt in letzten 5 Jahren Opfer von
# Einbruch/Diebstahl/Überfall. Gewichtung pspwght (post-stratifiziert,
# empfohlen für Deskription). Migrationshintergrund (MZ-ähnlich):
# selbst im Ausland geboren ODER (Vater ODER Mutter im Ausland geboren).
ESS_RUNDEN <- tibble(
  essround = 1:11,
  jahr     = c(2002, 2004, 2006, 2008, 2010, 2012, 2014, 2016, 2018, 2020, 2023)
)
# Deutschland hat an Runde 10 (2020-22) nicht teilgenommen.

lese_ess_de <- function(rnd) {
  f <- list.files(file.path(ESS_DIR, sprintf("ESS%d", rnd)), pattern = "\\.csv$",
                  full.names = TRUE)
  stopifnot(length(f) == 1)
  # ESS-CSV: breites Format, cntry ist Text, alle Zielvariablen numerisch.
  # Nur benötigte Spalten laden (Dateien haben 500-700 Spalten).
  d <- read_csv(f, progress = FALSE,
                col_select = any_of(c("cntry", "pspwght", "aesfdrk", "crmvct",
                                      "brncntr", "facntr", "mocntr", "eisced",
                                      "hinctnta")),
                col_types = cols(cntry = col_character(),
                                 .default = col_double()))
  d <- d %>%
    filter(.data$cntry == "DE") %>%
    mutate(essround = rnd)
  d
}

ess_all <- bind_rows(lapply(1:11, function(r) {
  cat("Lese ESS Runde", r, "...\n")
  tryCatch(lese_ess_de(r), error = function(e) {
    cat("  Runde", r, "fehlt:", conditionMessage(e), "\n"); NULL
  })
}))

# --- Datenaufbereitung ---------------------------------------
ess <- ess_all %>%
  mutate(
    unsicher = ifelse(.data$aesfdrk %in% c(3, 4), 1,
                      ifelse(.data$aesfdrk %in% c(1, 2), 0, NA_real_)),
    viktim  = ifelse(.data$crmvct == 1, 1,
                     ifelse(.data$crmvct == 2, 0, NA_real_)),
    # Migrationshintergrund: Fehlcodes (7,8) -> NA nur für Eltern, wenn Person
    # im Inland geboren UND Eltern-Angabe fehlt -> konservativ "kein MH".
    mh = case_when(
      .data$brncntr == 2 ~ 1,
      .data$brncntr == 1 & (.data$facntr == 2 | .data$mocntr == 2) ~ 1,
      .data$brncntr == 1 ~ 0,
      TRUE ~ NA_real_
    ),
    tertiaer = ifelse(.data$eisced %in% 5:7, 1,
                      ifelse(.data$eisced %in% 1:4, 0, NA_real_)),
    eink_ok = ifelse(.data$hinctnta %in% 1:10, .data$hinctnta, NA_real_)
  ) %>%
  left_join(ESS_RUNDEN, by = "essround")

anteil <- function(d, var, gew = "pspwght") {
  d <- d %>% filter(!is.na(.data[[var]]), !is.na(.data[[gew]]))
  n <- nrow(d)
  p <- sum(d[[var]] * d[[gew]]) / sum(d[[gew]])
  # KI-Näherung unter Vernachlässigung des Designeffekts
  se <- sqrt(p * (1 - p) / n)
  tibble(anteil = p * 100, n = n, ki_lo = (p - 1.96 * se) * 100,
         ki_hi = (p + 1.96 * se) * 100)
}

# Zeitreihe Sicherheitsgefühl
ess_unsicher <- ess %>%
  filter(!is.na(.data$unsicher)) %>%
  group_by(.data$jahr) %>%
  group_modify(~ anteil(.x, "unsicher")) %>%
  ungroup()

cat("\n=== ESS-DE: Anteil 'unsicher/sehr unsicher' beim Alleingehen nach Dunkelheit ===\n")
print(as.data.frame(ess_unsicher), right = FALSE)

# Zeitreihe Haushalts-Viktimisierung (5 Jahre)
ess_viktim <- ess %>%
  filter(!is.na(.data$viktim)) %>%
  group_by(.data$jahr) %>%
  group_modify(~ anteil(.x, "viktim")) %>%
  ungroup()

cat("\n=== ESS-DE: Haushalts-Viktimisierung (Einbruch/Diebstahl/Überfall, 5 Jahre) ===\n")
print(as.data.frame(ess_viktim), right = FALSE)

write_csv(ess_unsicher, file.path(OUT_DIR, "ess_de_unsicher_zeitreihe.csv"))
write_csv(ess_viktim, file.path(OUT_DIR, "ess_de_viktimisierung_zeitreihe.csv"))

# --- fig07: Sicherheitsgefühl + Viktimisierung ---------------
farbe_aes <- "#b22222"; farbe_crm <- "#1f4e79"

p_aes <- ggplot(ess_unsicher, aes(x = .data$jahr, y = .data$anteil)) +
  geom_ribbon(aes(ymin = .data$ki_lo, ymax = .data$ki_hi), alpha = 0.18, fill = farbe_aes) +
  geom_line(linewidth = 0.9, color = farbe_aes) +
  geom_point(size = 2.2, color = farbe_aes) +
  geom_label(aes(label = pct1(.data$anteil)), vjust = -0.4, size = 2.7,
             color = farbe_aes, fill = "white", linewidth = 0,
             label.padding = unit(0.12, "lines")) +
  geom_label(aes(label = paste0("n = ", format(.data$n, big.mark = "."))),
             vjust = 1.6, size = 2.2, color = "grey45",
             fill = "white", linewidth = 0,
             label.padding = unit(0.1, "lines")) +
  scale_x_continuous(breaks = ess_unsicher$jahr) +
  scale_y_continuous(labels = function(x) paste0(dez1(x), " %")) +
  labs(
    title = "ESS-DE: Unsicherheitsgefühl beim Alleingehen nach Einbruch der Dunkelheit",
    subtitle = str_wrap("Anteil 'unsicher' oder 'sehr unsicher' (aesfdrk 3/4), gewichtet (pspwght); Band = 95-%-KI (Näherung ohne Designeffekt). Lücke 2020: DE nicht in Runde 10.", 100),
    x = "Erhebungsjahr", y = "Anteil unsicher (%)",
    caption = "Quelle: European Social Survey R1-R11 (DE), eigene Berechnung."
  ) +
  THEME

p_crm <- ggplot(ess_viktim, aes(x = .data$jahr, y = .data$anteil)) +
  geom_ribbon(aes(ymin = .data$ki_lo, ymax = .data$ki_hi), alpha = 0.18, fill = farbe_crm) +
  geom_line(linewidth = 0.9, color = farbe_crm) +
  geom_point(size = 2.2, color = farbe_crm) +
  geom_label(aes(label = pct1(.data$anteil)), vjust = -0.4, size = 2.7,
             color = farbe_crm, fill = "white", linewidth = 0,
             label.padding = unit(0.12, "lines")) +
  scale_x_continuous(breaks = ess_viktim$jahr) +
  scale_y_continuous(labels = function(x) paste0(dez1(x), " %")) +
  labs(
    title = "ESS-DE: Haushalts-Viktimisierung (Einbruch, Diebstahl oder \u00dcberfall, letzte 5 Jahre)",
    subtitle = str_wrap("Anteil der Haushalte mit mindestens einem Vorfall (crmvct), gewichtet (pspwght).", 100),
    x = "Erhebungsjahr", y = "Anteil betroffen (%)",
    caption = "Quelle: European Social Survey R1-R11 (DE), eigene Berechnung."
  ) +
  THEME

ggsave(file.path(OUT_DIR, "fig07_ess_unsicherheit_zeitreihe.png"),
       p_aes / p_crm, width = 9.5, height = 8.5, dpi = 150)

# --- fig08: Subgruppen ----------------------------------------
subgruppen <- function(d, var, label_ja, label_nein) {
  d %>%
    filter(!is.na(.data[[var]]), !is.na(.data$unsicher)) %>%
    mutate(gruppe = factor(ifelse(.data[[var]] == 1, label_ja, label_nein),
                           levels = c(label_ja, label_nein))) %>%
    group_by(.data$jahr, .data$gruppe) %>%
    group_modify(~ anteil(.x, "unsicher")) %>%
    ungroup()
}

ess_mh   <- subgruppen(ess, "mh", "Migrationshintergrund", "Ohne Migrationshintergrund")
ess_bild <- subgruppen(ess, "tertiaer", "Tertiärbildung", "Keine Tertiärbildung")

# Einkommen in Terzilen innerhalb jeder Runde
ess_eink <- ess %>%
  filter(!is.na(.data$eink_ok), !is.na(.data$unsicher)) %>%
  group_by(.data$jahr) %>%
  mutate(terzil = cut(.data$eink_ok, quantile(.data$eink_ok, c(0, 1/3, 2/3, 1)),
                      include.lowest = TRUE, labels = c("Einkommen unten", "Einkommen Mitte", "Einkommen oben"))) %>%
  ungroup() %>%
  group_by(.data$jahr, .data$terzil) %>%
  group_modify(~ anteil(.x, "unsicher")) %>%
  ungroup() %>%
  rename(gruppe = .data$terzil)

plot_sub <- function(d, titel) {
  ggplot(d, aes(x = .data$jahr, y = .data$anteil, color = .data$gruppe)) +
    geom_line(linewidth = 0.85) +
    geom_point(size = 1.8) +
    scale_x_continuous(breaks = ess_unsicher$jahr) +
    scale_y_continuous(labels = function(x) paste0(dez1(x), " %")) +
    labs(title = titel, x = "Erhebungsjahr", y = "Anteil unsicher (%)", color = NULL) +
    THEME
}

fig08 <- (plot_sub(ess_mh, "Nach Migrationshintergrund (selbst/Eltern im Ausland geboren)") +
            scale_color_manual(values = c("Migrationshintergrund" = "#b22222",
                                          "Ohne Migrationshintergrund" = "#1f4e79"))) /
  (plot_sub(ess_bild, "Nach Bildung (ISCED)") +
     scale_color_manual(values = c("Tertiärbildung" = "#1f4e79",
                                   "Keine Tertiärbildung" = "#b22222"))) /
  (plot_sub(ess_eink, "Nach Haushalts-Nettoeinkommen (Terzile je Runde; ab 2008)") +
     scale_color_manual(values = c("Einkommen unten" = "#b22222",
                                   "Einkommen Mitte" = "#6baed6",
                                   "Einkommen oben" = "#1f4e79")))

ggsave(file.path(OUT_DIR, "fig08_ess_unsicherheit_subgruppen.png"),
       fig08 + plot_annotation(
         title = "Unsicherheitsgefühl nach sozialen Gruppen (ESS-DE)",
         caption = str_wrap("Quelle: European Social Survey R1-R11, eigene Berechnung, gewichtet (pspwght). n je Zelle 200-3.000; kleine Zellen in den 2010er-Jahren (n < 300) unzuverlässig.", 110)
       ),
       width = 9.5, height = 10.5, dpi = 150)

cat("\nExporte:\n")
cat("- pks_hauptgruppen_2002-2025.csv\n- pks_aufklaerungsquoten_2025.csv\n")
cat("- ess_de_unsicher_zeitreihe.csv\n- ess_de_viktimisierung_zeitreihe.csv\n")
cat("Charts: fig05_hauptgruppen_hz, fig06_aufklaerungsquoten_2025,",
    "fig07_ess_unsicherheit_zeitreihe, fig08_ess_unsicherheit_subgruppen\n")
