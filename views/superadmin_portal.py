"""
CropPricePredict - Super Administrator Portal (@super.com)
Provides complete oversight across the entire ecosystem:
- System overview KPIs & platform trade metrics
- Deep Buyer-Seller Interaction and Negotiation Tracking
- All Registered Users Directory (Farmers & Traders)
- Global Produce Listings & Stock Audit
- Global Order Ledger & Transaction Records
- APMC Mandi Historical Records & Model Calibration
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from config import CROPS_METADATA, STATE_MANDIS
from data.marketplace_db import (
    get_platform_overview_metrics, get_all_users, get_all_listings,
    get_all_orders, get_all_interactions, admin_delete_listing
)
from ui.styles import render_metric_card, render_status_badge, render_role_badge
from views.model_management import render_model_management_page
from data.database import load_data_from_db

def render_superadmin_portal(user: dict):
    """Main entrypoint for Super Administrator (@super.com)."""
    admin_email = user["email"]
    admin_name = user["name"]

    st.markdown(f"""
    <div class="brand-header" style="background: linear-gradient(135deg, #2e1065 0%, #3b0764 50%, #581c87 100%);">
        <div>
            <div style="display:flex; align-items:center; gap:10px;">
                <h1 class="brand-title">🛡️ National APMC Super Administrator Portal</h1>
                <span class="role-badge role-superadmin">Super Admin Authority</span>
            </div>
            <div class="brand-subtitle" style="color: #e9d5ff;">
                Logged in as <b>{admin_name}</b> ({admin_email}) | National Regulatory & Mandi Oversight Cell
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_overview, tab_interactions, tab_users, tab_listings, tab_orders, tab_mandi, tab_ml = st.tabs([
        "📊 Command Center",
        "🔄 Buyer-Seller Interactions",
        "👥 Users Directory",
        "🌾 All Produce Listings",
        "📦 All Trade Orders",
        "🏛️ Mandi Historical Records",
        "⚙️ Forecasting Models"
    ])

    # ==========================================
    # TAB 1: COMMAND CENTER & PLATFORM OVERVIEW
    # ==========================================
    with tab_overview:
        metrics = get_platform_overview_metrics()

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.markdown(render_metric_card("Registered Farmers", f"{metrics['total_sellers']}", "Produce sellers", trend="neutral"), unsafe_allow_html=True)
        with c2:
            st.markdown(render_metric_card("Registered Buyers", f"{metrics['total_buyers']}", "Traders & Mills", trend="neutral"), unsafe_allow_html=True)
        with c3:
            st.markdown(render_metric_card("Available Stock", f"{metrics['active_stock_qtl']:,.0f} Qtl", f"{metrics['total_listings']} listings", trend="up"), unsafe_allow_html=True)
        with c4:
            st.markdown(render_metric_card("Trade Volume", f"{metrics['total_ordered_qtl']:,.0f} Qtl", f"{metrics['total_orders']} orders", trend="blue"), unsafe_allow_html=True)
        with c5:
            st.markdown(render_metric_card("Gross Trade Value", f"₹{metrics['gross_trade_value']:,.0f}", "Total order value", trend="up"), unsafe_allow_html=True)
        with c6:
            st.markdown(render_metric_card("Logged Interactions", f"{metrics['total_interactions']}", "Negotiations & deals", trend="neutral"), unsafe_allow_html=True)

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

        col_c1, col_c2 = st.columns(2)
        all_orders = get_all_orders()
        all_listings = get_all_listings()

        with col_c1:
            st.markdown("### Trade Volume by Commodity")
            if all_orders:
                df_ord = pd.DataFrame(all_orders)
                crop_grp = df_ord.groupby("commodity")["quantity_quintals"].sum().reset_index()
                fig_crop = px.bar(
                    crop_grp,
                    x="commodity",
                    y="quantity_quintals",
                    color="commodity",
                    labels={"commodity": "Crop", "quantity_quintals": "Volume (Quintals)"},
                    template="plotly_white",
                    height=320
                )
                fig_crop.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_crop, use_container_width=True)
            else:
                st.info("No trade orders placed yet.")

        with col_c2:
            st.markdown("### Order Fulfillment Status")
            if all_orders:
                df_ord = pd.DataFrame(all_orders)
                st_grp = df_ord["status"].value_counts().reset_index()
                st_grp.columns = ["Status", "Count"]
                fig_pie = px.pie(
                    st_grp,
                    names="Status",
                    values="Count",
                    color_discrete_sequence=px.colors.qualitative.Bold,
                    template="plotly_white",
                    height=320
                )
                fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No order status data available.")

    # ==========================================
    # TAB 2: BUYER-SELLER INTERACTIONS & AUDIT
    # ==========================================
    with tab_interactions:
        st.markdown("### 🔄 Buyer & Seller Market Interactions Tracker")
        st.caption("Inspect live communication, order placements, price bids, seller acceptances, and fulfillments between buyers and farmers.")

        users = get_all_users()
        buyers_list = [u["email"] for u in users if u["role"] == "buyer"]
        sellers_list = [u["email"] for u in users if u["role"] == "seller"]

        # Filter bar
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_buyer = st.selectbox("Filter by Buyer", ["All Buyers"] + buyers_list)
        with col_f2:
            filter_seller = st.selectbox("Filter by Farmer / Seller", ["All Sellers"] + sellers_list)
        with col_f3:
            order_filter_input = st.text_input("Filter by Order ID # (Optional)", placeholder="e.g. 1")

        ord_id_param = int(order_filter_input) if order_filter_input.strip().isdigit() else None
        b_email_param = filter_buyer if filter_buyer != "All Buyers" else None
        s_email_param = filter_seller if filter_seller != "All Sellers" else None

        interactions = get_all_interactions(
            buyer_email=b_email_param,
            seller_email=s_email_param,
            order_id=ord_id_param
        )

        # Buyer ↔ Seller Pairings Matrix
        st.markdown("#### 🤝 Active Buyer ↔ Seller Trading Relationships")
        all_ords = get_all_orders()
        if all_ords:
            pairs = []
            for o in all_ords:
                pairs.append({
                    "Buyer": f"{o['buyer_name']} ({o['buyer_email']})",
                    "Farmer / Seller": f"{o['seller_name']} ({o['seller_email']})",
                    "Crop": o["commodity"],
                    "Quantity": f"{o['quantity_quintals']} Qtl",
                    "Rate": f"₹{o['offered_price_per_quintal']:,.0f}",
                    "Total Deal (₹)": f"₹{o['total_amount']:,.0f}",
                    "Status": o["status"],
                    "Date": o["created_at"]
                })
            st.dataframe(pd.DataFrame(pairs), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown(f"#### 📜 Chronological Interaction Log ({len(interactions)} events)")

        if not interactions:
            st.info("No interaction events match the selected criteria.")
        else:
            for item in interactions:
                actor_role = item.get("actor_role", "unknown")
                card_class = "seller-action" if actor_role == "seller" else ("buyer-action" if actor_role == "buyer" else "admin-action")
                badge_color = "#10b981" if actor_role == "seller" else ("#3b82f6" if actor_role == "buyer" else "#8b5cf6")

                st.markdown(f"""
                <div class="interaction-card {card_class}">
                    <div class="interaction-header">
                        <div>
                            <span class="interaction-actor" style="color:{badge_color};">
                                {'🌾 Farmer' if actor_role == 'seller' else '🛒 Buyer'}: {item['actor_name']}
                            </span>
                            <span style="font-size:12px; color:#64748b; margin-left:8px;">
                                ↔ Counterparty: <b>{item['seller_email'] if actor_role == 'buyer' else item['buyer_email']}</b>
                            </span>
                            {f"<span style='background:#f1f5f9; padding:2px 6px; border-radius:4px; font-size:11px; margin-left:6px;'>Order #{item['order_id']}</span>" if item.get('order_id') else ""}
                        </div>
                        <div class="interaction-time">{item['timestamp']}</div>
                    </div>
                    <div class="interaction-body">
                        <b>{item['action_type'].replace('_', ' ')}:</b> {item['message']}
                    </div>
                    {f"<div class='interaction-details'><b>Logistics / Negotiation Remarks:</b> {item['details']}</div>" if item.get('details') else ""}
                </div>
                """, unsafe_allow_html=True)

    # ==========================================
    # TAB 3: USERS DIRECTORY
    # ==========================================
    with tab_users:
        st.markdown("### 👥 Registered Users Directory")
        st.caption("Full directory of all registered farmers, grain merchants, and administrative personnel.")

        all_u = get_all_users()
        user_rows = []
        for u in all_u:
            user_rows.append({
                "User ID": f"#{u['id']}",
                "Full Name": u["name"],
                "Email": u["email"],
                "Role": u["role"].upper(),
                "Phone": u.get("phone", "-"),
                "State": u.get("state", "-"),
                "Mandi / Center": u.get("mandi", "-"),
                "Address": u.get("address", "-"),
                "Joined": u.get("created_at", "-")
            })
        st.dataframe(pd.DataFrame(user_rows), use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 4: ALL PRODUCE LISTINGS
    # ==========================================
    with tab_listings:
        st.markdown("### 🌾 Global Produce Inventory Audit")
        st.caption("Review all produce listed by all farmers across India. Super Admins can remove fraudulent or duplicate listings.")

        listings = get_all_listings()
        if not listings:
            st.info("No listings found in the database.")
        else:
            list_table = []
            for item in listings:
                list_table.append({
                    "Listing ID": f"#{item['id']}",
                    "Farmer": item["seller_name"],
                    "Email": item["seller_email"],
                    "Crop": item["commodity"],
                    "Variety": item.get("variety", "-"),
                    "Total (Qtl)": item["quantity_quintals"],
                    "Available (Qtl)": item["available_quintals"],
                    "Rate (₹/Qtl)": f"₹{item['price_per_quintal']:,.0f}",
                    "Mandi": item["mandi"],
                    "State": item["state"],
                    "Status": item["status"],
                    "Date": item["created_at"]
                })
            st.dataframe(pd.DataFrame(list_table), use_container_width=True, hide_index=True)

            with st.expander("⚠️ Administrative Action: Delete Listing"):
                del_id = st.number_input("Enter Listing ID to delete", min_value=1, step=1)
                if st.button("Delete Listing Immediately"):
                    ok, msg = admin_delete_listing(del_id)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    # ==========================================
    # TAB 5: ALL TRADE ORDERS
    # ==========================================
    with tab_orders:
        st.markdown("### 📦 Global Orders Ledger")
        st.caption("Complete transactional record of all purchase deals between buyers and sellers.")

        orders = get_all_orders()
        if not orders:
            st.info("No orders placed yet.")
        else:
            ord_table = []
            for o in orders:
                ord_table.append({
                    "Order ID": f"#{o['id']}",
                    "Buyer Name": o["buyer_name"],
                    "Buyer Email": o["buyer_email"],
                    "Farmer Name": o["seller_name"],
                    "Farmer Email": o["seller_email"],
                    "Crop": o["commodity"],
                    "Qty (Qtl)": o["quantity_quintals"],
                    "Rate (₹/Qtl)": f"₹{o['offered_price_per_quintal']:,.0f}",
                    "Total Deal (₹)": f"₹{o['total_amount']:,.0f}",
                    "Delivery Mandi": f"{o.get('mandi', '')}, {o.get('state', '')}",
                    "Status": o["status"],
                    "Date": o["created_at"]
                })
            df_ord_view = pd.DataFrame(ord_table)
            st.dataframe(df_ord_view, use_container_width=True, hide_index=True)

            csv_data = df_ord_view.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Complete Orders Ledger (CSV)",
                data=csv_data,
                file_name=f"mandi_trade_ledger_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    # ==========================================
    # TAB 6: APMC MANDI HISTORICAL RECORDS
    # ==========================================
    with tab_mandi:
        st.markdown("### 🏛️ APMC Mandi Benchmark Records (360,000+ Records)")
        st.caption("Inspect official APMC mandi arrival records, modal prices, and minimum/maximum rates.")

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            sel_m_crop = st.selectbox("Select Commodity", ["All Crops"] + list(CROPS_METADATA.keys()))
        with m_col2:
            sel_m_state = st.selectbox("Select State", ["All States"] + list(STATE_MANDIS.keys()))

        df_bench = load_data_from_db(
            commodity=sel_m_crop if sel_m_crop != "All Crops" else None,
            state=sel_m_state if sel_m_state != "All States" else None
        )
        if not df_bench.empty:
            st.write(f"Showing recent records out of **{len(df_bench):,} matching entries**:")
            st.dataframe(df_bench.tail(100), use_container_width=True, hide_index=True)
        else:
            st.warning("No benchmark records found.")

    # ==========================================
    # TAB 7: FORECASTING MODELS
    # ==========================================
    with tab_ml:
        render_model_management_page()
