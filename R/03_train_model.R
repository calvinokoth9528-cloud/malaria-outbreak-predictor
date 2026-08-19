# ==============================================================================
# Malaria Outbreak Predictor — Step 3: Machine Learning Models
# ==============================================================================
# Input:  data/processed/malaria_ml_features.csv
# Output: data/processed/predictions.csv, models/rf_model.rds
#
# Packages: tidyverse, tidymodels, ranger
# Run:      Rscript R/03_train_model.R
# ==============================================================================

library(tidyverse)
library(tidymodels)

# ── Configuration ──────────────────────────────────────────────────────────────

set.seed(42)

PROC_DIR <- file.path("data", "processed")
MODEL_DIR <- file.path("models")
dir.create(MODEL_DIR, showWarnings = FALSE, recursive = TRUE)

cat(strrep("=", 70), "\n")
cat("  Malaria Outbreak Predictor — ML Training\n")
cat(strrep("=", 70), "\n\n")


# ── 1. Load & Prepare Data ────────────────────────────────────────────────────

cat("[1/5] Loading and preparing data...\n")

ml_data <- read_csv(file.path(PROC_DIR, "malaria_ml_features.csv"), show_col_types = FALSE)

# Select features for modeling
model_data <- ml_data %>%
  select(
    year,
    # Target
    malaria_incidence_per_1000,
    # Features
    incidence_lag1, incidence_lag2,
    precip_total_mm, precip_lag1, precip_lag2,
    temp_mean_c, temp_lag1, temp_lag2,
    humidity_mean,
    precip_anomaly, temp_anomaly,
    population_total, urban_population_pct,
    health_expenditure_pct_gdp,
    malaria_deaths,
    precip_days, wind_mean_ms, solar_mean_mj
  ) %>%
  filter(!is.na(incidence_lag1))

cat(sprintf("  %d rows x %d columns\n", nrow(model_data), ncol(model_data)))


# ── 2. Train/Test Split (Time Series) ─────────────────────────────────────────

cat("\n[2/5] Creating time-series split...\n")

# Use 2001-2019 for training, 2020-2024 for testing
split_year <- 2020
train_data <- model_data %>% filter(year < split_year)
test_data  <- model_data %>% filter(year >= split_year)

cat(sprintf("  Training: %d years (%d-%d)\n", nrow(train_data), min(train_data$year), max(train_data$year)))
cat(sprintf("  Testing:  %d years (%d-%d)\n", nrow(test_data), min(test_data$year), max(test_data$year)))


# ── 3. Define & Train Models ──────────────────────────────────────────────────

cat("\n[3/5] Training models...\n")

# Features (exclude target and year)
feature_cols <- setdiff(names(model_data), c("year", "malaria_incidence_per_1000"))
formula_str  <- as.formula(paste("malaria_incidence_per_1000 ~", paste(feature_cols, collapse = " + ")))

results <- list()

# ── Model 1: Ridge Regression ─────────────────────────────────────────────────
cat("  Training Ridge Regression...\n")
ridge_spec <- linear_reg(mixture = 0, penalty = 0.1) %>%
  set_engine("glmnet") %>%
  set_mode("regression")

ridge_fit <- ridge_spec %>%
  fit(formula_str, data = train_data)

ridge_pred <- predict(ridge_fit, test_data) %>%
  bind_cols(test_data %>% select(year, malaria_incidence_per_1000))

ridge_metrics <- ridge_pred %>%
  metrics(truth = malaria_incidence_per_1000, estimate = .pred)

results$ridge <- ridge_metrics
cat(sprintf("    RMSE: %.2f, R-sq: %.3f\n",
            ridge_metrics$.estimate[ridge_metrics$.metric == "rmse"],
            ridge_metrics$.estimate[ridge_metrics$.metric == "rsq"]))


# ── Model 2: Random Forest ────────────────────────────────────────────────────
cat("  Training Random Forest...\n")
rf_spec <- rand_forest(mtry = 5, trees = 500, min_n = 3) %>%
  set_engine("ranger", importance = "impurity") %>%
  set_mode("regression")

rf_fit <- rf_spec %>%
  fit(formula_str, data = train_data)

rf_pred <- predict(rf_fit, test_data) %>%
  bind_cols(test_data %>% select(year, malaria_incidence_per_1000))

rf_metrics <- rf_pred %>%
  metrics(truth = malaria_incidence_per_1000, estimate = .pred)

results$rf <- rf_metrics
cat(sprintf("    RMSE: %.2f, R-sq: %.3f\n",
            rf_metrics$.estimate[rf_metrics$.metric == "rmse"],
            rf_metrics$.estimate[rf_metrics$.metric == "rsq"]))


# ── Model 3: Gradient Boosting ────────────────────────────────────────────────
cat("  Training Gradient Boosting...\n")
gbm_spec <- boost_tree(tree_depth = 4, trees = 200, learn_rate = 0.1) %>%
  set_engine("xgboost") %>%
  set_mode("regression")

gbm_fit <- gbm_spec %>%
  fit(formula_str, data = train_data)

gbm_pred <- predict(gbm_fit, test_data) %>%
  bind_cols(test_data %>% select(year, malaria_incidence_per_1000))

gbm_metrics <- gbm_pred %>%
  metrics(truth = malaria_incidence_per_1000, estimate = .pred)

results$gbm <- gbm_metrics
cat(sprintf("    RMSE: %.2f, R-sq: %.3f\n",
            gbm_metrics$.estimate[gbm_metrics$.metric == "rmse"],
            gbm_metrics$.estimate[gbm_metrics$.metric == "rsq"]))


# ── Model 4: Linear Regression (baseline) ─────────────────────────────────────
cat("  Training Linear Regression (baseline)...\n")
lm_spec <- linear_reg() %>%
  set_engine("lm") %>%
  set_mode("regression")

lm_fit <- lm_spec %>%
  fit(formula_str, data = train_data)

lm_pred <- predict(lm_fit, test_data) %>%
  bind_cols(test_data %>% select(year, malaria_incidence_per_1000))

lm_metrics <- lm_pred %>%
  metrics(truth = malaria_incidence_per_1000, estimate = .pred)

results$lm <- lm_metrics
cat(sprintf("    RMSE: %.2f, R-sq: %.3f\n",
            lm_metrics$.estimate[lm_metrics$.metric == "rmse"],
            lm_metrics$.estimate[lm_metrics$.metric == "rsq"]))


# ── 4. Compare Models ─────────────────────────────────────────────────────────

cat("\n[4/5] Comparing models...\n")

comparison <- bind_rows(
  results$ridge %>% mutate(model = "Ridge"),
  results$rf    %>% mutate(model = "Random Forest"),
  results$gbm   %>% mutate(model = "Gradient Boosting"),
  results$lm    %>% mutate(model = "Linear Regression")
) %>%
  filter(.metric %in% c("rmse", "rsq", "mae")) %>%
  select(model, .metric, .estimate) %>%
  pivot_wider(names_from = .metric, values_from = .estimate) %>%
  mutate(mape = rmse / mean(model_data$malaria_incidence_per_1000) * 100) %>%
  arrange(rmse)

print(comparison)

best_model_name <- comparison$model[1]
cat(sprintf("\n  Best model: %s\n", best_model_name))


# ── 5. Save Predictions & Model ───────────────────────────────────────────────

cat("\n[5/5] Saving predictions and model...\n")

# Use the best model for predictions
if (best_model_name == "Random Forest") {
  best_fit <- rf_fit
} else if (best_model_name == "Gradient Boosting") {
  best_fit <- gbm_fit
} else if (best_model_name == "Ridge") {
  best_fit <- ridge_fit
} else {
  best_fit <- lm_fit
}

# Full predictions (train + test)
all_pred <- predict(best_fit, model_data) %>%
  bind_cols(model_data %>% select(year, malaria_incidence_per_1000)) %>%
  mutate(
    residual = malaria_incidence_per_1000 - .pred,
    model    = ifelse(year < split_year, "train", "test")
  ) %>%
  rename(predicted = .pred)

write_csv(all_pred, file.path(PROC_DIR, "predictions.csv"))
cat("  Saved predictions.csv\n")

# Save the best model
saveRDS(best_fit, file.path(MODEL_DIR, "best_model.rds"))
cat("  Saved best_model.rds\n")

# ── 6. Feature Importance (for tree-based models) ────────────────────────────

if (best_model_name %in% c("Random Forest", "Gradient Boosting")) {
  cat("\n  Feature Importance:\n")
  importance <- best_fit$fit$fit$fit$importance %>%
    enframe(name = "feature", value = "importance") %>%
    arrange(desc(importance)) %>%
    mutate(pct = importance / sum(importance) * 100)
  print(head(importance, 10))
}

cat("\n", strrep("=", 70), "\n")
cat("  ML Training Complete!\n")
cat(strrep("=", 70), "\n")
cat("\nNext: Rscript R/04_shiny_app.R\n")
