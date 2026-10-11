"""
CropPricePredict - Feature Engineering Pipeline
Constructs temporal lags, rolling statistics, calendar cyclical encodings, arrival elasticity, and macro indices.
"""
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any
from config import CROPS_METADATA

def build_crop_features(
    df: pd.DataFrame,
    commodity: str = "Wheat",
    market: str = None,
    include_future_lags: bool = False
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Builds rich feature matrix for a specific crop (and optional market).
    Returns (featured_df, feature_column_names).
    """
    df_crop = df.copy()
    if "date" in df_crop.columns:
        df_crop["date"] = pd.to_datetime(df_crop["date"])
        df_crop = df_crop.sort_values(by="date").reset_index(drop=True)

    if commodity and "commodity" in df_crop.columns:
        df_crop = df_crop[df_crop["commodity"] == commodity]
    
    if market and "market" in df_crop.columns and market != "All Mandis":
        df_crop = df_crop[df_crop["market"] == market]

    if df_crop.empty:
        return pd.DataFrame(), []

    # If multiple mandis exist, group by date taking mean or aggregate
    if df_crop.duplicated(subset=["date"]).any():
        df_crop = df_crop.groupby("date").agg({
            "modal_price": "mean",
            "min_price": "min",
            "max_price": "max",
            "arrivals_quintal": "sum",
            "temperature_c": "mean",
            "rainfall_mm": "mean",
            "fuel_index": "mean",
            "latitude": "first",
            "longitude": "first"
        }).reset_index()

    df_crop = df_crop.sort_values("date").reset_index(drop=True)

    # 1. Price Temporal Lags
    for lag in [1, 2, 3, 7, 14, 21, 30]:
        df_crop[f"lag_{lag}"] = df_crop["modal_price"].shift(lag)

    # 2. Rolling Moving Averages & EMAs
    df_crop["ma_7"] = df_crop["modal_price"].rolling(window=7, min_periods=1).mean()
    df_crop["ma_14"] = df_crop["modal_price"].rolling(window=14, min_periods=1).mean()
    df_crop["ma_30"] = df_crop["modal_price"].rolling(window=30, min_periods=1).mean()
    df_crop["ema_7"] = df_crop["modal_price"].ewm(span=7, adjust=False).mean()
    df_crop["ema_21"] = df_crop["modal_price"].ewm(span=21, adjust=False).mean()

    # 3. Rolling Volatility (Standard Deviation)
    df_crop["vol_7"] = df_crop["modal_price"].rolling(window=7, min_periods=2).std().fillna(0)
    df_crop["vol_30"] = df_crop["modal_price"].rolling(window=30, min_periods=2).std().fillna(0)

    # 4. Price Momentum (% change over 7 and 30 days)
    df_crop["momentum_7"] = (df_crop["modal_price"] - df_crop["lag_7"]) / (df_crop["lag_7"] + 1e-5)
    df_crop["momentum_30"] = (df_crop["modal_price"] - df_crop["lag_30"]) / (df_crop["lag_30"] + 1e-5)

    # 5. Price Spread (High - Low)
    if "max_price" in df_crop.columns and "min_price" in df_crop.columns:
        df_crop["price_spread"] = df_crop["max_price"] - df_crop["min_price"]
    else:
        df_crop["price_spread"] = df_crop["modal_price"] * 0.08

    # 6. Arrival Dynamics & Elasticity
    if "arrivals_quintal" in df_crop.columns:
        df_crop["arrival_lag_1"] = df_crop["arrivals_quintal"].shift(1)
        df_crop["arrival_ma_7"] = df_crop["arrivals_quintal"].rolling(window=7, min_periods=1).mean()
        df_crop["arrival_ratio"] = df_crop["arrivals_quintal"] / (df_crop["arrival_ma_7"] + 1.0)
    else:
        df_crop["arrivals_quintal"] = 1000.0
        df_crop["arrival_lag_1"] = 1000.0
        df_crop["arrival_ma_7"] = 1000.0
        df_crop["arrival_ratio"] = 1.0

    # 7. Calendar & Cyclical Encodings
    dt = df_crop["date"].dt
    df_crop["month"] = dt.month
    df_crop["day_of_week"] = dt.dayofweek
    df_crop["day_of_year"] = dt.dayofyear
    df_crop["quarter"] = dt.quarter

    df_crop["sin_month"] = np.sin(2 * np.pi * df_crop["month"] / 12.0)
    df_crop["cos_month"] = np.cos(2 * np.pi * df_crop["month"] / 12.0)
    df_crop["sin_doy"] = np.sin(2 * np.pi * df_crop["day_of_year"] / 365.25)
    df_crop["cos_doy"] = np.cos(2 * np.pi * df_crop["day_of_year"] / 365.25)

    # 8. Crop-Specific Harvest & Lean Flags
    meta = CROPS_METADATA.get(commodity, {})
    peak_harvest = meta.get("peak_harvest_months", [])
    lean_months = meta.get("lean_months", [])

    df_crop["is_peak_harvest"] = df_crop["month"].isin(peak_harvest).astype(int)
    df_crop["is_lean_season"] = df_crop["month"].isin(lean_months).astype(int)

    # 9. Environmental & Macro Factors
    if "rainfall_mm" in df_crop.columns:
        df_crop["rainfall_7d_sum"] = df_crop["rainfall_mm"].rolling(window=7, min_periods=1).sum()
    else:
        df_crop["rainfall_mm"] = 0.0
        df_crop["rainfall_7d_sum"] = 0.0

    if "temperature_c" not in df_crop.columns:
        df_crop["temperature_c"] = 28.0
    if "fuel_index" not in df_crop.columns:
        df_crop["fuel_index"] = 105.0

    feature_cols = [
        "lag_1", "lag_2", "lag_3", "lag_7", "lag_14", "lag_21", "lag_30",
        "ma_7", "ma_14", "ma_30", "ema_7", "ema_21",
        "vol_7", "vol_30", "momentum_7", "momentum_30", "price_spread",
        "arrivals_quintal", "arrival_lag_1", "arrival_ma_7", "arrival_ratio",
        "sin_month", "cos_month", "sin_doy", "cos_doy", "day_of_week", "quarter",
        "is_peak_harvest", "is_lean_season",
        "temperature_c", "rainfall_mm", "rainfall_7d_sum", "fuel_index"
    ]

    # Drop early rows with NaN from lags if we are training
    clean_df = df_crop.dropna(subset=feature_cols).reset_index(drop=True)
    return clean_df, feature_cols
