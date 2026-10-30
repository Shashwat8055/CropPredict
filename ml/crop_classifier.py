"""
CropPricePredict - Machine Learning Classification Pipeline for Crop Recommendation
B.Tech Capstone Project - Department of Computer Science & Engineering

Implements Supervised Multiclass Classification to recommend optimal crops based on:
- Soil Nutrients: Nitrogen (N), Phosphorus (P), Potassium (K), Soil pH
- Meteorological Factors: Temperature (°C), Humidity (%), Rainfall (mm)

Algorithms Evaluated:
1. Random Forest Classifier (Ensemble Bagging)
2. HistGradientBoosting Classifier (Ensemble Boosting)
3. Support Vector Classifier (RBF Kernel)
4. Decision Tree Classifier (CART)
5. Gaussian Naive Bayes (Probabilistic Baseline)
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import time

from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from config import MODELS_DIR, DATA_DIR, CROPS_METADATA

CLASSIFIER_PATH = MODELS_DIR / "crop_classifier.joblib"
CLASSIFIER_META_PATH = MODELS_DIR / "crop_classifier_metadata.joblib"
AGRONOMIC_DATASET_PATH = DATA_DIR / "crop_agronomic_dataset.csv"

# Agronomic optimal parameter distributions for supported crops
# Values derived from ICAR (Indian Council of Agricultural Research) & agricultural research benchmarks
AGRONOMIC_PROFILES = {
    "Wheat": {
        "N": (90, 140), "P": (40, 70), "K": (30, 60),
        "temperature": (15.0, 25.0), "humidity": (50.0, 70.0),
        "ph": (6.0, 7.5), "rainfall": (350.0, 650.0)
    },
    "Rice (Paddy)": {
        "N": (70, 110), "P": (35, 60), "K": (35, 55),
        "temperature": (22.0, 32.0), "humidity": (80.0, 95.0),
        "ph": (5.5, 7.0), "rainfall": (1000.0, 1800.0)
    },
    "Cotton": {
        "N": (100, 145), "P": (45, 75), "K": (40, 65),
        "temperature": (24.0, 35.0), "humidity": (60.0, 80.0),
        "ph": (6.0, 8.0), "rainfall": (600.0, 1000.0)
    },
    "Soybean": {
        "N": (20, 45), "P": (55, 85), "K": (35, 65),
        "temperature": (20.0, 30.0), "humidity": (60.0, 75.0),
        "ph": (6.0, 7.5), "rainfall": (650.0, 1000.0)
    },
    "Mustard": {
        "N": (60, 95), "P": (30, 55), "K": (25, 45),
        "temperature": (12.0, 24.0), "humidity": (45.0, 65.0),
        "ph": (6.0, 7.5), "rainfall": (300.0, 550.0)
    },
    "Maize (Corn)": {
        "N": (80, 125), "P": (40, 65), "K": (35, 55),
        "temperature": (20.0, 30.0), "humidity": (55.0, 75.0),
        "ph": (5.8, 7.2), "rainfall": (500.0, 900.0)
    },
    "Gram (Chickpea)": {
        "N": (20, 40), "P": (50, 75), "K": (25, 45),
        "temperature": (16.0, 26.0), "humidity": (45.0, 65.0),
        "ph": (6.0, 7.8), "rainfall": (400.0, 700.0)
    },
    "Tomato": {
        "N": (110, 160), "P": (60, 95), "K": (60, 100),
        "temperature": (20.0, 30.0), "humidity": (60.0, 80.0),
        "ph": (6.0, 7.0), "rainfall": (500.0, 850.0)
    },
    "Onion": {
        "N": (80, 120), "P": (45, 75), "K": (40, 70),
        "temperature": (18.0, 28.0), "humidity": (55.0, 70.0),
        "ph": (6.0, 7.5), "rainfall": (450.0, 750.0)
    },
    "Potato": {
        "N": (90, 135), "P": (50, 80), "K": (80, 125),
        "temperature": (15.0, 23.0), "humidity": (65.0, 85.0),
        "ph": (5.2, 6.5), "rainfall": (450.0, 700.0)
    }
}

FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

def generate_or_load_agronomic_dataset(n_samples_per_crop: int = 250) -> pd.DataFrame:
    """
    Generates or loads the agricultural soil & climate training dataset.
    Uses realistic Gaussian distributions around agronomic optima.
    """
    if AGRONOMIC_DATASET_PATH.exists():
        df = pd.read_csv(AGRONOMIC_DATASET_PATH)
        if len(df) >= len(AGRONOMIC_PROFILES) * 100:
            return df

    np.random.seed(42)
    records = []
    for crop, prof in AGRONOMIC_PROFILES.items():
        for _ in range(n_samples_per_crop):
            n_val = np.clip(np.random.normal((prof["N"][0] + prof["N"][1]) / 2, (prof["N"][1] - prof["N"][0]) / 4), 0, 250)
            p_val = np.clip(np.random.normal((prof["P"][0] + prof["P"][1]) / 2, (prof["P"][1] - prof["P"][0]) / 4), 0, 200)
            k_val = np.clip(np.random.normal((prof["K"][0] + prof["K"][1]) / 2, (prof["K"][1] - prof["K"][0]) / 4), 0, 200)
            t_val = np.clip(np.random.normal((prof["temperature"][0] + prof["temperature"][1]) / 2, (prof["temperature"][1] - prof["temperature"][0]) / 4), 5, 45)
            h_val = np.clip(np.random.normal((prof["humidity"][0] + prof["humidity"][1]) / 2, (prof["humidity"][1] - prof["humidity"][0]) / 4), 10, 100)
            ph_val = np.clip(np.random.normal((prof["ph"][0] + prof["ph"][1]) / 2, (prof["ph"][1] - prof["ph"][0]) / 4), 3.5, 9.5)
            r_val = np.clip(np.random.normal((prof["rainfall"][0] + prof["rainfall"][1]) / 2, (prof["rainfall"][1] - prof["rainfall"][0]) / 4), 100, 2500)

            records.append({
                "N": round(float(n_val), 1),
                "P": round(float(p_val), 1),
                "K": round(float(k_val), 1),
                "temperature": round(float(t_val), 2),
                "humidity": round(float(h_val), 2),
                "ph": round(float(ph_val), 2),
                "rainfall": round(float(r_val), 1),
                "crop": crop
            })

    df = pd.DataFrame(records)
    df.to_csv(AGRONOMIC_DATASET_PATH, index=False)
    return df

def train_and_evaluate_classifiers(
    test_size: float = 0.20,
    random_state: int = 42
) -> Tuple[Any, Dict[str, Any], pd.DataFrame]:
    """
    Trains and benchmarks multiple multiclass classifiers:
    - Random Forest
    - HistGradientBoosting
    - Support Vector Machine (SVC)
    - Decision Tree
    - Gaussian Naive Bayes

    Returns:
        (best_model_pipeline, metadata_dictionary, comparison_dataframe)
    """
    df = generate_or_load_agronomic_dataset()
    X = df[FEATURE_COLUMNS]
    y = df["crop"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    models = {
        "Random Forest Classifier": RandomForestClassifier(n_estimators=100, max_depth=12, random_state=random_state, n_jobs=-1),
        "HistGradientBoosting Classifier": HistGradientBoostingClassifier(max_iter=100, learning_rate=0.1, random_state=random_state),
        "Support Vector Classifier (RBF)": Pipeline([("scaler", StandardScaler()), ("svc", SVC(probability=True, kernel="rbf", C=2.0, random_state=random_state))]),
        "Decision Tree Classifier": DecisionTreeClassifier(max_depth=10, random_state=random_state),
        "Gaussian Naive Bayes": GaussianNB()
    }

    eval_results = {}
    fitted_models = {}
    classes_list = sorted(list(y.unique()))

    for name, model in models.items():
        t0 = time.time()
        model.fit(X_train, y_train)
        fit_time = time.time() - t0

        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
        rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
        f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

        eval_results[name] = {
            "accuracy": float(acc),
            "precision_macro": float(prec),
            "recall_macro": float(rec),
            "f1_macro": float(f1),
            "train_time_sec": round(float(fit_time), 3)
        }
        fitted_models[name] = model

    # Select best model based on F1-score
    comp_rows = []
    for name, m in eval_results.items():
        comp_rows.append({
            "Model": name,
            "Accuracy": f"{m['accuracy'] * 100:.2f}%",
            "Precision": f"{m['precision_macro'] * 100:.2f}%",
            "Recall": f"{m['recall_macro'] * 100:.2f}%",
            "Macro F1-Score": f"{m['f1_macro'] * 100:.2f}%",
            "Fit Time (s)": f"{m['train_time_sec']:.3f}",
            "raw_f1": m["f1_macro"]
        })
    comp_df = pd.DataFrame(comp_rows).sort_values(by="raw_f1", ascending=False).drop(columns=["raw_f1"]).reset_index(drop=True)

    best_name = comp_df.iloc[0]["Model"]
    best_model = fitted_models[best_name]

    # Compute Confusion Matrix for best model
    best_pred = best_model.predict(X_test)
    cm = confusion_matrix(y_test, best_pred, labels=classes_list)

    # Compute Feature Importances
    feature_importances = {}
    if hasattr(best_model, "feature_importances_"):
        for f, imp in zip(FEATURE_COLUMNS, best_model.feature_importances_):
            feature_importances[f] = float(imp)
    elif hasattr(best_model, "named_steps") and hasattr(best_model.named_steps.get("svc", None), "coef_"):
        pass
    else:
        # Fallback using Random Forest feature importances
        rf = fitted_models["Random Forest Classifier"]
        for f, imp in zip(FEATURE_COLUMNS, rf.feature_importances_):
            feature_importances[f] = float(imp)

    metadata = {
        "best_model_name": best_name,
        "classes": classes_list,
        "feature_names": FEATURE_COLUMNS,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "total_samples": len(X),
        "metrics": eval_results[best_name],
        "all_model_metrics": eval_results,
        "confusion_matrix": cm.tolist(),
        "feature_importances": feature_importances,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Persist model and metadata
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, CLASSIFIER_PATH)
    joblib.dump(metadata, CLASSIFIER_META_PATH)

    return best_model, metadata, comp_df

def get_or_train_crop_classifier() -> Tuple[Any, Dict[str, Any]]:
    """Loads cached classification model or trains a new one if missing."""
    if CLASSIFIER_PATH.exists() and CLASSIFIER_META_PATH.exists():
        try:
            model = joblib.load(CLASSIFIER_PATH)
            meta = joblib.load(CLASSIFIER_META_PATH)
            return model, meta
        except Exception:
            pass
    model, meta, _ = train_and_evaluate_classifiers()
    return model, meta

def predict_crop_suitability(
    n: float,
    p: float,
    k: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Inference function: Computes posterior crop probabilities given input soil & climate vector.
    Returns ranked list of top_k crops with confidence percentages.
    """
    model, meta = get_or_train_crop_classifier()
    input_df = pd.DataFrame([{
        "N": float(n),
        "P": float(p),
        "K": float(k),
        "temperature": float(temperature),
        "humidity": float(humidity),
        "ph": float(ph),
        "rainfall": float(rainfall)
    }])

    classes = meta.get("classes", [])

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(input_df)[0]
    else:
        # Fallback decision function
        pred_label = model.predict(input_df)[0]
        return [{"crop": pred_label, "confidence_pct": 95.0, "rank": 1}]

    ranked_indices = np.argsort(probs)[::-1]
    results = []
    for rank, idx in enumerate(ranked_indices[:top_k], start=1):
        crop_label = classes[idx]
        conf = float(probs[idx] * 100.0)
        results.append({
            "crop": crop_label,
            "confidence_pct": round(conf, 2),
            "rank": rank
        })

    return results
