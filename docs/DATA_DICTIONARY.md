# Data Dictionary

## malaria_climate_merged.csv

The primary analysis dataset. One row per year (2000-2024), 23 columns.

### Malaria Indicators

| Column | Source | Unit | Range | Description |
|--------|--------|------|-------|-------------|
| `malaria_incidence_per_1000` | World Bank | per 1,000 | 71.7 - 243.2 | Annual malaria incidence per 1,000 population at risk |
| `estimated_malaria_cases_value` | WHO | count | 4,185,536 - 7,690,612 | WHO model-estimated total malaria cases |
| `estimated_malaria_cases_low_ci` | WHO | count | Lower bound of 95% confidence interval |
| `estimated_malaria_cases_high_ci` | WHO | count | Upper bound of 95% confidence interval |
| `estimated_malaria_deaths_value` | WHO | count | 11,656 - 13,613 | WHO model-estimated malaria deaths |
| `estimated_malaria_deaths_low_ci` | WHO | count | Lower bound of 95% CI |
| `estimated_malaria_deaths_high_ci` | WHO | count | Upper bound of 95% CI |
| `estimated_incidence_per_1000_at_risk_value` | WHO | per 1,000 | WHO estimated incidence (may differ slightly from World Bank) |
| `estimated_incidence_per_1000_at_risk_low_ci` | WHO | per 1,000 | Lower bound of 95% CI |
| `estimated_incidence_per_1000_at_risk_high_ci` | WHO | per 1,000 | Upper bound of 95% CI |

### Population & Health

| Column | Source | Unit | Range | Description |
|--------|--------|------|-------|-------------|
| `population_total` | World Bank | count | 30,642,890 - 56,432,944 | Kenya total population |
| `health_expenditure_pct_gdp` | World Bank | % | 3.6 - 5.7 | Health expenditure as percentage of GDP |
| `urban_population_pct` | World Bank | % | 19.5 - 31.9 | Urban population as percentage of total |
| `agricultural_precipitation_mm` | World Bank | mm/year | 630 - 1,332 | Annual agricultural precipitation |

### Climate (Kenya-Wide Annual Averages from NASA POWER)

| Column | Source | Unit | Range | Description |
|--------|--------|------|-------|-------------|
| `temp_mean_c` | NASA POWER | °C | 20.7 - 21.5 | Annual mean temperature (8-city average) |
| `temp_max_c` | NASA POWER | °C | 31.8 - 33.5 | Annual maximum temperature |
| `precip_total_mm` | NASA POWER | mm/year | 1,024 - 1,973 | Total annual precipitation (8-city average) |
| `precip_days` | NASA POWER | days | 260 - 310 | Number of days with measurable rainfall (>0.1mm) |
| `humidity_mean` | NASA POWER | % | 69.3 - 76.8 | Mean relative humidity |
| `wind_mean_ms` | NASA POWER | m/s | 2.1 - 2.4 | Mean wind speed at 2 meters |
| `solar_mean_mj` | NASA POWER | MJ/m²/day | 19.5 - 21.0 | Mean solar radiation |
| `n_cities` | Calculated | count | 8 | Number of cities contributing to annual average |

---

## malaria_ml_features.csv

ML-ready dataset with lagged features and anomalies. Same base columns as merged, plus:

| Column | Description |
|--------|-------------|
| `incidence_lag1` | Malaria incidence 1 year prior |
| `incidence_lag2` | Malaria incidence 2 years prior |
| `incidence_change` | Year-over-year absolute change (current - previous) |
| `incidence_change_pct` | Year-over-year percentage change |
| `precip_lag1` | Precipitation 1 year prior |
| `precip_lag2` | Precipitation 2 years prior |
| `precip_anomaly` | Precipitation deviation from long-term mean (mm) |
| `temp_anomaly` | Temperature deviation from long-term mean (°C) |

---

## climate_monthly.csv

Monthly climate summaries by city. 1,440 rows (8 cities × 15 years × 12 months).

| Column | Unit | Description |
|--------|------|-------------|
| `city` | — | City name |
| `latitude` | decimal degrees | City latitude |
| `longitude` | decimal degrees | City longitude |
| `year` | — | Calendar year |
| `month` | 1-12 | Calendar month |
| `temp_mean_c` | °C | Mean daily temperature for the month |
| `temp_min_c` | °C | Minimum daily temperature |
| `temp_max_c` | °C | Maximum daily temperature |
| `temp_range_c` | °C | Monthly temperature range (max - min) |
| `precip_total_mm` | mm | Total precipitation for the month |
| `precip_days` | days | Number of rainy days (>0.1mm) |
| `precip_max_day` | mm | Maximum single-day precipitation |
| `humidity_mean` | % | Mean relative humidity |
| `wind_mean_ms` | m/s | Mean wind speed |
| `solar_mean_mj` | MJ/m²/day | Mean solar radiation |

---

## worldbank_east_africa.csv

Malaria incidence comparison across 8 East African countries. 200 rows (8 countries × 25 years).

| Column | Description |
|--------|-------------|
| `country` | Country name |
| `iso3` | ISO 3166-1 alpha-3 country code |
| `year` | Calendar year |
| `malaria_incidence_per_1000` | Cases per 1,000 population at risk |

**Countries included:** Burundi, Ethiopia, Kenya, Malawi, Mozambique, Rwanda, South Sudan, Tanzania, Uganda
