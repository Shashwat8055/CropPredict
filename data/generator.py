"""
CropPricePredict - Agricultural Market Data Generator
Generates realistic historical and live-streaming multi-crop market data.
"""
import math
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config import CROPS_METADATA, STATE_MANDIS

def generate_crop_market_data(
    start_date: str = "2023-01-01",
    end_date: str = "2026-08-11",
    crops=None,
    states=None,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates realistic daily Mandi records with price, arrival volume, weather, and macro indicators.
    """
    np.random.seed(random_seed)
    random.seed(random_seed)

    if crops is None:
        crops = list(CROPS_METADATA.keys())
    if states is None:
        states = list(STATE_MANDIS.keys())

    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    records = []

    # Baseline diesel/transport index starting in 2023 at 100 with modest inflation trend
    total_days = len(date_range)
    diesel_trend = np.linspace(95.0, 118.0, total_days) + np.random.normal(0, 0.5, total_days)

    for state in states:
        mandi_list = STATE_MANDIS[state]["mandis"]
        lat = STATE_MANDIS[state]["lat"]
        lon = STATE_MANDIS[state]["lon"]

        for mandi in mandi_list:
            # Mandi specific pricing adjustment factor (e.g. proximity to metro or transport hub)
            mandi_factor = 1.0 + np.random.uniform(-0.04, 0.04)

            for crop in crops:
                meta = CROPS_METADATA[crop]
                base_price = meta["base_price"] * mandi_factor
                price_std = meta["price_std"]
                harvest_months = meta["peak_harvest_months"]
                lean_months = meta["lean_months"]

                # Long term multi-year inflation trend (~4.5% annual)
                annual_inflation_rate = 0.045

                for idx, dt in enumerate(date_range):
                    # Skip some weekend days randomly to simulate mandi market days
                    if dt.weekday() == 6:  # Sunday closed for most mandis
                        continue

                    year_offset = (dt - date_range[0]).days / 365.25
                    inflation_mult = (1.0 + annual_inflation_rate) ** year_offset

                    month = dt.month
                    day_of_year = dt.dayofyear

                    # 1. Seasonal Harvest & Lean cycle
                    # Peak harvest = High arrival, lower modal price (-10% to -25%)
                    # Lean season = Low arrival, higher modal price (+10% to +30%)
                    if month in harvest_months:
                        season_price_mult = 0.88 + np.random.uniform(-0.05, 0.03)
                        arrival_base = 2500 + np.random.uniform(500, 2500)
                    elif month in lean_months:
                        season_price_mult = 1.14 + np.random.uniform(-0.02, 0.08)
                        arrival_base = 600 + np.random.uniform(100, 600)
                    else:
                        season_price_mult = 1.0 + np.random.uniform(-0.03, 0.03)
                        arrival_base = 1200 + np.random.uniform(300, 900)

                    # 2. Weather simulation (Temperature & Monsoon rainfall)
                    # Temperature peak in May-June (35-42C), lowest in Jan (10-18C)
                    temp_seasonal = 26 + 12 * np.sin(2 * np.pi * (day_of_year - 105) / 365)
                    temperature = round(float(temp_seasonal + np.random.normal(0, 2.0)), 1)

                    # Rainfall peak during Monsoon (June to Sept)
                    if 6 <= month <= 9:
                        rainfall = max(0.0, round(float(np.random.exponential(8.5) if np.random.rand() < 0.45 else 0.0), 1))
                    else:
                        rainfall = max(0.0, round(float(np.random.exponential(1.5) if np.random.rand() < 0.1 else 0.0), 1))

                    # 3. Macro Diesel index
                    fuel_index = round(float(diesel_trend[idx]), 2)
                    fuel_impact = 1.0 + (fuel_index - 100.0) * 0.0015

                    # 4. Festival / Demand Spikes (e.g. October/November Diwali & Wedding season)
                    festival_shock = 1.0
                    if month in [10, 11] and (15 <= dt.day <= 30):
                        festival_shock = 1.04 + np.random.uniform(0, 0.03)

                    # 5. Weather Shock (Excess rain damages perishable vegetables like Tomato/Onion)
                    weather_shock = 1.0
                    if crop in ["Tomato", "Onion", "Potato"] and rainfall > 25.0:
                        weather_shock = 1.08 + (rainfall / 100.0) * 0.12

                    # Calculate modal price
                    modal_price = (
                        base_price 
                        * inflation_mult 
                        * season_price_mult 
                        * fuel_impact 
                        * festival_shock 
                        * weather_shock
                        + np.random.normal(0, price_std * 0.35)
                    )
                    modal_price = max(base_price * 0.4, modal_price)
                    modal_price = round(float(modal_price), 2)

                    # Min and Max price spread
                    spread = modal_price * np.random.uniform(0.04, 0.12)
                    min_price = round(float(modal_price - spread * 0.5), 2)
                    max_price = round(float(modal_price + spread * 0.5), 2)

                    # Arrival quantity (Tonnes / Quintals) inversely correlated with price spikes
                    arrival_qty = arrival_base * (1.0 / (season_price_mult ** 0.5)) + np.random.normal(0, 100)
                    arrival_qty = max(50.0, round(float(arrival_qty), 1))

                    records.append({
                        "date": dt.strftime("%Y-%m-%d"),
                        "state": state,
                        "market": mandi,
                        "commodity": crop,
                        "category": meta["category"],
                        "arrivals_quintal": arrival_qty,
                        "min_price": min_price,
                        "max_price": max_price,
                        "modal_price": modal_price,
                        "temperature_c": temperature,
                        "rainfall_mm": rainfall,
                        "fuel_index": fuel_index,
                        "latitude": lat,
                        "longitude": lon
                    })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["commodity", "state", "market", "date"]).reset_index(drop=True)
    return df

def generate_live_ticks(
    df_existing: pd.DataFrame,
    days_ahead: int = 1,
    commodity: str = "Wheat",
    state: str = "Punjab",
    market: str = "Ludhiana Mandi"
) -> pd.DataFrame:
    """
    Generates live recent/streaming tick data appending to existing historical series.
    """
    sub = df_existing[(df_existing["commodity"] == commodity) & (df_existing["market"] == market)]
    if sub.empty:
        last_date = datetime.now() - timedelta(days=days_ahead)
        last_price = CROPS_METADATA.get(commodity, {}).get("base_price", 2200.0)
    else:
        last_date = pd.to_datetime(sub["date"].max())
        last_price = sub["modal_price"].iloc[-1]

    new_rows = []
    curr_date = last_date
    curr_price = last_price

    for i in range(1, days_ahead + 1):
        curr_date = curr_date + timedelta(days=1)
        # Random daily walk with mean reversion
        drift = (CROPS_METADATA.get(commodity, {}).get("base_price", 2200.0) - curr_price) * 0.05
        daily_ret = np.random.normal(0, 0.015) + (drift / curr_price)
        curr_price = round(float(curr_price * (1.0 + daily_ret)), 2)
        spread = curr_price * np.random.uniform(0.04, 0.08)

        new_rows.append({
            "date": curr_date.strftime("%Y-%m-%d"),
            "state": state,
            "market": market,
            "commodity": commodity,
            "category": CROPS_METADATA.get(commodity, {}).get("category", "Agricultural Produce"),
            "arrivals_quintal": round(float(max(100.0, np.random.normal(1200, 300))), 1),
            "min_price": round(float(curr_price - spread * 0.5), 2),
            "max_price": round(float(curr_price + spread * 0.5), 2),
            "modal_price": curr_price,
            "temperature_c": round(float(np.random.normal(28, 4)), 1),
            "rainfall_mm": round(float(max(0, np.random.exponential(2.0))), 1),
            "fuel_index": 112.5,
            "latitude": STATE_MANDIS.get(state, {}).get("lat", 28.0),
            "longitude": STATE_MANDIS.get(state, {}).get("lon", 77.0)
        })

    return pd.DataFrame(new_rows)
