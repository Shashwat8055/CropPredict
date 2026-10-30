# 🌾 KrishiMandi (CropPricePredict)
## Comprehensive Technical, Architectural & Machine Learning Specification Document
**Degree / Program:** Bachelor of Technology (B.Tech) - Computer Science & Engineering  
**Project Domain:** Applied Machine Learning, Agricultural Price Intelligence & Multiclass Recommendation Systems  
**Architecture:** Dual-Engine Machine Learning (Multiclass Classification + Time-Series Regression)

---

## 1. Complete Index of Imported Modules & Libraries

The system is developed using Python 3.10+ and relies on standard engineering packages for machine learning, statistical computing, persistent storage, and interactive web visualization.

### A. Core Machine Learning & Scientific Computing
| Package / Module | Sub-Modules / Classes Imported | Purpose in Project |
|---|---|---|
| **`scikit-learn` (`sklearn`)** | `sklearn.ensemble.RandomForestClassifier`<br>`sklearn.ensemble.HistGradientBoostingClassifier`<br>`sklearn.ensemble.RandomForestRegressor`<br>`sklearn.ensemble.HistGradientBoostingRegressor`<br>`sklearn.linear_model.LinearRegression`<br>`sklearn.linear_model.Ridge`<br>`sklearn.svm.SVC`<br>`sklearn.tree.DecisionTreeClassifier`<br>`sklearn.naive_bayes.GaussianNB` | Implements the core algorithms for both Multiclass Crop Classification and Time-Series Price Forecasting. |
| **`sklearn.preprocessing`** | `StandardScaler` | Normalizes feature scales (z-score scaling $\mu=0, \sigma=1$) for distance and linear models (SVC, Ridge, OLS). |
| **`sklearn.pipeline`** | `Pipeline` | Chained preprocessing and model inference to prevent data leakage during training and test evaluation. |
| **`sklearn.model_selection`**| `train_test_split` | Partitions datasets into stratified training and testing subsets. |
| **`sklearn.metrics`** | `accuracy_score`, `precision_score`, `recall_score`, `f1_score`, `confusion_matrix`, `mean_absolute_error` (MAE), `mean_squared_error` (MSE), `r2_score` | Computes statistical validation metrics and error distributions for both classification and regression models. |
| **`xgboost`** | `xgboost` | Support for Extreme Gradient Boosted decision trees. |
| **`numpy` (`np`)** | `numpy` (array ops, `sin`, `cos`, `mean`, `std`, `clip`, `random.normal`) | Vectorized mathematical operations, cyclical seasonal feature transforms, and synthetic distribution generation. |
| **`pandas` (`pd`)** | `DataFrame`, `Series`, `to_datetime`, `rolling`, `ewm`, `shift` | Tabular data manipulation, time-series window operations (moving averages, volatility), and data cleaning. |
| **`joblib`** | `dump`, `load` | High-efficiency disk serialization and deserialization of trained scikit-learn model pipelines and metadata. |

### B. User Interface & Data Visualization
| Package / Module | Classes / Functions Imported | Purpose in Project |
|---|---|---|
| **`streamlit` (`st`)** | `st.set_page_config`, `st.sidebar`, `st.columns`, `st.session_state`, `st.dataframe`, `st.plotly_chart`, `st.form` | Web application framework, user session management, and role-based view routing. |
| **`plotly.express` (`px`)** | `px.line`, `px.bar`, `px.scatter`, `px.imshow`, `px.histogram` | High-performance interactive visualizations: correlation heatmaps, $10 \times 10$ confusion matrix, actual vs. predicted diagnostics, and residual distributions. |
| **`plotly.graph_objects`** | `go.Figure`, `go.Scatter` | Multi-horizon confidence interval fan-charts and overlay graphs. |

### C. Persistent Storage & Document Generation
| Package / Module | Sub-Modules Imported | Purpose in Project |
|---|---|---|
| **`sqlite3`** | `connect`, `cursor`, `execute`, `commit` | Embedded relational SQL database engine managing 361,600 historical mandi transactions and role-based marketplace tables. |
| **`reportlab`** | `reportlab.platypus`, `reportlab.lib.pagesizes` | Automated compilation of printable agricultural advisory and financial PDF reports. |
| **`openpyxl`** | `openpyxl` | Excel spreadsheet (.xlsx) data ingestion and table export. |

### D. Python Standard Library Utilities
| Standard Module | Functions / Objects Used | Purpose |
|---|---|---|
| **`pathlib`** | `Path` | Cross-platform filesystem navigation (Windows/Linux agnostic). |
| **`os`, `sys`** | `sys.path`, `os.environ` | Environment configuration and root module resolution. |
| **`datetime`, `time`** | `datetime`, `timedelta`, `time.time`, `time.strftime` | Temporal computations, lead-time forecasting, and execution benchmarking. |
| **`hashlib`** | `hashlib.sha256` | Secure, irreversible salted hashing for user credentials. |
| **`typing`** | `Dict`, `List`, `Tuple`, `Optional`, `Any` | Static type hinting for code readability, validation, and maintenance. |
| **`math`** | `sin`, `cos`, `pi`, `sqrt` | Trigonometric conversions for calendar cyclical seasonality. |

---

## 2. Machine Learning Architecture Overview

The system is constructed upon a **Dual-Engine ML Architecture**:
```
                 ┌────────────────────────────────────────────────────────┐
                 │                  KrishiMandi System                   │
                 └──────────────────────────┬─────────────────────────────┘
                                            │
               ┌────────────────────────────┴───────────────────────────┐
               ▼                                                        ▼
┌───────────────────────────────┐                       ┌───────────────────────────────┐
│     ENGINE 1: CLASSIFIER      │                       │      ENGINE 2: REGRESSOR      │
│  Supervised Crop Suitability  │                       │   APMC Mandi Price Forecast   │
│   (Nutrients & Meteorology)   │                       │  (26 Lags & Chronological MA) │
├───────────────────────────────┤                       ├───────────────────────────────┤
│ Target: 10 Cultivar Classes   │                       │ Target: Modal Price (₹/Qtl)   │
│ Model: Gaussian Naive Bayes   │                       │ Model: L2 Ridge Regression    │
│ Accuracy: 95.20%              │                       │ Metric: R² = 0.998, MAPE = 0.3%│
└──────────────┬────────────────┘                       └───────────────┬───────────────┘
               │                                                        │
               └────────────────────────────┬───────────────────────────┘
                                            ▼
                 ┌────────────────────────────────────────────────────────┐
                 │    Dual-Engine Financial & Risk Optimization Output    │
                 │   Yield (Qtl) × Price (₹/Qtl) - Cultivation Cost = Net  │
                 └────────────────────────────────────────────────────────┘
```

---

## 3. Engine 1: Multiclass Crop Suitability Recommendation System

### A. Purpose
To classify and rank the most suitable crop cultivars for cultivation based on an agricultural field's chemical soil characteristics and prevailing meteorological parameters.

### B. Machine Learning Algorithms Evaluated
Five supervised classifiers were trained and bench-tested under identical conditions:
1. **Gaussian Naive Bayes (`GaussianNB`) — *(Selected Active Model)*:** Computes posterior probabilities $P(\text{Crop}_k \mid X) \propto P(\text{Crop}_k) \prod_{i=1}^d P(x_i \mid \text{Crop}_k)$ under normal distribution assumption.
2. **Support Vector Classifier (`SVC` with RBF Kernel):** Maximizes margin hyperplanes in non-linear kernel space ($C=2.0, \gamma=\text{'scale'}$).
3. **HistGradientBoosting Classifier:** Histogram-binned gradient boosted decision trees ($\text{max\_iter}=100, \eta=0.10$).
4. **Random Forest Classifier:** Bagging ensemble of 100 decision trees (`max_depth=12`, `random_state=42`).
5. **Decision Tree Classifier (`CART`):** Gini impurity recursive binary splitting (`max_depth=10`).

### C. Benchmark Comparison Matrix
| Algorithm | Test Accuracy | Macro Precision | Macro Recall | Macro F1-Score | Fit Latency |
|---|---|---|---|---|---|
| **Gaussian Naive Bayes** *(Selected)* | **95.20%** | **95.60%** | **95.20%** | **95.10%** | **0.006 s** |
| **Support Vector Classifier (RBF)** | 95.00% | 95.30% | 95.00% | 94.90% | 0.082 s |
| **HistGradientBoosting** | 94.60% | 94.90% | 94.60% | 94.50% | 0.420 s |
| **Random Forest Classifier** | 94.20% | 94.50% | 94.20% | 94.10% | 0.185 s |
| **Decision Tree (CART)** | 89.80% | 90.10% | 89.80% | 89.70% | 0.012 s |

### D. Dataset Details & Quantities
- **Source File:** [`data/crop_agronomic_dataset.csv`](file:///C:/Users/DELL/OneDrive/Desktop/CropPricePredict/data/crop_agronomic_dataset.csv) (Benchmarked from Indian Council of Agricultural Research agronomic standards).
- **Total Dataset Volume:** **2,500 samples**
  - Perfectly balanced: **250 records per crop** across 10 crops.
- **Data Splitting Protocol:** **Stratified Split (`stratify=y`)**
  - **Training Dataset (80%):** **2,000 samples** (200 records per class)
  - **Testing / Evaluation Dataset (20%):** **500 samples** (50 records per class)

### E. Dataset Attributes & Fields
The agronomic dataset contains **7 input features** and **1 target class**:

| Attribute | Data Type | Measurement Unit | Value Range | Agronomic Description |
|---|---|---|---|---|
| `N` | Continuous Float | $\text{kg/ha}$ | $10.0 - 200.0$ | Soil available Nitrogen ratio |
| `P` | Continuous Float | $\text{kg/ha}$ | $10.0 - 150.0$ | Soil available Phosphorus ratio |
| `K` | Continuous Float | $\text{kg/ha}$ | $10.0 - 150.0$ | Soil available Potassium ratio |
| `temperature` | Continuous Float | $^\circ\text{C}$ | $10.0 - 45.0$ | Average ambient temperature |
| `humidity` | Continuous Float | $\%$ | $20.0 - 100.0$ | Relative atmospheric humidity |
| `ph` | Continuous Float | $\text{pH scale}$ | $3.5 - 9.5$ | Soil acidity/alkalinity measure |
| `rainfall` | Continuous Float | $\text{mm}$ | $200.0 - 2200.0$ | Seasonal precipitation accumulation |
| **`crop`** | Categorical String | Class Label | 10 Classes | **Target Variable:** `Wheat`, `Rice (Paddy)`, `Cotton`, `Soybean`, `Mustard`, `Maize (Corn)`, `Gram (Chickpea)`, `Tomato`, `Onion`, `Potato` |

---

## 4. Engine 2: APMC Mandi Price Forecasting System

### A. Purpose
To predict daily modal transaction prices (₹/Quintal) across 1 to 90-day future horizons for APMC agricultural mandis to optimize harvest sale timing and arbitrage.

### B. Machine Learning Algorithms Evaluated
1. **$L_2$ Regularized Ridge Regression (`Ridge`) — *(Selected Active Model)*:** Penalized regression optimizing $\min_w \|y - Xw\|_2^2 + \alpha \|w\|_2^2$ with $\alpha = 10.0$, preventing overfitting caused by multicollinearity among rolling lags.
2. **Ordinary Least Squares (`LinearRegression`):** Unpenalized baseline regression model with standardized variables.
3. **Random Forest Regressor:** Non-linear bagged ensemble of 50 decision trees (`max_depth=12`).
4. **HistGradientBoosting Regressor:** Gradient boosted decision trees for non-linear residual minimization.

### C. Regression Performance Metrics
- **Coefficient of Determination ($R^2$):** **0.998 - 1.000**
- **Root Mean Squared Error (RMSE):** **< ₹15.50 / Quintal**
- **Mean Absolute Error (MAE):** **< ₹8.20 / Quintal**
- **Mean Absolute Percentage Error (MAPE):** **0.32%**

### D. Dataset Details & Quantities
- **Source Database:** SQLite database at [`data/market_data.sqlite`](file:///C:/Users/DELL/OneDrive/Desktop/CropPricePredict/data/market_data.sqlite) (AGMARKNET standard schema).
- **Total Master Database Volume:** **361,600 historical transactions** (10 crops, 32 APMC mandis, covering 2023 to 2026).
- **Per-Commodity Historical Series:** **36,130 records** (e.g., Wheat series after 30-day window stabilization).
- **Data Splitting Protocol:** **Strict Chronological Time-Series Split (80 / 20)**
  > **Methodological Justification:** K-Fold cross validation or random shuffling is methodologically invalid for time-series due to **look-ahead bias** (information leakage from future dates into past training sets). The dataset is partitioned chronologically along the timeline:
  - **Training Dataset (80% Historical Past):** **28,904 chronological records**
  - **Testing / Holdout Validation Dataset (20% Unseen Future):** **7,226 holdout records**

### E. Dataset Attributes & Fields

#### 1. Raw Database Attributes (`mandi_crop_prices` table):
| Column Name | SQL Type | Description |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY` | Auto-incrementing unique row identifier. |
| `date` | `TEXT` | Transaction date in ISO format (`YYYY-MM-DD`). |
| `state` | `TEXT` | Indian state jurisdiction (e.g., Punjab, Haryana, MP). |
| `market` | `TEXT` | Regulated APMC Mandi name (e.g., Khanna, Abohar). |
| `commodity` | `TEXT` | Agricultural commodity name. |
| `category` | `TEXT` | Commodity classification (Cereal, Fibre, Pulse, etc.). |
| `arrivals_quintal` | `REAL` | Total volume of crop arrival in the market (Quintals). |
| `min_price` | `REAL` | Minimum transaction rate of the day (₹/Quintal). |
| `max_price` | `REAL` | Maximum transaction rate of the day (₹/Quintal). |
| **`modal_price`** | `REAL` | **Target Variable $y$:** Most common clearing price (₹/Quintal). |
| `temperature_c` | `REAL` | Ambient temperature recorded on transaction day. |
| `rainfall_mm` | `REAL` | Precipitation recorded on transaction day. |
| `fuel_index` | `REAL` | Transportation/diesel fuel price index impacting freight. |
| `latitude`, `longitude` | `REAL` | Geocoordinates of the mandi market yard. |

#### 2. The 26 Engineered Machine Learning Features:
The raw time-series data is transformed into a **26-dimensional feature vector** for regression:

| Feature Family | Feature Identifiers | Count | Mathematical Formulation |
|---|---|:---:|---|
| **Autoregressive Price Lags** | `lag_1`, `lag_2`, `lag_3`, `lag_7`, `lag_14`, `lag_21`, `lag_30` | 7 | $P_{t-k} = \text{Price at day } (t-k)$ |
| **Simple Moving Averages** | `ma_7`, `ma_14`, `ma_30` | 3 | $\text{SMA}_W(t) = \frac{1}{W} \sum_{i=0}^{W-1} P_{t-i}$ |
| **Exponential Moving Averages** | `ema_7`, `ema_21` | 2 | $\text{EMA}(t) = \alpha P_t + (1-\alpha) \text{EMA}(t-1)$ |
| **Rolling Volatility** | `vol_7`, `vol_30` | 2 | Rolling price standard deviation $\sigma_W(t)$ |
| **Momentum & Velocity** | `momentum_7`, `momentum_30`, `price_change_1d` | 3 | Relative rate of price change $\frac{P_t - P_{t-W}}{P_{t-W}}$ and $(P_t - P_{t-1})$ |
| **Market Spread** | `price_spread` | 1 | Intraday spread: $(P_{\max} - P_{\min})$ |
| **Supply Arrival Dynamics** | `arrival`, `arrival_lag_1`, `arrival_ma_7` | 3 | Market supply volume and smoothed arrival trend |
| **Harmonic Cyclical Seasonality**| `sin_month`, `cos_month` | 2 | $\sin\left(\frac{2\pi m}{12}\right)$, $\cos\left(\frac{2\pi m}{12}\right)$ capturing continuous annual seasonality |
| **Exogenous Environmental Covariates** | `rainfall`, `temperature`, `humidity` | 3 | Climatic indicators affecting transit and storage deterioration |
| **TOTAL FEATURE DIMENSIONS** | — | **26** | **Engineered Feature Space $X \in \mathbb{R}^{26}$** |

---

## 5. Security & Access Control Specifications

| User Role | Access Boundaries | Data Isolation Rule |
|---|---|---|
| **Seller (Farmer)** | Listings, Mandi Prices, Crop Planning, Orders. | Can only view and update their own farm listings; read-only access to orders placed by buyers. |
| **Buyer (Trader)** | Marketplace, My Orders, Price Trends. | Can browse all active listings and submit purchase bids; cannot modify seller produce data. |
| **Super Administrator (`*@super.com`)**| Full Audit Trail, ML Model Studio, User Directory, Dispute Resolution. | Complete cross-platform visibility across all buyers, sellers, and logged transaction events. |
