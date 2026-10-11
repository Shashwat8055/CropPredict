"""
CropPricePredict - Utility Calculations
Handles yield estimation, profit calculation, risk assessment, and financial metrics.
"""
from typing import Dict, Any, List, Optional

def calculate_crop_profitability(
    crop_name: str,
    farm_area_acres: float,
    expected_yield_per_acre: float,
    predicted_market_price_per_qtl: float,
    estimated_cost_per_acre: float
) -> Dict[str, Any]:
    """
    Calculates expected revenue, total profit, profit per acre, and ROI.
    
    Formula:
    - Total Yield = Farm Area * Expected Yield per Acre
    - Expected Revenue = Total Yield * Predicted Market Price
    - Total Cost = Farm Area * Estimated Cost per Acre
    - Total Profit = Expected Revenue - Total Cost
    - Profit per Acre = Total Profit / Farm Area
    """
    total_yield_qtl = farm_area_acres * expected_yield_per_acre
    expected_revenue = total_yield_qtl * predicted_market_price_per_qtl
    total_cost = farm_area_acres * estimated_cost_per_acre
    total_profit = expected_revenue - total_cost
    profit_per_acre = total_profit / farm_area_acres if farm_area_acres > 0 else 0.0
    roi_pct = ((expected_revenue - total_cost) / total_cost * 100.0) if total_cost > 0 else 0.0

    return {
        "crop_name": crop_name,
        "farm_area_acres": farm_area_acres,
        "total_yield_qtl": round(total_yield_qtl, 2),
        "expected_revenue": round(expected_revenue, 2),
        "total_cost": round(total_cost, 2),
        "total_profit": round(total_profit, 2),
        "profit_per_acre": round(profit_per_acre, 2),
        "roi_pct": round(roi_pct, 2)
    }

def calculate_risk_level(
    price_volatility_pct: float,
    model_mape: float,
    perishability: str = "Medium",
    weather_risk: str = "Low"
) -> Dict[str, Any]:
    """
    Evaluates combined agricultural and market risk level (Low, Moderate, High).
    """
    risk_score = 0.0
    
    # Volatility contribution
    if price_volatility_pct > 15.0:
        risk_score += 35.0
    elif price_volatility_pct > 8.0:
        risk_score += 20.0
    else:
        risk_score += 10.0

    # Model error contribution
    if model_mape > 12.0:
        risk_score += 25.0
    elif model_mape > 6.0:
        risk_score += 15.0
    else:
        risk_score += 5.0

    # Perishability factor
    if perishability == "High":
        risk_score += 25.0
    elif perishability == "Medium":
        risk_score += 15.0
    else:
        risk_score += 5.0

    # Weather factor
    if weather_risk == "High":
        risk_score += 15.0
    elif weather_risk == "Medium":
        risk_score += 10.0
    else:
        risk_score += 5.0

    if risk_score >= 65.0:
        level = "High Risk"
        color = "#EF4444"
        explanation = "High price volatility and perishable crop nature increase market vulnerability."
    elif risk_score >= 40.0:
        level = "Moderate Risk"
        color = "#F59E0B"
        explanation = "Moderate seasonal price fluctuations within expected market thresholds."
    else:
        level = "Low Risk"
        color = "#10B981"
        explanation = "Stable market demand, strong shelf life, and robust prediction confidence."

    return {
        "risk_level": level,
        "risk_score": round(risk_score, 1),
        "color": color,
        "explanation": explanation
    }
