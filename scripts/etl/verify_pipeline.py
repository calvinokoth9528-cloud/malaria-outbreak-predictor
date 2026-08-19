#!/usr/bin/env python3
"""
Malaria Outbreak Predictor — Pipeline Verification (Python)
=============================================================
Mirrors the R tidyverse pipeline to verify data quality and
generate the same processed output files.

This script is a stopgap until R is installed. Once R is available,
run `Rscript R/data-pipeline/01_load_and_clean.R` instead.
"""

import os
import csv
import io
import sys
from collections import defaultdict
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
PROC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
os.makedirs(PROC_DIR, exist_ok=True)


def read_csv(filename):
    """Read a CSV file and return headers + rows as list of dicts."""
    filepath = os.path.join(RAW_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def write_csv(filename, headers, rows):
    """Write rows to a CSV file."""
    filepath = os.path.join(PROC_DIR, filename)
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"   Saved: {filename} ({len(rows)} rows)")


def safe_float(val):
    """Convert to float, returning None for empty/invalid values."""
    if val is None or val == "" or val == "NA":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def main():
    print("=" * 70)
    print("  Malaria Outbreak Predictor — Pipeline Verification (Python)")
    print("=" * 70)

    # ── 1. Load World Bank Data ────────────────────────────────────────
    print("\n1. Loading World Bank data...")
    wb = read_csv("worldbank_malaria_indicators.csv")
    print(f"   Loaded {len(wb)} rows")

    # Filter out malformed rows (e.g., Somalia with shifted fields)
    valid_indicators = {
        "malaria_incidence_per_1000", "malaria_incidence_total_cases",
        "malaria_mortality_rate", "malaria_deaths",
        "uhc_service_coverage", "annual_precipitation_mm",
        "temperature_anomaly", "health_expenditure_pct_gdp",
        "population_total", "urban_population_pct",
        "agricultural_precipitation_mm"
    }
    # Separate Kenya vs East Africa data
    wb_kenya_only = [r for r in wb if r["indicator"] in valid_indicators and r["iso3"] == "KEN"]
    wb_ea_raw = [r for r in wb if r["indicator"] == "malaria_incidence_per_1000" and r["iso3"] != "KEN"]
    
    indicators = set(r["indicator"] for r in wb_kenya_only)
    print(f"   Kenya indicators: {', '.join(sorted(indicators))}")
    years = sorted(set(r["year"] for r in wb_kenya_only))
    print(f"   Year range: {years[0]} - {years[-1]}")
    print(f"   East Africa rows: {len(wb_ea_raw)}")

    # Pivot Kenya data to wide
    wb_kenya = wb_kenya_only
    by_year = defaultdict(dict)
    for r in wb_kenya:
        by_year[r["year"]][r["indicator"]] = safe_float(r["value"])

    wb_wide = [{"year": y, **by_year[y]} for y in sorted(by_year.keys())]
    wb_headers = ["year"] + sorted(indicators)
    write_csv("worldbank_kenya_annual.csv", wb_headers, wb_wide)

    # East Africa comparison
    ea_headers = ["country", "iso3", "year", "malaria_incidence_per_1000"]
    wb_ea_clean = [{"country": r["country"], "iso3": r["iso3"],
                     "year": r["year"], "malaria_incidence_per_1000": r["value"]}
                    for r in wb_ea_raw]
    write_csv("worldbank_east_africa.csv", ea_headers, wb_ea_clean)
    ea_countries = set(r["country"] for r in wb_ea_raw)
    print(f"   East Africa: {len(wb_ea_clean)} rows, {len(ea_countries)} countries")

    # ── 2. Load WHO Data ───────────────────────────────────────────────
    print("\n2. Loading WHO malaria data...")
    who = read_csv("who_malaria_surveillance.csv")
    print(f"   Loaded {len(who)} rows")

    who_indicators = set(r["indicator"] for r in who)
    print(f"   Indicators: {', '.join(sorted(who_indicators))}")

    who_by_year = defaultdict(dict)
    for r in who:
        y = r["year"]
        ind = r["indicator"]
        who_by_year[y][f"{ind}_value"] = safe_float(r["value"])
        who_by_year[y][f"{ind}_low_ci"] = safe_float(r["low_ci"])
        who_by_year[y][f"{ind}_high_ci"] = safe_float(r["high_ci"])

    who_wide = [{"year": y, **who_by_year[y]} for y in sorted(who_by_year.keys())]
    who_headers = ["year"] + sorted(who_by_year[years[0]].keys()) if who_by_year else ["year"]
    if who_wide:
        who_headers = ["year"] + sorted(k for k in who_wide[0].keys() if k != "year")
    write_csv("who_malaria_annual.csv", who_headers, who_wide)

    # ── 3. Load NASA Climate Data ──────────────────────────────────────
    print("\n3. Loading NASA POWER climate data...")
    climate = read_csv("kenya_climate_daily.csv")
    print(f"   Loaded {len(climate)} daily records")

    cities = sorted(set(r["city"] for r in climate))
    print(f"   Cities: {', '.join(cities)}")

    # Parse dates and clean
    for r in climate:
        date_str = r["date"]
        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            r["date_parsed"] = dt
            r["year"] = dt.year
            r["month"] = dt.month
        except (ValueError, KeyError):
            r["date_parsed"] = None
            r["year"] = None
            r["month"] = None

    climate_valid = [r for r in climate if r["date_parsed"] is not None]

    # Replace sentinel values
    float_fields = ["temperature_c", "precipitation_mm", "humidity_pct",
                    "wind_speed_ms", "solar_radiation_mj"]
    for r in climate_valid:
        for f in float_fields:
            val = safe_float(r[f])
            if val is not None and val < -900:
                r[f] = None
            else:
                r[f] = val

    date_range = sorted(set(r["date_parsed"] for r in climate_valid if r["date_parsed"]))
    print(f"   Date range: {date_range[0].strftime('%Y-%m-%d')} to {date_range[-1].strftime('%Y-%m-%d')}")

    # ── 4. Aggregate to Monthly ────────────────────────────────────────
    print("\n4. Aggregating to monthly summaries...")
    monthly = defaultdict(lambda: defaultdict(list))
    for r in climate_valid:
        key = (r["city"], r["latitude"], r["longitude"], r["year"], r["month"])
        for f in float_fields:
            if r[f] is not None:
                monthly[key][f].append(r[f])

    climate_monthly = []
    for key in sorted(monthly.keys()):
        city, lat, lon, year, month = key
        data = monthly[key]
        row = {
            "city": city, "latitude": lat, "longitude": lon,
            "year": year, "month": month,
        }
        if data.get("temperature_c"):
            temps = data["temperature_c"]
            row["temp_mean_c"] = round(sum(temps) / len(temps), 2)
            row["temp_min_c"] = round(min(temps), 2)
            row["temp_max_c"] = round(max(temps), 2)
            row["temp_range_c"] = round(max(temps) - min(temps), 2)
        if data.get("precipitation_mm"):
            precips = data["precipitation_mm"]
            row["precip_total_mm"] = round(sum(precips), 2)
            row["precip_days"] = sum(1 for p in precips if p > 0.1)
            row["precip_max_day"] = round(max(precips), 2)
        if data.get("humidity_pct"):
            hums = data["humidity_pct"]
            row["humidity_mean"] = round(sum(hums) / len(hums), 2)
        if data.get("wind_speed_ms"):
            winds = data["wind_speed_ms"]
            row["wind_mean_ms"] = round(sum(winds) / len(winds), 2)
        if data.get("solar_radiation_mj"):
            solars = data["solar_radiation_mj"]
            row["solar_mean_mj"] = round(sum(solars) / len(solars), 2)
        climate_monthly.append(row)

    monthly_headers = ["city", "latitude", "longitude", "year", "month",
                       "temp_mean_c", "temp_min_c", "temp_max_c", "temp_range_c",
                       "precip_total_mm", "precip_days", "precip_max_day",
                       "humidity_mean", "wind_mean_ms", "solar_mean_mj"]
    write_csv("climate_monthly.csv", monthly_headers, climate_monthly)
    print(f"   {len(climate_monthly)} monthly records across {len(cities)} cities")

    # ── 5. Aggregate to Annual ─────────────────────────────────────────
    print("\n5. Computing Kenya-wide annual climate averages...")
    annual = defaultdict(lambda: defaultdict(list))
    for r in climate_valid:
        y = r["year"]
        for f in float_fields:
            if r[f] is not None:
                annual[y][f].append(r[f])
        annual[y]["_n_cities"].append(r["city"])

    climate_annual = []
    for year in sorted(annual.keys()):
        data = annual[year]
        row = {"year": year}
        if data.get("temperature_c"):
            row["temp_mean_c"] = round(sum(data["temperature_c"]) / len(data["temperature_c"]), 2)
            row["temp_max_c"] = round(max(data["temperature_c"]), 2)
        if data.get("precipitation_mm"):
            n_cities = len(set(data.get("_n_cities", [1])))
            row["precip_total_mm"] = round(sum(data["precipitation_mm"]) / max(n_cities, 1), 2)
            row["precip_days"] = round(sum(1 for p in data["precipitation_mm"] if p > 0.1) / max(n_cities, 1), 1)
        if data.get("humidity_pct"):
            row["humidity_mean"] = round(sum(data["humidity_pct"]) / len(data["humidity_pct"]), 2)
        if data.get("wind_speed_ms"):
            row["wind_mean_ms"] = round(sum(data["wind_speed_ms"]) / len(data["wind_speed_ms"]), 2)
        if data.get("solar_radiation_mj"):
            row["solar_mean_mj"] = round(sum(data["solar_radiation_mj"]) / len(data["solar_radiation_mj"]), 2)
        row["n_cities"] = len(set(data.get("_n_cities", [])))
        climate_annual.append(row)

    annual_headers = ["year", "temp_mean_c", "temp_max_c", "precip_total_mm", "precip_days",
                      "humidity_mean", "wind_mean_ms", "solar_mean_mj", "n_cities"]
    write_csv("climate_annual_kenya.csv", annual_headers, climate_annual)

    # ── 6. Merge ───────────────────────────────────────────────────────
    print("\n6. Merging all datasets...")
    # Build lookup tables
    wb_lookup = {str(r["year"]): r for r in wb_wide}
    who_lookup = {str(r["year"]): r for r in who_wide}
    climate_lookup = {str(r["year"]): r for r in climate_annual}

    all_years_raw = set(list(wb_lookup.keys()) + list(who_lookup.keys()) + list(climate_lookup.keys()))
    all_years = sorted([int(y) for y in all_years_raw if y and str(y).isdigit()])

    merged = []
    for year in all_years:
        row = {"year": year}
        row.update(wb_lookup.get(str(year), {}))
        row.update(who_lookup.get(str(year), {}))
        row.update(climate_lookup.get(str(year), {}))
        merged.append(row)

    # Get all column names
    all_cols = set()
    for r in merged:
        all_cols.update(r.keys())
    all_cols = sorted(all_cols - {"year"}) + []  # year first
    merged_headers = ["year"] + sorted(c for c in all_cols if c != "year")

    write_csv("malaria_climate_merged.csv", merged_headers, merged)
    print(f"   Merged: {len(merged)} rows × {len(merged_headers)} columns")

    # ── 7. Create ML Features ──────────────────────────────────────────
    print("\n7. Creating lagged features for ML...")
    merged_sorted = sorted(merged, key=lambda r: int(r["year"]))

    ml_features = []
    for i, row in enumerate(merged_sorted):
        ml_row = dict(row)
        year = int(row.get("year", 0))

        # Lagged malaria incidence
        incidence = safe_float(row.get("malaria_incidence_per_1000"))
        if i >= 1 and incidence is not None:
            prev = safe_float(merged_sorted[i-1].get("malaria_incidence_per_1000"))
            if prev is not None:
                ml_row["incidence_lag1"] = prev
                ml_row["incidence_change"] = round(incidence - prev, 2)
                ml_row["incidence_change_pct"] = round(((incidence - prev) / prev) * 100, 2) if prev != 0 else None
        if i >= 2:
            ml_row["incidence_lag2"] = safe_float(merged_sorted[i-2].get("malaria_incidence_per_1000"))

        # Lagged climate
        precip = safe_float(row.get("precip_total_mm"))
        temp = safe_float(row.get("temp_mean_c"))
        if i >= 1:
            if precip is not None:
                ml_row["precip_lag1"] = safe_float(merged_sorted[i-1].get("precip_total_mm"))
            if temp is not None:
                ml_row["temp_lag1"] = safe_float(merged_sorted[i-1].get("temp_mean_c"))
        if i >= 2:
            if precip is not None:
                ml_row["precip_lag2"] = safe_float(merged_sorted[i-2].get("precip_total_mm"))
            if temp is not None:
                ml_row["temp_lag2"] = safe_float(merged_sorted[i-2].get("temp_mean_c"))

        # Anomalies
        all_precips = [safe_float(r.get("precip_total_mm")) for r in merged_sorted]
        all_temps = [safe_float(r.get("temp_mean_c")) for r in merged_sorted]
        valid_precips = [p for p in all_precips if p is not None]
        valid_temps = [t for t in all_temps if t is not None]
        if valid_precips and precip is not None:
            ml_row["precip_anomaly"] = round(precip - sum(valid_precips) / len(valid_precips), 2)
        if valid_temps and temp is not None:
            ml_row["temp_anomaly"] = round(temp - sum(valid_temps) / len(valid_temps), 2)

        ml_features.append(ml_row)

    all_ml_cols = set()
    for r in ml_features:
        all_ml_cols.update(r.keys())
    ml_headers = ["year"] + sorted(c for c in all_ml_cols if c != "year")
    write_csv("malaria_ml_features.csv", ml_headers, ml_features)

    # ── Summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  PIPELINE VERIFICATION COMPLETE")
    print("=" * 70)

    print(f"\n  Output files in: {os.path.abspath(PROC_DIR)}")
    for f in sorted(os.listdir(PROC_DIR)):
        if f.endswith(".csv"):
            filepath = os.path.join(PROC_DIR, f)
            with open(filepath, "r") as fh:
                lines = sum(1 for _ in fh) - 1  # subtract header
            print(f"    {f}: {lines} rows")

    # Data quality
    print("\n  Key variable summaries (merged dataset):")
    key_vars = ["malaria_incidence_per_1000", "precip_total_mm", "temp_mean_c",
                "humidity_mean", "population_total"]
    for var in key_vars:
        vals = [safe_float(r.get(var)) for r in merged]
        vals = [v for v in vals if v is not None]
        if vals:
            print(f"    {var:40s}: n={len(vals):2d}  "
                  f"mean={sum(vals)/len(vals):10.1f}  "
                  f"min={min(vals):10.1f}  max={max(vals):10.1f}")

    print(f"\n  Next step: Build ML models in python/ml/ or R/shiny/")
    print(f"  Dataset ready for: prediction, visualization, Shiny dashboard\n")


if __name__ == "__main__":
    main()
