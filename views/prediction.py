"""
CropPricePredict - Price Prediction & Crop Comparison Page
Predicts future crop market prices using supervised machine learning models.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from config import CROPS_METADATA, STATE_MANDIS, FORECAST_HORIZONS, MODELS_DIR
from data.database import load_data_from_db
from ml.predict import predict_future_crop_prices
from ml.train_model import train_and_evaluate_models
from ui.styles import render_metric_card

def render_prediction_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">Mandi Price Forecasting</h1>
            <div class="brand-subtitle">Forecast expected future crop prices using historical APMC market trends and statistical regression</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_single, tab_compare = st.tabs(["Crop Price Prediction", "Compare Multiple Crops"])

    with tab_single:
        st.markdown("### Prediction Inputs")
        
        with st.form("prediction_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                sel_crop = st.selectbox("Crop", list(CROPS_METADATA.keys()), index=0)
                sel_state = st.selectbox("State", list(STATE_MANDIS.keys()), index=0)
                sel_mandi = st.selectbox("Market / Mandi", STATE_MANDIS[sel_state]["mandis"], index=0)
            with col2:
                sel_season = st.selectbox("Season", ["Rabi", "Kharif", "Zaid", "Whole Year"], index=0)
                sel_year = st.number_input("Year", min_value=2023, max_value=2030, value=datetime.now().year)
                sel_month = st.selectbox("Month", [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ], index=datetime.now().month - 1)
            with col3:
                base_price = CROPS_METADATA.get(sel_crop, {}).get("base_price", 2200.0)
                current_price_input = st.number_input("Current / Latest Price (₹/Quintal)", min_value=100.0, max_value=50000.0, value=float(base_price))
                prev_price_input = st.number_input("Previous Month Price (₹/Quintal)", min_value=100.0, max_value=50000.0, value=float(base_price * 0.98))
                sel_horizon_label = st.selectbox("Prediction Horizon", list(FORECAST_HORIZONS.keys()), index=3)
                horizon_days = FORECAST_HORIZONS[sel_horizon_label]

            with st.expander("Optional Agricultural & Weather Factors", expanded=False):
                env1, env2, env3 = st.columns(3)
                with env1:
                    rainfall_input = st.number_input("Rainfall (mm)", min_value=0.0, max_value=2000.0, value=25.0)
                with env2:
                    temp_input = st.number_input("Temperature (°C)", min_value=-10.0, max_value=60.0, value=26.0)
                with env3:
                    humidity_input = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=65.0)

            submit_btn = st.form_submit_button("Predict Price", use_container_width=True, type="primary")

        # Load historical database records
        df_hist = load_data_from_db(commodity=sel_crop, market=sel_mandi)
        if df_hist.empty:
            df_hist = load_data_from_db(commodity=sel_crop)

        # Check for trained model
        model_path = MODELS_DIR / "price_model.joblib"
        if not model_path.exists():
            st.info("Calibrating regression forecasting model on mandi price history...")
            with st.spinner("Calculating price regression trends..."):
                try:
                    df_all = load_data_from_db()
                    train_and_evaluate_models(df_all)
                except Exception as e:
                    st.error("Please train the model using a suitable dataset before making predictions.")
                    return

        try:
            forecast_df, summary = predict_future_crop_prices(
                df_raw=df_hist,
                commodity=sel_crop,
                market=sel_mandi,
                horizon_days=horizon_days
            )
        except Exception as err:
            st.error(f"Prediction Error: {err}")
            return

        # Display Prediction Output Cards
        st.markdown("---")
        st.markdown("### Prediction Output")

        pred_price = summary["predicted_price"]
        pct_change = summary["pct_change"]
        trend = summary["trend"]
        curr_price = summary["current_price"]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(render_metric_card("Current Price", f"₹{curr_price:,.2f} / Qtl", "Latest market price", trend="neutral"), unsafe_allow_html=True)
        with c2:
            st.markdown(render_metric_card("Predicted Price", f"₹{pred_price:,.2f} / Qtl", f"Horizon: {sel_horizon_label}", trend="up" if pct_change >= 0 else "down"), unsafe_allow_html=True)
        with c3:
            st.markdown(render_metric_card("Expected Change", f"{pct_change:+.2f}%", f"Change: ₹{pred_price - curr_price:+,.2f}", trend="up" if pct_change >= 0 else "down"), unsafe_allow_html=True)
        with c4:
            st.markdown(render_metric_card("Market Trend", f"{trend}", f"Model: {summary['model_used']}", trend="blue"), unsafe_allow_html=True)

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

        # Plotly Trajectory Chart
        fig_pred = go.Figure()
        fig_pred.add_trace(go.Scatter(
            x=forecast_df["date"], y=forecast_df["upper_bound_90"],
            mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"
        ))
        fig_pred.add_trace(go.Scatter(
            x=forecast_df["date"], y=forecast_df["lower_bound_90"],
            mode="lines", line=dict(width=0), fill="tonexty",
            fillcolor="rgba(14, 165, 233, 0.18)", name="90% Confidence Interval"
        ))
        fig_pred.add_trace(go.Scatter(
            x=forecast_df["date"], y=forecast_df["predicted_price"],
            mode="lines+markers", name="Predicted Trajectory",
            line=dict(color="#0284C7", width=3)
        ))
        fig_pred.update_layout(
            title=f"Predicted Price Trend for {sel_crop} ({sel_mandi}) - {sel_horizon_label}",
            xaxis_title="Date", yaxis_title="Price (₹ / Quintal)",
            template="plotly_white", height=400
        )
        st.plotly_chart(fig_pred, use_container_width=True)

    # Tab 2: Multi-Crop Comparison
    with tab_compare:
        st.markdown("### Crop Price Comparison")
        selected_compare_crops = st.multiselect(
            "Select Crops to Compare",
            options=list(CROPS_METADATA.keys()),
            default=["Wheat", "Rice (Paddy)", "Maize (Corn)"]
        )

        if len(selected_compare_crops) > 0:
            compare_rows = []
            for crop in selected_compare_crops:
                df_c = load_data_from_db(commodity=crop)
                if not df_c.empty:
                    try:
                        _, sum_c = predict_future_crop_prices(df_c, commodity=crop, horizon_days=30)
                        compare_rows.append({
                            "Crop": crop,
                            "Current Price": f"₹{sum_c['current_price']:,.2f}",
                            "Predicted Price": f"₹{sum_c['predicted_price']:,.2f}",
                            "Expected Change": f"{sum_c['pct_change']:+.2f}%",
                            "Trend": sum_c["trend"],
                            "raw_current": sum_c['current_price'],
                            "raw_pred": sum_c['predicted_price']
                        })
                    except Exception:
                        pass

            if compare_rows:
                cmp_df = pd.DataFrame(compare_rows)
                st.dataframe(cmp_df[["Crop", "Current Price", "Predicted Price", "Expected Change", "Trend"]], use_container_width=True)

                fig_cmp = px.bar(
                    cmp_df,
                    x="Crop",
                    y=["raw_current", "raw_pred"],
                    barmode="group",
                    labels={"value": "Price (₹/Quintal)", "variable": "Price Type"},
                    title="Current vs 30-Day Predicted Prices Comparison",
                    template="plotly_white",
                    color_discrete_sequence=["#10B981", "#0284C7"]
                )
                st.plotly_chart(fig_cmp, use_container_width=True)
            else:
                st.warning("Insufficient data available for comparison.")
