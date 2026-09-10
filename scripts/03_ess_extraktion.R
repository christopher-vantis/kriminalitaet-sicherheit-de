#!/usr/bin/env Rscript
# ============================================================
# 03_ess_extraktion.R
# Projekt: 47_kriminalitaetsdiskrepanz_de
# Zweck: Vollständige ESS-DE-Extraktion (Runden 1-11) für die
#        Angst-/Sicherheitsanalyse. Erzeugt eine Personenebene
#        (bereinigt) + Runden-Aggregate als CSV für das Dashboard.
#
# Quelle: ESS-Rohdaten (Data Portal), liegen im 43er-Projekt:
#   ~/jd/40_projects/43_human_values_project/data/raw/ess/ESS<r>/*.csv
#   Kodierungen gegen die mitgelieferten Codebooks (HTML) verifiziert:
#   aesfdrk 1=very safe..4=very unsafe (7/8/9 fehlend);
#   crmvct 1=ja/2=nein (7/8/9 fehlend); brncntr/facntr/mocntr 1=ja/2=nein;
#   eisced 1-7 (0,55,77,88,99 fehlend); hinctnta 1-10 Dezile (77/88/99 fehlend);
#   domicil 1=Grossstadt..5=Hof/Land; dscrgrp 1=ja/2=nein; nwspol Minuten
#   (7777/8888/9999 fehlend); trst*/stf* 0-10 (77/88/99 fehlend).
# Deutschland fehlt in Runde 10 (2020) -> 10 Erhebungswellen.
# ============================================================

suppressMessages({
  library(readr); library(dplyr); library(tidyr); library(stringr)
})

args <- commandArgs(trailingOnly = FALSE)
fa <- grep("^--file=", args, value = TRUE)
script_dir <- if (length(fa) > 0) dirname(normalizePath(sub("^--file=", "", fa[1]))) else getwd()
ROOT <- normalizePath(file.path(script_dir, ".."))
ESS_DIR <- "/home/c-vantis/jd/40_projects/43_human_values_project/data/raw/ess"
OUT <- file.path(ROOT, "dashboard/data")
dir.create(OUT, showWarnings = FALSE, recursive = TRUE)

RUNDEN <- tibble(essround = 1:11,
                 jahr = c(2002, 2004, 2006, 2008, 2010, 2012, 2014,
                          2016, 2018, 2020, 2023))

VARS <- c("cntry", "pspwght", "dweight", "anweight",
          # Kern
          "aesfdrk", "crmvct",
          # Soziodemografie
          "gndr", "agea", "eisced", "hinctnta", "brncntr", "facntr", "mocntr",
          "domicil", "uempla", "mnactic", "hhmmb", "chldhhe", "eduyrs",
          # Vertrauen / Einstellungen
          "ppltrst", "pplfair", "pplhlp", "trstplc", "trstprl", "trstlgl",
          "trstplt", "stfgov", "stfdem", "stflife", "stfeco", "happy",
          "lrscale", "imwbcnt", "imsmetn", "impcntr", "imdfetn", "gincdif",
          "freehms", "hincfel", "health", "rlgatnd", "pray", "dscrgrp",
          "nwspol", "netusoft", "sclmeet", "sclact", "inprdsc",
          "polintr", "vote", "clsprty", "region")

lese <- function(r) {
  f <- list.files(file.path(ESS_DIR, paste0("ESS", r)), pattern = "\\.csv$", full.names = TRUE)
  stopifnot(length(f) == 1)
  read_csv(f, progress = FALSE, show_col_types = FALSE,
           col_select = any_of(VARS),
           col_types = cols(cntry = col_character(), region = col_character(),
                            .default = col_double())) %>%
    filter(.data$cntry == "DE") %>%
    mutate(essround = r)
}
cat("Lese ESS-Runden 1-11 (DE)...\n")
ess_raw <- bind_rows(lapply(1:11, lese)) %>% left_join(RUNDEN, by = "essround")

# --- Fehlcodes -> NA -------------------------------------------------------
na_setzen <- function(x, fehl) ifelse(x %in% fehl, NA_real_, x)
num <- function(v) if (v %in% names(ess_raw)) ess_raw[[v]] else rep(NA_real_, nrow(ess_raw))

ess <- ess_raw %>%
  mutate(
    aesfdrk_c = na_setzen(num("aesfdrk"), c(7, 8, 9)),
    crmvct_c  = na_setzen(num("crmvct"),  c(7, 8, 9)),
    gndr_c    = na_setzen(num("gndr"),    c(7, 8, 9)),
    agea_c    = na_setzen(num("agea"),    c(999)),
    eisced_c  = na_setzen(num("eisced"),  c(0, 55, 77, 88, 99)),
    hinc    = na_setzen(num("hinctnta"), c(77, 88, 99)),
    brncntr_c = na_setzen(num("brncntr"), c(7, 8, 9)),
    facntr_c  = na_setzen(num("facntr"),  c(7, 8, 9)),
    mocntr_c  = na_setzen(num("mocntr"),  c(7, 8, 9)),
    domicil_c = na_setzen(num("domicil"), c(7, 8, 9)),
    dscrgrp_c = na_setzen(num("dscrgrp"), c(7, 8, 9)),
    ppltrst_c = na_setzen(num("ppltrst"), c(77, 88, 99)),
    trstplc_c = na_setzen(num("trstplc"), c(77, 88, 99)),
    trstprl_c = na_setzen(num("trstprl"), c(77, 88, 99)),
    trstlgl_c = na_setzen(num("trstlgl"), c(77, 88, 99)),
    trstplt_c = na_setzen(num("trstplt"), c(77, 88, 99)),
    stfgov_c  = na_setzen(num("stfgov"),  c(77, 88, 99)),
    stfdem_c  = na_setzen(num("stfdem"),  c(77, 88, 99)),
    stflife_c = na_setzen(num("stflife"), c(77, 88, 99)),
    happy_c   = na_setzen(num("happy"),   c(77, 88, 99)),
    lrscale_c = na_setzen(num("lrscale"), c(77, 88, 99)),
    imwbcnt_c = na_setzen(num("imwbcnt"), c(77, 88, 99)),
    imsmetn_c = na_setzen(num("imsmetn"), c(7, 8, 9)),
    impcntr_c = na_setzen(num("impcntr"), c(7, 8, 9)),
    hincfel_c = na_setzen(num("hincfel"), c(7, 8, 9)),
    health_c  = na_setzen(num("health"),  c(7, 8, 9)),
    nwspol_c  = na_setzen(num("nwspol"),  c(7777, 8888, 9999)),
    inprdsc_c = na_setzen(num("inprdsc"), c(77, 88, 99)),
    uempla_c  = na_setzen(num("uempla"),  c(7, 8, 9)),
    w = ifelse(!is.na(num("pspwght")) & num("pspwght") > 0, num("pspwght"), NA_real_)
  ) %>%
  mutate(
    unsicher  = ifelse(.data$aesfdrk_c %in% c(3, 4), 1,
                       ifelse(.data$aesfdrk_c %in% c(1, 2), 0, NA_real_)),
    viktim    = ifelse(.data$crmvct_c == 1, 1, ifelse(.data$crmvct_c == 2, 0, NA_real_)),
    mh        = case_when(
      .data$brncntr_c == 2 ~ 1,
      .data$brncntr_c == 1 & (.data$facntr_c == 2 | .data$mocntr_c == 2) ~ 1,
      .data$brncntr_c == 1 ~ 0,
      TRUE ~ NA_real_),
    tertiaer  = ifelse(.data$eisced_c %in% 5:7, 1,
                       ifelse(.data$eisced_c %in% 1:4, 0, NA_real_)),
    alter_gr  = cut(.data$agea_c, c(15, 29, 44, 59, 74, 120),
                    labels = c("16-29", "30-44", "45-59", "60-74", "75+")),
    stadt_land = factor(dplyr::recode(.data$domicil_c,
                                      `1` = "Grossstadt", `2` = "Vorort", `3` = "Kleinstadt",
                                      `4` = "Dorf", `5` = "Land"),
                        levels = c("Grossstadt", "Vorort", "Kleinstadt", "Dorf", "Land")),
    diskriminiert = ifelse(.data$dscrgrp_c == 1, 1,
                           ifelse(.data$dscrgrp_c == 2, 0, NA_real_)),
    geschlecht = factor(dplyr::recode(.data$gndr_c, `1` = "Mann", `2` = "Frau")),
    vertrauen_polizei_hoch = ifelse(.data$trstplc_c >= 7, 1,
                                    ifelse(.data$trstplc_c <= 5, 0, NA_real_)),
    news_min = .data$nwspol_c
  )

# --- Kontrolle: Fallzahlen je Runde ---------------------------------------
kontrolle <- ess %>% group_by(.data$essround, .data$jahr) %>%
  summarise(n_de = n(), n_aesfdrk = sum(!is.na(.data$unsicher)),
            n_viktim = sum(!is.na(.data$viktim)), n_mh = sum(!is.na(.data$mh)),
            .groups = "drop")
cat("\n=== Fallzahlen je Runde (DE) ===\n"); print(as.data.frame(kontrolle), right = FALSE)
stopifnot(nrow(kontrolle[!is.na(kontrolle$n_aesfdrk) & kontrolle$n_aesfdrk < 2000, ]) == 0)

# --- Speichern -------------------------------------------------------------
personen <- ess %>%
  select(essround, jahr, region, w, unsicher, viktim, aesfdrk_c, crmvct_c,
         geschlecht, agea_c, alter_gr, eisced_c, tertiaer, hinc, hincfel_c,
         mh, brncntr_c, stadt_land, diskriminiert, uempla_c, health_c,
         ppltrst_c, trstplc_c, trstprl_c, trstlgl_c, trstplt_c,
         stfgov_c, stfdem_c, stflife_c, happy_c, lrscale_c, imwbcnt_c,
         imsmetn_c, impcntr_c, news_min, vertrauen_polizei_hoch, clsprty, vote)
write_csv(personen, file.path(OUT, "ess_de_personen.csv"))

cat("\nPersonendatei:", nrow(personen), "Zeilen,",
    ncol(personen), "Spalten ->", file.path(OUT, "ess_de_personen.csv"), "\n")
cat("Runden mit DE-Daten:", paste(sort(unique(personen$essround)), collapse = ", "), "\n")
