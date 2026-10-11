"""
CropPricePredict - Main Dashboard Page
Displays dataset summary, market KPIs, and price trend charts.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from config import CROPS_METADATA, STATE_MANDIS
from data.database import load_data_from_db, get_database_summary
from ui.styles import render_metric_card

def render_dashboard_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">Crop Price Dashboard</h1>
            <div class="brand-subtitle">Overview of market prices, historical dataset records, and price trends</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    summary_info = get_database_summary()
    
    # Global Filters Bar
    with st.expander("Filter Dashboard Data", expanded=True):
        col_crop, col_state, col_mandi = st.columns(3)
        with col_crop:
            crops_list = ["All Crops"] + summary_info.get("crops", list(CROPS_METADATA.keys()))
            selected_crop = st.selectbox("Selected Crop", crops_list, index=0)
        with col_state:
            states_list = ["All States"] + summary_info.get("states", list(STATE_MANDIS.keys()))
            selected_state = st.selectbox("Selected State", states_list, index=0)
        with col_mandi:
            if selected_state != "All States" and selected_state in STATE_MANDIS:
                mandis_list = ["All Mandis"] + STATE_MANDIS[selected_state]["mandis"]
            else:
                mandis_list = ["All Mandis"] + summary_info.get("mandis", [])
            selected_mandi = st.selectbox("Selected Market/Mandi", mandis_list, index=0)

    # Load filtered dataset
    df = load_data_from_db(
        commodity=selected_crop if selected_crop != "All Crops" else None,
        state=selected_state if selected_state != "All States" else None,
        market=selected_mandi if selected_mandi != "All Mandis" else None
    )

    if df.empty:
        st.warning("No market records found for the selected filters.")
        return

    # Calculate Summary KPIs
    total_crops = df["commodity"].nunique() if "commodity" in df.columns else len(CROPS_METADATA)
    record_count = len(df)
    latest_price = float(df["modal_price"].iloc[-1]) if "modal_price" in df.columns else 0.0
    avg_price = float(df["modal_price"].mean()) if "modal_price" in df.columns else 0.0
    highest_price = float(df["modal_price"].max()) if "modal_price" in df.columns else 0.0
    lowest_price = float(df["modal_price"].min()) if "modal_price" in df.columns else 0.0

    # KPI Metric Cards Grid
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
    with kpi1:
        st.markdown(render_metric_card("Total Crops", f"{total_crops}", "Active crops", trend="neutral"), unsafe_allow_html=True)
    with kpi2:
        st.markdown(render_metric_card("Dataset Records", f"{record_count:,}", "Total rows", trend="neutral"), unsafe_allow_html=True)
    with kpi3:
        st.markdown(render_metric_card("Latest Price", f"₹{latest_price:,.0f}", "Current price", trend="up"), unsafe_allow_html=True)
    with kpi4:
        st.markdown(render_metric_card("Average Price", f"₹{avg_price:,.0f}", "Mean price", trend="blue"), unsafe_allow_html=True)
    with kpi5:
        st.markdown(render_metric_card("Highest Price", f"₹{highest_price:,.0f}", "Max historical", trend="up"), unsafe_allow_html=True)
    with kpi6:
        st.markdown(render_metric_card("Lowest Price", f"₹{lowest_price:,.0f}", "Min historical", trend="down"), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # Charts Grid
    row1_left, row1_right = st.columns([1.6, 1])

    with row1_left:
        st.markdown("### Price Trend Over Time")
        if "date" in df.columns and "modal_price" in df.columns:
            trend_df = df.groupby(["date", "commodity"])["modal_price"].mean().reset_index()
            fig_trend = px.line(
                trend_df,
                x="date",
                y="modal_price",
                color="commodity" if selected_crop == "All Crops" else None,
                labels={"modal_price": "Price (₹ / Quintal)", "date": "Date"},
                template="plotly_white",
                height=380
            )
            fig_trend.update_layout(margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified")
            st.plotly_chart(fig_trend, use_container_width=True)

    with row1_right:
        st.markdown("### Crop-wise Average Price")
        if "commodity" in df.columns and "modal_price" in df.columns:
            crop_avg = df.groupby("commodity")["modal_price"].mean().reset_index().sort_values(by="modal_price", ascending=False)
            fig_crop = px.bar(
                crop_avg,
                x="modal_price",
                y="commodity",
                orientation="h",
                color="modal_price",
                color_continuous_scale="Greens",
                labels={"modal_price": "Avg Price (₹)", "commodity": "Crop"},
                template="plotly_white",
                height=380
            )
            fig_crop.update_layout(margin=dict(l=20, r=20, t=20, b=20), coloraxis_showscale=False)
            st.plotly_chart(fig_crop, use_container_width=True)

    row2_left, row2_right = st.columns(2)

    with row2_left:
        st.markdown("### Market-wise Average Price")
        if "market" in df.columns and "modal_price" in df.columns:
            mandi_avg = df.groupby("market")["modal_price"].mean().reset_index().sort_values(by="modal_price", ascending=False).head(10)
            fig_mandi = px.bar(
                mandi_avg,
                x="market",
                y="modal_price",
                color="modal_price",
                color_continuous_scale="Teal",
                labels={"modal_price": "Avg Price (₹)", "market": "Mandi"},
                template="plotly_white",
                height=340
            )
            fig_mandi.update_layout(margin=dict(l=20, r=20, t=20, b=20), coloraxis_showscale=False)
            st.plotly_chart(fig_mandi, use_container_width=True)

    with row2_right:
        st.markdown("### Monthly Price Variation")
        if "date" in df.columns and "modal_price" in df.columns:
            df_m = df.copy()
            df_m["month_num"] = df_m["date"].dt.month
            df_m["month_name"] = df_m["date"].dt.strftime("%b")
            monthly_avg = df_m.groupby(["month_num", "month_name"])["modal_price"].mean().reset_index().sort_values(by="month_num")
            fig_month = px.line(
                monthly_avg,
                x="month_name",
                y="modal_price",
                markers=True,
                labels={"modal_price": "Avg Price (₹)", "month_name": "Month"},
                template="plotly_white",
                height=340
            )
            fig_month.update_traces(line_color="#0284C7", line_width=3, marker_size=8)
            fig_month.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_month, use_container_width=True)
