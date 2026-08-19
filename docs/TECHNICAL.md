# Technical Documentation

## Data Pipeline Architecture

### Stage 1: Data Ingestion (`scripts/etl/fetch_malaria_data.py`)

Fetches raw data from three public APIs:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   World Bank    │    │   WHO GHO API   │    │  NASA POWER     │
│   REST API      │    │   OData API     │    │  REST API       │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ▼                      ▼                      ▼
   worldbank_              who_malaria_           kenya_climate_
   malaria_                surveillance.csv       daily.csv
   indicators.csv
```

**API Details:**

| API | Endpoint | Format | Rate Limit |
|-----|----------|--------|------------|
| World Bank | `api.worldbank.org/v2/country/{iso3}/indicator/{code}` | JSON | None (polite: 0.3s delay) |
| WHO GHO | `ghoapi.azureedge.net/api/{indicator}` | OData JSON | None |
| NASA POWER | `power.larc.nasa.gov/api/temporal/daily/point` | JSON | None (polite: 0.5s delay) |

**World Bank Indicators Fetched:**
- `SH.MLR.INCD.P3` — Malaria incidence per 1,000 at risk
- `SH.XPD.CHEX.GD.ZS` — Health expenditure (% of GDP)
- `SP.POP.TOTL` — Total population
- `SP.URB.TOTL.IN.ZS` — Urban population (% of total)
- `AG.LND.PRCP.MM` — Agricultural precipitation (mm/year)

**WHO Indicators Fetched:**
- `MALARIA_EST_INCIDENCE` — Estimated malaria incidence per 1,000 at risk
- `MALARIA_EST_CASES` — Estimated total malaria cases
- `MALARIA_EST_DEATHS` — Estimated malaria deaths

**NASA POWER Parameters:**
- `T2M` — Temperature at 2 meters (°C)
- `PRECTOTCORR` — Precipitation (mm/day)
- `RH2M` — Relative humidity at 2 meters (%)
- `WS2M` — Wind speed at 2 meters (m/s)
- `ALLSKY_SFC_SW_DWN` — Solar radiation (MJ/m²/day)

### Stage 2: Data Processing (`R/data-pipeline/01_load_and_clean.R`)

Transforms raw data into analysis-ready format:

```r
# Pipeline steps:
1. Load raw CSVs with proper column types
2. Pivot World Bank data to wide format (one row per year)
3. Parse WHO confidence intervals into separate columns
4. Convert NASA daily data to date objects, replace -999 sentinels with NA
5. Aggregate daily climate → monthly summaries (mean, min, max, totals)
6. Aggregate monthly → Kenya-wide annual averages
7. Merge all three sources on year
8. Create lagged features for time-series ML
9. Compute climate anomalies (deviation from long-term mean)
```

**Output Variables (malaria_climate_merged.csv):**

| Variable | Source | Type | Description |
|----------|--------|------|-------------|
| `year` | — | int | Calendar year (2000-2024) |
| `malaria_incidence_per_1000` | World Bank | double | Cases per 1,000 at-risk population |
| `population_total` | World Bank | double | Kenya total population |
| `health_expenditure_pct_gdp` | World Bank | double | Health spending as % of GDP |
| `urban_population_pct` | World Bank | double | Urban population as % of total |
| `agricultural_precipitation_mm` | World Bank | double | Annual precipitation (mm) |
| `estimated_malaria_cases_value` | WHO | double | WHO point estimate of total cases |
| `estimated_malaria_cases_low_ci` | WHO | double | 95% CI lower bound |
| `estimated_malaria_cases_high_ci` | WHO | double | 95% CI upper bound |
| `estimated_malaria_deaths_value` | WHO | double | WHO point estimate of deaths |
| `temp_mean_c` | NASA | double | Annual mean temperature (°C) |
| `temp_max_c` | NASA | double | Annual max temperature (°C) |
| `precip_total_mm` | NASA | double | Annual precipitation (mm) |
| `precip_days` | NASA | double | Number of rainy days per year |
| `humidity_mean` | NASA | double | Mean relative humidity (%) |
| `wind_mean_ms` | NASA | double | Mean wind speed (m/s) |
| `solar_mean_mj` | NASA | double | Mean solar radiation (MJ/m²/day) |

### Stage 3: ML Feature Engineering (`malaria_ml_features.csv`)

Creates time-series features for prediction:

| Feature | Description |
|---------|-------------|
| `incidence_lag1` | Malaria incidence 1 year prior |
| `incidence_lag2` | Malaria incidence 2 years prior |
| `incidence_change` | Year-over-year change in incidence |
| `incidence_change_pct` | Percentage change in incidence |
| `precip_lag1` | Precipitation 1 year prior |
| `precip_lag2` | Precipitation 2 years prior |
| `precip_anomaly` | Precipitation deviation from long-term mean |
| `temp_anomaly` | Temperature deviation from long-term mean |

---

## Climate Analysis

### Spatial Coverage

Daily climate data for 8 Kenyan cities (2010-2024):

| City | Lat | Lon | Climate Zone |
|------|-----|-----|--------------|
| Nairobi | -1.29 | 36.82 | Highland |
| Mombasa | -4.04 | 39.67 | Coastal |
| Kisumu | -0.10 | 34.76 | Lakeside |
| Nakuru | -0.30 | 36.07 | Highland |
| Eldoret | 0.52 | 35.27 | Highland |
| Garissa | -0.47 | 39.64 | Semi-arid |
| Kakamega | 0.28 | 34.75 | Western |
| Machakos | -1.52 | 37.26 | Eastern |

### Malaria-Climate Correlations

Malaria transmission depends on:
1. **Rainfall** — Creates breeding sites for Anopheles mosquitoes (2-month lag)
2. **Temperature** — Affects mosquito development speed and parasite incubation
3. **Humidity** — Higher humidity = longer mosquito lifespan
4. **Altitude** — Malaria risk decreases above 1,500m

---

## Known Data Limitations

1. **Spatial resolution**: Climate data covers 8 cities, not all 47 counties
2. **Temporal mismatch**: WHO/World Bank data is annual; climate is daily (aggregated)
3. **Estimation uncertainty**: WHO provides confidence intervals reflecting model uncertainty
4. **Non-reporting**: Actual malaria cases may be underreported in rural areas
5. **Confounding factors**: Vector control interventions, drug resistance not captured

---

## Running the Full Pipeline

```bash
# Step 1: Fetch data (requires internet)
python scripts/etl/fetch_malaria_data.py

# Step 2: Verify pipeline (Python)
python scripts/etl/verify_pipeline.py

# Step 3: Run R pipeline (requires R + tidyverse)
Rscript R/data-pipeline/01_load_and_clean.R

# Step 4: Build ML models (coming soon)
# python python/ml/train_model.py

# Step 5: Launch dashboard (coming soon)
# Rscript R/shiny/app.R
```
