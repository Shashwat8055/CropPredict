"""
CropPricePredict - Multi-Horizon Price Forecasting Engine
Executes multi-step recursive price forecasting (1 to 90 days) with confidence intervals.
"""
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from config import MODELS_DIR, CROPS_METADATA
from ml.preprocessing import preprocess_crop_dataset
from ml.feature_engineering import create_time_series_features

def predict_future_crop_prices(
    df_raw: pd.DataFrame,
    commodity: str = "Wheat",
    market: str = "Karnal Mandi",
    horizon_days: int = 30,
    model_obj: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generates multi-horizon daily price predictions using the trained machine learning model.
    """
    # Load model and metadata from disk if not provided
    if model_obj is None or metadata is None:
        model_path = MODELS_DIR / "price_model.joblib"
        meta_path = MODELS_DIR / "model_metadata.joblib"
        
        if not model_path.exists() or not meta_path.exists():
            raise FileNotFoundError("No trained machine learning model found. Please train the model first.")

        model_obj = joblib.load(model_path)
        metadata = joblib.load(meta_path)

    feat_cols = metadata["feature_cols"]
    residual_std = metadata.get("residual_std", 35.0)

    # Clean and preprocess historical data
    df_clean, _ = preprocess_crop_dataset(df_raw, commodity=commodity, market=market)
    if df_clean.empty:
        df_clean, _ = preprocess_crop_dataset(df_raw, commodity=commodity)

    if df_clean.empty:
        raise ValueError(f"No historical records found for commodity '{commodity}'.")

    df_feat, _ = create_time_series_features(df_clean, target_col="price")
    if df_feat.empty:
        raise ValueError("Insufficient data to build historical time-series features.")

    last_date = df_feat["date"].max() if "date" in df_feat.columns else datetime.now()
    current_price = float(df_feat["price"].iloc[-1])

    sim_series = list(df_feat["price"].values)
    forecast_rows = []

    for step in range(1, horizon_days + 1):
        future_date = last_date + timedelta(days=step)
        month = future_date.month

        lag_1 = sim_series[-1]
        lag_2 = sim_series[-2] if len(sim_series) >= 2 else lag_1
        lag_3 = sim_series[-3] if len(sim_series) >= 3 else lag_2
        lag_7 = sim_series[-7] if len(sim_series) >= 7 else lag_1
        lag_14 = sim_series[-14] if len(sim_series) >= 14 else lag_7
        lag_21 = sim_series[-21] if len(sim_series) >= 21 else lag_14
        lag_30 = sim_series[-30] if len(sim_series) >= 30 else lag_21

        ma_7 = float(np.mean(sim_series[-7:]))
        ma_14 = float(np.mean(sim_series[-14:]))
        ma_30 = float(np.mean(sim_series[-30:]))

        ema_7 = float(pd.Series(sim_series).ewm(span=7).mean().iloc[-1])
        ema_21 = float(pd.Series(sim_series).ewm(span=21).mean().iloc[-1])

        vol_7 = float(np.std(sim_series[-7:])) if len(sim_series) >= 7 else 10.0
        vol_30 = float(np.std(sim_series[-30:])) if len(sim_series) >= 30 else 20.0

        momentum_7 = float((lag_1 - lag_7) / (lag_7 + 1e-5))
        momentum_30 = float((lag_1 - lag_30) / (lag_30 + 1e-5))
        price_change_1d = float(lag_1 - lag_2)
        price_spread = float(lag_1 * 0.08)

        sin_month = np.sin(2 * np.pi * month / 12.0)
        cos_month = np.cos(2 * np.pi * month / 12.0)

        row_dict = {
            "lag_1": lag_1, "lag_2": lag_2, "lag_3": lag_3, "lag_7": lag_7,
            "lag_14": lag_14, "lag_21": lag_21, "lag_30": lag_30,
            "ma_7": ma_7, "ma_14": ma_14, "ma_30": ma_30,
            "ema_7": ema_7, "ema_21": ema_21,
            "vol_7": vol_7, "vol_30": vol_30,
            "momentum_7": momentum_7, "momentum_30": momentum_30,
            "price_change_1d": price_change_1d, "price_spread": price_spread,
            "arrival": 1200.0, "arrival_lag_1": 1200.0, "arrival_ma_7": 1200.0,
            "sin_month": sin_month, "cos_month": cos_month,
            "rainfall": 2.0, "temperature": 25.0, "humidity": 65.0
        }

        # Align with model feature order
        feat_vector = pd.DataFrame([row_dict])
        for c in feat_cols:
            if c not in feat_vector.columns:
                feat_vector[c] = 0.0
        feat_vector = feat_vector[feat_cols]

        pred_val = float(model_obj.predict(feat_vector)[0])
        pred_val = round(max(current_price * 0.4, pred_val), 2)

        uncertainty = 1.645 * residual_std * np.sqrt(step)
        lower_b = round(max(pred_val * 0.5, pred_val - uncertainty), 2)
        upper_b = round(pred_val + uncertainty, 2)

        forecast_rows.append({
            "date": future_date,
            "forecast_day": step,
            "predicted_price": pred_val,
            "lower_bound_90": lower_b,
            "upper_bound_90": upper_b
        })

        sim_series.append(pred_val)

    forecast_df = pd.DataFrame(forecast_rows)
    final_pred = forecast_df["predicted_price"].iloc[-1]
    pct_change = ((final_pred - current_price) / current_price) * 100.0

    if pct_change > 1.5:
        trend = "Likely Increasing"
    elif pct_change < -1.5:
        trend = "Likely Decreasing"
    else:
        trend = "Stable"

    summary = {
        "current_price": current_price,
        "predicted_price": final_pred,
        "price_change": round(final_pred - current_price, 2),
        "pct_change": round(pct_change, 2),
        "trend": trend,
        "horizon_days": horizon_days,
        "model_used": metadata.get("best_model_name", "Random Forest Regressor")
    }

    return forecast_df, summary
