"""
CropPricePredict - Profit & Selling Advisor Page
Evaluates whether farmers should sell now or wait based on predicted future prices and storage costs.
"""
import streamlit as st
import pandas as pd
import numpy as np

from config import CROPS_METADATA, STATE_MANDIS
from data.database import load_data_from_db
from ml.predict import predict_future_crop_prices
from core.advisor import analyze_selling_window, find_inter_mandi_arbitrage
from ui.styles import render_metric_card

def render_selling_advisor_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">Profit & Selling Advisor</h1>
            <div class="brand-subtitle">Decision-support feature to help farmers evaluate selling timing and market choices</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sel_crop = st.selectbox("Crop", list(CROPS_METADATA.keys()), index=0)
    with c2:
        sel_state = st.selectbox("State", list(STATE_MANDIS.keys()), index=0)
    with c3:
        sel_mandi = st.selectbox("Current Market", STATE_MANDIS[sel_state]["mandis"], index=0)
    with c4:
        qty_quintals = st.number_input("Crop Quantity (Quintals)", min_value=1.0, max_value=10000.0, value=100.0)

    df_hist = load_data_from_db(commodity=sel_crop, market=sel_mandi)
    if df_hist.empty:
        df_hist = load_data_from_db(commodity=sel_crop)

    if df_hist.empty:
        st.warning(f"No records found for {sel_crop}.")
        return

    # Load forecast for 90 days
    try:
        forecast_df, sum_dict = predict_future_crop_prices(df_hist, commodity=sel_crop, market=sel_mandi, horizon_days=90)
    except Exception as e:
        st.error(f"Error making predictions for selling advisor: {e}")
        return

    curr_price = sum_dict["current_price"]
    selling_analysis = analyze_selling_window(
        forecast_df=forecast_df,
        commodity=sel_crop,
        current_price=curr_price,
        quantity_quintals=qty_quintals
    )

    # Selling Suggestion Badge
    rec = selling_analysis["recommendation"]
    st.markdown(f"""
    <div style="background:{selling_analysis['badge_color']}; color:white; padding:18px; border-radius:10px; margin-bottom:20px;">
        <h2 style="margin:0; font-size:22px; color:white;">SELLING SUGGESTION: {rec}</h2>
        <p style="margin-top:8px; font-size:14px; opacity:0.95; color:white;">{selling_analysis['reasoning']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Comparison Table
    st.markdown("### Expected Profit / Net Revenue by Holding Duration")
    st.dataframe(
        selling_analysis["comparison_table"].rename(columns={
            "timeframe": "Holding Timeframe",
            "date": "Target Date",
            "projected_price": "Predicted Price (₹/Qtl)",
            "pct_delta": "Price Change (%)",
            "storage_cost_per_qtl": "Storage Cost (₹/Qtl)",
            "net_price_per_qtl": "Net Price (₹/Qtl)",
            "total_net_revenue": "Total Expected Revenue (₹)",
            "net_profit_diff": "Net Profit Difference (₹)"
        }),
        use_container_width=True
    )

    st.markdown("---")

    # Spatial Inter-Mandi Arbitrage
    st.markdown("### Market Price Comparison Across Mandis")
    df_all = load_data_from_db(commodity=sel_crop)
    if not df_all.empty:
        arb_df = find_inter_mandi_arbitrage(df_all, commodity=sel_crop, origin_mandi=sel_mandi)
        if not arb_df.empty:
            st.dataframe(arb_df, use_container_width=True)
