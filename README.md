# KrishiMandi – Dual-Engine Machine Learning Agricultural Intelligence & Trading System

**B.Tech Final Year Capstone Project**  
**Department of Computer Science & Engineering**

---

##  Project Abstract & Problem Formulation

Agricultural markets in India suffer from dual systemic inefficiencies:
1. **Agronomic Misallocation**: Smallholder farmers often cultivate crops without empirical compatibility analysis of their soil chemistry ($N, P, K, \text{pH}$) and localized agro-climatic conditions (Temperature, Humidity, Rainfall).
2. **Post-Harvest Price Volatility**: Lack of transparent future mandi price estimations forces farmers into distress selling during seasonal harvest gluts.

**KrishiMandi** solves both challenges using a **Dual-Engine Machine Learning Pipeline** integrated with a secure, role-isolated commodity trading portal:
- **Engine 1 (Supervised Multiclass Classification)**: Recommends optimal crops based on soil nutrient profiles and meteorological parameters, returning posterior class probabilities $P(\text{Crop}_i \mid \mathbf{x})$.
- **Engine 2 (Supervised Time-Series Regression)**: Predicts expected APMC mandi prices using autoregressive price lags, rolling moving averages, and cyclical seasonal encodings over 1 to 90-day forecast horizons.
- **ML Research & Model Studio**: An interactive experimentation environment providing Exploratory Data Analysis (EDA), confusion matrices, feature importances, actual vs. predicted diagnostics, and live hyperparameter retraining.

---

## 🔬 Machine Learning Pipeline Architecture

```
                                 ┌────────────────────────────────────────────────────────┐
                                 │       KRISHIMANDI DUAL-ENGINE ML ARCHITECTURE          │
                                 └───────────────────────────┬────────────────────────────┘
                                                             │
                             ┌───────────────────────────────┴───────────────────────────────┐
                             ▼                                                               ▼
        ┌─────────────────────────────────────────┐                     ┌─────────────────────────────────────────┐
        │        ENGINE 1: CROP SUITABILITY       │                     │       ENGINE 2: PRICE FORECASTING       │
        │      (Multiclass ML Classification)     │                     │       (Time-Series ML Regression)       │
        ├─────────────────────────────────────────┤                     ├─────────────────────────────────────────┤
        │ • Feature Vector x ∈ R⁷:                │                     │ • Feature Vector z ∈ R²⁶:               │
        │   [N, P, K, Temp, Humidity, pH, Rain]   │                     │   - Price Lags: t-1, t-2, t-3, t-7...   │
        │ • Target: 10 Cultivar Classes           │                     │   - Moving Averages: MA_7, MA_14, MA_30 │
        │ • Algorithms Benchmarked:               │                     │   - Volatility & Momentum: Std_7, Mom_30│
        │   1. Random Forest Classifier           │                     │   - Cyclical Seasonality: sin/cos(m)    │
        │   2. HistGradientBoosting Classifier    │                     │ • Algorithms Benchmarked:               │
        │   3. Support Vector Classifier (RBF)    │                     │   1. Ordinary Least Squares (Linear)    │
        │   4. CART Decision Tree                 │                     │   2. Ridge Regression (L2 Penalty)      │
        │   5. Gaussian Naive Bayes               │                     │   3. Random Forest Regressor            │
        │ • Metrics: Accuracy (95.2%), Macro-F1,  │                     │   4. HistGradientBoosting Regressor     │
        │   Macro-Precision, Confusion Matrix     │                     │ • Metrics: R², RMSE, MAE, MAPE          │
        │ • Output: P(Crop_i | x) Top-K Ranking   │                     │ • Diagnostics: Residual error analysis  │
        └─────────────────────────────────────────┘                     └─────────────────────────────────────────┘
                                                             │
                                                             ▼
                                 ┌────────────────────────────────────────────────────────┐
                                 │          ML RESEARCH & MODEL BENCHMARK STUDIO          │
                                 │    (Correlation Matrix • Confusion Matrix • XAI)       │
                                 └────────────────────────────────────────────────────────┘
```

---

##  Mathematical & Methodological Details

### 1. Engine 1: Multiclass Classification
- **Feature Space**: $\mathbf{x} = [N, P, K, T, H, \text{pH}, R]^T \in \mathbb{R}^7$.
- **Validation**: Stratified 80/20 train/test split ensuring balanced class representation across all 10 cultivar targets.
- **Evaluation Criteria**:
  $$\text{Macro-F1} = \frac{1}{|\mathcal{C}|} \sum_{c \in \mathcal{C}} \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$$
- **Confusion Matrix**: Full $10 \times 10$ matrix computed to analyze inter-class confusion between similar crops (e.g., Gram vs. Soybean).

### 2. Engine 2: Time-Series Regression
- **Feature Construction**:
  - Autoregressive lags: $y_{t-1}, y_{t-2}, y_{t-3}, y_{t-7}, y_{t-14}, y_{t-30}$.
  - Rolling statistics: $\text{MA}_7 = \frac{1}{7}\sum_{i=0}^6 y_{t-i}$, $\text{MA}_{30} = \frac{1}{30}\sum_{i=0}^{29} y_{t-i}$.
  - Cyclical seasonal encoding:
    $$x_{\sin} = \sin\left(\frac{2\pi \cdot \text{month}}{12}\right), \quad x_{\cos} = \cos\left(\frac{2\pi \cdot \text{month}}{12}\right)$$
- **Validation**: Chronological time-series split (first 80% chronologically for training, final 20% for testing) to prevent future data leakage.
- **Evaluation Metrics**:
  $$\text{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^n (y_i - \hat{y}_i)^2}, \quad R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$

---

## 👥 Multi-Role Marketplace & Data Isolation

```
Farmer / Seller Portal ────────┐
                               ├────► SQLite Relational Database ◄──── Super Administrator Portal
Trader / Buyer Portal ─────────┘      (Strict Ownership Controls)      (@super.com Live Oversight)
```

1. **Farmer / Seller Portal**: Manage produce stock, monitor buyer offers, accept/dispatch orders, and access crop planning.
2. **Trader / Buyer Portal**: Browse active farm listings, submit purchase bids, and track order fulfillment. Buyers cannot modify seller listings.
3. **Super Administrator Portal (`*@super.com`)**: Complete real-time audit trail of all transactions and buyer-seller negotiations, with full database record explorer.

---

##  Quick Test Credentials

| Role | User Name | Email | Password | Mandatory Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Seller** | Ramesh Kumar | `ramesh.farmer@mandi.in` | `farmer123` | Can edit only his own produce listings |
| **Seller** | Baldev Singh | `baldev.singh@mandi.in` | `farmer123` | Can respond to incoming orders for his crops |
| **Buyer** | Suresh Patel | `suresh.trader@mandi.in` | `buyer123` | Can browse marketplace and place purchase bids |
| **Buyer** | Rajesh Gupta | `rajesh.mills@mandi.in` | `buyer123` | Can view and track his own procurement orders |
| **Super Admin** | Dr. Priya Sharma | `admin@super.com` | `admin123` | Oversight of all transactions and user interactions |

---

##  Repository Structure

```text
CropPricePredict/
├── app.py                      # Main entry point & role-based routing
├── config.py                   # System configuration, crops metadata & mandis mapping
├── requirements.txt            # Python dependencies
├── README.md                   # Academic project documentation
├── run_app.py                  # CLI launcher script
├── test_pipeline.py            # End-to-end automated test suite (8/8 tests)
│
├── ml/
│   ├── crop_classifier.py      # Multiclass classification pipeline (Random Forest, SVM, etc.)
│   ├── train_model.py          # Time-series regression training pipeline (Linear, RF, HGB)
│   ├── feature_engineering.py  # Lags (t-1..30), rolling moving averages, cyclical sin/cos
│   ├── preprocessing.py        # Outlier filtering, missing value imputation
│   ├── evaluate.py             # MAE, RMSE, R², MAPE, confusion metrics
│   └── predict.py              # Recursive multi-horizon forecasting engine
│
├── views/
│   ├── ml_studio.py            # Academic ML Research & Model Studio (EDA, CM, Residuals, Tuning)
│   ├── crop_recommendation.py  # Dual-engine suitability classification & profit planner
│   ├── prediction.py           # Mandi price forecasting interface
│   ├── seller_portal.py        # Farmer produce listings & order management
│   ├── buyer_portal.py         # Trader marketplace & procurement tracker
│   ├── superadmin_portal.py    # Administrative command center & audit logs
│   ├── auth.py                 # Multi-role authentication & demo login
│   ├── market_analysis.py      # Inter-mandi price spread & spatial comparisons
│   ├── selling_advisor.py      # Storage cost vs. price appreciation timing advisor
│   ├── dashboard.py            # APMC market summary & price trends
│   ├── data_management.py      # APMC CSV dataset upload & inspector
│   └── reports.py              # Market reports & CSV exporter
│
├── data/
│   ├── database.py             # APMC historical benchmark data loader (360k+ records)
│   ├── marketplace_db.py       # User accounts, listings, orders, and interaction tracking
│   ├── generator.py            # Dataset generator utilities
│   ├── crop_agronomic_dataset.csv # Agronomic training dataset (N, P, K, pH, climate)
│   └── market_data.sqlite      # SQLite database
│
├── ui/
│   └── styles.py               # CSS design system, badges, and layout rules
│
└── utils/
    ├── calculations.py         # Agronomic profit calculations & financial metrics
    └── validation.py           # Dataset schema validation
```
pen your browser at `http://localhost:8501`.
