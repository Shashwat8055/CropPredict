"""
CropPricePredict - Machine Learning Training Pipeline
Trains Linear Regression, Random Forest Regressor, and HistGradientBoostingRegressor models
using chronological time-based validation (80/20 split) to select and persist the optimal model.
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, GradientBoostingRegressor
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
    target_col: str = "price"
) -> Tuple[Any, Dict[str, Any], pd.DataFrame]:
    """
    Trains multiple regression models using chronological time-series validation.
    
    Returns:
        (best_model_obj, best_metrics_and_meta, comparison_dataframe)
    """
    # 1. Preprocess raw data
    df_clean, stats = preprocess_crop_dataset(df_raw, commodity=commodity, market=market)
    if df_clean.empty:
        raise ValueError("Cleaned dataset is empty. Check filtering criteria or uploaded data.")

    # 2. Build time-series lag and seasonal features
    df_feat, feat_cols = create_time_series_features(df_clean, target_col=target_col)
    if df_feat.empty or len(df_feat) < 15:
        raise ValueError("Insufficient chronological records to construct lag features (minimum 15 rows needed).")

    X = df_feat[feat_cols]
    y = df_feat[target_col]

    # 3. Chronological Time-based Train / Test Split (80% older -> train, 20% newer -> test)
    split_idx = int(len(X) * 0.80)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    models_to_train = {
        "Linear Regression": Pipeline([("scaler", StandardScaler()), ("reg", LinearRegression())]),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=40, max_depth=10, random_state=42, n_jobs=-1),
        "HistGradientBoostingRegressor": HistGradientBoostingRegressor(max_iter=60, learning_rate=0.08, random_state=42)
    }

    eval_results = {}
    fitted_models = {}

    for name, model_instance in models_to_train.items():
        model_instance.fit(X_train, y_train)
        y_pred = model_instance.predict(X_test)
        metrics = evaluate_regression_model(y_test.values, y_pred)
        eval_results[name] = metrics
        fitted_models[name] = model_instance

    comp_df = format_model_comparison_table(eval_results)

    # Best model selection based on lowest RMSE
    best_model_name = comp_df.iloc[0]["Model"]
    best_model = fitted_models[best_model_name]
    best_metrics = eval_results[best_model_name]

    # Retrain best model on complete dataset for production forecasting
    best_model.fit(X, y)

    # Feature Importance computation if supported
    feature_importances = {}
    if hasattr(best_model, "feature_importances_"):
        for f, imp in zip(feat_cols, best_model.feature_importances_):
            feature_importances[f] = float(imp)
    elif best_model_name == "Linear Regression":
        reg_coefs = np.abs(best_model.named_steps["reg"].coef_)
        total = np.sum(reg_coefs) + 1e-8
        for f, coef in zip(feat_cols, reg_coefs):
            feature_importances[f] = float(coef / total)

    metadata = {
        "best_model_name": best_model_name,
        "feature_cols": feat_cols,
        "train_records": len(X_train),
        "test_records": len(X_test),
        "total_records": len(X),
        "metrics": best_metrics,
        "all_model_metrics": eval_results,
        "feature_importances": feature_importances,
        "target_col": target_col,
        "residual_std": float(np.std(y_test.values - fitted_models[best_model_name].predict(X_test)))
    }

    # Save trained model artifact
    save_path = MODELS_DIR / "price_model.joblib"
    meta_path = MODELS_DIR / "model_metadata.joblib"
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(best_model, save_path)
    joblib.dump(metadata, meta_path)

    return best_model, metadata, comp_df
