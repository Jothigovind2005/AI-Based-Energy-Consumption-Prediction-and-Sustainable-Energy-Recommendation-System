"""
Model Training and Comparison Pipeline.
Trains and compares:
1. Linear Regression
2. Decision Tree Regressor
3. Random Forest Regressor
4. Gradient Boosting Regressor

Computes MAE, RMSE, R² Score, and MAPE.
Saves the best model and performance metrics for the web application.
"""

import os
import csv
import json
import pickle
import numpy as np
from datetime import datetime

from ml_engine import (
    LinearRegressionModel,
    DecisionTreeRegressorModel,
    RandomForestRegressorModel,
    GradientBoostingRegressorModel,
    StandardScaler,
    train_test_split,
    mean_absolute_error,
    root_mean_squared_error,
    r2_score,
    mean_absolute_percentage_error
)

FEATURE_COLUMNS = [
    "Occupants",
    "Lights",
    "Fans",
    "AC_Usage_Hours",
    "Computer_Usage_Hours",
    "Appliance_Operating_Hours",
    "Temperature",
    "Humidity",
    "Is_Weekend",
    "Hour",
    "Month",
    "Cooling_Degree",
    "Total_Appliance_Hours"
]

def load_and_preprocess_dataset(csv_path="dataset/energy_data.csv"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    features = []
    targets = []
    raw_records = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Parse basic features
                occupants = float(row.get("Occupants", 1))
                lights = float(row.get("Lights", 2))
                fans = float(row.get("Fans", 1))
                ac_hours = float(row.get("AC_Usage_Hours", 0))
                comp_hours = float(row.get("Computer_Usage_Hours", 0))
                appliance_hours = float(row.get("Appliance_Operating_Hours", 0.5))
                temperature = float(row.get("Temperature", 25.0))
                humidity = float(row.get("Humidity", 50.0))
                is_weekend = float(row.get("Is_Weekend", 0))
                energy_kwh = float(row["Energy_kWh"])

                # Parse date & time
                time_str = row.get("Time", "12:00")
                date_str = row.get("Date", "2025-01-01")

                try:
                    hour = float(time_str.split(":")[0])
                except Exception:
                    hour = 12.0

                try:
                    month = float(datetime.strptime(date_str, "%Y-%m-%d").month)
                except Exception:
                    month = 6.0

                # Engineered features
                cooling_degree = max(0.0, temperature - 24.0) * ac_hours
                total_appliance_hours = ac_hours + comp_hours + appliance_hours

                feat_vector = [
                    occupants,
                    lights,
                    fans,
                    ac_hours,
                    comp_hours,
                    appliance_hours,
                    temperature,
                    humidity,
                    is_weekend,
                    hour,
                    month,
                    cooling_degree,
                    total_appliance_hours
                ]

                features.append(feat_vector)
                targets.append(energy_kwh)
                raw_records.append(row)
            except (ValueError, KeyError) as e:
                continue

    return np.array(features, dtype=float), np.array(targets, dtype=float), raw_records


def train_and_evaluate(dataset_path="dataset/energy_data.csv", models_dir="models"):
    os.makedirs(models_dir, exist_ok=True)
    print("=" * 60)
    print("AI Energy Consumption Prediction - Model Training Pipeline")
    print("=" * 60)

    X, y, raw_records = load_and_preprocess_dataset(dataset_path)
    print(f"Loaded {len(X)} samples with {X.shape[1]} features.")

    # Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Training set: {len(X_train)} | Testing set: {len(X_test)}")

    # Feature Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Instantiate candidate models
    models = {
        "Linear Regression": LinearRegressionModel(),
        "Decision Tree": DecisionTreeRegressorModel(max_depth=6, min_samples_split=5),
        "Random Forest": RandomForestRegressorModel(n_estimators=30, max_depth=8, min_samples_split=4, random_state=42),
        "Gradient Boosting": GradientBoostingRegressorModel(n_estimators=35, learning_rate=0.1, max_depth=4, random_state=42)
    }

    metrics_results = {}
    test_predictions = {}
    best_model_name = None
    best_r2 = -float("inf")

    print("\nEvaluating Machine Learning Algorithms...")
    print("-" * 60)
    print(f"{'Model':<22} | {'MAE':<8} | {'RMSE':<8} | {'R² Score':<10} | {'MAPE (%)':<8}")
    print("-" * 60)

    for name, model in models.items():
        # Train
        model.fit(X_train_scaled, y_train)

        # Predict
        y_pred = model.predict(X_test_scaled)
        test_predictions[name] = y_pred.tolist()

        # Compute metrics
        mae = round(mean_absolute_error(y_test, y_pred), 4)
        rmse = round(root_mean_squared_error(y_test, y_pred), 4)
        r2 = round(r2_score(y_test, y_pred), 4)
        mape = round(mean_absolute_percentage_error(y_test, y_pred), 2)

        metrics_results[name] = {
            "name": name,
            "mae": mae,
            "rmse": rmse,
            "r2_score": r2,
            "mape": mape
        }

        print(f"{name:<22} | {mae:<8.4f} | {rmse:<8.4f} | {r2:<10.4f} | {mape:<8.2f}%")

        if r2 > best_r2:
            best_r2 = r2
            best_model_name = name

    print("-" * 60)
    print(f">> Best Performing Model: {best_model_name} (R^2 = {best_r2:.4f})")

    # Prepare Actual vs Predicted comparison samples (first 30 points for clean visualization)
    comparison_data = []
    for i in range(min(40, len(y_test))):
        comparison_data.append({
            "sample_index": i + 1,
            "actual": round(float(y_test[i]), 3),
            "predicted_best": round(float(test_predictions[best_model_name][i]), 3),
            "predicted_lr": round(float(test_predictions["Linear Regression"][i]), 3),
            "predicted_dt": round(float(test_predictions["Decision Tree"][i]), 3),
            "predicted_rf": round(float(test_predictions["Random Forest"][i]), 3),
            "predicted_gb": round(float(test_predictions["Gradient Boosting"][i]), 3)
        })

    # Save Best Model Package
    best_model_package = {
        "best_model_name": best_model_name,
        "model": models[best_model_name],
        "scaler": scaler,
        "feature_columns": FEATURE_COLUMNS,
        "trained_at": datetime.now().isoformat(),
        "metrics": metrics_results[best_model_name]
    }

    best_model_path = os.path.join(models_dir, "energy_model.pkl")
    with open(best_model_path, "wb") as f:
        pickle.dump(best_model_package, f)

    # Save all models bundle for comparative live predictions
    all_models_package = {
        "models": models,
        "scaler": scaler,
        "feature_columns": FEATURE_COLUMNS,
        "best_model_name": best_model_name
    }
    with open(os.path.join(models_dir, "all_models.pkl"), "wb") as f:
        pickle.dump(all_models_package, f)

    # Save metrics JSON for dashboard and reports
    metrics_summary = {
        "best_model": best_model_name,
        "best_r2_score": best_r2,
        "models": metrics_results,
        "comparison_samples": comparison_data,
        "feature_names": FEATURE_COLUMNS,
        "total_training_samples": len(X_train),
        "total_testing_samples": len(X_test),
        "last_trained": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    metrics_path = os.path.join(models_dir, "model_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=4)

    print(f"\nSaved best model to '{best_model_path}'")
    print(f"Saved evaluation metrics to '{metrics_path}'")
    print("=" * 60)

    return metrics_summary


if __name__ == "__main__":
    train_and_evaluate()
