"""
Automated Test Suite for AI Energy Consumption Prediction & Recommendation System.
Verifies all modules, ML algorithms, database tables, calculations, and Flask HTTP routes.
"""

import unittest
import os
import json
import sqlite3

from init_db import init_db, get_db_connection
from ml_engine import (
    LinearRegressionModel, DecisionTreeRegressorModel,
    RandomForestRegressorModel, GradientBoostingRegressorModel,
    StandardScaler, mean_absolute_error, root_mean_squared_error, r2_score
)
from train_model import train_and_evaluate
from prediction import predict_energy_consumption, get_model_metrics
from energy_calculator import calculate_costs, calculate_tiered_bill, calculate_co2_emissions, calculate_potential_savings
from anomaly_detector import detect_consumption_anomalies, analyze_appliance_waste_summary
from recommendation import generate_dynamic_recommendations
from app import app

class TestEnergySystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        train_and_evaluate()
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_database_tables(self):
        conn = get_db_connection()
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        self.assertIn('users', tables)
        self.assertIn('energy_data', tables)
        self.assertIn('appliances', tables)
        self.assertIn('predictions', tables)
        self.assertIn('recommendations', tables)

    def test_energy_calculator(self):
        cost = calculate_costs(10.0, tariff_rate=7.50)
        self.assertEqual(cost['daily_cost'], 75.0)
        self.assertEqual(cost['monthly_cost'], 2250.0)

        tiered = calculate_tiered_bill(250)
        self.assertGreater(tiered['grand_total'], 0)

        co2 = calculate_co2_emissions(10.0)
        self.assertGreater(co2['daily_co2_kg'], 0)
        self.assertGreater(co2['trees_needed_to_offset'], 0)

        savings = calculate_potential_savings(10.0, target_reduction_pct=20.0, tariff_rate=7.50)
        self.assertGreater(savings['monthly_savings'], 0)

    def test_ml_prediction(self):
        inputs = {
            "occupants": 3,
            "temperature": 32.0,
            "humidity": 50.0,
            "ac_hours": 0.8,
            "computer_hours": 0.6,
            "appliance_hours": 0.5,
            "lights": 5,
            "fans": 3,
            "is_weekend": 0
        }
        res = predict_energy_consumption(inputs)
        self.assertIn('predicted_hourly_kwh', res)
        self.assertGreater(res['predicted_hourly_kwh'], 0)
        self.assertIn('model_comparisons', res)
        self.assertEqual(len(res['model_comparisons']), 4)

    def test_anomaly_detector(self):
        records = [
            {"energy_kwh": 1.2, "temperature": 28, "ac_hours": 0.5, "lights": 3, "occupants": 2, "computer_hours": 0.5, "appliance_hours": 0.5, "Time": "14:00"},
            {"energy_kwh": 5.8, "temperature": 19, "ac_hours": 1.0, "lights": 16, "occupants": 0, "computer_hours": 1.0, "appliance_hours": 2.0, "Time": "02:00"}
        ]
        analyzed = detect_consumption_anomalies(records)
        self.assertEqual(len(analyzed), 2)
        self.assertEqual(analyzed[1]['is_anomaly'], 1)

    def test_recommendation_engine(self):
        data = [{"ac_hours": 0.9, "computer_hours": 0.8, "temperature": 34, "lights": 6, "energy_kwh": 3.2}]
        recs = generate_dynamic_recommendations(data, tariff_rate=7.50)
        self.assertGreater(len(recs), 0)
        self.assertIn('estimated_cost_saving', recs[0])

    def test_flask_routes(self):
        # Test Login Page
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Sign In', res.data)

        # Test Register Page
        res = self.client.get('/register')
        self.assertEqual(res.status_code, 200)

        # Login as demo_user
        login_res = self.client.post('/login', data={'username': 'demo_user', 'password': 'password123'}, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Energy Intelligence Dashboard', login_res.data)

        # Test Dashboard
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 200)

        # Test Prediction Page
        pred_res = self.client.get('/prediction')
        self.assertEqual(pred_res.status_code, 200)
        self.assertIn(b'Simulation', pred_res.data)

        # Test Analysis Page
        ana_res = self.client.get('/analysis')
        self.assertEqual(ana_res.status_code, 200)

        # Test Appliances Page
        app_res = self.client.get('/appliances')
        self.assertEqual(app_res.status_code, 200)

        # Test Recommendations Page
        rec_res = self.client.get('/recommendations')
        self.assertEqual(rec_res.status_code, 200)

        # Test Reports Page
        rep_res = self.client.get('/reports')
        self.assertEqual(rep_res.status_code, 200)

        # Test API Dashboard Charts
        api_res = self.client.get('/api/dashboard-charts')
        self.assertEqual(api_res.status_code, 200)
        api_data = json.loads(api_res.data)
        self.assertIn('time_series', api_data)
        self.assertIn('hourly_profile', api_data)
        self.assertIn('appliance_share', api_data)

        # Test Live Predict API
        live_res = self.client.post('/api/predict-live', json={'occupants': 2, 'temperature': 30, 'ac_hours': 0.5})
        self.assertEqual(live_res.status_code, 200)
        live_data = json.loads(live_res.data)
        self.assertIn('predicted_hourly_kwh', live_data)

if __name__ == '__main__':
    unittest.main()
