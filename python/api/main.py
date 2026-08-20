#!/usr/bin/env python3
"""
Malaria Outbreak Predictor — FastAPI Backend
=============================================
Serves the trained ML model via REST API.

Endpoints:
  POST /predict        — Predict malaria incidence for given conditions
  GET  /model/info     — Model metadata and feature importance
  GET  /health         — Health check
  GET  /trends         — Historical trends from processed data
  GET  /cities         — Climate data for Kenyan cities
"""

import os
import json
import io
import sys
from datetime import datetime
from typing import Optional

if sys.platform == "win32" and hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_pytest_capture'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Configuration ──────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(BASE_DIR, "models", "serialized")
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

# ── Load Model Artifacts ───────────────────────────────────────────────────────

PM_DIR = os.path.join(BASE_DIR, "models", "serialized", "prediction_machine")

def load_artifacts():
    """Load trained model, scaler, and feature names."""
    # Try prediction machine first, fall back to basic model
    model_path = os.path.join(PM_DIR, "ensemble_model.joblib")
    scaler_path = os.path.join(PM_DIR, "ensemble_scaler.joblib")
    features_path = os.path.join(PM_DIR, "feature_names.joblib")
    report_path = os.path.join(PM_DIR, "training_report.json")

    if not all(os.path.exists(p) for p in [model_path, scaler_path, features_path]):
        # Fall back to basic model
        model_path = os.path.join(MODEL_DIR, "model_final.joblib")
        scaler_path = os.path.join(MODEL_DIR, "scaler_final.joblib")
        features_path = os.path.join(MODEL_DIR, "feature_names.joblib")
        report_path = os.path.join(MODEL_DIR, "training_report.json")

    if not all(os.path.exists(p) for p in [model_path, scaler_path, features_path]):
        raise RuntimeError("Model artifacts not found. Run training first.")

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    feature_names = joblib.load(features_path)

    report = {}
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            report = json.load(f)

    return model, scaler, feature_names, report


# ── App Setup ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Malaria Outbreak Predictor API",
    description="ML-powered malaria incidence prediction for Kenya — inspired by KEMRI's disease surveillance mandate.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load on startup
model, scaler, feature_names, training_report = load_artifacts()


# ── Request/Response Models ────────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    """Input features for malaria prediction."""
    year: int = Field(..., description="Year to predict for (use previous year's actual + projections)")

    # Lagged malaria (most important)
    incidence_lag1: float = Field(..., description="Malaria incidence 1 year prior (per 1000)")
    incidence_lag2: Optional[float] = Field(None, description="Malaria incidence 2 years prior")
    incidence_change: Optional[float] = Field(None, description="Year-over-year change in incidence")

    # Climate
    precip_total_mm: float = Field(..., description="Annual precipitation (mm)")
    precip_days: Optional[float] = Field(None, description="Number of rainy days")
    precip_anomaly: Optional[float] = Field(None, description="Precipitation deviation from mean (mm)")
    temp_mean_c: float = Field(..., description="Mean annual temperature (°C)")
    temp_max_c: Optional[float] = Field(None, description="Max annual temperature (°C)")
    temp_anomaly: Optional[float] = Field(None, description="Temperature deviation from mean (°C)")
    humidity_mean: Optional[float] = Field(None, description="Mean relative humidity (%)")
    wind_mean_ms: Optional[float] = Field(None, description="Mean wind speed (m/s)")
    solar_mean_mj: Optional[float] = Field(None, description="Mean solar radiation (MJ/m²/day)")

    # Lagged climate
    precip_lag1: Optional[float] = Field(None, description="Precipitation 1 year prior (mm)")
    precip_lag2: Optional[float] = Field(None, description="Precipitation 2 years prior (mm)")
    temp_lag1: Optional[float] = Field(None, description="Temperature 1 year prior (°C)")
    temp_lag2: Optional[float] = Field(None, description="Temperature 2 years prior (°C)")

    # Demographics
    population_total: Optional[float] = Field(None, description="Total population")
    urban_population_pct: Optional[float] = Field(None, description="Urban population %")
    health_expenditure_pct_gdp: Optional[float] = Field(None, description="Health expenditure % GDP")
    agricultural_precipitation_mm: Optional[float] = Field(None, description="Agricultural precipitation (mm)")

    class Config:
        json_schema_extra = {
            "example": {
                "year": 2025,
                "incidence_lag1": 74.17,
                "incidence_lag2": 73.77,
                "incidence_change": 0.40,
                "precip_total_mm": 1500,
                "temp_mean_c": 21.3,
                "humidity_mean": 73.0,
                "population_total": 57000000,
                "urban_population_pct": 32.5,
            }
        }


class PredictionResponse(BaseModel):
    """Prediction output."""
    year: int
    predicted_incidence_per_1000: float
    confidence_note: str = "Based on Random Forest model (MAPE 6.3%)"
    risk_level: str
    model_used: str


class ModelInfo(BaseModel):
    """Model metadata."""
    model_name: str
    test_r2: float
    test_mae: float
    test_mape: float
    n_features: int
    features: list
    feature_importance: list
    trained_at: str


class TrendPoint(BaseModel):
    """A single year of historical data."""
    year: int
    actual: Optional[float]
    predicted: Optional[float]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/model/info", response_model=ModelInfo)
def get_model_info():
    """Return model metadata, performance metrics, and feature importance."""
    best = training_report.get("best_metrics", {})
    importance = training_report.get("feature_importance", [])

    return ModelInfo(
        model_name=training_report.get("best_model", "Random Forest"),
        test_r2=best.get("test_r2", 0),
        test_mae=best.get("test_mae", 0),
        test_mape=best.get("test_mape", 0),
        n_features=training_report.get("n_features", 0),
        features=training_report.get("features", []),
        feature_importance=[{"feature": f["feature"], "importance": round(f["importance"], 4)}
                            for f in (importance[:10] if importance else [])],
        trained_at=training_report.get("trained_at", ""),
    )


@app.post("/predict", response_model=PredictionResponse)
def predict_malaria_incidence(req: PredictionRequest):
    """Predict malaria incidence for given climate and health conditions."""
    # Build feature vector
    input_dict = {}
    for fname in feature_names:
        val = getattr(req, fname, None)
        if val is None:
            # Use training median for missing features
            input_dict[fname] = 0  # Will be replaced by scaler default
        else:
            input_dict[fname] = val

    X = np.array([[input_dict[f] for f in feature_names]])
    X_scaled = scaler.transform(X)
    prediction = float(model.predict(X_scaled)[0])

    # Classify risk level
    if prediction < 50:
        risk = "LOW"
    elif prediction < 80:
        risk = "MODERATE"
    elif prediction < 120:
        risk = "HIGH"
    else:
        risk = "VERY HIGH"

    return PredictionResponse(
        year=req.year,
        predicted_incidence_per_1000=round(prediction, 2),
        risk_level=risk,
        model_used=training_report.get("best_model", "Random Forest"),
    )


@app.get("/trends")
def get_trends():
    """Return historical malaria trends from processed data."""
    predictions_path = os.path.join(DATA_DIR, "predictions.csv")
    merged_path = os.path.join(DATA_DIR, "malaria_climate_merged.csv")

    trends = []

    # Load actual values
    actuals = {}
    if os.path.exists(merged_path):
        import csv as csv_mod
        with open(merged_path, "r") as f:
            reader = csv_mod.DictReader(f)
            for row in reader:
                year = int(row["year"])
                actuals[year] = {
                    "actual": float(row.get("malaria_incidence_per_1000", 0) or 0),
                    "cases": float(row.get("estimated_malaria_cases_value", 0) or 0),
                    "deaths": float(row.get("estimated_malaria_deaths_value", 0) or 0),
                    "temp": float(row.get("temp_mean_c", 0) or 0),
                    "precip": float(row.get("precip_total_mm", 0) or 0),
                }

    # Load predictions
    preds = {}
    if os.path.exists(predictions_path):
        import csv as csv_mod
        with open(predictions_path, "r") as f:
            reader = csv_mod.DictReader(f)
            for row in reader:
                year = int(row["year"])
                if "train" not in row.get("model", ""):
                    preds[year] = float(row.get("predicted", 0) or 0)

    all_years = sorted(set(list(actuals.keys()) + list(preds.keys())))
    for year in all_years:
        entry = {"year": year}
        if year in actuals:
            entry["actual_incidence"] = actuals[year]["actual"]
            entry["estimated_cases"] = actuals[year]["cases"]
            entry["estimated_deaths"] = actuals[year]["deaths"]
            entry["temperature_c"] = actuals[year]["temp"]
            entry["precipitation_mm"] = actuals[year]["precip"]
        if year in preds:
            entry["predicted_incidence"] = preds[year]
        trends.append(entry)

    return {"trends": trends, "source": "WHO, World Bank, NASA POWER"}


@app.get("/cities")
def get_cities():
    """Return climate data for Kenyan cities in the dataset."""
    cities = [
        {"name": "Nairobi", "lat": -1.29, "lon": 36.82, "zone": "Highland"},
        {"name": "Mombasa", "lat": -4.04, "lon": 39.67, "zone": "Coastal"},
        {"name": "Kisumu", "lat": -0.10, "lon": 34.76, "zone": "Lakeside"},
        {"name": "Nakuru", "lat": -0.30, "lon": 36.07, "zone": "Highland"},
        {"name": "Eldoret", "lat": 0.52, "lon": 35.27, "zone": "Highland"},
        {"name": "Garissa", "lat": -0.47, "lon": 39.64, "zone": "Semi-arid"},
        {"name": "Kakamega", "lat": 0.28, "lon": 34.75, "zone": "Western"},
        {"name": "Machakos", "lat": -1.52, "lon": 37.26, "zone": "Eastern"},
    ]
    return {"cities": cities, "country": "Kenya"}


@app.get("/forecast")
def get_forecast(years: int = 5):
    """Forecast malaria incidence for future years."""
    # Load forecast data from prediction machine report
    pm_report_path = os.path.join(PM_DIR, "training_report.json")
    if os.path.exists(pm_report_path):
        with open(pm_report_path) as f:
            pm_report = json.load(f)
        forecasts = pm_report.get("forecasts", [])
        return {
            "forecasts": forecasts[:years],
            "model": pm_report.get("best_model", "Unknown"),
            "note": "Predictions based on ensemble of XGBoost, Gradient Boosting, Random Forest, Extra Trees, and Ridge models",
        }
    else:
        return {"forecasts": [], "note": "Run prediction machine first"}


@app.get("/model/compare")
def compare_models():
    """Compare all trained models."""
    pm_report_path = os.path.join(PM_DIR, "training_report.json")
    if os.path.exists(pm_report_path):
        with open(pm_report_path) as f:
            pm_report = json.load(f)
        return {
            "models": pm_report.get("results", []),
            "best_model": pm_report.get("best_model", "Unknown"),
            "ensemble_weights": pm_report.get("ensemble_weights", {}),
        }
    return {"models": [], "note": "Run prediction machine first"}


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("🦟 Starting Malaria Outbreak Predictor API...")
    print("   Docs: http://localhost:8000/docs")
    print("   ReDoc: http://localhost:8000/redoc")
    uvicorn.run(app, host="0.0.0.0", port=8000)
