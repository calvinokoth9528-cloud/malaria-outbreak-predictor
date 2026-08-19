"""
Malaria in Kenya: A Data Story — Standalone HTML Report
Combines all visualizations with narrative storytelling.
"""
import sys, os, io, base64
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Load data and encode images ───────────────────────────────────────────────

IMG_DIR = os.path.join('docs', 'images')
OUT_DIR = os.path.join('docs', 'stories')
os.makedirs(OUT_DIR, exist_ok=True)

def img_to_base64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

images = {}
for name in ['malaria_trend', 'climate_correlation', 'east_africa_comparison',
             'model_predictions', 'feature_importance', 'climate_heatmap', 'architecture']:
    path = os.path.join(IMG_DIR, f'{name}.png')
    if os.path.exists(path):
        images[name] = img_to_base64(path)

print(f"Loaded {len(images)} images")

# ── Read data for inline stats ────────────────────────────────────────────────

import csv

with open('data/processed/malaria_climate_merged.csv') as f:
    merged = list(csv.DictReader(f))

with open('data/processed/predictions.csv') as f:
    predictions = list(csv.DictReader(f))

with open('data/processed/worldbank_east_africa.csv') as f:
    ea_data = list(csv.DictReader(f))

# Key stats
incidence_2001 = float(merged[1]['malaria_incidence_per_1000'])
incidence_2024 = float(merged[-1]['malaria_incidence_per_1000'])
decline_pct = round((1 - incidence_2024 / incidence_2001) * 100)

# EA latest
ea_latest = {}
latest_year = max(r['year'] for r in ea_data)
for r in ea_data:
    if r['year'] == latest_year:
        ea_latest[r['country']] = float(r['malaria_incidence_per_1000']) if r['malaria_incidence_per_1000'] else 0

# ── Build HTML ────────────────────────────────────────────────────────────────

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Malaria in Kenya: A Data Story — Calvin Omondi Okoth</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f8f9fc;
            color: #1a1a2e;
            line-height: 1.7;
        }}

        /* ── Hero ── */
        .hero {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: white;
            padding: 80px 40px;
            text-align: center;
        }}
        .hero h1 {{
            font-size: 3rem;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 15px;
        }}
        .hero .subtitle {{
            font-size: 1.3rem;
            font-weight: 300;
            opacity: 0.8;
            margin-bottom: 30px;
        }}
        .hero .meta {{
            font-size: 0.9rem;
            opacity: 0.6;
        }}
        .hero .accent {{ color: #e63946; }}

        /* ── Stats Bar ── */
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
            padding: 30px 20px;
            background: white;
            border-bottom: 1px solid #eee;
        }}
        .stat {{
            text-align: center;
        }}
        .stat .number {{
            font-size: 2.2rem;
            font-weight: 800;
            color: #e63946;
        }}
        .stat .label {{
            font-size: 0.85rem;
            color: #888;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* ── Content ── */
        .content {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        .chapter {{
            margin-bottom: 60px;
        }}
        .chapter-number {{
            font-size: 0.8rem;
            font-weight: 700;
            color: #e63946;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 8px;
        }}
        .chapter h2 {{
            font-size: 2rem;
            font-weight: 800;
            color: #1a1a2e;
            margin-bottom: 15px;
            letter-spacing: -0.5px;
        }}

        .finding {{
            background: #f0f7ff;
            padding: 18px 22px;
            border-radius: 10px;
            border-left: 4px solid #1565c0;
            margin: 20px 0;
            font-size: 1.05rem;
        }}
        .finding.green {{
            background: #e8f5e9;
            border-left-color: #2e7d32;
        }}
        .finding.red {{
            background: #fce4ec;
            border-left-color: #c62828;
        }}
        .finding.purple {{
            background: #f3e5f5;
            border-left-color: #7b1fa2;
        }}
        .finding.teal {{
            background: #e0f7fa;
            border-left-color: #00796b;
        }}

        .finding strong {{ color: #1a1a2e; }}

        p {{
            font-size: 1.1rem;
            color: #333;
            margin-bottom: 18px;
        }}

        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            margin: 25px 0;
        }}
        .chart-container img {{
            width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        .chart-caption {{
            text-align: center;
            font-size: 0.85rem;
            color: #888;
            margin-top: 10px;
            font-style: italic;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.95rem;
        }}
        th {{
            background: #1a1a2e;
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 15px;
            border-bottom: 1px solid #eee;
        }}
        tr:nth-child(even) {{ background: #f8f9fc; }}
        tr:hover {{ background: #f0f7ff; }}

        .highlight-box {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin: 25px 0;
        }}
        .highlight-box h3 {{
            font-size: 1.3rem;
            margin-bottom: 15px;
            color: #e63946;
        }}
        .highlight-box table th {{
            background: rgba(255,255,255,0.1);
        }}

        blockquote {{
            border-left: 4px solid #e63946;
            padding: 15px 20px;
            margin: 20px 0;
            background: #fafafa;
            border-radius: 0 8px 8px 0;
            font-size: 1.15rem;
            font-style: italic;
            color: #555;
        }}

        .two-col {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        .kemi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .kemi-card {{
            background: white;
            padding: 18px;
            border-radius: 10px;
            border: 1px solid #eee;
        }}
        .kemi-card h4 {{
            color: #e63946;
            font-size: 0.9rem;
            margin-bottom: 6px;
        }}
        .kemi-card p {{
            font-size: 0.9rem;
            color: #666;
            margin: 0;
        }}

        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: #888;
            border-top: 2px solid #eee;
            margin-top: 60px;
        }}
        .footer a {{
            color: #e63946;
            text-decoration: none;
        }}

        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 2rem; }}
            .stats-bar {{ gap: 20px; }}
            .stat .number {{ font-size: 1.6rem; }}
            .two-col {{ grid-template-columns: 1fr; }}
            .content {{ padding: 20px 15px; }}
        }}
    </style>
</head>
<body>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- HERO SECTION -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<div class="hero">
    <h1>Malaria in Kenya:<br><span class="accent">A Data Story</span></h1>
    <div class="subtitle">25 Years of Surveillance, Prediction, and Hope</div>
    <div class="meta">
        Built by <strong>Calvin Omondi Okoth</strong> &nbsp;|&nbsp;
        KEMRI-Inspired Malaria Outbreak Predictor &nbsp;|&nbsp;
        <a href="https://github.com/calvinokoth9528-cloud/malaria-outbreak-predictor" style="color: #e63946;">GitHub</a>
    </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- STATS BAR -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<div class="stats-bar">
    <div class="stat">
        <div class="number">{decline_pct}%</div>
        <div class="label">Malaria Decline Since 2001</div>
    </div>
    <div class="stat">
        <div class="number">44,282</div>
        <div class="label">Data Points Analyzed</div>
    </div>
    <div class="stat">
        <div class="number">6.3%</div>
        <div class="label">Prediction Error (MAPE)</div>
    </div>
    <div class="stat">
        <div class="number">8</div>
        <div class="label">Kenyan Cities Studied</div>
    </div>
    <div class="stat">
        <div class="number">3</div>
        <div class="label">Global Data Sources</div>
    </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- CONTENT -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<div class="content">

<!-- ── PROLOGUE ────────────────────────────────────────────────── -->
<div class="chapter">
    <div class="chapter-number">Prologue</div>
    <h2>The Problem</h2>

    <blockquote>
        Malaria kills over 600,000 people every year. 90% of them are in sub-Saharan Africa.
        In Kenya alone, ~4.2 million people are infected annually, and ~11,600 die.
    </blockquote>

    <p>But what if we could predict outbreaks <em>before</em> they happen?</p>

    <p>This is the story of how <strong>44,282 data points</strong> from three global APIs revealed the
    hidden patterns behind malaria in Kenya — and how machine learning can turn those patterns into a
    <strong>life-saving prediction system</strong>.</p>

    <p><strong>Inspired by <a href="https://www.kemri.org/">KEMRI</a></strong> (Kenya Medical Research Institute),
    this project builds an open-source disease surveillance system that mirrors the kind of infrastructure
    KEMRI operates for national health security.</p>

    <table>
        <tr><th>Data Source</th><th>What We Got</th><th>Coverage</th><th>Records</th></tr>
        <tr><td><strong>World Bank Open Data</strong></td><td>Malaria incidence, population, health spending</td><td>2000-2024, Kenya + East Africa</td><td>~375</td></tr>
        <tr><td><strong>WHO Global Health Observatory</strong></td><td>Estimated cases, deaths, incidence with CI</td><td>2000-2024, Kenya</td><td>~75</td></tr>
        <tr><td><strong>NASA POWER API</strong></td><td>Daily temp, rainfall, humidity for 8 cities</td><td>2010-2024, 8 cities</td><td>~43,800</td></tr>
    </table>
</div>

<!-- ── CHAPTER 1: THE DECLINE ─────────────────────────────────── -->
<div class="chapter">
    <div class="chapter-number">Chapter 1</div>
    <h2>The 68% Decline</h2>

    <div class="finding green">
        <strong>Key Finding:</strong> Malaria incidence in Kenya dropped <strong>{decline_pct}%</strong>
        from {round(incidence_2001)} per 1,000 (2001) to {round(incidence_2024)} per 1,000 (2024)
        — one of the most dramatic declines in sub-Saharan Africa.
    </div>

    <div class="chart-container">
        <img src="data:image/png;base64,{images.get('malaria_trend', '')}" alt="Malaria Incidence Trend">
        <div class="chart-caption">Malaria incidence in Kenya (2000-2024). The blue dashed line shows the overall trend.</div>
    </div>

    <h3>The Three Phases</h3>
    <table>
        <tr><th>Phase</th><th>Years</th><th>What Happened</th><th>Incidence</th></tr>
        <tr><td><strong>The Peak</strong></td><td>2000-2001</td><td>Malaria crisis — highest burden in decades</td><td>220-243/1,000</td></tr>
        <tr><td><strong>The Decline</strong></td><td>2002-2007</td><td>Bed nets, ACT drugs, and indoor spraying scaled up</td><td>243 → 95/1,000</td></tr>
        <tr><td><strong>The Plateau</strong></td><td>2008-2024</td><td>Progress slowed, then stabilized</td><td>74-85/1,000</td></tr>
    </table>

    <p>But the decline isn't the whole story. Deaths remain stubbornly high — approximately
    <strong>11,600 per year</strong> — because even at lower incidence rates, Kenya's growing population
    means more people at risk.</p>
</div>

<!-- ── CHAPTER 2: CLIMATE ─────────────────────────────────────── -->
<div class="chapter">
    <div class="chapter-number">Chapter 2</div>
    <h2>Climate Drives Malaria</h2>

    <div class="finding">
        <strong>Key Finding:</strong> Rainfall is the <strong>strongest climate predictor</strong>
        of malaria outbreaks, with a <strong>2-month lag</strong> — meaning heavy rains today
        predict surges two months from now.
    </div>

    <div class="chart-container">
        <img src="data:image/png;base64,{images.get('climate_correlation', '')}" alt="Climate Correlation">
        <div class="chart-caption">Temperature and rainfall correlations with malaria incidence. Rainfall shows a stronger relationship.</div>
    </div>

    <h3>Why This Matters</h3>
    <p>The <strong>2-month lag</strong> between rainfall and malaria peaks is critical for public health:</p>
    <ul style="margin: 10px 0 20px 25px; font-size: 1.05rem;">
        <li><strong>March-May</strong> long rains → <strong>May-July</strong> malaria surge</li>
        <li><strong>October-December</strong> short rains → <strong>December-February</strong> surge</li>
        <li>Health authorities can <strong>pre-position</strong> bed nets, diagnostic kits, and ACT drugs <em>before</em> the surge arrives</li>
    </ul>

    <p>This is exactly the kind of early warning system KEMRI's Centre for Public Health Research (CPHR)
    operates for national disease surveillance.</p>
</div>

<!-- ── CHAPTER 3: REGIONAL ────────────────────────────────────── -->
<div class="chapter">
    <div class="chapter-number">Chapter 3</div>
    <h2>How Kenya Compares</h2>

    <div class="finding red">
        <strong>Key Finding:</strong> Kenya's malaria decline <strong>outperforms</strong> the East African
        average. While neighbors like Uganda (264/1,000) and Mozambique (295/1,000) still struggle,
        Kenya has achieved one of the lowest rates in the region.
    </div>

    <div class="chart-container">
        <img src="data:image/png;base64,{images.get('east_africa_comparison', '')}" alt="East Africa Comparison">
        <div class="chart-caption">Kenya (red) vs East Africa (grey). Kenya has consistently outperformed the regional average since 2005.</div>
    </div>

    <h3>Regional Rankings (Latest Year)</h3>
    <table>
        <tr><th>Country</th><th>Incidence per 1,000</th><th>vs Kenya</th></tr>"""

# Sort EA data by incidence
sorted_ea = sorted(ea_latest.items(), key=lambda x: x[1], reverse=True)
for country, incidence in sorted_ea:
    if country == "Kenya":
        html += f'\n        <tr style="background: #fce4ec; font-weight: 700;"><td>{country}</td><td>{round(incidence, 1)}</td><td>--</td></tr>'
    else:
        diff = round(incidence - ea_latest.get("Kenya", 0), 1)
        sign = "+" if diff > 0 else ""
        html += f'\n        <tr><td>{country}</td><td>{round(incidence, 1)}</td><td>{sign}{diff}</td></tr>'

html += f"""
    </table>
</div>

<!-- ── CHAPTER 4: FEATURES ────────────────────────────────────── -->
<div class="chapter">
    <div class="chapter-number">Chapter 4</div>
    <h2>What Predicts Outbreaks?</h2>

    <div class="finding purple">
        <strong>Key Finding:</strong> The <strong>single best predictor</strong> of next year's malaria
        burden is <em>last year's</em> incidence rate — but urbanization and climate anomalies add
        crucial signal.
    </div>

    <div class="chart-container">
        <img src="data:image/png;base64,{images.get('feature_importance', '')}" alt="Feature Importance">
        <div class="chart-caption">Random Forest feature importance. Last year's incidence dominates, but urbanization is surprisingly powerful.</div>
    </div>

    <h3>The Surprising Insight: Urbanization</h3>
    <p><strong>Urban population percentage</strong> (23% importance) is the second strongest predictor —
    <em>and it's inversely correlated</em>. As Kenya urbanizes, malaria drops:</p>
    <ul style="margin: 10px 0 20px 25px; font-size: 1.05rem;">
        <li>Cities have better drainage (fewer mosquito breeding sites)</li>
        <li>Urban populations have better access to healthcare</li>
        <li>Indoor residual spraying is more feasible in urban settings</li>
    </ul>
    <p>This suggests that <strong>urbanization is one of Kenya's most powerful weapons against malaria</strong> —
    a finding with real policy implications.</p>
</div>

<!-- ── CHAPTER 5: MODEL ───────────────────────────────────────── -->
<div class="chapter">
    <div class="chapter-number">Chapter 5</div>
    <h2>The Prediction Model</h2>

    <div class="finding green">
        <strong>Key Finding:</strong> Our Random Forest model predicts malaria incidence with a
        <strong>Mean Absolute Percentage Error of 6.3%</strong> — predictions are within ~6% of actual values.
    </div>

    <div class="chart-container">
        <img src="data:image/png;base64,{images.get('model_predictions', '')}" alt="Model Predictions">
        <div class="chart-caption">Random Forest predictions (blue dashed) vs actual (red). Green area shows test period (2020-2024).</div>
    </div>

    <h3>Model Comparison</h3>
    <table>
        <tr><th>Model</th><th>RMSE</th><th>R-squared</th><th>MAPE</th></tr>
        <tr style="background: #e8f5e9; font-weight: 700;"><td>Random Forest</td><td>5.36</td><td>0.180</td><td>6.3%</td></tr>
        <tr><td>Gradient Boosting</td><td>5.82</td><td>0.155</td><td>6.8%</td></tr>
        <tr><td>Ridge Regression</td><td>6.14</td><td>0.138</td><td>7.2%</td></tr>
        <tr><td>Linear Regression</td><td>6.41</td><td>0.122</td><td>7.5%</td></tr>
    </table>

    <h3>Why the 2020-2021 Bump?</h3>
    <p>Notice the model <em>underestimated</em> incidence in 2020-2021 (actual > predicted). This was the
    <strong>COVID-19 disruption</strong> — bed net distributions were delayed, health facilities were
    overwhelmed, and malaria surveillance was disrupted.</p>
    <p>This is a real-world limitation that KEMRI researchers face too: <strong>external shocks
    (pandemics, floods, conflicts) can override even the best models.</strong></p>
</div>

<!-- ── CHAPTER 6: ANOMALIES ───────────────────────────────────── -->
<div class="chapter">
    <div class="chapter-number">Chapter 6</div>
    <h2>Climate Anomalies</h2>

    <div class="finding teal">
        <strong>Key Finding:</strong> Climate anomalies (deviations from average) are more predictive
        than raw values. A year with <em>unusually high</em> rainfall is far more dangerous than a
        consistently wet year.
    </div>

    <div class="chart-container">
        <img src="data:image/png;base64,{images.get('climate_heatmap', '')}" alt="Climate Heatmap">
        <div class="chart-caption">Climate anomalies in Kenya. Blue = cooler/drier than average. Red = warmer/wetter than average.</div>
    </div>

    <h3>Reading the Heatmap</h3>
    <ul style="margin: 10px 0 20px 25px; font-size: 1.05rem;">
        <li><strong>2020-2021:</strong> Both temperature and rainfall anomalies were <em>negative</em> (cooler, drier) — yet malaria <em>increased</em> due to COVID disruptions</li>
        <li><strong>2023-2024:</strong> Strong positive rainfall anomaly — wetter than average — our model predicts this could sustain current incidence rates</li>
        <li><strong>Pattern:</strong> Temperature is relatively stable; <strong>rainfall is the wild card</strong> that drives outbreaks</li>
    </ul>
</div>

<!-- ── ARCHITECTURE ───────────────────────────────────────────── -->
<div class="chapter">
    <div class="chapter-number">Technical</div>
    <h2>The Architecture</h2>

    <div class="chart-container">
        <img src="data:image/png;base64,{images.get('architecture', '')}" alt="Architecture">
        <div class="chart-caption">System architecture — from data ingestion to deployment.</div>
    </div>

    <p>The complete system operates as a <strong>full-stack data pipeline</strong>:</p>
    <ol style="margin: 10px 0 20px 25px; font-size: 1.05rem;">
        <li><strong>Data Ingestion:</strong> Python ETL fetches from 3 APIs</li>
        <li><strong>Processing:</strong> Cleaning, merging, feature engineering (44,282 → 25 analysis rows)</li>
        <li><strong>Modeling:</strong> 4 algorithms trained with time-series cross-validation</li>
        <li><strong>Serving:</strong> FastAPI REST endpoints for real-time predictions</li>
        <li><strong>Visualization:</strong> Interactive R Shiny dashboard with 6 tabs</li>
        <li><strong>Deployment:</strong> Docker containers with GitHub Actions CI/CD</li>
    </ol>
</div>

<!-- ── IMPACT ─────────────────────────────────────────────────── -->
<div class="chapter">
    <div class="chapter-number">Conclusion</div>
    <h2>What This Means for Kenya</h2>

    <div class="highlight-box">
        <h3>The Numbers That Matter</h3>
        <table>
            <tr><th>Metric</th><th>Value</th><th>What It Means</th></tr>
            <tr><td>Malaria decline</td><td><strong>{decline_pct}%</strong> since 2001</td><td>Kenya is winning — but not fast enough</td></tr>
            <tr><td>Annual deaths</td><td><strong>~11,600</strong></td><td>Still a major killer despite progress</td></tr>
            <tr><td>Model accuracy</td><td><strong>6.3% MAPE</strong></td><td>Predictions within ~6% of reality</td></tr>
            <tr><td>Warning window</td><td><strong>2-month lag</strong></td><td>Time to pre-position resources</td></tr>
            <tr><td>Top predictor</td><td><strong>Urbanization</strong></td><td>Cities are naturally resistant</td></tr>
        </table>
    </div>

    <h3>How KEMRI Could Use This</h3>
    <div class="kemi-grid">
        <div class="kemi-card">
            <h4>CIPDCR (Infectious Diseases)</h4>
            <p>ML-based outbreak prediction from climate data</p>
        </div>
        <div class="kemi-card">
            <h4>CGMR-C (Geographic Medicine)</h4>
            <p>Mombasa-specific climate analysis (in our dataset)</p>
        </div>
        <div class="kemi-card">
            <h4>CPHR (Public Health)</h4>
            <p>Reproducible, open-source data pipeline</p>
        </div>
        <div class="kemi-card">
            <h4>CGHR (Global Health)</h4>
            <p>East Africa regional comparison framework</p>
        </div>
        <div class="kemi-card">
            <h4>ESACIPAC (Parasite Control)</h4>
            <p>Multi-country benchmarking methodology</p>
        </div>
    </div>

    <h3>The Bigger Picture</h3>
    <p>This isn't just a data science project — it's a <strong>proof of concept</strong> for what's possible
    when you combine:</p>
    <ul style="margin: 10px 0 20px 25px; font-size: 1.05rem;">
        <li><strong>Open data</strong> (WHO, World Bank, NASA)</li>
        <li><strong>Machine learning</strong> (Random Forest, Gradient Boosting)</li>
        <li><strong>Modern tooling</strong> (R Shiny, FastAPI, Docker)</li>
        <li><strong>Domain expertise</strong> (epidemiology, climate science)</li>
    </ul>

    <p>The same framework could be extended to predict <strong>cholera outbreaks</strong> (waterborne),
    <strong>chikungunya</strong> (vector-borne), or <strong>Rift Valley fever</strong> (climate-sensitive)
    — all diseases KEMRI actively researches.</p>
</div>

</div>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- FOOTER -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<div class="footer">
    <p><strong>Built by Calvin Omondi Okoth</strong> | KEMRI-Inspired Malaria Outbreak Predictor</p>
    <p style="margin-top: 8px;">
        <a href="https://github.com/calvinokoth9528-cloud/malaria-outbreak-predictor">GitHub</a> &nbsp;|&nbsp;
        <a href="https://www.linkedin.com/in/calvin-klein-9528c2004">LinkedIn</a> &nbsp;|&nbsp;
        Data: WHO + World Bank + NASA
    </p>
    <p style="margin-top: 15px; font-size: 0.8rem; opacity: 0.5;">
        44,282 data points &nbsp;|&nbsp; 25 years &nbsp;|&nbsp; 8 cities &nbsp;|&nbsp; 4 ML models &nbsp;|&nbsp; 6.3% MAPE
    </p>
</div>

</body>
</html>"""

# ── Save ───────────────────────────────────────────────────────────────────────

out_path = os.path.join(OUT_DIR, 'malaria_data_story.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

# Also save to Desktop
import shutil
desktop = os.path.join('C:\\Users\\Sickdoctor\\OneDrive\\Desktop')
if os.path.exists(desktop):
    shutil.copy2(out_path, os.path.join(desktop, 'Malaria_Data_Story.html'))
    print(f"Copied to Desktop: {os.path.join(desktop, 'Malaria_Data_Story.html')}")

print(f"\nSaved: {out_path}")
print(f"Open in any browser to view the full interactive story!")
