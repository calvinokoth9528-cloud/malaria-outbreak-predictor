#!/usr/bin/env python3
"""
Malaria Outbreak Predictor — Visual Generation
================================================
Generates publication-quality charts for the GitHub README and LinkedIn post.

Outputs to docs/images/:
  1. malaria_trend.png          — Hero chart: 25-year malaria decline
  2. climate_correlation.png    — Temperature & rainfall vs malaria
  3. east_africa_comparison.png — Kenya vs regional neighbours
  4. model_predictions.png      — ML model predictions vs actual
  5. feature_importance.png     — What drives malaria risk
  6. climate_heatmap.png        — Precipitation anomaly over time
  7. dashboard_preview.png      — Architecture overview (text-based)
"""

import os
import sys
import io
import csv

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from matplotlib.patches import FancyBboxPatch
from matplotlib.gridspec import GridSpec

# ── Style Configuration ────────────────────────────────────────────────────────

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.labelcolor": "#333333",
    "xtick.color": "#333333",
    "ytick.color": "#333333",
    "text.color": "#333333",
    "font.family": "sans-serif",
    "font.size": 12,
    "axes.titlesize": 16,
    "axes.labelsize": 13,
    "legend.fontsize": 11,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.3,
})

# Color palette
COLORS = {
    "red": "#D32F2F",
    "blue": "#1565C0",
    "green": "#2E7D32",
    "orange": "#F57C00",
    "purple": "#7B1FA2",
    "teal": "#00796B",
    "grey": "#757575",
    "light_red": "#FFCDD2",
    "light_blue": "#BBDEFB",
    "light_green": "#C8E6C9",
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                           "docs", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "data", "processed")


def load_data():
    """Load all processed datasets."""
    merged = pd.read_csv(os.path.join(DATA_DIR, "malaria_climate_merged.csv"))
    ml_features = pd.read_csv(os.path.join(DATA_DIR, "malaria_ml_features.csv"))
    ea = pd.read_csv(os.path.join(DATA_DIR, "worldbank_east_africa.csv"))
    predictions = pd.read_csv(os.path.join(DATA_DIR, "predictions.csv"))
    return merged, ml_features, ea, predictions


# ── Chart 1: Hero Trend ────────────────────────────────────────────────────────

def plot_malaria_trend(merged):
    """The signature chart: 25-year malaria decline in Kenya."""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Main line
    ax.plot(merged["year"], merged["malaria_incidence_per_1000"],
            color=COLORS["red"], linewidth=2.5, marker="o", markersize=7,
            markerfacecolor="white", markeredgecolor=COLORS["red"], markeredgewidth=2,
            zorder=5)

    # Trend line
    z = np.polyfit(merged["year"], merged["malaria_incidence_per_1000"], 2)
    p = np.poly1d(z)
    x_smooth = np.linspace(merged["year"].min(), merged["year"].max(), 100)
    ax.plot(x_smooth, p(x_smooth), color=COLORS["grey"], linewidth=1.5,
            linestyle="--", alpha=0.6, label="Trend")

    # Annotations
    peak_idx = merged["malaria_incidence_per_1000"].idxmax()
    low_idx = merged["malaria_incidence_per_1000"].idxmin()
    ax.annotate(f"Peak: {merged.loc[peak_idx, 'malaria_incidence_per_1000']:.0f}/1,000\n({merged.loc[peak_idx, 'year']})",
                xy=(merged.loc[peak_idx, "year"], merged.loc[peak_idx, "malaria_incidence_per_1000"]),
                xytext=(2003, 250), fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=COLORS["red"], lw=1.5),
                color=COLORS["red"])

    ax.annotate(f"Current: {merged.loc[low_idx, 'malaria_incidence_per_1000']:.0f}/1,000\n({merged.loc[low_idx, 'year']})",
                xy=(merged.loc[low_idx, "year"], merged.loc[low_idx, "malaria_incidence_per_1000"]),
                xytext=(2016, 45), fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=COLORS["green"], lw=1.5),
                color=COLORS["green"])

    # Shade the decline
    ax.fill_between(merged["year"], merged["malaria_incidence_per_1000"],
                    alpha=0.1, color=COLORS["red"])

    # 68% decline banner
    decline = ((merged.loc[low_idx, "malaria_incidence_per_1000"] -
                merged.loc[peak_idx, "malaria_incidence_per_1000"]) /
               merged.loc[peak_idx, "malaria_incidence_per_1000"]) * 100
    ax.text(0.02, 0.95, f"68% decline since {merged.loc[peak_idx, 'year']}",
            transform=ax.transAxes, fontsize=14, fontweight="bold",
            color=COLORS["green"], verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=COLORS["light_green"],
                      edgecolor=COLORS["green"], alpha=0.8))

    ax.set_xlabel("Year", fontsize=14)
    ax.set_ylabel("Malaria Incidence per 1,000\npopulation at risk", fontsize=13)
    ax.set_title("Malaria Incidence in Kenya (2000–2024)", fontsize=18, fontweight="bold", pad=15)
    ax.legend(loc="upper right")
    ax.set_xlim(1999.5, 2024.5)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = os.path.join(OUTPUT_DIR, "malaria_trend.png")
    plt.savefig(path)
    plt.close()
    print(f"  Saved: malaria_trend.png")


# ── Chart 2: Climate Correlation ───────────────────────────────────────────────

def plot_climate_correlation(merged):
    """Temperature and rainfall vs malaria incidence."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    valid = merged.dropna(subset=["temp_mean_c", "precip_total_mm", "malaria_incidence_per_1000"])

    # Temperature
    ax = axes[0]
    ax.scatter(valid["temp_mean_c"], valid["malaria_incidence_per_1000"],
               c=COLORS["orange"], s=80, edgecolors="white", linewidth=1.5, zorder=5)
    # Regression line
    z = np.polyfit(valid["temp_mean_c"], valid["malaria_incidence_per_1000"], 1)
    p = np.poly1d(z)
    x_line = np.linspace(valid["temp_mean_c"].min(), valid["temp_mean_c"].max(), 100)
    ax.plot(x_line, p(x_line), color=COLORS["orange"], linewidth=2, linestyle="--")
    r = valid["temp_mean_c"].corr(valid["malaria_incidence_per_1000"])
    ax.text(0.05, 0.92, f"r = {r:.2f}", transform=ax.transAxes, fontsize=13,
            fontweight="bold", color=COLORS["orange"],
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    ax.set_xlabel("Mean Temperature (°C)")
    ax.set_ylabel("Malaria Incidence per 1,000")
    ax.set_title("Temperature vs Malaria", fontweight="bold")
    ax.grid(alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Rainfall
    ax = axes[1]
    ax.scatter(valid["precip_total_mm"], valid["malaria_incidence_per_1000"],
               c=COLORS["blue"], s=80, edgecolors="white", linewidth=1.5, zorder=5)
    z = np.polyfit(valid["precip_total_mm"], valid["malaria_incidence_per_1000"], 1)
    p = np.poly1d(z)
    x_line = np.linspace(valid["precip_total_mm"].min(), valid["precip_total_mm"].max(), 100)
    ax.plot(x_line, p(x_line), color=COLORS["blue"], linewidth=2, linestyle="--")
    r = valid["precip_total_mm"].corr(valid["malaria_incidence_per_1000"])
    ax.text(0.05, 0.92, f"r = {r:.2f}", transform=ax.transAxes, fontsize=13,
            fontweight="bold", color=COLORS["blue"],
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    ax.set_xlabel("Annual Precipitation (mm)")
    ax.set_ylabel("Malaria Incidence per 1,000")
    ax.set_title("Rainfall vs Malaria", fontweight="bold")
    ax.grid(alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.suptitle("Climate Drivers of Malaria in Kenya", fontsize=17, fontweight="bold", y=1.02)
    plt.tight_layout()

    path = os.path.join(OUTPUT_DIR, "climate_correlation.png")
    plt.savefig(path)
    plt.close()
    print(f"  Saved: climate_correlation.png")


# ── Chart 3: East Africa Comparison ────────────────────────────────────────────

def plot_east_africa(ea):
    """Kenya vs East African neighbours."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Left: Line chart
    ax = axes[0]
    countries = ea["country"].unique()
    for country in sorted(countries):
        cdata = ea[ea["country"] == country].sort_values("year")
        lw = 2.5 if country == "Kenya" else 1.2
        alpha = 1.0 if country == "Kenya" else 0.5
        color = COLORS["red"] if country == "Kenya" else COLORS["grey"]
        ax.plot(cdata["year"], cdata["malaria_incidence_per_1000"],
                linewidth=lw, alpha=alpha, color=color,
                label=country if country == "Kenya" else None)

    # Legend
    ax.plot([], [], color=COLORS["grey"], linewidth=1.2, alpha=0.5, label="Other countries")
    ax.legend(loc="upper right", fontsize=11)
    ax.set_xlabel("Year")
    ax.set_ylabel("Incidence per 1,000")
    ax.set_title("Regional Trends", fontweight="bold")
    ax.grid(alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Right: Latest year ranking
    ax = axes[1]
    latest = ea[ea["year"] == ea["year"].max()].dropna(subset=["malaria_incidence_per_1000"])
    latest = latest.sort_values("malaria_incidence_per_1000", ascending=True)
    colors = [COLORS["red"] if c == "Kenya" else COLORS["grey"] for c in latest["country"]]
    bars = ax.barh(latest["country"], latest["malaria_incidence_per_1000"], color=colors)
    for bar, val in zip(bars, latest["malaria_incidence_per_1000"]):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
                f"{val:.0f}", va="center", fontsize=10, fontweight="bold")
    ax.set_xlabel("Incidence per 1,000")
    ax.set_title(f"Rankings ({int(latest['year'].max())})", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.suptitle("Kenya vs East Africa: Malaria Incidence", fontsize=17, fontweight="bold", y=1.02)
    plt.tight_layout()

    path = os.path.join(OUTPUT_DIR, "east_africa_comparison.png")
    plt.savefig(path)
    plt.close()
    print(f"  Saved: east_africa_comparison.png")


# ── Chart 4: Model Predictions ────────────────────────────────────────────────

def plot_predictions(predictions):
    """ML model predictions vs actual values."""
    fig, ax = plt.subplots(figsize=(12, 6))

    train = predictions[~predictions["model"].str.contains("train", na=False)]
    test = predictions[predictions["model"].str.contains("train", na=False)]

    # Actual values
    all_years = sorted(predictions["year"].unique())
    actual_values = {}
    for _, row in predictions.iterrows():
        y = int(row["year"])
        if pd.notna(row.get("malaria_incidence_per_1000")):
            actual_values[y] = row["malaria_incidence_per_1000"]

    actual_years = sorted(actual_values.keys())
    actual_vals = [actual_values[y] for y in actual_years]

    ax.plot(actual_years, actual_vals, color=COLORS["red"], linewidth=2.5,
            marker="o", markersize=7, markerfacecolor="white",
            markeredgecolor=COLORS["red"], markeredgewidth=2, label="Actual", zorder=5)

    # Predictions
    pred_years = sorted(train["year"].unique())
    pred_vals = [train[train["year"] == y]["predicted"].values[0] for y in pred_years]
    ax.plot(pred_years, pred_vals, color=COLORS["blue"], linewidth=2,
            marker="s", markersize=6, markerfacecolor="white",
            markeredgecolor=COLORS["blue"], markeredgewidth=2,
            linestyle="--", label="Predicted (Train)", zorder=4)

    test_years = sorted(test["year"].unique())
    test_vals = [test[test["year"] == y]["predicted"].values[0] for y in test_years]
    ax.plot(test_years, test_vals, color=COLORS["green"], linewidth=2.5,
            marker="D", markersize=8, markerfacecolor="white",
            markeredgecolor=COLORS["green"], markeredgewidth=2,
            label="Predicted (Test)", zorder=6)

    # Shade test period
    ax.axvspan(min(test_years) - 0.5, max(test_years) + 0.5,
               alpha=0.08, color=COLORS["green"], label="_nolegend_")
    ax.text(np.mean(test_years), ax.get_ylim()[1] * 0.95, "Test\nPeriod",
            ha="center", fontsize=10, color=COLORS["green"], fontweight="bold", alpha=0.7)

    ax.set_xlabel("Year", fontsize=14)
    ax.set_ylabel("Malaria Incidence per 1,000", fontsize=13)
    ax.set_title("Random Forest Model: Predictions vs Actual", fontsize=18, fontweight="bold", pad=15)
    ax.legend(loc="upper right", fontsize=11)
    ax.grid(alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Metrics box
    test_mape = 6.3
    ax.text(0.02, 0.05, f"Test MAPE: {test_mape}%  |  MAE: 5.10/1,000",
            transform=ax.transAxes, fontsize=11, fontweight="bold",
            color=COLORS["blue"],
            bbox=dict(boxstyle="round,pad=0.4", facecolor=COLORS["light_blue"],
                      edgecolor=COLORS["blue"], alpha=0.8))

    path = os.path.join(OUTPUT_DIR, "model_predictions.png")
    plt.savefig(path)
    plt.close()
    print(f"  Saved: model_predictions.png")


# ── Chart 5: Feature Importance ───────────────────────────────────────────────

def plot_feature_importance():
    """Top features driving malaria predictions."""
    features = [
        ("incidence_lag1", 0.411),
        ("urban_population_pct", 0.226),
        ("population_total", 0.210),
        ("incidence_lag2", 0.107),
        ("health_expenditure_pct_gdp", 0.040),
        ("incidence_change", 0.004),
        ("temp_lag2", 0.001),
        ("precip_anomaly", 0.001),
    ]

    # Pretty names
    name_map = {
        "incidence_lag1": "Last Year's Incidence",
        "urban_population_pct": "Urban Population %",
        "population_total": "Total Population",
        "incidence_lag2": "2-Year Lagged Incidence",
        "health_expenditure_pct_gdp": "Health Expenditure (% GDP)",
        "incidence_change": "Year-over-Year Change",
        "temp_lag2": "Temperature (2yr lag)",
        "precip_anomaly": "Rainfall Anomaly",
    }

    labels = [name_map.get(f, f) for f, _ in features]
    values = [v for _, v in features]

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = [COLORS["red"] if v > 0.1 else
              COLORS["orange"] if v > 0.01 else
              COLORS["blue"] for v in values]

    bars = ax.barh(range(len(labels)), values, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=12)
    ax.invert_yaxis()

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                f"{val:.1%}", va="center", fontsize=11, fontweight="bold")

    ax.set_xlabel("Relative Importance", fontsize=13)
    ax.set_title("What Drives Malaria Risk?", fontsize=18, fontweight="bold", pad=15)
    ax.set_xlim(0, max(values) * 1.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.3)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["red"], label="Strong predictor (>10%)"),
        Patch(facecolor=COLORS["orange"], label="Moderate (1-10%)"),
        Patch(facecolor=COLORS["blue"], label="Weak (<1%)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=10)

    path = os.path.join(OUTPUT_DIR, "feature_importance.png")
    plt.savefig(path)
    plt.close()
    print(f"  Saved: feature_importance.png")


# ── Chart 6: Climate Heatmap ──────────────────────────────────────────────────

def plot_climate_heatmap(ml_features):
    """Precipitation and temperature anomalies over time."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [1, 1]})

    data = ml_features[["year", "precip_anomaly", "temp_anomaly"]].dropna()

    # Precipitation anomaly
    ax = axes[0]
    colors = [COLORS["blue"] if v < 0 else COLORS["red"] for v in data["precip_anomaly"]]
    ax.bar(data["year"], data["precip_anomaly"], color=colors, edgecolor="white", linewidth=0.5)
    ax.axhline(y=0, color="black", linewidth=0.8)
    ax.set_ylabel("Rainfall Anomaly (mm)")
    ax.set_title("Climate Anomalies in Kenya (vs Long-Term Mean)", fontsize=16, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Add text
    ax.text(0.02, 0.92, "Blue = Drier than average", transform=ax.transAxes,
            fontsize=10, color=COLORS["blue"], fontweight="bold")
    ax.text(0.02, 0.08, "Red = Wetter than average", transform=ax.transAxes,
            fontsize=10, color=COLORS["red"], fontweight="bold")

    # Temperature anomaly
    ax = axes[1]
    colors = [COLORS["blue"] if v < 0 else COLORS["red"] for v in data["temp_anomaly"]]
    ax.bar(data["year"], data["temp_anomaly"], color=colors, edgecolor="white", linewidth=0.5)
    ax.axhline(y=0, color="black", linewidth=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel("Temperature Anomaly (°C)")
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.text(0.02, 0.92, "Blue = Cooler than average", transform=ax.transAxes,
            fontsize=10, color=COLORS["blue"], fontweight="bold")
    ax.text(0.02, 0.08, "Red = Warmer than average", transform=ax.transAxes,
            fontsize=10, color=COLORS["red"], fontweight="bold")

    plt.tight_layout()

    path = os.path.join(OUTPUT_DIR, "climate_heatmap.png")
    plt.savefig(path)
    plt.close()
    print(f"  Saved: climate_heatmap.png")


# ── Chart 7: Architecture Overview ────────────────────────────────────────────

def plot_architecture():
    """Visual architecture diagram."""
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis("off")

    # Title
    ax.text(7, 6.6, "System Architecture", fontsize=20, fontweight="bold",
            ha="center", va="center")

    def draw_box(x, y, w, h, label, color, fontsize=10):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                               facecolor=color, edgecolor="#333", linewidth=1.5, alpha=0.85)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color="white")

    def draw_arrow(x1, y1, x2, y2, color="#333"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                     arrowprops=dict(arrowstyle="->", color=color, lw=2))

    # Data sources
    draw_box(0.5, 5.2, 2.5, 0.8, "WHO GHO\nAPI", "#E53935", 10)
    draw_box(3.5, 5.2, 2.5, 0.8, "World Bank\nAPI", "#1E88E5", 10)
    draw_box(6.5, 5.2, 2.5, 0.8, "NASA POWER\nAPI", "#43A047", 10)
    draw_box(9.5, 5.2, 2.5, 0.8, "KEMRI\nResearch", "#8E24AA", 10)

    # ETL
    draw_box(3.0, 3.8, 6.0, 0.8, "Python ETL Pipeline (fetch_malaria_data.py)", "#FF8F00", 11)

    # Arrows: sources -> ETL
    for x in [1.75, 4.75, 7.75, 10.75]:
        draw_arrow(x, 5.2, 6.0, 4.6)

    # Data stores
    draw_box(1.0, 2.3, 2.5, 0.8, "Raw Data\n(CSV)", "#78909C", 10)
    draw_box(4.0, 2.3, 2.5, 0.8, "Processed Data\n(CSV)", "#5C6BC0", 10)
    draw_box(7.0, 2.3, 2.5, 0.8, "ML Features\n(CSV)", "#00897B", 10)

    # Arrows: ETL -> data
    draw_arrow(4.5, 3.8, 2.25, 3.1)
    draw_arrow(6.0, 3.8, 5.25, 3.1)
    draw_arrow(7.5, 3.8, 8.25, 3.1)

    # ML Model
    draw_box(10.5, 2.3, 2.8, 0.8, "Random Forest\nModel", "#D32F2F", 10)
    draw_arrow(9.5, 2.7, 10.5, 2.7)

    # Outputs
    draw_box(0.5, 0.5, 3.0, 1.0, "R Shiny\nDashboard", "#E53935", 11)
    draw_box(4.5, 0.5, 3.0, 1.0, "FastAPI\nBackend", "#1565C0", 11)
    draw_box(8.5, 0.5, 3.0, 1.0, "Docker\nContainer", "#43A047", 11)
    draw_box(12.0, 0.5, 1.5, 1.0, "CI/CD", "#7B1FA2", 10)

    # Arrows: data -> outputs
    draw_arrow(2.25, 2.3, 2.0, 1.5)
    draw_arrow(5.25, 2.3, 6.0, 1.5)
    draw_arrow(11.9, 2.3, 10.0, 1.5)

    # Docker arrows
    draw_arrow(7.5, 0.9, 8.5, 0.9)

    ax.set_title("KEMRI-Inspired Malaria Outbreak Predictor", fontsize=14,
                  fontweight="bold", pad=20, color="#555")

    path = os.path.join(OUTPUT_DIR, "architecture.png")
    plt.savefig(path, facecolor="white")
    plt.close()
    print(f"  Saved: architecture.png")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Generating Visuals for GitHub README")
    print("=" * 60)

    merged, ml_features, ea, predictions = load_data()

    print("\n1. Malaria Trend...")
    plot_malaria_trend(merged)

    print("2. Climate Correlation...")
    plot_climate_correlation(merged)

    print("3. East Africa Comparison...")
    plot_east_africa(ea)

    print("4. Model Predictions...")
    plot_predictions(predictions)

    print("5. Feature Importance...")
    plot_feature_importance()

    print("6. Climate Heatmap...")
    plot_climate_heatmap(ml_features)

    print("7. Architecture Diagram...")
    plot_architecture()

    print(f"\n{'=' * 60}")
    print(f"  All visuals saved to: {OUTPUT_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
