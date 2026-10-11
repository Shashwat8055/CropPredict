"""
CropPricePredict - Grain Trader / Buyer Portal
Provides:
- Buyer Dashboard (procurement overview, order tracker)
- Live Crop Marketplace (browse verified farm listings, place purchase orders & bids)
- My Orders & Purchases (strict buyer isolation, track delivery status, cancel pending orders)
- Mandi Price Comparison (compare mandi rates across states to optimize procurement)
"""
import streamlit as st
import pandas as pd

from config import CROPS_METADATA, STATE_MANDIS
from data.marketplace_db import (
    get_marketplace_listings, place_buyer_order, get_buyer_orders, cancel_order_by_buyer
)
from ui.styles import render_metric_card, render_status_badge
from views.market_analysis import render_market_analysis_page
from views.prediction import render_prediction_page

def render_buyer_portal(user: dict):
    """Main entrypoint for logged-in Buyer/Trader."""
    buyer_email = user["email"]
    buyer_name = user["name"]

    st.markdown(f"""
    <div class="brand-header">
        <div>
            <div style="display:flex; align-items:center; gap:10px;">
                <h1 class="brand-title">🛒 Vyapar Buyer Portal</h1>
                <span class="role-badge role-buyer">Buyer / Trader Account</span>
            </div>
            <div class="brand-subtitle">
                Welcome, <b>{buyer_name}</b> | Location: {user.get('mandi', 'General')} ({user.get('state', 'India')}) | {buyer_email}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_dash, tab_market, tab_orders, tab_compare, tab_trends = st.tabs([
        "📊 Buyer Dashboard",
        "🌾 Browse Farm Marketplace",
        "📋 My Orders & Purchases",
        "🔍 Mandi Price Comparison",
        "📈 Price Trend Analysis"
    ])

    # ==========================================
    # TAB 1: BUYER DASHBOARD
    # ==========================================
    with tab_dash:
        orders = get_buyer_orders(buyer_email)
        total_orders = len(orders)
        pending_orders = sum(1 for o in orders if o["status"] == "Pending")
        active_orders = sum(1 for o in orders if o["status"] in ["Accepted", "Dispatched"])
        completed_orders = sum(1 for o in orders if o["status"] == "Completed")
        total_qty = sum(o["quantity_quintals"] for o in orders if o["status"] != "Cancelled")
        total_spent = sum(o["total_amount"] for o in orders if o["status"] != "Cancelled")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(render_metric_card("Total Orders Placed", f"{total_orders}", "All-time procurement bids", trend="neutral"), unsafe_allow_html=True)
        with c2:
            st.markdown(render_metric_card("Active Deliveries", f"{active_orders}", "Accepted & In-transit", trend="blue"), unsafe_allow_html=True)
        with c3:
            st.markdown(render_metric_card("Purchased Volume", f"{total_qty:,.1f} Qtl", "Total crop quantity", trend="up"), unsafe_allow_html=True)
        with c4:
            st.markdown(render_metric_card("Total Procurement Spend", f"₹{total_spent:,.0f}", f"{completed_orders} delivered deals", trend="neutral"), unsafe_allow_html=True)

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1.3, 1])

        with col_left:
            st.markdown("### 📋 Your Recent Purchases")
            if orders:
                ord_data = []
                for o in orders[:5]:
                    ord_data.append({
                        "Order ID": f"#{o['id']}",
                        "Farmer / Seller": o["seller_name"],
                        "Crop": o["commodity"],
                        "Quantity (Qtl)": o["quantity_quintals"],
                        "Agreed Rate": f"₹{o['offered_price_per_quintal']:,.0f}",
                        "Total (₹)": f"₹{o['total_amount']:,.0f}",
                        "Status": o["status"]
                    })
                st.dataframe(pd.DataFrame(ord_data), use_container_width=True, hide_index=True)
            else:
                st.info("You haven't placed any orders yet. Visit the 'Browse Farm Marketplace' tab to find fresh crop listings!")

        with col_right:
            st.markdown("### 🌾 Fresh Farm Produce Available")
            fresh_listings = get_marketplace_listings()
            if fresh_listings:
                st.write(f"Currently **{len(fresh_listings)} produce lots** available from verified farmers:")
                for item in fresh_listings[:3]:
                    st.markdown(f"""
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px; margin-bottom:8px;">
                        <b style="color:#0f172a;">{item['commodity']} ({item.get('variety', 'Grade A')})</b><br>
                        <span style="font-size:12px; color:#475569;">👨‍🌾 {item['seller_name']} | 📍 {item['mandi']}, {item['state']}</span><br>
                        <span style="font-size:13px; font-weight:700; color:#166534;">₹{item['price_per_quintal']:,.0f}/Qtl</span> • <span style="font-size:12px; color:#64748b;">{item['available_quintals']} Qtl in stock</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No active marketplace listings currently.")

    # ==========================================
    # TAB 2: BROWSE FARM MARKETPLACE
    # ==========================================
    with tab_market:
        st.markdown("### Direct Farm Marketplace")
        st.caption("Browse produce listed directly by verified farmers. Place purchase orders with your offered rates.")

        # Filter bar
        with st.expander("Filter Marketplace Listings", expanded=True):
            f1, f2, f3, f4 = st.columns(4)
            with f1:
                filter_crop = st.selectbox("Crop", ["All Crops"] + list(CROPS_METADATA.keys()))
            with f2:
                filter_state = st.selectbox("State", ["All States"] + list(STATE_MANDIS.keys()))
            with f3:
                if filter_state != "All States":
                    mandis_avail = ["All Mandis"] + STATE_MANDIS[filter_state]["mandis"]
                else:
                    mandis_avail = ["All Mandis"]
                filter_mandi = st.selectbox("Mandi", mandis_avail)
            with f4:
                max_rate = st.number_input("Max Asking Rate (₹/Qtl)", min_value=0.0, max_value=100000.0, value=0.0, step=500.0, help="0 means any price")

        listings = get_marketplace_listings(
            crop=filter_crop if filter_crop != "All Crops" else None,
            state=filter_state if filter_state != "All States" else None,
            mandi=filter_mandi if filter_mandi != "All Mandis" else None,
            max_price=max_rate if max_rate > 0 else None
        )

        if not listings:
            st.warning("No listings found matching your search filters. Try resetting the filters.")
        else:
            st.markdown(f"#### Available Produce Lots ({len(listings)})")
            for item in listings:
                with st.container():
                    st.markdown(f"""
                    <div class="product-card">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                                <b style="font-size:18px; color:#0f172a;">{item['commodity']}</b>
                                <span style="font-size:14px; color:#475569; margin-left:6px;">— {item.get('variety', 'Standard')}</span>
                                <div style="font-size:13px; color:#334155; margin-top:4px;">
                                    👨‍🌾 Farmer: <b>{item['seller_name']}</b> | 📞 {item.get('seller_phone', 'Available upon order')}
                                </div>
                                <div style="font-size:12px; color:#64748b; margin-top:2px;">
                                    📍 <b>{item['mandi']}, {item['state']}</b> | Grade: <b>{item.get('quality_grade', 'Grade A')}</b> | Harvest: {item.get('harvest_date', 'Recent')}
                                </div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:22px; font-weight:800; color:#166534;">₹{item['price_per_quintal']:,.0f} <span style="font-size:12px; font-weight:400; color:#64748b;">/ Quintal</span></div>
                                <div style="font-size:13px; font-weight:600; color:#0f172a; margin-top:2px;">Stock: {item['available_quintals']:.1f} Qtl</div>
                            </div>
                        </div>
                        <div style="background:#f8fafc; border-radius:6px; padding:8px 12px; margin-top:10px; font-size:12.5px; color:#475569; border:1px solid #e2e8f0;">
                            <b>Farmer's Quality Notes:</b> <i>"{item.get('notes') or 'Quality tested clean produce.'}"</i>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Order Placement Form
                    with st.expander(f"🛒 Place Purchase Order / Bid for {item['commodity']} (Lot #{item['id']})"):
                        with st.form(f"buy_form_{item['id']}"):
                            b_c1, b_c2, b_c3 = st.columns(3)
                            with b_c1:
                                req_qty = st.number_input(
                                    "Desired Quantity (Quintals)",
                                    min_value=1.0,
                                    max_value=float(item['available_quintals']),
                                    value=min(50.0, float(item['available_quintals'])),
                                    step=5.0
                                )
                            with b_c2:
                                offer_rate = st.number_input(
                                    "Offered Rate (₹/Quintal)",
                                    min_value=100.0,
                                    max_value=100000.0,
                                    value=float(item['price_per_quintal']),
                                    step=25.0
                                )
                            with b_c3:
                                total_calc = req_qty * offer_rate
                                st.metric("Calculated Total (₹)", f"₹{total_calc:,.0f}")

                            deliv_addr = st.text_input("Delivery Depot / Godown Address", value=user.get("address", "Local Mandi Gate #2 Delivery"))
                            buyer_msg = st.text_area("Order Notes / Payment Terms for Farmer", placeholder="e.g. 50% advance upon loading, balance within 24h of weighbridge slip.")
                            
                            submit_order = st.form_submit_button("Send Purchase Offer to Farmer", type="primary", use_container_width=True)

                            if submit_order:
                                ok, msg, ord_id = place_buyer_order(
                                    listing_id=item["id"],
                                    buyer_email=buyer_email,
                                    buyer_name=buyer_name,
                                    buyer_phone=user.get("phone", "+91 98220 00000"),
                                    quantity_quintals=req_qty,
                                    offered_price_per_quintal=offer_rate,
                                    delivery_address=deliv_addr,
                                    buyer_notes=buyer_msg
                                )
                                if ok:
                                    st.success(f"{msg} The farmer will be notified to accept your order.")
                                    st.rerun()
                                else:
                                    st.error(msg)

    # ==========================================
    # TAB 3: MY ORDERS & PURCHASES
    # ==========================================
    with tab_orders:
        st.markdown("### Your Procurement Orders & History")
        st.caption("Track order status, delivery progress, and seller responses. Only you can view your purchase records.")

        buyer_orders = get_buyer_orders(buyer_email)
        if not buyer_orders:
            st.info("You haven't placed any orders yet. Visit 'Browse Farm Marketplace' to purchase produce.")
        else:
            for ord_item in buyer_orders:
                st.markdown(f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:16px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <span style="font-size:12px; font-weight:700; color:#475569;">ORDER #{ord_item['id']}</span>
                            <h3 style="margin:2px 0; font-size:18px; color:#0f172a;">{ord_item['commodity']} - {ord_item['quantity_quintals']} Quintals</h3>
                            <div style="font-size:13px; color:#334155; margin-top:2px;">
                                👨‍🌾 Farmer / Seller: <b>{ord_item['seller_name']}</b> ({ord_item.get('seller_email')}) | 📍 {ord_item.get('mandi', '')}, {ord_item.get('state', '')}
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:20px; font-weight:800; color:#0284c7;">₹{ord_item['total_amount']:,.0f}</div>
                            <div style="font-size:12px; color:#64748b;">Rate: ₹{ord_item['offered_price_per_quintal']:,.0f}/Qtl</div>
                            <div style="margin-top:4px;">{render_status_badge(ord_item['status'])}</div>
                        </div>
                    </div>
                    <div style="background:#f8fafc; border-radius:6px; padding:10px; margin-top:10px; font-size:12.5px; color:#334155; border:1px solid #e2e8f0;">
                        <b>Delivery Address:</b> {ord_item.get('delivery_address') or 'Mandi delivery'}<br>
                        <b>Your Notes to Farmer:</b> <i>"{ord_item.get('buyer_notes') or 'None'}"</i><br>
                        {f"<b>Farmer Response:</b> <span style='color:#166534;'>{ord_item.get('seller_response_notes')}</span>" if ord_item.get('seller_response_notes') else "<b>Farmer Response:</b> <i>Awaiting farmer update...</i>"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Cancel option for pending orders
                if ord_item["status"] == "Pending":
                    with st.expander(f"⚠️ Cancel Pending Order #{ord_item['id']}"):
                        reason = st.text_input("Reason for Cancellation", key=f"cncl_rsn_{ord_item['id']}")
                        if st.button("Confirm Cancellation", key=f"cncl_btn_{ord_item['id']}"):
                            ok, msg = cancel_order_by_buyer(ord_item["id"], buyer_email, reason)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

    # ==========================================
    # TAB 4: MANDI PRICE COMPARISON
    # ==========================================
    with tab_compare:
        st.markdown("### Mandi Rate Comparison & Price Spread")
        st.caption("Compare prices across different states and mandis to discover the most economical procurement locations.")
        render_market_analysis_page()

    # ==========================================
    # TAB 5: PRICE TREND ANALYSIS
    # ==========================================
    with tab_trends:
        st.markdown("### Historical Price Trends & Rate Estimation")
        st.caption("Review historical mandi arrival rates and statistical price forecasts to negotiate fair purchase contracts.")
        render_prediction_page()
