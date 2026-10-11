"""
CropPricePredict - Database & Storage Manager
Handles SQLite persistence, CSV/Excel import with auto column mapping, and record insertion.
"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from config import DB_PATH, DEFAULT_DATASET_PATH, CROPS_METADATA, STATE_MANDIS
from data.generator import generate_crop_market_data

TABLE_NAME = "mandi_crop_prices"

SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    state TEXT NOT NULL,
    market TEXT NOT NULL,
    commodity TEXT NOT NULL,
    category TEXT,
    arrivals_quintal REAL,
    min_price REAL,
    max_price REAL,
    modal_price REAL NOT NULL,
    temperature_c REAL,
    rainfall_mm REAL,
    fuel_index REAL,
    latitude REAL,
    longitude REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, state, market, commodity) ON CONFLICT REPLACE
);
"""

def init_database():
    """Initializes SQLite database schema and seeds initial data if empty."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(SCHEMA_SQL)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        count = cursor.fetchone()[0]
        
        if count == 0:
            if DEFAULT_DATASET_PATH.exists():
                df = pd.read_csv(DEFAULT_DATASET_PATH)
            else:
                # Generate seed dataset
                df = generate_crop_market_data(
                    start_date="2023-01-01",
                    end_date="2026-08-11"
                )
                df.to_csv(DEFAULT_DATASET_PATH, index=False)
            
            # Format date as string
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            
            df.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
            conn.commit()

def load_data_from_db(
    commodity: Optional[str] = None,
    state: Optional[str] = None,
    market: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """Loads filtered market data from SQLite database."""
    init_database()
    with sqlite3.connect(DB_PATH) as conn:
        query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
        params = []

        if commodity and commodity != "All Crops":
            query += " AND commodity = ?"
            params.append(commodity)
        if state and state != "All States":
            query += " AND state = ?"
            params.append(state)
        if market and market != "All Mandis":
            query += " AND market = ?"
            params.append(market)
        if start_date:
            query += " AND date >= ?"
            params.append(str(start_date))
        if end_date:
            query += " AND date <= ?"
            params.append(str(end_date))

        query += " ORDER BY date ASC"
        df = pd.read_sql_query(query, conn, params=params)

    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df

def insert_single_record(record: Dict[str, Any]) -> Tuple[bool, str]:
    """Inserts a single new crop price record into SQLite."""
    try:
        init_database()
        required_fields = ["date", "state", "market", "commodity", "modal_price"]
        for field in required_fields:
            if field not in record or record[field] is None:
                return False, f"Missing required field: {field}"

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            insert_query = f"""
            INSERT INTO {TABLE_NAME} (
                date, state, market, commodity, category,
                arrivals_quintal, min_price, max_price, modal_price,
                temperature_c, rainfall_mm, fuel_index, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, state, market, commodity) DO UPDATE SET
                arrivals_quintal = excluded.arrivals_quintal,
                min_price = excluded.min_price,
                max_price = excluded.max_price,
                modal_price = excluded.modal_price,
                temperature_c = excluded.temperature_c,
                rainfall_mm = excluded.rainfall_mm,
                fuel_index = excluded.fuel_index;
            """
            cursor.execute(insert_query, (
                str(record["date"]),
                str(record["state"]),
                str(record["market"]),
                str(record["commodity"]),
                str(record.get("category", CROPS_METADATA.get(record["commodity"], {}).get("category", "General"))),
                float(record.get("arrivals_quintal", 1000.0)),
                float(record.get("min_price", record["modal_price"] * 0.95)),
                float(record.get("max_price", record["modal_price"] * 1.05)),
                float(record["modal_price"]),
                float(record.get("temperature_c", 28.0)),
                float(record.get("rainfall_mm", 0.0)),
                float(record.get("fuel_index", 105.0)),
                float(record.get("latitude", STATE_MANDIS.get(record.get("state"), {}).get("lat", 25.0))),
                float(record.get("longitude", STATE_MANDIS.get(record.get("state"), {}).get("lon", 75.0))),
            ))
            conn.commit()
        return True, "Record saved successfully!"
    except Exception as e:
        return False, f"Database Error: {str(e)}"

def bulk_insert_dataframe(df: pd.DataFrame) -> Tuple[int, str]:
    """Inserts or updates multiple records into the database."""
    try:
        init_database()
        df_copy = df.copy()
        
        # Ensure date format
        if "date" in df_copy.columns:
            df_copy["date"] = pd.to_datetime(df_copy["date"]).dt.strftime("%Y-%m-%d")

        # Required columns mapping validation
        if "modal_price" not in df_copy.columns and "price" in df_copy.columns:
            df_copy["modal_price"] = df_copy["price"]
        if "commodity" not in df_copy.columns and "crop" in df_copy.columns:
            df_copy["commodity"] = df_copy["crop"]
        if "market" not in df_copy.columns and "mandi" in df_copy.columns:
            df_copy["market"] = df_copy["mandi"]

        # Default missing values
        if "min_price" not in df_copy.columns:
            df_copy["min_price"] = df_copy["modal_price"] * 0.95
        if "max_price" not in df_copy.columns:
            df_copy["max_price"] = df_copy["modal_price"] * 1.05
        if "arrivals_quintal" not in df_copy.columns:
            df_copy["arrivals_quintal"] = 1000.0
        if "temperature_c" not in df_copy.columns:
            df_copy["temperature_c"] = 28.0
        if "rainfall_mm" not in df_copy.columns:
            df_copy["rainfall_mm"] = 0.0
        if "fuel_index" not in df_copy.columns:
            df_copy["fuel_index"] = 105.0

        with sqlite3.connect(DB_PATH) as conn:
            # Insert into temporary table and upsert
            df_copy.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
            conn.commit()

        return len(df_copy), f"Successfully imported {len(df_copy)} records."
    except Exception as e:
        return 0, f"Import Error: {str(e)}"

def get_database_summary() -> Dict[str, Any]:
    """Returns total records, crops list, mandis list, date range."""
    init_database()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        total_rows = cursor.fetchone()[0]

        cursor.execute(f"SELECT MIN(date), MAX(date) FROM {TABLE_NAME}")
        min_date, max_date = cursor.fetchone()

        cursor.execute(f"SELECT DISTINCT commodity FROM {TABLE_NAME} ORDER BY commodity")
        crops = [row[0] for row in cursor.fetchall()]

        cursor.execute(f"SELECT DISTINCT state FROM {TABLE_NAME} ORDER BY state")
        states = [row[0] for row in cursor.fetchall()]

        cursor.execute(f"SELECT DISTINCT market FROM {TABLE_NAME} ORDER BY market")
        mandis = [row[0] for row in cursor.fetchall()]

    return {
        "total_rows": total_rows,
        "min_date": min_date,
        "max_date": max_date,
        "crops": crops,
        "states": states,
        "mandis": mandis
    }
