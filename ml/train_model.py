"""
CropPricePredict - Machine Learning Training Pipeline for Mandi Price Forecasting
B.Tech Capstone Project - Department of Computer Science & Engineering

Implements Supervised Time-Series Regression with Chronological Validation (80/20 split):
Features Engineered:
- Autoregressive Lags (t-1, t-2, t-3, t-7, t-14, t-21, t-30)
- Rolling Moving Averages (7-day, 14-day, 30-day window)
- Rolling Volatility (7-day standard deviation) & 30-day Price Momentum
- Cyclical Seasonal Encoding (Sine & Cosine transforms of calendar month)

Algorithms Evaluated:
1. Ordinary Least Squares (Linear Regression)
2. L2 Regularized Linear Model (Ridge Regression)
3. Random Forest Regressor (Ensemble Bagging)
4. HistGradientBoosting Regressor (Ensemble Boosting)
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import time

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from config import MODELS_DIR
from ml.preprocessing import preprocess_crop_dataset
from ml.feature_engineering import create_time_series_features
from ml.evaluate import evaluate_regression_model, format_model_comparison_table

def train_and_evaluate_models(
    df_raw: pd.DataFrame,
    commodity: Optional[str] = None,
    market: Optional[str] = None,
    target_col: str = "price",
    train_ratio: float = 0.80,
    rf_n_estimators: int = 50,
    rf_max_depth: int = 12,
    hgb_max_iter: int = 80,
    hgb_learning_rate: float = 0.08
) -> Tuple[Any, Dict[str, Any], pd.DataFrame]:
    """
    Trains multiple regression models using chronological time-series validation.
    
    Returns:
        (best_model_obj, best_metrics_and_meta, comparison_dataframe)
    """
    # 1. Preprocess raw data
    df_clean, stats = preprocess_crop_dataset(df_raw, commodity=commodity, market=market)
    if df_clean.empty:
        raise ValueError("Cleaned dataset is empty. Check filtering criteria or database records.")

    # 2. Build time-series lag and seasonal features
    df_feat, feat_cols = create_time_series_features(df_clean, target_col=target_col)
    if df_feat.empty or len(df_feat) < 15:
        raise ValueError("Insufficient chronological records to construct lag features (minimum 15 rows needed).")

    X = df_feat[feat_cols]
    y = df_feat[target_col]

    # 3. Chronological Time-based Train / Test Split (no future data leakage)
    split_idx = int(len(X) * train_ratio)
    split_idx = max(10, min(split_idx, len(X) - 5))
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    models_to_train = {
        "Linear Regression": Pipeline([("scaler", StandardScaler()), ("reg", LinearRegression())]),
        "Ridge Regression (L2)": Pipeline([("scaler", StandardScaler()), ("ridge", Ridge(alpha=10.0))]),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=rf_n_estimators, max_depth=rf_max_depth, random_state=42, n_jobs=-1),
        "HistGradientBoosting Regressor": HistGradientBoostingRegressor(max_iter=hgb_max_iter, learning_rate=hgb_learning_rate, random_state=42)
    }

    eval_results = {}
    fitted_models = {}
    model_predictions = {}
    fit_times = {}

    for name, model_instance in models_to_train.items():
        t0 = time.time()
        model_instance.fit(X_train, y_train)
        fit_times[name] = round(time.time() - t0, 3)

        y_pred = model_instance.predict(X_test)
        metrics = evaluate_regression_model(y_test.values, y_pred)
        metrics["fit_time_sec"] = fit_times[name]
        eval_results[name] = metrics
        fitted_models[name] = model_instance
        model_predictions[name] = y_pred

    comp_df = format_model_comparison_table(eval_results)

    # Best model selection based on lowest RMSE
    best_model_name = comp_df.iloc[0]["Model"]
    best_model = fitted_models[best_model_name]
    best_metrics = eval_results[best_model_name]
    best_pred = model_predictions[best_model_name]

    # Subsample test set for fast, crisp scatter plotting in UI
    max_plot_pts = min(300, len(y_test))
    step = max(1, len(y_test) // max_plot_pts)
    plot_actuals = [float(val) for val in y_test.values[::step]]
    plot_preds = [float(val) for val in best_pred[::step]]
    plot_residuals = [float(a - p) for a, p in zip(plot_actuals, plot_preds)]

    # Retrain best model on complete dataset for production forecasting
    best_model.fit(X, y)

    # Feature Importance computation
    feature_importances = {}
    if hasattr(best_model, "feature_importances_"):
        for f, imp in zip(feat_cols, best_model.feature_importances_):
            feature_importances[f] = float(imp)
    elif best_model_name in ["Linear Regression", "Ridge Regression (L2)"]:
        step_name = "reg" if "reg" in best_model.named_steps else "ridge"
        reg_coefs = np.abs(best_model.named_steps[step_name].coef_)
        total = np.sum(reg_coefs) + 1e-8
        for f, coef in zip(feat_cols, reg_coefs):
            feature_importances[f] = float(coef / total)

    metadata = {
        "best_model_name": best_model_name,
        "feature_cols": feat_cols,
        "train_records": len(X_train),
        "test_records": len(X_test),
        "total_records": len(X),
        "train_ratio": train_ratio,
        "metrics": best_metrics,
        "all_model_metrics": eval_results,
        "feature_importances": feature_importances,
        "target_col": target_col,
        "plot_actuals": plot_actuals,
        "plot_preds": plot_preds,
        "plot_residuals": plot_residuals,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Save trained model artifact
    save_path = MODELS_DIR / "price_model.joblib"
    meta_path = MODELS_DIR / "model_metadata.joblib"
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(best_model, save_path)
    joblib.dump(metadata, meta_path)

    return best_model, metadata, comp_df
