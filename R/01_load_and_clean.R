# ==============================================================================
# Malaria Outbreak Predictor — Step 1: Load, Clean & Merge
# ==============================================================================
# Input:  data/raw/*.csv  (from 00_fetch_data.R)
# Output: data/processed/*.csv  (analysis-ready)
#
# Packages: tidyverse, lubridate
# Run:      Rscript R/01_load_and_clean.R
# ==============================================================================

library(tidyverse)
library(lubridate)

# ── Configuration ──────────────────────────────────────────────────────────────

RAW_DIR  <- file.path("data", "raw")
PROC_DIR <- file.path("data", "processed")
dir.create(PROC_DIR, showWarnings = FALSE, recursive = TRUE)

cat(strrep("=", 70), "\n")
cat("  Malaria Outbreak Predictor — Data Pipeline\n")
cat(strrep("=", 70), "\n\n")


# ── 1. Load World Bank Data ────────────────────────────────────────────────────

cat("[1/6] Loading World Bank data...\n")

wb_raw <- read_csv(
  file.path(RAW_DIR, "worldbank_malaria_indicators.csv"),
  col_types = cols(
    country   = col_character(),
    iso3      = col_character(),
    year      = col_integer(),
    indicator = col_character(),
    value     = col_double()
  ),
  show_col_types = FALSE
)

cat(sprintf("  %d rows, %d indicators\n", nrow(wb_raw), n_distinct(wb_raw$indicator)))

# Pivot Kenya data to wide format
wb_wide <- wb_raw %>%
  filter(iso3 == "KEN") %>%
  select(year, indicator, value) %>%
  pivot_wider(names_from = indicator, values_from = value) %>%
  arrange(year)

cat(sprintf("  Kenya wide: %d years x %d indicators\n", nrow(wb_wide), ncol(wb_wide) - 1))

# East Africa comparison
wb_ea <- wb_raw %>%
  filter(indicator == "malaria_incidence_per_1000", iso3 != "KEN") %>%
  select(country, year, malaria_incidence_per_1000 = value) %>%
  arrange(country, year)

cat(sprintf("  East Africa: %d rows, %d countries\n\n", nrow(wb_ea), n_distinct(wb_ea$country)))


# ── 2. Load WHO Malaria Data ───────────────────────────────────────────────────

cat("[2/6] Loading WHO malaria surveillance data...\n")

who_raw <- read_csv(
  file.path(RAW_DIR, "who_malaria_surveillance.csv"),
  col_types = cols(
    country    = col_character(),
    iso3       = col_character(),
    year       = col_integer(),
    indicator  = col_character(),
    value      = col_double(),
    low_ci     = col_double(),
    high_ci    = col_double(),
    value_type = col_character()
  ),
  show_col_types = FALSE
)

cat(sprintf("  %d rows, %d indicators\n", nrow(who_raw), n_distinct(who_raw$indicator)))

# Pivot WHO data to wide
who_wide <- who_raw %>%
  select(year, indicator, value, low_ci, high_ci) %>%
  pivot_wider(
    names_from  = indicator,
    values_from = c(value, low_ci, high_ci),
    names_glue  = "{indicator}_{.value}"
  ) %>%
  arrange(year)

cat(sprintf("  WHO wide: %d years\n\n", nrow(who_wide)))


# ── 3. Load NASA POWER Climate Data ───────────────────────────────────────────

cat("[3/6] Loading NASA POWER climate data...\n")

climate_raw <- read_csv(
  file.path(RAW_DIR, "kenya_climate_daily.csv"),
  col_types = cols(
    city              = col_character(),
    latitude          = col_double(),
    longitude         = col_double(),
    date              = col_integer(),
    temperature_c     = col_double(),
    precipitation_mm  = col_double(),
    humidity_pct      = col_double(),
    wind_speed_ms     = col_double(),
    solar_radiation_mj = col_double()
  ),
  show_col_types = FALSE
)

cat(sprintf("  %d daily records, %d cities\n", nrow(climate_raw), n_distinct(climate_raw$city)))

# Parse dates
climate_clean <- climate_raw %>%
  mutate(
    date_parsed = as.Date(as.character(date), format = "%Y%m%d"),
    year  = year(date_parsed),
    month = month(date_parsed)
  ) %>%
  filter(!is.na(date_parsed))

# Replace sentinel values
climate_clean <- climate_clean %>%
  mutate(across(
    c(temperature_c, precipitation_mm, humidity_pct, wind_speed_ms, solar_radiation_mj),
    ~ ifelse(. < -900, NA_real_, .)
  ))


# ── 4. Aggregate Climate to Monthly ───────────────────────────────────────────

cat("[4/6] Aggregating climate data...\n")

climate_monthly <- climate_clean %>%
  group_by(city, latitude, longitude, year, month) %>%
  summarise(
    temp_mean_c     = mean(temperature_c, na.rm = TRUE),
    temp_min_c      = min(temperature_c, na.rm = TRUE),
    temp_max_c      = max(temperature_c, na.rm = TRUE),
    temp_range_c    = temp_max_c - temp_min_c,
    precip_total_mm = sum(precipitation_mm, na.rm = TRUE),
    precip_days     = sum(precipitation_mm > 0.1, na.rm = TRUE),
    humidity_mean   = mean(humidity_pct, na.rm = TRUE),
    wind_mean_ms    = mean(wind_speed_ms, na.rm = TRUE),
    solar_mean_mj   = mean(solar_radiation_mj, na.rm = TRUE),
    n_days          = n(),
    .groups = "drop"
  )

cat(sprintf("  Monthly: %d rows\n", nrow(climate_monthly)))

# Kenya-wide annual averages
climate_annual <- climate_clean %>%
  group_by(year) %>%
  summarise(
    temp_mean_c     = mean(temperature_c, na.rm = TRUE),
    precip_total_mm = sum(precipitation_mm, na.rm = TRUE) / n_distinct(city),
    precip_days     = sum(precipitation_mm > 0.1, na.rm = TRUE) / n_distinct(city),
    humidity_mean   = mean(humidity_pct, na.rm = TRUE),
    wind_mean_ms    = mean(wind_speed_ms, na.rm = TRUE),
    solar_mean_mj   = mean(solar_radiation_mj, na.rm = TRUE),
    n_cities        = n_distinct(city),
    .groups = "drop"
  )

cat(sprintf("  Annual: %d years\n\n", nrow(climate_annual)))


# ── 5. Merge All Datasets ─────────────────────────────────────────────────────

cat("[5/6] Merging datasets...\n")

merged <- wb_wide %>%
  left_join(who_wide, by = "year", suffix = c("_wb", "_who")) %>%
  left_join(climate_annual, by = "year")

cat(sprintf("  Merged: %d rows x %d columns\n\n", nrow(merged), ncol(merged)))


# ── 6. Create ML Features & Save ──────────────────────────────────────────────

cat("[6/6] Creating ML features & saving...\n")

ml_features <- merged %>%
  arrange(year) %>%
  mutate(
    # Lagged malaria incidence
    incidence_lag1 = lag(malaria_incidence_per_1000, 1),
    incidence_lag2 = lag(malaria_incidence_per_1000, 2),

    # Lagged climate
    precip_lag1 = lag(precip_total_mm, 1),
    precip_lag2 = lag(precip_total_mm, 2),
    temp_lag1   = lag(temp_mean_c, 1),
    temp_lag2   = lag(temp_mean_c, 2),

    # Anomalies
    precip_anomaly = precip_total_mm - mean(precip_total_mm, na.rm = TRUE),
    temp_anomaly   = temp_mean_c - mean(temp_mean_c, na.rm = TRUE),

    # Rolling means (using R base)
    precip_roll3 = stats::filter(precip_total_mm, rep(1/3, 3), sides = 1) %>% as.numeric(),
    temp_roll3   = stats::filter(temp_mean_c, rep(1/3, 3), sides = 1) %>% as.numeric(),

    # Change metrics
    incidence_change    = malaria_incidence_per_1000 - lag(malaria_incidence_per_1000, 1),
    incidence_change_pct = (incidence_change / lag(malaria_incidence_per_1000, 1)) * 100
  )

# ── Save all processed files ──────────────────────────────────────────────────

write_csv(wb_wide,         file.path(PROC_DIR, "worldbank_kenya_annual.csv"))
write_csv(wb_ea,           file.path(PROC_DIR, "worldbank_east_africa.csv"))
write_csv(who_wide,        file.path(PROC_DIR, "who_malaria_annual.csv"))
write_csv(climate_monthly, file.path(PROC_DIR, "climate_monthly.csv"))
write_csv(climate_annual,  file.path(PROC_DIR, "climate_annual_kenya.csv"))
write_csv(merged,          file.path(PROC_DIR, "malaria_climate_merged.csv"))
write_csv(ml_features,     file.path(PROC_DIR, "malaria_ml_features.csv"))

cat("\n  Saved 7 processed files to data/processed/\n")


# ── Data Quality Report ────────────────────────────────────────────────────────

cat("\n", strrep("=", 70), "\n")
cat("  DATA QUALITY REPORT\n")
cat(strrep("=", 70), "\n\n")

missing_summary <- merged %>%
  summarise(across(everything(), ~ sum(is.na(.)))) %>%
  pivot_longer(everything(), names_to = "column", values_to = "n_missing") %>%
  filter(n_missing > 0) %>%
  arrange(desc(n_missing))

if (nrow(missing_summary) > 0) {
  print(missing_summary)
} else {
  cat("  No missing values!\n")
}

cat(sprintf("\n  Year range: %d - %d\n", min(merged$year), max(merged$year)))
cat(sprintf("  Merged: %d rows x %d columns\n", nrow(merged), ncol(merged)))

cat("\n  Key variable summaries:\n")
merged %>%
  select(malaria_incidence_per_1000, precip_total_mm, temp_mean_c, humidity_mean) %>%
  summary() %>%
  print()

cat("\n\nPipeline complete! Next: Rscript R/02_eda.R\n")
