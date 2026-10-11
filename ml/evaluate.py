"""
CropPricePredict - Model Evaluation & Comparison Metrics
Calculates MAE, RMSE, R², MAPE, and directional accuracy for regression model evaluation.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def evaluate_regression_model(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, float]:
    """
    Calculates MAE, RMSE, R², and MAPE regression performance metrics.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[mask]
    y_pred = y_pred[mask]

    if len(y_true) == 0:
        return {"mae": 0.0, "rmse": 0.0, "r2": 0.0, "mape": 0.0}

    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))

    nonzero = y_true != 0
    if np.any(nonzero):
        mape = float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100.0)
    else:
        mape = 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
        "mape": round(mape, 2)
    }

def format_model_comparison_table(metrics_dict: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """
    Formats dictionary of model metrics into a comparison DataFrame.
    """
    rows = []
    for model_name, metrics in metrics_dict.items():
        rows.append({
            "Model": model_name,
            "MAE (₹)": metrics.get("mae", 0.0),
            "RMSE (₹)": metrics.get("rmse", 0.0),
            "R² Score": metrics.get("r2", 0.0),
            "MAPE (%)": metrics.get("mape", 0.0)
        })
    df_comp = pd.DataFrame(rows)
    return df_comp.sort_values(by="RMSE (₹)", ascending=True).reset_index(drop=True)
