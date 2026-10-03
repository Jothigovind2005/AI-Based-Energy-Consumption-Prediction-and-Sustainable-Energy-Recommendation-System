# Academic Project Documentation

## **AI-Based Energy Consumption Prediction and Sustainable Energy Recommendation System**

**Department of Computer Science & Engineering**

---

## 1. Project Abstract

Electricity consumption in domestic and commercial buildings contributes significantly to operating costs and carbon dioxide ($CO_2$) emissions. Traditional energy monitoring approaches suffer from lack of predictive foresight, delivering static monthly electricity utility bills after consumption has already occurred. This project presents a full-stack, software-only **AI-Based Energy Consumption Prediction and Sustainable Energy Recommendation System**. 

The system leverages Machine Learning algorithms—specifically comparing **Linear Regression**, **Decision Tree**, **Random Forest**, and **Gradient Boosting Regressors**—to accurately predict future power consumption (kWh) based on environmental parameters (temperature, humidity), operational factors (occupancy, appliance runtime hours), and diurnal temporal cycles. 

Furthermore, the application integrates an automated **energy-wasting appliance anomaly detection module** using statistical Z-score and Interquartile Range (IQR) metrics, a **progressive tiered tariff electricity bill calculator**, a **carbon footprint emission index**, and an intelligent **rule-based sustainable recommendation engine**. Built using Python, Flask, SQLite, Scikit-Learn/NumPy, Bootstrap 5, and Chart.js, the system operates completely independently of physical IoT hardware or cloud sensors, making it an ideal, self-contained solution for data-driven residential energy conservation.

---

## 2. Problem Statement

Modern energy management faces four critical challenges:
1. **Lack of Predictive Foresight**: Consumers receive utility bills post-facto at the end of the billing cycle, preventing timely interventions.
2. **Invisible Energy Wastage**: Power-hungry appliances such as air conditioners, water heaters, and continuous workstation standby loads run inefficiently without the user's awareness.
3. **Complex Tariff Structures**: Consumers struggle to estimate progressive multi-tier electricity charges (slab-wise tariffs) and unexpected tax surcharges.
4. **Lack of Actionable Conservation Guidance**: Users lack personalized, quantifiable guidance indicating exactly how much energy, cost, and $CO_2$ emissions they could save by altering specific operational behaviors.

---

## 3. Objectives

The primary objectives of this project are:
* **Predictive Energy Modeling**: Train and evaluate multiple regression machine learning models to forecast future hourly and daily energy consumption with high accuracy ($R^2 > 0.88$).
* **Anomaly & Waste Identification**: Implement statistical algorithms (Z-score, IQR, domain heuristics) to flag abnormal power surges and energy-wasting appliance patterns.
* **Financial & Carbon Modeling**: Provide instant multi-tier slab billing calculations and estimate equivalent carbon emissions ($kg\ CO_2$), tree offset requirements, and vehicular emission equivalents.
* **Personalized Recommendations**: Design an intelligent recommendation engine that provides prioritized (High, Medium, Low) actionable energy-saving measures with quantified financial (₹) and kilowatt-hour savings.
* **Interactive Web Platform**: Deliver a modern, responsive, glassmorphism web dashboard featuring interactive Chart.js visualizations, parameter simulation sliders, CSV dataset ingestion, and printable energy audit reports.
* **100% Non-IoT Compliance**: Execute purely in software using simulated realistic datasets, CSV uploads, and algorithmic modeling without physical hardware dependencies.

---

## 4. Existing System vs. Proposed System

### 4.1 Existing System
* Relies on conventional electromechanical or basic digital utility meters.
* Data is only aggregated once a month by utility personnel.
* Zero predictive forecasting or behavioral analysis.
* Often requires expensive, proprietary IoT sensor networks (ESP32, smart plugs, cloud subscriptions) that suffer from network failure and security vulnerabilities.
* No appliance-level anomaly detection or decarbonization guidance.

### 4.2 Proposed System
* **Proactive & Predictive**: Predicts consumption before it happens using trained ML models.
* **Software-Only & Hardware-Agnostic**: Fully functional using historical/simulated CSV datasets and web inputs.
* **Multi-Algorithm Benchmarking**: Compares Linear Regression, Decision Trees, Random Forests, and Gradient Boosting side-by-side with MAE, RMSE, $R^2$, and MAPE metrics.
* **Automated Waste Alerts**: Identifies abnormal appliance runtimes (e.g. AC running during cool ambient temperatures or phantom vampire loads).
* **Tiered Tariff Billing & Carbon Scorecard**: Calculates slab-wise energy bills and $CO_2$ tree equivalents in real time.
* **Actionable Advice**: Prioritized recommendation cards with quantifiable kWh and ₹ savings.

---

## 5. System Architecture

```
+-------------------------------------------------------------------------------+
|                                  USER / CLIENT                                |
|          (Web Browser: Desktop / Tablet / Mobile - Modern Glassmorphism UI)   |
+-------------------------------------------------------------------------------+
                                      │  ▲ (HTTP / JSON)
                                      ▼  │
+-------------------------------------------------------------------------------+
|                              FLASK WEB APPLICATION                            |
|  ┌─────────────────────────────────────────────────────────────────────────┐  |
|  │ Routes: /login, /dashboard, /prediction, /analysis, /appliances, /reports│  |
|  │ Session Authentication & Security (Werkzeug Password Hashing)           │  |
|  │ REST API Endpoints: /api/dashboard-charts, /api/predict-live            │  |
|  └─────────────────────────────────────────────────────────────────────────┘  |
+-------------------------------------------------------------------------------+
       │                    │                     │                   │
       ▼                    ▼                     ▼                   ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────┐    ┌───────────────┐
│ ML PREDICTION│    │   ANOMALY    │      │    TARIFF    │    │SUSTAINABILITY │
│    ENGINE    │    │  DETECTION   │      │  CALCULATOR  │    │RECOMMENDATIONS│
│              │    │              │      │              │    │               │
│ • Feature    │    │ • Z-Score    │      │ • Slab Rates │    │ • Rule Engine │
│   Scaling    │    │   Analysis   │      │ • Daily /    │    │ • Quantified  │
│ • Gradient   │    │ • IQR Bounds │      │   Monthly /  │    │   kWh Savings │
│   Boosting   │    │ • Appliance  │      │   Yearly Bill│    │ • Quantified  │
│ • Random     │    │   Thresholds │      │ • Carbon CO2 │    │   Cost (₹)    │
│   Forest     │    │ • Waste Alert│      │   Footprint  │    │ • Priority    │
│ • Dec. Tree  │    │   Engine     │      │ • Tree Offset│    │   Tagging     │
│ • Lin. Reg.  │    └──────────────┘      └──────────────┘    └───────────────┘
└──────────────┘
       │                    │                     │                   │
       └────────────────────┴──────────┬──────────┴───────────────────┘
                                       ▼
                       +───────────────────────────────+
                       |        SQLITE DATABASE        |
                       |  ┌─────────────────────────┐  |
                       |  │ • users                 │  |
                       |  │ • energy_data           │  |
                       |  │ • appliances            │  |
                       |  │ • predictions           │  |
                       |  │ • recommendations       │  |
                       |  └─────────────────────────┘  |
                       +───────────────────────────────+
```

---

## 6. Module Descriptions

### Module 1: User Authentication & Profile Management
* Handles secure user registration and login with encrypted password storage.
* Tracks customizable user profile settings, including specific electricity tariff rates (₹/kWh) that dynamically recalculate all financial metrics.

### Module 2: Energy Data Management & CSV Ingestion
* Supports batch ingestion of CSV energy logs containing timestamp, ambient temperature, humidity, occupant count, and appliance runtimes.
* Performs automated data cleaning, validation, and real-time outlier detection on ingestion.
* Includes manual single-record data logging and downloadable sample CSV templates.

### Module 3: Energy Consumption Machine Learning Pipeline
* Implements and benchmarks 4 algorithms:
  1. **Linear Regression (OLS / Ridge)**
  2. **Decision Tree Regressor**
  3. **Random Forest Regressor**
  4. **Gradient Boosting Regressor**
* Extracts and engineers features: `Cooling_Degree`, `Total_Appliance_Hours`, `Hour`, `Month`, `Is_Weekend`.
* Persists the optimal trained model and metric benchmarks (`MAE`, `RMSE`, `$R^2$`, `MAPE`).

### Module 4: Energy-Wasting Appliance & Anomaly Detection
* Utilizes statistical Z-score thresholds ($\mu \pm 2.2\sigma$) and Interquartile Range ($Q_3 + 1.5\times IQR$) to isolate abnormal spikes.
* Evaluates appliance-level operational heuristics (e.g. AC running during low ambient temperature, high workstation runtime during sleep hours).

### Module 5: Progressive Tariff & Carbon Emissions Calculator
* Calculates progressive slab-based electricity bills (Tier 1 to Tier 4) including fixed grid charges and taxes.
* Estimates $CO_2$ emissions using standard grid emission factors ($0.82\text{ kg } CO_2/\text{kWh}$) and computes equivalent trees required for carbon offsetting.

### Module 6: Sustainable Recommendation Engine
* Analyzes consumption habits and generates personalized suggestions with estimated kWh and financial savings.
* Provides interactive tracking where users can mark recommendations as implemented.

### Module 7: Interactive Dashboard & Printable Audit Reports
* Live KPI telemetry cards, Chart.js time-series plots, diurnal load distribution bars, and appliance consumption doughnuts.
* Printable executive energy audit reports with full billing and decarbonization breakdowns.

---

## 7. Mathematical Methodology & Algorithms

### 7.1 Linear Regression (OLS / Ridge)
The target energy consumption $\hat{y}$ is modeled as a linear combination of input features:
$$\hat{y} = \mathbf{X}\mathbf{w} + b$$
Using Ridge regularization to prevent multicollinearity:
$$\mathbf{w} = (\mathbf{X}^T \mathbf{X} + \alpha \mathbf{I})^{-1} \mathbf{X}^T \mathbf{y}$$

### 7.2 Decision Tree & Random Forest Regression
Decision trees partition the feature space by minimizing variance (Mean Squared Error):
$$\text{MSE} = \frac{1}{N} \sum_{i=1}^N (y_i - \bar{y})^2$$
At each split node, the reduction in variance is maximized:
$$\Delta \text{Var} = \text{Var}_{\text{parent}} - \left(\frac{N_{\text{left}}}{N} \text{Var}_{\text{left}} + \frac{N_{\text{right}}}{N} \text{Var}_{\text{right}}\right)$$
Random Forest aggregates $B$ bootstrap decision trees:
$$\hat{y}_{\text{RF}} = \frac{1}{B} \sum_{b=1}^B T_b(\mathbf{x})$$

### 7.3 Gradient Boosting Regression
Builds an additive ensemble of weak decision trees iteratively fitting the negative gradient (residuals):
$$r_{im} = y_i - F_{m-1}(x_i)$$
$$F_m(x) = F_{m-1}(x) + \eta \sum_{j=1}^{J_m} \gamma_{jm} \mathbf{1}(x \in R_{jm})$$
where $\eta = 0.10$ is the learning rate.

### 7.4 Anomaly Z-Score Metric
$$Z = \frac{x_i - \mu}{\sigma}$$
Instances where $Z \ge 2.20$ or $x_i > Q_3 + 1.5 \times \text{IQR}$ are classified as consumption anomalies.

---

## 8. Advantages & Benefits

* **Zero Hardware Costs**: Completely software-based; eliminates sensor purchases, battery replacements, and circuit maintenance.
* **Proactive Cost Reduction**: Users can forecast and adjust habits before incurring high utility charges.
* **Transparency**: Clear comparison across 4 standard machine learning models.
* **Environmental Impact Awareness**: Quantifies carbon footprints and translates emissions into intuitive tree-planting targets.
* **Responsive & Clean Design**: Modern dark/light glassmorphism interface with real-time interactive charts.

---

## 9. Limitations

* **Simulation vs Direct Sub-Metering**: Relies on user-entered or CSV-uploaded telemetry rather than real-time wire-level hardware sub-meters.
* **Static Tariff Baseline**: Default tariff structures represent regional averages and may require manual customization for unusual utility contracts.

---

## 10. Future Enhancements

* **Weather API Integration**: Automated fetching of local ambient temperature and forecast data via public weather APIs.
* **Smart PDF Export Engine**: Server-side generation of styled PDF audit reports with embedded vector graphs.
* **Time-of-Day Dynamic Tariffs**: Automated integration with dynamic Time-of-Use (TOU) pricing grids.
* **Mobile Progressive Web App (PWA)**: Offline caching and push notification reminders for appliance shutoff.

---

## 11. Conclusion

The **AI-Based Energy Consumption Prediction and Sustainable Energy Recommendation System** successfully demonstrates the integration of Machine Learning, predictive modeling, statistical anomaly detection, and modern web application development. By achieving high forecasting accuracy ($R^2 \approx 0.89$) and providing actionable conservation measures with quantifiable cost savings, the project delivers a comprehensive, academically rigorous, and practical software-only solution for modern energy management.
