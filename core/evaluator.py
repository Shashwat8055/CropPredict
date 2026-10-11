"""
CropPricePredict - Model Evaluator & Metrics Suite
Calculates R², RMSE, MAE, MAPE, Directional Accuracy, and residual diagnostics.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes standard regression & financial directional metrics.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    # Filter any NaNs or infinite values if present
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[mask]
    y_pred = y_pred[mask]

    if len(y_true) == 0:
        return {
            "r2": 0.0,
            "rmse": 0.0,
            "mae": 0.0,
            "mape": 0.0,
            "directional_accuracy": 0.0
        }

    r2 = float(r2_score(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_true, y_pred))

    # MAPE (%)
    nonzero = y_true != 0
    if np.any(nonzero):
        mape = float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100.0)
    else:
        mape = 0.0

    # Directional Accuracy (% of correct day-over-day movement direction)
    if len(y_true) > 1:
        diff_true = np.diff(y_true)
        diff_pred = np.diff(y_pred)
        correct_dir = np.sign(diff_true) == np.sign(diff_pred)
        directional_acc = float(np.mean(correct_dir) * 100.0)
    else:
        directional_acc = 100.0

    return {
        "r2": round(r2, 4),
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "mape": round(mape, 2),
        "directional_accuracy": round(directional_acc, 2)
    }

def compute_residuals(y_true: np.ndarray, y_pred: np.ndarray) -> pd.DataFrame:
    """Returns residual analysis dataframe."""
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    residuals = y_true - y_pred
    pct_error = (residuals / (y_true + 1e-5)) * 100.0

    return pd.DataFrame({
        "actual": y_true,
        "predicted": y_pred,
        "residual": residuals,
        "pct_error": pct_error
    })
