#!/usr/bin/env python3
"""
Malaria Outbreak Predictor — Data Fetcher
==========================================
Downloads publicly available malaria surveillance and climate data
from World Bank, WHO, and NASA POWER APIs.

Data Sources:
  1. World Bank — Malaria incidence, climate indicators, health spending
  2. WHO Global Health Observatory — Malaria confirmed cases & deaths
  3. NASA POWER — Daily temperature and precipitation for Kenya

All data is publicly available and free to use.
"""

import os
import sys
import json
import time
import io
import urllib.request
import urllib.parse
from datetime import datetime

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Configuration ──────────────────────────────────────────────────────────────
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
METADATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "metadata")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

# Kenya ISO3 code
KENYA_ISO3 = "KEN"
KENYA_ISO2 = "KE"

# Countries in East Africa for comparison context
EAST_AFRICA = ["KEN", "UGA", "TZA", "RWA", "ETH", "SSD", "SOM", "BDI", "MOZ", "MWI"]


def fetch_json(url, description=""):
    """Fetch JSON from a URL with basic error handling."""
    print(f"  📡 Fetching: {description or url[:80]}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MalariaPredictor/1.0 (research)"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(f"     ✅ Success")
            return data
    except Exception as e:
        print(f"     ❌ Error: {e}")
        return None


def save_csv_from_wb(data, filename, value_name="value"):
    """Convert World Bank API JSON response to CSV."""
    filepath = os.path.join(RAW_DIR, filename)
    rows = []
    if data and "countries" in data:
        for country_data in data["countries"]:
            country_name = country_data.get("country", {}).get("value", "")
            country_iso3 = country_data.get("countryiso3code", "")
            for item in country_data.get("dates", []):
                rows.append({
                    "country": country_name,
                    "iso3": country_iso3,
                    "year": item.get("date", ""),
                    value_name: item.get("value", ""),
                })
    elif isinstance(data, list):
        for item in data:
            rows.append(item)

    # Validate: skip rows where year is not a 4-digit number
    valid_rows = []
    for row in rows:
        year_val = str(row.get("year", "")).strip()
        if year_val.isdigit() and len(year_val) == 4:
            valid_rows.append(row)
        else:
            print(f"     ⚠️  Skipping malformed row: year={year_val!r}")
    rows = valid_rows

    if rows:
        headers = list(rows[0].keys())
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for row in rows:
                f.write(",".join(str(row.get(h, "")) for h in headers) + "\n")
        print(f"     💾 Saved {len(rows)} rows → {filename}")
    else:
        print(f"     ⚠️  No data to save for {filename}")
    return rows


# ── 1. World Bank Data ─────────────────────────────────────────────────────────

def fetch_worldbank_malaria():
    """Fetch malaria-related indicators from the World Bank API."""
    print("\n🦟 Fetching World Bank Malaria Data...")
    
    indicators = {
        "SH.MLR.INCD.P3": "malaria_incidence_per_1000",
        "SH.MLR.INCD": "malaria_incidence_total_cases",
        "SH.MLR.MORT": "malaria_mortality_rate",
        "SH.MLR.DTHS": "malaria_deaths",
        "SH.UHC.SRVS.CV.XD": "uhc_service_coverage",
    }
    
    all_data = {}
    for indicator_code, name in indicators.items():
        # Fetch for Kenya specifically
        url = (f"https://api.worldbank.org/v2/country/{KENYA_ISO3}"
               f"/indicator/{indicator_code}?format=json&per_page=100&date=2000:2024")
        data = fetch_json(url, f"WB {name}")
        
        if data and len(data) > 1 and data[1]:
            rows = []
            for item in data[1]:
                rows.append({
                    "country": "Kenya",
                    "iso3": KENYA_ISO3,
                    "year": item.get("date", ""),
                    "indicator": name,
                    "value": item.get("value", ""),
                })
            all_data[name] = rows
            print(f"     📊 {name}: {len(rows)} data points (Kenya)")
        
        time.sleep(0.3)  # Be nice to the API
    
    # Fetch for East Africa comparison
    for indicator_code, name in [("SH.MLR.INCD.P3", "malaria_incidence_per_1000")]:
        country_str = ";".join(EAST_AFRICA)
        url = (f"https://api.worldbank.org/v2/country/{country_str}"
               f"/indicator/{indicator_code}?format=json&per_page=500&date=2000:2024")
        data = fetch_json(url, f"WB {name} (East Africa)")
        
        if data and len(data) > 1 and data[1]:
            rows = []
            for item in data[1]:
                year_val = item.get("date", "")
                iso3_val = item.get("countryiso3code", "")
                # Validate: year must be 4-digit, iso3 must be 3-letter alpha
                if (str(year_val).strip().isdigit() and len(str(year_val).strip()) == 4
                        and iso3_val and len(iso3_val.strip()) == 3 and iso3_val.strip().isalpha()):
                    rows.append({
                        "country": item.get("country", {}).get("value", ""),
                        "iso3": iso3_val.strip(),
                        "year": str(year_val).strip(),
                        "indicator": name,
                        "value": item.get("value", ""),
                    })
            all_data[f"{name}_east_africa"] = rows
            print(f"     📊 {name} (East Africa): {len(rows)} data points")
        time.sleep(0.3)
    
    # Also fetch climate & health spending indicators
    extra_indicators = {
        "EN.ATM.PREC.MM": "annual_precipitation_mm",
        "EN.ATM.FTEMP.ZD": "temperature_anomaly",
        "SH.XPD.CHEX.GD.ZS": "health_expenditure_pct_gdp",
        "SP.POP.TOTL": "population_total",
        "SP.URB.TOTL.IN.ZS": "urban_population_pct",
        "AG.LND.PRCP.MM": "agricultural_precipitation_mm",
    }
    
    for indicator_code, name in extra_indicators.items():
        url = (f"https://api.worldbank.org/v2/country/{KENYA_ISO3}"
               f"/indicator/{indicator_code}?format=json&per_page=100&date=2000:2024")
        data = fetch_json(url, f"WB {name}")
        
        if data and len(data) > 1 and data[1]:
            rows = []
            for item in data[1]:
                rows.append({
                    "country": "Kenya",
                    "iso3": KENYA_ISO3,
                    "year": item.get("date", ""),
                    "indicator": name,
                    "value": item.get("value", ""),
                })
            all_data[name] = rows
            print(f"     📊 {name}: {len(rows)} data points")
        time.sleep(0.3)
    
    # Save all World Bank data
    filepath = os.path.join(RAW_DIR, "worldbank_malaria_indicators.csv")
    all_rows = []
    for name, rows in all_data.items():
        all_rows.extend(rows)
    
    # Validate: filter out rows with malformed data (e.g., shifted fields from API quirks)
    valid_rows = []
    for row in all_rows:
        year_val = str(row.get("year", "")).strip()
        iso3_val = str(row.get("iso3", "")).strip()
        if (year_val.isdigit() and len(year_val) == 4
                and iso3_val.isalpha() and len(iso3_val) == 3):
            valid_rows.append(row)
        else:
            print(f"     ⚠️  Skipping malformed row: year={year_val!r}, iso3={iso3_val!r}")
    all_rows = valid_rows
    
    if all_rows:
        headers = ["country", "iso3", "year", "indicator", "value"]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for row in all_rows:
                f.write(",".join(str(row.get(h, "")) for h in headers) + "\n")
        print(f"\n  💾 Saved World Bank data: {len(all_rows)} total rows → worldbank_malaria_indicators.csv")
    
    return all_data


# ── 2. WHO Global Health Observatory Data ──────────────────────────────────────

def fetch_who_malaria():
    """Fetch malaria data from the WHO Global Health Observatory API."""
    print("\n🏥 Fetching WHO Malaria Data...")
    
    # WHO GHO OData API
    base_url = "https://ghoapi.azureedge.net/api"
    
    # Key malaria indicators
    who_indicators = {
        "MALARIA_EST_INCIDENCE": "estimated_incidence_per_1000_at_risk",
        "MALARIA_EST_CASES": "estimated_malaria_cases",
        "MALARIA_EST_DEATHS": "estimated_malaria_deaths",
        "MALARIA_CONF Cases": "confirmed_malaria_cases",
        "MAL_RDT": "rapid_diagnostic_tests_performed",
        "MAL_ARTEM": "artemisinin_based_treatments",
    }
    
    all_who_data = {}
    
    for indicator_code, name in who_indicators.items():
        # Fetch for Kenya (URL-encode the OData filter)
        filter_str = f"SpatialDim eq '{KENYA_ISO3}'"
        encoded_filter = urllib.parse.quote(filter_str, safe="")
        url = f"{base_url}/{indicator_code}?$filter={encoded_filter}"
        data = fetch_json(url, f"WHO {name}")
        
        if data and "value" in data:
            rows = []
            for item in data["value"]:
                rows.append({
                    "country": "Kenya",
                    "iso3": KENYA_ISO3,
                    "year": item.get("TimeDim", ""),
                    "indicator": name,
                    "value": item.get("NumericValue", ""),
                    "low_ci": item.get("Low", ""),
                    "high_ci": item.get("High", ""),
                    "value_type": item.get("Value", ""),
                })
            all_who_data[name] = rows
            print(f"     📊 {name}: {len(rows)} data points")
        
        time.sleep(0.3)
    
    # Save WHO data
    filepath = os.path.join(RAW_DIR, "who_malaria_surveillance.csv")
    all_rows = []
    for name, rows in all_who_data.items():
        all_rows.extend(rows)
    
    if all_rows:
        headers = ["country", "iso3", "year", "indicator", "value", "low_ci", "high_ci", "value_type"]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for row in all_rows:
                f.write(",".join(str(row.get(h, "")) for h in headers) + "\n")
        print(f"\n  💾 Saved WHO data: {len(all_rows)} total rows → who_malaria_surveillance.csv")
    
    return all_who_data


# ── 3. NASA POWER Climate Data ─────────────────────────────────────────────────

def fetch_nasa_power_climate():
    """Fetch climate data (temp, precip) for Kenya from NASA POWER API."""
    print("\n🌡️  Fetching NASA POWER Climate Data for Kenya...")
    
    # Kenya bounding box (approximate)
    # Kenya: lat -4.7 to 5.0, lon 34.0 to 42.0
    # Nairobi: -1.29, 36.82 (as reference point)
    # Use a grid of points across Kenya
    
    kenya_points = {
        "nairobi": (-1.29, 36.82),
        "mombasa": (-4.04, 39.67),
        "kisumu": (-0.10, 34.76),
        "nakuru": (-0.30, 36.07),
        "eldoret": (0.52, 35.27),
        "garissa": (-0.47, 39.64),
        "kakamega": (0.28, 34.75),
        "machakos": (-1.52, 37.26),
    }
    
    all_climate = {}
    
    for city, (lat, lon) in kenya_points.items():
        url = (f"https://power.larc.nasa.gov/api/temporal/daily/point"
               f"?parameters=T2M,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN"
               f"&community=AG"
               f"&longitude={lon}&latitude={lat}"
               f"&start=20100101&end=20241231"
               f"&format=JSON")
        
        data = fetch_json(url, f"NASA POWER {city}")
        
        if data and "properties" in data:
            params = data["properties"].get("parameter", {})
            times = data["properties"].get("times", {})
            
            if params:
                # Get all dates
                temp_data = params.get("T2M", {})
                precip_data = params.get("PRECTOTCORR", {})
                humidity_data = params.get("RH2M", {})
                wind_data = params.get("WS2M", {})
                solar_data = params.get("ALLSKY_SFC_SW_DWN", {})
                
                all_dates = sorted(set(list(temp_data.keys()) + list(precip_data.keys())))
                
                rows = []
                for date_key in all_dates:
                    if date_key == "-999.0":
                        continue
                    rows.append({
                        "city": city,
                        "latitude": lat,
                        "longitude": lon,
                        "date": date_key,
                        "temperature_c": temp_data.get(date_key, ""),
                        "precipitation_mm": precip_data.get(date_key, ""),
                        "humidity_pct": humidity_data.get(date_key, ""),
                        "wind_speed_ms": wind_data.get(date_key, ""),
                        "solar_radiation_mj": solar_data.get(date_key, ""),
                    })
                
                all_climate[city] = rows
                print(f"     📊 {city}: {len(rows)} daily records")
        
        time.sleep(0.5)  # Be nice to NASA
    
    # Save climate data
    filepath = os.path.join(RAW_DIR, "kenya_climate_daily.csv")
    all_rows = []
    for city, rows in all_climate.items():
        all_rows.extend(rows)
    
    if all_rows:
        headers = ["city", "latitude", "longitude", "date", 
                    "temperature_c", "precipitation_mm", "humidity_pct",
                    "wind_speed_ms", "solar_radiation_mj"]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for row in all_rows:
                f.write(",".join(str(row.get(h, "")) for h in headers) + "\n")
        print(f"\n  💾 Saved climate data: {len(all_rows)} total rows → kenya_climate_daily.csv")
    
    return all_climate


# ── 4. Metadata & Summary ─────────────────────────────────────────────────────

def save_metadata():
    """Save metadata about all fetched datasets."""
    metadata = {
        "project": "Malaria Outbreak Predictor",
        "fetched_at": datetime.now().isoformat(),
        "datasets": {
            "worldbank_malaria_indicators.csv": {
                "source": "World Bank Open Data API",
                "url": "https://data.worldbank.org/",
                "license": "Creative Commons Attribution 4.0 (CC BY 4.0)",
                "description": "Malaria incidence, mortality, and related health/climate indicators for Kenya",
                "indicators": [
                    "SH.MLR.INCD.P3 - Malaria incidence per 1000 at risk",
                    "SH.MLR.INCD - Malaria incidence (total cases)",
                    "SH.MLR.MORT - Malaria mortality rate",
                    "SH.MLR.DTHS - Malaria deaths",
                    "EN.ATM.PREC.MM - Annual precipitation",
                    "EN.ATM.FTEMP.ZD - Temperature anomaly",
                    "SH.XPD.CHEX.GD.ZS - Health expenditure % GDP",
                    "SP.POP.TOTL - Total population",
                ],
                "temporal_coverage": "2000-2024",
                "spatial_coverage": "Kenya + East Africa comparison",
            },
            "who_malaria_surveillance.csv": {
                "source": "WHO Global Health Observatory (GHO) API",
                "url": "https://ghoapi.azureedge.net/",
                "license": "Open access - WHO",
                "description": "WHO estimated malaria cases, deaths, and intervention data for Kenya",
                "indicators": [
                    "Estimated incidence per 1000 population at risk",
                    "Estimated number of malaria cases",
                    "Estimated number of malaria deaths",
                    "Confirmed malaria cases",
                    "Rapid diagnostic tests performed",
                    "Artemisinin-based combination therapy treatments",
                ],
                "temporal_coverage": "2000-2023",
                "spatial_coverage": "Kenya",
            },
            "kenya_climate_daily.csv": {
                "source": "NASA POWER API (Prediction Of Worldwide Energy Resources)",
                "url": "https://power.larc.nasa.gov/",
                "license": "Public domain (NASA)",
                "description": "Daily climate data (temperature, precipitation, humidity, wind, solar radiation) for 8 cities in Kenya",
                "parameters": [
                    "T2M - Temperature at 2 meters (°C)",
                    "PRECTOTCORR - Precipitation (mm/day)",
                    "RH2M - Relative Humidity at 2 meters (%)",
                    "WS2M - Wind Speed at 2 meters (m/s)",
                    "ALLSKY_SFC_SW_DWN - Solar Radiation (MJ/m²/day)",
                ],
                "temporal_coverage": "2010-2024",
                "spatial_coverage": "8 cities across Kenya (Nairobi, Mombasa, Kisumu, Nakuru, Eldoret, Garissa, Kakamega, Machakos)",
            },
        },
        "usage_notes": [
            "All datasets are publicly available and free to use",
            "World Bank data is under CC BY 4.0 license",
            "WHO data is open access",
            "NASA POWER data is public domain",
            "For commercial use, verify individual dataset licenses",
            "Cite original sources in any publications",
        ],
    }
    
    filepath = os.path.join(METADATA_DIR, "dataset_metadata.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"\n📋 Saved dataset metadata → metadata/dataset_metadata.json")
    return metadata


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("🦟 Malaria Outbreak Predictor — Data Fetcher")
    print("=" * 70)
    print(f"Output directory: {os.path.abspath(RAW_DIR)}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Fetch all datasets
    wb_data = fetch_worldbank_malaria()
    who_data = fetch_who_malaria()
    climate_data = fetch_nasa_power_climate()
    
    # Save metadata
    save_metadata()
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ DATA FETCH COMPLETE")
    print("=" * 70)
    
    total_rows = sum(len(rows) for rows in wb_data.values())
    total_rows += sum(len(rows) for rows in who_data.values())
    total_rows += sum(len(rows) for rows in climate_data.values())
    
    print(f"\n📊 Total data points fetched: {total_rows:,}")
    print(f"📁 Files saved to: {os.path.abspath(RAW_DIR)}")
    print(f"\nNext steps:")
    print(f"  1. Run the R data pipeline: Rscript R/data-pipeline/01_load_and_clean.R")
    print(f"  2. Explore the data: Rscript R/visualization/02_eda.R")
    print(f"  3. Start building the Shiny dashboard")


if __name__ == "__main__":
    main()
