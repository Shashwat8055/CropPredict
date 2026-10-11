"""
CropPricePredict - Market Intelligence & Selling Advisor Studio
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from config import CROPS_METADATA, STATE_MANDIS
from data.database import load_data_from_db
from core.feature_engineering import build_crop_features
from core.models import CropPriceModel
from core.predictor import MultiHorizonPredictor
from core.advisor import analyze_selling_window, find_inter_mandi_arbitrage, assess_market_risk
from ui.styles import render_metric_card

def render_market_intelligence_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">🧠 Market Intelligence & Selling Advisor</h1>
            <div class="brand-subtitle">Optimal Timing Optimizer, Inter-Mandi Price Arbitrage & Volatility Sentinel</div>
        </div>
        <div>
            <span class="status-pill pill-amber">Decision Support</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_selling, tab_arbitrage, tab_risk = st.tabs([
        "💰 Optimal Selling Window ('Sell Now vs. Hold')",
        "🚚 Inter-Mandi Price Arbitrage Finder",
        "🛡️ Price Risk & Volatility Sentinel"
    ])

    # TAB 1: SELLING WINDOW ADVISOR
    with tab_selling:
        st.markdown("### 💰 Profit Maximization: Should You Sell Now or Hold?")
        st.caption("Evaluates projected future price growth against warehousing/storage costs to maximize your net take-home profit.")

        c_col1, c_col2, c_col3, c_col4 = st.columns(4)
        with c_col1:
            sel_crop = st.selectbox("Crop Commodity", list(CROPS_METADATA.keys()), key="adv_crop")
        with c_col2:
            sel_state = st.selectbox("Your State", list(STATE_MANDIS.keys()), key="adv_state")
            sel_mandi = st.selectbox("Your Primary Mandi", STATE_MANDIS[sel_state]["mandis"], key="adv_mandi")
        with c_col3:
            crop_qty = st.number_input("Your Crop Quantity (Quintals)", min_value=1.0, max_value=10000.0, value=100.0, step=10.0)
        with c_col4:
            default_storage = CROPS_METADATA[sel_crop]["storage_cost_per_month_quintal"]
            storage_cost = st.number_input("Storage Cost (₹/Qtl/Month)", min_value=0.0, max_value=500.0, value=float(default_storage), step=2.0)

        # Run forecast pipeline for 90 days to feed advisor
        hist_df = load_data_from_db(commodity=sel_crop, market=sel_mandi)
        if hist_df.empty:
            hist_df = load_data_from_db(commodity=sel_crop)

        if not hist_df.empty:
            featured_df, feat_cols = build_crop_features(hist_df, commodity=sel_crop, market=sel_mandi)
            model = CropPriceModel("XGBoost Regressor")
            model.fit(featured_df[feat_cols], featured_df["modal_price"])
            predictor = MultiHorizonPredictor(model, feat_cols)
            
            forecast_df = predictor.forecast(
                historical_df=hist_df,
                horizon_days=90,
                commodity=sel_crop,
                market=sel_mandi,
                state=sel_state
            )

            current_p = hist_df["modal_price"].iloc[-1]
            adv_res = analyze_selling_window(
                forecast_df=forecast_df,
                commodity=sel_crop,
                current_price=current_p,
                quantity_quintals=crop_qty,
                custom_storage_cost_per_month=storage_cost
            )

            # Recommendation Box
            is_sell = "SELL NOW" in adv_res["recommendation"]
            badge_cls = "badge-sell-now" if is_sell else "badge-hold"
            st.markdown(f"""
            <div class="rec-card">
                <span class="rec-badge {badge_cls}">Recommendation: {adv_res['recommendation']}</span>
                <h3 style="margin-top:0; color:white; font-size:22px;">Optimal Selling Window: {adv_res['best_timeframe']} ({adv_res['best_date']})</h3>
                <p style="color:#CBD5E1; font-size:15px; margin-bottom:0;">{adv_res['reasoning']}</p>
            </div>
            """, unsafe_allow_html=True)

            # Comparison Visualizer
            comp_table = adv_res["comparison_table"]
            
            fig_adv = go.Figure()
            fig_adv.add_trace(go.Bar(
                x=comp_table["timeframe"],
                y=comp_table["total_net_revenue"],
                text=comp_table["total_net_revenue"].map("₹{:,.0f}".format),
                textposition="auto",
                marker_color=["#10B981" if t == adv_res["best_timeframe"] else "#64748B" for t in comp_table["timeframe"]],
                name="Net Revenue"
            ))
            fig_adv.update_layout(
                title=f"Net Realized Revenue Comparison Across Holding Periods ({crop_qty:.0f} Quintals of {sel_crop})",
                yaxis_title="Total Net Revenue (₹)",
                template="plotly_white",
                height=380,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_adv, use_container_width=True)

            # Details Table
            st.markdown("#### 📋 Holding Period Breakdown Table")
            display_comp = comp_table.copy()
            display_comp["Projected Price"] = display_comp["projected_price"].map("₹{:,.2f}".format)
            display_comp["Storage Cost"] = display_comp["storage_cost_per_qtl"].map("₹{:,.2f}".format)
            display_comp["Net Price/Qtl"] = display_comp["net_price_per_qtl"].map("₹{:,.2f}".format)
            display_comp["Total Net Revenue"] = display_comp["total_net_revenue"].map("₹{:,.2f}".format)
            display_comp["Net Profit vs Today"] = display_comp["net_profit_diff"].map("₹{:,.2f}".format)

            st.dataframe(
                display_comp[["timeframe", "date", "Projected Price", "Storage Cost", "Net Price/Qtl", "Total Net Revenue", "Net Profit vs Today"]],
                use_container_width=True
            )

    # TAB 2: INTER-MANDI ARBITRAGE
    with tab_arbitrage:
        st.markdown("### 🚚 Spatial Price Arbitrage & Mandi Finder")
        st.caption("Discover higher-paying nearby mandis and calculate whether transporting your harvest yields net profit after diesel/freight costs.")

        arb_col1, arb_col2, arb_col3 = st.columns(3)
        with arb_col1:
            arb_crop = st.selectbox("Commodity", list(CROPS_METADATA.keys()), key="arb_crop")
        with arb_col2:
            arb_state = st.selectbox("Your State", list(STATE_MANDIS.keys()), key="arb_state")
            arb_mandi = st.selectbox("Origin Mandi", STATE_MANDIS[arb_state]["mandis"], key="arb_mandi")
        with arb_col3:
            transport_rate = st.number_input("Freight Rate (₹ / Quintal / 10 km)", min_value=0.5, max_value=20.0, value=2.5, step=0.5)

        all_latest_df = load_data_from_db(commodity=arb_crop)
        if not all_latest_df.empty:
            arb_results = find_inter_mandi_arbitrage(
                df_latest=all_latest_df,
                commodity=arb_crop,
                origin_mandi=arb_mandi,
                transport_rate_per_km_qtl=transport_rate / 10.0
            )

            if not arb_results.empty:
                # Top Arbitrage Highlight
                best_arb = arb_results.iloc[0]
                if best_arb["Net Profit Margin (₹/Qtl)"] > 20 and best_arb["Market"] != arb_mandi:
                    st.success(f"💡 **Top Arbitrage Opportunity Found:** Transporting {arb_crop} to **{best_arb['Market']} ({best_arb['State']})** yields **+₹{best_arb['Net Profit Margin (₹/Qtl)']:.2f} / Quintal** net gain after deducting ₹{best_arb['Transport Cost (₹/Qtl)']:.2f}/Qtl transport cost for {best_arb['Est Distance (km)']} km distance.")
                else:
                    st.info(f"Your local market ({arb_mandi}) is currently offering competitive rates. Inter-mandi freight costs outweigh price spreads for nearby markets.")

                st.dataframe(arb_results, use_container_width=True, height=360)
            else:
                st.info("No comparative mandi data found.")

    # TAB 3: PRICE RISK & VOLATILITY SENTINEL
    with tab_risk:
        st.markdown("### 🛡️ Volatility Sentinel & Supply Shock Monitor")
        
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            risk_crop = st.selectbox("Commodity to Audit", list(CROPS_METADATA.keys()), key="risk_crop")
        with r_col2:
            risk_mandi = st.selectbox("Mandi Center", ["All Mandis"] + [m for s in STATE_MANDIS.values() for m in s["mandis"]], key="risk_mandi")

        risk_df = load_data_from_db(commodity=risk_crop, market=risk_mandi if risk_mandi != "All Mandis" else None)
        if not risk_df.empty:
            risk_info = assess_market_risk(risk_df, commodity=risk_crop)

            rk1, rk2, rk3 = st.columns(3)
            with rk1:
                st.markdown(render_metric_card(
                    "Market Risk Rating",
                    risk_info["risk_level"],
                    f"Risk Score: {risk_info['risk_score']} / 100",
                    trend="up" if risk_info["risk_score"] < 40 else ("down" if risk_info["risk_score"] > 70 else "amber")
                ), unsafe_allow_html=True)
            with rk2:
                st.markdown(render_metric_card(
                    "30-Day Price Volatility",
                    f"{risk_info['volatility_pct']:.1f}%",
                    "Annualized 30-day standard deviation",
                    trend="neutral"
                ), unsafe_allow_html=True)
            with rk3:
                st.markdown(render_metric_card(
                    "30-Day Net Price Drift",
                    f"{risk_info['price_change_30d_pct']:+.1f}%",
                    "Net price trajectory over 30 days",
                    trend="up" if risk_info['price_change_30d_pct'] >= 0 else "down"
                ), unsafe_allow_html=True)

            st.markdown("#### 🚨 Market Signals & Alerts")
            for alert in risk_info["alerts"]:
                st.markdown(f"- {alert}")
