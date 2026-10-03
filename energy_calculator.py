"""
Energy Calculator Module.
Provides functions for:
1. Electricity bill and tariff calculation (Daily, Monthly, Yearly, Tiered Slabs)
2. Carbon Footprint (CO2 emissions in kg) & Environmental Equivalents (Trees, Car km)
3. Energy savings and efficiency metrics.
"""

# Standard Grid Carbon Emission Factor: ~0.82 kg CO2 / kWh
CO2_FACTOR_KG_PER_KWH = 0.82
TREE_ABSORPTION_KG_PER_YEAR = 21.77 # 1 mature tree absorbs ~21.77 kg CO2 / year
CAR_EMISSION_KG_PER_KM = 0.12 # Average passenger car emits ~0.12 kg CO2 / km

def calculate_costs(kwh, tariff_rate=7.50, is_monthly_total=False):
    """
    Calculates Daily, Monthly, and Yearly costs.
    If is_monthly_total is True, kwh is treated as a 30-day sum.
    Otherwise, kwh is treated as a daily average / single day reading.
    """
    if is_monthly_total:
        monthly_kwh = float(kwh)
        daily_kwh = monthly_kwh / 30.0
        yearly_kwh = monthly_kwh * 12.0
    else:
        daily_kwh = float(kwh)
        monthly_kwh = daily_kwh * 30.0
        yearly_kwh = daily_kwh * 365.0

    daily_cost = round(daily_kwh * tariff_rate, 2)
    monthly_cost = round(monthly_kwh * tariff_rate, 2)
    yearly_cost = round(yearly_kwh * tariff_rate, 2)

    return {
        "daily_kwh": round(daily_kwh, 3),
        "monthly_kwh": round(monthly_kwh, 2),
        "yearly_kwh": round(yearly_kwh, 2),
        "tariff_rate": round(tariff_rate, 2),
        "daily_cost": daily_cost,
        "monthly_cost": monthly_cost,
        "yearly_cost": yearly_cost,
        "currency_symbol": "₹"
    }

def calculate_tiered_bill(monthly_kwh, slabs=None):
    """
    Calculates electricity bill based on progressive slab/tiered pricing.
    Default slab:
    0 - 100 kWh: 4.50 / kWh
    101 - 300 kWh: 6.50 / kWh
    301 - 500 kWh: 8.50 / kWh
    > 500 kWh: 10.00 / kWh
    """
    if slabs is None:
        slabs = [
            (100, 4.50),
            (200, 6.50),
            (200, 8.50),
            (float('inf'), 10.00)
        ]

    remaining = float(monthly_kwh)
    total_bill = 0.0
    breakdown = []

    for limit, rate in slabs:
        if remaining <= 0:
            break
        units_in_slab = min(remaining, limit)
        slab_cost = units_in_slab * rate
        total_bill += slab_cost
        breakdown.append({
            "units": round(units_in_slab, 2),
            "rate": rate,
            "cost": round(slab_cost, 2)
        })
        remaining -= units_in_slab

    fixed_charges = 60.0 # Standard meter fixed charges
    gst_tax = total_bill * 0.05 # 5% tax
    grand_total = round(total_bill + fixed_charges + gst_tax, 2)

    return {
        "monthly_kwh": round(monthly_kwh, 2),
        "energy_charges": round(total_bill, 2),
        "fixed_charges": fixed_charges,
        "tax": round(gst_tax, 2),
        "grand_total": grand_total,
        "breakdown": breakdown
    }

def calculate_co2_emissions(kwh, is_monthly_total=False):
    """
    Calculates carbon footprint and ecological impact equivalents.
    """
    if is_monthly_total:
        monthly_kwh = float(kwh)
        daily_kwh = monthly_kwh / 30.0
        yearly_kwh = monthly_kwh * 12.0
    else:
        daily_kwh = float(kwh)
        monthly_kwh = daily_kwh * 30.0
        yearly_kwh = daily_kwh * 365.0

    daily_co2 = round(daily_kwh * CO2_FACTOR_KG_PER_KWH, 3)
    monthly_co2 = round(monthly_kwh * CO2_FACTOR_KG_PER_KWH, 2)
    yearly_co2 = round(yearly_kwh * CO2_FACTOR_KG_PER_KWH, 2)

    trees_needed = max(1, round(yearly_co2 / TREE_ABSORPTION_KG_PER_YEAR, 1))
    car_km_equivalent = round(monthly_co2 / CAR_EMISSION_KG_PER_KM, 1)

    return {
        "daily_co2_kg": daily_co2,
        "monthly_co2_kg": monthly_co2,
        "yearly_co2_kg": yearly_co2,
        "trees_needed_to_offset": trees_needed,
        "car_km_equivalent": car_km_equivalent,
        "co2_factor": CO2_FACTOR_KG_PER_KWH
    }

def calculate_potential_savings(current_kwh, target_reduction_pct=15.0, tariff_rate=7.50):
    """
    Calculates estimated money and carbon savings if usage is reduced by X%.
    """
    reduced_kwh_monthly = (current_kwh * 30.0) * (target_reduction_pct / 100.0)
    monthly_money_saved = round(reduced_kwh_monthly * tariff_rate, 2)
    yearly_money_saved = round(monthly_money_saved * 12.0, 2)
    monthly_co2_saved = round(reduced_kwh_monthly * CO2_FACTOR_KG_PER_KWH, 2)
    yearly_co2_saved = round(monthly_co2_saved * 12.0, 2)

    return {
        "reduction_pct": target_reduction_pct,
        "kwh_saved_monthly": round(reduced_kwh_monthly, 2),
        "monthly_savings": monthly_money_saved,
        "yearly_savings": yearly_money_saved,
        "monthly_co2_saved_kg": monthly_co2_saved,
        "yearly_co2_saved_kg": yearly_co2_saved
    }
