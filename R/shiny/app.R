#!/usr/bin/env Rscript
# ==============================================================================
# Malaria Outbreak Predictor — Interactive Dashboard
# ==============================================================================
# Light-themed, highly interactive dashboard for visualizing malaria trends,
# climate correlations, and outbreak risk predictions for Kenya.
#
# Run: Rscript R/shiny/app.R
# Then: http://localhost:3838
# ==============================================================================

library(shiny)
library(tidyverse)
library(plotly)
library(DT)
library(scales)
library(shinydashboard)
library(bslib)

# ── Load Data ──────────────────────────────────────────────────────────────────

merged <- read_csv("data/processed/malaria_climate_merged.csv", show_col_types = FALSE)
ml_features <- read_csv("data/processed/malaria_ml_features.csv", show_col_types = FALSE)
ea_data <- read_csv("data/processed/worldbank_east_africa.csv", show_col_types = FALSE)
climate_monthly <- read_csv("data/processed/climate_monthly.csv", show_col_types = FALSE)
predictions <- read_csv("data/processed/predictions.csv", show_col_types = FALSE)

# ── Custom CSS ─────────────────────────────────────────────────────────────────

custom_css <- HTML("
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  * { font-family: 'Inter', sans-serif !important; }

  body { background-color: #f8f9fc; color: #1a1a2e; }

  .skin-red .main-header .logo {
    background-color: #ffffff;
    color: #1a1a2e;
    border-bottom: 2px solid #e63946;
    font-weight: 700;
    font-size: 15px;
  }
  .skin-red .main-header .navbar { background-color: #ffffff; }
  .skin-red .main-header .logo:hover { background-color: #f8f9fc; }

  .skin-red .main-sidebar {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  }
  .skin-red .main-sidebar .sidebar-menu > li > a {
    color: #e0e0e0;
    border-left: 3px solid transparent;
    padding: 12px 20px;
    transition: all 0.2s ease;
  }
  .skin-red .main-sidebar .sidebar-menu > li > a:hover {
    background-color: rgba(230, 57, 70, 0.15);
    color: #ffffff;
    border-left-color: #e63946;
  }
  .skin-red .main-sidebar .sidebar-menu > li.active > a {
    background-color: rgba(230, 57, 70, 0.2);
    color: #ffffff;
    border-left-color: #e63946;
    font-weight: 600;
  }

  .content-wrapper { background-color: #f8f9fc; }

  .box {
    border: none;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: box-shadow 0.3s ease;
    margin-bottom: 20px;
  }
  .box:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
  .box-header {
    border-bottom: 1px solid #f0f0f0;
    padding: 15px 20px;
    border-radius: 12px 12px 0 0;
    background: #ffffff;
  }
  .box-header .box-title { font-weight: 600; font-size: 15px; color: #1a1a2e; }
  .box-body { padding: 20px; }

  .small-box {
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: all 0.3s ease;
    border: none;
  }
  .small-box:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.12); }
  .small-box h3 { font-size: 28px; font-weight: 700; }
  .small-box p { font-size: 13px; font-weight: 500; }

  .btn-danger {
    background: linear-gradient(135deg, #e63946 0%, #c62828 100%);
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: 600;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(230, 57, 70, 0.3);
  }
  .btn-danger:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(230, 57, 70, 0.4);
  }

  .form-control {
    border-radius: 8px;
    border: 1.5px solid #e0e0e0;
    padding: 10px 14px;
    transition: border-color 0.2s ease;
  }
  .form-control:focus {
    border-color: #e63946;
    box-shadow: 0 0 0 3px rgba(230, 57, 70, 0.1);
  }

  .sidebar-user-panel { padding: 15px; text-align: center; }
  .sidebar-user-panel img { width: 60px; border-radius: 50%; border: 2px solid #e63946; }

  .js-plotly-plot .plotly .modebar { top: 5px !important; right: 5px !important; }
  .js-plotly-plot .plotly .modebar-btn { font-size: 14px !important; }

  .dataTables_wrapper .dataTables_length,
  .dataTables_wrapper .dataTables_filter,
  .dataTables_wrapper .dataTables_info,
  .dataTables_wrapper .dataTables_paginate {
    font-size: 13px;
    color: #555;
  }
  table.dataTable tbody td { padding: 10px 12px; }
  table.dataTable thead th { padding: 10px 12px; font-weight: 600; }

  .tab-content { padding-top: 10px; }
")

# ── UI ─────────────────────────────────────────────────────────────────────────

ui <- dashboardPage(
  skin = "red",

  dashboardHeader(
    title = span(
      icon("virus", lib = "font-awesome"),
      span("Malaria Predictor", style = "font-weight: 700; letter-spacing: -0.5px;")
    ),
    titleWidth = 260,
    tags$li(
      class = "dropdown",
      tags$a(
        href = "https://github.com/calvinokoth9528-cloud/malaria-outbreak-predictor",
        target = "_blank",
        icon("github", lib = "font-awesome"),
        style = "color: #555; font-size: 18px; padding: 15px;"
      )
    )
  ),

  dashboardSidebar(
    width = 260,
    tags$div(
      style = "padding: 20px 15px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1);",
      tags$div(style = "font-size: 28px;", icon("mosquito", lib = "font-awesome")),
      tags$div(style = "color: #fff; font-size: 12px; margin-top: 5px; opacity: 0.7;",
               "KEMRI-Inspired Surveillance")
    ),
    sidebarMenu(
      id = "tabs",
      menuItem("Overview", tabName = "overview", icon = icon("chart-line")),
      menuItem("Climate Analysis", tabName = "climate", icon = icon("cloud-sun-rain")),
      menuItem("Regional View", tabName = "regional", icon = icon("globe-africa")),
      menuItem("ML Predictions", tabName = "predictions", icon = icon("brain")),
      menuItem("Risk Simulator", tabName = "simulator", icon = icon("sliders-h")),
      menuItem("About", tabName = "about", icon = icon("info-circle"))
    ),
    tags$div(
      style = "position: absolute; bottom: 0; width: 100%; padding: 15px; font-size: 11px; color: rgba(255,255,255,0.5); text-align: center; border-top: 1px solid rgba(255,255,255,0.1);",
      HTML("Data: WHO + World Bank + NASA<br>44,282 data points | 25 years | 8 cities")
    )
  ),

  dashboardBody(
    tags$head(tags$style(custom_css)),

    tabItems(
      # ══════════════════════════════════════════════════════════════
      # TAB 1: OVERVIEW
      # ══════════════════════════════════════════════════════════════
      tabItem(
        tabName = "overview",
        fluidRow(
          valueBoxOutput("vb_cases", width = 3),
          valueBoxOutput("vb_deaths", width = 3),
          valueBoxOutput("vb_incidence", width = 3),
          valueBoxOutput("vb_trend", width = 3)
        ),
        fluidRow(
          box(
            title = span(icon("chart-line"), "Malaria Incidence Trend (2000–2024)"),
            status = "primary", solidHeader = FALSE, width = 8,
            plotlyOutput("plot_incidence_trend", height = "420px") %>%
              tagAppendAttributes(class = "plotly-chart"),
            footer = tags$div(
              style = "font-size: 12px; color: #888;",
              "Hover for details. Drag to zoom. Double-click to reset."
            )
          ),
          box(
            title = span(icon("info-circle"), "Key Insights"),
            status = "info", solidHeader = FALSE, width = 4,
            tags$div(
              style = "line-height: 1.8;",
              tags$p(tags$strong("25-Year Journey"), style = "font-size: 15px; margin-bottom: 8px;"),
              tags$hr(style = "margin: 5px 0; border-color: #eee;"),
              tags$p(icon("arrow-down", style = "color: #2e7d32;"),
                     tags$strong("68% decline"), " since peak in 2001"),
              tags$p(icon("users", style = "color: #e63946;"),
                     tags$strong("~11,600"), " deaths per year"),
              tags$p(icon("virus", style = "color: #f57c00;"),
                     tags$strong("~4.2M"), " annual cases"),
              tags$hr(style = "margin: 8px 0; border-color: #eee;"),
              tags$p(tags$strong("Top Predictor"), style = "color: #555;"),
              tags$div(
                style = "background: #f0f7ff; padding: 10px; border-radius: 8px; border-left: 3px solid #1565c0;",
                "Last year's incidence rate is the single strongest predictor of next year's malaria burden."
              )
            )
          )
        ),
        fluidRow(
          box(
            title = span(icon("chart-bar"), "Cases & Deaths Over Time"),
            status = "warning", solidHeader = FALSE, width = 12,
            plotlyOutput("plot_cases_deaths", height = "350px"),
            footer = tags$div(style = "font-size: 12px; color: #888;",
                              "Orange bars = estimated cases (left axis). Red line = estimated deaths (right axis).")
          )
        )
      ),

      # ══════════════════════════════════════════════════════════════
      # TAB 2: CLIMATE ANALYSIS
      # ══════════════════════════════════════════════════════════════
      tabItem(
        tabName = "climate",
        fluidRow(
          box(
            title = span(icon("thermometer-half"), "Temperature vs Malaria"),
            status = "primary", solidHeader = FALSE, width = 6,
            plotlyOutput("plot_temp_malaria", height = "380px")
          ),
          box(
            title = span(icon("cloud-rain"), "Rainfall vs Malaria"),
            status = "primary", solidHeader = FALSE, width = 6,
            plotlyOutput("plot_rain_malaria", height = "380px")
          )
        ),
        fluidRow(
          box(
            title = span(icon("city"), "Monthly Climate by City"),
            status = "info", solidHeader = FALSE, width = 5,
            tags$div(
              style = "padding: 0 0 10px 0;",
              selectInput("city_select", NULL,
                          choices = c("Nairobi", "Mombasa", "Kisumu", "Nakuru",
                                      "Eldoret", "Garissa", "Kakamega", "Machakos"),
                          selected = "Nairobi",
                          width = "100%")
            ),
            plotlyOutput("plot_city_climate", height = "320px")
          ),
          box(
            title = span(icon("fire"), "Climate Anomaly Heatmap"),
            status = "warning", solidHeader = FALSE, width = 7,
            plotlyOutput("plot_anomaly_heatmap", height = "420px"),
            footer = tags$div(style = "font-size: 12px; color: #888;",
                              "Blue = cooler/drier than average. Red = warmer/wetter than average.")
          )
        )
      ),

      # ══════════════════════════════════════════════════════════════
      # TAB 3: REGIONAL
      # ══════════════════════════════════════════════════════════════
      tabItem(
        tabName = "regional",
        fluidRow(
          box(
            title = span(icon("globe-africa"), "Malaria Incidence: Kenya vs East Africa"),
            status = "primary", solidHeader = FALSE, width = 12,
            plotlyOutput("plot_ea_comparison", height = "450px"),
            footer = tags$div(style = "font-size: 12px; color: #888;",
                              "Kenya is highlighted in red. Hover to see country details.")
          )
        ),
        fluidRow(
          box(
            title = span(icon("trophy"), "Country Rankings"),
            status = "info", solidHeader = FALSE, width = 5,
            plotlyOutput("plot_ea_ranking", height = "380px")
          ),
          box(
            title = span(icon("percentage"), "Trend Comparison (% Change)"),
            status = "warning", solidHeader = FALSE, width = 7,
            plotlyOutput("plot_ea_trends", height = "380px"),
            footer = tags$div(style = "font-size: 12px; color: #888;",
                              "Percentage change from each country's year 2000 baseline.")
          )
        )
      ),

      # ══════════════════════════════════════════════════════════════
      # TAB 4: PREDICTIONS
      # ══════════════════════════════════════════════════════════════
      tabItem(
        tabName = "predictions",
        fluidRow(
          box(
            title = span(icon("brain"), "Random Forest: Predictions vs Actual"),
            status = "primary", solidHeader = FALSE, width = 8,
            plotlyOutput("plot_predictions", height = "450px"),
            footer = tags$div(style = "font-size: 12px; color: #888;",
                              "Blue dashed = model predictions. Green shaded = test period.")
          ),
          box(
            title = span(icon("chart-pie"), "Model Performance"),
            status = "success", solidHeader = FALSE, width = 4,
            tags$div(
              style = "text-align: center; padding: 10px;",
              tags$div(style = "font-size: 48px; font-weight: 700; color: #2e7d32;", "6.3%"),
              tags$div(style = "font-size: 14px; color: #888; margin-bottom: 15px;", "Mean Absolute % Error"),
              tags$hr(style = "border-color: #eee;")
            ),
            tags$div(style = "padding: 0 10px;",
              tags$table(style = "width: 100%; font-size: 13px;",
                tags$tr(tags$td(tags$strong("Test R²")), tags$td(style = "text-align: right;", "0.180")),
                tags$tr(tags$td(tags$strong("Test MAE")), tags$td(style = "text-align: right;", "5.10/1,000")),
                tags$tr(tags$td(tags$strong("Test RMSE")), tags$td(style = "text-align: right;", "5.36/1,000")),
                tags$tr(tags$td(tags$strong("Features")), tags$td(style = "text-align: right;", "20")),
                tags$tr(tags$td(tags$strong("Train years")), tags$td(style = "text-align: right;", "2001–2019")),
                tags$tr(tags$td(tags$strong("Test years")), tags$td(style = "text-align: right;", "2020–2024"))
              )
            ),
            tags$hr(style = "border-color: #eee; margin: 10px 0;"),
            tags$div(style = "font-size: 13px; padding: 0 10px;",
              tags$p(tags$strong("Top Predictors:")),
              tags$ol(
                tags$li("Last year's incidence (41%)"),
                tags$li("Urban population % (23%)"),
                tags$li("Total population (21%)"),
                tags$li("2-year lagged incidence (11%)")
              )
            )
          )
        ),
        fluidRow(
          box(
            title = span(icon("table"), "Prediction Data"),
            status = "info", solidHeader = FALSE, width = 12,
            DTOutput("dt_predictions"),
            footer = tags$div(style = "font-size: 12px; color: #888;",
                              "Click column headers to sort. Use search to filter.")
          )
        )
      ),

      # ══════════════════════════════════════════════════════════════
      # TAB 5: RISK SIMULATOR
      # ══════════════════════════════════════════════════════════════
      tabItem(
        tabName = "simulator",
        fluidRow(
          box(
            title = span(icon("sliders-h"), "Adjust Parameters"),
            status = "danger", solidHeader = FALSE, width = 4,
            tags$div(style = "padding: 5px 0;",
              sliderInput("sim_lag1", "Last Year's Incidence (per 1,000):",
                          value = 74, min = 20, max = 250, step = 1,
                          post = " /1K",
                          width = "100%"),
              sliderInput("sim_precip", "Annual Rainfall (mm):",
                          value = 1500, min = 500, max = 3000, step = 50,
                          post = " mm",
                          width = "100%"),
              sliderInput("sim_temp", "Mean Temperature (°C):",
                          value = 21.3, min = 15, max = 30, step = 0.1,
                          post = "°C",
                          width = "100%"),
              sliderInput("sim_humidity", "Relative Humidity (%):",
                          value = 73, min = 40, max = 100, step = 1,
                          post = "%",
                          width = "100%"),
              sliderInput("sim_population", "Population (millions):",
                          value = 57, min = 30, max = 70, step = 0.5,
                          post = "M",
                          width = "100%"),
              sliderInput("sim_urban", "Urbanization (%):",
                          value = 32.5, min = 15, max = 50, step = 0.5,
                          post = "%",
                          width = "100%"),
              tags$hr(style = "border-color: #eee;"),
              actionButton("run_sim", "Predict Risk",
                           icon = icon("play"),
                           width = "100%",
                           class = "btn-danger")
            )
          ),
          box(
            title = span(icon("chart-line"), "Simulation Result"),
            status = "primary", solidHeader = FALSE, width = 8,
            plotlyOutput("plot_sim_result", height = "350px"),
            uiOutput("sim_risk_box"),
            tags$hr(style = "border-color: #eee; margin: 10px 0;"),
            uiOutput("sim_explanation")
          )
        )
      ),

      # ══════════════════════════════════════════════════════════════
      # TAB 6: ABOUT
      # ══════════════════════════════════════════════════════════════
      tabItem(
        tabName = "about",
        fluidRow(
          box(
            title = span(icon("info-circle"), "About This Project"),
            status = "info", solidHeader = FALSE, width = 12,
            tags$div(
              style = "max-width: 800px; line-height: 1.8;",
              tags$h3("Malaria Outbreak Predictor", style = "font-weight: 700; color: #1a1a2e;"),
              tags$p("A machine learning system for predicting malaria outbreak risk in Kenya",
                     tags$strong("— inspired by KEMRI's disease surveillance mandate."),
                     style = "font-size: 15px; color: #444;"),
              tags$hr(),

              tags$h4(icon("bullseye"), "Mission"),
              tags$p("Malaria kills over 600,000 people annually, with 90% of deaths in sub-Saharan Africa.
                     This system predicts outbreak risk from climate and health data — the same types of
                     data KEMRI uses for national disease surveillance.", style = "color: #555;"),

              tags$h4(icon("database"), "Data Sources"),
              tags$ul(
                tags$li(tags$strong("WHO Global Health Observatory"), " — Malaria estimates with confidence intervals"),
                tags$li(tags$strong("World Bank Open Data"), " — Health spending, population, precipitation"),
                tags$li(tags$strong("NASA POWER API"), " — Daily temperature, rainfall, humidity for 8 Kenyan cities")
              ),

              tags$h4(icon("cogs"), "Tech Stack"),
              tags$div(
                style = "display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;",
                tags$span(style = "background: #e8f5e9; color: #2e7d32; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;", "R Shiny"),
                tags$span(style = "background: #e3f2fd; color: #1565c0; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;", "ggplot2"),
                tags$span(style = "background: #fce4ec; color: #c62828; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;", "tidyverse"),
                tags$span(style = "background: #f3e5f5; color: #7b1fa2; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;", "scikit-learn"),
                tags$span(style = "background: #e0f7fa; color: #00796b; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;", "FastAPI"),
                tags$span(style = "background: #fff3e0; color: #e65100; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;", "Docker"),
                tags$span(style = "background: #e8eaf6; color: #283593; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;", "GitHub Actions")
              ),

              tags$h4(icon("handshake"), "KEMRI Connection"),
              tags$p("This project maps directly to KEMRI's research centres:"),
              tags$ul(
                tags$li(tags$strong("CIPDCR"), " — Malaria surveillance & control"),
                tags$li(tags$strong("CGMR-C"), " — Coastal disease patterns (Mombasa data!)"),
                tags$li(tags$strong("CPHR"), " — Public health research & outbreak prediction"),
                tags$li(tags$strong("CGHR"), " — Global health outcomes"),
                tags$li(tags$strong("ESACIPAC"), " — Cross-border parasite control")
              ),

              tags$hr(),
              tags$p(
                icon("code"), " Built by ",
                tags$strong("Calvin Omondi Okoth"),
                " | ",
                tags$a(href = "https://www.linkedin.com/in/calvin-klein-9528c2004",
                       target = "_blank", icon("linkedin"), " LinkedIn"),
                " | ",
                tags$a(href = "https://github.com/calvinokoth9528-cloud/malaria-outbreak-predictor",
                       target = "_blank", icon("github"), " GitHub"),
                style = "color: #888; font-size: 13px;"
              )
            )
          )
        )
      )
    )
  )
)

# ── Server ─────────────────────────────────────────────────────────────────────

server <- function(input, output, session) {

  # ══════════════════════════════════════════════════════════════════
  # VALUE BOXES
  # ══════════════════════════════════════════════════════════════════

  output$vb_cases <- renderValueBox({
    latest <- tail(merged$estimated_malaria_cases_value, 1)
    valueBox(
      label = format(round(latest / 1e6, 1), nsmall = 1) |> paste0("M"),
      subtitle = "Annual Cases (2024)",
      icon = icon("virus", lib = "font-awesome"),
      color = "red"
    )
  })

  output$vb_deaths <- renderValueBox({
    latest <- tail(merged$estimated_malaria_deaths_value, 1)
    valueBox(
      label = format(round(latest / 1000, 1), nsmall = 1) |> paste0("K"),
      subtitle = "Annual Deaths (2024)",
      icon = icon("skull-crossbones", lib = "font-awesome"),
      color = "black"
    )
  })

  output$vb_incidence <- renderValueBox({
    latest <- tail(merged$malaria_incidence_per_1000, 1)
    valueBox(
      label = round(latest, 1) |> as.character(),
      subtitle = "Incidence per 1,000 (2024)",
      icon = icon("chart-line", lib = "font-awesome"),
      color = "yellow"
    )
  })

  output$vb_trend <- renderValueBox({
    change <- merged$malaria_incidence_per_1000
    pct <- round(((tail(change, 1) - head(change, 1)) / head(change, 1)) * 100)
    valueBox(
      label = paste0(pct, "%"),
      subtitle = "Change Since 2000",
      icon = icon("arrow-down", lib = "font-awesome"),
      color = "green"
    )
  })

  # ══════════════════════════════════════════════════════════════════
  # TAB 1: OVERVIEW
  # ══════════════════════════════════════════════════════════════════

  output$plot_incidence_trend <- renderPlotly({
    p <- ggplot(merged, aes(x = year, y = malaria_incidence_per_1000,
                             text = paste0("Year: ", year,
                                           "<br>Incidence: ", round(malaria_incidence_per_1000, 1), " per 1,000"))) +
      geom_area(fill = "#e63946", alpha = 0.1) +
      geom_line(color = "#e63946", linewidth = 1.5) +
      geom_point(color = "#e63946", size = 4, stroke = 2, fill = "white") +
      geom_smooth(method = "loess", se = TRUE, color = "#1565c0", linetype = "dashed", alpha = 0.15, linewidth = 0.8) +
      labs(x = NULL, y = "Incidence per 1,000") +
      theme_minimal(base_size = 13) +
      theme(
        panel.grid.minor = element_blank(),
        panel.grid.major.x = element_blank(),
        plot.margin = margin(10, 15, 10, 15)
      )
    ggplotly(p, tooltip = "text") %>%
      layout(
        hoverlabel = list(bgcolor = "white", font = list(size = 12)),
        margin = list(t = 10, b = 40, l = 60, r = 20)
      ) %>%
      config(displayModeBar = TRUE, modeBarButtonsToRemove = c("lasso2d", "select2d"),
             displaylogo = FALSE, responsive = TRUE)
  })

  output$plot_cases_deaths <- renderPlotly({
    p <- merged %>%
      filter(!is.na(estimated_malaria_cases_value), !is.na(estimated_malaria_deaths_value)) %>%
      mutate(
        cases_M = estimated_malaria_cases_value / 1e6,
        deaths_K = estimated_malaria_deaths_value / 1000,
        text_cases = paste0("Year: ", year, "<br>Cases: ", round(cases_M, 1), "M"),
        text_deaths = paste0("Year: ", year, "<br>Deaths: ", round(estimated_malaria_deaths_value))
      ) %>%
      ggplot(aes(x = year)) +
      geom_col(aes(y = cases_M, text = text_cases, fill = "Cases (millions)"), alpha = 0.7) +
      geom_line(aes(y = deaths_K, text = text_deaths, color = "Deaths (thousands)"), linewidth = 1.5) +
      geom_point(aes(y = deaths_K, text = text_deaths, color = "Deaths (thousands)"), size = 3) +
      scale_fill_manual(values = c("Cases (millions)" = "#ff9800"), name = NULL) +
      scale_color_manual(values = c("Deaths (thousands)" = "#e63946"), name = NULL) +
      scale_y_continuous(
        name = "Cases (millions)",
        sec.axis = sec_axis(~. * 1000, name = "Deaths", labels = function(x) paste0(x, "K"))
      ) +
      labs(x = NULL) +
      theme_minimal(base_size = 13) +
      theme(
        panel.grid.minor = element_blank(),
        panel.grid.major.x = element_blank(),
        legend.position = "top",
        plot.margin = margin(10, 15, 10, 15)
      )
    ggplotly(p, tooltip = "text") %>%
      layout(
        hoverlabel = list(bgcolor = "white", font = list(size = 12)),
        margin = list(t = 40, b = 40, l = 60, r = 60)
      ) %>%
      config(displayModeBar = FALSE, responsive = TRUE)
  })

  # ══════════════════════════════════════════════════════════════════
  # TAB 2: CLIMATE
  # ══════════════════════════════════════════════════════════════════

  output$plot_temp_malaria <- renderPlotly({
    p <- merged %>%
      filter(!is.na(temp_mean_c), !is.na(malaria_incidence_per_1000)) %>%
      mutate(text = paste0("Year: ", year,
                           "<br>Temp: ", round(temp_mean_c, 1), "°C",
                           "<br>Malaria: ", round(malaria_incidence_per_1000, 1))) %>%
      ggplot(aes(x = temp_mean_c, y = malaria_incidence_per_1000, text = text)) +
      geom_point(color = "#f57c00", size = 5, stroke = 1.5, fill = "white") +
      geom_smooth(method = "lm", se = TRUE, color = "#e63946", linewidth = 1.2) +
      labs(x = "Mean Temperature (°C)", y = "Malaria Incidence") +
      theme_minimal(base_size = 13) +
      theme(panel.grid.minor = element_blank(), plot.margin = margin(10, 15, 10, 15))
    ggplotly(p, tooltip = "text") %>%
      config(displayModeBar = FALSE, responsive = TRUE)
  })

  output$plot_rain_malaria <- renderPlotly({
    p <- merged %>%
      filter(!is.na(precip_total_mm), !is.na(malaria_incidence_per_1000)) %>%
      mutate(text = paste0("Year: ", year,
                           "<br>Rainfall: ", round(precip_total_mm), " mm",
                           "<br>Malaria: ", round(malaria_incidence_per_1000, 1))) %>%
      ggplot(aes(x = precip_total_mm, y = malaria_incidence_per_1000, text = text)) +
      geom_point(color = "#1565c0", size = 5, stroke = 1.5, fill = "white") +
      geom_smooth(method = "lm", se = TRUE, color = "#00796b", linewidth = 1.2) +
      labs(x = "Total Precipitation (mm)", y = "Malaria Incidence") +
      theme_minimal(base_size = 13) +
      theme(panel.grid.minor = element_blank(), plot.margin = margin(10, 15, 10, 15))
    ggplotly(p, tooltip = "text") %>%
      config(displayModeBar = FALSE, responsive = TRUE)
  })

  output$plot_city_climate <- renderPlotly({
    month_names <- c("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    city_data <- climate_monthly %>%
      filter(city == tolower(input$city_select)) %>%
      group_by(month) %>%
      summarise(
        temp = mean(temp_mean_c, na.rm = TRUE),
        precip = mean(precip_total_mm, na.rm = TRUE),
        humidity = mean(humidity_mean, na.rm = TRUE),
        .groups = "drop"
      ) %>%
      mutate(month_name = factor(month_names[month], levels = month_names)) %>%
      pivot_longer(cols = c(temp, precip, humidity), names_to = "var", values_to = "val") %>%
      mutate(label = recode(var,
                             temp = "Temperature (°C)",
                             precip = "Rainfall (mm)",
                             humidity = "Humidity (%)")) %>%
      mutate(text = paste0(month_name, "<br>", label, ": ", round(val, 1)))

    p <- ggplot(city_data, aes(x = month_name, y = val, color = label, group = label, text = text)) +
      geom_line(linewidth = 1.3) +
      geom_point(size = 3, fill = "white", stroke = 1.5) +
      labs(x = NULL, y = "Value", color = NULL) +
      theme_minimal(base_size = 12) +
      theme(legend.position = "bottom", panel.grid.minor = element_blank(),
            plot.margin = margin(10, 10, 10, 10))
    ggplotly(p, tooltip = "text") %>%
      layout(legend = list(orientation = "h", y = -0.15)) %>%
      config(displayModeBar = FALSE, responsive = TRUE)
  })

  output$plot_anomaly_heatmap <- renderPlotly({
    p <- ml_features %>%
      filter(!is.na(precip_anomaly), !is.na(temp_anomaly)) %>%
      select(year, precip_anomaly, temp_anomaly) %>%
      pivot_longer(cols = c(precip_anomaly, temp_anomaly),
                   names_to = "var", values_to = "anomaly") %>%
      mutate(
        label = recode(var, precip_anomaly = "Rainfall", temp_anomaly = "Temperature"),
        text = paste0("Year: ", year, "<br>", label, " anomaly: ", round(anomaly, 1))
      ) %>%
      ggplot(aes(x = factor(year), y = label, fill = anomaly, text = text)) +
      geom_tile(color = "white", linewidth = 0.5) +
      scale_fill_gradient2(low = "#1565c0", mid = "white", high = "#e63946",
                           midpoint = 0, name = "Anomaly") +
      labs(x = NULL, y = NULL) +
      theme_minimal(base_size = 12) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1),
            panel.grid = element_blank(),
            plot.margin = margin(10, 10, 10, 10))
    ggplotly(p, tooltip = "text") %>%
      config(displayModeBar = FALSE, responsive = TRUE)
  })

  # ══════════════════════════════════════════════════════════════════
  # TAB 3: REGIONAL
  # ══════════════════════════════════════════════════════════════════

  output$plot_ea_comparison <- renderPlotly({
    p <- ea_data %>%
      filter(!is.na(malaria_incidence_per_1000)) %>%
      mutate(
        is_kenya = country == "Kenya",
        linewidth = ifelse(is_kenya, 2.5, 1),
        alpha_val = ifelse(is_kenya, 1, 0.4),
        text = paste0(country, "<br>Year: ", year,
                      "<br>Incidence: ", round(malaria_incidence_per_1000, 1))
      ) %>%
      ggplot(aes(x = year, y = malaria_incidence_per_1000, color = is_kenya,
                 group = country, alpha = alpha_val, text = text)) +
      geom_line(linewidth = 1) +
      geom_point(size = 2) +
      scale_color_manual(values = c("TRUE" = "#e63946", "FALSE" = "#bdbdbd"),
                         labels = c("East Africa", "Kenya"), name = NULL) +
      scale_alpha_identity() +
      labs(x = NULL, y = "Incidence per 1,000") +
      theme_minimal(base_size = 13) +
      theme(legend.position = "top", panel.grid.minor = element_blank(),
            plot.margin = margin(10, 15, 10, 15))
    ggplotly(p, tooltip = "text") %>%
      config(displayModeBar = FALSE, responsive = TRUE)
  })

  output$plot_ea_ranking <- renderPlotly({
    latest <- ea_data %>%
      filter(year == max(year, na.rm = TRUE), !is.na(malaria_incidence_per_1000)) %>%
      arrange(desc(malaria_incidence_per_1000))

    p <- ggplot(latest, aes(x = reorder(country, malaria_incidence_per_1000),
                             y = malaria_incidence_per_1000,
                             fill = country == "Kenya",
                             text = paste0(country, "<br>", round(malaria_incidence_per_1000, 1), " per 1,000"))) +
      geom_col() +
      coord_flip() +
      scale_fill_manual(values = c("TRUE" = "#e63946", "FALSE" = "#bdbdbd"),
                        guide = "none") +
      labs(x = NULL, y = "Incidence per 1,000") +
      theme_minimal(base_size = 12) +
      theme(panel.grid.major.y = element_blank(), panel.grid.minor = element_blank(),
            plot.margin = margin(10, 15, 10, 10))
    ggplotly(p, tooltip = "text") %>%
      config(displayModeBar = FALSE, responsive = TRUE)
  })

  output$plot_ea_trends <- renderPlotly({
    p <- ea_data %>%
      filter(!is.na(malaria_incidence_per_1000)) %>%
      group_by(country) %>%
      mutate(
        change = ((malaria_incidence_per_1000 - first(malaria_incidence_per_1000))
                  / first(malaria_incidence_per_1000)) * 100,
        is_kenya = country == "Kenya",
        text = paste0(country, "<br>Year: ", year,
                      "<br>Change: ", round(change, 1), "%")
      ) %>%
      ungroup() %>%
      ggplot(aes(x = year, y = change, color = is_kenya, group = country, text = text)) +
      geom_hline(yintercept = 0, linetype = "dashed", color = "gray60", linewidth = 0.5) +
      geom_line(linewidth = 1) +
      scale_color_manual(values = c("TRUE" = "#e63946", "FALSE" = "#bdbdbd"),
                         labels = c("East Africa", "Kenya"), name = NULL) +
      labs(x = NULL, y = "% Change from 2000") +
      theme_minimal(base_size = 13) +
      theme(legend.position = "top", panel.grid.minor = element_blank(),
            plot.margin = margin(10, 15, 10, 15))
    ggplotly(p, tooltip = "text") %>%
      config(displayModeBar = FALSE, responsive = TRUE)
  })

  # ══════════════════════════════════════════════════════════════════
  # TAB 4: PREDICTIONS
  # ══════════════════════════════════════════════════════════════════

  output$plot_predictions <- renderPlotly({
    train <- predictions %>% filter(!grepl("train", model))
    test <- predictions %>% filter(grepl("train", model))

    p <- ggplot() +
      geom_ribbon(data = test, aes(x = year, ymin = pmin(malaria_incidence_per_1000, predicted),
                                   ymax = pmax(malaria_incidence_per_1000, predicted)),
                  fill = "#c8e6c9", alpha = 0.5) +
      geom_line(data = train, aes(x = year, y = malaria_incidence_per_1000,
                                   text = paste0("Year: ", year,
                                                 "<br>Actual: ", round(malaria_incidence_per_1000, 1))),
                color = "#e63946", linewidth = 1.5) +
      geom_point(data = train, aes(x = year, y = malaria_incidence_per_1000),
                 color = "#e63946", size = 4, fill = "white", stroke = 1.5) +
      geom_line(data = train, aes(x = year, y = predicted,
                                   text = paste0("Year: ", year,
                                                 "<br>Predicted: ", round(predicted, 1))),
                color = "#1565c0", linewidth = 1.2, linetype = "dashed") +
      geom_point(data = train, aes(x = year, y = predicted),
                 color = "#1565c0", size = 3, fill = "white", stroke = 1.5) +
      geom_point(data = test, aes(x = year, y = predicted,
                                   text = paste0("Year: ", year,
                                                 "<br>Predicted: ", round(predicted, 1),
                                                 "<br>Actual: ", round(malaria_incidence_per_1000, 1))),
                 color = "#2e7d32", size = 5, shape = 18, stroke = 2) +
      annotate("text", x = mean(test$year), y = max(train$malaria_incidence_per_1000, na.rm = TRUE) * 0.95,
               label = "Test Period", color = "#2e7d32", fontface = "bold", size = 4) +
      labs(x = NULL, y = "Incidence per 1,000") +
      theme_minimal(base_size = 13) +
      theme(panel.grid.minor = element_blank(), panel.grid.major.x = element_blank(),
            plot.margin = margin(10, 15, 10, 15))
    ggplotly(p, tooltip = "text") %>%
      layout(
        hoverlabel = list(bgcolor = "white", font = list(size = 12)),
        margin = list(t = 10, b = 40, l = 60, r = 20)
      ) %>%
      config(displayModeBar = FALSE, responsive = TRUE)
  })

  output$dt_predictions <- renderDT({
    predictions %>%
      select(year, malaria_incidence_per_1000, predicted, residual, model) %>%
      mutate(across(where(is.numeric), ~ round(., 2))) %>%
      datatable(
        options = list(
          pageLength = 10, dom = "ftip",
          columnDefs = list(
            list(className = "dt-center", targets = 0:4)
          )
        ),
        caption = htmltools::tags$caption(
          style = "caption-side: top; text-align: left; font-size: 13px; color: #888; padding: 5px;",
          "Model predictions by year. Click column headers to sort."
        ),
        rownames = FALSE
      ) %>%
      formatStyle("residual",
                  backgroundColor = styleInterval(
                    c(-5, 5),
                    c("rgba(46, 125, 50, 0.1)", "transparent", "rgba(230, 57, 70, 0.1)")
                  ))
  })

  # ══════════════════════════════════════════════════════════════════
  # TAB 5: SIMULATOR
  # ══════════════════════════════════════════════════════════════════

  sim_result <- eventReactive(input$run_sim, {
    lag1 <- input$sim_lag1
    precip <- input$sim_precip
    temp <- input$sim_temp
    humidity <- input$sim_humidity
    population <- input$sim_population * 1e6
    urban <- input$sim_urban

    pred <- lag1 * 0.45 +
      (precip / 100) * 2.5 +
      (temp - 21) * 5 +
      (humidity - 70) * 0.3 +
      (urban / 10) * (-0.5) +
      rnorm(1, 0, 1.5)

    pred <- max(10, min(300, pred))

    list(
      prediction = round(pred, 1),
      risk = case_when(
        pred < 50 ~ "LOW",
        pred < 80 ~ "MODERATE",
        pred < 120 ~ "HIGH",
        TRUE ~ "VERY HIGH"
      ),
      color = case_when(
        pred < 50 ~ "#2e7d32",
        pred < 80 ~ "#f57c00",
        pred < 120 ~ "#e65100",
        TRUE ~ "#c62828"
      ),
      bg = case_when(
        pred < 50 ~ "#e8f5e9",
        pred < 80 ~ "#fff3e0",
        pred < 120 ~ "#fbe9e7",
        TRUE -> "#ffebee"
      ),
      explanation = case_when(
        pred < 50 ~ "Low risk. Current conditions are favorable for malaria control. Maintain surveillance.",
        pred < 80 ~ "Moderate risk. Increased monitoring recommended. Consider pre-positioning diagnostic kits.",
        pred < 120 ~ "High risk. Deploy rapid response teams. Increase bed net distribution and ACT supplies.",
        TRUE ~ "Critical risk. Emergency response needed. Activate all available malaria control resources."
      )
    )
  })

  output$plot_sim_result <- renderPlotly({
    res <- sim_result()
    all_years <- merged$year
    all_incidence <- merged$malaria_incidence_per_1000

    sim_year <- 2025
    sim_value <- res$prediction

    plot_data <- data.frame(
      year = c(all_years, sim_year),
      incidence = c(all_incidence, sim_value),
      type = c(rep("Historical", length(all_years)), "Simulated"),
      text = c(paste0("Year: ", all_years,
                       "<br>Actual: ", round(all_incidence, 1)),
               paste0("Year: 2025<br>Predicted: ", sim_value))
    )

    p <- ggplot(plot_data, aes(x = year, y = incidence, color = type, text = text)) +
      geom_line(aes(linewidth = type)) +
      geom_point(aes(size = type)) +
      scale_color_manual(values = c("Historical" = "#e63946", "Simulated" = "#1565c0"), name = NULL) +
      scale_linewidth_manual(values = c("Historical" = 1.5, "Simulated" = 2.5), guide = "none") +
      scale_size_manual(values = c("Historical" = 3, "Simulated" = 6), guide = "none") +
      labs(x = NULL, y = "Incidence per 1,000") +
      theme_minimal(base_size = 13) +
      theme(legend.position = "top", panel.grid.minor = element_blank(),
            plot.margin = margin(10, 15, 10, 15))
    ggplotly(p, tooltip = "text") %>%
      config(displayModeBar = FALSE, responsive = TRUE)
  })

  output$sim_risk_box <- renderUI({
    res <- sim_result()
    tags$div(
      style = paste0("padding: 20px; margin-top: 15px; border-radius: 12px; ",
                      "background: ", res$bg, "; border-left: 5px solid ", res$color, ";"),
      tags$div(style = "display: flex; justify-content: space-between; align-items: center;",
        tags$div(
          tags$div(style = paste0("font-size: 36px; font-weight: 700; color: ", res$color, ";"),
                   paste(res$prediction, "per 1,000")),
          tags$div(style = paste0("font-size: 16px; font-weight: 600; color: ", res$color, ";"),
                   paste("Risk Level:", res$risk))
        )
      )
    )
  })

  output$sim_explanation <- renderUI({
    res <- sim_result()
    tags$div(
      style = paste0("padding: 12px 15px; border-radius: 8px; background: #fafafa; ",
                      "border-left: 3px solid ", res$color, "; font-size: 13px; color: #555;"),
      icon("lightbulb", lib = "font-awesome", style = paste0("color: ", res$color)),
      tags$strong(" Recommendation: "), res$explanation
    )
  })
}

# ── Run ────────────────────────────────────────────────────────────────────────

shinyApp(ui = ui, server = server)
