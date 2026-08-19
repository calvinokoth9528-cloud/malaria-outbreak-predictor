# ==============================================================================
# Malaria Outbreak Predictor — Data Fetcher (Pure R)
# ==============================================================================
# Downloads malaria surveillance and climate data from:
#   1. World Bank Open Data API
#   2. WHO Global Health Observatory API
#   3. NASA POWER Climate API
#
# All data is publicly available and free to use.
# Run this BEFORE 01_load_and_clean.R
# ==============================================================================

library(tidyverse)
library(httr)
library(jsonlite)

# ── Configuration ──────────────────────────────────────────────────────────────

RAW_DIR <- file.path("data", "raw")
dir.create(RAW_DIR, showWarnings = FALSE, recursive = TRUE)

KENYA_ISO3 <- "KEN"
EAST_AFRICA <- c("KEN", "UGA", "TZA", "RWA", "ETH", "SSD", "SOM", "BDI", "MOZ", "MWI")

cat(strrep("=", 70), "\n")
cat("  Malaria Outbreak Predictor — Data Fetcher (R)\n")
cat(strrep("=", 70), "\n\n")

# ── Helper Functions ───────────────────────────────────────────────────────────

fetch_json <- function(url, description = "") {
  cat("  Fetching:", description, "...\n")
  tryCatch({
    resp <- GET(url, timeout(30), user_agent("MalariaPredictor/1.0 (research)"))
    stop_for_status(resp)
    data <- content(resp, as = "parsed", type = "application/json")
    cat("    Success\n")
    return(data)
  }, error = function(e) {
    cat("    Error:", conditionMessage(e), "\n")
    return(NULL)
  })
}

safe_sleep <- function(seconds = 0.3) {
  Sys.sleep(seconds)
}


# ── 1. World Bank Data ─────────────────────────────────────────────────────────

cat("\n[1/3] Fetching World Bank Data...\n")

wb_indicators <- c(
  "SH.MLR.INCD.P3"  = "malaria_incidence_per_1000",
  "SH.MLR.INCD"     = "malaria_incidence_total_cases",
  "SH.MLR.MORT"     = "malaria_mortality_rate",
  "SH.MLR.DTHS"     = "malaria_deaths",
  "SH.UHC.SRVS.CV.XD" = "uhc_service_coverage"
)

extra_indicators <- c(
  "EN.ATM.PREC.MM"     = "annual_precipitation_mm",
  "EN.ATM.FTEMP.ZD"    = "temperature_anomaly",
  "SH.XPD.CHEX.GD.ZS"  = "health_expenditure_pct_gdp",
  "SP.POP.TOTL"         = "population_total",
  "SP.URB.TOTL.IN.ZS"   = "urban_population_pct",
  "AG.LND.PRCP.MM"      = "agricultural_precipitation_mm"
)

all_wb_rows <- list()

# Fetch Kenya indicators
for (i in seq_along(c(wb_indicators, extra_indicators))) {
  codes <- c(wb_indicators, extra_indicators)
  code <- names(codes)[i]
  name <- codes[i]

  url <- paste0(
    "https://api.worldbank.org/v2/country/", KENYA_ISO3,
    "/indicator/", code,
    "?format=json&per_page=100&date=2000:2024"
  )

  data <- fetch_json(url, name)

  if (!is.null(data) && length(data) > 1 && !is.null(data[[2]])) {
    rows <- map_dfr(data[[2]], ~ tibble(
      country = "Kenya",
      iso3    = KENYA_ISO3,
      year    = as.integer(.x$date),
      indicator = name,
      value   = as.numeric(.x$value)
    ))
    all_wb_rows[[name]] <- rows
    cat(sprintf("    %s: %d data points\n", name, nrow(rows)))
  }
  safe_sleep()
}

# Fetch East Africa comparison
url <- paste0(
  "https://api.worldbank.org/v2/country/",
  paste(EAST_AFRICA, collapse = ";"),
  "/indicator/SH.MLR.INCD.P3",
  "?format=json&per_page=500&date=2000:2024"
)

data <- fetch_json(url, "malaria_incidence (East Africa)")

if (!is.null(data) && length(data) > 1 && !is.null(data[[2]])) {
  ea_rows <- map_dfr(data[[2]], ~ {
    iso3_val <- trimws(.x$countryiso3code)
    year_val <- trimws(.x$date)
    if (nchar(iso3_val) == 3 && grepl("^\\d{4}$", year_val)) {
      tibble(
        country   = .x$country$value,
        iso3      = iso3_val,
        year      = as.integer(year_val),
        indicator = "malaria_incidence_per_1000",
        value     = as.numeric(.x$value)
      )
    }
  })
  all_wb_rows[["malaria_incidence_east_africa"]] <- ea_rows
  cat(sprintf("    malaria_incidence (East Africa): %d rows\n", nrow(ea_rows)))
}
safe_sleep()

# Combine and save
wb_all <- bind_rows(all_wb_rows)
write_csv(wb_all, file.path(RAW_DIR, "worldbank_malaria_indicators.csv"))
cat(sprintf("\n  Saved World Bank: %d rows\n", nrow(wb_all)))


# ── 2. WHO Global Health Observatory ──────────────────────────────────────────

cat("\n[2/3] Fetching WHO Malaria Data...\n")

who_indicators <- c(
  "MALARIA_EST_INCIDENCE" = "estimated_incidence_per_1000_at_risk",
  "MALARIA_EST_CASES"     = "estimated_malaria_cases",
  "MALARIA_EST_DEATHS"    = "estimated_malaria_deaths",
  "MAL_RDT"               = "rapid_diagnostic_tests_performed",
  "MAL_ARTEM"             = "artemisinin_based_treatments"
)

all_who_rows <- list()

for (i in seq_along(who_indicators)) {
  code <- names(who_indicators)[i]
  name <- who_indicators[i]

  filter_str <- URLencode(paste0("SpatialDim eq '", KENYA_ISO3, "'"))
  url <- paste0("https://ghoapi.azureedge.net/api/", code, "?$filter=", filter_str)

  data <- fetch_json(url, name)

  if (!is.null(data) && !is.null(data$value)) {
    rows <- map_dfr(data$value, ~ {
      val <- .x$NumericValue
      if (!is.null(val)) {
        tibble(
          country   = "Kenya",
          iso3      = KENYA_ISO3,
          year      = as.integer(.x$TimeDim),
          indicator = name,
          value     = as.numeric(val),
          low_ci    = as.numeric(.x$Low),
          high_ci   = as.numeric(.x$High),
          value_type = as.character(.x$Value)
        )
      }
    })
    all_who_rows[[name]] <- rows
    cat(sprintf("    %s: %d data points\n", name, nrow(rows)))
  }
  safe_sleep()
}

who_all <- bind_rows(all_who_rows)
write_csv(who_all, file.path(RAW_DIR, "who_malaria_surveillance.csv"))
cat(sprintf("\n  Saved WHO: %d rows\n", nrow(who_all)))


# ── 3. NASA POWER Climate Data ────────────────────────────────────────────────

cat("\n[3/3] Fetching NASA POWER Climate Data...\n")

kenya_cities <- list(
  nairobi  = c(-1.29, 36.82),
  mombasa  = c(-4.04, 39.67),
  kisumu   = c(-0.10, 34.76),
  nakuru   = c(-0.30, 36.07),
  eldoret  = c(0.52,  35.27),
  garissa  = c(-0.47, 39.64),
  kakamega = c(0.28,  34.75),
  machakos = c(-1.52, 37.26)
)

all_climate_rows <- list()

for (city in names(kenya_cities)) {
  lat <- kenya_cities[[city]][1]
  lon <- kenya_cities[[city]][2]

  url <- paste0(
    "https://power.larc.nasa.gov/api/temporal/daily/point",
    "?parameters=T2M,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN",
    "&community=AG",
    "&longitude=", lon, "&latitude=", lat,
    "&start=20100101&end=20241231",
    "&format=JSON"
  )

  data <- fetch_json(url, paste("NASA POWER", city))

  if (!is.null(data) && !is.null(data$properties)) {
    params <- data$properties$parameter

    if (!is.null(params)) {
      temp    <- params$T2M
      precip  <- params$PRECTOTCORR
      humid   <- params$RH2M
      wind    <- params$WS2M
      solar   <- params$ALLSKY_SFC_SW_DWN

      all_dates <- unique(c(names(temp), names(precip), names(humid)))
      all_dates <- setdiff(all_dates, "-999.0")

      rows <- map_dfr(all_dates, ~ {
        date_val <- as.integer(.x)
        if (is.na(date_val)) return(NULL)
        tibble(
          city              = city,
          latitude          = lat,
          longitude         = lon,
          date              = date_val,
          temperature_c     = as.numeric(temp[[.x]]),
          precipitation_mm  = as.numeric(precip[[.x]]),
          humidity_pct      = as.numeric(humid[[.x]]),
          wind_speed_ms     = as.numeric(wind[[.x]]),
          solar_radiation_mj = as.numeric(solar[[.x]])
        )
      })

      all_climate_rows[[city]] <- rows
      cat(sprintf("    %s: %d daily records\n", city, nrow(rows)))
    }
  }
  safe_sleep(0.5)
}

climate_all <- bind_rows(all_climate_rows)
write_csv(climate_all, file.path(RAW_DIR, "kenya_climate_daily.csv"))
cat(sprintf("\n  Saved Climate: %d rows\n", nrow(climate_all)))


# ── Summary ────────────────────────────────────────────────────────────────────

cat("\n", strrep("=", 70), "\n")
cat("  DATA FETCH COMPLETE\n")
cat(strrep("=", 70), "\n")
total <- nrow(wb_all) + nrow(who_all) + nrow(climate_all)
cat(sprintf("  Total data points: %s\n", format(total, big.mark = ",")))
cat(sprintf("  Files saved to: %s\n", normalizePath(RAW_DIR)))
cat("\n  Next step: Rscript R/01_load_and_clean.R\n")
