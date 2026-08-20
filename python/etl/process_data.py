#!/usr/bin/env python3
"""
Malaria Outbreak Predictor — Data Processing Pipeline (Python)
===============================================================
Transforms raw CSVs from WHO, World Bank, and NASA POWER APIs
into ML-ready features for the prediction model.

This is the Python equivalent of R/01_load_and_clean.R.

Input:
  data/raw/worldbank_malaria_indicators.csv
  data/raw/who_malaria_surveillance.csv
  data/raw/kenya_climate_daily.csv

Output:
  data/processed/malaria_ml_features.csv
  data/processed/malaria_climate_merged.csv
  data/processed/climate_annual_kenya.csv
  data/processed/climate_monthly.csv
  data/processed/who_malaria_annual.csv
  data/processed/worldbank_kenya_annual.csv
  data/processed/worldbank_east_africa.csv
"""

import os
import sys
import io
import warnings
warnings.filterwarnings("ignore")

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)


# ── 1. Load World Bank Data ───────────────────────────────────────────────────

def load_worldbank():
    """Load and pivot World Bank malaria indicators."""
    filepath = os.path.join(RAW_DIR, "worldbank_malaria_indicators.csv")
    df = pd.read_csv(filepath, on_bad_lines="warn", encoding="utf-8")
    print(f"  Loaded World Bank: {len(df)} rows")

    # Pivot: one row per year, columns = indicators
    kenya = df[df["country"] == "Kenya"].copy()
    kenya["year"] = pd.to_numeric(kenya["year"], errors="coerce")
    kenya["value"] = pd.to_numeric(kenya["value"], errors="coerce")
    kenya = kenya.dropna(subset=["year", "value"])

    # Pivot to wide format
    kenya_wide = kenya.pivot_table(
        index="year", columns="indicator", values="value", aggfunc="first"
    ).reset_index()
    kenya_wide.columns.name = None

    # Rename columns for clarity
    rename_map = {
        "malaria_incidence_per_1000": "malaria_incidence_per_1000",
        "malaria_incidence_total_cases": "malaria_incidence_total_cases",
        "malaria_mortality_rate": "malaria_mortality_rate",
        "malaria_deaths": "malaria_deaths",
        "annual_precipitation_mm": "annual_precipitation_mm_wb",
        "temperature_anomaly": "temperature_anomaly_wb",
        "health_expenditure_pct_gdp": "health_expenditure_pct_gdp",
        "population_total": "population_total",
        "urban_population_pct": "urban_population_pct",
        "agricultural_precipitation_mm": "agricultural_precipitation_mm",
        "uhc_service_coverage": "uhc_service_coverage",
    }
    kenya_wide = kenya_wide.rename(columns={k: v for k, v in rename_map.items() if k in kenya_wide.columns})

    # Save
    kenya_wide.to_csv(os.path.join(PROCESSED_DIR, "worldbank_kenya_annual.csv"), index=False)
    print(f"  ✅ worldbank_kenya_annual.csv: {len(kenya_wide)} years, {len(kenya_wide.columns)} columns")

    # East Africa comparison
    ea = df[df["indicator"] == "malaria_incidence_per_1000"].copy()
    ea["year"] = pd.to_numeric(ea["year"], errors="coerce")
    ea["value"] = pd.to_numeric(ea["value"], errors="coerce")
    ea = ea.dropna(subset=["year", "value"])
    ea.to_csv(os.path.join(PROCESSED_DIR, "worldbank_east_africa.csv"), index=False)
    print(f"  ✅ worldbank_east_africa.csv: {len(ea)} rows")

    return kenya_wide


# ── 2. Load WHO Data ──────────────────────────────────────────────────────────

def load_who():
    """Load WHO malaria surveillance data."""
    filepath = os.path.join(RAW_DIR, "who_malaria_surveillance.csv")
    df = pd.read_csv(filepath)
    print(f"  Loaded WHO: {len(df)} rows")

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["year", "value"])

    # Pivot to wide format
    who_wide = df.pivot_table(
        index="year", columns="indicator", values="value", aggfunc="first"
    ).reset_index()
    who_wide.columns.name = None

    # Rename for consistency
    col_renames = {}
    for col in who_wide.columns:
        if col != "year":
            col_renames[col] = col.lower().replace(" ", "_").replace("(", "").replace(")", "")
    who_wide = who_wide.rename(columns=col_renames)

    who_wide.to_csv(os.path.join(PROCESSED_DIR, "who_malaria_annual.csv"), index=False)
    print(f"  ✅ who_malaria_annual.csv: {len(who_wide)} years, {len(who_wide.columns)} columns")

    return who_wide


# ── 3. Process NASA Climate Data ──────────────────────────────────────────────

def load_climate():
    """Load and aggregate NASA POWER daily climate data."""
    filepath = os.path.join(RAW_DIR, "kenya_climate_daily.csv")
    df = pd.read_csv(filepath)
    print(f"  Loaded NASA climate: {len(df)} rows, {df['city'].nunique()} cities")

    # Convert types
    for col in ["temperature_c", "precipitation_mm", "humidity_pct", "wind_speed_ms", "solar_radiation_mj"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Date is stored as integer YYYYMMDD (e.g., 20100101)
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d", errors="coerce")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Remove invalid values
    df = df[df["temperature_c"] > -900]
    df = df[df["precipitation_mm"] >= 0]

    # ── Monthly averages per city ──────────────────────────────────
    monthly = df.groupby(["city", "year", "month"]).agg(
        temp_mean_c=("temperature_c", "mean"),
        temp_max_c=("temperature_c", "max"),
        precip_total_mm=("precipitation_mm", "sum"),
        precip_days=("precipitation_mm", lambda x: (x > 1).sum()),
        humidity_mean=("humidity_pct", "mean"),
        wind_mean_ms=("wind_speed_ms", "mean"),
        solar_mean_mj=("solar_radiation_mj", "mean"),
    ).reset_index()
    monthly.to_csv(os.path.join(PROCESSED_DIR, "climate_monthly.csv"), index=False)
    print(f"  ✅ climate_monthly.csv: {len(monthly)} rows")

    # ── Annual averages across all cities (Kenya-wide) ─────────────
    annual = df.groupby("year").agg(
        temp_mean_c=("temperature_c", "mean"),
        temp_max_c=("temperature_c", "max"),
        precip_total_mm=("precipitation_mm", "sum"),
        precip_days=("precipitation_mm", lambda x: (x > 1).sum()),
        humidity_mean=("humidity_pct", "mean"),
        wind_mean_ms=("wind_speed_ms", "mean"),
        solar_mean_mj=("solar_radiation_mj", "mean"),
        n_cities=("city", "nunique"),
    ).reset_index()
    annual.to_csv(os.path.join(PROCESSED_DIR, "climate_annual_kenya.csv"), index=False)
    print(f"  ✅ climate_annual_kenya.csv: {len(annual)} years")

    return monthly, annual


# ── 4. Merge & Create ML Features ─────────────────────────────────────────────

def create_ml_features(kenya_wb, who_wide, climate_annual):
    """Merge all datasets and create ML features."""
    print("\n4. Creating ML features...")

    # Start with World Bank data
    merged = kenya_wb.copy()

    # Merge WHO data
    if who_wide is not None and len(who_wide) > 0:
        who_merge = who_wide.copy()
        # Ensure year is numeric
        who_merge["year"] = pd.to_numeric(who_merge["year"], errors="coerce")
        merged = merged.merge(who_merge, on="year", how="outer", suffixes=("", "_who"))

    # Merge climate data
    if climate_annual is not None and len(climate_annual) > 0:
        climate_merge = climate_annual.copy()
        climate_merge["year"] = pd.to_numeric(climate_merge["year"], errors="coerce")
        merged = merged.merge(climate_merge, on="year", how="outer", suffixes=("", "_climate"))

    # Sort by year
    merged = merged.sort_values("year").reset_index(drop=True)

    # Save merged dataset
    merged.to_csv(os.path.join(PROCESSED_DIR, "malaria_climate_merged.csv"), index=False)
    print(f"  ✅ malaria_climate_merged.csv: {len(merged)} rows, {len(merged.columns)} columns")

    # ── Create lagged features for ML ──────────────────────────────
    features = merged.copy()

    # Ensure target column exists
    if "malaria_incidence_per_1000" not in features.columns:
        # Try to find it from WHO data
        for col in features.columns:
            if "incidence" in col.lower() and "1000" in col.lower():
                features["malaria_incidence_per_1000"] = features[col]
                print(f"  Mapped {col} → malaria_incidence_per_1000")
                break

    if "malaria_incidence_per_1000" in features.columns:
        # Lagged malaria incidence
        features["incidence_lag1"] = features["malaria_incidence_per_1000"].shift(1)
        features["incidence_lag2"] = features["malaria_incidence_per_1000"].shift(2)
        features["incidence_change"] = features["malaria_incidence_per_1000"].diff()
        features["incidence_change_pct"] = features["malaria_incidence_per_1000"].pct_change() * 100

    # Lagged climate features
    for col in ["precip_total_mm", "temp_mean_c", "humidity_mean"]:
        if col in features.columns:
            features[f"{col}_lag1"] = features[col].shift(1)
            features[f"{col}_lag2"] = features[col].shift(2)

    # Climate anomalies (deviation from rolling mean)
    if "precip_total_mm" in features.columns:
        rolling_precip = features["precip_total_mm"].rolling(window=5, min_periods=1).mean()
        features["precip_anomaly"] = features["precip_total_mm"] - rolling_precip

    if "temp_mean_c" in features.columns:
        rolling_temp = features["temp_mean_c"].rolling(window=5, min_periods=1).mean()
        features["temp_anomaly"] = features["temp_mean_c"] - rolling_temp

    # Rename lagged columns for consistency with ML model
    rename_lags = {
        "precip_total_mm_lag1": "precip_lag1",
        "precip_total_mm_lag2": "precip_lag2",
        "temp_mean_c_lag1": "temp_lag1",
        "temp_mean_c_lag2": "temp_lag2",
    }
    features = features.rename(columns={k: v for k, v in rename_lags.items() if k in features.columns})

    # Save ML features
    features.to_csv(os.path.join(PROCESSED_DIR, "malaria_ml_features.csv"), index=False)
    print(f"  ✅ malaria_ml_features.csv: {len(features)} rows, {len(features.columns)} columns")

    # Summary
    target = "malaria_incidence_per_1000"
    if target in features.columns:
        valid = features[target].notna().sum()
        print(f"\n  📊 Target column '{target}': {valid} valid values")
        print(f"     Range: {features[target].min():.1f} - {features[target].max():.1f} per 1,000")
        print(f"     Years: {int(features['year'].min())} - {int(features['year'].max())}")

    return features


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  🦟 Malaria Outbreak Predictor — Data Processing Pipeline")
    print("=" * 70)
    print(f"  Raw data:     {RAW_DIR}")
    print(f"  Processed:    {PROCESSED_DIR}")
    print(f"  Started:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check raw data exists
    required_files = [
        "worldbank_malaria_indicators.csv",
        "who_malaria_surveillance.csv",
        "kenya_climate_daily.csv",
    ]
    for f in required_files:
        path = os.path.join(RAW_DIR, f)
        if not os.path.exists(path):
            print(f"\n  ❌ Missing: {f}")
            print(f"     Run: python scripts/etl/fetch_malaria_data.py")
            sys.exit(1)
        size = os.path.getsize(path) / 1024
        print(f"  ✅ {f} ({size:.1f} KB)")

    # Process each dataset
    print("\n1. Processing World Bank data...")
    kenya_wb = load_worldbank()

    print("\n2. Processing WHO data...")
    who_wide = load_who()

    print("\n3. Processing NASA climate data...")
    monthly, annual = load_climate()

    # Create ML features
    features = create_ml_features(kenya_wb, who_wide, annual)

    # Summary
    print("\n" + "=" * 70)
    print("  ✅ DATA PROCESSING COMPLETE")
    print("=" * 70)

    processed_files = os.listdir(PROCESSED_DIR)
    total_size = sum(os.path.getsize(os.path.join(PROCESSED_DIR, f)) for f in processed_files)
    print(f"\n  📁 Files: {len(processed_files)}")
    print(f"  💾 Total size: {total_size / 1024:.1f} KB")
    print(f"\n  Next step: python python/ml/train_model.py")


if __name__ == "__main__":
    main()
