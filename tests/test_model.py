#!/usr/bin/env python3
"""
Tests for the Malaria Outbreak Predictor.
Run: python -m pytest tests/ -v
"""

import os
import sys
import json
import pytest

# Add project root to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

MODEL_DIR = os.path.join(BASE_DIR, "models", "serialized")
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")


# ── Model Tests ────────────────────────────────────────────────────────────────

class TestModel:
    """Test that the trained model loads and predicts correctly."""

    def test_model_files_exist(self):
        """All model artifacts should exist."""
        required = ["model_final.joblib", "scaler_final.joblib", "feature_names.joblib"]
        for f in required:
            path = os.path.join(MODEL_DIR, f)
            assert os.path.exists(path), f"Missing: {f}"

    def test_model_loads(self):
        """Model should load without errors."""
        import joblib
        model = joblib.load(os.path.join(MODEL_DIR, "model_final.joblib"))
        assert model is not None
        assert hasattr(model, "predict")

    def test_scaler_loads(self):
        """Scaler should load without errors."""
        import joblib
        scaler = joblib.load(os.path.join(MODEL_DIR, "scaler_final.joblib"))
        assert scaler is not None
        assert hasattr(scaler, "transform")

    def test_feature_names_load(self):
        """Feature names should load and be a list."""
        import joblib
        features = joblib.load(os.path.join(MODEL_DIR, "feature_names.joblib"))
        assert isinstance(features, list)
        assert len(features) > 0

    def test_prediction_shape(self):
        """Model should return a single prediction."""
        import joblib
        import numpy as np

        model = joblib.load(os.path.join(MODEL_DIR, "model_final.joblib"))
        scaler = joblib.load(os.path.join(MODEL_DIR, "scaler_final.joblib"))
        features = joblib.load(os.path.join(MODEL_DIR, "feature_names.joblib"))

        X = np.zeros((1, len(features)))
        X_scaled = scaler.transform(X)
        pred = model.predict(X_scaled)

        assert len(pred) == 1
        assert isinstance(float(pred[0]), float)

    def test_prediction_range(self):
        """Prediction should be in a reasonable range (0-500 per 1,000)."""
        import joblib
        import numpy as np

        model = joblib.load(os.path.join(MODEL_DIR, "model_final.joblib"))
        scaler = joblib.load(os.path.join(MODEL_DIR, "scaler_final.joblib"))
        features = joblib.load(os.path.join(MODEL_DIR, "feature_names.joblib"))

        X = np.zeros((1, len(features)))
        X_scaled = scaler.transform(X)
        pred = float(model.predict(X_scaled)[0])

        assert 0 <= pred <= 500, f"Prediction {pred} out of range"


# ── Data Tests ─────────────────────────────────────────────────────────────────

class TestData:
    """Test that processed data files exist and are valid."""

    def test_ml_features_exist(self):
        path = os.path.join(DATA_DIR, "malaria_ml_features.csv")
        assert os.path.exists(path), "malaria_ml_features.csv missing"

    def test_ml_features_readable(self):
        import pandas as pd
        path = os.path.join(DATA_DIR, "malaria_ml_features.csv")
        df = pd.read_csv(path)
        assert len(df) > 0
        assert "year" in df.columns

    def test_predictions_exist(self):
        path = os.path.join(DATA_DIR, "predictions.csv")
        assert os.path.exists(path), "predictions.csv missing"

    def test_merged_data_exists(self):
        path = os.path.join(DATA_DIR, "malaria_climate_merged.csv")
        assert os.path.exists(path), "malaria_climate_merged.csv missing"

    def test_training_report_exists(self):
        path = os.path.join(MODEL_DIR, "training_report.json")
        assert os.path.exists(path), "training_report.json missing"

    def test_training_report_valid(self):
        path = os.path.join(MODEL_DIR, "training_report.json")
        with open(path) as f:
            report = json.load(f)
        assert "best_model" in report
        assert "best_metrics" in report
        assert "test_r2" in report["best_metrics"]


# ── API Tests ──────────────────────────────────────────────────────────────────

class TestAPI:
    """Test the FastAPI endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi.testclient import TestClient
        from python.api.main import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Health check should return healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_model_info_endpoint(self, client):
        """Model info should return valid metadata."""
        response = client.get("/model/info")
        assert response.status_code == 200
        data = response.json()
        assert "model_name" in data
        assert "test_r2" in data
        assert "features" in data

    def test_cities_endpoint(self, client):
        """Cities endpoint should return Kenyan cities."""
        response = client.get("/cities")
        assert response.status_code == 200
        data = response.json()
        assert len(data["cities"]) == 8

    def test_trends_endpoint(self, client):
        """Trends endpoint should return historical data."""
        response = client.get("/trends")
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data

    def test_predict_endpoint(self, client):
        """Prediction should work with valid input."""
        payload = {
            "year": 2025,
            "incidence_lag1": 74.0,
            "incidence_lag2": 73.0,
            "incidence_change": 1.0,
            "precip_total_mm": 1500,
            "temp_mean_c": 22.0,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "predicted_incidence_per_1000" in data
        assert "risk_level" in data
        assert data["risk_level"] in ["LOW", "MODERATE", "HIGH", "VERY HIGH"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
