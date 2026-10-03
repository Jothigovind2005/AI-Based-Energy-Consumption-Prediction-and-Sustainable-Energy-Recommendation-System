"""
Flask Web Application for AI-Based Energy Consumption Prediction
and Sustainable Energy Recommendation System.
"""

import os
import io
import csv
import json
import sqlite3
from functools import wraps
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_file, Response
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from init_db import init_db, get_db_connection, DB_PATH
from prediction import predict_energy_consumption, get_model_metrics
from energy_calculator import (
    calculate_costs, calculate_co2_emissions,
    calculate_tiered_bill, calculate_potential_savings
)
from anomaly_detector import detect_consumption_anomalies, analyze_appliance_waste_summary
from recommendation import generate_dynamic_recommendations

app = Flask(__name__)
app.secret_key = "energy_ai_secret_key_academic_cse_project_2025"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB upload limit

# Ensure DB is created on startup
if not os.path.exists(DB_PATH):
    init_db()

# ==========================================
# AUTHENTICATION HELPERS & DECORATORS
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' not in session:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    return user

@app.context_processor
def inject_user():
    return {'current_user': get_current_user()}

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Please provide both username and password.", "danger")
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f"Welcome back, {user['full_name']}!", "success")
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard'))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        tariff_rate = float(request.form.get('tariff_rate', 7.50))

        if not username or not email or not full_name or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html')

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
        if existing:
            conn.close()
            flash("Username or Email already registered. Please login.", "warning")
            return render_template('register.html')

        pwd_hash = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, tariff_rate, role)
        VALUES (?, ?, ?, ?, ?, 'user')
        """, (username, email, pwd_hash, full_name, tariff_rate))
        new_user_id = cursor.lastrowid
        conn.commit()

        # Seed initial sample appliances for new user
        default_appliances = [
            (new_user_id, "Inverter AC (1.5 Ton)", "Cooling", 1500, 6.0, 9.0, 2025.0, 221.4, "High Usage"),
            (new_user_id, "Refrigerator (260L)", "Refrigeration", 170, 24.0, 2.04, 459.0, 50.18, "Normal"),
            (new_user_id, "Workstation PC", "Computing", 250, 7.0, 1.75, 393.75, 43.05, "Normal"),
            (new_user_id, "Ceiling Fans (3 Units)", "Circulation", 210, 10.0, 2.10, 472.5, 51.66, "Normal"),
            (new_user_id, "LED Lighting (8 Units)", "Lighting", 80, 5.0, 0.40, 90.0, 9.84, "Efficient")
        ]
        cursor.executemany("""
        INSERT INTO appliances (user_id, appliance_name, category, rated_power_w, avg_daily_hours, daily_kwh, monthly_cost, co2_kg_monthly, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, default_appliances)
        conn.commit()
        conn.close()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out safely.", "info")
    return redirect(url_for('login'))


# ==========================================
# DASHBOARD ROUTE
# ==========================================

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    user_id = user['id']
    tariff_rate = user['tariff_rate']

    conn = get_db_connection()
    # Fetch recent energy logs
    records = conn.execute("""
    SELECT * FROM energy_data 
    WHERE user_id = ? 
    ORDER BY record_date DESC, record_time DESC 
    LIMIT 200
    """, (user_id,)).fetchall()

    # If no data for this user, fallback to all data for preview
    if not records:
        records = conn.execute("""
        SELECT * FROM energy_data 
        ORDER BY record_date DESC, record_time DESC 
        LIMIT 200
        """).fetchall()

    # Appliances
    appliances = conn.execute("SELECT * FROM appliances WHERE user_id = ?", (user_id,)).fetchall()
    if not appliances:
        appliances = conn.execute("SELECT * FROM appliances LIMIT 10").fetchall()

    # Recommendations
    recommendations = conn.execute("""
    SELECT * FROM recommendations 
    WHERE user_id = ? 
    ORDER BY priority DESC, id ASC 
    LIMIT 4
    """, (user_id,)).fetchall()

    conn.close()

    # Analytics calculation
    total_records = len(records)
    if total_records > 0:
        energies = [r['energy_kwh'] for r in records]
        total_kwh = sum(energies)
        avg_hourly_kwh = total_kwh / total_records
        daily_kwh_est = round(avg_hourly_kwh * 24 * 0.45, 2)
        peak_kwh = max(energies)
    else:
        total_kwh = 0.0
        avg_hourly_kwh = 0.0
        daily_kwh_est = 0.0
        peak_kwh = 0.0

    cost_info = calculate_costs(daily_kwh_est, tariff_rate=tariff_rate)
    co2_info = calculate_co2_emissions(daily_kwh_est)
    savings_info = calculate_potential_savings(daily_kwh_est, target_reduction_pct=18.0, tariff_rate=tariff_rate)

    # Highest consuming appliance
    highest_appliance = "Air Conditioner"
    if appliances:
        sorted_apps = sorted(appliances, key=lambda a: a['daily_kwh'], reverse=True)
        if sorted_apps:
            highest_appliance = sorted_apps[0]['appliance_name']

    # Anomaly records count
    anomalies_count = sum(1 for r in records if r['is_anomaly'] == 1)

    # Model metrics
    metrics_data = get_model_metrics()

    return render_template(
        'dashboard.html',
        user=user,
        total_kwh=round(total_kwh, 2),
        avg_hourly_kwh=round(avg_hourly_kwh, 2),
        daily_kwh_est=daily_kwh_est,
        peak_kwh=round(peak_kwh, 2),
        cost_info=cost_info,
        co2_info=co2_info,
        savings_info=savings_info,
        highest_appliance=highest_appliance,
        anomalies_count=anomalies_count,
        appliances=appliances,
        recommendations=recommendations,
        recent_records=records[:10],
        metrics_data=metrics_data
    )


# ==========================================
# ENERGY DATA MANAGEMENT & CSV UPLOAD
# ==========================================

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    user = get_current_user()
    user_id = user['id']

    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash("No file part in the form.", "danger")
            return redirect(request.url)

        file = request.files['csv_file']
        if file.filename == '':
            flash("No file selected.", "danger")
            return redirect(request.url)

        if not file.filename.endswith('.csv'):
            flash("Please upload a valid CSV file.", "danger")
            return redirect(request.url)

        try:
            stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
            reader = csv.DictReader(stream)

            required_cols = {"Energy_kWh"}
            if not reader.fieldnames or not required_cols.issubset(set(reader.fieldnames)):
                flash("CSV file must contain at least 'Energy_kWh' column.", "danger")
                return redirect(request.url)

            rows_to_insert = []
            parsed_records_for_anomaly = []
            now = datetime.now()

            for row in reader:
                try:
                    energy_kwh = float(row.get("Energy_kWh", 0.0))
                    occupants = int(float(row.get("Occupants", 1)))
                    lights = int(float(row.get("Lights", 2)))
                    fans = int(float(row.get("Fans", 1)))
                    ac_h = float(row.get("AC_Usage_Hours", 0.0))
                    comp_h = float(row.get("Computer_Usage_Hours", 0.0))
                    app_h = float(row.get("Appliance_Operating_Hours", 0.5))
                    temp = float(row.get("Temperature", 25.0))
                    humidity = float(row.get("Humidity", 50.0))
                    is_weekend = int(float(row.get("Is_Weekend", 0)))
                    rec_date = row.get("Date", now.strftime("%Y-%m-%d")).strip()
                    rec_time = row.get("Time", now.strftime("%H:%M")).strip()

                    row_dict = {
                        "user_id": user_id,
                        "record_date": rec_date,
                        "record_time": rec_time,
                        "energy_kwh": energy_kwh,
                        "occupants": occupants,
                        "lights": lights,
                        "fans": fans,
                        "ac_hours": ac_h,
                        "computer_hours": comp_h,
                        "appliance_hours": app_h,
                        "temperature": temp,
                        "humidity": humidity,
                        "is_weekend": is_weekend
                    }
                    parsed_records_for_anomaly.append(row_dict)
                except (ValueError, TypeError):
                    continue

            if not parsed_records_for_anomaly:
                flash("No valid rows found in the CSV file.", "warning")
                return redirect(request.url)

            # Detect anomalies
            analyzed = detect_consumption_anomalies(parsed_records_for_anomaly)

            conn = get_db_connection()
            cursor = conn.cursor()
            for r in analyzed:
                cursor.execute("""
                INSERT INTO energy_data (
                    user_id, record_date, record_time, energy_kwh, occupants, lights,
                    fans, ac_hours, computer_hours, appliance_hours, temperature,
                    humidity, is_weekend, is_anomaly, anomaly_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, r["record_date"], r["record_time"], r["energy_kwh"],
                    r["occupants"], r["lights"], r["fans"], r["ac_hours"],
                    r["computer_hours"], r["appliance_hours"], r["temperature"],
                    r["humidity"], r["is_weekend"], r["is_anomaly"], r["anomaly_reason"]
                ))
            conn.commit()
            conn.close()

            flash(f"Successfully uploaded and analyzed {len(analyzed)} energy records!", "success")
            return redirect(url_for('analysis'))

        except Exception as e:
            flash(f"Error parsing CSV file: {str(e)}", "danger")
            return redirect(request.url)

    # Fetch recent uploads summary
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM energy_data WHERE user_id = ?", (user_id,)).fetchone()[0]
    conn.close()

    return render_template('upload.html', total_records_count=count)


@app.route('/entry/manual', methods=['POST'])
@login_required
def manual_entry():
    user = get_current_user()
    user_id = user['id']

    try:
        rec_date = request.form.get('record_date', datetime.now().strftime("%Y-%m-%d"))
        rec_time = request.form.get('record_time', datetime.now().strftime("%H:%M"))
        energy_kwh = float(request.form.get('energy_kwh', 1.0))
        occupants = int(request.form.get('occupants', 1))
        lights = int(request.form.get('lights', 2))
        fans = int(request.form.get('fans', 1))
        ac_hours = float(request.form.get('ac_hours', 0.0))
        comp_hours = float(request.form.get('computer_hours', 0.0))
        app_hours = float(request.form.get('appliance_hours', 0.5))
        temp = float(request.form.get('temperature', 25.0))
        humidity = float(request.form.get('humidity', 50.0))
        is_weekend = 1 if request.form.get('is_weekend') == '1' else 0

        # Run anomaly detection on single entry
        sample_row = [{
            "energy_kwh": energy_kwh, "temperature": temp, "occupants": occupants,
            "lights": lights, "ac_hours": ac_hours, "computer_hours": comp_hours,
            "appliance_hours": app_hours, "record_time": rec_time
        }]
        analyzed = detect_consumption_anomalies(sample_row)[0]

        conn = get_db_connection()
        conn.execute("""
        INSERT INTO energy_data (
            user_id, record_date, record_time, energy_kwh, occupants, lights,
            fans, ac_hours, computer_hours, appliance_hours, temperature,
            humidity, is_weekend, is_anomaly, anomaly_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, rec_date, rec_time, energy_kwh, occupants, lights,
            fans, ac_hours, comp_hours, app_hours, temp, humidity,
            is_weekend, analyzed["is_anomaly"], analyzed["anomaly_reason"]
        ))
        conn.commit()
        conn.close()

        flash("Manual energy reading recorded successfully!", "success")
    except Exception as e:
        flash(f"Error saving energy record: {str(e)}", "danger")

    return redirect(url_for('analysis'))


@app.route('/download/sample-csv')
def download_sample_csv():
    csv_file = "dataset/energy_data.csv"
    if os.path.exists(csv_file):
        return send_file(csv_file, as_attachment=True, download_name="sample_energy_data.csv")
    else:
        # Generate inline sample CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Date", "Time", "Energy_kWh", "Occupants", "Lights", "Fans",
            "AC_Usage_Hours", "Computer_Usage_Hours", "Appliance_Operating_Hours",
            "Temperature", "Humidity", "Is_Weekend"
        ])
        writer.writerow(["2025-06-15", "14:00", "2.85", "3", "4", "2", "1.0", "0.8", "0.6", "34.5", "48.0", "0"])
        writer.writerow(["2025-06-15", "15:00", "2.92", "3", "5", "3", "1.0", "0.7", "0.5", "35.2", "45.0", "0"])
        output.seek(0)
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=sample_energy_data.csv"})


@app.route('/dataset/reload-sample', methods=['POST'])
@login_required
def reload_sample_data():
    user = get_current_user()
    user_id = user['id']
    csv_file = "dataset/energy_data.csv"

    if not os.path.exists(csv_file):
        from dataset.generate_dataset import generate_energy_dataset
        generate_energy_dataset()

    conn = get_db_connection()
    # Remove existing for this user and reload
    conn.execute("DELETE FROM energy_data WHERE user_id = ?", (user_id,))

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows_to_insert = []
        for row in reader:
            energy = float(row.get("Energy_kWh", 0))
            ac_h = float(row.get("AC_Usage_Hours", 0))
            temp = float(row.get("Temperature", 25))
            is_anomaly = 1 if (energy > 3.8 or (ac_h > 0.8 and temp < 24)) else 0
            reason = "Spike in consumption" if is_anomaly else ""

            rows_to_insert.append((
                user_id, row.get("Date"), row.get("Time"), energy,
                int(row.get("Occupants", 1)), int(row.get("Lights", 2)),
                int(row.get("Fans", 1)), ac_h, float(row.get("Computer_Usage_Hours", 0)),
                float(row.get("Appliance_Operating_Hours", 0.5)), temp,
                float(row.get("Humidity", 50)), int(row.get("Is_Weekend", 0)),
                is_anomaly, reason
            ))

        conn.executemany("""
        INSERT INTO energy_data (
            user_id, record_date, record_time, energy_kwh, occupants, lights,
            fans, ac_hours, computer_hours, appliance_hours, temperature,
            humidity, is_weekend, is_anomaly, anomaly_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows_to_insert)
        conn.commit()
    conn.close()

    flash(f"Loaded {len(rows_to_insert)} simulated benchmark records into your workspace!", "success")
    return redirect(url_for('analysis'))


# ==========================================
# ENERGY ANALYSIS & EXPLORATION
# ==========================================

@app.route('/analysis')
@login_required
def analysis():
    user = get_current_user()
    user_id = user['id']

    conn = get_db_connection()
    records = conn.execute("""
    SELECT * FROM energy_data 
    WHERE user_id = ? 
    ORDER BY record_date DESC, record_time DESC 
    LIMIT 500
    """, (user_id,)).fetchall()

    if not records:
        records = conn.execute("""
        SELECT * FROM energy_data 
        ORDER BY record_date DESC, record_time DESC 
        LIMIT 500
        """).fetchall()

    conn.close()

    # Statistical computation
    if records:
        energies = [r['energy_kwh'] for r in records]
        temperatures = [r['temperature'] for r in records]
        ac_usages = [r['ac_hours'] for r in records]

        stats = {
            "total_records": len(records),
            "total_kwh": round(sum(energies), 2),
            "mean_kwh": round(sum(energies) / len(energies), 3),
            "min_kwh": round(min(energies), 3),
            "max_kwh": round(max(energies), 3),
            "avg_temp": round(sum(temperatures) / len(temperatures), 1),
            "avg_ac_hours": round(sum(ac_usages) / len(ac_usages), 2),
            "anomalies_count": sum(1 for r in records if r['is_anomaly'] == 1)
        }
    else:
        stats = {
            "total_records": 0, "total_kwh": 0, "mean_kwh": 0,
            "min_kwh": 0, "max_kwh": 0, "avg_temp": 0,
            "avg_ac_hours": 0, "anomalies_count": 0
        }

    return render_template('analysis.html', records=records, stats=stats)


# ==========================================
# PREDICTION & MODEL COMPARISON
# ==========================================

@app.route('/prediction', methods=['GET', 'POST'])
@login_required
def prediction():
    user = get_current_user()
    user_id = user['id']
    tariff_rate = user['tariff_rate']

    # Default form values
    form_data = {
        "occupants": 3,
        "temperature": 32.0,
        "humidity": 55.0,
        "ac_hours": 0.8,
        "computer_hours": 0.6,
        "appliance_hours": 0.5,
        "lights": 5,
        "fans": 3,
        "is_weekend": 0,
        "model_name": "Gradient Boosting"
    }

    prediction_result = None

    if request.method == 'POST':
        form_data = {
            "occupants": int(request.form.get("occupants", 2)),
            "temperature": float(request.form.get("temperature", 28.0)),
            "humidity": float(request.form.get("humidity", 50.0)),
            "ac_hours": float(request.form.get("ac_hours", 0.5)),
            "computer_hours": float(request.form.get("computer_hours", 0.5)),
            "appliance_hours": float(request.form.get("appliance_hours", 0.5)),
            "lights": int(request.form.get("lights", 3)),
            "fans": int(request.form.get("fans", 2)),
            "is_weekend": int(request.form.get("is_weekend", 0)),
            "model_name": request.form.get("model_name", "Gradient Boosting")
        }

        # Inference
        prediction_result = predict_energy_consumption(
            form_data,
            model_name=form_data["model_name"],
            tariff_rate=tariff_rate
        )

        # Save to predictions history
        conn = get_db_connection()
        conn.execute("""
        INSERT INTO predictions (
            user_id, occupants, lights, fans, ac_hours, computer_hours,
            appliance_hours, temperature, humidity, predicted_kwh,
            model_used, daily_cost_est, monthly_cost_est, co2_emissions_kg
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, form_data["occupants"], form_data["lights"], form_data["fans"],
            form_data["ac_hours"], form_data["computer_hours"], form_data["appliance_hours"],
            form_data["temperature"], form_data["humidity"],
            prediction_result["predicted_hourly_kwh"],
            prediction_result["chosen_model"],
            prediction_result["hourly_cost"],
            prediction_result["monthly_cost"],
            prediction_result["monthly_co2_kg"]
        ))
        conn.commit()
        conn.close()

    # Load history & metrics
    conn = get_db_connection()
    history = conn.execute("""
    SELECT * FROM predictions 
    WHERE user_id = ? 
    ORDER BY created_at DESC 
    LIMIT 10
    """, (user_id,)).fetchall()
    conn.close()

    metrics_meta = get_model_metrics()

    # Run default prediction if GET request
    if prediction_result is None:
        prediction_result = predict_energy_consumption(
            form_data,
            model_name=form_data["model_name"],
            tariff_rate=tariff_rate
        )

    return render_template(
        'prediction.html',
        form_data=form_data,
        prediction_result=prediction_result,
        metrics_meta=metrics_meta,
        history=history
    )


# ==========================================
# APPLIANCES & ANOMALY DETECTION
# ==========================================

@app.route('/appliances', methods=['GET', 'POST'])
@login_required
def appliances():
    user = get_current_user()
    user_id = user['id']
    tariff_rate = user['tariff_rate']

    if request.method == 'POST':
        app_name = request.form.get('appliance_name', '').strip()
        category = request.form.get('category', 'General').strip()
        power_w = float(request.form.get('rated_power_w', 100))
        hours = float(request.form.get('avg_daily_hours', 4.0))

        # Calculate daily kWh, monthly cost, and monthly CO2
        daily_kwh = round((power_w * hours) / 1000.0, 3)
        monthly_cost = round(daily_kwh * 30.0 * tariff_rate, 2)
        co2_monthly = round(daily_kwh * 30.0 * 0.82, 2)

        status = "Normal"
        if category == "Cooling" and hours > 7.0:
            status = "High Usage"
        elif category == "Heating" and hours > 2.0:
            status = "High Usage"
        elif power_w < 50:
            status = "Efficient"

        conn = get_db_connection()
        conn.execute("""
        INSERT INTO appliances (
            user_id, appliance_name, category, rated_power_w, avg_daily_hours,
            daily_kwh, monthly_cost, co2_kg_monthly, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, app_name, category, power_w, hours, daily_kwh, monthly_cost, co2_monthly, status))
        conn.commit()
        conn.close()

        flash(f"Appliance '{app_name}' added to inventory!", "success")
        return redirect(url_for('appliances'))

    conn = get_db_connection()
    app_list = conn.execute("SELECT * FROM appliances WHERE user_id = ?", (user_id,)).fetchall()
    if not app_list:
        app_list = conn.execute("SELECT * FROM appliances LIMIT 10").fetchall()

    # Get recent anomalies for user
    anomalies = conn.execute("""
    SELECT * FROM energy_data 
    WHERE user_id = ? AND is_anomaly = 1 
    ORDER BY record_date DESC, record_time DESC 
    LIMIT 20
    """, (user_id,)).fetchall()

    conn.close()

    waste_alerts = analyze_appliance_waste_summary([dict(a) for a in app_list])
    total_app_kwh = sum(a['daily_kwh'] for a in app_list)
    total_app_cost = sum(a['monthly_cost'] for a in app_list)

    return render_template(
        'appliances.html',
        appliances=app_list,
        waste_alerts=waste_alerts,
        anomalies=anomalies,
        total_app_kwh=round(total_app_kwh, 2),
        total_app_cost=round(total_app_cost, 2)
    )


@app.route('/appliances/delete/<int:app_id>', methods=['POST'])
@login_required
def delete_appliance(app_id):
    user = get_current_user()
    conn = get_db_connection()
    conn.execute("DELETE FROM appliances WHERE id = ? AND user_id = ?", (app_id, user['id']))
    conn.commit()
    conn.close()
    flash("Appliance removed from inventory.", "info")
    return redirect(url_for('appliances'))


# ==========================================
# SUSTAINABLE RECOMMENDATIONS
# ==========================================

@app.route('/recommendations')
@login_required
def recommendations():
    user = get_current_user()
    user_id = user['id']
    tariff_rate = user['tariff_rate']

    conn = get_db_connection()
    # Fetch user records & appliances
    user_data = conn.execute("SELECT * FROM energy_data WHERE user_id = ? LIMIT 300", (user_id,)).fetchall()
    appliances = conn.execute("SELECT * FROM appliances WHERE user_id = ?", (user_id,)).fetchall()
    stored_recs = conn.execute("SELECT * FROM recommendations WHERE user_id = ? ORDER BY id ASC", (user_id,)).fetchall()
    conn.close()

    dynamic_recs = generate_dynamic_recommendations(
        [dict(r) for r in user_data],
        [dict(a) for a in appliances],
        tariff_rate=tariff_rate
    )

    total_kwh_savings = sum(r['estimated_saving_kwh'] for r in dynamic_recs)
    total_cost_savings = sum(r['estimated_cost_saving'] for r in dynamic_recs)
    total_co2_savings = sum(r['estimated_co2_saving'] for r in dynamic_recs)

    return render_template(
        'recommendations.html',
        recommendations=dynamic_recs,
        stored_recommendations=stored_recs,
        total_kwh_savings=round(total_kwh_savings, 1),
        total_cost_savings=round(total_cost_savings, 2),
        total_co2_savings=round(total_co2_savings, 1)
    )


@app.route('/recommendations/toggle/<int:rec_id>', methods=['POST'])
@login_required
def toggle_recommendation(rec_id):
    user = get_current_user()
    conn = get_db_connection()
    current = conn.execute("SELECT is_implemented FROM recommendations WHERE id = ? AND user_id = ?", (rec_id, user['id'])).fetchone()
    if current:
        new_val = 0 if current['is_implemented'] == 1 else 1
        conn.execute("UPDATE recommendations SET is_implemented = ? WHERE id = ?", (new_val, rec_id))
        conn.commit()
        flash("Recommendation status updated!", "success")
    conn.close()
    return redirect(url_for('recommendations'))


# ==========================================
# ENERGY AUDIT & REPORTS
# ==========================================

@app.route('/reports')
@login_required
def reports():
    user = get_current_user()
    user_id = user['id']
    tariff_rate = user['tariff_rate']

    conn = get_db_connection()
    records = conn.execute("SELECT * FROM energy_data WHERE user_id = ? ORDER BY record_date DESC LIMIT 300", (user_id,)).fetchall()
    appliances = conn.execute("SELECT * FROM appliances WHERE user_id = ?", (user_id,)).fetchall()
    predictions = conn.execute("SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (user_id,)).fetchall()
    conn.close()

    total_kwh = sum(r['energy_kwh'] for r in records) if records else 0.0
    daily_avg_kwh = round((total_kwh / len(records)) * 24 * 0.45, 2) if records else 0.0
    monthly_kwh = round(daily_avg_kwh * 30, 2)

    bill_calc = calculate_tiered_bill(monthly_kwh)
    co2_calc = calculate_co2_emissions(monthly_kwh, is_monthly_total=True)
    savings_calc = calculate_potential_savings(daily_avg_kwh, target_reduction_pct=20.0, tariff_rate=tariff_rate)
    metrics_meta = get_model_metrics()

    return render_template(
        'reports.html',
        user=user,
        records=records,
        appliances=appliances,
        predictions=predictions,
        bill_calc=bill_calc,
        co2_calc=co2_calc,
        savings_calc=savings_calc,
        metrics_meta=metrics_meta,
        report_date=datetime.now().strftime("%B %d, %Y")
    )


@app.route('/reports/export-csv')
@login_required
def export_csv():
    user = get_current_user()
    conn = get_db_connection()
    records = conn.execute("SELECT * FROM energy_data WHERE user_id = ? ORDER BY record_date DESC, record_time DESC", (user['id'],)).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Date", "Time", "Energy_kWh", "Occupants", "Lights", "Fans",
        "AC_Usage_Hours", "Computer_Usage_Hours", "Appliance_Operating_Hours",
        "Temperature", "Humidity", "Is_Weekend", "Is_Anomaly", "Anomaly_Reason"
    ])

    for r in records:
        writer.writerow([
            r['id'], r['record_date'], r['record_time'], r['energy_kwh'],
            r['occupants'], r['lights'], r['fans'], r['ac_hours'],
            r['computer_hours'], r['appliance_hours'], r['temperature'],
            r['humidity'], r['is_weekend'], r['is_anomaly'], r['anomaly_reason']
        ])

    output.seek(0)
    filename = f"energy_audit_report_{user['username']}_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


# ==========================================
# USER PROFILE & SETTINGS
# ==========================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    user_id = user['id']

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        tariff_rate = float(request.form.get('tariff_rate', 7.50))
        new_password = request.form.get('new_password', '')

        if not full_name or not email:
            flash("Name and email cannot be empty.", "danger")
            return redirect(url_for('profile'))

        conn = get_db_connection()
        if new_password:
            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "danger")
                conn.close()
                return redirect(url_for('profile'))
            pwd_hash = generate_password_hash(new_password)
            conn.execute("""
            UPDATE users SET full_name = ?, email = ?, tariff_rate = ?, password_hash = ?
            WHERE id = ?
            """, (full_name, email, tariff_rate, pwd_hash, user_id))
        else:
            conn.execute("""
            UPDATE users SET full_name = ?, email = ?, tariff_rate = ?
            WHERE id = ?
            """, (full_name, email, tariff_rate, user_id))

        conn.commit()
        conn.close()

        flash("Profile and tariff settings updated successfully!", "success")
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


# ==========================================
# REST JSON APIs FOR CHART.JS VISUALIZATION
# ==========================================

@app.route('/api/dashboard-charts')
@login_required
def api_dashboard_charts():
    user = get_current_user()
    user_id = user['id']

    conn = get_db_connection()
    records = conn.execute("""
    SELECT * FROM energy_data 
    WHERE user_id = ? 
    ORDER BY record_date ASC, record_time ASC 
    LIMIT 150
    """, (user_id,)).fetchall()

    if not records:
        records = conn.execute("""
        SELECT * FROM energy_data 
        ORDER BY record_date ASC, record_time ASC 
        LIMIT 150
        """).fetchall()

    appliances = conn.execute("SELECT * FROM appliances WHERE user_id = ?", (user_id,)).fetchall()
    if not appliances:
        appliances = conn.execute("SELECT * FROM appliances LIMIT 10").fetchall()
    conn.close()

    # Time series labels and values
    time_series_labels = [f"{r['record_date']} {r['record_time']}" for r in records[-40:]]
    time_series_kwh = [r['energy_kwh'] for r in records[-40:]]
    anomalies_points = [
        {"x": f"{r['record_date']} {r['record_time']}", "y": r['energy_kwh']}
        for r in records[-40:] if r['is_anomaly'] == 1
    ]

    # Hourly average profile (24 hours)
    hourly_buckets = {h: [] for h in range(24)}
    for r in records:
        try:
            h = int(r['record_time'].split(':')[0])
            hourly_buckets[h].append(r['energy_kwh'])
        except Exception:
            continue

    hourly_labels = [f"{h:02d}:00" for h in range(24)]
    hourly_avg_kwh = [
        round(float(sum(hourly_buckets[h]) / len(hourly_buckets[h])), 3) if hourly_buckets[h] else 0.5
        for h in range(24)
    ]

    # Appliance share breakdown
    appliance_labels = [a['appliance_name'] for a in appliances]
    appliance_kwh = [a['daily_kwh'] for a in appliances]

    return jsonify({
        "time_series": {
            "labels": time_series_labels,
            "values": time_series_kwh,
            "anomalies": anomalies_points
        },
        "hourly_profile": {
            "labels": hourly_labels,
            "values": hourly_avg_kwh
        },
        "appliance_share": {
            "labels": appliance_labels,
            "values": appliance_kwh
        }
    })


@app.route('/api/predict-live', methods=['POST'])
@login_required
def api_predict_live():
    data = request.get_json() or {}
    user = get_current_user()
    tariff = user['tariff_rate'] if user else 7.50
    result = predict_energy_consumption(data, model_name=data.get('model_name'), tariff_rate=tariff)
    return jsonify(result)


# ==========================================
# APPLICATION ENTRYPOINT
# ==========================================

if __name__ == '__main__':
    print(">> Starting AI Energy Consumption Prediction & Recommendation System...")
    print(">> Local URL: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
