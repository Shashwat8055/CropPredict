"""
CropPricePredict - UI Design System & Styling
Provides clean, practical styling for agricultural trade, buyer/seller dashboards, and interaction tracking.
"""

def get_custom_css() -> str:
    return """
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Application Styles */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Top Brand Header Bar */
    .brand-header {
        background: linear-gradient(135deg, #1e3a2f 0%, #164e3b 50%, #065f46 100%);
        border-radius: 14px;
        padding: 22px 28px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 8px 20px -4px rgba(6, 78, 59, 0.25);
        display: flex;
        align-items: center;
        justify-content: space-between;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }
    .brand-title {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        color: #ffffff;
    }
    .brand-subtitle {
        font-size: 13.5px;
        color: #a7f3d0;
        margin-top: 4px;
        font-weight: 400;
    }

    /* Role Badges */
    .role-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .role-seller {
        background: #059669;
        color: #ffffff;
    }
    .role-buyer {
        background: #2563eb;
        color: #ffffff;
    }
    .role-superadmin {
        background: #7c3aed;
        color: #ffffff;
    }

    /* Metric Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease-in-out;
    }
    .metric-card:hover {
        border-color: #10b981;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.06);
    }
    .metric-title {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 2px;
    }
    .metric-subtitle {
        font-size: 11.5px;
        font-weight: 500;
    }
    .text-emerald { color: #059669; }
    .text-rose { color: #e11d48; }
    .text-blue { color: #2563eb; }
    .text-amber { color: #d97706; }

    /* Order Status Badges */
    .order-status {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .status-pending { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .status-accepted { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .status-dispatched { background: #e0e7ff; color: #3730a3; border: 1px solid #c7d2fe; }
    .status-completed { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .status-cancelled { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .status-declined { background: #f3f4f6; color: #4b5563; border: 1px solid #e5e7eb; }

    /* Interaction Timeline Card */
    .interaction-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .interaction-card.seller-action {
        border-left-color: #10b981;
    }
    .interaction-card.buyer-action {
        border-left-color: #3b82f6;
    }
    .interaction-card.admin-action {
        border-left-color: #8b5cf6;
    }
    .interaction-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .interaction-actor {
        font-weight: 700;
        font-size: 13px;
        color: #1e293b;
    }
    .interaction-time {
        font-size: 11px;
        color: #94a3b8;
    }
    .interaction-body {
        font-size: 13px;
        color: #334155;
        line-height: 1.4;
    }
    .interaction-details {
        margin-top: 6px;
        padding: 6px 10px;
        background: #f8fafc;
        border-radius: 6px;
        font-size: 12px;
        color: #475569;
        border: 1px dashed #cbd5e1;
    }

    /* Product Marketplace Card */
    .product-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    .product-card:hover {
        border-color: #059669;
        box-shadow: 0 4px 12px rgba(5,150,105,0.08);
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    /* User Profile Pill */
    .user-pill {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 14px;
    }

    /* Hide Default Streamlit Multi-Page Navigation */
    [data-testid="stSidebarNav"],
    nav[data-testid="stSidebarNav"],
    div[data-testid="stSidebarNav"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        overflow: hidden !important;
    }
    </style>
    """

def render_metric_card(title: str, value: str, subtitle: str = "", trend: str = "neutral") -> str:
    """Renders HTML component for responsive metric card."""
    color_class = "text-emerald" if trend == "up" else ("text-rose" if trend == "down" else ("text-blue" if trend == "blue" else "text-amber"))
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtitle {color_class}">{subtitle}</div>
    </div>
    """

def render_status_badge(status: str) -> str:
    """Renders formatted HTML badge for order status."""
    st_low = status.lower()
    css_class = f"status-{st_low}" if st_low in ["pending", "accepted", "dispatched", "completed", "cancelled", "declined"] else "status-pending"
    return f'<span class="order-status {css_class}">{status}</span>'

def render_role_badge(role: str) -> str:
    """Renders formatted HTML badge for user role."""
    r_low = role.lower()
    if r_low == "seller":
        return '<span class="role-badge role-seller">🌾 Farmer / Seller</span>'
    elif r_low == "buyer":
        return '<span class="role-badge role-buyer">🛒 Trader / Buyer</span>'
    elif r_low == "superadmin":
        return '<span class="role-badge role-superadmin">🛡️ Super Administrator</span>'
    return f'<span class="role-badge role-seller">{role.title()}</span>'
