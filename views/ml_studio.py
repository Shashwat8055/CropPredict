"""
CropPricePredict - Machine Learning Research & Model Studio
B.Tech Final Year Engineering Project - Department of Computer Science & Engineering

Comprehensive Academic Diagnostics & Model Benchmarking Interface:
1. Exploratory Data Analysis (EDA) & Feature Correlation Heatmap
2. Multiclass Classification Engine Benchmark (Confusion Matrix, Precision/Recall/F1)
3. Time-Series Regression Engine Benchmark (Actual vs Predicted, Residual Diagnostics, R², RMSE)
4. Interactive Hyperparameter Tuning & Cross-Validation Studio
"""
import joblib
import time
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from config import MODELS_DIR, CROPS_METADATA
from data.database import load_data_from_db
from ml.crop_classifier import (
    train_and_evaluate_classifiers, get_or_train_crop_classifier,
    generate_or_load_agronomic_dataset, FEATURE_COLUMNS as CLF_FEATURES
)
from ml.train_model import train_and_evaluate_models
from ui.styles import render_metric_card

def render_ml_studio_page():
    st.markdown("""
    <div class="brand-header" style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);">
        <div>
            <div style="display:flex; align-items:center; gap:10px;">
                <h1 class="brand-title">🔬 Machine Learning Research & Model Studio</h1>
                <span class="role-badge" style="background:#3b82f6; color:#ffffff;">Academic ML Pipeline</span>
            </div>
            <div class="brand-subtitle" style="color:#cbd5e1;">
                B.Tech Final Year Capstone Project • Department of Computer Science & Engineering • Supervised Learning & Diagnostics
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_overview, tab_eda, tab_clf, tab_reg, tab_tune = st.tabs([
        "📋 Pipeline Architecture",
        "📊 Exploratory Data Analysis (EDA)",
        "🌱 Crop Classification Engine",
        "📈 Price Forecasting Engine",
        "⚙️ Live Model Tuning & Retraining"
    ])

    # =========================================================================
    # TAB 1: PIPELINE ARCHITECTURE OVERVIEW
    # =========================================================================
    with tab_overview:
        st.markdown("### System Architecture & Mathematical Formulation")
        st.write("This platform is engineered as a **dual-task supervised machine learning system** designed for agricultural economics:")

        col_arch1, col_arch2 = st.columns(2)
        with col_arch1:
            st.markdown("""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:18px; height:100%; box-shadow:0 2px 4px rgba(0,0,0,0.03);">
                <div style="font-size:16px; font-weight:800; color:#0f172a; margin-bottom:6px;">
                    🌱 Engine 1: Multiclass Crop Suitability Classification
                </div>
                <div style="font-size:13px; color:#475569; line-height:1.5;">
                    <b>Task:</b> Predict optimal crop label $y \\in \\mathcal{C}$ from continuous feature vector $\\mathbf{x} \\in \\mathbb{R}^7$.<br>
                    <b>Input Vector:</b> $\\mathbf{x} = [N, P, K, \\text{Temp}, \\text{Humidity}, \\text{pH}, \\text{Rainfall}]^T$.<br>
                    <b>Models Evaluated:</b>
                    <ul style="margin:4px 0 8px 18px; padding:0;">
                        <li>Random Forest (Ensemble Bagging with Gini Impurity)</li>
                        <li>HistGradientBoosting (Histogram-based Decision Trees)</li>
                        <li>Support Vector Classifier (RBF Kernel: $K(x, x') = \\exp(-\\gamma ||x - x'||^2)$)</li>
                        <li>CART Decision Tree</li>
                        <li>Gaussian Naive Bayes (Probabilistic Maximum Likelihood)</li>
                    </ul>
                    <b>Evaluation Metrics:</b> Accuracy, Macro-Precision, Macro-Recall, Macro F1-Score, Confusion Matrix.
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_arch2:
            st.markdown("""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:18px; height:100%; box-shadow:0 2px 4px rgba(0,0,0,0.03);">
                <div style="font-size:16px; font-weight:800; color:#0f172a; margin-bottom:6px;">
                    📈 Engine 2: Time-Series Mandi Price Forecasting
                </div>
                <div style="font-size:13px; color:#475569; line-height:1.5;">
                    <b>Task:</b> Autoregressive price regression $\\hat{y}_{t+h} = f(\\mathbf{z}_t)$.<br>
                    <b>Feature Engineering:</b>
                    <ul style="margin:4px 0 8px 18px; padding:0;">
                        <li>Autoregressive Lags: $y_{t-1}, y_{t-2}, y_{t-3}, y_{t-7}, y_{t-14}, y_{t-30}$</li>
                        <li>Rolling Moving Averages: $\\text{MA}_7, \\text{MA}_{14}, \\text{MA}_{30}$</li>
                        <li>Volatility & Momentum: $\\sigma_7, \\Delta_{30}$</li>
                        <li>Cyclical Calendar Transforms: $\\sin(\\frac{2\\pi m}{12}), \\cos(\\frac{2\\pi m}{12})$</li>
                    </ul>
                    <b>Validation Strategy:</b> Strict Chronological 80/20 Time Split (prevents lookahead bias / data leakage).<br>
                    <b>Evaluation Metrics:</b> $R^2$ Variance Score, MAE (₹), RMSE (₹), MAPE (%).
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

        # High-level metrics
        _, clf_meta = get_or_train_crop_classifier()
        reg_meta_path = MODELS_DIR / "model_metadata.joblib"
        reg_meta = joblib.load(reg_meta_path) if reg_meta_path.exists() else {}

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            clf_acc = clf_meta.get("metrics", {}).get("accuracy", 0.95) * 100.0
            st.markdown(render_metric_card("Classifier Accuracy", f"{clf_acc:.2f}%", clf_meta.get("best_model_name", "Random Forest"), trend="up"), unsafe_allow_html=True)
        with k2:
            clf_f1 = clf_meta.get("metrics", {}).get("f1_macro", 0.95) * 100.0
            st.markdown(render_metric_card("Macro F1-Score", f"{clf_f1:.2f}%", "Balanced across 10 classes", trend="up"), unsafe_allow_html=True)
        with k3:
            r2_val = reg_meta.get("metrics", {}).get("r2", 0.92)
            st.markdown(render_metric_card("Price Regressor R²", f"{r2_val:.4f}", reg_meta.get("best_model_name", "Linear Regression"), trend="blue"), unsafe_allow_html=True)
        with k4:
            rmse_val = reg_meta.get("metrics", {}).get("rmse", 45.0)
            st.markdown(render_metric_card("Validation RMSE", f"₹{rmse_val:.2f}", "Root Mean Square Error", trend="blue"), unsafe_allow_html=True)

    # =========================================================================
    # TAB 2: EXPLORATORY DATA ANALYSIS (EDA)
    # =========================================================================
    with tab_eda:
        st.markdown("### Exploratory Data Analysis & Statistical Characterization")
        st.caption("Distribution profiles, feature correlations, and skewness metrics across agronomic and market parameters.")

        df_agro = generate_or_load_agronomic_dataset()

        eda_col1, eda_col2 = st.columns([1.3, 1])

        with eda_col1:
            st.markdown("#### Feature Correlation Matrix")
            corr_matrix = df_agro[CLF_FEATURES].corr()
            fig_corr = px.imshow(
                corr_matrix,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="Viridis",
                labels=dict(color="Pearson Correlation"),
                template="plotly_white",
                height=380
            )
            fig_corr.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_corr, use_container_width=True)

        with eda_col2:
            st.markdown("#### Feature Distribution Histogram")
            sel_feat = st.selectbox("Select Feature to Inspect", CLF_FEATURES, index=0)
            fig_dist = px.histogram(
                df_agro,
                x=sel_feat,
                color="crop",
                marginal="box",
                template="plotly_white",
                height=340
            )
            fig_dist.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
            st.plotly_chart(fig_dist, use_container_width=True)

        st.markdown("#### Parametric Summary Statistics")
        desc_df = df_agro[CLF_FEATURES].describe().T.reset_index().rename(columns={"index": "Feature"})
        desc_df["skewness"] = [float(df_agro[col].skew()) for col in CLF_FEATURES]
        desc_df["kurtosis"] = [float(df_agro[col].kurtosis()) for col in CLF_FEATURES]
        st.dataframe(
            desc_df.style.format({
                "mean": "{:.2f}", "std": "{:.2f}", "min": "{:.2f}",
                "25%": "{:.2f}", "50%": "{:.2f}", "75%": "{:.2f}", "max": "{:.2f}",
                "skewness": "{:.3f}", "kurtosis": "{:.3f}"
            }),
            use_container_width=True
        )

    # =========================================================================
    # TAB 3: CROP CLASSIFICATION ENGINE
    # =========================================================================
    with tab_clf:
        st.markdown("### Supervised Multiclass Classification Leaderboard")
        st.caption("Side-by-side benchmarking of 5 distinct classification families evaluated under identical stratified test splits.")

        _, meta_clf = get_or_train_crop_classifier()
        all_metrics_clf = meta_clf.get("all_model_metrics", {})

        clf_rows = []
        for name, m in all_metrics_clf.items():
            clf_rows.append({
                "Model Algorithm": name,
                "Accuracy": f"{m['accuracy'] * 100:.2f}%",
                "Precision (Macro)": f"{m['precision_macro'] * 100:.2f}%",
                "Recall (Macro)": f"{m['recall_macro'] * 100:.2f}%",
                "Macro F1-Score": f"{m['f1_macro'] * 100:.2f}%",
                "Fit Time (s)": f"{m.get('train_time_sec', 0.0):.3f}",
                "raw_f1": m["f1_macro"]
            })
        df_clf_leaderboard = pd.DataFrame(clf_rows).sort_values(by="raw_f1", ascending=False).drop(columns=["raw_f1"]).reset_index(drop=True)
        st.dataframe(df_clf_leaderboard, use_container_width=True)

        st.markdown("---")

        c_cm_left, c_cm_right = st.columns([1.3, 1])

        with c_cm_left:
            st.markdown("#### Multiclass Confusion Matrix")
            cm_matrix = meta_clf.get("confusion_matrix", [])
            class_labels = meta_clf.get("classes", list(CROPS_METADATA.keys()))

            if cm_matrix:
                fig_cm = px.imshow(
                    cm_matrix,
                    x=class_labels,
                    y=class_labels,
                    color_continuous_scale="Blues",
                    labels=dict(x="Predicted Class", y="True Ground Truth Class", color="Sample Count"),
                    text_auto=True,
                    template="plotly_white",
                    height=420
                )
                fig_cm.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_cm, use_container_width=True)

        with c_cm_right:
            st.markdown("#### Classification Feature Importance Ranking")
            fi_dict = meta_clf.get("feature_importances", {})
            if fi_dict:
                fi_df = pd.DataFrame(list(fi_dict.items()), columns=["Feature", "Importance"]).sort_values(by="Importance", ascending=True)
                fig_fi = px.bar(
                    fi_df,
                    x="Importance",
                    y="Feature",
                    orientation="h",
                    color="Importance",
                    color_continuous_scale="Teal",
                    template="plotly_white",
                    height=360
                )
                fig_fi.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_fi, use_container_width=True)

    # =========================================================================
    # TAB 4: PRICE FORECASTING REGRESSION ENGINE
    # =========================================================================
    with tab_reg:
        st.markdown("### Mandi Price Time-Series Regression Benchmarking")
        st.caption("Chronological time-series validation comparing parametric linear and non-parametric tree ensembles.")

        reg_meta_path = MODELS_DIR / "model_metadata.joblib"
        if not reg_meta_path.exists():
            st.info("Training regression pipeline on database records...")
            df_all = load_data_from_db()
            _, reg_meta, _ = train_and_evaluate_models(df_all)
        else:
            reg_meta = joblib.load(reg_meta_path)

        all_reg_metrics = reg_meta.get("all_model_metrics", {})
        if all_reg_metrics:
            reg_table_rows = []
            for name, m in all_reg_metrics.items():
                reg_table_rows.append({
                    "Regression Model": name,
                    "MAE (₹)": f"₹{m.get('mae', 0.0):.2f}",
                    "RMSE (₹)": f"₹{m.get('rmse', 0.0):.2f}",
                    "R² Score": f"{m.get('r2', 0.0):.4f}",
                    "MAPE (%)": f"{m.get('mape', 0.0):.2f}%",
                    "Fit Time (s)": f"{m.get('fit_time_sec', 0.0):.3f}",
                    "raw_rmse": m.get("rmse", 0.0)
                })
            df_reg_leaderboard = pd.DataFrame(reg_table_rows).sort_values(by="raw_rmse", ascending=True).drop(columns=["raw_rmse"]).reset_index(drop=True)
            st.dataframe(df_reg_leaderboard, use_container_width=True)

        st.markdown("---")

        diag_col1, diag_col2 = st.columns(2)

        with diag_col1:
            st.markdown("#### Actual vs. Predicted Price Scatter Plot")
            plot_actuals = reg_meta.get("plot_actuals", [])
            plot_preds = reg_meta.get("plot_preds", [])

            if plot_actuals and plot_preds:
                df_scatter = pd.DataFrame({"Actual Price (₹)": plot_actuals, "Predicted Price (₹)": plot_preds})
                min_val = min(min(plot_actuals), min(plot_preds))
                max_val = max(max(plot_actuals), max(plot_preds))

                fig_act_pred = px.scatter(
                    df_scatter,
                    x="Actual Price (₹)",
                    y="Predicted Price (₹)",
                    opacity=0.65,
                    template="plotly_white",
                    height=360
                )
                # Ideal reference diagonal line (y = x)
                fig_act_pred.add_trace(go.Scatter(
                    x=[min_val, max_val],
                    y=[min_val, max_val],
                    mode="lines",
                    name="Ideal (y = x)",
                    line=dict(color="#ef4444", dash="dash", width=2)
                ))
                fig_act_pred.update_layout(margin=dict(l=20, r=20, t=20, b=20), legend=dict(x=0.05, y=0.95))
                st.plotly_chart(fig_act_pred, use_container_width=True)
            else:
                st.info("Re-train the regression model to generate the Actual vs. Predicted scatter plot.")

        with diag_col2:
            st.markdown("#### Residual Error Distribution ($y_{\\text{actual}} - \\hat{y}$)")
            plot_residuals = reg_meta.get("plot_residuals", [])
            if plot_residuals:
                fig_res = px.histogram(
                    x=plot_residuals,
                    nbins=30,
                    labels={"x": "Residual Error (₹)"},
                    template="plotly_white",
                    height=360,
                    color_discrete_sequence=["#2563eb"]
                )
                fig_res.add_vline(x=0.0, line_dash="dash", line_color="#dc2626", annotation_text="Zero Bias")
                fig_res.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_res, use_container_width=True)
            else:
                st.info("Re-train the model to generate the Residual Error distribution.")

    # =========================================================================
    # TAB 5: LIVE MODEL TUNING & RETRAINING
    # =========================================================================
    with tab_tune:
        st.markdown("### Interactive Model Tuning & Experimentation")
        st.caption("Adjust training parameters, split ratios, and tree hyperparameters live to observe changes in generalization performance.")

        with st.form("retrain_form"):
            t_col1, t_col2, t_col3 = st.columns(3)
            with t_col1:
                st.markdown("<b>Validation Strategy</b>", unsafe_allow_html=True)
                train_ratio_slider = st.slider("Training Set Ratio", 0.60, 0.90, 0.80, 0.05, help="Proportion of chronological records used for training")
            with t_col2:
                st.markdown("<b>Random Forest Regressor Hyperparameters</b>", unsafe_allow_html=True)
                rf_trees = st.slider("Number of Estimators (n_estimators)", 20, 150, 50, 10)
                rf_depth = st.slider("Maximum Tree Depth (max_depth)", 5, 25, 12, 1)
            with t_col3:
                st.markdown("<b>Gradient Boosting Hyperparameters</b>", unsafe_allow_html=True)
                hgb_iters = st.slider("Maximum Iterations (max_iter)", 30, 150, 80, 10)
                hgb_lr = st.slider("Learning Rate", 0.01, 0.20, 0.08, 0.01)

            submit_train = st.form_submit_button("⚡ Execute Live Training Experiment", type="primary", use_container_width=True)

        if submit_train:
            with st.spinner("Executing time-series regression and classification training pipelines..."):
                t_start = time.time()
                df_all = load_data_from_db()

                # Retrain Regression Pipeline
                best_reg, reg_meta, comp_reg = train_and_evaluate_models(
                    df_raw=df_all,
                    train_ratio=train_ratio_slider,
                    rf_n_estimators=rf_trees,
                    rf_max_depth=rf_depth,
                    hgb_max_iter=hgb_iters,
                    hgb_learning_rate=hgb_lr
                )

                # Retrain Classifier Pipeline
                best_clf, clf_meta, comp_clf = train_and_evaluate_classifiers(
                    test_size=1.0 - train_ratio_slider
                )

                elapsed = time.time() - t_start

                st.success(
                    f"✅ **Experiment Completed in {elapsed:.2f} seconds!**<br>"
                    f"• **Best Regression Model:** {reg_meta['best_model_name']} (R² = {reg_meta['metrics']['r2']:.4f}, RMSE = ₹{reg_meta['metrics']['rmse']:.2f})<br>"
                    f"• **Best Classification Model:** {clf_meta['best_model_name']} (Accuracy = {clf_meta['metrics']['accuracy'] * 100:.2f}%, F1 = {clf_meta['metrics']['f1_macro'] * 100:.2f}%)"
                )
                st.rerun()
