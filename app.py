"""
KrishiMandi / CropPricePredict - Agricultural Commodity Trade & Price Intelligence System
B.Tech Final Year Engineering Project

Features:
- Role-based Dashboards: Farmer/Seller, Trader/Buyer, and Super Administrator (@super.com)
- Strict Data Isolation: Buyers cannot alter sellers' listings; sellers cannot alter buyers' orders
- Deep Oversight: Super Admin can monitor all data and live buyer-seller interactions
- Statistical APMC Mandi Price Forecasting & Storage Advisory
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root directory to python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from styles import get_custom_css, render_role_badge
except Exception:
    from ui.styles import get_custom_css, render_role_badge
from data.marketplace_db import init_marketplace_tables, is_superadmin_email
from views.auth import render_login_page
from views.seller_portal import render_seller_portal
from views.buyer_portal import render_buyer_portal
from views.superadmin_portal import render_superadmin_portal
from views.dashboard import render_dashboard_page
from views.prediction import render_prediction_page
from views.market_analysis import render_market_analysis_page
from views.crop_recommendation import render_crop_recommendation_page
from views.selling_advisor import render_selling_advisor_page
from views.data_management import render_data_management_page
from views.model_management import render_model_management_page
from views.reports import render_reports_page
from views.ml_studio import render_ml_studio_page

# Page Configuration
st.set_page_config(
    page_title="KrishiMandi - Agricultural Trade & Mandi Price Portal",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply CSS Theme
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize Marketplace DB & Session State
init_marketplace_tables()

if "user" not in st.session_state:
    st.session_state["user"] = None

# If not authenticated, render Login / Register screen
if st.session_state["user"] is None:
    with st.sidebar:
        st.markdown("""
        <div style="padding: 10px 0 16px 0;">
            <div style="font-size: 20px; font-weight: 800; color: #164e3b;">🌾 KrishiMandi</div>
            <div style="font-size: 12px; color: #64748b; font-weight: 500;">Direct Farmer-Trader Trading & Mandi Forecasting</div>
            <div style="font-size: 11px; color: #334155; font-weight: 600; margin-top: 6px; background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; display: inline-block;">
                B.Tech Final Year Project
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.info("👋 Please Sign In or Create an Account to enter the portal as a **Farmer (Seller)**, **Trader (Buyer)**, or **Super Administrator**.")
        st.markdown("---")
        st.markdown("""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px; font-size:12px; color:#475569;">
            <b>Role Privileges:</b><br>
            • <b>Seller:</b> Add produce, view orders, price forecast.<br>
            • <b>Buyer:</b> Browse mandi, buy produce, track orders.<br>
            • <b>Super Admin:</b> Full oversight (@super.com) of buyers, sellers & negotiations.
        </div>
        """, unsafe_allow_html=True)

    render_login_page()
    st.stop()

# ==========================================
# AUTHENTICATED USER SESSION
current_user = st.session_state.get("user")
if not current_user:
    st.stop()
user_role = current_user.get("role", "seller")
user_email = current_user.get("email", "")

# Verify Super Admin rule: any email ending in @super.com is always superadmin
if is_superadmin_email(user_email) and user_role != "superadmin":
    current_user["role"] = "superadmin"
    user_role = "superadmin"

# Sidebar for Authenticated Users
with st.sidebar:
    st.markdown("""
    <div style="padding: 6px 0 14px 0;">
        <div style="font-size: 20px; font-weight: 800; color: #164e3b;">🌾 KrishiMandi</div>
        <div style="font-size: 11.5px; color: #64748b; font-weight: 500;">Agricultural Trade & Price Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    # User Profile Card
    badge_html = render_role_badge(user_role)
    st.markdown(f"""
    <div class="user-pill">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <b style="font-size:14px; color:#0f172a;">{current_user['name']}</b>
        </div>
        <div style="margin-top:4px;">{badge_html}</div>
        <div style="font-size:11px; color:#64748b; margin-top:6px;">
            ✉️ {current_user['email']}<br>
            📍 {current_user.get('mandi', 'General Mandi')}, {current_user.get('state', '')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Role-Specific Navigation Options
    if user_role == "seller":
        nav_options = [
            "🌾 Seller Dashboard & Produce",
            "🔬 ML Research & Model Studio",
            "📋 Crop Planning & Profit Estimation",
            "📈 Mandi Price Forecasting",
            "💡 Storage & Sale Advisor",
            "📑 Mandi Market Comparison",
            "📄 Market Reports"
        ]
    elif user_role == "buyer":
        nav_options = [
            "🛒 Buyer Dashboard & Marketplace",
            "🔬 ML Research & Model Studio",
            "🔍 Mandi Price Comparison",
            "📈 Historical Price Trends",
            "📄 Market Reports"
        ]
    elif user_role == "superadmin":
        nav_options = [
            "🛡️ Super Admin Command Center",
            "🔬 ML Research & Model Studio",
            "🔄 Buyer-Seller Interactions",
            "👥 Users Directory",
            "🌾 All Produce Listings",
            "📦 All Trade Orders",
            "🏛️ APMC Mandi Benchmark Records",
            "📊 Platform Overview Dashboard"
        ]
    else:
        nav_options = ["🌾 Dashboard", "🔬 ML Research & Model Studio"]

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Sign Out Button
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["user"] = None
        st.rerun()

    st.caption("College Capstone Project • Python & SQLite")

# ==========================================
# PAGE ROUTING BY ROLE AND NAVIGATION
# ==========================================
if selected_nav == "🔬 ML Research & Model Studio":
    render_ml_studio_page()

elif user_role == "seller":
    if selected_nav == "🌾 Seller Dashboard & Produce":
        render_seller_portal(current_user)
    elif selected_nav == "📈 Mandi Price Forecasting":
        render_prediction_page()
    elif selected_nav == "💡 Storage & Sale Advisor":
        render_selling_advisor_page()
    elif selected_nav == "📋 Crop Planning & Profit Estimation":
        render_crop_recommendation_page()
    elif selected_nav == "📑 Mandi Market Comparison":
        render_market_analysis_page()
    elif selected_nav == "📄 Market Reports":
        render_reports_page()

elif user_role == "buyer":
    if selected_nav == "🛒 Buyer Dashboard & Marketplace":
        render_buyer_portal(current_user)
    elif selected_nav == "🔍 Mandi Price Comparison":
        render_market_analysis_page()
    elif selected_nav == "📈 Historical Price Trends":
        render_prediction_page()
    elif selected_nav == "📄 Market Reports":
        render_reports_page()

elif user_role == "superadmin":
    if selected_nav == "🛡️ Super Admin Command Center":
        render_superadmin_portal(current_user)
    elif selected_nav == "🔄 Buyer-Seller Interactions":
        render_superadmin_portal(current_user)
    elif selected_nav == "👥 Users Directory":
        render_superadmin_portal(current_user)
    elif selected_nav == "🌾 All Produce Listings":
        render_superadmin_portal(current_user)
    elif selected_nav == "📦 All Trade Orders":
        render_superadmin_portal(current_user)
    elif selected_nav == "🏛️ APMC Mandi Benchmark Records":
        render_data_management_page()
    elif selected_nav == "📊 Platform Overview Dashboard":
        render_dashboard_page()
