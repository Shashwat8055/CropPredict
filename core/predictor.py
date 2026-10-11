"""
CropPricePredict - Multi-Horizon Forecasting Engine
Handles recursive multi-step forecasting (1 to 90 days), uncertainty intervals, and confidence bands.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from config import CROPS_METADATA, STATE_MANDIS
from core.feature_engineering import build_crop_features
from core.models import CropPriceModel, EnsembleStackingModel

class MultiHorizonPredictor:
    """
    Recursive Time-Series Predictor with Uncertainty Intervals.
    """
    def __init__(self, model_instance, feature_names: List[str], std_residual: float = 45.0):
        self.model = model_instance
        self.feature_names = feature_names
        self.std_residual = max(15.0, std_residual)

    def forecast(
        self,
        historical_df: pd.DataFrame,
        horizon_days: int = 30,
        commodity: str = "Wheat",
        market: str = "Ludhiana Mandi",
        state: str = "Punjab",
        scenario_adjustments: Optional[Dict[str, float]] = None
    ) -> pd.DataFrame:
        """
        Generates daily forecasts for the next `horizon_days` ahead.
        scenario_adjustments can contain:
            - 'rainfall_pct_change': e.g. -30 for drought, +50 for excess
            - 'arrival_pct_change': e.g. +25 for bumper crop
            - 'fuel_pct_change': e.g. +10 for diesel price rise
        """
        scenario = scenario_adjustments or {}
        rainfall_mult = 1.0 + (scenario.get("rainfall_pct_change", 0.0) / 100.0)
        arrival_mult = 1.0 + (scenario.get("arrival_pct_change", 0.0) / 100.0)
        fuel_mult = 1.0 + (scenario.get("fuel_pct_change", 0.0) / 100.0)

        # Work on recent historical window
        df_work = historical_df.copy()
        if "date" in df_work.columns:
            df_work["date"] = pd.to_datetime(df_work["date"])
            df_work = df_work.sort_values("date").reset_index(drop=True)

        if df_work.empty:
            raise ValueError("Historical dataframe is empty for prediction!")

        last_date = df_work["date"].max()
        meta = CROPS_METADATA.get(commodity, {})
        peak_harvest = meta.get("peak_harvest_months", [])
        lean_months = meta.get("lean_months", [])

        forecast_records = []
        sim_df = df_work.copy()

        # Forecast step by step
        for step in range(1, horizon_days + 1):
            future_date = last_date + timedelta(days=step)
            # Skip Sundays if desired, or include continuous calendar
            month = future_date.month
            day_of_year = future_date.dayofyear
            day_of_week = future_date.weekday()
            quarter = (month - 1) // 3 + 1

            # Extract recent prices from simulated series
            recent_prices = sim_df["modal_price"].values
            n_prices = len(recent_prices)

            lag_1 = recent_prices[-1]
            lag_2 = recent_prices[-2] if n_prices >= 2 else lag_1
            lag_3 = recent_prices[-3] if n_prices >= 3 else lag_2
            lag_7 = recent_prices[-7] if n_prices >= 7 else lag_1
            lag_14 = recent_prices[-14] if n_prices >= 14 else lag_7
            lag_21 = recent_prices[-21] if n_prices >= 21 else lag_14
            lag_30 = recent_prices[-30] if n_prices >= 30 else lag_21

            ma_7 = float(np.mean(recent_prices[-7:]))
            ma_14 = float(np.mean(recent_prices[-14:]))
            ma_30 = float(np.mean(recent_prices[-30:]))
            ema_7 = float(pd.Series(recent_prices).ewm(span=7).mean().iloc[-1])
            ema_21 = float(pd.Series(recent_prices).ewm(span=21).mean().iloc[-1])

            vol_7 = float(np.std(recent_prices[-7:])) if n_prices >= 7 else 10.0
            vol_30 = float(np.std(recent_prices[-30:])) if n_prices >= 30 else 20.0

            momentum_7 = float((lag_1 - lag_7) / (lag_7 + 1e-5))
            momentum_30 = float((lag_1 - lag_30) / (lag_30 + 1e-5))
            price_spread = float(lag_1 * 0.08)

            # Estimated arrival and weather for future step
            last_arrival = sim_df["arrivals_quintal"].iloc[-1] if "arrivals_quintal" in sim_df.columns else 1200.0
            est_arrival = max(50.0, float(last_arrival * arrival_mult))
            arrival_lag_1 = last_arrival
            arrival_ma_7 = float(sim_df["arrivals_quintal"].tail(7).mean()) if "arrivals_quintal" in sim_df.columns else 1200.0
            arrival_ratio = est_arrival / (arrival_ma_7 + 1.0)

            # Cyclical seasonality
            sin_month = np.sin(2 * np.pi * month / 12.0)
            cos_month = np.cos(2 * np.pi * month / 12.0)
            sin_doy = np.sin(2 * np.pi * day_of_year / 365.25)
            cos_doy = np.cos(2 * np.pi * day_of_year / 365.25)

            is_peak = 1 if month in peak_harvest else 0
            is_lean = 1 if month in lean_months else 0

            temp_c = 28.0 + 10.0 * np.sin(2 * np.pi * (day_of_year - 105) / 365.0)
            rain_mm = (12.0 if 6 <= month <= 9 else 1.5) * rainfall_mult
            fuel_idx = (sim_df["fuel_index"].iloc[-1] if "fuel_index" in sim_df.columns else 110.0) * fuel_mult

            # Construct feature vector dictionary
            feat_dict = {
                "lag_1": lag_1, "lag_2": lag_2, "lag_3": lag_3, "lag_7": lag_7,
                "lag_14": lag_14, "lag_21": lag_21, "lag_30": lag_30,
                "ma_7": ma_7, "ma_14": ma_14, "ma_30": ma_30,
                "ema_7": ema_7, "ema_21": ema_21,
                "vol_7": vol_7, "vol_30": vol_30,
                "momentum_7": momentum_7, "momentum_30": momentum_30,
                "price_spread": price_spread,
                "arrivals_quintal": est_arrival, "arrival_lag_1": arrival_lag_1,
                "arrival_ma_7": arrival_ma_7, "arrival_ratio": arrival_ratio,
                "sin_month": sin_month, "cos_month": cos_month,
                "sin_doy": sin_doy, "cos_doy": cos_doy,
                "day_of_week": day_of_week, "quarter": quarter,
                "is_peak_harvest": is_peak, "is_lean_season": is_lean,
                "temperature_c": temp_c, "rainfall_mm": rain_mm,
                "rainfall_7d_sum": rain_mm * 4.0, "fuel_index": fuel_idx
            }

            feat_df = pd.DataFrame([feat_dict])
            # Ensure columns order matches model features
            for f in self.feature_names:
                if f not in feat_df.columns:
                    feat_df[f] = 0.0

            feat_df = feat_df[self.feature_names]

            # Predict next step
            pred_price = float(self.model.predict(feat_df)[0])
            pred_price = round(max(meta.get("base_price", 1000.0) * 0.4, pred_price), 2)

            # Confidence interval grows with sqrt(horizon step)
            uncertainty = 1.645 * self.std_residual * np.sqrt(step)
            lower_bound = round(max(pred_price * 0.5, pred_price - uncertainty), 2)
            upper_bound = round(pred_price + uncertainty, 2)

            forecast_records.append({
                "date": future_date,
                "forecast_day": step,
                "predicted_price": pred_price,
                "lower_bound_90": lower_bound,
                "upper_bound_90": upper_bound,
                "commodity": commodity,
                "market": market,
                "state": state
            })

            # Append predicted row into sim_df for next recursive step
            new_sim_row = pd.DataFrame([{
                "date": future_date,
                "modal_price": pred_price,
                "arrivals_quintal": est_arrival,
                "min_price": pred_price * 0.95,
                "max_price": pred_price * 1.05,
                "temperature_c": temp_c,
                "rainfall_mm": rain_mm,
                "fuel_index": fuel_idx
            }])
            sim_df = pd.concat([sim_df, new_sim_row], ignore_index=True)

        return pd.DataFrame(forecast_records)
