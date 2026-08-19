# ==============================================================================
# Malaria Outbreak Predictor — Master Script
# ==============================================================================
# Run this ONE script to execute the entire pipeline from start to finish:
#
#   Step 1: Fetch data from WHO, World Bank, NASA APIs
#   Step 2: Load, clean, merge, and create features
#   Step 3: Exploratory data analysis + 7 publication-quality charts
#   Step 4: Train ML models (Ridge, RF, GBM, Linear)
#   Step 5: Launch interactive Shiny dashboard
#
# Usage:
#   1. Open this file in RStudio
#   2. Set working directory to project root (malaria-outbreak-predictor/)
#   3. Click "Source" or run:  source("R/run_all.R")
#
# Or run individual steps:
#   source("R/00_fetch_data.R")
#   source("R/01_load_and_clean.R")
#   source("R/02_eda.R")
#   source("R/03_train_model.R")
#   source("R/04_shiny_app.R")
# ==============================================================================

cat("\n")
cat("  ====================================================\n")
cat("  Malaria Outbreak Predictor — Full Pipeline\n")
cat("  ====================================================\n")
cat("  Author: Calvin Omondi Okoth\n")
cat("  ====================================================\n\n")

# ── Step 0: Install Required Packages ──────────────────────────────────────────

cat("[STEP 0] Checking and installing packages...\n\n")

required_packages <- c(
  # Data wrangling
  "tidyverse", "lubridate",
  # API access
  "httr", "jsonlite",
  # ML
  "tidymodels", "ranger", "xgboost",
  # Visualization
  "scales", "plotly",
  # Dashboard
  "shiny", "shinydashboard", "bslib", "DT"
)

missing <- required_packages[!required_packages %in% installed.packages()[, "Package"]]

if (length(missing) > 0) {
  cat("  Installing missing packages:", paste(missing, collapse = ", "), "\n")
  cat("  This may take a few minutes...\n\n")
  install.packages(missing, repos = "https://cran.r-project.org")
} else {
  cat("  All packages already installed!\n")
}


# ── Step 1: Fetch Data ─────────────────────────────────────────────────────────

cat("\n\n[STEP 1] Fetching data from APIs...\n")
cat("  This downloads ~44,000 data points from WHO, World Bank, and NASA.\n")
cat("  It may take 2-3 minutes.\n\n")

tryCatch(
  source("R/00_fetch_data.R", local = TRUE),
  error = function(e) {
    cat("  ERROR in data fetch:", conditionMessage(e), "\n")
    cat("  If you already have data/raw/*.csv files, you can skip this step.\n")
  }
)


# ── Step 2: Clean & Merge ─────────────────────────────────────────────────────

cat("\n\n[STEP 2] Cleaning and merging data...\n\n")

source("R/01_load_and_clean.R", local = TRUE)


# ── Step 3: Exploratory Analysis ──────────────────────────────────────────────

cat("\n\n[STEP 3] Generating visualizations...\n\n")

source("R/02_eda.R", local = TRUE)


# ── Step 4: Train Models ──────────────────────────────────────────────────────

cat("\n\n[STEP 4] Training ML models...\n\n")

source("R/03_train_model.R", local = TRUE)


# ── Step 5: Launch Dashboard ──────────────────────────────────────────────────

cat("\n\n[STEP 5] Launching Shiny dashboard...\n")
cat("  The dashboard will open in your browser at http://localhost:3838\n")
cat("  Press Escape or Ctrl+C in the console to stop it.\n\n")

source("R/04_shiny_app.R", local = TRUE)
