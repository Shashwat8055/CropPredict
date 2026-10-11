"""
CropPricePredict - Dashboard Page (Live Market Overview)
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from config import CROPS_METADATA, STATE_MANDIS
from data.database import load_data_from_db, get_database_summary
from ui.styles import render_metric_card

def render_dashboard_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">🌾 CropPricePredict™ Dashboard</h1>
            <div class="brand-subtitle">Real-time Agricultural Market Intelligence, Mandi Inflows & Price Action</div>
        </div>
        <div style="text-align: right;">
            <span class="status-pill pill-green">● Live Market Active</span>
            <div style="font-size: 11px; opacity: 0.85; margin-top: 4px;">Updated: {}</div>
        </div>
    </div>
    """.format(datetime.now().strftime("%d %b %Y, %I:%M %p")), unsafe_allow_html=True)

    summary = get_database_summary()
    total_records = summary["total_rows"]
    all_crops = summary["crops"]
    all_states = summary["states"]

    if total_records == 0:
        st.warning("No records found in database. Please navigate to the Data Studio to seed or upload data.")
        return

    # Filter Bar
    col_c, col_s, col_m = st.columns([1.2, 1, 1])
    with col_c:
        selected_crop = st.selectbox("🎯 Highlight Commodity", ["All Crops"] + all_crops, index=0)
    with col_s:
        selected_state = st.selectbox("📍 Select State", ["All States"] + all_states, index=0)
    with col_m:
        date_filter = st.selectbox("📅 Time Window", ["Last 30 Days", "Last 90 Days", "Last 1 Year", "All History"], index=1)

    # Date range parsing
    end_dt = datetime.now()
    if date_filter == "Last 30 Days":
        start_dt = end_dt - timedelta(days=30)
    elif date_filter == "Last 90 Days":
        start_dt = end_dt - timedelta(days=90)
    elif date_filter == "Last 1 Year":
        start_dt = end_dt - timedelta(days=365)
    else:
        start_dt = None

    start_str = start_dt.strftime("%Y-%m-%d") if start_dt else None
    df = load_data_from_db(
        commodity=selected_crop if selected_crop != "All Crops" else None,
        state=selected_state if selected_state != "All States" else None,
        start_date=start_str
    )

    if df.empty:
        st.info("No records matching the selected filter criteria.")
        return

    # Top KPI Metrics Cards
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date]
    prev_date = df[df["date"] < latest_date]["date"].max() if len(df["date"].unique()) > 1 else latest_date
    prev_df = df[df["date"] == prev_date]

    avg_modal_today = latest_df["modal_price"].mean() if not latest_df.empty else 0.0
    avg_modal_prev = prev_df["modal_price"].mean() if not prev_df.empty else avg_modal_today
    price_pct_change = ((avg_modal_today - avg_modal_prev) / (avg_modal_prev + 1e-5)) * 100.0

    total_arrivals_today = latest_df["arrivals_quintal"].sum() if "arrivals_quintal" in latest_df.columns else 0.0
    total_arrivals_prev = prev_df["arrivals_quintal"].sum() if "arrivals_quintal" in prev_df.columns else total_arrivals_today
    arrival_pct_change = ((total_arrivals_today - total_arrivals_prev) / (total_arrivals_prev + 1e-5)) * 100.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(render_metric_card(
            "Avg Modal Price",
            f"₹{avg_modal_today:,.1f} / Qtl",
            f"{price_pct_change:+.2f}% vs prev session",
            trend="up" if price_pct_change >= 0 else "down"
        ), unsafe_allow_html=True)
    with kpi2:
        st.markdown(render_metric_card(
            "Daily Mandi Arrivals",
            f"{total_arrivals_today:,.0f} Qtl",
            f"{arrival_pct_change:+.1f}% volume shift",
            trend="blue"
        ), unsafe_allow_html=True)
    with kpi3:
        tracked_commodities = len(df["commodity"].unique())
        st.markdown(render_metric_card(
            "Tracked Commodities",
            f"{tracked_commodities} Crops",
            f"Across {len(df['market'].unique())} APMC Mandis",
            trend="neutral"
        ), unsafe_allow_html=True)
    with kpi4:
        st.markdown(render_metric_card(
            "Database Records",
            f"{total_records:,}",
            f"History: {summary['min_date']} → {summary['max_date']}",
            trend="up"
        ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Interactive Trend Charts
    tab_price, tab_arrival, tab_mandi_comp = st.tabs([
        "📈 Price Trajectory & Volatility",
        "🚜 Arrival Volumes & Elasticity",
        "🏛️ Mandi Price Comparison Heatmap"
    ])

    with tab_price:
        # Group by date and commodity
        time_series = df.groupby(["date", "commodity"])["modal_price"].mean().reset_index()
        fig_price = px.line(
            time_series,
            x="date",
            y="modal_price",
            color="commodity",
            title="Daily Modal Market Price (₹/Quintal) Across Commodities",
            labels={"modal_price": "Price (₹/Quintal)", "date": "Date", "commodity": "Crop"},
            template="plotly_white"
        )
        fig_price.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=50, b=20),
            height=420
        )
        st.plotly_chart(fig_price, use_container_width=True)

    with tab_arrival:
        if "arrivals_quintal" in df.columns:
            arrival_series = df.groupby(["date", "commodity"])["arrivals_quintal"].sum().reset_index()
            fig_arr = px.bar(
                arrival_series,
                x="date",
                y="arrivals_quintal",
                color="commodity",
                title="Daily Mandi Inflow Volume (Quintals)",
                labels={"arrivals_quintal": "Arrivals (Qtl)", "date": "Date"},
                template="plotly_white"
            )
            fig_arr.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=50, b=20),
                height=420
            )
            st.plotly_chart(fig_arr, use_container_width=True)

    with tab_mandi_comp:
        mandi_latest = df[df["date"] >= (latest_date - pd.Timedelta(days=7))].groupby(["market", "commodity"])["modal_price"].mean().reset_index()
        pivot_mandi = mandi_latest.pivot(index="market", columns="commodity", values="modal_price")
        if not pivot_mandi.empty:
            fig_heat = px.imshow(
                pivot_mandi,
                labels=dict(x="Commodity", y="Mandi Market", color="Price (₹/Qtl)"),
                title="Recent 7-Day Average Price Across Mandis & Crops",
                color_continuous_scale="Viridis",
                aspect="auto"
            )
            fig_heat.update_layout(height=480, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Insufficient data for heatmap.")

    # Recent Market Tickers & Gainers / Losers
    st.markdown("<div class='section-title'>⚡ Market Movers & Recent Price Tickers</div>", unsafe_allow_html=True)
    c_gain, c_loss = st.columns(2)

    # Compute 7-day change per crop
    crop_changes = []
    for c in all_crops:
        c_sub = df[df["commodity"] == c].sort_values("date")
        if len(c_sub) >= 7:
            p_now = c_sub["modal_price"].iloc[-1]
            p_7d = c_sub["modal_price"].iloc[-7]
            pct_7d = ((p_now - p_7d) / (p_7d + 1e-5)) * 100.0
            crop_changes.append({
                "Crop": c,
                "Current Price": f"₹{p_now:,.2f}",
                "7-Day Change": pct_7d,
                "Raw Price": p_now
            })

    if crop_changes:
        ch_df = pd.DataFrame(crop_changes).sort_values(by="7-Day Change", ascending=False)
        with c_gain:
            st.markdown("##### 🚀 Top Bullish Movers (7-Day Gainers)")
            top_gainers = ch_df.head(5)
            for _, r in top_gainers.iterrows():
                icon = CROPS_METADATA.get(r["Crop"], {}).get("icon", "🌱")
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; background:#F0FDF4; border-left:4px solid #16A34A; padding:10px 14px; margin-bottom:8px; border-radius:6px;">
                    <div><b>{icon} {r['Crop']}</b> &nbsp; <span style="font-size:12px; color:#4B5563;">{r['Current Price']}/Qtl</span></div>
                    <div style="font-weight:700; color:#16A34A;">+{r['7-Day Change']:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        with c_loss:
            st.markdown("##### 📉 Top Harvest Inflow / Price Drops (7-Day)")
            top_losers = ch_df.tail(5).iloc[::-1]
            for _, r in top_losers.iterrows():
                icon = CROPS_METADATA.get(r["Crop"], {}).get("icon", "🌱")
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; background:#FEF2F2; border-left:4px solid #DC2626; padding:10px 14px; margin-bottom:8px; border-radius:6px;">
                    <div><b>{icon} {r['Crop']}</b> &nbsp; <span style="font-size:12px; color:#4B5563;">{r['Current Price']}/Qtl</span></div>
                    <div style="font-weight:700; color:#DC2626;">{r['7-Day Change']:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
