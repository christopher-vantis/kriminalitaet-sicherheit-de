#!/usr/bin/env Rscript
# 22_mediation_lavaan.R — Mediation als Strukturgleichungsmodell
# =============================================================
# Der saubere Weg für indirekte Effekte: Alle Gleichungen werden GLEICHZEITIG
# geschätzt, und lavaan liefert den Standardfehler des Produkts a·b über die
# Delta-Methode — unter Berücksichtigung der Kovarianz der beiden Pfade.
#
# Eingabe:  output/analyse_datensatz.csv (vorbereitet von Skript 21)
# Ausgabe:  output/mediation_lavaan.csv
#
# Modell je Pfad:
#   mediator ~ a * X + Kontrollen
#   unsicher ~ b * mediator + cp * X + Kontrollen
#   indirekt := a * b        (Delta-Methode)
#   total    := cp + a * b
library(lavaan)

setwd("/home/c-vantis/jd/40_projects/47_kriminalitaetsdiskrepanz_de")
d <- read.csv("output/analyse_datensatz.csv")
cat(sprintf("Datensatz: %d Faelle, %d Spalten\n\n", nrow(d), ncol(d)))

kontrollen <- c("geschlecht_f", "agea_c_z", "eisced_c_z", "hinc_z", "hincfel_c",
                "mh", "stadt_land_num_z", "health_c_z")

pfade <- list(
  list(x = "diskriminiert", m = "ppltrst_c_z", name = "Diskriminierung -> Sozialvertrauen -> Furcht"),
  list(x = "eisced_c_z",    m = "ppltrst_c_z", name = "Bildung -> Sozialvertrauen -> Furcht"),
  list(x = "viktim",        m = "trstlgl_c_z", name = "Viktimisierung -> Vertrauen Justiz -> Furcht"),
  list(x = "imwbcnt_c_z",   m = "ppltrst_c_z", name = "Zuwanderungseinstellung -> Sozialvertrauen -> Furcht")
)

ergebnis <- data.frame()

for (p in pfade) {
  k <- setdiff(kontrollen, p$x)
  modell <- paste0(
    p$m, " ~ a*", p$x, " + ", paste(k, collapse = " + "), "\n",
    "unsicher ~ b*", p$m, " + cp*", p$x, " + ", paste(k, collapse = " + "), "\n",
    "indirekt := a*b\n",
    "total := cp + a*b\n"
  )
  # se = "standard" ist in lavaan die Delta-Methode; fuer definierte Parameter
  # (:=) liefert sie den Standardfehler des Produkts a*b unter Beruecksichtigung
  # der Kovarianz der beiden Pfade.
  fit <- sem(modell, data = d, se = "standard", missing = "listwise")
  pe <- parameterEstimates(fit)
  zeile <- pe[pe$label %in% c("a", "b", "cp", "indirekt", "total"), ]
  for (i in seq_len(nrow(zeile))) {
    ergebnis <- rbind(ergebnis, data.frame(
      pfad = p$name, parameter = zeile$label[i],
      schaetzer = round(zeile$est[i], 5),
      se = round(zeile$se[i], 5),
      z = round(zeile$z[i], 3),
      p_wert = signif(zeile$pvalue[i], 4),
      ki_lo = round(zeile$ci.lower[i], 5),
      ki_hi = round(zeile$ci.upper[i], 5),
      n = nrow(d)))
  }
  cat(sprintf("%-52s indirekt = %+.5f [%+.5f, %+.5f]  p = %.4f\n",
              p$name,
              pe$est[pe$label == "indirekt"],
              pe$ci.lower[pe$label == "indirekt"],
              pe$ci.upper[pe$label == "indirekt"],
              pe$pvalue[pe$label == "indirekt"]))
}

write.csv2(ergebnis, "output/mediation_lavaan.csv", row.names = FALSE)
cat("\n-> output/mediation_lavaan.csv\n")
cat("\nHinweis: se = 'standard' schaetzt den Standardfehler des Produkts a*b ueber die\n")
cat("Delta-Methode unter Beruecksichtigung der Kovarianz beider Pfade. Das ist der\n")
cat("Standardweg in Strukturgleichungsmodellen und braucht keinen Bootstrap.\n")
