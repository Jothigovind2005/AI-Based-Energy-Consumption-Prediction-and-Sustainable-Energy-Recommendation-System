"""
Sustainable Energy Recommendation Engine.
Generates personalized, actionable energy-conservation recommendations
based on user consumption patterns, appliance inventory, and ML prediction trends.
"""

def generate_dynamic_recommendations(user_data, appliances=None, tariff_rate=7.50):
    """
    Analyzes user profile, usage records, and appliances to generate tailored recommendations.
    """
    recommendations = []
    
    # Analyze recent consumption statistics
    total_records = len(user_data)
    if total_records == 0:
        return _get_default_recommendations(tariff_rate)

    avg_ac_hours = sum(float(r.get("ac_hours", r.get("AC_Usage_Hours", 0))) for r in user_data) / total_records
    avg_comp_hours = sum(float(r.get("computer_hours", r.get("Computer_Usage_Hours", 0))) for r in user_data) / total_records
    avg_temp = sum(float(r.get("temperature", r.get("Temperature", 25))) for r in user_data) / total_records
    avg_lights = sum(int(r.get("lights", r.get("Lights", 2))) for r in user_data) / total_records
    avg_energy = sum(float(r.get("energy_kwh", r.get("Energy_kWh", 1.0))) for r in user_data) / total_records

    # 1. AC & Thermal Optimization Rule
    if avg_ac_hours > 0.4:
        daily_saving_kwh = round(avg_ac_hours * 0.45 * 1.5, 2)
        monthly_saving_kwh = round(daily_saving_kwh * 30, 1)
        cost_saving = round(monthly_saving_kwh * tariff_rate, 2)
        co2_saving = round(monthly_saving_kwh * 0.82, 1)

        recommendations.append({
            "category": "Cooling Optimization",
            "title": "Set AC Thermostat to Eco-Friendly 24°C - 26°C",
            "description": f"Your current AC runtime averages {avg_ac_hours*24:.1f} hours/day. Increasing thermostat temperature from 18°C/20°C to 24°C saves up to 6% electricity per degree, reducing cooling power by ~24%.",
            "estimated_saving_kwh": monthly_saving_kwh,
            "estimated_cost_saving": cost_saving,
            "estimated_co2_saving": co2_saving,
            "priority": "High",
            "impact_badge": "Save ~24% Cooling Cost",
            "icon": "bi-snow"
        })

    # 2. Standby / Phantom Power Elimination Rule
    if avg_comp_hours > 0.3 or avg_energy > 1.2:
        monthly_kwh_save = 25.0
        cost_saving = round(monthly_kwh_save * tariff_rate, 2)
        co2_saving = round(monthly_kwh_save * 0.82, 1)

        recommendations.append({
            "category": "Vampire Power",
            "title": "Eliminate Standby & Idle Workstation Consumption",
            "description": "Computers, displays, and chargers in idle standby consume 8-15% of total household power. Connect your workspace to a master smart switch to eliminate ghost drain when not in use.",
            "estimated_saving_kwh": monthly_kwh_save,
            "estimated_cost_saving": cost_saving,
            "estimated_co2_saving": co2_saving,
            "priority": "Medium",
            "impact_badge": "Cut 10% Idle Drain",
            "icon": "bi-plug-fill"
        })

    # 3. Smart Lighting & Daylight Harvesting Rule
    if avg_lights > 4:
        monthly_kwh_save = round(avg_lights * 0.015 * 5 * 30, 1)
        cost_saving = round(monthly_kwh_save * tariff_rate, 2)
        co2_saving = round(monthly_kwh_save * 0.82, 1)

        recommendations.append({
            "category": "Lighting Efficiency",
            "title": "Implement Daylight Harvesting & 9W LED Retrofits",
            "description": f"You have an average of {avg_lights:.0f} concurrent active lights. Replacing older fluorescent/incandescent fixtures with 9W 5-star LEDs and opening curtains during daytime slashes lighting wattage by 80%.",
            "estimated_saving_kwh": monthly_kwh_save,
            "estimated_cost_saving": cost_saving,
            "estimated_co2_saving": co2_saving,
            "priority": "Low",
            "impact_badge": "80% Lighting Savings",
            "icon": "bi-lightbulb-fill"
        })

    # 4. Load Shifting to Off-Peak / Solar Windows Rule
    monthly_kwh_shift = 45.0
    cost_saving = round(monthly_kwh_shift * (tariff_rate * 0.25), 2)
    co2_saving = round(monthly_kwh_shift * 0.40, 1)
    recommendations.append({
        "category": "Peak Load Shifting",
        "title": "Shift Heavy Appliances (Washing Machine / Geyser) to Off-Peak Hours",
        "description": "Run high-wattage resistive heating cycles (geysers, dishwashers, washing machines) during off-peak morning periods (06:00 - 10:00) to prevent peak tariff penalties and grid stress.",
        "estimated_saving_kwh": monthly_kwh_shift,
        "estimated_cost_saving": cost_saving,
        "estimated_co2_saving": co2_saving,
        "priority": "Medium",
        "impact_badge": "Peak Shifting",
        "icon": "bi-clock-history"
    })

    # 5. Natural Ventilation Rule
    if avg_temp < 28.0:
        monthly_kwh_save = 60.0
        cost_saving = round(monthly_kwh_save * tariff_rate, 2)
        co2_saving = round(monthly_kwh_save * 0.82, 1)
        recommendations.append({
            "category": "Natural Cooling",
            "title": "Leverage Cross-Ventilation & BLDC Fans During Mild Weather",
            "description": f"The ambient temperature is moderate (~{avg_temp:.1f}°C). Using energy-efficient BLDC ceiling fans (28W vs 75W regular) alongside open windows completely replaces compressor AC usage.",
            "estimated_saving_kwh": monthly_kwh_save,
            "estimated_cost_saving": cost_saving,
            "estimated_co2_saving": co2_saving,
            "priority": "High",
            "impact_badge": "60% Fan Efficiency",
            "icon": "bi-wind"
        })

    return recommendations

def _get_default_recommendations(tariff_rate=7.50):
    return [
        {
            "category": "Cooling Optimization",
            "title": "Set AC Thermostat to 24°C",
            "description": "Increasing AC setpoint to 24°C saves ~24% electricity compared to 18°C.",
            "estimated_saving_kwh": 96.0,
            "estimated_cost_saving": round(96.0 * tariff_rate, 2),
            "estimated_co2_saving": 78.7,
            "priority": "High",
            "impact_badge": "Save ~24% Cooling",
            "icon": "bi-snow"
        },
        {
            "category": "Vampire Power",
            "title": "Turn Off Idle Standby Power",
            "description": "Unplug or switch off standby equipment to eliminate phantom energy drain.",
            "estimated_saving_kwh": 24.0,
            "estimated_cost_saving": round(24.0 * tariff_rate, 2),
            "estimated_co2_saving": 19.6,
            "priority": "Medium",
            "impact_badge": "Cut 10% Standby",
            "icon": "bi-plug-fill"
        }
    ]
