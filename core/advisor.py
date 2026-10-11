"""
CropPricePredict - Market Intelligence & Selling Advisor
Includes Sell vs. Hold optimization, Storage cost analysis, Inter-Mandi Arbitrage, and Price Risk Sentinel.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from config import CROPS_METADATA, STATE_MANDIS

def analyze_selling_window(
    forecast_df: pd.DataFrame,
    commodity: str = "Wheat",
    current_price: float = 2275.0,
    quantity_quintals: float = 100.0,
    custom_storage_cost_per_month: Optional[float] = None
) -> Dict[str, Any]:
    """
    Evaluates net profit of selling today vs holding across future forecast dates.
    Accounts for holding storage costs and perishability risks.
    """
    meta = CROPS_METADATA.get(commodity, {})
    monthly_storage = custom_storage_cost_per_month if custom_storage_cost_per_month is not None else meta.get("storage_cost_per_month_quintal", 20.0)
    weekly_storage = monthly_storage / 4.33
    shelf_life_months = meta.get("shelf_life_months", 6)

    # Aggregate weekly forecast targets
    forecast_df = forecast_df.copy()
    if "date" in forecast_df.columns:
        forecast_df["date"] = pd.to_datetime(forecast_df["date"])

    analysis_rows = []
    
    # Week 0 (Today / Immediate Sale)
    immediate_revenue = current_price * quantity_quintals
    analysis_rows.append({
        "timeframe": "Today (Immediate)",
        "days_ahead": 0,
        "date": "Today",
        "projected_price": current_price,
        "price_delta": 0.0,
        "pct_delta": 0.0,
        "storage_cost_per_qtl": 0.0,
        "net_price_per_qtl": current_price,
        "total_net_revenue": immediate_revenue,
        "net_profit_diff": 0.0
    })

    # Sample milestones: Day 7, Day 14, Day 21, Day 30, Day 45, Day 60, Day 90
    max_days = forecast_df["forecast_day"].max() if "forecast_day" in forecast_df.columns else len(forecast_df)
    milestone_days = [d for d in [7, 14, 21, 30, 45, 60, 90] if d <= max_days]

    for d in milestone_days:
        sub = forecast_df[forecast_df["forecast_day"] == d]
        if sub.empty:
            continue
        row = sub.iloc[0]
        pred_p = row["predicted_price"]
        f_date = row["date"].strftime("%d %b %Y") if hasattr(row["date"], "strftime") else str(row["date"])

        weeks_held = d / 7.0
        storage_cost = weeks_held * weekly_storage
        
        # Perishability penalty for short-lived crops held too long
        perish_penalty = 0.0
        if weeks_held > (shelf_life_months * 4.33 * 0.75):
            perish_penalty = pred_p * 0.08

        net_p = pred_p - storage_cost - perish_penalty
        net_revenue = net_p * quantity_quintals
        profit_diff = net_revenue - immediate_revenue
        pct_change = ((pred_p - current_price) / current_price) * 100.0

        analysis_rows.append({
            "timeframe": f"{d} Days Ahead",
            "days_ahead": d,
            "date": f_date,
            "projected_price": round(pred_p, 2),
            "price_delta": round(pred_p - current_price, 2),
            "pct_delta": round(pct_change, 2),
            "storage_cost_per_qtl": round(storage_cost, 2),
            "net_price_per_qtl": round(net_p, 2),
            "total_net_revenue": round(net_revenue, 2),
            "net_profit_diff": round(profit_diff, 2)
        })

    analysis_df = pd.DataFrame(analysis_rows)
    best_option = analysis_df.loc[analysis_df["net_profit_diff"].idxmax()]

    if best_option["days_ahead"] == 0 or best_option["net_profit_diff"] <= (current_price * 0.015 * quantity_quintals):
        recommendation = "SELL NOW"
        badge_color = "#10B981"  # Emerald green
        reasoning = (
            f"Holding is not advised. Future projected price gains do not adequately exceed warehousing/storage "
            f"costs (₹{monthly_storage:.1f}/Qtl/mo) and market volatility risks. Selling today maximizes secure returns."
        )
    else:
        recommendation = f"HOLD FOR {best_option['days_ahead']} DAYS"
        badge_color = "#3B82F6"  # Royal blue
        reasoning = (
            f"Hold recommendation: Expected price appreciation reaches ₹{best_option['projected_price']:.2f}/Qtl "
            f"by {best_option['date']}. Net gain after ₹{best_option['storage_cost_per_qtl']:.2f}/Qtl storage cost "
            f"is +₹{best_option['net_profit_diff']:,.2f} for {quantity_quintals:.0f} Quintals (+{best_option['pct_delta']:.1f}%)."
        )

    return {
        "recommendation": recommendation,
        "badge_color": badge_color,
        "best_timeframe": best_option["timeframe"],
        "best_date": best_option["date"],
        "max_net_profit_gain": best_option["net_profit_diff"],
        "reasoning": reasoning,
        "comparison_table": analysis_df
    }

def find_inter_mandi_arbitrage(
    df_latest: pd.DataFrame,
    commodity: str = "Wheat",
    origin_mandi: str = "Ludhiana Mandi",
    transport_rate_per_km_qtl: float = 0.25
) -> pd.DataFrame:
    """
    Compares commodity prices across all mandis to find spatial price arbitrage opportunities.
    """
    sub = df_latest[df_latest["commodity"] == commodity]
    if sub.empty:
        return pd.DataFrame()

    # Get most recent price per mandi
    latest_per_mandi = sub.sort_values("date").groupby(["state", "market"]).last().reset_index()
    
    origin_rows = latest_per_mandi[latest_per_mandi["market"] == origin_mandi]
    if origin_rows.empty:
        origin_price = latest_per_mandi["modal_price"].median()
        origin_lat = 28.0
        origin_lon = 77.0
    else:
        origin_price = origin_rows["modal_price"].iloc[0]
        origin_lat = origin_rows["latitude"].iloc[0] if "latitude" in origin_rows.columns else 28.0
        origin_lon = origin_rows["longitude"].iloc[0] if "longitude" in origin_rows.columns else 77.0

    arbitrage_list = []
    for _, row in latest_per_mandi.iterrows():
        target_mandi = row["market"]
        target_state = row["state"]
        target_price = row["modal_price"]
        target_lat = row.get("latitude", 28.0)
        target_lon = row.get("longitude", 77.0)

        # Approximate distance in KM using Euclidean coordinate degrees (~111 km/deg)
        dist_km = float(np.sqrt((target_lat - origin_lat)**2 + (target_lon - origin_lon)**2) * 111.0)
        dist_km = max(15.0 if target_mandi != origin_mandi else 0.0, dist_km)

        est_transport_cost = round(dist_km * transport_rate_per_km_qtl, 2)
        price_spread = round(target_price - origin_price, 2)
        net_arbitrage_margin = round(price_spread - est_transport_cost, 2)

        arbitrage_list.append({
            "Market": target_mandi,
            "State": target_state,
            "Modal Price (₹/Qtl)": target_price,
            "Est Distance (km)": round(dist_km, 1),
            "Transport Cost (₹/Qtl)": est_transport_cost,
            "Price Spread (₹)": price_spread,
            "Net Profit Margin (₹/Qtl)": net_arbitrage_margin,
            "Opportunity": "Profitable Arbitrage" if net_arbitrage_margin > 30 else ("Neutral" if net_arbitrage_margin >= -10 else "Not Viable")
        })

    arb_df = pd.DataFrame(arbitrage_list)
    return arb_df.sort_values(by="Net Profit Margin (₹/Qtl)", ascending=False).reset_index(drop=True)

def assess_market_risk(
    historical_sub: pd.DataFrame,
    commodity: str = "Wheat"
) -> Dict[str, Any]:
    """
    Computes volatility risk score, recent supply momentum, and market stability indicators.
    """
    if len(historical_sub) < 14:
        return {
            "risk_level": "Moderate",
            "risk_score": 50,
            "volatility_pct": 5.0,
            "trend": "Stable",
            "alerts": ["Limited historical data points for risk computation."]
        }

    prices = historical_sub["modal_price"].values
    recent_prices = prices[-30:] if len(prices) >= 30 else prices
    returns = np.diff(recent_prices) / (recent_prices[:-1] + 1e-5)
    volatility = float(np.std(returns) * np.sqrt(30) * 100.0)

    # Trend calculation
    price_change_30d = float((recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100.0)
    
    alerts = []
    if volatility > 18.0:
        risk_level = "High Risk / High Volatility"
        risk_score = 85
        alerts.append("Elevated price volatility detected in recent market sessions.")
    elif volatility > 9.0:
        risk_level = "Moderate Volatility"
        risk_score = 55
        alerts.append("Standard seasonal price fluctuations within normal historical bounds.")
    else:
        risk_level = "Low Risk / Stable"
        risk_score = 25
        alerts.append("Market exhibiting high price stability with steady arrival patterns.")

    if price_change_30d > 12.0:
        alerts.append(f"Strong Bullish Momentum: +{price_change_30d:.1f}% surge over the last 30 days.")
    elif price_change_30d < -12.0:
        alerts.append(f"Bearish Inflow Shock: {price_change_30d:.1f}% decline due to harvesting influx.")

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "volatility_pct": round(volatility, 2),
        "price_change_30d_pct": round(price_change_30d, 2),
        "alerts": alerts
    }
