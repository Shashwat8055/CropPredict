"""
CropPricePredict - Dataset Schema Validation Utility
Checks uploaded or ingested CSV files against required, recommended, and optional column schemas.
"""
import pandas as pd
from typing import Dict, Any, List, Tuple

REQUIRED_COLUMNS = ["date", "crop", "price"]
RECOMMENDED_COLUMNS = ["state", "market", "district", "season"]
OPTIONAL_COLUMNS = ["rainfall", "temperature", "humidity", "arrival", "production"]

COLUMN_ALIASES = {
    "commodity": "crop",
    "crop_name": "crop",
    "modal_price": "price",
    "price_per_qtl": "price",
    "arrivals_quintal": "arrival",
    "arrivals": "arrival",
    "mandi": "market",
    "temperature_c": "temperature",
    "rainfall_mm": "rainfall",
    "humidity_pct": "humidity"
}

def standardize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes column names using standard aliases.
    """
    df_clean = df.copy()
    df_clean.columns = [str(c).strip().lower() for c in df_clean.columns]
    
    rename_dict = {}
    for col in df_clean.columns:
        if col in COLUMN_ALIASES:
            rename_dict[col] = COLUMN_ALIASES[col]
            
    return df_clean.rename(columns=rename_dict)

def validate_dataset_schema(df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates dataset against required, recommended, and optional column schemas.
    Returns (is_valid, validation_report).
    """
    df_norm = standardize_dataframe_columns(df)
    present_cols = set(df_norm.columns)
    
    missing_required = [col for col in REQUIRED_COLUMNS if col not in present_cols]
    missing_recommended = [col for col in RECOMMENDED_COLUMNS if col not in present_cols]
    missing_optional = [col for col in OPTIONAL_COLUMNS if col not in present_cols]
    
    found_required = [col for col in REQUIRED_COLUMNS if col in present_cols]
    found_recommended = [col for col in RECOMMENDED_COLUMNS if col in present_cols]
    found_optional = [col for col in OPTIONAL_COLUMNS if col in present_cols]

    is_valid = len(missing_required) == 0
    
    total_rows = len(df)
    duplicate_count = df.duplicated().sum()
    null_counts = df.isnull().sum().to_dict()

    report = {
        "is_valid": is_valid,
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "found_required": found_required,
        "missing_required": missing_required,
        "found_recommended": found_recommended,
        "missing_recommended": missing_recommended,
        "found_optional": found_optional,
        "missing_optional": missing_optional,
        "duplicate_count": duplicate_count,
        "null_counts": null_counts,
        "status_message": (
            "Valid dataset with all required fields." if is_valid 
            else f"Missing required columns: {', '.join(missing_required)}"
        )
    }

    return is_valid, report
