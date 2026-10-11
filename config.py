"""
CropPricePredict - Configuration & Metadata Module
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models_cache"
REPORTS_DIR = BASE_DIR / "generated_reports"

for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "market_data.sqlite"
DEFAULT_DATASET_PATH = DATA_DIR / "sample_crops_data.csv"

# Supported Crops & Metadata
CROPS_METADATA = {
    "Wheat": {
        "category": "Cereal / Rabi",
        "unit": "₹/Quintal",
        "base_price": 2275.0,
        "price_std": 180.0,
        "peak_harvest_months": [3, 4, 5],
        "lean_months": [10, 11, 12, 1],
        "storage_cost_per_month_quintal": 18.0,
        "shelf_life_months": 12,
    },
    "Rice (Paddy)": {
        "category": "Cereal / Kharif",
        "unit": "₹/Quintal",
        "base_price": 2183.0,
        "price_std": 160.0,
        "peak_harvest_months": [10, 11, 12],
        "lean_months": [5, 6, 7, 8],
        "storage_cost_per_month_quintal": 20.0,
        "shelf_life_months": 12,
    },
    "Cotton": {
        "category": "Cash Crop / Fibre",
        "unit": "₹/Quintal",
        "base_price": 7020.0,
        "price_std": 450.0,
        "peak_harvest_months": [10, 11, 12, 1],
        "lean_months": [5, 6, 7],
        "storage_cost_per_month_quintal": 35.0,
        "shelf_life_months": 8,
    },
    "Soybean": {
        "category": "Oilseed / Kharif",
        "unit": "₹/Quintal",
        "base_price": 4600.0,
        "price_std": 320.0,
        "peak_harvest_months": [9, 10, 11],
        "lean_months": [4, 5, 6, 7],
        "storage_cost_per_month_quintal": 25.0,
        "shelf_life_months": 9,
    },
    "Mustard": {
        "category": "Oilseed / Rabi",
        "unit": "₹/Quintal",
        "base_price": 5650.0,
        "price_std": 380.0,
        "peak_harvest_months": [2, 3, 4],
        "lean_months": [8, 9, 10],
        "storage_cost_per_month_quintal": 22.0,
        "shelf_life_months": 10,
    },
    "Maize (Corn)": {
        "category": "Cereal / Kharif & Rabi",
        "unit": "₹/Quintal",
        "base_price": 2090.0,
        "price_std": 140.0,
        "peak_harvest_months": [9, 10, 1, 2],
        "lean_months": [5, 6, 7],
        "storage_cost_per_month_quintal": 16.0,
        "shelf_life_months": 9,
    },
    "Gram (Chickpea)": {
        "category": "Pulse / Rabi",
        "unit": "₹/Quintal",
        "base_price": 5440.0,
        "price_std": 310.0,
        "peak_harvest_months": [3, 4, 5],
        "lean_months": [9, 10, 11],
        "storage_cost_per_month_quintal": 24.0,
        "shelf_life_months": 12,
    },
    "Tomato": {
        "category": "Vegetable / Perishable",
        "unit": "₹/Quintal",
        "base_price": 2800.0,
        "price_std": 950.0,
        "peak_harvest_months": [12, 1, 2],
        "lean_months": [6, 7, 8],
        "storage_cost_per_month_quintal": 95.0,
        "shelf_life_months": 1,
    },
    "Onion": {
        "category": "Horticulture / Semi-Perishable",
        "unit": "₹/Quintal",
        "base_price": 2400.0,
        "price_std": 720.0,
        "peak_harvest_months": [1, 2, 3, 4],
        "lean_months": [8, 9, 10, 11],
        "storage_cost_per_month_quintal": 40.0,
        "shelf_life_months": 4,
    },
    "Potato": {
        "category": "Horticulture / Cold Storage",
        "unit": "₹/Quintal",
        "base_price": 1650.0,
        "price_std": 420.0,
        "peak_harvest_months": [1, 2, 3],
        "lean_months": [8, 9, 10, 11],
        "storage_cost_per_month_quintal": 28.0,
        "shelf_life_months": 8,
    }
}

# State and Mandi Mapping
STATE_MANDIS = {
    "Punjab": {
        "mandis": ["Ludhiana Mandi", "Khanna Mandi", "Amritsar Mandi", "Bathinda Mandi"],
        "lat": 30.9010,
        "lon": 75.8573
    },
    "Haryana": {
        "mandis": ["Karnal Mandi", "Sirsa Mandi", "Ambala Mandi", "Hisar Mandi"],
        "lat": 29.0588,
        "lon": 76.0856
    },
    "Madhya Pradesh": {
        "mandis": ["Indore Mandi", "Ujjain Mandi", "Bhopal Mandi", "Dewas Mandi"],
        "lat": 22.9734,
        "lon": 78.6569
    },
    "Maharashtra": {
        "mandis": ["Lasalgaon Mandi (Nashik)", "Pune Market", "Nagpur APMC", "Ahmednagar Mandi"],
        "lat": 19.7515,
        "lon": 75.7139
    },
    "Uttar Pradesh": {
        "mandis": ["Agra Mandi", "Lucknow Mandi", "Kanpur Mandi", "Varanasi Mandi"],
        "lat": 26.8467,
        "lon": 80.9462
    },
    "Rajasthan": {
        "mandis": ["Kota Mandi", "Jaipur Mandi", "Sri Ganganagar Mandi", "Bikaner Mandi"],
        "lat": 27.0238,
        "lon": 74.2179
    },
    "Gujarat": {
        "mandis": ["Rajkot APMC", "Gondal Mandi", "Unjha APMC", "Surat Mandi"],
        "lat": 22.2587,
        "lon": 71.1924
    },
    "Karnataka": {
        "mandis": ["Kolar APMC", "Hubballi Mandi", "Mysuru APMC", "Belagavi Mandi"],
        "lat": 15.3173,
        "lon": 75.7139
    }
}

# Model Settings
SUPPORTED_MODELS = [
    "Linear Regression",
    "Random Forest Regressor",
    "HistGradientBoostingRegressor"
]

FORECAST_HORIZONS = {
    "Next 1 Day": 1,
    "Next 7 Days": 7,
    "Next 14 Days": 14,
    "Next 30 Days": 30,
    "Next 60 Days": 60,
    "Next 90 Days": 90
}

DEFAULT_CURRENCY = "₹"
DEFAULT_WEIGHT_UNIT = "Quintal (100 kg)"
