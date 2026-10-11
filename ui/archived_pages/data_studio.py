"""
CropPricePredict - Data Studio & Ingestion Center
Supports CSV/Excel upload with auto-mapping, manual record entry, synthetic live generation, and data export.
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, Any

from config import CROPS_METADATA, STATE_MANDIS
from data.database import (
    load_data_from_db,
    insert_single_record,
    bulk_insert_dataframe,
    get_database_summary
)
from data.generator import generate_live_ticks, generate_crop_market_data

def render_data_studio_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">📥 Data Ingestion & Management Studio</h1>
            <div class="brand-subtitle">Upload New Datasets, Add Daily Mandi Records, Stream Live Ticks & Manage Database</div>
        </div>
        <div>
            <span class="status-pill pill-green">Database Connected</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    summary = get_database_summary()
    st.info(f"📊 **Current Database Status:** **{summary['total_rows']:,}** total price records stored across **{len(summary['crops'])}** crops and **{len(summary['mandis'])}** mandis (Date range: {summary['min_date']} to {summary['max_date']}).")

    tab_upload, tab_manual, tab_generator, tab_explorer = st.tabs([
        "📂 Upload Dataset (CSV / Excel)",
        "✍️ Manual Single Entry Form",
        "⚡ Live Stream Simulator",
        "🔍 Data Explorer & Export"
    ])

    # TAB 1: UPLOAD DATASET
    with tab_upload:
        st.markdown("### 📂 Upload New or Latest Market Data")
        st.markdown("Upload your own custom agricultural price datasets. The system automatically inspects headers and maps columns.")

        uploaded_file = st.file_uploader(
            "Select CSV or Excel file (.csv, .xlsx, .xls)",
            type=["csv", "xlsx", "xls"],
            help="Files should contain columns for Date, Commodity/Crop, Market/Mandi, and Modal Price."
        )

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    raw_df = pd.read_csv(uploaded_file)
                else:
                    raw_df = pd.read_excel(uploaded_file)

                st.success(f"Successfully loaded file `{uploaded_file.name}` with **{len(raw_df):,} rows** and **{len(raw_df.columns)} columns**.")
                
                with st.expander("👁️ Preview Raw Uploaded Data", expanded=True):
                    st.dataframe(raw_df.head(10), use_container_width=True)

                st.markdown("#### 🗺️ Column Mapping Assistant")
                st.caption("Confirm or adjust column matches to align with CropPricePredict schema:")

                c_cols = list(raw_df.columns)
                col1, col2, col3, col4 = st.columns(4)

                # Helper to guess column match
                def guess_col(candidates, default_idx=0):
                    for idx, c in enumerate(c_cols):
                        if any(cand.lower() in c.lower() for cand in candidates):
                            return idx
                    return min(default_idx, len(c_cols) - 1)

                with col1:
                    date_col = st.selectbox("Date Column", c_cols, index=guess_col(["date", "time", "day"], 0))
                    crop_col = st.selectbox("Commodity / Crop", c_cols, index=guess_col(["commodity", "crop", "item"], 1))
                with col2:
                    mandi_col = st.selectbox("Market / Mandi", c_cols, index=guess_col(["market", "mandi", "center", "apmc"], 2))
                    state_col = st.selectbox("State Column", ["-- Auto Fill Default --"] + c_cols, index=guess_col(["state", "region"], 0) + 1 if any("state" in c.lower() for c in c_cols) else 0)
                with col3:
                    price_col = st.selectbox("Modal Price Column", c_cols, index=guess_col(["modal", "price", "avg", "rate"], 3))
                    arrival_col = st.selectbox("Arrivals / Volume Column", ["-- Auto Fill 1000 --"] + c_cols, index=guess_col(["arrival", "qty", "volume"], 0) + 1 if any("arrival" in c.lower() for c in c_cols) else 0)
                with col4:
                    min_p_col = st.selectbox("Min Price (Optional)", ["-- Optional --"] + c_cols, index=0)
                    max_p_col = st.selectbox("Max Price (Optional)", ["-- Optional --"] + c_cols, index=0)

                if st.button("🚀 Process & Ingest Data into System", type="primary", use_container_width=True):
                    with st.spinner("Validating and inserting records..."):
                        mapped_df = pd.DataFrame()
                        mapped_df["date"] = pd.to_datetime(raw_df[date_col]).dt.strftime("%Y-%m-%d")
                        mapped_df["commodity"] = raw_df[crop_col].astype(str)
                        mapped_df["market"] = raw_df[mandi_col].astype(str)
                        mapped_df["modal_price"] = pd.to_numeric(raw_df[price_col], errors="coerce").fillna(2000.0)

                        if state_col != "-- Auto Fill Default --":
                            mapped_df["state"] = raw_df[state_col].astype(str)
                        else:
                            mapped_df["state"] = "General State"

                        if arrival_col != "-- Auto Fill 1000 --":
                            mapped_df["arrivals_quintal"] = pd.to_numeric(raw_df[arrival_col], errors="coerce").fillna(1000.0)
                        else:
                            mapped_df["arrivals_quintal"] = 1000.0

                        if min_p_col != "-- Optional --":
                            mapped_df["min_price"] = pd.to_numeric(raw_df[min_p_col], errors="coerce").fillna(mapped_df["modal_price"] * 0.95)
                        else:
                            mapped_df["min_price"] = mapped_df["modal_price"] * 0.95

                        if max_p_col != "-- Optional --":
                            mapped_df["max_price"] = pd.to_numeric(raw_df[max_p_col], errors="coerce").fillna(mapped_df["modal_price"] * 1.05)
                        else:
                            mapped_df["max_price"] = mapped_df["modal_price"] * 1.05

                        mapped_df["temperature_c"] = 28.0
                        mapped_df["rainfall_mm"] = 0.0
                        mapped_df["fuel_index"] = 105.0

                        inserted_count, msg = bulk_insert_dataframe(mapped_df)
                        st.success(f"🎉 {msg}")
                        st.balloons()
            except Exception as e:
                st.error(f"Error parsing uploaded file: {str(e)}")

    # TAB 2: MANUAL ENTRY FORM
    with tab_manual:
        st.markdown("### ✍️ Record Today's Single Mandi Price")
        st.caption("Quickly input daily price and arrival updates from your local mandi.")

        with st.form("manual_entry_form", clear_on_submit=True):
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                entry_date = st.date_input("Date of Record", value=date.today())
                entry_crop = st.selectbox("Commodity", list(CROPS_METADATA.keys()))
            with m_col2:
                entry_state = st.selectbox("State", list(STATE_MANDIS.keys()))
                entry_mandi = st.selectbox("Market / Mandi", STATE_MANDIS[entry_state]["mandis"])
            with m_col3:
                entry_modal = st.number_input("Modal Price (₹/Quintal)", min_value=100.0, max_value=50000.0, value=2350.0, step=10.0)
                entry_arrival = st.number_input("Arrival Quantity (Quintals)", min_value=0.0, max_value=100000.0, value=1500.0, step=50.0)

            with st.expander("🌦️ Weather & Micro Indicators (Optional)"):
                w_col1, w_col2, w_col3 = st.columns(3)
                with w_col1:
                    entry_temp = st.number_input("Temperature (°C)", value=29.5, step=0.5)
                with w_col2:
                    entry_rain = st.number_input("Rainfall (mm)", value=0.0, step=0.5)
                with w_col3:
                    entry_fuel = st.number_input("Fuel/Diesel Index", value=112.0, step=1.0)

            submitted = st.form_submit_button("💾 Save Record to Database", type="primary", use_container_width=True)
            if submitted:
                record = {
                    "date": entry_date.strftime("%Y-%m-%d"),
                    "commodity": entry_crop,
                    "state": entry_state,
                    "market": entry_mandi,
                    "modal_price": entry_modal,
                    "min_price": entry_modal * 0.95,
                    "max_price": entry_modal * 1.05,
                    "arrivals_quintal": entry_arrival,
                    "temperature_c": entry_temp,
                    "rainfall_mm": entry_rain,
                    "fuel_index": entry_fuel
                }
                success, msg = insert_single_record(record)
                if success:
                    st.success(f"✅ Record for {entry_crop} on {entry_date} successfully added to database!")
                else:
                    st.error(f"❌ {msg}")

    # TAB 3: LIVE STREAM SIMULATOR
    with tab_generator:
        st.markdown("### ⚡ Live Streaming & Synthetic Tick Simulator")
        st.caption("Simulate continuous real-time market arrivals and price ticks appending to latest date.")

        g_col1, g_col2, g_col3 = st.columns(3)
        with g_col1:
            sim_crop = st.selectbox("Target Commodity", list(CROPS_METADATA.keys()), key="sim_crop")
        with g_col2:
            sim_state = st.selectbox("Target State", list(STATE_MANDIS.keys()), key="sim_state")
            sim_mandi = st.selectbox("Target Mandi", STATE_MANDIS[sim_state]["mandis"], key="sim_mandi")
        with g_col3:
            sim_days = st.slider("Generate Ticks (Days)", min_value=1, max_value=30, value=7)

        if st.button("⚡ Generate & Append Live Market Ticks", type="primary", use_container_width=True):
            with st.spinner("Simulating live mandi arrivals and market ticks..."):
                existing_df = load_data_from_db(commodity=sim_crop, market=sim_mandi)
                ticks_df = generate_live_ticks(
                    df_existing=existing_df,
                    days_ahead=sim_days,
                    commodity=sim_crop,
                    state=sim_state,
                    market=sim_mandi
                )
                inserted, msg = bulk_insert_dataframe(ticks_df)
                st.success(f"🎉 Generated and appended {inserted} new live market days for {sim_crop} in {sim_mandi}!")
                st.dataframe(ticks_df, use_container_width=True)

    # TAB 4: DATA EXPLORER & EXPORT
    with tab_explorer:
        st.markdown("### 🔍 Agricultural Database Explorer")
        
        e_col1, e_col2, e_col3 = st.columns(3)
        with e_col1:
            exp_crop = st.selectbox("Filter Commodity", ["All Crops"] + list(CROPS_METADATA.keys()), key="exp_crop")
        with e_col2:
            exp_state = st.selectbox("Filter State", ["All States"] + list(STATE_MANDIS.keys()), key="exp_state")
        with e_col3:
            limit_rows = st.select_slider("Limit Rows Displayed", options=[100, 500, 1000, 5000, 20000], value=500)

        df_exp = load_data_from_db(
            commodity=exp_crop if exp_crop != "All Crops" else None,
            state=exp_state if exp_state != "All States" else None
        )

        if not df_exp.empty:
            st.markdown(f"**Found {len(df_exp):,} matching records** (Showing top {min(len(df_exp), limit_rows)}):")
            st.dataframe(df_exp.tail(limit_rows), use_container_width=True, height=380)

            # Export button
            csv_exp = df_exp.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Filtered Database to CSV",
                data=csv_exp,
                file_name=f"market_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No records match the selected explorer filters.")
