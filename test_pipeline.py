"""
CropPricePredict - Comprehensive End-to-End Automated Test Suite
"""
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
from data.database import (
    init_database, load_data_from_db, insert_single_record,
    bulk_insert_dataframe, get_database_summary
)
from utils.validation import validate_dataset_schema
from utils.calculations import calculate_crop_profitability, calculate_risk_level
from ml.preprocessing import preprocess_crop_dataset
from ml.feature_engineering import create_time_series_features
from ml.train_model import train_and_evaluate_models
from ml.predict import predict_future_crop_prices
from ml.evaluate import evaluate_regression_model
from core.advisor import analyze_selling_window, find_inter_mandi_arbitrage

def run_all_tests():
    print("=" * 70)
    print("[*] Starting CropPricePredict Automated Test Suite...")
    print("=" * 70)

    # 1. Database & Ingestion Test
    print("\n[1/6] Testing Database Initialization & Summary...")
    init_database()
    summary = get_database_summary()
    assert summary["total_rows"] > 0, "Database should contain rows"
    assert len(summary["crops"]) >= 5, "Database should have multiple crops"
    print(f"  [OK] Database verified: {summary['total_rows']:,} rows, {len(summary['crops'])} crops, {len(summary['mandis'])} mandis.")

    # 2. Schema Validation Test
    print("\n[2/6] Testing Schema Validation Utility...")
    df_sample = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02"],
        "crop": ["Wheat", "Wheat"],
        "price": [2300, 2350],
        "state": ["Punjab", "Punjab"]
    })
    is_valid, report = validate_dataset_schema(df_sample)
    assert is_valid, "Valid dataset should pass schema validation"
    print("  [OK] Schema validation passed.")

    # 3. Preprocessing & Feature Engineering Test
    print("\n[3/6] Testing Preprocessing & Time-Series Feature Engineering...")
    df_wheat = load_data_from_db(commodity="Wheat")
    df_clean, stats = preprocess_crop_dataset(df_wheat, commodity="Wheat")
    assert not df_clean.empty, "Cleaned dataset should not be empty"
    
    df_feat, feat_cols = create_time_series_features(df_clean, target_col="price")
    assert not df_feat.empty, "Feature dataframe should not be empty"
    assert "lag_1" in feat_cols and "ma_7" in feat_cols, "Features should include lag_1 and ma_7"
    print(f"  [OK] Generated {len(feat_cols)} features for {len(df_feat)} historical rows.")

    # 4. Supervised Model Training & Time-Series Split Test
    print("\n[4/6] Testing Chronological Model Training & Comparison...")
    best_model, meta, comp_df = train_and_evaluate_models(df_wheat, commodity="Wheat")
    assert meta["metrics"]["r2"] > 0.50, f"R2 score should be reasonable (>0.5), got {meta['metrics']['r2']}"
    assert len(comp_df) >= 3, "Comparison table should evaluate at least 3 models"
    print(f"  [OK] Selected best model '{meta['best_model_name']}' with R2: {meta['metrics']['r2']:.4f}, RMSE: Rs. {meta['metrics']['rmse']:.2f}.")

    # 5. Multi-Horizon Forecast Engine Test
    print("\n[5/6] Testing Multi-Horizon Forecast Engine (1 to 90 Days)...")
    forecast_df, sum_dict = predict_future_crop_prices(df_wheat, commodity="Wheat", horizon_days=30)
    assert len(forecast_df) == 30, "Forecast should contain 30 rows"
    assert (forecast_df["upper_bound_90"] >= forecast_df["predicted_price"]).all(), "Upper bound must be >= predicted"
    assert (forecast_df["lower_bound_90"] <= forecast_df["predicted_price"]).all(), "Lower bound must be <= predicted"
    print(f"  [OK] 30-Day Forecast: Current Rs. {sum_dict['current_price']:.2f} -> Predicted Rs. {sum_dict['predicted_price']:.2f} ({sum_dict['pct_change']:+.2f}%).")

    # 6. Multiclass Crop Classification Engine Test
    print("\n[6/8] Testing Multiclass Crop Classification Engine...")
    from ml.crop_classifier import train_and_evaluate_classifiers, predict_crop_suitability
    clf_model, clf_meta, clf_comp = train_and_evaluate_classifiers()
    assert clf_meta["metrics"]["accuracy"] > 0.85, f"Classifier accuracy should be > 85%, got {clf_meta['metrics']['accuracy']}"
    assert len(clf_comp) >= 4, "Leaderboard should evaluate at least 4 classifiers"
    
    top_pred = predict_crop_suitability(n=95, p=50, k=40, temperature=22.0, humidity=65.0, ph=6.8, rainfall=480.0, top_k=3)
    assert len(top_pred) == 3, "Prediction should return top 3 crops"
    assert "confidence_pct" in top_pred[0], "Prediction should include confidence percentage"
    print(f"  [OK] Crop Classifier: Best model '{clf_meta['best_model_name']}' achieved {clf_meta['metrics']['accuracy']*100:.2f}% accuracy. Top predicted: {top_pred[0]['crop']} ({top_pred[0]['confidence_pct']:.1f}%).")

    # 7. Financial Profitability & Selling Advisor Test
    print("\n[7/8] Testing Financial Calculations & Selling Advisor...")
    prof_info = calculate_crop_profitability(
        crop_name="Wheat",
        farm_area_acres=5.0,
        expected_yield_per_acre=22.0,
        predicted_market_price_per_qtl=2400.0,
        estimated_cost_per_acre=24000.0
    )
    assert prof_info["expected_revenue"] == 264000.0, "Revenue calculation error"
    assert prof_info["total_cost"] == 120000.0, "Cost calculation error"
    assert prof_info["total_profit"] == 144000.0, "Profit calculation error"
    print(f"  [OK] Profitability: Total Profit Rs. {prof_info['total_profit']:,.2f} for {prof_info['farm_area_acres']} acres.")

    adv_res = analyze_selling_window(forecast_df, commodity="Wheat", current_price=sum_dict["current_price"])
    assert "recommendation" in adv_res, "Selling advisor must return recommendation"
    print(f"  [OK] Selling Advisor: {adv_res['recommendation']}")

    # 8. Multi-Role Marketplace & Super Admin Oversight Test
    print("\n[8/8] Testing Multi-Role Marketplace, Data Isolation & Super Admin Oversight...")
    from data.marketplace_db import (
        init_marketplace_tables, authenticate_user, register_user,
        get_seller_listings, add_seller_listing, update_seller_listing,
        get_marketplace_listings, place_buyer_order, get_buyer_orders,
        cancel_order_by_buyer, update_order_status_by_seller,
        get_all_users, get_all_listings, get_all_orders, get_all_interactions,
        get_platform_overview_metrics, is_superadmin_email
    )
    init_marketplace_tables()

    # Verify Super Admin rule
    assert is_superadmin_email("admin@super.com") is True, "admin@super.com must be identified as superadmin"
    assert is_superadmin_email("audit.officer@super.com") is True, "*@super.com must be identified as superadmin"
    assert is_superadmin_email("farmer@gmail.com") is False, "Regular email should not be superadmin"

    # Authenticate default users
    seller_u = authenticate_user("ramesh.farmer@mandi.in", "farmer123")
    assert seller_u is not None and seller_u["role"] == "seller", "Seller auth failed"
    buyer_u = authenticate_user("suresh.trader@mandi.in", "buyer123")
    assert buyer_u is not None and buyer_u["role"] == "buyer", "Buyer auth failed"
    admin_u = authenticate_user("admin@super.com", "admin123")
    assert admin_u is not None and admin_u["role"] == "superadmin", "Super admin auth failed"
    print("  [OK] Successfully authenticated Seller, Buyer, and Super Admin (@super.com).")

    # Verify strict data isolation: Buyer cannot modify seller listing
    seller_listings = get_seller_listings(seller_u["email"])
    assert len(seller_listings) > 0, "Seller should have listings"
    first_listing = seller_listings[0]
    
    # Tamper test 1: Buyer tries to update seller's listing
    tamper_ok, msg = update_seller_listing(
        listing_id=first_listing["id"],
        seller_email=buyer_u["email"],  # buyer trying to update
        quantity_quintals=999,
        price_per_quintal=10,
        quality_grade="Hacked",
        status="Active",
        notes="Hacked"
    )
    assert tamper_ok is False, "Security failure: Buyer was able to modify seller listing!"
    print("  [OK] Permission verified: Buyer cannot alter seller listings.")

    # Tamper test 2: Cancel another buyer's order
    buyer_orders = get_buyer_orders(buyer_u["email"])
    assert len(buyer_orders) > 0, "Buyer should have orders"
    first_order = buyer_orders[0]
    tamper_cancel_ok, msg = cancel_order_by_buyer(first_order["id"], "unauthorized@buyer.com", "Malicious")
    assert tamper_cancel_ok is False, "Security failure: Unauthorized buyer cancelled order!"
    print("  [OK] Permission verified: User cannot cancel other buyers' orders.")

    # Super Admin oversight test: Query interactions
    all_interactions = get_all_interactions()
    assert len(all_interactions) > 0, "Interactions log should not be empty"
    print(f"  [OK] Super Admin oversight verified: {len(all_interactions)} buyer-seller interaction events logged.")

    # Super Admin platform metrics
    plat_metrics = get_platform_overview_metrics()
    assert plat_metrics["total_sellers"] >= 2, "Should have sellers"
    assert plat_metrics["total_buyers"] >= 2, "Should have buyers"
    assert plat_metrics["total_orders"] >= 3, "Should have orders"
    print(f"  [OK] Platform overview verified: {plat_metrics['total_sellers']} sellers, {plat_metrics['total_buyers']} buyers, Rs. {plat_metrics['gross_trade_value']:,.0f} trade value.")

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL AUTOMATED TESTS (8/8) PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
