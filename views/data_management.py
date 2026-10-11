"""
CropPricePredict - Data Management Page
Upload dataset CSV files, preview data, check missing values, remove duplicates, and download cleaned data.
"""
import streamlit as st
import pandas as pd
import numpy as np

from data.database import get_database_summary, load_data_from_db, bulk_insert_dataframe
from utils.validation import validate_dataset_schema
from ml.preprocessing import preprocess_crop_dataset

def render_data_management_page():
    st.markdown("""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">Data Management</h1>
            <div class="brand-subtitle">Upload agricultural dataset CSVs, validate columns, handle missing values, and manage database records</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    db_info = get_database_summary()

    # DB Overview Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Records", f"{db_info['total_rows']:,}")
    with c2:
        st.metric("Total Crops", f"{len(db_info['crops'])}")
    with c3:
        st.metric("Total Mandis", f"{len(db_info['mandis'])}")
    with c4:
        st.metric("Date Span", f"{db_info['min_date']} to {db_info['max_date']}")

    st.markdown("---")

    # CSV Upload Section
    st.markdown("### Upload Dataset (CSV File)")
    uploaded_file = st.file_uploader("Upload Crop Price CSV", type=["csv"])

    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file)
            st.success(f"File uploaded! Loaded **{len(df_upload):,} rows** and **{len(df_upload.columns)} columns**.")

            is_valid, val_report = validate_dataset_schema(df_upload)

            # Schema Validation Breakdown
            if is_valid:
                st.info("**Column Validation Passed**: All required columns (`date`, `crop`, `price`) are present.")
            else:
                st.error(f"**Missing Columns**: {val_report['status_message']}")

            # Summary Metrics
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                st.write("**Required Columns**:", val_report["found_required"])
            with col_v2:
                st.write("**Recommended Columns**:", val_report["found_recommended"])
            with col_v3:
                st.write("**Duplicate Rows Detected**:", val_report["duplicate_count"])

            st.markdown("#### Data Preview")
            st.dataframe(df_upload.head(10), use_container_width=True)

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Clean Data & Import to Database", type="primary", use_container_width=True):
                    df_clean, _ = preprocess_crop_dataset(df_upload)
                    inserted, msg = bulk_insert_dataframe(df_clean)
                    st.success(msg)
                    st.experimental_rerun()

            with col_btn2:
                df_clean, _ = preprocess_crop_dataset(df_upload)
                csv_bytes = df_clean.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Cleaned Dataset",
                    data=csv_bytes,
                    file_name="cleaned_crop_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"Failed to read CSV file: {e}")

    st.markdown("---")
    st.markdown("### Database Preview & Export")
    df_db = load_data_from_db()
    if not df_db.empty:
        st.dataframe(df_db.head(20), use_container_width=True)
        csv_db = df_db.to_csv(index=False).encode("utf-8")
        st.download_button("Download Full Database (CSV)", data=csv_db, file_name="full_mandi_database.csv", mime="text/csv")
