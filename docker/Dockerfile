# ==============================================================================
# Malaria Outbreak Predictor — Multi-Stage Docker Build
# ==============================================================================
# Stage 1: Python ML + API
# Stage 2: R Shiny Dashboard
# Stage 3: Combined production image
# ==============================================================================

# ── Stage 1: Python ML & API ──────────────────────────────────────────────────

FROM python:3.11-slim AS python-stage

WORKDIR /app

# Install Python dependencies
COPY python/api/ python/api/
COPY python/ml/ python/ml/
COPY models/serialized/ models/serialized/
COPY data/processed/ data/processed/
COPY scripts/etl/ scripts/etl/

COPY python/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt || \
    pip install --no-cache-dir fastapi uvicorn scikit-learn joblib numpy pandas

EXPOSE 8000

# ── Stage 2: R Shiny ──────────────────────────────────────────────────────────

FROM rocker/shiny:4.3.2 AS r-stage

WORKDIR /srv/shiny-server

# Install R packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

RUN R -e "install.packages(c('tidyverse', 'plotly', 'DT', 'scales', 'shinydashboard'), \
    repos='https://cloud.r-project.org', dependencies=TRUE)"

# Copy app files
COPY R/shiny/ /srv/shiny-server/malaria-predictor/
COPY data/processed/ /srv/shiny-server/malaria-predictor/data/processed/

EXPOSE 3838

# ── Stage 3: Production ───────────────────────────────────────────────────────

FROM python:3.11-slim AS production

WORKDIR /app

# Install Python
COPY python/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt || \
    pip install --no-cache-dir fastapi uvicorn scikit-learn joblib numpy pandas

# Copy Python API
COPY python/api/ python/api/
COPY python/ml/ python/ml/
COPY models/serialized/ models/serialized/
COPY data/processed/ data/processed/

# Install R (lightweight)
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    r-cran-tidyverse \
    && rm -rf /var/lib/apt/lists/*

# Install R Shiny
RUN R -e "install.packages(c('shiny', 'plotly', 'DT', 'scales', 'shinydashboard'), \
    repos='https://cloud.r-project.org')"

# Copy R app
COPY R/shiny/ /app/R/shiny/
COPY data/processed/ /app/data/processed/

# Copy startup script
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 8000 3838

CMD ["/app/start.sh"]
