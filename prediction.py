"""
Prediction Module.
Provides inference capabilities for single-instance inputs and comparative
predictions across Linear Regression, Decision Tree, Random Forest, and Gradient Boosting.
"""

import os
import json
import pickle
import numpy as np
from datetime import datetime

from ml_engine import StandardScaler
from energy_calculator import calculate_costs, calculate_co2_emissions

MODEL_PATH = "models/energy_model.pkl"
ALL_MODELS_PATH = "models/all_models.pkl"
METRICS_PATH = "models/model_metrics.json"

_cached_best_model = None
_cached_all_models = None
_cached_metrics = None

def load_best_model():
    global _cached_best_model
    if _cached_best_model is None:
        if not os.path.exists(MODEL_PATH):
            from train_model import train_and_evaluate
            train_and_evaluate()
        with open(MODEL_PATH, "rb") as f:
            _cached_best_model = pickle.load(f)
    return _cached_best_model

def load_all_models():
    global _cached_all_models
    if _cached_all_models is None:
        if not os.path.exists(ALL_MODELS_PATH):
            from train_model import train_and_evaluate
            train_and_evaluate()
        with open(ALL_MODELS_PATH, "rb") as f:
            _cached_all_models = pickle.load(f)
    return _cached_all_models

def get_model_metrics():
    global _cached_metrics
    if _cached_metrics is None:
        if not os.path.exists(METRICS_PATH):
            from train_model import train_and_evaluate
            train_and_evaluate()
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            _cached_metrics = json.load(f)
    return _cached_metrics

def prepare_feature_vector(inputs):
    """
    Constructs normalized 13-feature array matching the trained pipeline:
    [Occupants, Lights, Fans, AC_Hours, Comp_Hours, Appliance_Hours, Temp, Humidity, Is_Weekend, Hour, Month, Cooling_Degree, Total_Appliance_Hours]
    """
    occupants = float(inputs.get("occupants", 2))
    lights = float(inputs.get("lights", 4))
    fans = float(inputs.get("fans", 2))
    ac_hours = float(inputs.get("ac_hours", 0.5))
    comp_hours = float(inputs.get("computer_hours", 0.5))
    app_hours = float(inputs.get("appliance_hours", 0.5))
    temp = float(inputs.get("temperature", 28.0))
    humidity = float(inputs.get("humidity", 55.0))
    is_weekend = float(inputs.get("is_weekend", 0))

    now = datetime.now()
    hour = float(inputs.get("hour", now.hour))
    month = float(inputs.get("month", now.month))

    cooling_degree = max(0.0, temp - 24.0) * ac_hours
    total_appliance_hours = ac_hours + comp_hours + app_hours

    feature_row = [
        occupants,
        lights,
        fans,
        ac_hours,
        comp_hours,
        app_hours,
        temp,
        humidity,
        is_weekend,
        hour,
        month,
        cooling_degree,
        total_appliance_hours
    ]
    return np.array([feature_row], dtype=float)

def predict_energy_consumption(inputs, model_name=None, tariff_rate=7.50):
    """
    Predicts energy consumption (kWh) and returns multi-model comparisons,
    cost estimates, and CO2 emissions.
    """
    all_bundle = load_all_models()
    scaler = all_bundle["scaler"]
    models = all_bundle["models"]
    best_name = all_bundle.get("best_model_name", "Gradient Boosting")

    X_raw = prepare_feature_vector(inputs)
    X_scaled = scaler.transform(X_raw)

    comparisons = {}
    for name, model in models.items():
        pred_val = max(0.05, float(model.predict(X_scaled)[0]))
        comparisons[name] = round(pred_val, 3)

    chosen_model = model_name if model_name in models else best_name
    primary_pred_kwh = comparisons[chosen_model]

    # Calculate full daily cycle projection
    # If the user enters hourly scenario, we scale to daily estimation
    daily_estimated_kwh = round(primary_pred_kwh * 24.0 * 0.45, 2) # Typical daily load factor

    cost_info = calculate_costs(primary_pred_kwh, tariff_rate=tariff_rate)
    co2_info = calculate_co2_emissions(primary_pred_kwh)

    # Monthly and Annual Projections
    monthly_costs = calculate_costs(daily_estimated_kwh, tariff_rate=tariff_rate)
    monthly_co2 = calculate_co2_emissions(daily_estimated_kwh)

    metrics_meta = get_model_metrics()

    return {
        "inputs": inputs,
        "chosen_model": chosen_model,
        "best_model_name": best_name,
        "predicted_hourly_kwh": primary_pred_kwh,
        "predicted_daily_kwh": daily_estimated_kwh,
        "monthly_projected_kwh": round(daily_estimated_kwh * 30, 1),
        "yearly_projected_kwh": round(daily_estimated_kwh * 365, 1),
        "model_comparisons": comparisons,
        "hourly_cost": cost_info["daily_cost"], # cost per hour
        "monthly_cost": monthly_costs["monthly_cost"],
        "yearly_cost": monthly_costs["yearly_cost"],
        "hourly_co2_kg": co2_info["daily_co2_kg"],
        "monthly_co2_kg": monthly_co2["monthly_co2_kg"],
        "yearly_co2_kg": monthly_co2["yearly_co2_kg"],
        "trees_needed": monthly_co2["trees_needed_to_offset"],
        "metrics": metrics_meta.get("models", {}).get(chosen_model, {})
    }
