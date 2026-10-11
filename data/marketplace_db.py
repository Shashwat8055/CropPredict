"""
CropPricePredict - Marketplace & User Management Database Module
Handles:
- User accounts (Seller, Buyer, Super Admin)
- Seller Produce Listings with strict ownership checks
- Buyer Orders & Inquiries with strict ownership checks
- Real-time Buyer-Seller Interaction and Negotiation Logging
- Super Admin Oversight (@super.com)
"""
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from config import DB_PATH

def _hash_password(password: str) -> str:
    """Hashes password with SHA-256 and constant salt."""
    salt = "kisan_mandi_portal_2026_secure"
    return hashlib.sha256(f"{password}_{salt}".encode("utf-8")).hexdigest()

def is_superadmin_email(email: str) -> bool:
    """Checks if email belongs to superadmin domain (@super.com)."""
    if not email:
        return False
    return email.strip().lower().endswith("@super.com")

def init_marketplace_tables():
    """Initializes marketplace schema and seeds realistic test data."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT,
            state TEXT,
            mandi TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Seller Listings Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS seller_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_email TEXT NOT NULL,
            seller_name TEXT NOT NULL,
            seller_phone TEXT,
            commodity TEXT NOT NULL,
            variety TEXT,
            state TEXT NOT NULL,
            mandi TEXT NOT NULL,
            quantity_quintals REAL NOT NULL,
            available_quintals REAL NOT NULL,
            price_per_quintal REAL NOT NULL,
            harvest_date TEXT,
            quality_grade TEXT DEFAULT 'Grade A',
            notes TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 3. Buyer Orders Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS buyer_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            buyer_email TEXT NOT NULL,
            buyer_name TEXT NOT NULL,
            buyer_phone TEXT,
            seller_email TEXT NOT NULL,
            seller_name TEXT NOT NULL,
            commodity TEXT NOT NULL,
            state TEXT,
            mandi TEXT,
            quantity_quintals REAL NOT NULL,
            offered_price_per_quintal REAL NOT NULL,
            total_amount REAL NOT NULL,
            delivery_address TEXT,
            buyer_notes TEXT,
            status TEXT DEFAULT 'Pending',
            seller_response_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(listing_id) REFERENCES seller_listings(id)
        );
        """)

        # 4. Market Interactions Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            listing_id INTEGER,
            buyer_email TEXT NOT NULL,
            seller_email TEXT NOT NULL,
            actor_name TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            action_type TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()

        # Seed initial data if users table is empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            _seed_initial_marketplace_data(cursor)
            conn.commit()

def _seed_initial_marketplace_data(cursor: sqlite3.Cursor):
    """Populates realistic seed data for sellers, buyers, listings, orders, and interactions."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Seed Users
    users_data = [
        # Sellers
        ("ramesh.farmer@mandi.in", _hash_password("farmer123"), "Ramesh Kumar", "seller", "+91 98765 43210", "Punjab", "Khanna Mandi", "Village Bhari, Tehsil Khanna, Ludhiana"),
        ("baldev.singh@mandi.in", _hash_password("farmer123"), "Baldev Singh", "seller", "+91 98123 45678", "Haryana", "Karnal Mandi", "Taraori Farm Road, Karnal District"),
        # Buyers
        ("suresh.trader@mandi.in", _hash_password("buyer123"), "Suresh Patel", "buyer", "+91 98220 12345", "Maharashtra", "Pune Market", "Ganj Peth Grain Merchants Association, Pune"),
        ("rajesh.mills@mandi.in", _hash_password("buyer123"), "Rajesh Gupta", "buyer", "+91 94150 98765", "Uttar Pradesh", "Kanpur Mandi", "Gupta Agro Processing Mills, Fazalganj, Kanpur"),
        # Super Admin
        ("admin@super.com", _hash_password("admin123"), "Dr. Priya Sharma", "superadmin", "+91 99999 00001", "Delhi", "National APMC Oversight Cell", "Krishi Bhawan, New Delhi")
    ]
    cursor.executemany("""
    INSERT INTO users (email, password_hash, name, role, phone, state, mandi, address, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(u[0], u[1], u[2], u[3], u[4], u[5], u[6], u[7], now_str) for u in users_data])

    # 2. Seed Listings
    listings_data = [
        ("ramesh.farmer@mandi.in", "Ramesh Kumar", "+91 98765 43210", "Wheat", "Sharbati Gold", "Punjab", "Khanna Mandi", 350.0, 250.0, 2450.0, "2026-03-25", "Grade A (Cleaned, 11% Moisture)", "Farm harvested dried wheat, ready for bulk transport.", "Active"),
        ("ramesh.farmer@mandi.in", "Ramesh Kumar", "+91 98765 43210", "Mustard", "Pusa Bold 42% Oil", "Punjab", "Khanna Mandi", 180.0, 180.0, 5800.0, "2026-03-15", "Grade A+", "High oil content laboratory certified sample available.", "Active"),
        ("baldev.singh@mandi.in", "Baldev Singh", "+91 98123 45678", "Rice (Paddy)", "Basmati 1121 Extra Long", "Haryana", "Karnal Mandi", 500.0, 380.0, 3850.0, "2026-02-10", "Premium Export Grade", "Aged paddy stored in well-ventilated farm godown.", "Active"),
        ("baldev.singh@mandi.in", "Baldev Singh", "+91 98123 45678", "Cotton", "Long Staple Shankar-6", "Haryana", "Karnal Mandi", 220.0, 220.0, 7200.0, "2026-01-28", "Grade A", "First picking clean white bolls, zero trash content.", "Active"),
        ("ramesh.farmer@mandi.in", "Ramesh Kumar", "+91 98765 43210", "Gram (Chickpea)", "Desi Chana Bold", "Punjab", "Khanna Mandi", 120.0, 120.0, 5550.0, "2026-04-02", "Grade A", "Sun dried and graded, ideal for dal milling.", "Active")
    ]
    for item in listings_data:
        cursor.execute("""
        INSERT INTO seller_listings (
            seller_email, seller_name, seller_phone, commodity, variety,
            state, mandi, quantity_quintals, available_quintals, price_per_quintal,
            harvest_date, quality_grade, notes, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11], item[12], item[13], now_str, now_str))

    # 3. Seed Orders
    # Order 1: Suresh bought 100 Qtl Wheat from Ramesh (Accepted)
    cursor.execute("""
    INSERT INTO buyer_orders (
        listing_id, buyer_email, buyer_name, buyer_phone,
        seller_email, seller_name, commodity, state, mandi,
        quantity_quintals, offered_price_per_quintal, total_amount,
        delivery_address, buyer_notes, status, seller_response_notes,
        created_at, updated_at
    ) VALUES (1, 'suresh.trader@mandi.in', 'Suresh Patel', '+91 98220 12345',
              'ramesh.farmer@mandi.in', 'Ramesh Kumar', 'Wheat', 'Punjab', 'Khanna Mandi',
              100.0, 2420.0, 242000.0,
              'Godown #14, Market Yard, Pune, Maharashtra',
              'Need delivery by 15th of this month with lab test certificate.',
              'Accepted', 'Price agreed at Rs. 2,420/Qtl. Loading scheduled for tomorrow morning.',
              ?, ?)
    """, (now_str, now_str))
    order_1_id = cursor.lastrowid

    # Order 2: Rajesh bought 120 Qtl Basmati from Baldev (Dispatched)
    cursor.execute("""
    INSERT INTO buyer_orders (
        listing_id, buyer_email, buyer_name, buyer_phone,
        seller_email, seller_name, commodity, state, mandi,
        quantity_quintals, offered_price_per_quintal, total_amount,
        delivery_address, buyer_notes, status, seller_response_notes,
        created_at, updated_at
    ) VALUES (3, 'rajesh.mills@mandi.in', 'Rajesh Gupta', '+91 94150 98765',
              'baldev.singh@mandi.in', 'Baldev Singh', 'Rice (Paddy)', 'Haryana', 'Karnal Mandi',
              120.0, 3850.0, 462000.0,
              'Gupta Agro Mills Unit 2, Fazalganj Industrial Area, Kanpur',
              'Urgent requirement for processing batch. Dispatch via truck transport.',
              'Dispatched', 'Loaded in Truck HR-05-AB-4412. Driver Contact: +91 97290 11223.',
              ?, ?)
    """, (now_str, now_str))
    order_2_id = cursor.lastrowid

    # Order 3: Suresh placed pending order on Mustard with Ramesh
    cursor.execute("""
    INSERT INTO buyer_orders (
        listing_id, buyer_email, buyer_name, buyer_phone,
        seller_email, seller_name, commodity, state, mandi,
        quantity_quintals, offered_price_per_quintal, total_amount,
        delivery_address, buyer_notes, status, seller_response_notes,
        created_at, updated_at
    ) VALUES (2, 'suresh.trader@mandi.in', 'Suresh Patel', '+91 98220 12345',
              'ramesh.farmer@mandi.in', 'Ramesh Kumar', 'Mustard', 'Punjab', 'Khanna Mandi',
              50.0, 5750.0, 287500.0,
              'Wholesale Yard, Market Yard, Pune',
              'Requesting Rs. 5,750 rate for prompt payment upon unloading.',
              'Pending', '',
              ?, ?)
    """, (now_str, now_str))
    order_3_id = cursor.lastrowid

    # 4. Seed Interactions Log
    interactions = [
        (order_1_id, 1, "suresh.trader@mandi.in", "ramesh.farmer@mandi.in", "Suresh Patel", "buyer", "ORDER_PLACED",
         "Placed order for 100.0 Quintals of Wheat at Rs. 2,420/Qtl (Total: Rs. 2,42,000).",
         "Delivery to Pune Market Yard."),
        (order_1_id, 1, "suresh.trader@mandi.in", "ramesh.farmer@mandi.in", "Ramesh Kumar", "seller", "ORDER_ACCEPTED",
         "Accepted order for 100.0 Quintals of Wheat.",
         "Price confirmed at Rs. 2,420/Qtl. Loading scheduled for tomorrow."),
        (order_2_id, 3, "rajesh.mills@mandi.in", "baldev.singh@mandi.in", "Rajesh Gupta", "buyer", "ORDER_PLACED",
         "Placed order for 120.0 Quintals of Rice (Paddy) at Rs. 3,850/Qtl (Total: Rs. 4,62,000).",
         "Delivery to Gupta Agro Mills, Kanpur."),
        (order_2_id, 3, "rajesh.mills@mandi.in", "baldev.singh@mandi.in", "Baldev Singh", "seller", "ORDER_ACCEPTED",
         "Accepted order for 120.0 Quintals of Rice (Paddy).",
         "Quality certificates verified."),
        (order_2_id, 3, "rajesh.mills@mandi.in", "baldev.singh@mandi.in", "Baldev Singh", "seller", "ORDER_DISPATCHED",
         "Produce dispatched via Truck HR-05-AB-4412.",
         "Bilty Number: BL-99214. ETA: 48 hours."),
        (order_3_id, 2, "suresh.trader@mandi.in", "ramesh.farmer@mandi.in", "Suresh Patel", "buyer", "ORDER_PLACED",
         "Placed inquiry and order for 50.0 Quintals of Mustard at Rs. 5,750/Qtl (Total: Rs. 2,87,500).",
         "Awaiting seller confirmation.")
    ]
    cursor.executemany("""
    INSERT INTO market_interactions (
        order_id, listing_id, buyer_email, seller_email, actor_name,
        actor_role, action_type, message, details, timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], now_str) for i in interactions])


# ==========================================
# AUTHENTICATION & USER MANAGEMENT
# ==========================================

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticates a user by email and password. Grants superadmin if @super.com."""
    init_marketplace_tables()
    email_clean = email.strip().lower()
    pw_hash = _hash_password(password)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
        user_row = cursor.fetchone()

        if user_row:
            if user_row["password_hash"] == pw_hash:
                user_dict = dict(user_row)
                # Ensure superadmin role for any @super.com email
                if is_superadmin_email(email_clean) and user_dict["role"] != "superadmin":
                    cursor.execute("UPDATE users SET role = 'superadmin' WHERE id = ?", (user_dict["id"],))
                    conn.commit()
                    user_dict["role"] = "superadmin"
                return user_dict
            return None
        else:
            # If user does not exist but has @super.com email, auto-create superadmin account!
            if is_superadmin_email(email_clean):
                name = email_clean.split("@")[0].replace(".", " ").title()
                cursor.execute("""
                INSERT INTO users (email, password_hash, name, role, phone, state, mandi, address)
                VALUES (?, ?, ?, 'superadmin', '+91 99999 00000', 'Central', 'APMC Oversight', 'National Portal')
                """, (email_clean, pw_hash, f"SuperAdmin ({name})"))
                conn.commit()
                cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
                return dict(cursor.fetchone())

    return None

def register_user(
    email: str,
    password: str,
    name: str,
    role: str,
    phone: str = "",
    state: str = "",
    mandi: str = "",
    address: str = ""
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Registers a new user (seller or buyer, or superadmin if @super.com)."""
    init_marketplace_tables()
    email_clean = email.strip().lower()

    if not email_clean or "@" not in email_clean:
        return False, "Please provide a valid email address.", None
    if len(password) < 4:
        return False, "Password must be at least 4 characters long.", None
    if not name.strip():
        return False, "Please enter your full name.", None

    # Role resolution
    if is_superadmin_email(email_clean):
        final_role = "superadmin"
    else:
        final_role = role.lower()
        if final_role not in ["seller", "buyer"]:
            return False, "Please select whether you are a Seller or Buyer.", None

    pw_hash = _hash_password(password)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO users (email, password_hash, name, role, phone, state, mandi, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (email_clean, pw_hash, name.strip(), final_role, phone.strip(), state.strip(), mandi.strip(), address.strip()))
            conn.commit()

            cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
            conn.row_factory = sqlite3.Row
            row = conn.cursor().execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,)).fetchone()
            return True, f"Registration successful as {final_role.upper()}!", dict(row)
    except sqlite3.IntegrityError:
        return False, f"An account with email '{email_clean}' already exists. Please log in.", None
    except Exception as e:
        return False, f"Registration error: {str(e)}", None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves user profile dictionary by email."""
    init_marketplace_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email.strip().lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None


# ==========================================
# SELLER ACCESS: STRICT OWNERSHIP ENFORCED
# ==========================================

def get_seller_listings(seller_email: str) -> List[Dict[str, Any]]:
    """Returns only listings owned by the given seller (strictly isolated)."""
    init_marketplace_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM seller_listings
        WHERE LOWER(seller_email) = ?
        ORDER BY created_at DESC
        """, (seller_email.strip().lower(),))
        return [dict(r) for r in cursor.fetchall()]

def add_seller_listing(
    seller_email: str,
    seller_name: str,
    seller_phone: str,
    commodity: str,
    variety: str,
    state: str,
    mandi: str,
    quantity_quintals: float,
    price_per_quintal: float,
    harvest_date: str,
    quality_grade: str,
    notes: str
) -> Tuple[bool, str]:
    """Adds a new produce listing owned by the seller."""
    init_marketplace_tables()
    if quantity_quintals <= 0:
        return False, "Quantity must be greater than zero."
    if price_per_quintal <= 0:
        return False, "Asking price must be greater than zero."

    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO seller_listings (
                seller_email, seller_name, seller_phone, commodity, variety,
                state, mandi, quantity_quintals, available_quintals, price_per_quintal,
                harvest_date, quality_grade, notes, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?)
            """, (
                seller_email.strip().lower(), seller_name, seller_phone,
                commodity, variety, state, mandi,
                float(quantity_quintals), float(quantity_quintals), float(price_per_quintal),
                str(harvest_date), quality_grade, notes, now_str, now_str
            ))
            conn.commit()
        return True, "Produce listing created successfully!"
    except Exception as e:
        return False, f"Failed to create listing: {str(e)}"

def update_seller_listing(
    listing_id: int,
    seller_email: str,
    quantity_quintals: float,
    price_per_quintal: float,
    quality_grade: str,
    status: str,
    notes: str
) -> Tuple[bool, str]:
    """Updates listing with strict ownership verification: sellers cannot touch other sellers' data."""
    init_marketplace_tables()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seller_email, available_quintals, quantity_quintals FROM seller_listings WHERE id = ?", (listing_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Listing not found."
            if row[0].lower() != seller_email.strip().lower():
                return False, "Permission Denied: You cannot modify another seller's listing."

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
            UPDATE seller_listings
            SET quantity_quintals = ?,
                available_quintals = ?,
                price_per_quintal = ?,
                quality_grade = ?,
                status = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ? AND LOWER(seller_email) = ?
            """, (
                float(quantity_quintals), float(quantity_quintals), float(price_per_quintal),
                quality_grade, status, notes, now_str, listing_id, seller_email.strip().lower()
            ))
            conn.commit()
        return True, "Listing updated successfully!"
    except Exception as e:
        return False, f"Update failed: {str(e)}"

def delete_seller_listing(listing_id: int, seller_email: str) -> Tuple[bool, str]:
    """Deletes a listing with strict ownership check."""
    init_marketplace_tables()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seller_email FROM seller_listings WHERE id = ?", (listing_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Listing not found."
            if row[0].lower() != seller_email.strip().lower():
                return False, "Permission Denied: You cannot delete another seller's listing."

            cursor.execute("DELETE FROM seller_listings WHERE id = ? AND LOWER(seller_email) = ?", (listing_id, seller_email.strip().lower()))
            conn.commit()
        return True, "Listing deleted successfully."
    except Exception as e:
        return False, f"Deletion failed: {str(e)}"

def get_seller_orders(seller_email: str) -> List[Dict[str, Any]]:
    """Returns incoming orders placed by buyers for this seller only."""
    init_marketplace_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM buyer_orders
        WHERE LOWER(seller_email) = ?
        ORDER BY created_at DESC
        """, (seller_email.strip().lower(),))
        return [dict(r) for r in cursor.fetchall()]

def update_order_status_by_seller(
    order_id: int,
    seller_email: str,
    seller_name: str,
    new_status: str,
    seller_notes: str = ""
) -> Tuple[bool, str]:
    """Seller updates order status (Accepted, Declined, Dispatched, Completed) and logs interaction."""
    init_marketplace_tables()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM buyer_orders WHERE id = ?", (order_id,))
            order = cursor.fetchone()
            if not order:
                return False, "Order not found."
            if order["seller_email"].lower() != seller_email.strip().lower():
                return False, "Permission Denied: This order belongs to a different seller."

            cursor.execute("""
            UPDATE buyer_orders
            SET status = ?, seller_response_notes = ?, updated_at = ?
            WHERE id = ? AND LOWER(seller_email) = ?
            """, (new_status, seller_notes, now_str, order_id, seller_email.strip().lower()))

            # Deduct listing stock if accepted
            if new_status in ["Accepted", "Completed"]:
                cursor.execute("""
                UPDATE seller_listings
                SET available_quintals = MAX(0, available_quintals - ?),
                    status = CASE WHEN available_quintals - ? <= 0 THEN 'Sold Out' ELSE status END
                WHERE id = ?
                """, (order["quantity_quintals"], order["quantity_quintals"], order["listing_id"]))

            # Log interaction
            action_code = f"ORDER_{new_status.upper()}"
            msg = f"{seller_name} (Seller) updated Order #{order_id} status to '{new_status}'."
            if seller_notes:
                msg += f" Note: {seller_notes}"

            cursor.execute("""
            INSERT INTO market_interactions (
                order_id, listing_id, buyer_email, seller_email, actor_name,
                actor_role, action_type, message, details, timestamp
            ) VALUES (?, ?, ?, ?, ?, 'seller', ?, ?, ?, ?)
            """, (order_id, order["listing_id"], order["buyer_email"], seller_email, seller_name, action_code, msg, seller_notes, now_str))

            conn.commit()
        return True, f"Order #{order_id} updated to {new_status}!"
    except Exception as e:
        return False, f"Failed to update order: {str(e)}"


# ==========================================
# BUYER ACCESS: STRICT ISOLATION ENFORCED
# ==========================================

def get_marketplace_listings(
    crop: Optional[str] = None,
    state: Optional[str] = None,
    mandi: Optional[str] = None,
    max_price: Optional[float] = None
) -> List[Dict[str, Any]]:
    """Buyers browse active produce listings from all sellers."""
    init_marketplace_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM seller_listings WHERE status = 'Active' AND available_quintals > 0"
        params = []

        if crop and crop != "All Crops":
            query += " AND commodity = ?"
            params.append(crop)
        if state and state != "All States":
            query += " AND state = ?"
            params.append(state)
        if mandi and mandi != "All Mandis":
            query += " AND mandi = ?"
            params.append(mandi)
        if max_price and max_price > 0:
            query += " AND price_per_quintal <= ?"
            params.append(float(max_price))

        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]

def get_buyer_orders(buyer_email: str) -> List[Dict[str, Any]]:
    """Returns only orders placed by this specific buyer (strictly isolated from other buyers)."""
    init_marketplace_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM buyer_orders
        WHERE LOWER(buyer_email) = ?
        ORDER BY created_at DESC
        """, (buyer_email.strip().lower(),))
        return [dict(r) for r in cursor.fetchall()]

def place_buyer_order(
    listing_id: int,
    buyer_email: str,
    buyer_name: str,
    buyer_phone: str,
    quantity_quintals: float,
    offered_price_per_quintal: float,
    delivery_address: str,
    buyer_notes: str
) -> Tuple[bool, str, Optional[int]]:
    """Buyer places purchase order/bid on a seller's listing."""
    init_marketplace_tables()
    if quantity_quintals <= 0:
        return False, "Order quantity must be greater than zero.", None
    if offered_price_per_quintal <= 0:
        return False, "Offered price must be greater than zero.", None

    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM seller_listings WHERE id = ?", (listing_id,))
            listing = cursor.fetchone()
            if not listing:
                return False, "Selected listing does not exist.", None
            if listing["status"] != "Active":
                return False, "This listing is no longer active.", None
            if quantity_quintals > listing["available_quintals"]:
                return False, f"Requested quantity ({quantity_quintals} Qtl) exceeds available stock ({listing['available_quintals']} Qtl).", None

            total_amt = float(quantity_quintals * offered_price_per_quintal)

            cursor.execute("""
            INSERT INTO buyer_orders (
                listing_id, buyer_email, buyer_name, buyer_phone,
                seller_email, seller_name, commodity, state, mandi,
                quantity_quintals, offered_price_per_quintal, total_amount,
                delivery_address, buyer_notes, status, seller_response_notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', '', ?, ?)
            """, (
                listing_id, buyer_email.strip().lower(), buyer_name, buyer_phone,
                listing["seller_email"], listing["seller_name"], listing["commodity"],
                listing["state"], listing["mandi"],
                float(quantity_quintals), float(offered_price_per_quintal), total_amt,
                delivery_address, buyer_notes, now_str, now_str
            ))
            order_id = cursor.lastrowid

            # Log interaction
            msg = f"{buyer_name} (Buyer) placed Order #{order_id} for {quantity_quintals} Qtl of {listing['commodity']} at Rs. {offered_price_per_quintal:,.2f}/Qtl (Total: Rs. {total_amt:,.2f})."
            cursor.execute("""
            INSERT INTO market_interactions (
                order_id, listing_id, buyer_email, seller_email, actor_name,
                actor_role, action_type, message, details, timestamp
            ) VALUES (?, ?, ?, ?, ?, 'buyer', 'ORDER_PLACED', ?, ?, ?)
            """, (order_id, listing_id, buyer_email.strip().lower(), listing["seller_email"], buyer_name, msg, buyer_notes, now_str))

            conn.commit()
            return True, f"Order #{order_id} placed successfully with farmer {listing['seller_name']}!", order_id
    except Exception as e:
        return False, f"Failed to place order: {str(e)}", None

def cancel_order_by_buyer(order_id: int, buyer_email: str, reason: str = "") -> Tuple[bool, str]:
    """Buyer cancels their own pending order. Cannot cancel accepted/dispatched orders."""
    init_marketplace_tables()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM buyer_orders WHERE id = ?", (order_id,))
            order = cursor.fetchone()
            if not order:
                return False, "Order not found."
            if order["buyer_email"].lower() != buyer_email.strip().lower():
                return False, "Permission Denied: You cannot cancel another buyer's order."
            if order["status"] != "Pending":
                return False, f"Cannot cancel order in '{order['status']}' state. Only 'Pending' orders can be cancelled."

            cursor.execute("""
            UPDATE buyer_orders
            SET status = 'Cancelled', buyer_notes = buyer_notes || ' [Cancelled by Buyer: ' || ? || ']', updated_at = ?
            WHERE id = ? AND LOWER(buyer_email) = ?
            """, (reason, now_str, order_id, buyer_email.strip().lower()))

            # Log interaction
            msg = f"{order['buyer_name']} (Buyer) cancelled Order #{order_id}. Reason: {reason or 'No reason provided'}."
            cursor.execute("""
            INSERT INTO market_interactions (
                order_id, listing_id, buyer_email, seller_email, actor_name,
                actor_role, action_type, message, details, timestamp
            ) VALUES (?, ?, ?, ?, ?, 'buyer', 'ORDER_CANCELLED', ?, ?, ?)
            """, (order_id, order["listing_id"], buyer_email.strip().lower(), order["seller_email"], order["buyer_name"], msg, reason, now_str))

            conn.commit()
        return True, f"Order #{order_id} cancelled successfully."
    except Exception as e:
        return False, f"Failed to cancel order: {str(e)}"


# ==========================================
# SUPER ADMIN OVERSIGHT (@super.com)
# ==========================================

def get_platform_overview_metrics() -> Dict[str, Any]:
    """Super Admin high-level metrics across all buyers and sellers."""
    init_marketplace_tables()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'seller'")
        total_sellers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'buyer'")
        total_buyers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(quantity_quintals), 0), COALESCE(SUM(available_quintals), 0) FROM seller_listings")
        listings_row = cursor.fetchone()
        total_listings = listings_row[0]
        total_listed_qtl = listings_row[1]
        active_stock_qtl = listings_row[2]

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(quantity_quintals), 0), COALESCE(SUM(total_amount), 0) FROM buyer_orders")
        orders_row = cursor.fetchone()
        total_orders = orders_row[0]
        total_ordered_qtl = orders_row[1]
        gross_trade_value = orders_row[2]

        cursor.execute("SELECT COUNT(*) FROM buyer_orders WHERE status = 'Completed'")
        completed_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM buyer_orders WHERE status = 'Pending'")
        pending_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM market_interactions")
        total_interactions = cursor.fetchone()[0]

    return {
        "total_sellers": total_sellers,
        "total_buyers": total_buyers,
        "total_listings": total_listings,
        "total_listed_qtl": total_listed_qtl,
        "active_stock_qtl": active_stock_qtl,
        "total_orders": total_orders,
        "total_ordered_qtl": total_ordered_qtl,
        "gross_trade_value": gross_trade_value,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
        "total_interactions": total_interactions
    }

def get_all_users() -> List[Dict[str, Any]]:
    """Super Admin: View directory of all registered users."""
    init_marketplace_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, role, phone, state, mandi, address, created_at FROM users ORDER BY created_at DESC")
        return [dict(r) for r in cursor.fetchall()]

def get_all_listings() -> List[Dict[str, Any]]:
    """Super Admin: View all listings across all sellers."""
    init_marketplace_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM seller_listings ORDER BY created_at DESC")
        return [dict(r) for r in cursor.fetchall()]

def get_all_orders() -> List[Dict[str, Any]]:
    """Super Admin: View all orders across all buyers and sellers."""
    init_marketplace_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM buyer_orders ORDER BY created_at DESC")
        return [dict(r) for r in cursor.fetchall()]

def get_all_interactions(
    buyer_email: Optional[str] = None,
    seller_email: Optional[str] = None,
    order_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Super Admin: Inspect chronological timeline of how buyers and sellers are interacting."""
    init_marketplace_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM market_interactions WHERE 1=1"
        params = []

        if buyer_email:
            query += " AND LOWER(buyer_email) = ?"
            params.append(buyer_email.strip().lower())
        if seller_email:
            query += " AND LOWER(seller_email) = ?"
            params.append(seller_email.strip().lower())
        if order_id:
            query += " AND order_id = ?"
            params.append(int(order_id))

        query += " ORDER BY timestamp DESC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]

def admin_delete_listing(listing_id: int) -> Tuple[bool, str]:
    """Super Admin: Remove inappropriate listing."""
    init_marketplace_tables()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM seller_listings WHERE id = ?", (listing_id,))
            conn.commit()
        return True, f"Listing #{listing_id} deleted by Super Admin."
    except Exception as e:
        return False, str(e)
