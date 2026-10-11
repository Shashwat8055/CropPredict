"""
CropPricePredict - Market Analysis Page
Provides market analysis, historical price trends, monthly variation, and mandi comparison.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from config import CROPS_METADATA, STATE_MANDIS
from data.database import load_data_from_db
from ui.styles import render_metric_card

def render_market_analysis_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">Market Analysis</h1>
            <div class="brand-subtitle">Analyze historical price trends, monthly variations, and state/market comparisons</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        sel_crop = st.selectbox("Select Crop", list(CROPS_METADATA.keys()), index=0)
    with col2:
        sel_state = st.selectbox("Select State", ["All States"] + list(STATE_MANDIS.keys()), index=0)

    df = load_data_from_db(
        commodity=sel_crop,
        state=sel_state if sel_state != "All States" else None
    )

    if df.empty:
        st.warning(f"No records available for {sel_crop} in {sel_state}.")
        return

    # Calculate Key Statistics
    latest_record = df.sort_values("date").iloc[-1]
    curr_price = float(latest_record["modal_price"])
    avg_price = float(df["modal_price"].mean())
    max_price = float(df["modal_price"].max())
    min_price = float(df["modal_price"].min())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_metric_card("Current Price", f"₹{curr_price:,.2f} / Qtl", f"Date: {latest_record['date'].strftime('%d %b %Y')}", trend="neutral"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric_card("Average Price", f"₹{avg_price:,.2f} / Qtl", "Historical average", trend="blue"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric_card("Highest Price", f"₹{max_price:,.2f} / Qtl", "Highest price recorded", trend="up"), unsafe_allow_html=True)
    with c4:
        st.markdown(render_metric_card("Lowest Price", f"₹{min_price:,.2f} / Qtl", "Lowest price recorded", trend="down"), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # Identify Market with Highest Current & Historical Price
    st.markdown("### Market Price Comparison")
    mandi_summary = df.groupby(["state", "market"]).agg(
        current_price=("modal_price", "last"),
        avg_price=("modal_price", "mean"),
        max_price=("modal_price", "max"),
        min_price=("modal_price", "min")
    ).reset_index().sort_values(by="current_price", ascending=False)

    if not mandi_summary.empty:
        top_mandi_row = mandi_summary.iloc[0]
        st.info(
            f"**Market Summary**: **{top_mandi_row['market']}** ({top_mandi_row['state']}) currently records the highest market price of **₹{top_mandi_row['current_price']:,.2f} / Quintal** for {sel_crop}."
        )

        st.dataframe(
            mandi_summary.rename(columns={
                "market": "Market / Mandi",
                "state": "State",
                "current_price": "Current Price (₹)",
                "avg_price": "Average Price (₹)",
                "max_price": "Highest Price (₹)",
                "min_price": "Lowest Price (₹)"
            }).style.format({
                "Current Price (₹)": "₹{:,.2f}",
                "Average Price (₹)": "₹{:,.2f}",
                "Highest Price (₹)": "₹{:,.2f}",
                "Lowest Price (₹)": "₹{:,.2f}"
            }),
            use_container_width=True
        )

    # Visual Charts
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("### Market-wise Comparison")
        fig_m = px.bar(
            mandi_summary.head(10),
            x="current_price",
            y="market",
            orientation="h",
            color="current_price",
            color_continuous_scale="Viridis",
            labels={"current_price": "Price (₹)", "market": "Mandi"},
            template="plotly_white"
        )
        st.plotly_chart(fig_m, use_container_width=True)

    with col_chart2:
        st.markdown("### Monthly Trend")
        df_m = df.copy()
        df_m["month"] = df_m["date"].dt.strftime("%b")
        df_m["month_num"] = df_m["date"].dt.month
        monthly_df = df_m.groupby(["month_num", "month"])["modal_price"].mean().reset_index().sort_values("month_num")
        fig_mon = px.line(
            monthly_df,
            x="month",
            y="modal_price",
            markers=True,
            title=f"Monthly Average Price Trend for {sel_crop}",
            template="plotly_white"
        )
        st.plotly_chart(fig_mon, use_container_width=True)
