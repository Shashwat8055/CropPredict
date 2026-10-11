"""
CropPricePredict - Farmer / Seller Portal
Provides:
- Seller Dashboard (sales overview, stock, incoming orders)
- Produce Inventory Management (add, update, delete own listings)
- Buyer Orders Management (accept, dispatch, complete, decline with communication notes)
- Mandi Price Forecast & Storage Advisory (helps farmer decide when to sell)
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date

from config import CROPS_METADATA, STATE_MANDIS
from data.marketplace_db import (
    get_seller_listings, add_seller_listing, update_seller_listing,
    delete_seller_listing, get_seller_orders, update_order_status_by_seller
)
from ui.styles import render_metric_card, render_status_badge
from views.prediction import render_prediction_page
from views.selling_advisor import render_selling_advisor_page

def render_seller_portal(user: dict):
    """Main entrypoint for logged-in Seller/Farmer."""
    seller_email = user["email"]
    seller_name = user["name"]

    st.markdown(f"""
    <div class="brand-header">
        <div>
            <div style="display:flex; align-items:center; gap:10px;">
                <h1 class="brand-title">🌾 Kisan Seller Portal</h1>
                <span class="role-badge role-seller">Seller Account</span>
            </div>
            <div class="brand-subtitle">
                Welcome, <b>{seller_name}</b> | Mandi: {user.get('mandi', 'General')} ({user.get('state', 'India')}) | {seller_email}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_dash, tab_listings, tab_orders, tab_forecast, tab_advisor = st.tabs([
        "📊 Seller Dashboard",
        "🌾 My Produce Listings",
        "📦 Incoming Buyer Orders",
        "📈 Mandi Price Forecasting",
        "💡 Storage & Sale Advisor"
    ])

    # ==========================================
    # TAB 1: SELLER DASHBOARD
    # ==========================================
    with tab_dash:
        listings = get_seller_listings(seller_email)
        orders = get_seller_orders(seller_email)

        total_listings = len(listings)
        active_stock = sum(item["available_quintals"] for item in listings if item["status"] == "Active")
        pending_orders = sum(1 for o in orders if o["status"] == "Pending")
        accepted_orders = sum(1 for o in orders if o["status"] in ["Accepted", "Dispatched"])
        completed_orders = sum(1 for o in orders if o["status"] == "Completed")
        realized_revenue = sum(o["total_amount"] for o in orders if o["status"] in ["Accepted", "Dispatched", "Completed"])

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(render_metric_card("My Active Listings", f"{total_listings}", "Produce items listed", trend="neutral"), unsafe_allow_html=True)
        with c2:
            st.markdown(render_metric_card("Available Produce", f"{active_stock:,.1f} Qtl", "Unsold inventory stock", trend="up"), unsafe_allow_html=True)
        with c3:
            st.markdown(render_metric_card("Pending Orders", f"{pending_orders}", "Awaiting your response", trend="down" if pending_orders > 0 else "neutral"), unsafe_allow_html=True)
        with c4:
            st.markdown(render_metric_card("Total Trade Value", f"₹{realized_revenue:,.0f}", f"{completed_orders + accepted_orders} accepted orders", trend="blue"), unsafe_allow_html=True)

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1.2, 1])

        with col_left:
            st.markdown("### 🌾 Current Produce Inventory")
            if listings:
                list_data = []
                for item in listings:
                    list_data.append({
                        "Listing ID": f"#{item['id']}",
                        "Crop": item["commodity"],
                        "Variety": item.get("variety", "-"),
                        "Available (Qtl)": f"{item['available_quintals']:.1f}",
                        "Asking Rate": f"₹{item['price_per_quintal']:,.0f}/Qtl",
                        "Mandi": f"{item['mandi']}, {item['state']}",
                        "Status": item["status"]
                    })
                st.dataframe(pd.DataFrame(list_data), use_container_width=True, hide_index=True)
            else:
                st.info("You haven't listed any farm produce yet. Go to the 'My Produce Listings' tab to add your first crop!")

        with col_right:
            st.markdown("### 📦 Recent Buyer Orders")
            if orders:
                ord_data = []
                for o in orders[:5]:
                    ord_data.append({
                        "Order": f"#{o['id']}",
                        "Buyer": o["buyer_name"],
                        "Crop": o["commodity"],
                        "Qty (Qtl)": o["quantity_quintals"],
                        "Offer Rate": f"₹{o['offered_price_per_quintal']:,.0f}",
                        "Total (₹)": f"₹{o['total_amount']:,.0f}",
                        "Status": o["status"]
                    })
                st.dataframe(pd.DataFrame(ord_data), use_container_width=True, hide_index=True)
                if pending_orders > 0:
                    st.warning(f"⚠️ You have {pending_orders} pending buyer order(s) requiring your confirmation in the 'Incoming Buyer Orders' tab.")
            else:
                st.info("No orders received from buyers yet.")

    # ==========================================
    # TAB 2: MY PRODUCE LISTINGS
    # ==========================================
    with tab_listings:
        st.markdown("### Manage Your Farm Produce Listings")
        st.caption("Add your harvested produce to the mandi marketplace. Only you can edit or delete your listings.")

        with st.expander("➕ List New Crop Produce for Sale", expanded=False):
            with st.form("new_listing_form"):
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1:
                    new_crop = st.selectbox("Select Crop", list(CROPS_METADATA.keys()))
                    new_variety = st.text_input("Variety / Grade Title", placeholder="e.g. Sharbati Gold / Basmati 1121")
                    new_grade = st.selectbox("Quality Grade", ["Grade A (Premium)", "Grade B (Standard)", "Fair Average Quality (FAQ)"])
                with f_col2:
                    default_state = user.get("state") if user.get("state") in STATE_MANDIS else list(STATE_MANDIS.keys())[0]
                    new_state = st.selectbox("State", list(STATE_MANDIS.keys()), index=list(STATE_MANDIS.keys()).index(default_state))
                    mandis_in_state = STATE_MANDIS[new_state]["mandis"]
                    default_mandi = user.get("mandi") if user.get("mandi") in mandis_in_state else mandis_in_state[0]
                    new_mandi = st.selectbox("Mandi / Market", mandis_in_state, index=mandis_in_state.index(default_mandi))
                    new_harvest_date = st.date_input("Harvest Date", value=date.today())
                with f_col3:
                    base_price = CROPS_METADATA.get(new_crop, {}).get("base_price", 2200.0)
                    new_qty = st.number_input("Total Quantity (Quintals)", min_value=1.0, max_value=50000.0, value=100.0, step=10.0)
                    new_price = st.number_input("Asking Price (₹/Quintal)", min_value=100.0, max_value=100000.0, value=float(base_price), step=50.0)
                    new_phone = st.text_input("Contact Phone for Inquiries", value=user.get("phone", "+91 98765 00000"))

                new_notes = st.text_area("Produce Quality Notes / Storage Details", placeholder="e.g. Moisture 11%, machine cleaned, stored in dry warehouse, loading facility available.")
                submit_listing = st.form_submit_button("Publish Produce Listing to Marketplace", type="primary", use_container_width=True)

                if submit_listing:
                    ok, msg = add_seller_listing(
                        seller_email=seller_email,
                        seller_name=seller_name,
                        seller_phone=new_phone,
                        commodity=new_crop,
                        variety=new_variety or f"{new_crop} FAQ",
                        state=new_state,
                        mandi=new_mandi,
                        quantity_quintals=new_qty,
                        price_per_quintal=new_price,
                        harvest_date=str(new_harvest_date),
                        quality_grade=new_grade,
                        notes=new_notes
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        # Existing Listings Table & Management
        my_listings = get_seller_listings(seller_email)
        if my_listings:
            st.markdown(f"#### Your Active Listings ({len(my_listings)})")
            for item in my_listings:
                with st.container():
                    st.markdown(f"""
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:16px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                                <b style="font-size:17px; color:#0f172a;">{item['commodity']}</b> 
                                <span style="font-size:13px; color:#475569; margin-left:6px;">({item.get('variety', 'Standard')})</span>
                                <div style="font-size:12px; color:#64748b; margin-top:2px;">
                                    📍 <b>{item['mandi']}, {item['state']}</b> | Grade: <b>{item.get('quality_grade', 'Grade A')}</b> | Harvest: {item.get('harvest_date', 'Recent')}
                                </div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:20px; font-weight:800; color:#166534;">₹{item['price_per_quintal']:,.0f} <span style="font-size:12px; font-weight:400; color:#64748b;">/ Quintal</span></div>
                                <span class="order-status {'status-completed' if item['status'] == 'Active' else 'status-cancelled'}">{item['status']}</span>
                            </div>
                        </div>
                        <div style="margin-top:10px; font-size:13px; color:#334155;">
                            📦 Available Stock: <b>{item['available_quintals']:.1f} Quintals</b> (Total Initial: {item['quantity_quintals']:.1f} Qtl)
                        </div>
                        <div style="font-size:12px; color:#64748b; margin-top:4px;">
                            <i>"{item.get('notes') or 'No extra notes provided.'}"</i>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    c_act1, c_act2, c_act3 = st.columns([1, 1, 2])
                    with c_act1:
                        with st.expander(f"✏️ Edit Listing #{item['id']}"):
                            with st.form(f"edit_form_{item['id']}"):
                                edit_qty = st.number_input("Available Stock (Qtl)", min_value=0.0, max_value=50000.0, value=float(item['available_quintals']))
                                edit_price = st.number_input("Asking Price (₹/Qtl)", min_value=100.0, max_value=100000.0, value=float(item['price_per_quintal']))
                                edit_grade = st.text_input("Quality Grade", value=item.get("quality_grade", "Grade A"))
                                edit_status = st.selectbox("Status", ["Active", "Sold Out", "Closed"], index=0 if item["status"] == "Active" else 1)
                                edit_notes = st.text_area("Remarks", value=item.get("notes", ""))
                                save_btn = st.form_submit_button("Update Listing")
                                if save_btn:
                                    ok, msg = update_seller_listing(
                                        listing_id=item["id"],
                                        seller_email=seller_email,
                                        quantity_quintals=edit_qty,
                                        price_per_quintal=edit_price,
                                        quality_grade=edit_grade,
                                        status=edit_status,
                                        notes=edit_notes
                                    )
                                    if ok:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    with c_act2:
                        if st.button(f"🗑️ Delete Listing #{item['id']}", key=f"del_{item['id']}"):
                            ok, msg = delete_seller_listing(item["id"], seller_email)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
        else:
            st.info("You have no active listings. Expand the form above to add your first crop produce listing.")

    # ==========================================
    # TAB 3: INCOMING BUYER ORDERS
    # ==========================================
    with tab_orders:
        st.markdown("### Orders & Inquiries from Registered Buyers")
        st.caption("Review purchase offers sent directly by traders and buyers for your crops. Accept, dispatch, or complete orders.")

        seller_orders = get_seller_orders(seller_email)
        if not seller_orders:
            st.info("No orders received yet from buyers.")
        else:
            for ord_item in seller_orders:
                st.markdown(f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:16px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <span style="font-size:12px; font-weight:700; color:#475569;">ORDER #{ord_item['id']}</span>
                            <h3 style="margin:2px 0; font-size:18px; color:#0f172a;">{ord_item['commodity']} - {ord_item['quantity_quintals']} Quintals</h3>
                            <div style="font-size:13px; color:#334155; margin-top:2px;">
                                👤 Buyer: <b>{ord_item['buyer_name']}</b> ({ord_item.get('buyer_email')}) | 📞 {ord_item.get('buyer_phone', 'Not provided')}
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:20px; font-weight:800; color:#0284c7;">₹{ord_item['total_amount']:,.0f}</div>
                            <div style="font-size:12px; color:#64748b;">Offered: ₹{ord_item['offered_price_per_quintal']:,.0f} / Qtl</div>
                            <div style="margin-top:4px;">{render_status_badge(ord_item['status'])}</div>
                        </div>
                    </div>
                    <div style="background:#f8fafc; border-radius:6px; padding:10px; margin-top:10px; font-size:12.5px; color:#334155; border:1px solid #e2e8f0;">
                        <b>Delivery Address:</b> {ord_item.get('delivery_address') or 'Mandi delivery'}<br>
                        <b>Buyer Notes:</b> <i>"{ord_item.get('buyer_notes') or 'None'}"</i><br>
                        {f"<b>Your Response:</b> <span style='color:#166534;'>{ord_item.get('seller_response_notes')}</span>" if ord_item.get('seller_response_notes') else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Order Status Action Buttons
                st_val = ord_item["status"]
                with st.expander(f"⚙️ Respond to Order #{ord_item['id']} (Current Status: {st_val})"):
                    with st.form(f"order_act_{ord_item['id']}"):
                        resp_note = st.text_input("Message / Logistics Note for Buyer", placeholder="e.g. Loading ready, truck transport details, invoice bill number...", value=ord_item.get("seller_response_notes", ""))
                        
                        col_btns = st.columns(4)
                        with col_btns[0]:
                            accept_btn = st.form_submit_button("✅ Accept Order")
                        with col_btns[1]:
                            dispatch_btn = st.form_submit_button("🚚 Mark Dispatched")
                        with col_btns[2]:
                            complete_btn = st.form_submit_button("🎉 Mark Completed")
                        with col_btns[3]:
                            decline_btn = st.form_submit_button("❌ Decline Order")

                        if accept_btn:
                            ok, msg = update_order_status_by_seller(ord_item["id"], seller_email, seller_name, "Accepted", resp_note or "Order accepted. Produce reserved.")
                            if ok: st.success(msg); st.rerun()
                            else: st.error(msg)
                        elif dispatch_btn:
                            ok, msg = update_order_status_by_seller(ord_item["id"], seller_email, seller_name, "Dispatched", resp_note or "Produce dispatched via truck.")
                            if ok: st.success(msg); st.rerun()
                            else: st.error(msg)
                        elif complete_btn:
                            ok, msg = update_order_status_by_seller(ord_item["id"], seller_email, seller_name, "Completed", resp_note or "Deal completed and payment received.")
                            if ok: st.success(msg); st.rerun()
                            else: st.error(msg)
                        elif decline_btn:
                            ok, msg = update_order_status_by_seller(ord_item["id"], seller_email, seller_name, "Declined", resp_note or "Declined due to price mismatch or lack of stock.")
                            if ok: st.success(msg); st.rerun()
                            else: st.error(msg)

    # ==========================================
    # TAB 4: MANDI PRICE FORECASTING
    # ==========================================
    with tab_forecast:
        st.markdown("### Mandi Historical Price Forecasting")
        st.caption("Analyze historical market trends and estimated prices over 7 to 90 days before finalizing your sale price.")
        render_prediction_page()

    # ==========================================
    # TAB 5: STORAGE & SALE ADVISOR
    # ==========================================
    with tab_advisor:
        st.markdown("### Mandi Storage & Sale Strategy Advisor")
        st.caption("Calculate monthly godown/cold-storage costs vs expected future price increase to decide whether to sell now or hold.")
        render_selling_advisor_page()
