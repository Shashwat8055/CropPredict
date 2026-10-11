"""
CropPricePredict - Report Generator Page
Generate summary reports, CSV exports, and prediction summaries with model disclaimers.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from config import CROPS_METADATA, STATE_MANDIS
from data.database import load_data_from_db
from ml.predict import predict_future_crop_prices
from core.advisor import analyze_selling_window

DISCLAIMER_TEXT = (
    "KrishiMandi / CropPricePredict provides statistical estimates based on historical APMC mandi trading records. "
    "Actual market prices may vary depending on local arrivals, weather, state policies, quality grade, and real-time demand. "
    "These figures are intended as trade guidance and planning benchmarks, not as guaranteed contractual prices."
)

def render_reports_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">Mandi Market Reports</h1>
            <div class="brand-subtitle">Generate mandi price summaries, export trade forecast spreadsheets, and review market notes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        sel_crop = st.selectbox("Crop", list(CROPS_METADATA.keys()), index=0)
    with c2:
        sel_state = st.selectbox("State", list(STATE_MANDIS.keys()), index=0)
    with c3:
        sel_mandi = st.selectbox("Market / Mandi", STATE_MANDIS[sel_state]["mandis"], index=0)

    df_hist = load_data_from_db(commodity=sel_crop, market=sel_mandi)
    if df_hist.empty:
        df_hist = load_data_from_db(commodity=sel_crop)

    if df_hist.empty:
        st.warning(f"No records available for {sel_crop}.")
        return

    try:
        forecast_df, sum_dict = predict_future_crop_prices(df_hist, commodity=sel_crop, market=sel_mandi, horizon_days=30)
    except Exception as e:
        st.error(f"Failed to generate prediction report: {e}")
        return

    curr_p = sum_dict["current_price"]
    pred_p = sum_dict["predicted_price"]
    pct_c = sum_dict["pct_change"]
    model_u = sum_dict["model_used"]

    selling_info = analyze_selling_window(forecast_df, commodity=sel_crop, current_price=curr_p)

    st.markdown("### Prediction Summary Report")

    st.markdown(f"""
    <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:20px; border-radius:10px;">
        <h3 style="margin-top:0; color:#064E3B;">Crop Market Report: {sel_crop}</h3>
        <p><b>Target Market:</b> {sel_mandi} ({sel_state})</p>
        <p><b>Report Date:</b> {datetime.now().strftime('%d %B %Y')}</p>
        <hr>
        <table style="width:100%; border-collapse:collapse; line-height: 1.8;">
            <tr><td><b>Current Market Price:</b></td><td>₹{curr_p:,.2f} / Quintal</td></tr>
            <tr><td><b>30-Day Predicted Price:</b></td><td>₹{pred_p:,.2f} / Quintal</td></tr>
            <tr><td><b>Expected Price Change:</b></td><td>{pct_c:+.2f}% ({sum_dict['trend']})</td></tr>
            <tr><td><b>Model Used:</b></td><td>{model_u}</td></tr>
            <tr><td><b>Selling Advice:</b></td><td><b>{selling_info['recommendation']}</b></td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # CSV Download
    report_rows = [{
        "Prediction Date": datetime.now().strftime("%Y-%m-%d"),
        "Commodity": sel_crop,
        "State": sel_state,
        "Market": sel_mandi,
        "Current Price (₹)": curr_p,
        "Predicted Price 30d (₹)": pred_p,
        "Expected Change (%)": pct_c,
        "Trend": sum_dict["trend"],
        "Model Used": model_u,
        "Selling Advice": selling_info["recommendation"]
    }]
    report_df = pd.DataFrame(report_rows)
    csv_bytes = report_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Report (CSV)",
        data=csv_bytes,
        file_name=f"report_{sel_crop}_{sel_mandi}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        type="primary"
    )

    st.markdown("---")
    st.warning(f"**Model Accuracy Disclaimer**: {DISCLAIMER_TEXT}")
