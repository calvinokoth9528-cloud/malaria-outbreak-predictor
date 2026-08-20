#!/usr/bin/env python3
"""
Malaria Outbreak Predictor — Interactive Dashboard (Streamlit)
================================================================
A fully interactive dashboard for exploring malaria trends,
climate correlations, and ML predictions for Kenya.

Run: streamlit run python/dashboard/app.py
"""

import os
import sys
import io
import json
import warnings
warnings.filterwarnings("ignore")

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
MODEL_DIR = os.path.join(BASE_DIR, "models", "serialized")

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Malaria Outbreak Predictor — Kenya",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1a1a2e; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem; border-radius: 12px; color: white; text-align: center;
    }
    .metric-value { font-size: 2.2rem; font-weight: 700; }
    .metric-label { font-size: 0.9rem; opacity: 0.9; }
    .risk-low { color: #27ae60; }
    .risk-moderate { color: #f39c12; }
    .risk-high { color: #e74c3c; }
    .risk-very-high { color: #c0392b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ── Data Loading ───────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    """Load all processed datasets."""
    data = {}

    files = {
        "merged": "malaria_climate_merged.csv",
        "ml_features": "malaria_ml_features.csv",
        "predictions": "predictions.csv",
        "who_annual": "who_malaria_annual.csv",
        "climate_annual": "climate_annual_kenya.csv",
        "climate_monthly": "climate_monthly.csv",
        "east_africa": "worldbank_east_africa.csv",
        "kenya_wb": "worldbank_kenya_annual.csv",
    }

    for key, filename in files.items():
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            data[key] = pd.read_csv(path)
        else:
            data[key] = pd.DataFrame()

    return data


@st.cache_data
def load_model_info():
    """Load model training report."""
    path = os.path.join(MODEL_DIR, "training_report.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.image("https://em-content.zobj.net/source/twitter/408/mosquito_1f99f.png", width=60)
        st.title("🦟 Malaria Predictor")
        st.caption("KEMRI-Inspired Disease Surveillance")

        st.divider()
        page = st.radio(
            "Navigate",
            ["📊 Overview", "🌡️ Climate Analysis", "🗺️ Regional Comparison",
             "🤖 ML Predictions", "⚡ Risk Simulator", "ℹ️ About"],
            index=0,
        )

        st.divider()
        st.markdown("**Data Sources**")
        st.markdown("""
        - 🏥 WHO Global Health Observatory
        - 🌍 World Bank Open Data
        - 🛰️ NASA POWER Climate API
        """)

        st.divider()
        st.markdown(f"**Author:** Calvin Omondi Okoth")
        st.markdown("[GitHub →](https://github.com/calvinokoth9528-cloud/malaria-outbreak-predictor)")

    return page


# ── Pages ──────────────────────────────────────────────────────────────────────

def page_overview(data):
    """Overview dashboard with key metrics and trends."""
    st.markdown('<p class="main-header">🦟 Malaria in Kenya</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">25 years of disease surveillance data analyzed through machine learning</p>', unsafe_allow_html=True)

    merged = data.get("merged", pd.DataFrame())
    if merged.empty:
        st.warning("No data available. Run the data pipeline first.")
        return

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if "malaria_incidence_per_1000" in merged.columns:
            latest = merged["malaria_incidence_per_1000"].dropna().iloc[-1]
            earliest = merged["malaria_incidence_per_1000"].dropna().iloc[0]
            decline = ((earliest - latest) / earliest) * 100
            st.metric("Malaria Incidence", f"{latest:.1f}/1,000", f"-{decline:.0f}% since 2001")
        else:
            st.metric("Malaria Incidence", "N/A")

    with col2:
        if "estimated_malaria_cases_value" in merged.columns:
            cases = merged["estimated_malaria_cases_value"].dropna().iloc[-1]
            st.metric("Estimated Cases", f"{cases/1e6:.1f}M")
        else:
            st.metric("Estimated Cases", "N/A")

    with col3:
        if "estimated_malaria_deaths_value" in merged.columns:
            deaths = merged["estimated_malaria_deaths_value"].dropna().iloc[-1]
            st.metric("Estimated Deaths", f"{deaths/1e3:.1f}K")
        else:
            st.metric("Estimated Deaths", "N/A")

    with col4:
        st.metric("Data Points", "44,282", "3 API sources")

    st.divider()

    # Main trend chart
    st.subheader("📈 Malaria Incidence Trend (2000–2024)")

    if "malaria_incidence_per_1000" in merged.columns:
        trend_data = merged[["year", "malaria_incidence_per_1000"]].dropna()

        fig = px.line(
            trend_data, x="year", y="malaria_incidence_per_1000",
            markers=True,
            labels={"malaria_incidence_per_1000": "Cases per 1,000 at risk", "year": "Year"},
        )
        fig.update_traces(
            line=dict(color="#e74c3c", width=3),
            marker=dict(size=8, color="#e74c3c"),
            hovertemplate="<b>%{x}</b><br>Incidence: %{y:.1f}/1,000<extra></extra>",
        )
        fig.update_layout(
            plot_bgcolor="white", height=450,
            xaxis=dict(gridcolor="#eee"), yaxis=dict(gridcolor="#eee"),
        )

        # Add trendline
        z = np.polyfit(trend_data["year"], trend_data["malaria_incidence_per_1000"], 1)
        p = np.poly1d(z)
        fig.add_scatter(
            x=trend_data["year"], y=p(trend_data["year"]),
            mode="lines", name="Trend",
            line=dict(dash="dash", color="#3498db", width=2),
        )

        st.plotly_chart(fig, use_container_width=True)

    # Two-column layout
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🌡️ Climate vs Malaria")
        if "malaria_incidence_per_1000" in merged.columns and "precip_total_mm" in merged.columns:
            climate_data = merged[["year", "malaria_incidence_per_1000", "precip_total_mm", "temp_mean_c"]].dropna()
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(x=climate_data["year"], y=climate_data["malaria_incidence_per_1000"],
                           name="Malaria", line=dict(color="#e74c3c", width=2)),
                secondary_y=False,
            )
            fig.add_trace(
                go.Bar(x=climate_data["year"], y=climate_data["precip_total_mm"],
                       name="Rainfall (mm)", marker_color="#3498db", opacity=0.5),
                secondary_y=True,
            )
            fig.update_layout(height=400, plot_bgcolor="white", title="Malaria vs Rainfall")
            fig.update_yaxes(title_text="Malaria (per 1,000)", secondary_y=False)
            fig.update_yaxes(title_text="Rainfall (mm)", secondary_y=True)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("🗺️ East Africa Comparison")
        ea = data.get("east_africa", pd.DataFrame())
        if not ea.empty and "value" in ea.columns:
            ea_clean = ea[["country", "year", "value"]].dropna()
            ea_clean["year"] = pd.to_numeric(ea_clean["year"], errors="coerce")
            ea_clean["value"] = pd.to_numeric(ea_clean["value"], errors="coerce")
            ea_clean = ea_clean.dropna()

            fig = px.line(
                ea_clean, x="year", y="value", color="country",
                labels={"value": "Cases per 1,000", "year": "Year", "country": "Country"},
            )
            fig.update_layout(height=400, plot_bgcolor="white", title="East Africa Malaria Trends")
            st.plotly_chart(fig, use_container_width=True)


def page_climate(data):
    """Climate analysis page."""
    st.markdown('<p class="main-header">🌡️ Climate Analysis</p>', unsafe_allow_html=True)
    st.markdown("How temperature, rainfall, and humidity correlate with malaria in Kenya")

    climate = data.get("climate_annual", pd.DataFrame())
    monthly = data.get("climate_monthly", pd.DataFrame())

    if climate.empty:
        st.warning("No climate data available.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Annual Rainfall")
        if "precip_total_mm" in climate.columns:
            fig = px.bar(
                climate, x="year", y="precip_total_mm",
                color="precip_total_mm",
                color_continuous_scale="Blues",
                labels={"precip_total_mm": "Rainfall (mm)"},
            )
            fig.update_layout(height=350, plot_bgcolor="white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Temperature Trend")
        if "temp_mean_c" in climate.columns:
            fig = px.line(
                climate, x="year", y="temp_mean_c",
                markers=True,
                labels={"temp_mean_c": "Temperature (°C)"},
            )
            fig.update_traces(line=dict(color="#e74c3c", width=2))
            fig.update_layout(height=350, plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

    # Climate heatmap
    st.subheader("📅 Monthly Climate Heatmap")
    if not monthly.empty and "month" in monthly.columns:
        city_filter = st.selectbox("Select City", monthly["city"].unique(), index=0)
        city_data = monthly[monthly["city"] == city_filter]

        pivot_temp = city_data.pivot_table(index="month", columns="year", values="temp_mean_c")
        pivot_precip = city_data.pivot_table(index="month", columns="year", values="precip_total_mm")

        col1, col2 = st.columns(2)
        with col1:
            fig = px.imshow(
                pivot_temp, labels=dict(x="Year", y="Month", color="°C"),
                title=f"Temperature — {city_filter.title()}",
                color_continuous_scale="RdYlBu_r",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.imshow(
                pivot_precip, labels=dict(x="Year", y="Month", color="mm"),
                title=f"Precipitation — {city_filter.title()}",
                color_continuous_scale="Blues",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


def page_regional(data):
    """Regional comparison page."""
    st.markdown('<p class="main-header">🗺️ Regional Comparison</p>', unsafe_allow_html=True)
    st.markdown("How Kenya compares to other East African countries")

    ea = data.get("east_africa", pd.DataFrame())
    if ea.empty:
        st.warning("No regional data available.")
        return

    ea_clean = ea[["country", "year", "value"]].dropna()
    ea_clean["year"] = pd.to_numeric(ea_clean["year"], errors="coerce")
    ea_clean["value"] = pd.to_numeric(ea_clean["value"], errors="coerce")
    ea_clean = ea_clean.dropna()

    # Interactive country filter
    countries = sorted(ea_clean["country"].unique())
    selected = st.multiselect("Select Countries", countries, default=["Kenya", "Uganda", "Tanzania", "Ethiopia"])

    if selected:
        filtered = ea_clean[ea_clean["country"].isin(selected)]

        fig = px.line(
            filtered, x="year", y="value", color="country",
            markers=True,
            labels={"value": "Malaria Incidence (per 1,000)", "year": "Year"},
        )
        fig.update_layout(height=500, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

        # Latest comparison
        st.subheader("📊 Latest Year Comparison")
        latest_year = filtered["year"].max()
        latest = filtered[filtered["year"] == latest_year].sort_values("value", ascending=False)

        fig = px.bar(
            latest, x="country", y="value", color="country",
            labels={"value": f"Malaria Incidence ({int(latest_year)})", "country": "Country"},
        )
        fig.update_layout(height=350, plot_bgcolor="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def page_predictions(data):
    """ML predictions page."""
    st.markdown('<p class="main-header">🤖 ML Predictions</p>', unsafe_allow_html=True)

    # Try prediction machine report first
    pm_path = os.path.join(MODEL_DIR, "prediction_machine", "training_report.json")
    model_info = {}
    if os.path.exists(pm_path):
        with open(pm_path) as f:
            model_info = json.load(f)
    else:
        model_info = load_model_info()

    if not model_info:
        st.warning("No model info available. Run training first.")
        return

    # Model metrics
    best = model_info.get("best_metrics", {})
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Best Model", model_info.get("best_model", "N/A"))
    with col2:
        st.metric("R² Score", f"{best.get('test_r2', 0):.3f}")
    with col3:
        st.metric("MAE", f"{best.get('test_mae', 0):.2f}")
    with col4:
        mape = best.get("test_mape", 0)
        st.metric("MAPE", f"{mape:.1f}%" if mape else "N/A")

    st.divider()

    # Model comparison
    st.subheader("📊 Model Comparison")
    results = model_info.get("results", [])
    if results:
        comp_df = pd.DataFrame(results)
        comp_df = comp_df.sort_values("test_mae")
        fig = px.bar(
            comp_df, x="name", y="test_mae",
            color="test_r2", color_continuous_scale="RdYlGn",
            labels={"test_mae": "Mean Absolute Error", "name": "Model", "test_r2": "R² Score"},
        )
        fig.update_layout(height=350, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    # Forecasts
    st.subheader("🔮 Future Predictions (5-Year Forecast)")
    forecasts = model_info.get("forecasts", [])
    if forecasts:
        fc_df = pd.DataFrame(forecasts)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fc_df["year"], y=fc_df["predicted_incidence"],
            mode="markers+lines+text", name="Forecast",
            line=dict(color="#e74c3c", width=3),
            marker=dict(size=10),
            text=[f"{v:.1f}" for v in fc_df["predicted_incidence"]],
            textposition="top center",
        ))
        # Confidence interval
        if "lower_bound" in fc_df.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([fc_df["year"], fc_df["year"].iloc[::-1]]),
                y=pd.concat([fc_df["upper_bound"], fc_df["lower_bound"].iloc[::-1]]),
                fill="toself", fillcolor="rgba(231,76,60,0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                name="95% Confidence",
            ))
        fig.update_layout(height=400, plot_bgcolor="white", title="Malaria Incidence Forecast")
        st.plotly_chart(fig, use_container_width=True)

        # Forecast table
        st.dataframe(fc_df, use_container_width=True)

    # Feature importance
    st.subheader("🔍 Feature Importance")
    importance = model_info.get("feature_importance", [])
    if importance:
        imp_df = pd.DataFrame(importance)
        fig = px.bar(
            imp_df, x="importance", y="feature", orientation="h",
            color="importance", color_continuous_scale="Reds",
        )
        fig.update_layout(height=400, plot_bgcolor="white", yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)


def page_simulator(data):
    """Risk simulator page."""
    st.markdown('<p class="main-header">⚡ Risk Simulator</p>', unsafe_allow_html=True)
    st.markdown("Adjust climate and health parameters to see predicted malaria risk")

    model_info = load_model_info()
    if not model_info:
        st.warning("No model available. Run training first.")
        return

    st.divider()

    # Input controls
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📋 Malaria History")
        incidence_lag1 = st.slider("Incidence last year (per 1,000)", 0.0, 300.0, 74.0, 1.0)
        incidence_lag2 = st.slider("Incidence 2 years ago", 0.0, 300.0, 73.0, 1.0)
        incidence_change = incidence_lag1 - incidence_lag2

    with col2:
        st.subheader("🌡️ Climate")
        precip_total = st.slider("Annual rainfall (mm)", 200.0, 3000.0, 1500.0, 50.0)
        temp_mean = st.slider("Mean temperature (°C)", 15.0, 30.0, 22.0, 0.5)
        humidity = st.slider("Humidity (%)", 30.0, 95.0, 70.0, 1.0)

    with col3:
        st.subheader("👥 Demographics")
        population = st.slider("Population (millions)", 20.0, 70.0, 55.0, 1.0) * 1e6
        urban_pct = st.slider("Urban population (%)", 15.0, 50.0, 28.0, 0.5)
        health_exp = st.slider("Health expenditure (% GDP)", 2.0, 8.0, 4.5, 0.1)

    # Predict button
    if st.button("🔮 Predict Malaria Risk", type="primary", use_container_width=True):
        try:
            import joblib
            model = joblib.load(os.path.join(MODEL_DIR, "model_final.joblib"))
            scaler = joblib.load(os.path.join(MODEL_DIR, "scaler_final.joblib"))
            feature_names = joblib.load(os.path.join(MODEL_DIR, "feature_names.joblib"))

            # Build input
            defaults = {
                "incidence_lag1": incidence_lag1,
                "incidence_lag2": incidence_lag2,
                "incidence_change": incidence_change,
                "precip_total_mm": precip_total,
                "temp_mean_c": temp_mean,
                "humidity_mean": humidity,
                "population_total": population,
                "urban_population_pct": urban_pct,
                "health_expenditure_pct_gdp": health_exp,
                "precip_days": precip_total / 10,
                "precip_anomaly": 0,
                "temp_max_c": temp_mean + 8,
                "temp_anomaly": 0,
                "wind_mean_ms": 3.0,
                "solar_mean_mj": 18.0,
                "precip_lag1": precip_total * 0.95,
                "precip_lag2": precip_total * 1.05,
                "temp_lag1": temp_mean - 0.2,
                "temp_lag2": temp_mean + 0.1,
                "agricultural_precipitation_mm": precip_total * 0.6,
            }

            X = np.array([[defaults.get(f, 0) for f in feature_names]])
            X_scaled = scaler.transform(X)
            prediction = float(model.predict(X_scaled)[0])

            # Risk classification
            if prediction < 50:
                risk = "LOW"
                risk_color = "green"
                risk_emoji = "🟢"
            elif prediction < 80:
                risk = "MODERATE"
                risk_color = "orange"
                risk_emoji = "🟡"
            elif prediction < 120:
                risk = "HIGH"
                risk_color = "red"
                risk_emoji = "🔴"
            else:
                risk = "VERY HIGH"
                risk_color = "darkred"
                risk_emoji = "⛔"

            st.divider()
            st.subheader(f"{risk_emoji} Prediction Result")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Predicted Incidence", f"{prediction:.1f}", "per 1,000 at risk")
            with col2:
                st.metric("Risk Level", risk)
            with col3:
                st.metric("Model Used", model_info.get("best_model", "Random Forest"))

            # Gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prediction,
                title={"text": "Malaria Risk Score"},
                gauge={
                    "axis": {"range": [0, 200]},
                    "bar": {"color": risk_color},
                    "steps": [
                        {"range": [0, 50], "color": "#d4edda"},
                        {"range": [50, 80], "color": "#fff3cd"},
                        {"range": [80, 120], "color": "#f8d7da"},
                        {"range": [120, 200], "color": "#f5c6cb"},
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 4},
                        "thickness": 0.75,
                        "value": prediction,
                    },
                },
            ))
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Prediction failed: {e}")


def page_about():
    """About page."""
    st.markdown('<p class="main-header">ℹ️ About This Project</p>', unsafe_allow_html=True)

    st.markdown("""
    ### 🦟 Malaria Outbreak Predictor

    A **KEMRI-inspired** machine learning system for predicting malaria outbreak risk in Kenya.

    #### What It Does
    - Fetches real-time data from 3 global APIs (WHO, World Bank, NASA)
    - Analyzes 44,000+ data points across 8 Kenyan cities
    - Trains multiple ML models (Ridge, Random Forest, Gradient Boosting, XGBoost)
    - Predicts malaria incidence 1-2 years ahead

    #### Key Findings
    - Malaria incidence dropped **68%** since 2001 (243 → 74 per 1,000)
    - **Rainfall** is the #1 climate predictor with a 2-month lag
    - **Urbanization** is inversely correlated with malaria risk
    - Last year's incidence is the single best predictor of next year's burden

    #### Tech Stack
    | Component | Technology |
    |-----------|-----------|
    | Data Pipeline | Python (pandas, numpy) |
    | Machine Learning | scikit-learn, XGBoost |
    | API | FastAPI, Uvicorn |
    | Dashboard | Streamlit, Plotly |
    | R Dashboard | Shiny, ggplot2, plotly |
    | DevOps | Docker, GitHub Actions |

    #### Author
    **Calvin Omondi Okoth**
    - GitHub: [calvinokoth9528-cloud](https://github.com/calvinokoth9528-cloud)
    - LinkedIn: [calvin-klein-9528c2004](https://www.linkedin.com/in/calvin-klein-9528c2004)

    #### License
    MIT License — see [LICENSE](LICENSE) for details.
    """)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    data = load_data()
    page = render_sidebar()

    if page == "📊 Overview":
        page_overview(data)
    elif page == "🌡️ Climate Analysis":
        page_climate(data)
    elif page == "🗺️ Regional Comparison":
        page_regional(data)
    elif page == "🤖 ML Predictions":
        page_predictions(data)
    elif page == "⚡ Risk Simulator":
        page_simulator(data)
    elif page == "ℹ️ About":
        page_about()


if __name__ == "__main__":
    main()
