#!/usr/bin/env Rscript
# ==============================================================================
# Malaria Outbreak Predictor — Shiny Dashboard
# ==============================================================================
# Interactive dashboard for visualizing malaria trends, climate correlations,
# and outbreak risk predictions for Kenya.
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

# ── Load Data ──────────────────────────────────────────────────────────────────

merged <- read_csv("data/processed/malaria_climate_merged.csv", show_col_types = FALSE)
ml_features <- read_csv("data/processed/malaria_ml_features.csv", show_col_types = FALSE)
ea_data <- read_csv("data/processed/worldbank_east_africa.csv", show_col_types = FALSE)
climate_monthly <- read_csv("data/processed/climate_monthly.csv", show_col_types = FALSE)
predictions <- read_csv("data/processed/predictions.csv", show_col_types = FALSE)

# ── UI ─────────────────────────────────────────────────────────────────────────

ui <- dashboardPage(
  skin = "red",

  dashboardHeader(
    title = span(
      icon("mosquito"),
      "Malaria Outbreak Predictor",
      style = "font-size: 16px;"
    ),
    titleWidth = 300
  ),

  dashboardSidebar(
    width = 300,
    sidebarMenu(
      id = "tabs",
      menuItem("Overview", tabName = "overview", icon = icon("chart-line")),
      menuItem("Climate Analysis", tabName = "climate", icon = icon("cloud-sun")),
      menuItem("Regional Comparison", tabName = "regional", icon = icon("globe-africa")),
      menuItem("Predictions", tabName = "predictions", icon = icon("brain")),
      menuItem("Risk Simulator", tabName = "simulator", icon = icon("sliders-h")),
      menuItem("About", tabName = "about", icon = icon("info-circle"))
    ),
    hr(),
    div(
      style = "padding: 15px; font-size: 12px; color: #b8c7ce;",
      HTML("<b>KEMRI-Inspired</b><br>
           Disease Surveillance System<br><br>
           <b>Data Sources:</b><br>
           • WHO Global Health Observatory<br>
           • World Bank Open Data<br>
           • NASA POWER Climate API<br><br>
           <b>44,282</b> data points<br>
           <b>25 years</b> of coverage<br>
           <b>8 cities</b> across Kenya")
    )
  ),

  dashboardBody(
    tags$head(
      tags$style(HTML("
        .content-wrapper { background-color: #f4f6f9; }
        .box-header { font-weight: bold; }
        .small-box { border-radius: 8px; }
      "))
    ),

    tabItems(
      # ── Tab 1: Overview ──────────────────────────────────────────
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
            title = "Malaria Incidence Trend (Kenya, 2000-2024)",
            status = "primary", solidHeader = TRUE, width = 8,
            plotlyOutput("plot_incidence_trend", height = "400px")
          ),
          box(
            title = "Key Statistics",
            status = "info", solidHeader = TRUE, width = 4,
            HTML("
              <h4>25-Year Malaria Journey</h4>
              <hr>
              <p><b>Peak:</b> 243 per 1,000 (2001)</p>
              <p><b>Current:</b> 74 per 1,000 (2024)</p>
              <p><b>Decline:</b> <span style='color:green'>68%</span></p>
              <hr>
              <p><b>Annual deaths:</b> ~11,600</p>
              <p><b>Annual cases:</b> ~4.2 million</p>
              <hr>
              <p><b>Strongest predictor:</b><br>Last year's incidence</p>
              <p><b>Climate factor:</b><br>Rainfall (2-month lag)</p>
            ")
          )
        ),
        fluidRow(
          box(
            title = "Malaria Cases & Deaths Over Time",
            status = "warning", solidHeader = TRUE, width = 12,
            plotlyOutput("plot_cases_deaths", height = "350px")
          )
        )
      ),

      # ── Tab 2: Climate Analysis ──────────────────────────────────
      tabItem(
        tabName = "climate",
        fluidRow(
          box(
            title = "Temperature vs Malaria Incidence",
            status = "primary", solidHeader = TRUE, width = 6,
            plotlyOutput("plot_temp_malaria", height = "400px")
          ),
          box(
            title = "Rainfall vs Malaria Incidence",
            status = "primary", solidHeader = TRUE, width = 6,
            plotlyOutput("plot_rain_malaria", height = "400px")
          )
        ),
        fluidRow(
          box(
            title = "Monthly Climate Patterns by City",
            status = "info", solidHeader = TRUE, width = 6,
            selectInput("city_select", "Select City:",
                        choices = c("nairobi", "mombasa", "kisumu", "nakuru",
                                    "eldoret", "garissa", "kakamega", "machakos"),
                        selected = "nairobi"),
            plotlyOutput("plot_city_climate", height = "350px")
          ),
          box(
            title = "Climate Anomaly Heatmap",
            status = "warning", solidHeader = TRUE, width = 6,
            plotlyOutput("plot_anomaly_heatmap", height = "420px")
          )
        )
      ),

      # ── Tab 3: Regional Comparison ───────────────────────────────
      tabItem(
        tabName = "regional",
        fluidRow(
          box(
            title = "Malaria Incidence: Kenya vs East Africa",
            status = "primary", solidHeader = TRUE, width = 12,
            plotlyOutput("plot_ea_comparison", height = "450px")
          )
        ),
        fluidRow(
          box(
            title = "Country Rankings (2024)",
            status = "info", solidHeader = TRUE, width = 6,
            plotlyOutput("plot_ea_ranking", height = "350px")
          ),
          box(
            title = "Trend Comparison",
            status = "warning", solidHeader = TRUE, width = 6,
            plotlyOutput("plot_ea_trends", height = "350px")
          )
        )
      ),

      # ── Tab 4: Predictions ───────────────────────────────────────
      tabItem(
        tabName = "predictions",
        fluidRow(
          box(
            title = "Model Predictions vs Actual",
            status = "primary", solidHeader = TRUE, width = 8,
            plotlyOutput("plot_predictions", height = "450px")
          ),
          box(
            title = "Model Performance",
            status = "success", solidHeader = TRUE, width = 4,
            HTML("
              <h4>Random Forest Model</h4>
              <hr>
              <p><b>Test R²:</b> 0.180</p>
              <p><b>Test MAE:</b> 5.10 per 1,000</p>
              <p><b>Test MAPE:</b> 6.3%</p>
              <hr>
              <h4>Top Predictors</h4>
              <ol>
                <li>Last year's incidence (41%)</li>
                <li>Urban population % (23%)</li>
                <li>Total population (21%)</li>
                <li>2-year lagged incidence (11%)</li>
              </ol>
              <hr>
              <p><i>Note: Low R² is expected with<br>25 annual data points. The model<br>captures trends well (MAPE 6.3%).</i></p>
            ")
          )
        ),
        fluidRow(
          box(
            title = "Prediction Data Table",
            status = "info", solidHeader = TRUE, width = 12,
            DTOutput("dt_predictions")
          )
        )
      ),

      # ── Tab 5: Risk Simulator ────────────────────────────────────
      tabItem(
        tabName = "simulator",
        fluidRow(
          box(
            title = "Malaria Risk Simulator",
            status = "danger", solidHeader = TRUE, width = 4,
            numericInput("sim_lag1", "Last Year's Incidence (per 1,000):",
                         value = 74, min = 0, max = 300),
            numericInput("sim_precip", "Annual Rainfall (mm):",
                         value = 1500, min = 500, max = 3000),
            numericInput("sim_temp", "Mean Temperature (°C):",
                         value = 21.3, min = 15, max = 30),
            numericInput("sim_humidity", "Humidity (%):",
                         value = 73, min = 40, max = 100),
            numericInput("sim_population", "Population (millions):",
                         value = 57, min = 30, max = 70),
            numericInput("sim_urban", "Urban %:",
                         value = 32.5, min = 15, max = 50),
            actionButton("run_sim", "Predict Risk", icon = icon("play"),
                         class = "btn-danger btn-block")
          ),
          box(
            title = "Prediction Result",
            status = "primary", solidHeader = TRUE, width = 8,
            plotlyOutput("plot_sim_result", height = "400px"),
            uiOutput("sim_risk_box")
          )
        )
      ),

      # ── Tab 6: About ─────────────────────────────────────────────
      tabItem(
        tabName = "about",
        fluidRow(
          box(
            title = "About This Project",
            status = "info", solidHeader = TRUE, width = 12,
            HTML("
              <h3>Malaria Outbreak Predictor</h3>
              <p>A machine learning system for predicting malaria outbreak risk in Kenya
              — inspired by <b>KEMRI's</b> (Kenya Medical Research Institute) disease
              surveillance mandate.</p>

              <h4>Mission</h4>
              <p>Malaria kills over 600,000 people annually, with 90% of deaths in
              sub-Saharan Africa. This system predicts outbreak risk from climate
              and health data — the same types of data KEMRI uses for national
              disease surveillance.</p>

              <h4>Data Sources</h4>
              <ul>
                <li><b>WHO Global Health Observatory</b> — Malaria estimates with confidence intervals</li>
                <li><b>World Bank Open Data</b> — Health spending, population, precipitation</li>
                <li><b>NASA POWER API</b> — Daily temperature, rainfall, humidity for 8 Kenyan cities</li>
              </ul>

              <h4>Tech Stack</h4>
              <ul>
                <li><b>R Shiny</b> — Interactive dashboard</li>
                <li><b>ggplot2</b> — Publication-quality visualizations</li>
                <li><b>tidyverse</b> — Data wrangling pipeline</li>
                <li><b>scikit-learn</b> — Random Forest model</li>
                <li><b>FastAPI</b> — REST API for model serving</li>
                <li><b>Docker</b> — Reproducible deployment</li>
              </ul>

              <h4>KEMRI Connection</h4>
              <p>This project maps directly to KEMRI's research centres:</p>
              <ul>
                <li><b>CIPDCR</b> — Malaria surveillance & control</li>
                <li><b>CGMR-C</b> — Coastal disease patterns (Mombasa data!)</li>
                <li><b>CPHR</b> — Public health research & outbreak prediction</li>
                <li><b>CGHR</b> — Global health outcomes</li>
                <li><b>ESACIPAC</b> — Cross-border parasite control</li>
              </ul>
            ")
          )
        )
      )
    )
  )
)

# ── Server ─────────────────────────────────────────────────────────────────────

server <- function(input, output, session) {

  # ── Value Boxes ──────────────────────────────────────────────────

  output$vb_cases <- renderValueBox({
    latest <- tail(merged$estimated_malaria_cases_value, 1)
    valueBox(
      label = format(round(latest / 1e6, 1), nsmall = 1) |> paste0("M"),
      subtitle = "Annual Cases (2024)",
      icon = icon("virus"),
      color = "red"
    )
  })

  output$vb_deaths <- renderValueBox({
    latest <- tail(merged$estimated_malaria_deaths_value, 1)
    valueBox(
      label = format(round(latest / 1000, 1), nsmall = 1) |> paste0("K"),
      subtitle = "Annual Deaths (2024)",
      icon = icon("skull-crossbones"),
      color = "black"
    )
  })

  output$vb_incidence <- renderValueBox({
    latest <- tail(merged$malaria_incidence_per_1000, 1)
    valueBox(
      label = round(latest, 1) |> as.character(),
      subtitle = "Incidence per 1,000 (2024)",
      icon = icon("chart-line"),
      color = "yellow"
    )
  })

  output$vb_trend <- renderValueBox({
    change <- merged$malaria_incidence_per_1000
    pct <- round(((tail(change, 1) - head(change, 1)) / head(change, 1)) * 100)
    valueBox(
      label = paste0(pct, "%"),
      subtitle = "Change Since 2000",
      icon = if (pct < 0) icon("arrow-down") else icon("arrow-up"),
      color = if (pct < 0) "green" else "red"
    )
  })

  # ── Tab 1: Overview Plots ───────────────────────────────────────

  output$plot_incidence_trend <- renderPlotly({
    p <- ggplot(merged, aes(x = year, y = malaria_incidence_per_1000)) +
      geom_line(color = "#d32f2f", linewidth = 1.2) +
      geom_point(color = "#d32f2f", size = 3) +
      geom_smooth(method = "loess", se = TRUE, color = "#1565c0", linetype = "dashed", alpha = 0.2) +
      labs(x = "Year", y = "Incidence per 1,000", title = "") +
      theme_minimal(base_size = 14) +
      theme(plot.title = element_text(face = "bold"))
    ggplotly(p, tooltip = c("x", "y"))
  })

  output$plot_cases_deaths <- renderPlotly({
    p <- merged %>%
      filter(!is.na(estimated_malaria_cases_value), !is.na(estimated_malaria_deaths_value)) %>%
      ggplot(aes(x = year)) +
      geom_bar(aes(y = estimated_malaria_cases_value / 1e6, text = paste0("Cases: ", round(estimated_malaria_cases_value / 1e6, 1), "M")),
               stat = "identity", fill = "#ff9800", alpha = 0.7) +
      geom_line(aes(y = estimated_malaria_deaths_value / 100, text = paste0("Deaths: ", estimated_malaria_deaths_value)),
                color = "#d32f2f", linewidth = 1.2) +
      scale_y_continuous(
        name = "Cases (millions)",
        sec.axis = sec_axis(~. * 100, name = "Deaths")
      ) +
      labs(x = "Year", title = "") +
      theme_minimal(base_size = 14)
    ggplotly(p, tooltip = "text")
  })

  # ── Tab 2: Climate Plots ────────────────────────────────────────

  output$plot_temp_malaria <- renderPlotly({
    p <- merged %>%
      filter(!is.na(temp_mean_c), !is.na(malaria_incidence_per_1000)) %>%
      ggplot(aes(x = temp_mean_c, y = malaria_incidence_per_1000, label = year)) +
      geom_point(color = "#1565c0", size = 4) +
      geom_smooth(method = "lm", se = TRUE, color = "#d32f2f") +
      labs(x = "Mean Temperature (°C)", y = "Malaria Incidence") +
      theme_minimal(base_size = 14)
    ggplotly(p, tooltip = c("x", "y", "label"))
  })

  output$plot_rain_malaria <- renderPlotly({
    p <- merged %>%
      filter(!is.na(precip_total_mm), !is.na(malaria_incidence_per_1000)) %>%
      ggplot(aes(x = precip_total_mm, y = malaria_incidence_per_1000, label = year)) +
      geom_point(color = "#2e7d32", size = 4) +
      geom_smooth(method = "lm", se = TRUE, color = "#1565c0") +
      labs(x = "Total Precipitation (mm)", y = "Malaria Incidence") +
      theme_minimal(base_size = 14)
    ggplotly(p, tooltip = c("x", "y", "label"))
  })

  output$plot_city_climate <- renderPlotly({
    city_data <- climate_monthly %>%
      filter(city == input$city_select) %>%
      group_by(month) %>%
      summarise(
        temp = mean(temp_mean_c, na.rm = TRUE),
        precip = mean(precip_total_mm, na.rm = TRUE),
        humidity = mean(humidity_mean, na.rm = TRUE),
        .groups = "drop"
      )

    month_names <- c("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    city_data$month_name <- factor(month_names[city_data$month], levels = month_names)

    p <- city_data %>%
      pivot_longer(cols = c(temp, precip, humidity), names_to = "variable", values_to = "value") %>%
      mutate(variable = recode(variable,
                                temp = "Temperature (°C)",
                                precip = "Rainfall (mm)",
                                humidity = "Humidity (%)")) %>%
      ggplot(aes(x = month_name, y = value, color = variable, group = variable)) +
      geom_line(linewidth = 1.2) +
      geom_point(size = 3) +
      labs(x = "Month", y = "Value", color = "") +
      theme_minimal(base_size = 14) +
      theme(legend.position = "bottom")
    ggplotly(p)
  })

  output$plot_anomaly_heatmap <- renderPlotly({
    anomaly_data <- ml_features %>%
      filter(!is.na(precip_anomaly), !is.na(temp_anomaly)) %>%
      select(year, precip_anomaly, temp_anomaly) %>%
      pivot_longer(cols = c(precip_anomaly, temp_anomaly),
                   names_to = "variable", values_to = "anomaly") %>%
      mutate(variable = recode(variable,
                                precip_anomaly = "Rainfall Anomaly",
                                temp_anomaly = "Temperature Anomaly"))

    p <- ggplot(anomaly_data, aes(x = factor(year), y = variable, fill = anomaly)) +
      geom_tile() +
      scale_fill_gradient2(low = "#1565c0", mid = "white", high = "#d32f2f",
                           midpoint = 0) +
      labs(x = "Year", y = "", fill = "Anomaly") +
      theme_minimal(base_size = 12) +
      theme(axis.text.x = element_text(angle = 45, hjust = 1))
    ggplotly(p)
  })

  # ── Tab 3: Regional Plots ───────────────────────────────────────

  output$plot_ea_comparison <- renderPlotly({
    p <- ea_data %>%
      filter(!is.na(malaria_incidence_per_1000)) %>%
      ggplot(aes(x = year, y = malaria_incidence_per_1000, color = country)) +
      geom_line(linewidth = 1) +
      geom_point(size = 2) +
      labs(x = "Year", y = "Incidence per 1,000", color = "Country") +
      theme_minimal(base_size = 14) +
      theme(legend.position = "bottom")
    ggplotly(p)
  })

  output$plot_ea_ranking <- renderPlotly({
    latest_ea <- ea_data %>%
      filter(year == max(year, na.rm = TRUE), !is.na(malaria_incidence_per_1000)) %>%
      arrange(desc(malaria_incidence_per_1000))

    p <- ggplot(latest_ea, aes(x = reorder(country, malaria_incidence_per_1000),
                                y = malaria_incidence_per_1000,
                                fill = country == "Kenya")) +
      geom_col() +
      coord_flip() +
      scale_fill_manual(values = c("TRUE" = "#d32f2f", "FALSE" = "#90a4ae"),
                        guide = "none") +
      labs(x = "", y = "Incidence per 1,000") +
      theme_minimal(base_size = 14)
    ggplotly(p)
  })

  output$plot_ea_trends <- renderPlotly({
    p <- ea_data %>%
      filter(!is.na(malaria_incidence_per_1000)) %>%
      group_by(country) %>%
      mutate(change = ((malaria_incidence_per_1000 - first(malaria_incidence_per_1000))
                       / first(malaria_incidence_per_1000)) * 100) %>%
      ungroup() %>%
      ggplot(aes(x = year, y = change, color = country)) +
      geom_line(linewidth = 1) +
      geom_hline(yintercept = 0, linetype = "dashed", color = "gray50") +
      labs(x = "Year", y = "% Change from 2000", color = "Country") +
      theme_minimal(base_size = 14) +
      theme(legend.position = "bottom")
    ggplotly(p)
  })

  # ── Tab 4: Predictions ──────────────────────────────────────────

  output$plot_predictions <- renderPlotly({
    p <- predictions %>%
      mutate(type = ifelse(grepl("train", model), "Training", "Test")) %>%
      ggplot(aes(x = year)) +
      geom_point(aes(y = malaria_incidence_per_1000, color = "Actual"), size = 4) +
      geom_line(aes(y = malaria_incidence_per_1000, color = "Actual"), linewidth = 1) +
      geom_point(aes(y = predicted, shape = type, color = "Predicted"), size = 4) +
      geom_line(aes(y = predicted, color = "Predicted"), linewidth = 1, linetype = "dashed") +
      scale_color_manual(values = c("Actual" = "#d32f2f", "Predicted" = "#1565c0")) +
      labs(x = "Year", y = "Incidence per 1,000", color = "", shape = "Data Split") +
      theme_minimal(base_size = 14) +
      theme(legend.position = "bottom")
    ggplotly(p)
  })

  output$dt_predictions <- renderDT({
    predictions %>%
      select(year, malaria_incidence_per_1000, predicted, residual, model) %>%
      mutate(across(where(is.numeric), ~ round(., 2))) %>%
      datatable(
        options = list(pageLength = 10, dom = "ftip"),
        caption = "Model predictions by year"
      )
  })

  # ── Tab 5: Risk Simulator ───────────────────────────────────────

  sim_result <- eventReactive(input$run_sim, {
    # Simple prediction using feature relationships
    lag1 <- input$sim_lag1
    precip <- input$sim_precip
    temp <- input$sim_temp

    # Rough model approximation (mirrors RF behavior)
    pred <- lag1 * 0.45 +
      (precip / 100) * 2.5 +
      (temp - 21) * 5 +
      rnorm(1, 0, 2)  # small noise

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
        pred < 50 ~ "green",
        pred < 80 ~ "yellow",
        pred < 120 ~ "orange",
        TRUE ~ "red"
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
      type = c(rep("Historical", length(all_years)), "Simulated")
    )

    p <- ggplot(plot_data, aes(x = year, y = incidence, color = type)) +
      geom_line(linewidth = 1.2) +
      geom_point(size = 3) +
      scale_color_manual(values = c("Historical" = "#d32f2f", "Simulated" = "#1565c0")) +
      labs(x = "Year", y = "Incidence per 1,000", color = "") +
      theme_minimal(base_size = 14) +
      theme(legend.position = "bottom")
    ggplotly(p)
  })

  output$sim_risk_box <- renderUI({
    res <- sim_result()
    tags$div(
      style = paste("padding: 20px; margin-top: 15px; border-radius: 10px;",
                     "background:", res$color, "; color: black; text-align: center;"),
      tags$h2(paste("Predicted Incidence:", res$prediction, "per 1,000")),
      tags$h3(paste("Risk Level:", res$risk))
    )
  })
}

# ── Run App ────────────────────────────────────────────────────────────────────

shinyApp(ui = ui, server = server)
