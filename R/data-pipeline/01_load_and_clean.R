#!/usr/bin/env Rscript
# ==============================================================================
# Malaria Outbreak Predictor — Data Pipeline
# ==============================================================================
# Step 1: Load, clean, merge, and transform raw data into analysis-ready format
#
# Datasets loaded:
#   1. World Bank malaria + health + climate indicators (annual, Kenya)
#   2. WHO malaria surveillance estimates (annual, Kenya, with CI)
#   3. NASA POWER daily climate data (daily, 8 Kenyan cities, 2010-2024)
#
# Output:
#   - data/processed/malaria_annual.csv     (annual malaria + covariates)
#   - data/processed/climate_monthly.csv    (monthly climate aggregates by city)
#   - data/processed/climate_annual.csv     (annual climate averages for Kenya)
#   - data/processed/malaria_climate_merged.csv (final merged dataset)
# ==============================================================================

library(tidyverse)
library(lubridate)

# ── Configuration ──────────────────────────────────────────────────────────────

RAW_DIR    <- file.path("data", "raw")
PROC_DIR   <- file.path("data", "processed")
dir.create(PROC_DIR, showWarnings = FALSE, recursive = TRUE)

cat("=" %+% strrep("=", 69) %>% paste0("\n"))
cat("  Malaria Outbreak Predictor — Data Pipeline (R)\n")
cat(strrep("=", 70) %>% paste0("\n\n"))

# Helper: paste without separator
`%+%` <- paste0

# ── 1. Load World Bank Data ────────────────────────────────────────────────────

cat("1. Loading World Bank data...\n")

wb_raw <- read_csv(
  file.path(RAW_DIR, "worldbank_malaria_indicators.csv"),
  col_types = cols(
    country  = col_character(),
    iso3     = col_character(),
    year     = col_integer(),
    indicator = col_character(),
    value    = col_double()
  ),
  show_col_types = FALSE
)

cat(sprintf("   Loaded %d rows, %d indicators\n", nrow(wb_raw), n_distinct(wb_raw$indicator)))
cat(sprintf("   Indicators: %s\n", paste(unique(wb_raw$indicator), collapse = ", ")))
cat(sprintf("   Year range: %d - %d\n\n", min(wb_raw$year, na.rm = TRUE), max(wb_raw$year, na.rm = TRUE)))

# Pivot to wide format: one row per year
wb_wide <- wb_raw %>%
  filter(iso3 == "KEN") %>%
  select(year, indicator, value) %>%
  pivot_wider(names_from = indicator, values_from = value) %>%
  arrange(year)

cat("   Kenya World Bank indicators (wide format):\n")
print(head(wb_wide, 5))

# Also get East Africa comparison data
wb_ea <- wb_raw %>%
  filter(indicator == "malaria_incidence_per_1000") %>%
  filter(iso3 != "KEN") %>%
  select(country, year, malaria_incidence_per_1000 = value) %>%
  arrange(country, year)

cat(sprintf("\n   East Africa comparison: %d rows, %d countries\n\n",
            nrow(wb_ea), n_distinct(wb_ea$country)))


# ── 2. Load WHO Malaria Data ───────────────────────────────────────────────────

cat("2. Loading WHO malaria surveillance data...\n")

who_raw <- read_csv(
  file.path(RAW_DIR, "who_malaria_surveillance.csv"),
  col_types = cols(
    country   = col_character(),
    iso3      = col_character(),
    year      = col_integer(),
    indicator = col_character(),
    value     = col_double(),
    low_ci    = col_double(),
    high_ci   = col_double(),
    value_type = col_character()
  ),
  show_col_types = FALSE
)

cat(sprintf("   Loaded %d rows, %d indicators\n", nrow(who_raw), n_distinct(who_raw$indicator)))

# Pivot WHO data to wide
who_wide <- who_raw %>%
  select(year, indicator, value, low_ci, high_ci) %>%
  pivot_wider(
    names_from = indicator,
    values_from = c(value, low_ci, high_ci),
    names_glue = "{indicator}_{.value}"
  ) %>%
  arrange(year)

cat("   WHO indicators (wide format):\n")
print(head(who_wide, 5))
cat("\n")


# ── 3. Load NASA POWER Climate Data ───────────────────────────────────────────

cat("3. Loading NASA POWER climate data...\n")

climate_raw <- read_csv(
  file.path(RAW_DIR, "kenya_climate_daily.csv"),
  col_types = cols(
    city             = col_character(),
    latitude         = col_double(),
    longitude        = col_double(),
    date             = col_integer(),
    temperature_c    = col_double(),
    precipitation_mm = col_double(),
    humidity_pct     = col_double(),
    wind_speed_ms    = col_double(),
    solar_radiation_mj = col_double()
  ),
  show_col_types = FALSE
)

cat(sprintf("   Loaded %d daily records across %d cities\n",
            nrow(climate_raw), n_distinct(climate_raw$city)))

# Parse dates properly (format: YYYYMMDD as integer)
climate_clean <- climate_raw %>%
  mutate(
    date_parsed = as.Date(as.character(date), format = "%Y%m%d"),
    year  = year(date_parsed),
    month = month(date_parsed),
    day   = day(date_parsed)
  ) %>%
  filter(!is.na(date_parsed))

cat(sprintf("   Date range: %s to %s\n",
            min(climate_clean$date_parsed, na.rm = TRUE),
            max(climate_clean$date_parsed, na.rm = TRUE)))

# Replace -999 sentinel values with NA
climate_clean <- climate_clean %>%
  mutate(across(
    c(temperature_c, precipitation_mm, humidity_pct, wind_speed_ms, solar_radiation_mj),
    ~ ifelse(. < -900, NA_real_, .)
  ))


# ── 4. Aggregate Climate to Monthly ───────────────────────────────────────────

cat("\n4. Aggregating climate data to monthly summaries...\n")

climate_monthly <- climate_clean %>%
  group_by(city, latitude, longitude, year, month) %>%
  summarise(
    # Temperature
    temp_mean_c     = mean(temperature_c, na.rm = TRUE),
    temp_min_c      = min(temperature_c, na.rm = TRUE),
    temp_max_c      = max(temperature_c, na.rm = TRUE),
    temp_range_c    = temp_max_c - temp_min_c,

    # Precipitation
    precip_total_mm = sum(precipitation_mm, na.rm = TRUE),
    precip_days     = sum(precipitation_mm > 0.1, na.rm = TRUE),  # rainy days
    precip_max_day  = max(precipitation_mm, na.rm = TRUE),

    # Humidity
    humidity_mean   = mean(humidity_pct, na.rm = TRUE),

    # Wind
    wind_mean_ms    = mean(wind_speed_ms, na.rm = TRUE),

    # Solar
    solar_mean_mj   = mean(solar_radiation_mj, na.rm = TRUE),

    # Count of valid observations
    n_days          = n(),
    n_valid         = sum(!is.na(temperature_c)),

    .groups = "drop"
  )

cat(sprintf("   Monthly aggregates: %d rows (%d cities × %d months)\n",
            nrow(climate_monthly),
            n_distinct(climate_monthly$city),
            n_distinct(paste(climate_monthly$year, climate_monthly$month))))


# ── 5. Aggregate Climate to Kenya-Wide Annual ─────────────────────────────────

cat("5. Computing Kenya-wide annual climate averages...\n")

climate_annual <- climate_clean %>%
  group_by(year) %>%
  summarise(
    # Weighted by number of cities reporting
    temp_mean_c       = mean(temperature_c, na.rm = TRUE),
    temp_max_c        = mean(temp_max_c, na.rm = TRUE),  # This will be done differently
    precip_total_mm   = mean(precip_total_mm, na.rm = TRUE),  # Placeholder
    humidity_mean     = mean(humidity_pct, na.rm = TRUE),
    wind_mean_ms      = mean(wind_speed_ms, na.rm = TRUE),
    solar_mean_mj     = mean(solar_radiation_mj, na.rm = TRUE),
    n_days            = n(),
    n_cities          = n_distinct(city),
    .groups = "drop"
  )

# Recompute properly from daily data
climate_annual <- climate_clean %>%
  group_by(year) %>%
  summarise(
    temp_mean_c     = mean(temperature_c, na.rm = TRUE),
    temp_max_c      = max(temperature_c, na.rm = TRUE),
    precip_total_mm = sum(precipitation_mm, na.rm = TRUE) / n_distinct(city),
    precip_days     = sum(precipitation_mm > 0.1, na.rm = TRUE) / n_distinct(city),
    humidity_mean   = mean(humidity_pct, na.rm = TRUE),
    wind_mean_ms    = mean(wind_speed_ms, na.rm = TRUE),
    solar_mean_mj   = mean(solar_radiation_mj, na.rm = TRUE),
    n_cities        = n_distinct(city),
    .groups = "drop"
  )

cat(sprintf("   Kenya annual climate: %d years (%d - %d)\n",
            nrow(climate_annual),
            min(climate_annual$year),
            max(climate_annual$year)))
print(head(climate_annual, 5))


# ── 6. Merge All Data ─────────────────────────────────────────────────────────

cat("\n6. Merging World Bank + WHO + Climate into unified dataset...\n")

# Start with World Bank (Kenya only, annual)
merged <- wb_wide %>%
  left_join(who_wide, by = "year", suffix = c("_wb", "_who")) %>%
  left_join(climate_annual, by = "year")

cat(sprintf("   Merged dataset: %d rows × %d columns\n", nrow(merged), ncol(merged)))
cat(sprintf("   Columns: %s\n\n", paste(names(merged), collapse = ", ")))


# ── 7. Create Lagged Features for ML ──────────────────────────────────────────

cat("7. Creating lagged features for time-series ML...\n")

# Create lagged variables (1-year, 2-year lags) for key indicators
ml_features <- merged %>%
  arrange(year) %>%
  mutate(
    # Lagged malaria incidence
    incidence_lag1 = lag(malaria_incidence_per_1000, 1),
    incidence_lag2 = lag(malaria_incidence_per_1000, 2),

    # Lagged climate
    precip_lag1  = lag(precip_total_mm, 1),
    precip_lag2  = lag(precip_total_mm, 2),
    temp_lag1    = lag(temp_mean_c, 1),
    temp_lag2    = lag(temp_mean_c, 2),

    # Climate anomalies (deviation from long-term mean)
    precip_anomaly  = precip_total_mm - mean(precip_total_mm, na.rm = TRUE),
    temp_anomaly    = temp_mean_c - mean(temp_mean_c, na.rm = TRUE),

    # Rolling means
    precip_roll3    = zoo::rollmean(precip_total_mm, 3, fill = NA, align = "right"),
    temp_roll3      = zoo::rollmean(temp_mean_c, 3, fill = NA, align = "right"),

    # Change in incidence
    incidence_change = malaria_incidence_per_1000 - lag(malaria_incidence_per_1000, 1),
    incidence_change_pct = (incidence_change / lag(malaria_incidence_per_1000, 1)) * 100
  )

cat(sprintf("   ML features dataset: %d rows × %d columns\n",
            nrow(ml_features), ncol(ml_features)))


# ── 8. Save Processed Data ────────────────────────────────────────────────────

cat("\n8. Saving processed datasets...\n")

write_csv(wb_wide,          file.path(PROC_DIR, "worldbank_kenya_annual.csv"))
cat("   Saved: worldbank_kenya_annual.csv\n")

write_csv(wb_ea,            file.path(PROC_DIR, "worldbank_east_africa.csv"))
cat("   Saved: worldbank_east_africa.csv\n")

write_csv(who_wide,         file.path(PROC_DIR, "who_malaria_annual.csv"))
cat("   Saved: who_malaria_annual.csv\n")

write_csv(climate_monthly,  file.path(PROC_DIR, "climate_monthly.csv"))
cat("   Saved: climate_monthly.csv\n")

write_csv(climate_annual,   file.path(PROC_DIR, "climate_annual_kenya.csv"))
cat("   Saved: climate_annual_kenya.csv\n")

write_csv(merged,           file.path(PROC_DIR, "malaria_climate_merged.csv"))
cat("   Saved: malaria_climate_merged.csv\n")

write_csv(ml_features,      file.path(PROC_DIR, "malaria_ml_features.csv"))
cat("   Saved: malaria_ml_features.csv\n")


# ── 9. Data Quality Report ────────────────────────────────────────────────────

cat("\n" %+% strrep("=", 70) %>% paste0("\n"))
cat("  DATA QUALITY REPORT\n")
cat(strrep("=", 70) %>% paste0("\n\n"))

# Missing values in merged
cat("Missing values in merged dataset:\n")
missing_summary <- merged %>%
  summarise(across(everything(), ~ sum(is.na(.)))) %>%
  pivot_longer(everything(), names_to = "column", values_to = "n_missing") %>%
  filter(n_missing > 0) %>%
  arrange(desc(n_missing))

if (nrow(missing_summary) > 0) {
  print(missing_summary)
} else {
  cat("  No missing values! \n")
}

cat(sprintf("\nMerged dataset year range: %d - %d\n", min(merged$year), max(merged$year)))
cat(sprintf("Merged dataset: %d rows × %d columns\n", nrow(merged), ncol(merged)))

# Quick summary stats
cat("\nKey variable summaries:\n")
merged %>%
  select(
    malaria_incidence_per_1000,
    precip_total_mm, temp_mean_c, humidity_mean,
    population_total
  ) %>%
  summary() %>%
  print()

cat("\n\nPipeline complete! Output files in: data/processed/\n")
cat("Next step: Run R/visualization/02_eda.R for exploratory analysis\n")
