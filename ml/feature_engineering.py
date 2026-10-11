"""
CropPricePredict - Feature Engineering Pipeline
Constructs temporal lags, rolling statistics, calendar cyclical encodings, arrival dynamics, and environmental features.
"""
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any, Optional

def create_time_series_features(
    df: pd.DataFrame,
    target_col: str = "price"
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Constructs time-series features (lags, rolling averages, momentum, cyclical month/day)
    for crop market forecasting. Strictly respects chronological ordering (no future leakage).
    """
    if df.empty or target_col not in df.columns:
        return pd.DataFrame(), []

    df_feat = df.copy()
    if "date" in df_feat.columns:
        df_feat["date"] = pd.to_datetime(df_feat["date"])
        df_feat = df_feat.sort_values("date").reset_index(drop=True)

    # 1. Price Lags (Historical values only)
    for lag in [1, 2, 3, 7, 14, 21, 30]:
        df_feat[f"lag_{lag}"] = df_feat[target_col].shift(lag)

    # 2. Moving Averages & Exponential Moving Averages
    df_feat["ma_7"] = df_feat[target_col].rolling(window=7, min_periods=1).mean()
    df_feat["ma_14"] = df_feat[target_col].rolling(window=14, min_periods=1).mean()
    df_feat["ma_30"] = df_feat[target_col].rolling(window=30, min_periods=1).mean()

    df_feat["ema_7"] = df_feat[target_col].ewm(span=7, adjust=False).mean()
    df_feat["ema_21"] = df_feat[target_col].ewm(span=21, adjust=False).mean()

    # 3. Rolling Volatility (Standard Deviation)
    df_feat["vol_7"] = df_feat[target_col].rolling(window=7, min_periods=2).std().fillna(0.0)
    df_feat["vol_30"] = df_feat[target_col].rolling(window=30, min_periods=2).std().fillna(0.0)

    # 4. Momentum & Percentage Price Change
    df_feat["momentum_7"] = (df_feat[target_col] - df_feat["lag_7"]) / (df_feat["lag_7"] + 1e-5)
    df_feat["momentum_30"] = (df_feat[target_col] - df_feat["lag_30"]) / (df_feat["lag_30"] + 1e-5)
    df_feat["price_change_1d"] = df_feat[target_col] - df_feat["lag_1"]

    # 5. Price Spread (Max Price - Min Price) if available
    if "max_price" in df_feat.columns and "min_price" in df_feat.columns:
        df_feat["price_spread"] = df_feat["max_price"] - df_feat["min_price"]
    else:
        df_feat["price_spread"] = df_feat[target_col] * 0.08

    # 6. Market Arrivals Dynamics
    if "arrival" in df_feat.columns:
        df_feat["arrival_lag_1"] = df_feat["arrival"].shift(1)
        df_feat["arrival_ma_7"] = df_feat["arrival"].rolling(window=7, min_periods=1).mean()
    else:
        df_feat["arrival"] = 1000.0
        df_feat["arrival_lag_1"] = 1000.0
        df_feat["arrival_ma_7"] = 1000.0

    # 7. Calendar Cyclical Encodings
    if "month" in df_feat.columns:
        month = df_feat["month"]
    elif "date" in df_feat.columns:
        month = df_feat["date"].dt.month
        df_feat["month"] = month
    else:
        month = pd.Series(1, index=df_feat.index)

    df_feat["sin_month"] = np.sin(2 * np.pi * month / 12.0)
    df_feat["cos_month"] = np.cos(2 * np.pi * month / 12.0)

    # Optional environmental variables
    for env_col in ["rainfall", "temperature", "humidity"]:
        if env_col not in df_feat.columns:
            df_feat[env_col] = 0.0 if env_col == "rainfall" else (25.0 if env_col == "temperature" else 60.0)

    feature_cols = [
        "lag_1", "lag_2", "lag_3", "lag_7", "lag_14", "lag_21", "lag_30",
        "ma_7", "ma_14", "ma_30", "ema_7", "ema_21",
        "vol_7", "vol_30", "momentum_7", "momentum_30", "price_change_1d",
        "price_spread", "arrival", "arrival_lag_1", "arrival_ma_7",
        "sin_month", "cos_month", "rainfall", "temperature", "humidity"
    ]

    # Drop early rows with NaN from lags
    clean_df = df_feat.dropna(subset=feature_cols).reset_index(drop=True)
    return clean_df, feature_cols
