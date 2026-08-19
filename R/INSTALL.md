# Malaria Outbreak Predictor — R Setup Guide

## Quick Start (3 commands)

```r
# 1. Open the project in RStudio
#    File > Open Project > malaria_outbreak_predictor.Rproj

# 2. Run the master script (installs packages automatically)
source("R/run_all.R")

# 3. The dashboard opens at http://localhost:3838
```

---

## Prerequisites

- **R** >= 4.2.0 (download from https://cran.r-project.org/)
- **RStudio** (download from https://posit.co/download/rstudio-desktop/)
- **Internet connection** (for fetching data from APIs on first run)

---

## Package Installation

All packages are installed automatically by `run_all.R`, but if you prefer manual installation:

```r
install.packages(c(
  "tidyverse",    # Data wrangling + ggplot2
  "lubridate",    # Date handling
  "httr",         # HTTP requests (API access)
  "jsonlite",     # JSON parsing
  "tidymodels",   # ML framework
  "ranger",       # Random Forest engine
  "xgboost",      # Gradient Boosting engine
  "scales",       # Axis formatting
  "plotly",       # Interactive plots
  "shiny",        # Dashboard framework
  "shinydashboard", # Dashboard layout
  "bslib",        # Bootstrap theming
  "DT"            # Interactive tables
))
```

---

## Project Structure

```
malaria-outbreak-predictor/
├── malaria_outbreak_predictor.Rproj   <- Open this in RStudio
├── R/
│   ├── INSTALL.md                     <- You are here
│   ├── run_all.R                      <- Master script (run this!)
│   ├── 00_fetch_data.R                <- Fetch data from APIs
│   ├── 01_load_and_clean.R            <- Clean, merge, features
│   ├── 02_eda.R                       <- Charts + visualizations
│   ├── 03_train_model.R               <- ML model training
│   ├── 04_shiny_app.R                 <- Interactive dashboard
│   ├── data-pipeline/
│   │   └── 01_load_and_clean.R        <- (older version)
│   └── shiny/
│       └── app.R                      <- (older version)
├── data/
│   ├── raw/                           <- Downloaded from APIs
│   │   ├── worldbank_malaria_indicators.csv
│   │   ├── who_malaria_surveillance.csv
│   │   └── kenya_climate_daily.csv
│   └── processed/                     <- Clean analysis-ready data
│       ├── malaria_climate_merged.csv
│       ├── malaria_ml_features.csv
│       ├── predictions.csv
│       ├── climate_monthly.csv
│       ├── climate_annual_kenya.csv
│       ├── worldbank_kenya_annual.csv
│       ├── worldbank_east_africa.csv
│       └── who_malaria_annual.csv
├── models/
│   └── best_model.rds                 <- Trained ML model
└── docs/images/                       <- Publication-quality charts
    ├── malaria_trend.png
    ├── climate_correlation.png
    ├── east_africa_comparison.png
    ├── model_predictions.png
    ├── feature_importance.png
    ├── climate_heatmap.png
    └── architecture.png
```

---

## Running Individual Steps

If you want to run steps separately (recommended for learning):

### Step 1: Fetch Data
```r
source("R/00_fetch_data.R")
# Downloads ~44,000 data points from 3 APIs
# Takes 2-3 minutes on first run
```

### Step 2: Clean & Merge
```r
source("R/01_load_and_clean.R")
# Cleans raw data, creates 7 processed CSV files
```

### Step 3: Visualizations
```r
source("R/02_eda.R")
# Generates 7 PNG charts in docs/images/
```

### Step 4: Train Models
```r
source("R/03_train_model.R")
# Trains Ridge, RF, GBM, and Linear models
# Saves best model to models/best_model.rds
```

### Step 5: Launch Dashboard
```r
source("R/04_shiny_app.R")
# Opens interactive dashboard at http://localhost:3838
```

---

## Data Sources

| Source | API | License |
|--------|-----|---------|
| World Bank | `api.worldbank.org` | CC BY 4.0 |
| WHO GHO | `ghoapi.azureedge.net` | Open Access |
| NASA POWER | `power.larc.nasa.gov` | Public Domain |

---

## Troubleshooting

**"Could not find function" error:**
- Run `source("R/run_all.R")` to install all packages first

**"data/raw/*.csv not found":**
- Run `source("R/00_fetch_data.R")` to fetch data from APIs
- Requires internet connection

**Dashboard won't open:**
- Make sure port 3838 is not in use
- Try: `shiny::runApp("R/04_shiny_app.R", port = 3838)`

**Slow API fetching:**
- APIs are rate-limited; the script includes delays between requests
- If it fails, re-run — data is saved incrementally

---

## Built by Calvin Omondi Okoth

GitHub: https://github.com/calvinokoth9528-cloud/malaria-outbreak-predictor
LinkedIn: https://www.linkedin.com/in/calvin-klein-9528c2004
