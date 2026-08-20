# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Malaria Outbreak Predictor — Makefile
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Quick Start:
#   make setup        — Install all dependencies
#   make pipeline     — Run full pipeline (fetch → process → train)
#   make serve        — Start the API server
#   make dashboard    — Start the Streamlit dashboard
#   make test         — Run all tests
#   make all          — Run everything
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

.PHONY: setup fetch process train serve dashboard test clean all pipeline docker

# Default target
all: pipeline

# ── Setup ──────────────────────────────────────────────────────────────────────

setup:
	@echo "🦟 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Setup complete"

# ── Data Pipeline ──────────────────────────────────────────────────────────────

fetch:
	@echo "📡 Fetching data from WHO, World Bank, NASA..."
	python scripts/etl/fetch_malaria_data.py

process:
	@echo "⚙️  Processing raw data into ML features..."
	python python/etl/process_data.py

train:
	@echo "🤖 Training ML models..."
	python python/ml/train_model.py

pipeline: fetch process train
	@echo "🎉 Pipeline complete!"

# ── Serve ──────────────────────────────────────────────────────────────────────

serve:
	@echo "🚀 Starting API server at http://localhost:8000"
	python -m uvicorn python.api.main:app --reload --host 0.0.0.0 --port 8000

dashboard:
	@echo "📊 Starting Streamlit dashboard at http://localhost:8501"
	streamlit run python/dashboard/app.py

# ── Test ───────────────────────────────────────────────────────────────────────

test:
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v

# ── Docker ─────────────────────────────────────────────────────────────────────

docker:
	@echo "🐳 Building Docker image..."
	docker-compose -f docker/docker-compose.yml up --build

# ── Clean ──────────────────────────────────────────────────────────────────────

clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf data/processed/*.csv
	rm -rf models/serialized/*.joblib models/serialized/*.json
	rm -rf __pycache__ python/**/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	@echo "✅ Clean complete"

# ── Help ───────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "🦟 Malaria Outbreak Predictor — Available Commands"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "  make setup        Install all dependencies"
	@echo "  make fetch        Fetch data from APIs"
	@echo "  make process      Process raw data → ML features"
	@echo "  make train        Train ML models"
	@echo "  make pipeline     Run full pipeline (fetch → process → train)"
	@echo "  make serve        Start FastAPI server (port 8000)"
	@echo "  make dashboard    Start Streamlit dashboard (port 8501)"
	@echo "  make test         Run test suite"
	@echo "  make docker       Build and run Docker containers"
	@echo "  make clean        Remove generated files"
	@echo "  make all          Run full pipeline + serve"
	@echo ""
