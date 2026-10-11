# KrishiMandi – Agricultural Trade & Mandi Price Intelligence System

**B.Tech Final Year Capstone Project (Computer Science & Information Technology)**

---

## 🌾 Project Overview

**KrishiMandi (CropPricePredict)** is a full-stack agricultural commodity trading and price intelligence web application. It connects farmers directly with grain traders, eliminates unnecessary middlemen, provides statistical price forecasting for APMC mandis, and enforces secure, role-based data isolation with complete oversight for regulatory super administrators.

### Core Problems Solved:
1. **Information Asymmetry**: Farmers often do not know whether mandi prices will rise or fall next month, leading to distress sales right after harvest.
2. **Lack of Direct Market Access**: Produce is often routed through informal intermediaries. KrishiMandi gives farmers a dedicated listing platform to sell directly to verified wholesale buyers.
3. **Data Security & Privacy**: Buyers cannot alter or tamper with sellers' listings; sellers cannot alter buyers' purchase bids or access other farmers' private listings.
4. **Regulatory Transparency**: Regulatory bodies (Super Administrators with `@super.com` emails) can audit all transactions and observe live negotiations and deal interactions between buyers and sellers in real time.

---

## 👥 Multi-Role Architecture

The system features three distinct, isolated user portals:

```
                                 ┌──────────────────────────────┐
                                 │      KrishiMandi Portal      │
                                 │       (Authentication)       │
                                 └──────────────┬───────────────┘
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 ▼                              ▼                              ▼
    ┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
    │     FARMER / SELLER     │    │      TRADER / BUYER     │    │    SUPER ADMINISTRATOR  │
    │  (ramesh.farmer@...)    │    │   (suresh.trader@...)   │    │     (admin@super.com)   │
    ├─────────────────────────┤    ├─────────────────────────┤    ├─────────────────────────┤
    │ • Produce Inventory     │    │ • Farm Marketplace     │    │ • Platform Overview     │
    │ • Incoming Buyer Orders │    │ • My Purchases & Orders │    │ • Buyer-Seller Tracker  │
    │ • Accept / Ship Deals   │    │ • Place Bids & Orders   │    │ • All Users Directory   │
    │ • Mandi Price Forecast  │    │ • Mandi Rate Comparison │    │ • All Listings & Orders │
    │ • Storage vs Sell Advice│    │ • Cancel Pending Orders │    │ • APMC Historical Data  │
    └─────────────────────────┘    └─────────────────────────┘    └─────────────────────────┘
```

### 1. 🌾 Farmer / Seller Portal
- **Produce Management**: Add harvested crops (Commodity, Variety, Quality Grade, Available Quintals, Asking Rate ₹/Qtl, Harvest Date, Mandi location).
- **Strict Data Ownership**: A farmer can view, edit, update stock, or delete **only their own** produce listings. Other sellers' data cannot be modified.
- **Buyer Order Response**: Review incoming purchase offers from buyers. Accept, mark dispatched (with logistics notes), complete, or decline.
- **Mandi Price Forecaster**: Multi-horizon price regression models (7 to 90 days) based on APMC historical records to help farmers decide their asking rates.
- **Storage & Selling Advisor**: Compares warehouse/cold-storage costs against expected future price increases to recommend whether to sell now or store.

### 2. 🛒 Trader / Buyer Portal
- **Live Produce Marketplace**: Search and filter produce listed by verified farmers by crop, state, mandi, and maximum asking rate.
- **Purchase Order & Bidding**: Place purchase orders specifying required quintals, offered rate per quintal, delivery destination, and contract terms.
- **Order Tracker (Strict Isolation)**: A buyer can view **only their own** orders and transactions. A buyer cannot change seller asking prices or alter listings.
- **Pending Order Management**: Cancel pending bids before seller acceptance.
- **Mandi Price Comparison**: Compare mandi rates across states to discover optimal procurement hubs.

### 3. 🛡️ Super Administrator Portal (`*@super.com`)
- **Automatic Privilege Assignment**: Any account with an email address ending in `@super.com` (e.g. `admin@super.com`, `officer@super.com`) is granted Super Admin privileges.
- **Buyer-Seller Interaction Tracking**: Complete chronological audit trail showing how buyers and sellers are interacting (who placed which order, counter-offers, acceptance notes, truck dispatch notices, and deal completions).
- **Cross-Party Matrix**: Interactive matrix showing the exact trading relationships and transaction volumes between specific buyers and sellers.
- **Global User Directory**: Full directory of all registered farmers, grain merchants, and administrators.
- **Global Inventory & Ledger Audit**: Oversight of all produce listings and all orders placed platform-wide, with CSV export capabilities.
- **APMC Mandi Database Records**: Direct browser for the 361,000+ historical APMC benchmark records.

---

## ⚡ Quick Test Accounts

The portal includes 1-click demo logins on the sign-in screen:

| Role | Name | Email | Password | Details |
| :--- | :--- | :--- | :--- | :--- |
| **Seller** | Ramesh Kumar | `ramesh.farmer@mandi.in` | `farmer123` | Khanna Mandi, Punjab (Has active Wheat & Mustard listings) |
| **Seller** | Baldev Singh | `baldev.singh@mandi.in` | `farmer123` | Karnal Mandi, Haryana (Has active Basmati & Cotton listings) |
| **Buyer** | Suresh Patel | `suresh.trader@mandi.in` | `buyer123` | Pune Market Yard, Maharashtra (Has active purchase orders) |
| **Buyer** | Rajesh Gupta | `rajesh.mills@mandi.in` | `buyer123` | Kanpur Mandi, Uttar Pradesh (Has dispatched Rice orders) |
| **Super Admin** | Dr. Priya Sharma | `admin@super.com` | `admin123` | Full administrative oversight across all buyers & sellers |

*Note: You can also register a new account as a Seller or Buyer. Any new email ending in `@super.com` will automatically be granted Super Admin access.*

---

## 💻 Technology Stack

- **Frontend & Web Framework**: Streamlit (Python)
- **Database**: SQLite3 (`market_data.sqlite`) with relational schema for users, listings, orders, and interactions
- **Data Analysis**: Pandas, NumPy
- **Visualizations**: Plotly Express & Plotly Graph Objects
- **Statistical Modeling**: Scikit-Learn (Linear Regression, Random Forest Regressor, HistGradientBoosting)
- **Security & Integrity**: Salted SHA-256 password hashing & role-based database constraints

---

## 📁 Project Directory Structure

```text
CropPricePredict/
├── app.py                      # Application router, authentication check & navigation
├── config.py                   # System configuration, crops metadata & mandis mapping
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── run_app.py                  # CLI launcher script
├── test_pipeline.py            # End-to-end automated test suite
│
├── data/
│   ├── database.py             # APMC historical benchmark data loader (360k+ records)
│   ├── marketplace_db.py       # Users, listings, orders, and interaction tracking
│   ├── generator.py            # Historical dataset generation utilities
│   └── market_data.sqlite      # SQLite database
│
├── pages/
│   ├── auth.py                 # Login, registration & quick demo account picker
│   ├── seller_portal.py        # Seller dashboard, crop inventory & order response
│   ├── buyer_portal.py         # Buyer dashboard, marketplace browsing & order tracking
│   ├── superadmin_portal.py    # Super admin oversight, interaction log & user directory
│   ├── dashboard.py            # APMC market summary & price trends
│   ├── prediction.py           # Mandi price forecasting engine
│   ├── market_analysis.py      # Inter-state mandi price spread & comparison
│   ├── crop_recommendation.py  # Soil agronomics & crop yield profit planner
│   ├── selling_advisor.py      # Warehouse storage cost vs sale timing advisor
│   ├── data_management.py      # APMC CSV dataset upload & table inspector
│   ├── model_management.py     # Statistical regression model evaluation
│   └── reports.py              # Market reports & CSV exporter
│
├── core/
│   ├── advisor.py              # Storage cost calculations & price timing logic
│   ├── evaluator.py            # Model error metric calculations
│   └── predictor.py            # Forecast iteration logic
│
├── ml/
│   ├── preprocessing.py        # Data cleaning and handling missing values
│   ├── feature_engineering.py  # Time series lags, moving averages & seasonality
│   ├── train_model.py          # Time-based train/test split and regression training
│   └── predict.py              # Multi-horizon forecast engine
│
├── ui/
│   └── styles.py               # Custom UI design system, badges, and status pills
│
└── utils/
    ├── calculations.py         # Farm revenue and profit calculations
    └── validation.py           # Dataset schema validation
```

---

## 🚀 How to Run the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
Run the launcher script:
```bash
python run_app.py
```
Or run directly via Streamlit:
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

### 3. Run Automated Tests
```bash
python test_pipeline.py
```
