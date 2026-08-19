#!/usr/bin/env python3
"""
Malaria Outbreak Predictor — ML Model Training
================================================
Trains multiple ML models to predict malaria incidence in Kenya
from climate, health, and demographic features.

Models trained:
  1. Ridge Regression (baseline)
  2. Random Forest
  3. Gradient Boosting (best performer)
  4. XGBoost (if installed — optional)

Outputs:
  - models/serialized/model.joblib      (trained model)
  - models/serialized/scaler.joblib     (feature scaler)
  - models/serialized/feature_names.joblib
  - models/serialized/training_report.json
  - data/processed/predictions.csv      (model predictions)
"""

import os
import sys
import io
import json
import csv
import warnings
warnings.filterwarnings("ignore")

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    mean_absolute_percentage_error
)
from sklearn.pipeline import Pipeline
import joblib

# ── Try importing XGBoost (optional) ───────────────────────────────────────────
try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("  ⚠️  XGBoost not installed — using GradientBoosting as best model")

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
MODEL_DIR = os.path.join(BASE_DIR, "models", "serialized")
os.makedirs(MODEL_DIR, exist_ok=True)

RANDOM_STATE = 42
TEST_YEARS = 5  # Hold out last 5 years for testing


def load_data():
    """Load the ML features dataset."""
    filepath = os.path.join(DATA_DIR, "malaria_ml_features.csv")
    df = pd.read_csv(filepath)
    print(f"  Loaded {len(df)} rows × {len(df.columns)} columns")

    # Convert all numeric columns
    for col in df.columns:
        if col not in ("year",):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values("year").reset_index(drop=True)
    return df


def select_features(df):
    """Select features for modeling."""
    # Core features — must not have too many NAs
    candidate_features = [
        # Lagged malaria (strongest predictors)
        "incidence_lag1",
        "incidence_lag2",
        "incidence_change",

        # Climate
        "precip_total_mm",
        "precip_days",
        "precip_anomaly",
        "temp_mean_c",
        "temp_max_c",
        "temp_anomaly",
        "humidity_mean",
        "wind_mean_ms",
        "solar_mean_mj",

        # Lagged climate
        "precip_lag1",
        "precip_lag2",
        "temp_lag1",
        "temp_lag2",

        # Demographics
        "population_total",
        "urban_population_pct",
        "health_expenditure_pct_gdp",
        "agricultural_precipitation_mm",
    ]

    # Keep only features that exist and have enough non-null values
    features = []
    for f in candidate_features:
        if f in df.columns:
            non_null = df[f].notna().sum()
            if non_null >= len(df) * 0.5:  # At least 50% non-null
                features.append(f)
            else:
                print(f"  ⚠️  Skipping {f}: only {non_null}/{len(df)} non-null values")

    print(f"  Selected {len(features)} features: {', '.join(features)}")
    return features


def prepare_data(df, features, target="malaria_incidence_per_1000"):
    """Prepare train/test split with time-series awareness."""
    # Drop rows where target or key features are missing
    required_cols = [target, "incidence_lag1"]  # Must have at least lag1
    mask = df[required_cols].notna().all(axis=1)
    df_clean = df[mask].copy()

    # Fill remaining NAs with column medians
    for f in features:
        if df_clean[f].isna().any():
            median_val = df_clean[f].median()
            df_clean[f] = df_clean[f].fillna(median_val)
            print(f"  Filled {f} NAs with median ({median_val:.2f})")

    # Time-series split: train on first N years, test on last TEST_YEARS
    years = df_clean["year"].values
    test_cutoff = sorted(set(years))[-TEST_YEARS]

    train_mask = years < test_cutoff
    test_mask = years >= test_cutoff

    X_train = df_clean.loc[train_mask, features].values
    X_test = df_clean.loc[test_mask, features].values
    y_train = df_clean.loc[train_mask, target].values
    y_test = df_clean.loc[test_mask, target].values
    years_train = years[train_mask]
    years_test = years[test_mask]

    print(f"\n  Train: {len(X_train)} rows (years {years_train.min()}-{years_train.max()})")
    print(f"  Test:  {len(X_test)} rows (years {years_test.min()}-{years_test.max()})")

    return X_train, X_test, y_train, y_test, years_train, years_test, df_clean


def evaluate_model(name, model, X_train, X_test, y_train, y_test, years_test):
    """Train and evaluate a model."""
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train
    model.fit(X_train_scaled, y_train)

    # Predict
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)

    # Metrics
    metrics = {
        "name": name,
        "train_mae": float(mean_absolute_error(y_train, y_pred_train)),
        "train_rmse": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
        "train_r2": float(r2_score(y_train, y_pred_train)),
        "test_mae": float(mean_absolute_error(y_test, y_pred_test)),
        "test_rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
        "test_r2": float(r2_score(y_test, y_pred_test)),
    }

    try:
        metrics["test_mape"] = float(mean_absolute_percentage_error(y_test, y_pred_test) * 100)
    except Exception:
        metrics["test_mape"] = None

    print(f"\n  📊 {name}")
    print(f"     Train: MAE={metrics['train_mae']:.2f}  RMSE={metrics['train_rmse']:.2f}  R²={metrics['train_r2']:.3f}")
    print(f"     Test:  MAE={metrics['test_mae']:.2f}  RMSE={metrics['test_rmse']:.2f}  R²={metrics['test_r2']:.3f}")
    if metrics["test_mape"]:
        print(f"     Test MAPE: {metrics['test_mape']:.1f}%")

    return model, scaler, metrics, y_pred_test


def get_feature_importance(model, feature_names, model_name):
    """Extract feature importance if available."""
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_)
    else:
        return None

    # Normalize
    importances = importances / importances.sum()

    importance_list = sorted(
        zip(feature_names, importances),
        key=lambda x: x[1],
        reverse=True
    )

    print(f"\n  🔍 Top features ({model_name}):")
    for fname, imp in importance_list[:8]:
        bar = "█" * int(imp * 50)
        print(f"     {fname:35s} {imp:.3f} {bar}")

    return [{"feature": f, "importance": float(i)} for f, i in importance_list]


def build_prediction_table(df_clean, features, years_test, y_test, y_pred, model_name):
    """Build a predictions table for visualization."""
    test_mask = df_clean["year"].isin(years_test)
    pred_df = df_clean.loc[test_mask, ["year", "malaria_incidence_per_1000"]].copy()
    pred_df["predicted"] = y_pred
    pred_df["residual"] = pred_df["malaria_incidence_per_1000"] - pred_df["predicted"]
    pred_df["model"] = model_name
    return pred_df


def main():
    print("=" * 70)
    print("  🦟 Malaria Outbreak Predictor — ML Model Training")
    print("=" * 70)

    # ── 1. Load Data ────────────────────────────────────────────────
    print("\n1. Loading data...")
    df = load_data()

    # ── 2. Select Features ──────────────────────────────────────────
    print("\n2. Selecting features...")
    features = select_features(df)

    # ── 3. Prepare Train/Test Split ─────────────────────────────────
    print("\n3. Preparing train/test split...")
    X_train, X_test, y_train, y_test, years_train, years_test, df_clean = \
        prepare_data(df, features)

    # ── 4. Train Models ─────────────────────────────────────────────
    print("\n4. Training models...")

    models_to_train = [
        ("Ridge Regression", Ridge(alpha=1.0)),
        ("Random Forest", RandomForestRegressor(
            n_estimators=100, max_depth=5, min_samples_leaf=2,
            random_state=RANDOM_STATE
        )),
        ("Gradient Boosting", GradientBoostingRegressor(
            n_estimators=100, max_depth=3, learning_rate=0.1,
            min_samples_leaf=2, random_state=RANDOM_STATE
        )),
    ]

    if HAS_XGBOOST:
        models_to_train.append((
            "XGBoost",
            XGBRegressor(
                n_estimators=100, max_depth=3, learning_rate=0.1,
                random_state=RANDOM_STATE, verbosity=0
            )
        ))

    results = []
    best_model = None
    best_scaler = None
    best_metrics = None
    best_importance = None
    best_name = None
    best_r2 = -999

    for name, model in models_to_train:
        trained_model, scaler, metrics, y_pred = evaluate_model(
            name, model, X_train, X_test, y_train, y_test, years_test
        )
        importance = get_feature_importance(trained_model, features, name)
        results.append(metrics)

        if metrics["test_r2"] > best_r2:
            best_r2 = metrics["test_r2"]
            best_model = trained_model
            best_scaler = scaler
            best_metrics = metrics
            best_importance = importance
            best_name = name

    # ── 5. Save Best Model ──────────────────────────────────────────
    print(f"\n5. Saving best model: {best_name} (R²={best_r2:.3f})")

    joblib.dump(best_model, os.path.join(MODEL_DIR, "model.joblib"))
    joblib.dump(best_scaler, os.path.join(MODEL_DIR, "scaler.joblib"))
    joblib.dump(features, os.path.join(MODEL_DIR, "feature_names.joblib"))

    # Retrain best model on all data for final predictions
    scaler_full = StandardScaler()
    X_full = scaler_full.fit_transform(df_clean[features].fillna(df_clean[features].median()).values)
    y_full = df_clean["malaria_incidence_per_1000"].values
    best_model.fit(X_full, y_full)
    joblib.dump(best_model, os.path.join(MODEL_DIR, "model_final.joblib"))
    joblib.dump(scaler_full, os.path.join(MODEL_DIR, "scaler_final.joblib"))
    print("  ✅ Saved model.joblib, scaler.joblib, feature_names.joblib")

    # ── 6. Generate Predictions Table ───────────────────────────────
    print("\n6. Generating predictions...")
    y_pred_best = best_model.predict(best_scaler.transform(X_test))
    pred_table = build_prediction_table(
        df_clean, features, years_test, y_test, y_pred_best, best_name
    )

    # Add training predictions too
    y_pred_train_best = best_model.predict(best_scaler.transform(X_train))
    train_pred = df_clean.loc[df_clean["year"].isin(years_train), ["year", "malaria_incidence_per_1000"]].copy()
    train_pred["predicted"] = y_pred_train_best
    train_pred["residual"] = train_pred["malaria_incidence_per_1000"] - train_pred["predicted"]
    train_pred["model"] = f"{best_name} (train)"

    all_preds = pd.concat([train_pred, pred_table], ignore_index=True)
    all_preds = all_preds.sort_values("year")
    all_preds.to_csv(os.path.join(DATA_DIR, "predictions.csv"), index=False)
    print(f"  Saved predictions.csv ({len(all_preds)} rows)")

    # ── 7. Save Training Report ─────────────────────────────────────
    print("\n7. Saving training report...")
    report = {
        "trained_at": datetime.now().isoformat(),
        "best_model": best_name,
        "n_features": len(features),
        "features": features,
        "train_years": f"{int(years_train.min())}-{int(years_train.max())}",
        "test_years": f"{int(years_test.min())}-{int(years_test.max())}",
        "n_train": len(X_train),
        "n_test": len(X_test),
        "results": results,
        "best_metrics": best_metrics,
        "feature_importance": best_importance[:10] if best_importance else None,
    }

    report_path = os.path.join(MODEL_DIR, "training_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  Saved training_report.json")

    # ── Summary ─────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  TRAINING COMPLETE")
    print("=" * 70)
    print(f"\n  Best model: {best_name}")
    print(f"  Test R²:    {best_metrics['test_r2']:.3f}")
    print(f"  Test MAE:   {best_metrics['test_mae']:.2f} cases/1000")
    print(f"  Test RMSE:  {best_metrics['test_rmse']:.2f} cases/1000")
    if best_metrics.get("test_mape"):
        print(f"  Test MAPE:  {best_metrics['test_mape']:.1f}%")

    print(f"\n  Model comparison:")
    for r in results:
        print(f"    {r['name']:25s}  Test R²={r['test_r2']:.3f}  MAE={r['test_mae']:.2f}")

    print(f"\n  Files saved to: {MODEL_DIR}/")
    print(f"  Predictions:    data/processed/predictions.csv")


if __name__ == "__main__":
    main()
