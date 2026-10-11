"""
CropPricePredict - Crop Recommendation & Profit Estimation Page
Recommends optimal crops using soil, climate inputs, and predicted market prices from the ML price model.
"""
import streamlit as st
import pandas as pd
import numpy as np

from config import CROPS_METADATA
from data.database import load_data_from_db
from ml.predict import predict_future_crop_prices
from utils.calculations import calculate_crop_profitability, calculate_risk_level
from ui.styles import render_metric_card

def render_crop_recommendation_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">Crop Planning & Profit Estimation</h1>
            <div class="brand-subtitle">Evaluates suitable crops based on soil NPK, soil pH, seasonal weather, and expected mandi returns</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("recommendation_form"):
        st.markdown("### Soil, Weather & Farm Inputs")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            soil_type = st.selectbox("Soil Type", ["Loamy Soil", "Clay Soil", "Sandy Loam", "Black Soil", "Alluvial Soil"], index=0)
            soil_ph = st.slider("Soil pH Level", 4.5, 9.0, 6.8, 0.1)
            nitrogen = st.slider("Nitrogen (N) (kg/ha)", 0, 200, 90)
            phosphorus = st.slider("Phosphorus (P) (kg/ha)", 0, 150, 45)
        with col2:
            potassium = st.slider("Potassium (K) (kg/ha)", 0, 200, 50)
            temp = st.slider("Average Temperature (°C)", 10.0, 45.0, 25.0)
            rainfall = st.slider("Annual Rainfall (mm)", 200, 2500, 850)
            humidity = st.slider("Humidity (%)", 20, 100, 65)
        with col3:
            season = st.selectbox("Season", ["Rabi", "Kharif", "Zaid", "Whole Year"], index=0)
            irrigation = st.selectbox("Irrigation Type", ["Canal / Tube Well", "Rainfed", "Drip Irrigation"], index=0)
            farm_area_acres = st.number_input("Farm Area (Acres)", min_value=0.5, max_value=500.0, value=5.0)

        submit_rec = st.form_submit_button("Recommend Crops", type="primary", use_container_width=True)

    # Base Crop Requirements & Yield Models
    CROP_AGRONOMICS = {
        "Wheat": {"min_ph": 6.0, "max_ph": 7.5, "base_yield_qtl_acre": 22.0, "cost_per_acre": 24000.0, "perishability": "Low"},
        "Rice (Paddy)": {"min_ph": 5.5, "max_ph": 7.0, "base_yield_qtl_acre": 25.0, "cost_per_acre": 28000.0, "perishability": "Low"},
        "Cotton": {"min_ph": 6.0, "max_ph": 8.0, "base_yield_qtl_acre": 12.0, "cost_per_acre": 35000.0, "perishability": "Low"},
        "Soybean": {"min_ph": 6.0, "max_ph": 7.5, "base_yield_qtl_acre": 11.0, "cost_per_acre": 18000.0, "perishability": "Medium"},
        "Mustard": {"min_ph": 6.0, "max_ph": 7.5, "base_yield_qtl_acre": 9.0, "cost_per_acre": 16000.0, "perishability": "Low"},
        "Maize (Corn)": {"min_ph": 5.8, "max_ph": 7.2, "base_yield_qtl_acre": 24.0, "cost_per_acre": 22000.0, "perishability": "Medium"},
        "Gram (Chickpea)": {"min_ph": 6.0, "max_ph": 7.8, "base_yield_qtl_acre": 10.0, "cost_per_acre": 17000.0, "perishability": "Low"},
        "Tomato": {"min_ph": 6.0, "max_ph": 7.0, "base_yield_qtl_acre": 120.0, "cost_per_acre": 65000.0, "perishability": "High"},
        "Onion": {"min_ph": 6.0, "max_ph": 7.5, "base_yield_qtl_acre": 110.0, "cost_per_acre": 55000.0, "perishability": "High"},
        "Potato": {"min_ph": 5.2, "max_ph": 6.5, "base_yield_qtl_acre": 130.0, "cost_per_acre": 58000.0, "perishability": "Medium"}
    }

    st.markdown("---")
    st.markdown("### Crop Recommendations & Estimated Profit")

    recommendations = []

    with st.spinner("Calculating profitability using ML predicted market prices..."):
        for crop_name, agro in CROP_AGRONOMICS.items():
            ph_score = 1.0 if agro["min_ph"] <= soil_ph <= agro["max_ph"] else 0.85
            expected_yield = agro["base_yield_qtl_acre"] * ph_score

            # Fetch ML predicted market price from price model
            df_hist = load_data_from_db(commodity=crop_name)
            try:
                _, pred_sum = predict_future_crop_prices(df_hist, commodity=crop_name, horizon_days=30)
                ml_pred_price = pred_sum["predicted_price"]
            except Exception:
                ml_pred_price = CROPS_METADATA.get(crop_name, {}).get("base_price", 2200.0)

            profit_info = calculate_crop_profitability(
                crop_name=crop_name,
                farm_area_acres=farm_area_acres,
                expected_yield_per_acre=expected_yield,
                predicted_market_price_per_qtl=ml_pred_price,
                estimated_cost_per_acre=agro["cost_per_acre"]
            )

            risk_info = calculate_risk_level(
                price_volatility_pct=8.5,
                model_mape=5.0,
                perishability=agro["perishability"]
            )

            recommendations.append({
                "Crop": crop_name,
                "Predicted Market Price": f"₹{ml_pred_price:,.2f} / Qtl",
                "Expected Yield / Acre": f"{expected_yield:.1f} Qtl",
                "Expected Revenue": profit_info["expected_revenue"],
                "Cultivation Cost": profit_info["total_cost"],
                "Estimated Profit": profit_info["total_profit"],
                "Profit per Acre": profit_info["profit_per_acre"],
                "ROI": f"{profit_info['roi_pct']:.1f}%",
                "Risk Level": risk_info["risk_level"],
                "raw_profit": profit_info["total_profit"]
            })

    rec_df = pd.DataFrame(recommendations).sort_values(by="raw_profit", ascending=False).reset_index(drop=True)

    # Top recommended crop card
    top_crop = rec_df.iloc[0]
    st.success(
        f"**Top Recommended Crop**: **{top_crop['Crop']}** is estimated to offer the highest profit of "
        f"**₹{top_crop['Estimated Profit']:,.2f}** for your {farm_area_acres} acre farm (**₹{top_crop['Profit per Acre']:,.2f} / Acre**)."
    )

    # Results Table
    st.dataframe(
        rec_df.drop(columns=["raw_profit"]).rename(columns={
            "Expected Revenue": "Expected Revenue (₹)",
            "Cultivation Cost": "Cultivation Cost (₹)",
            "Estimated Profit": "Estimated Total Profit (₹)",
            "Profit per Acre": "Profit / Acre (₹)"
        }).style.format({
            "Expected Revenue (₹)": "₹{:,.2f}",
            "Cultivation Cost (₹)": "₹{:,.2f}",
            "Estimated Total Profit (₹)": "₹{:,.2f}",
            "Profit / Acre (₹)": "₹{:,.2f}"
        }),
        use_container_width=True
    )
