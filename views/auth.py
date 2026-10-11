"""
CropPricePredict - User Authentication & Role Selection Module
Provides secure Login and Registration for Sellers, Buyers, and Super Admins (@super.com).
"""
import streamlit as st
from config import STATE_MANDIS
from data.marketplace_db import authenticate_user, register_user, is_superadmin_email

def render_login_page():
    """Renders authentication page for login and new account creation."""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 24px; padding: 18px 10px;">
        <div style="font-size: 32px; font-weight: 800; color: #164e3b; letter-spacing: -0.5px;">
            🌾 KrishiMandi Portal
        </div>
        <div style="font-size: 15px; color: #475569; margin-top: 6px; font-weight: 500;">
            Agricultural Commodity Trading & Mandi Price Intelligence System
        </div>
        <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
            Role-Based Access for Farmers (Sellers), Grain Traders (Buyers), and Mandi Regulators (Super Admin)
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register, tab_quick = st.tabs(["🔑 Sign In", "📝 Create New Account", "⚡ Quick Demo Accounts"])

    # 1. LOGIN TAB
    with tab_login:
        st.markdown("#### Access Your Portal")
        with st.form("login_form"):
            login_email = st.text_input("Registered Email Address", placeholder="e.g. ramesh.farmer@mandi.in or admin@super.com")
            login_password = st.text_input("Password", type="password", placeholder="Enter your account password")
            submit_login = st.form_submit_button("Sign In to Dashboard", type="primary", use_container_width=True)

            if submit_login:
                if not login_email or not login_password:
                    st.error("Please enter both email and password.")
                else:
                    user = authenticate_user(login_email, login_password)
                    if user:
                        st.session_state["user"] = user
                        st.success(f"Welcome back, {user['name']}! Logging in as {user['role'].upper()}...")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please verify your email and password or use a demo account.")

    # 2. REGISTER TAB
    with tab_register:
        st.markdown("#### Register New Account")
        with st.form("register_form"):
            selected_role_label = st.radio(
                "Select Your Account Type:",
                options=["🌾 Farmer / Seller", "🛒 Trader / Buyer"],
                horizontal=True
            )
            role_value = "seller" if "Seller" in selected_role_label else "buyer"

            st.caption("ℹ️ Accounts registered with an `@super.com` email address will automatically receive Super Administrator privileges.")

            r_col1, r_col2 = st.columns(2)
            with r_col1:
                reg_name = st.text_input("Full Name / Business Name *")
                reg_email = st.text_input("Email Address *", placeholder="e.g. name@example.com")
                reg_password = st.text_input("Create Password *", type="password")
            with r_col2:
                reg_phone = st.text_input("Contact Phone Number", placeholder="+91 98765 00000")
                reg_state = st.selectbox("Primary State", list(STATE_MANDIS.keys()))
                reg_mandi = st.selectbox("Primary Mandi / APMC Market", STATE_MANDIS[reg_state]["mandis"])

            reg_address = st.text_area("Farm Address / Trading Office Address", placeholder="Village, Tehsil, District, PIN code...")
            submit_reg = st.form_submit_button("Create Account & Enter Portal", type="primary", use_container_width=True)

            if submit_reg:
                if not reg_name or not reg_email or not reg_password:
                    st.error("Please fill in all mandatory fields (Name, Email, Password).")
                else:
                    success, msg, new_user = register_user(
                        email=reg_email,
                        password=reg_password,
                        name=reg_name,
                        role=role_value,
                        phone=reg_phone,
                        state=reg_state,
                        mandi=reg_mandi,
                        address=reg_address
                    )
                    if success:
                        st.session_state["user"] = new_user
                        st.success(f"Account created successfully! Logging you in as {new_user['role'].upper()}...")
                        st.rerun()
                    else:
                        st.error(msg)

    # 3. QUICK DEMO TAB
    with tab_quick:
        st.markdown("#### Test Any Role with 1-Click Demo Login")
        st.write("Click any of the profiles below to immediately test the role-specific dashboards and isolation features:")

        d_col1, d_col2, d_col3 = st.columns(3)

        with d_col1:
            st.markdown("""
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; padding:14px;">
                <b style="color:#166534; font-size:15px;">🌾 Farmer Ramesh</b><br>
                <span style="font-size:12px; color:#15803d;">Role: <b>Seller</b> (Khanna Mandi, Punjab)</span><br>
                <span style="font-size:11px; color:#475569;">Email: ramesh.farmer@mandi.in</span><br>
                <span style="font-size:11px; color:#475569;">Has active listings for Wheat, Mustard, Gram.</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Log in as Farmer Ramesh", use_container_width=True):
                user = authenticate_user("ramesh.farmer@mandi.in", "farmer123")
                if user:
                    st.session_state["user"] = user
                    st.rerun()

        with d_col2:
            st.markdown("""
            <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; padding:14px;">
                <b style="color:#1e40af; font-size:15px;">🛒 Trader Suresh</b><br>
                <span style="font-size:12px; color:#1d4ed8;">Role: <b>Buyer</b> (Pune Market Yard)</span><br>
                <span style="font-size:11px; color:#475569;">Email: suresh.trader@mandi.in</span><br>
                <span style="font-size:11px; color:#475569;">Has placed orders and purchase bids.</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Log in as Trader Suresh", use_container_width=True):
                user = authenticate_user("suresh.trader@mandi.in", "buyer123")
                if user:
                    st.session_state["user"] = user
                    st.rerun()

        with d_col3:
            st.markdown("""
            <div style="background:#f5f3ff; border:1px solid #ddd6fe; border-radius:10px; padding:14px;">
                <b style="color:#5b21b6; font-size:15px;">🛡️ Super Admin</b><br>
                <span style="font-size:12px; color:#6d28d9;">Role: <b>Super Admin</b> (@super.com)</span><br>
                <span style="font-size:11px; color:#475569;">Email: admin@super.com</span><br>
                <span style="font-size:11px; color:#475569;">Full oversight of all buyers, sellers & interactions.</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Log in as Super Admin", use_container_width=True):
                user = authenticate_user("admin@super.com", "admin123")
                if user:
                    st.session_state["user"] = user
                    st.rerun()

if __name__ == "__main__":
    st.set_page_config(page_title="KrishiMandi - Login", page_icon="🌾", layout="wide")
    render_login_page()
