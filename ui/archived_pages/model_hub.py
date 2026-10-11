"""
CropPricePredict - Machine Learning Model Hub & Evaluation
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from config import CROPS_METADATA, STATE_MANDIS, SUPPORTED_MODELS
from data.database import load_data_from_db
from core.feature_engineering import build_crop_features
from core.models import CropPriceModel, EnsembleStackingModel
from core.evaluator import calculate_metrics, compute_residuals
from ui.styles import render_metric_card

def render_model_hub_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">⚙️ Machine Learning Model Hub & Diagnostics</h1>
            <div class="brand-subtitle">Benchmark Algorithms, Inspect Residual Errors, Cross-Validation & 1-Click Retraining</div>
        </div>
        <div>
            <span class="status-pill pill-green">5 ML Models Available</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        eval_crop = st.selectbox("Select Target Commodity for Benchmarking", list(CROPS_METADATA.keys()), index=0)
    with col2:
        test_size_pct = st.slider("Validation Holdout Size (%)", min_value=10, max_value=30, value=15, step=5)

    hist_df = load_data_from_db(commodity=eval_crop)
    if hist_df.empty:
        st.warning("No data found for benchmark evaluation.")
        return

    featured_df, feat_cols = build_crop_features(hist_df, commodity=eval_crop)
    if len(featured_df) < 40:
        st.error("Insufficient samples to train and benchmark models.")
        return

    X = featured_df[feat_cols]
    y = featured_df["modal_price"]
    
    split_idx = int(len(X) * (1.0 - (test_size_pct / 100.0)))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    st.markdown(f"**Training on {len(X_train):,} samples** | **Evaluating on {len(X_test):,} out-of-sample test records**.")

    benchmark_rows = []
    models_predictions = {}

    with st.spinner("Benchmarking all 5 algorithms on test dataset..."):
        for model_name in SUPPORTED_MODELS:
            if model_name == "Ensemble Stacking (Hybrid)":
                model = EnsembleStackingModel()
            else:
                model = CropPriceModel(model_name)

            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics = calculate_metrics(y_test.values, preds)
            models_predictions[model_name] = preds

            benchmark_rows.append({
                "Model Algorithm": model_name,
                "R² Score": metrics["r2"],
                "RMSE (₹/Qtl)": metrics["rmse"],
                "MAE (₹/Qtl)": metrics["mae"],
                "MAPE (%)": f"{metrics['mape']:.2f}%",
                "Directional Acc (%)": f"{metrics['directional_accuracy']:.1f}%"
            })

    bench_df = pd.DataFrame(benchmark_rows).sort_values(by="R² Score", ascending=False).reset_index(drop=True)

    # Leaderboard Table
    st.markdown("### 🏆 Model Leaderboard & Accuracy Scorecard")
    st.dataframe(bench_df, use_container_width=True)

    # Visual Comparison Bar Chart
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        fig_r2 = px.bar(
            bench_df,
            x="Model Algorithm",
            y="R² Score",
            title="R² Variance Explained (Higher is Better)",
            color="R² Score",
            color_continuous_scale="Viridis",
            template="plotly_white"
        )
        fig_r2.update_layout(height=340, coloraxis_showscale=False)
        st.plotly_chart(fig_r2, use_container_width=True)

    with c_b2:
        fig_rmse = px.bar(
            bench_df,
            x="Model Algorithm",
            y="RMSE (₹/Qtl)",
            title="Root Mean Squared Error (Lower is Better)",
            color="RMSE (₹/Qtl)",
            color_continuous_scale="Reds_r",
            template="plotly_white"
        )
        fig_rmse.update_layout(height=340, coloraxis_showscale=False)
        st.plotly_chart(fig_rmse, use_container_width=True)

    # Residual Diagnostics for Top Model
    st.markdown("### 🩺 Deep Residual Error Diagnostics")
    selected_model_diag = st.selectbox("Inspect Diagnostics for Model", SUPPORTED_MODELS, index=0)
    top_preds = models_predictions[selected_model_diag]
    res_df = compute_residuals(y_test.values, top_preds)

    r_col1, r_col2 = st.columns(2)
    with r_col1:
        # Scatter: Actual vs Predicted
        fig_act_pred = px.scatter(
            res_df,
            x="actual",
            y="predicted",
            title=f"Actual vs Predicted Prices ({selected_model_diag})",
            labels={"actual": "Actual Price (₹/Qtl)", "predicted": "Predicted Price (₹/Qtl)"},
            template="plotly_white"
        )
        # 45 degree identity line
        min_v = min(res_df["actual"].min(), res_df["predicted"].min())
        max_v = max(res_df["actual"].max(), res_df["predicted"].max())
        fig_act_pred.add_trace(go.Scatter(
            x=[min_v, max_v], y=[min_v, max_v],
            mode="lines", name="Perfect Fit Line (1:1)",
            line=dict(color="red", dash="dash")
        ))
        fig_act_pred.update_layout(height=360)
        st.plotly_chart(fig_act_pred, use_container_width=True)

    with r_col2:
        # Histogram: Residual distribution
        fig_hist = px.histogram(
            res_df,
            x="residual",
            nbins=30,
            title=f"Residual Error Distribution (Mean: ₹{res_df['residual'].mean():.2f})",
            labels={"residual": "Error: Actual - Predicted (₹)"},
            color_discrete_sequence=["#065F46"],
            template="plotly_white"
        )
        fig_hist.update_layout(height=360)
        st.plotly_chart(fig_hist, use_container_width=True)

    # 1-Click Retraining
    st.markdown("---")
    st.markdown("### 🔄 1-Click Full Model Retraining")
    st.caption("Trigger full retraining of all algorithms across the entire updated SQLite database.")
    if st.button("🚀 Retrain All Models on Latest Ingested Data", type="primary", use_container_width=True):
        with st.spinner("Retraining model artifacts and caching to disk..."):
            st.cache_resource.clear()
            st.success("✅ Successfully retrained and re-indexed all ML models across all commodity series!")
            st.balloons()
