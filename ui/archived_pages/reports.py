"""
CropPricePredict - Executive Reports & Export Center
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

from config import CROPS_METADATA, STATE_MANDIS, REPORTS_DIR
from data.database import load_data_from_db
from core.feature_engineering import build_crop_features
from core.models import CropPriceModel
from core.predictor import MultiHorizonPredictor
from core.advisor import analyze_selling_window
from core.evaluator import calculate_metrics
from reports.pdf_generator import generate_crop_pdf_report

def render_reports_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">📄 Executive Reports & Export Center</h1>
            <div class="brand-subtitle">Generate Formatted PDF Market Intelligence & Price Forecasting Reports</div>
        </div>
        <div>
            <span class="status-pill pill-green">PDF Engine Ready</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        rep_crop = st.selectbox("Select Commodity", list(CROPS_METADATA.keys()), key="rep_crop")
    with r_col2:
        rep_state = st.selectbox("Select State", list(STATE_MANDIS.keys()), key="rep_state")
        rep_mandi = st.selectbox("Target Mandi", STATE_MANDIS[rep_state]["mandis"], key="rep_mandi")
    with r_col3:
        rep_horizon = st.selectbox("Forecast Horizon for Report", [14, 30, 60, 90], index=1)

    if st.button("📑 Generate Official PDF Intelligence Report", type="primary", use_container_width=True):
        with st.spinner(f"Generating PDF Market Forecast Report for {rep_crop}..."):
            hist_df = load_data_from_db(commodity=rep_crop, market=rep_mandi)
            if hist_df.empty:
                hist_df = load_data_from_db(commodity=rep_crop)

            if hist_df.empty:
                st.error("No historical data found.")
                return

            featured_df, feat_cols = build_crop_features(hist_df, commodity=rep_crop, market=rep_mandi)
            model = CropPriceModel("XGBoost Regressor")
            
            # Split for metrics
            split_idx = int(len(featured_df) * 0.85)
            X_train, X_test = featured_df[feat_cols].iloc[:split_idx], featured_df[feat_cols].iloc[split_idx:]
            y_train, y_test = featured_df["modal_price"].iloc[:split_idx], featured_df["modal_price"].iloc[split_idx:]
            model.fit(X_train, y_train)
            test_preds = model.predict(X_test)
            metrics_res = calculate_metrics(y_test.values, test_preds)

            # Fit full model & forecast
            model.fit(featured_df[feat_cols], featured_df["modal_price"])
            predictor = MultiHorizonPredictor(model, feat_cols)
            forecast_df = predictor.forecast(
                historical_df=hist_df,
                horizon_days=rep_horizon,
                commodity=rep_crop,
                market=rep_mandi,
                state=rep_state
            )

            current_p = hist_df["modal_price"].iloc[-1]
            adv_res = analyze_selling_window(forecast_df, commodity=rep_crop, current_price=current_p)

            # Generate PDF
            pdf_path = generate_crop_pdf_report(
                commodity=rep_crop,
                market=rep_mandi,
                state=rep_state,
                current_price=current_p,
                forecast_df=forecast_df,
                advisor_data=adv_res,
                metrics_data=metrics_res
            )

            st.success(f"🎉 PDF Report successfully generated: `{pdf_path.name}`")
            
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="⬇️ Download PDF Intelligence Report",
                data=pdf_bytes,
                file_name=pdf_path.name,
                mime="application/pdf",
                use_container_width=True
            )

    # List Existing Generated Reports
    st.markdown("### 🗄️ Previously Generated Reports Archive")
    existing_pdfs = list(REPORTS_DIR.glob("*.pdf"))
    if existing_pdfs:
        for p in sorted(existing_pdfs, reverse=True)[:10]:
            col_name, col_down = st.columns([3, 1])
            with col_name:
                st.markdown(f"📄 **{p.name}** ({p.stat().st_size / 1024:.1f} KB)")
            with col_down:
                with open(p, "rb") as f:
                    st.download_button(
                        label="Download",
                        data=f.read(),
                        file_name=p.name,
                        mime="application/pdf",
                        key=f"dl_{p.name}"
                    )
    else:
        st.info("No saved PDF reports in archive yet. Click 'Generate Official PDF Intelligence Report' above.")
