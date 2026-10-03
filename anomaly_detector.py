"""
Energy-Wasting Appliance & Consumption Anomaly Detector.
Uses statistical z-score thresholds, IQR analysis, and domain heuristics
to detect abnormal power spikes and identify energy-wasting appliances.
"""

import numpy as np

def detect_consumption_anomalies(records, z_threshold=2.2):
    """
    Analyzes a list of energy data records (dictionaries or DB rows).
    Identifies consumption outliers and flags energy-wasting behaviors.
    """
    if not records:
        return []

    energies = [float(r.get("energy_kwh", r.get("Energy_kWh", 0))) for r in records]
    mean_energy = float(np.mean(energies))
    std_energy = float(np.std(energies))
    if std_energy == 0:
        std_energy = 1.0

    q25 = float(np.percentile(energies, 25))
    q75 = float(np.percentile(energies, 75))
    iqr = q75 - q25
    iqr_upper_bound = q75 + 1.5 * iqr

    analyzed_records = []
    for r in records:
        row = dict(r)
        kwh = float(row.get("energy_kwh", row.get("Energy_kWh", 0)))
        temp = float(row.get("temperature", row.get("Temperature", 25)))
        occupants = int(row.get("occupants", row.get("Occupants", 1)))
        lights = int(row.get("lights", row.get("Lights", 0)))
        ac_h = float(row.get("ac_hours", row.get("AC_Usage_Hours", 0)))
        comp_h = float(row.get("computer_hours", row.get("Computer_Usage_Hours", 0)))
        app_h = float(row.get("appliance_hours", row.get("Appliance_Operating_Hours", 0)))
        time_str = str(row.get("record_time", row.get("Time", "12:00")))

        try:
            hour = int(time_str.split(":")[0])
        except Exception:
            hour = 12

        z_score = (kwh - mean_energy) / std_energy
        is_anomaly = False
        reasons = []
        severity = "Normal"
        waste_appliance = "None"

        # Heuristic 1: AC waste during cool temperature
        if ac_h > 0.6 and temp < 24.0:
            is_anomaly = True
            severity = "High"
            waste_appliance = "Air Conditioner"
            reasons.append(f"AC active ({ac_h}h) despite cool outdoor temperature ({temp}°C).")

        # Heuristic 2: Excessive daylight lighting with zero/low occupants
        if 10 <= hour <= 16 and lights > 6 and occupants <= 1:
            is_anomaly = True
            severity = "Medium"
            waste_appliance = "Lighting"
            reasons.append(f"High daytime lighting ({lights} bulbs) with only {occupants} occupant.")

        # Heuristic 3: Late night phantom load / computer left running
        if 1 <= hour <= 5 and comp_h > 0.7:
            is_anomaly = True
            severity = "Medium"
            waste_appliance = "Computer/Workstation"
            reasons.append(f"Workstation active ({comp_h}h) during sleep hours (01:00 - 05:00).")

        # Heuristic 4: Statistical energy spike
        if z_score >= z_threshold or kwh > iqr_upper_bound:
            is_anomaly = True
            if severity != "High":
                severity = "Critical" if z_score > 3.0 else "High"
            reasons.append(f"Unusual energy spike ({kwh:.2f} kWh vs baseline {mean_energy:.2f} kWh, Z-score: {z_score:.2f}).")
            if waste_appliance == "None":
                if ac_h > 0.5:
                    waste_appliance = "Air Conditioner"
                elif app_h > 1.0:
                    waste_appliance = "Heavy Appliance / Heater"
                else:
                    waste_appliance = "General Load Spike"

        row["is_anomaly"] = 1 if is_anomaly else 0
        row["anomaly_reason"] = " | ".join(reasons) if reasons else "Normal consumption within benchmark limits"
        row["severity"] = severity
        row["waste_appliance"] = waste_appliance
        row["z_score"] = round(z_score, 2)
        analyzed_records.append(row)

    return analyzed_records

def analyze_appliance_waste_summary(appliances):
    """
    Evaluates individual appliances for excessive consumption patterns.
    """
    waste_alerts = []
    for app in appliances:
        name = app["appliance_name"]
        power_w = float(app["rated_power_w"])
        daily_hours = float(app["avg_daily_hours"])
        daily_kwh = float(app["daily_kwh"])
        category = app.get("category", "General")

        if category == "Cooling" and daily_hours > 8.0:
            waste_alerts.append({
                "appliance": name,
                "category": category,
                "issue": f"Excessive operation ({daily_hours} hrs/day)",
                "impact": f"Consuming {daily_kwh:.2f} kWh/day (~₹{daily_kwh * 30 * 7.5:.0f}/month)",
                "suggestion": "Set thermostat to 24°C and program auto-off timer after 4 hours.",
                "severity": "High"
            })
        elif category == "Heating" and daily_hours > 2.5:
            waste_alerts.append({
                "appliance": name,
                "category": category,
                "issue": f"Geyser/Heater left on ({daily_hours} hrs/day)",
                "impact": f"High continuous resistive load ({daily_kwh:.2f} kWh/day)",
                "suggestion": "Install a 30-minute mechanical timer plug or turn off after heating.",
                "severity": "High"
            })
        elif category == "Computing" and daily_hours > 10.0:
            waste_alerts.append({
                "appliance": name,
                "category": category,
                "issue": f"Workstation continuous run ({daily_hours} hrs/day)",
                "impact": f"Standby energy leakage (~{daily_kwh:.2f} kWh/day)",
                "suggestion": "Enable OS sleep mode after 15 mins of inactivity and power off monitors.",
                "severity": "Medium"
            })
        elif category == "Lighting" and daily_hours > 9.0:
            waste_alerts.append({
                "appliance": name,
                "category": category,
                "issue": f"Long lighting runtime ({daily_hours} hrs/day)",
                "impact": f"Daylight wastage",
                "suggestion": "Maximize daylight harvesting and replace legacy bulbs with 9W LEDs.",
                "severity": "Low"
            })

    return waste_alerts
