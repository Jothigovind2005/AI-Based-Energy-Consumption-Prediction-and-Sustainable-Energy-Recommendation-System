"""
Dataset Generator for Energy Consumption Prediction & Anomaly Detection System.
Generates realistic simulated energy usage records with seasonal, diurnal,
and occupancy-dependent patterns, clearly labeled as academic simulated data.
Uses Python standard libraries (csv, math, random, datetime) for maximum compatibility.
"""

import os
import csv
import math
import random
from datetime import datetime, timedelta

def generate_energy_dataset(num_records=1200, output_path="dataset/energy_data.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    random.seed(42)

    start_date = datetime(2025, 1, 1, 0, 0)
    records = []

    # Realistic base power ratings (kW approximate contribution)
    # AC: ~1.5 kW per hour of operation
    # Computer: ~0.15 - 0.3 kW per hour of operation
    # Light: ~0.025 kW per bulb per active hour
    # Fan: ~0.065 kW per fan per active hour
    # Base appliance (fridge, router, etc.): ~0.25 kW continuous baseline

    for i in range(num_records):
        current_time = start_date + timedelta(hours=i)
        date_str = current_time.strftime("%Y-%m-%d")
        time_str = current_time.strftime("%H:%M")
        hour = current_time.hour
        month = current_time.month
        day_of_week = current_time.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0

        # Seasonal temperature variations
        if month in [4, 5, 6, 7, 8]: # Summer
            base_temp = 32.0 + math.sin((hour - 6) / 24 * math.pi) * 7.5
        elif month in [12, 1, 2]: # Winter
            base_temp = 18.0 + math.sin((hour - 6) / 24 * math.pi) * 4.5
        else: # Spring / Autumn
            base_temp = 25.5 + math.sin((hour - 6) / 24 * math.pi) * 5.5

        temperature = round(max(15.0, min(44.0, base_temp + random.gauss(0, 1.2))), 1)
        humidity = round(max(25.0, min(92.0, 60.0 + random.gauss(0, 10.0) - (temperature - 25) * 0.7)), 1)

        # Occupancy pattern
        if is_weekend:
            occupants = random.choices([2, 3, 4, 5], weights=[0.2, 0.4, 0.3, 0.1])[0]
        else:
            if 9 <= hour <= 17:
                occupants = random.choices([0, 1, 2], weights=[0.55, 0.30, 0.15])[0]
            else:
                occupants = random.choices([1, 2, 3, 4], weights=[0.2, 0.45, 0.25, 0.1])[0]

        # Lights and Fans depending on occupancy and time
        if occupants == 0:
            lights = random.choices([0, 1], weights=[0.9, 0.1])[0]
            fans = random.choices([0, 1], weights=[0.95, 0.05])[0]
        else:
            if 18 <= hour or hour <= 6:
                lights = max(1, min(14, int(occupants * random.uniform(1.2, 3.5))))
            else:
                lights = max(0, min(8, int(occupants * random.uniform(0.0, 1.8))))

            if temperature > 26.0:
                fans = max(1, min(6, int(occupants * random.uniform(0.8, 1.5))))
            else:
                fans = max(0, min(4, int(occupants * random.uniform(0.0, 1.0))))

        # AC Usage (Hours per hourly slot)
        if temperature > 28.0 and occupants > 0:
            if (13 <= hour <= 16) or (21 <= hour <= 23) or (0 <= hour <= 5):
                ac_hours = round(max(0.0, min(1.0, random.uniform(0.6, 1.0))), 2)
            else:
                ac_hours = round(max(0.0, min(1.0, random.uniform(0.2, 0.7))), 2)
        elif temperature > 34.0:
            ac_hours = round(max(0.0, min(1.0, random.uniform(0.5, 1.0))), 2)
        else:
            ac_hours = 0.0

        # Computer usage
        if occupants > 0:
            if 9 <= hour <= 22:
                computer_hours = round(max(0.0, min(1.0, random.uniform(0.3, 1.0))), 2)
            else:
                computer_hours = round(max(0.0, min(1.0, random.uniform(0.0, 0.35))), 2)
        else:
            computer_hours = 0.0

        # Other appliance hours
        appliance_hours = round(max(0.1, min(1.5, random.uniform(0.2, 0.9) * (1.0 if occupants > 0 else 0.3))), 2)

        # Baseline calculation for Energy (kWh)
        baseline_load = 0.25 # Continuous standby/refrigeration
        lighting_load = lights * 0.025
        fan_load = fans * 0.065
        ac_factor = 1.0 + ((temperature - 28.0) * 0.035 if temperature > 28.0 else 0.0)
        ac_load = ac_hours * 1.55 * ac_factor
        computer_load = computer_hours * 0.22
        other_load = appliance_hours * 0.45

        noise = random.gauss(0, 0.06)
        energy_kwh = round(max(0.18, baseline_load + lighting_load + fan_load + ac_load + computer_load + other_load + noise), 3)

        # Inject realistic anomalies (4% of records)
        if random.random() < 0.04:
            anomaly_type = random.choice(["ac_waste", "high_light_waste", "comp_waste", "appliance_spike"])
            if anomaly_type == "ac_waste":
                ac_hours = 1.0
                energy_kwh = round(energy_kwh + random.uniform(1.8, 3.2), 3)
            elif anomaly_type == "high_light_waste":
                lights = 16
                energy_kwh = round(energy_kwh + random.uniform(0.6, 1.2), 3)
            elif anomaly_type == "comp_waste":
                computer_hours = 1.0
                energy_kwh = round(energy_kwh + random.uniform(0.7, 1.5), 3)
            elif anomaly_type == "appliance_spike":
                appliance_hours = 2.0
                energy_kwh = round(energy_kwh + random.uniform(1.2, 2.5), 3)

        records.append({
            "Date": date_str,
            "Time": time_str,
            "Energy_kWh": energy_kwh,
            "Occupants": occupants,
            "Lights": lights,
            "Fans": fans,
            "AC_Usage_Hours": ac_hours,
            "Computer_Usage_Hours": computer_hours,
            "Appliance_Operating_Hours": appliance_hours,
            "Temperature": temperature,
            "Humidity": humidity,
            "Is_Weekend": is_weekend
        })

    fieldnames = [
        "Date", "Time", "Energy_kWh", "Occupants", "Lights", "Fans",
        "AC_Usage_Hours", "Computer_Usage_Hours", "Appliance_Operating_Hours",
        "Temperature", "Humidity", "Is_Weekend"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Successfully generated {len(records)} records at '{output_path}'.")
    return records

if __name__ == "__main__":
    generate_energy_dataset()
