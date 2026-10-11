"""
CropPricePredict - Machine Learning Forecasting Models
Implements XGBoost, Random Forest, HistGradientBoosting, Ridge, and Stacking Ensemble.
"""
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb

from config import MODELS_DIR

class CropPriceModel:
    """Base wrapper for Crop Price Prediction Models."""
    def __init__(self, model_name: str, params: Optional[Dict[str, Any]] = None):
        self.model_name = model_name
        self.params = params or {}
        self.feature_names: List[str] = []
        self.model = None
        self._init_model()

    def _init_model(self):
        if self.model_name == "XGBoost Regressor":
            default_params = {
                "n_estimators": 150,
                "learning_rate": 0.05,
                "max_depth": 5,
                "subsample": 0.85,
                "colsample_bytree": 0.85,
                "random_state": 42,
                "n_jobs": -1
            }
            default_params.update(self.params)
            self.model = xgb.XGBRegressor(**default_params)

        elif self.model_name == "Random Forest Regressor":
            default_params = {
                "n_estimators": 120,
                "max_depth": 12,
                "min_samples_split": 4,
                "random_state": 42,
                "n_jobs": -1
            }
            default_params.update(self.params)
            self.model = RandomForestRegressor(**default_params)

        elif self.model_name == "HistGradientBoosting":
            default_params = {
                "max_iter": 150,
                "learning_rate": 0.06,
                "max_depth": 6,
                "random_state": 42
            }
            default_params.update(self.params)
            self.model = HistGradientBoostingRegressor(**default_params)

        elif self.model_name == "Ridge Regression":
            default_params = {"alpha": 1.0, "random_state": 42}
            default_params.update(self.params)
            self.model = Pipeline([
                ("scaler", StandardScaler()),
                ("regressor", Ridge(**default_params))
            ])

        elif self.model_name == "Ensemble Stacking (Hybrid)":
            self.model = None  # Handled separately in EnsembleStackingModel
        else:
            raise ValueError(f"Unknown model name: {self.model_name}")

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.feature_names = list(X.columns)
        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X[self.feature_names])

    def get_feature_importance(self) -> pd.DataFrame:
        """Returns sorted DataFrame of feature importances if supported."""
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            return pd.DataFrame({
                "feature": self.feature_names,
                "importance": importances
            }).sort_values(by="importance", ascending=False).reset_index(drop=True)
        elif self.model_name == "Ridge Regression":
            reg = self.model.named_steps["regressor"]
            importances = np.abs(reg.coef_)
            return pd.DataFrame({
                "feature": self.feature_names,
                "importance": importances / (importances.sum() + 1e-8)
            }).sort_values(by="importance", ascending=False).reset_index(drop=True)
        return pd.DataFrame(columns=["feature", "importance"])

    def save(self, filepath: Optional[Path] = None):
        if filepath is None:
            clean_name = self.model_name.replace(" ", "_").lower()
            filepath = MODELS_DIR / f"{clean_name}.joblib"
        joblib.dump({"model": self.model, "feature_names": self.feature_names, "name": self.model_name}, filepath)
        return filepath

    @classmethod
    def load(cls, filepath: Path):
        data = joblib.load(filepath)
        instance = cls(model_name=data["name"])
        instance.model = data["model"]
        instance.feature_names = data["feature_names"]
        return instance


class EnsembleStackingModel:
    """Ensemble blender combining XGBoost, Random Forest, and HistGradient."""
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.model_name = "Ensemble Stacking (Hybrid)"
        self.weights = weights or {
            "XGBoost Regressor": 0.45,
            "Random Forest Regressor": 0.35,
            "HistGradientBoosting": 0.20
        }
        self.models = {
            name: CropPriceModel(name) for name in self.weights.keys()
        }
        self.feature_names = []

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.feature_names = list(X.columns)
        for name, model in self.models.items():
            model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        preds = np.zeros(len(X))
        total_weight = sum(self.weights.values())
        for name, model in self.models.items():
            w = self.weights[name] / total_weight
            preds += w * model.predict(X)
        return preds

    def get_feature_importance(self) -> pd.DataFrame:
        dfs = []
        for name, model in self.models.items():
            fi = model.get_feature_importance()
            if not fi.empty:
                fi["importance"] = fi["importance"] * self.weights[name]
                dfs.append(fi)
        if dfs:
            combined = pd.concat(dfs).groupby("feature").sum().reset_index()
            combined["importance"] = combined["importance"] / combined["importance"].sum()
            return combined.sort_values(by="importance", ascending=False).reset_index(drop=True)
        return pd.DataFrame(columns=["feature", "importance"])

    def save(self, filepath: Optional[Path] = None):
        if filepath is None:
            filepath = MODELS_DIR / "ensemble_stacking.joblib"
        joblib.dump({"models": self.models, "weights": self.weights, "feature_names": self.feature_names}, filepath)
        return filepath
