"""
CropPricePredict - Machine Learning Model Page
Train, evaluate, compare regression models, and inspect feature importances.
"""
import joblib
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from config import MODELS_DIR
from data.database import load_data_from_db
from ml.train_model import train_and_evaluate_models
from ui.styles import render_metric_card

def render_model_management_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">Statistical Forecasting Models</h1>
            <div class="brand-subtitle">Calibrate price regression models, evaluate validation metrics (MAE, RMSE, R²), and inspect feature importances</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    model_path = MODELS_DIR / "price_model.joblib"
    meta_path = MODELS_DIR / "model_metadata.joblib"

    # Action bar for training
    with st.container():
        c_train1, c_train2 = st.columns([2, 1])
        with c_train1:
            st.markdown("### Train / Retrain Model Pipeline")
            st.write("Trains Linear Regression, Random Forest, and HistGradientBoosting models using chronological time-based validation (80/20 train-test split).")
        with c_train2:
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            if st.button("Train Model", type="primary", use_container_width=True):
                with st.spinner("Training models on agricultural dataset..."):
                    try:
                        df_all = load_data_from_db()
                        best_m, meta, comp_df = train_and_evaluate_models(df_all)
                        st.success(f"Model trained successfully! Selected **{meta['best_model_name']}** with validation RMSE of ₹{meta['metrics']['rmse']:.2f}.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Model training error: {e}")

    st.markdown("---")

    if not model_path.exists() or not meta_path.exists():
        st.warning("No trained model artifact currently exists on disk. Click 'Train Model' above to train the machine learning pipeline.")
        return

    metadata = joblib.load(meta_path)
    metrics = metadata.get("metrics", {})

    # Model Overview KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_metric_card("Current Model", metadata.get("best_model_name", "Random Forest"), "Selected prediction model", trend="neutral"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric_card("R² Score", f"{metrics.get('r2', 0.0):.4f}", "Variance score", trend="up"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric_card("MAE", f"₹{metrics.get('mae', 0.0):.2f}", "Mean Absolute Error", trend="blue"), unsafe_allow_html=True)
    with c4:
        st.markdown(render_metric_card("RMSE", f"₹{metrics.get('rmse', 0.0):.2f}", "Root Mean Square Error", trend="blue"), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # Model Evaluation Comparison Table
    st.markdown("### Model Performance Comparison")
    all_metrics = metadata.get("all_model_metrics", {})
    if all_metrics:
        rows = []
        for name, m in all_metrics.items():
            rows.append({
                "Model": name,
                "MAE (₹)": m.get("mae", 0.0),
                "RMSE (₹)": m.get("rmse", 0.0),
                "R² Score": m.get("r2", 0.0),
                "MAPE (%)": m.get("mape", 0.0)
            })
        comp_df = pd.DataFrame(rows).sort_values(by="RMSE (₹)", ascending=True)
        st.dataframe(comp_df, use_container_width=True)

        st.info(
            f"**Model Selection Result**: **{metadata.get('best_model_name')}** produced the lowest validation error "
            f"among the tested models and has therefore been selected as the current prediction model."
        )

    # Explainable ML: Feature Importance Chart
    st.markdown("---")
    st.markdown("### Feature Importance (Explainable ML)")
    fi_dict = metadata.get("feature_importances", {})
    if fi_dict:
        fi_df = pd.DataFrame(list(fi_dict.items()), columns=["Feature", "Importance"]).sort_values(by="Importance", ascending=False)
        top_10 = fi_df.head(10).sort_values(by="Importance", ascending=True)

        fig_fi = px.bar(
            top_10,
            x="Importance",
            y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale="Teal",
            title="Top Influencing Features in Model Predictions",
            template="plotly_white"
        )
        st.plotly_chart(fig_fi, use_container_width=True)

        # Natural Explanation
        st.markdown("#### Explanation of Model Factors")
        top_f = fi_df.iloc[0]["Feature"] if not fi_df.empty else "lag_1"
        st.markdown(
            f"- **Primary Influencer**: Feature `{top_f}` contributed the highest relative importance in predicting future price.\n"
            f"- **Lag Features**: Previous historical prices (`lag_1`, `lag_7`, `lag_30`) capture recent momentum.\n"
            f"- **Seasonality**: Month and cyclical features reflect seasonal supply variations during harvest periods."
        )
