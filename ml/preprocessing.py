"""
CropPricePredict - Machine Learning Preprocessing Pipeline
Handles data cleaning, missing value imputation, chronological sorting, and feature preprocessing.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List, Optional
from utils.validation import standardize_dataframe_columns

def preprocess_crop_dataset(
    df: pd.DataFrame,
    commodity: Optional[str] = None,
    market: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans, standardizes, and preprocesses raw crop market dataset.
    
    Steps:
    1. Standardize column names (mapping 'modal_price' -> 'price', 'commodity' -> 'crop', etc.)
    2. Remove duplicate rows.
    3. Filter out non-positive prices or invalid records.
    4. Parse dates chronologically.
    5. Handle missing values in numerical and categorical features.
    6. Extract temporal date features (year, month, quarter, day, day_of_week).
    """
    df_clean = standardize_dataframe_columns(df)
    initial_len = len(df_clean)

    # 1. Remove duplicates
    df_clean = df_clean.drop_duplicates().reset_index(drop=True)
    dedup_count = initial_len - len(df_clean)

    # 2. Filter target crop / market if specified
    if commodity and "crop" in df_clean.columns:
        df_clean = df_clean[df_clean["crop"].astype(str).str.lower() == commodity.lower()]
    if market and "market" in df_clean.columns and market != "All Mandis":
        df_clean = df_clean[df_clean["market"].astype(str).str.lower() == market.lower()]

    if df_clean.empty:
        return pd.DataFrame(), {
            "initial_count": initial_len,
            "final_count": 0,
            "dedup_count": dedup_count,
            "removed_invalid": 0
        }

    # 3. Parse and sort by date chronologically
    if "date" in df_clean.columns:
        df_clean["date"] = pd.to_datetime(df_clean["date"], errors="coerce")
        df_clean = df_clean.dropna(subset=["date"])
        df_clean = df_clean.sort_values(by="date").reset_index(drop=True)

    # 4. Clean invalid numerical values (e.g. price <= 0)
    invalid_mask = df_clean["price"] <= 0 if "price" in df_clean.columns else pd.Series(False, index=df_clean.index)
    removed_invalid = invalid_mask.sum()
    df_clean = df_clean[~invalid_mask].reset_index(drop=True)

    # 5. Handle missing values
    num_cols = df_clean.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if df_clean[col].isnull().any():
            median_val = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_val if pd.notnull(median_val) else 0.0)

    cat_cols = df_clean.select_dtypes(include=["object", "category"]).columns
    for col in cat_cols:
        if df_clean[col].isnull().any():
            df_clean[col] = df_clean[col].fillna("Unknown")

    # 6. Temporal date feature extraction
    if "date" in df_clean.columns:
        dt = df_clean["date"].dt
        df_clean["year"] = dt.year
        df_clean["month"] = dt.month
        df_clean["quarter"] = dt.quarter
        df_clean["day"] = dt.day
        df_clean["day_of_week"] = dt.dayofweek

    stats = {
        "initial_count": initial_len,
        "final_count": len(df_clean),
        "dedup_count": dedup_count,
        "removed_invalid": removed_invalid
    }

    return df_clean, stats
