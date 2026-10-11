"""
CropPricePredict - What-If Scenario Simulation Studio
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from config import CROPS_METADATA, STATE_MANDIS
from data.database import load_data_from_db
from core.feature_engineering import build_crop_features
from core.models import CropPriceModel
from core.predictor import MultiHorizonPredictor
from ui.styles import render_metric_card

def render_scenario_sim_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">🧪 What-If Scenario Simulation Studio</h1>
            <div class="brand-subtitle">Simulate Climate Shocks, Monsoon Variations, Arrival Influxes & Fuel Price Surges</div>
        </div>
        <div>
            <span class="status-pill pill-blue">Stress Test Engine</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_col1, c_col2, c_col3 = st.columns(3)
    with c_col1:
        sel_crop = st.selectbox("Commodity", list(CROPS_METADATA.keys()), key="scen_crop")
    with c_col2:
        sel_state = st.selectbox("State", list(STATE_MANDIS.keys()), key="scen_state")
        sel_mandi = st.selectbox("Mandi Center", STATE_MANDIS[sel_state]["mandis"], key="scen_mandi")
    with c_col3:
        sim_horizon = st.slider("Simulation Horizon (Days)", min_value=7, max_value=90, value=30, step=7)

    st.markdown("### 🎛️ Scenario Shock Controls")
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        rain_shock = st.slider("🌧️ Rainfall Variation (%)", min_value=-80, max_value=150, value=-30, step=10, help="Negative for drought / deficient monsoon; positive for excessive unseasonal rain.")
    with s_col2:
        arrival_shock = st.slider("🚜 Mandi Arrival Shift (%)", min_value=-50, max_value=100, value=25, step=5, help="Positive for bumper crop harvest influx; negative for supply shortage/pest damage.")
    with s_col3:
        fuel_shock = st.slider("⛽ Diesel & Freight Cost Shift (%)", min_value=-15, max_value=40, value=10, step=5, help="Simulate transportation fuel cost changes.")

    hist_df = load_data_from_db(commodity=sel_crop, market=sel_mandi)
    if hist_df.empty:
        hist_df = load_data_from_db(commodity=sel_crop)

    if hist_df.empty:
        st.warning("No data found for selected crop.")
        return

    # Train predictor
    featured_df, feat_cols = build_crop_features(hist_df, commodity=sel_crop, market=sel_mandi)
    model = CropPriceModel("XGBoost Regressor")
    model.fit(featured_df[feat_cols], featured_df["modal_price"])
    predictor = MultiHorizonPredictor(model, feat_cols)

    # 1. Baseline forecast (no adjustments)
    base_forecast = predictor.forecast(
        historical_df=hist_df,
        horizon_days=sim_horizon,
        commodity=sel_crop,
        market=sel_mandi,
        state=sel_state,
        scenario_adjustments={"rainfall_pct_change": 0.0, "arrival_pct_change": 0.0, "fuel_pct_change": 0.0}
    )

    # 2. Stress scenario forecast
    stress_forecast = predictor.forecast(
        historical_df=hist_df,
        horizon_days=sim_horizon,
        commodity=sel_crop,
        market=sel_mandi,
        state=sel_state,
        scenario_adjustments={
            "rainfall_pct_change": float(rain_shock),
            "arrival_pct_change": float(arrival_shock),
            "fuel_pct_change": float(fuel_shock)
        }
    )

    base_final = base_forecast["predicted_price"].iloc[-1]
    stress_final = stress_forecast["predicted_price"].iloc[-1]
    delta_p = stress_final - base_final
    pct_impact = (delta_p / base_final) * 100.0

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(render_metric_card(
            f"Baseline {sim_horizon}D Forecast",
            f"₹{base_final:,.2f} / Qtl",
            "Normal market trajectory",
            trend="neutral"
        ), unsafe_allow_html=True)
    with k2:
        st.markdown(render_metric_card(
            f"Scenario Impact Forecast",
            f"₹{stress_final:,.2f} / Qtl",
            f"{pct_impact:+.2f}% divergence from baseline",
            trend="up" if pct_impact >= 0 else "down"
        ), unsafe_allow_html=True)
    with k3:
        st.markdown(render_metric_card(
            "Net Price Shock Delta",
            f"₹{delta_p:+,.2f} / Qtl",
            f"Rain: {rain_shock:+d}% | Arr: {arrival_shock:+d}% | Fuel: {fuel_shock:+d}%",
            trend="blue"
        ), unsafe_allow_html=True)

    # Plot Comparison
    fig_sim = go.Figure()
    fig_sim.add_trace(go.Scatter(
        x=base_forecast["date"],
        y=base_forecast["predicted_price"],
        mode="lines+markers",
        name="Baseline Forecast (Standard)",
        line=dict(color="#065F46", width=2.5)
    ))
    fig_sim.add_trace(go.Scatter(
        x=stress_forecast["date"],
        y=stress_forecast["predicted_price"],
        mode="lines+markers",
        name="Stress Scenario Forecast",
        line=dict(color="#DC2626" if pct_impact < 0 else "#2563EB", width=3, dash="dash")
    ))

    fig_sim.update_layout(
        title=f"Scenario Comparison: Baseline vs Stress Impacts for {sel_crop} ({sim_horizon} Days)",
        xaxis_title="Forecast Date",
        yaxis_title="Market Price (₹ / Quintal)",
        template="plotly_white",
        hovermode="x unified",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig_sim, use_container_width=True)
