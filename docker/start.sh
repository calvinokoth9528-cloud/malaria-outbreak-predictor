#!/bin/bash
# ==============================================================================
# Malaria Outbreak Predictor — Docker Startup Script
# ==============================================================================
# Starts both the FastAPI backend (port 8000) and R Shiny dashboard (port 3838)
# ==============================================================================

set -e

echo "================================================================"
echo "  Malaria Outbreak Predictor"
echo "  Starting services..."
echo "================================================================"

# Start FastAPI in background
echo "  Starting FastAPI on port 8000..."
cd /app
python -m uvicorn python.api.main:app --host 0.0.0.0 --port 8000 &

# Start R Shiny in background
echo "  Starting Shiny on port 3838..."
cd /app
Rscript -e "shiny::runApp('R/shiny', port=3838, host='0.0.0.0')" &

echo ""
echo "  Services started:"
echo "    FastAPI:  http://localhost:8000/docs"
echo "    Shiny:    http://localhost:3838"
echo ""

# Wait for both processes
wait
