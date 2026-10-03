"""
Database Initialization Script for SQLite.
Creates all required tables (users, energy_data, appliances, predictions, recommendations),
indexes, and seeds initial demo data and appliances.
"""

import os
import sqlite3
import csv
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = "database.db"

def get_db_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Enable Foreign Keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        tariff_rate REAL DEFAULT 7.50,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Energy Data Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS energy_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        record_date TEXT NOT NULL,
        record_time TEXT NOT NULL,
        energy_kwh REAL NOT NULL,
        occupants INTEGER NOT NULL,
        lights INTEGER NOT NULL,
        fans INTEGER NOT NULL,
        ac_hours REAL NOT NULL,
        computer_hours REAL NOT NULL,
        appliance_hours REAL NOT NULL,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        is_weekend INTEGER NOT NULL,
        is_anomaly INTEGER DEFAULT 0,
        anomaly_reason TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 3. Appliances Inventory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appliances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        appliance_name TEXT NOT NULL,
        category TEXT NOT NULL,
        rated_power_w REAL NOT NULL,
        avg_daily_hours REAL NOT NULL,
        daily_kwh REAL NOT NULL,
        monthly_cost REAL NOT NULL,
        co2_kg_monthly REAL NOT NULL,
        status TEXT DEFAULT 'Normal',
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 4. Predictions History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        occupants INTEGER NOT NULL,
        lights INTEGER NOT NULL,
        fans INTEGER NOT NULL,
        ac_hours REAL NOT NULL,
        computer_hours REAL NOT NULL,
        appliance_hours REAL NOT NULL,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        predicted_kwh REAL NOT NULL,
        model_used TEXT NOT NULL,
        daily_cost_est REAL NOT NULL,
        monthly_cost_est REAL NOT NULL,
        co2_emissions_kg REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 5. Recommendations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        estimated_saving_kwh REAL NOT NULL,
        estimated_cost_saving REAL NOT NULL,
        estimated_co2_saving REAL NOT NULL,
        priority TEXT DEFAULT 'Medium',
        is_implemented INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Seed Default Users if not existing
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_pass = generate_password_hash("admin123")
        demo_pass = generate_password_hash("password123")

        cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, tariff_rate, role)
        VALUES 
        ('admin', 'admin@energyai.org', ?, 'System Administrator', 8.00, 'admin'),
        ('demo_user', 'demo@energyai.org', ?, 'Alex Sustainable', 7.50, 'user')
        """, (admin_pass, demo_pass))
        conn.commit()
        print(">> Created default user accounts: admin/admin123 and demo_user/password123")

    # Seed Default Appliances for demo_user (user_id = 2 and user_id = 1)
    cursor.execute("SELECT id FROM users WHERE username = 'demo_user'")
    user_row = cursor.fetchone()
    if user_row:
        demo_uid = user_row[0]
        cursor.execute("SELECT COUNT(*) FROM appliances WHERE user_id = ?", (demo_uid,))
        if cursor.fetchone()[0] == 0:
            default_appliances = [
                (demo_uid, "Inverter Split AC (1.5 Ton)", "Cooling", 1500, 6.5, 9.75, 2193.75, 239.85, "High Usage"),
                (demo_uid, "Refrigerator (Double Door 300L)", "Refrigeration", 180, 24.0, 2.16, 486.00, 53.14, "Normal"),
                (demo_uid, "Desktop Workstation & Dual Monitors", "Computing", 280, 8.0, 2.24, 504.00, 55.10, "High Usage"),
                (demo_uid, "Ceiling Fans (4 Units)", "Circulation", 260, 12.0, 3.12, 702.00, 76.75, "Normal"),
                (demo_uid, "LED Lights (10 Units)", "Lighting", 100, 6.0, 0.60, 135.00, 14.76, "Efficient"),
                (demo_uid, "Microwave Oven", "Kitchen", 1200, 0.4, 0.48, 108.00, 11.81, "Normal"),
                (demo_uid, "Washing Machine (Front Load)", "Laundry", 500, 1.2, 0.60, 135.00, 14.76, "Normal"),
                (demo_uid, "Water Geyser / Heater", "Heating", 2000, 1.0, 2.00, 450.00, 49.20, "High Usage")
            ]
            cursor.executemany("""
            INSERT INTO appliances (user_id, appliance_name, category, rated_power_w, avg_daily_hours, daily_kwh, monthly_cost, co2_kg_monthly, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_appliances)
            conn.commit()
            print(">> Seeded default appliances inventory.")

    # Seed Default Energy Data from dataset/energy_data.csv for demo_user
    cursor.execute("SELECT COUNT(*) FROM energy_data")
    if cursor.fetchone()[0] == 0:
        csv_file = "dataset/energy_data.csv"
        if os.path.exists(csv_file):
            print(">> Loading sample dataset into SQLite energy_data table...")
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows_to_insert = []
                for row in reader:
                    # Anomaly detection heuristic
                    ac_h = float(row.get("AC_Usage_Hours", 0))
                    energy = float(row.get("Energy_kWh", 0))
                    temp = float(row.get("Temperature", 25))
                    is_anomaly = 0
                    reason = ""

                    if energy > 3.8:
                        is_anomaly = 1
                        reason = "High Energy Consumption Spike"
                    elif ac_h > 0.8 and temp < 24:
                        is_anomaly = 1
                        reason = "AC operating during low ambient temperature"

                    rows_to_insert.append((
                        demo_uid if user_row else 1,
                        row.get("Date"),
                        row.get("Time"),
                        energy,
                        int(row.get("Occupants", 1)),
                        int(row.get("Lights", 2)),
                        int(row.get("Fans", 1)),
                        ac_h,
                        float(row.get("Computer_Usage_Hours", 0)),
                        float(row.get("Appliance_Operating_Hours", 0.5)),
                        temp,
                        float(row.get("Humidity", 50)),
                        int(row.get("Is_Weekend", 0)),
                        is_anomaly,
                        reason
                    ))

                cursor.executemany("""
                INSERT INTO energy_data (
                    user_id, record_date, record_time, energy_kwh, occupants, lights,
                    fans, ac_hours, computer_hours, appliance_hours, temperature,
                    humidity, is_weekend, is_anomaly, anomaly_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, rows_to_insert)
                conn.commit()
                print(f">> Successfully loaded {len(rows_to_insert)} records into energy_data.")

    # Seed Default Sustainability Recommendations
    cursor.execute("SELECT COUNT(*) FROM recommendations")
    if cursor.fetchone()[0] == 0:
        recommendations = [
            (demo_uid if user_row else 1, "Cooling Optimization", "Optimize Air Conditioner Thermostat to 24°C",
             "Increasing AC setpoint from 18°C/20°C to 24°C reduces cooling load by up to 24% without sacrificing thermal comfort.",
             3.2, 720.0, 78.7, "High", 0),
            (demo_uid if user_row else 1, "Phantom Load", "Eliminate Standby / Phantom Power on Workstations",
             "Use smart power strips for computer monitors, printers, and chargers to cut continuous vampire draw.",
             0.8, 180.0, 19.6, "Medium", 0),
            (demo_uid if user_row else 1, "Lighting", "Transition to Motion-Sensor High-Efficiency LEDs",
             "Upgrade common area lighting to 9W smart LEDs with automatic vacancy sensors to avoid daytime wastage.",
             0.5, 112.5, 12.3, "Low", 0),
            (demo_uid if user_row else 1, "Load Shifting", "Shift Washing Machine & Geyser to Off-Peak Hours",
             "Run heavy heating and washing cycles during early morning or solar peak hours to lower peak grid strain.",
             1.4, 315.0, 34.4, "Medium", 0),
            (demo_uid if user_row else 1, "Natural Ventilation", "Utilize Cross Ventilation During Cooler Evenings",
             "Switch off AC and leverage ceiling fans with open windows when ambient outdoor temperature drops below 26°C.",
             2.5, 562.5, 61.5, "High", 0)
        ]

        cursor.executemany("""
        INSERT INTO recommendations (
            user_id, category, title, description, estimated_saving_kwh,
            estimated_cost_saving, estimated_co2_saving, priority, is_implemented
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, recommendations)
        conn.commit()
        print(">> Seeded default sustainability recommendations.")

    conn.close()
    print(">> Database initialization completed successfully.")

if __name__ == "__main__":
    init_db()
