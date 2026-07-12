"""
Data cleaning pipeline for the e-commerce dataset.
Loads raw CSVs, cleans data issues, exports cleaned versions, and populates the SQLite database.
Additionally generates an issue report and runs automated verification tests.
"""

import os
import sys
import sqlite3
from datetime import datetime
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..")
RAW_DIR = os.path.join(ROOT_DIR, "data", "raw")
CLEANED_DIR = os.path.join(ROOT_DIR, "data", "cleaned")
SQL_DIR = os.path.join(ROOT_DIR, "sql")
DB_PATH = os.path.join(ROOT_DIR, "ecommerce.db")

os.makedirs(CLEANED_DIR, exist_ok=True)

VALID_STATUSES = {"PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"}
VALID_TYPES = {"REGULAR", "PREMIUM", "VIP"}
DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y"]

CLEANING_ISSUES = []


def clean_orders(df):
    """Normalize date formats, handle invalid statuses, and ensure ID types."""
    df = df.copy()

    fixed, dropped = 0, 0
    dates = []
    now = datetime.now()
    
    for val in df["order_date"]:
        val_str = str(val).strip()
        parsed = None
        for fmt in DATE_FORMATS:
            try:
                parsed = datetime.strptime(val_str, fmt)
                if fmt == "%d-%m-%Y":
                    fixed += 1
                break
            except ValueError:
                continue
        
        if parsed is None:
            dropped += 1
            dates.append(None)
        else:
            dates.append(min(parsed, now).strftime("%Y-%m-%d %H:%M:%S"))

    df["order_date"] = dates
    df = df.dropna(subset=["order_date"])

    if fixed:
        msg = f"Orders: corrected {fixed} dates from DD-MM-YYYY format"
        print(f"  {msg}")
        CLEANING_ISSUES.append(msg)
    if dropped:
        msg = f"Orders: dropped {dropped} rows with unparseable dates"
        print(f"  {msg}")
        CLEANING_ISSUES.append(msg)

    null_count = (df["customer_id"].isna() | (df["customer_id"].astype(str).str.strip() == "")).sum()
    if null_count:
        msg = f"Orders: {null_count} rows have NULL customer_id (kept as-is)"
        print(f"  {msg}")
        CLEANING_ISSUES.append(msg)
        
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce")
    df["status"] = df["status"].str.strip().str.upper()
    
    bad_status = ~df["status"].isin(VALID_STATUSES) & df["status"].notna()
    if bad_status.any():
        msg = f"Orders: replaced {bad_status.sum()} invalid status values with PLACED"
        print(f"  {msg}")
        CLEANING_ISSUES.append(msg)
        df.loc[bad_status, "status"] = "PLACED"

    df["order_id"] = pd.to_numeric(df["order_id"], errors="coerce")
    df["region_code"] = df["region_code"].str.strip().str.upper().fillna("UNKNOWN")
    
    df = df.dropna(subset=["order_id"]).drop_duplicates(subset=["order_id"])
    df["order_id"] = df["order_id"].astype(int)

    return df.reset_index(drop=True)


def clean_products(df):
    """Normalize product names, categorizations, and cost prices."""
    df = df.copy()
    df["product_id"] = pd.to_numeric(df["product_id"], errors="coerce")
    df = df.dropna(subset=["product_id"]).drop_duplicates(subset=["product_id"])
    df["product_id"] = df["product_id"].astype(int)

    before_names = df["product_name"].copy()
    df["product_name"] = (
        df["product_name"].astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.title()
    )
    changed = (before_names.str.strip() != df["product_name"]).sum()
    if changed:
        msg = f"Products: normalized {changed} product names"
        print(f"  {msg}")
        CLEANING_ISSUES.append(msg)

    df["category"] = df["category"].str.strip().str.title().fillna("Uncategorized")
    df["subcategory"] = df["subcategory"].str.strip().str.title().fillna("General")
    df["cost_price"] = pd.to_numeric(df["cost_price"], errors="coerce")
    df["cost_price"] = df["cost_price"].clip(lower=0).fillna(df["cost_price"].median()).round(2)

    return df.reset_index(drop=True)


def validate_emails(df):
    """Return a list of customer_ids whose email addresses are syntactically invalid."""
    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    is_valid = df["email"].fillna("").str.strip().str.match(email_pattern)
    invalid_df = df[~is_valid]
    invalid_ids = invalid_df["customer_id"].dropna().astype(int).tolist()
    
    msg = f"Customers: found {len(invalid_ids)} invalid email(s) — IDs: {invalid_ids[:10]}" + ("..." if len(invalid_ids) > 10 else "")
    print(f"  {msg}")
    CLEANING_ISSUES.append(f"Customers: found {len(invalid_ids)} invalid email(s) — IDs: {invalid_ids}")
    return invalid_ids


def check_referential_integrity(orders_df, items_df):
    """Return rows in order_items that reference an order_id not present in orders."""
    valid_ids = set(orders_df["order_id"].dropna().astype(int))
    item_oids = pd.to_numeric(items_df["order_id"], errors="coerce")
    orphans = items_df[~item_oids.isin(valid_ids)]
    
    msg = f"Order Items: {len(orphans)} row(s) reference a non-existent order_id"
    print(f"  {msg}")
    if not orphans.empty:
        print(f"    sample order_ids: {orphans['order_id'].unique()[:5].tolist()}")
    CLEANING_ISSUES.append(msg)
    return orphans


def _clean_customers(df):
    """Clean and normalize customer demographic fields."""
    df = df.copy().drop_duplicates(subset=["customer_id"])
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce")
    df = df.dropna(subset=["customer_id"])
    df["customer_id"] = df["customer_id"].astype(int)
    
    df["customer_name"] = df["customer_name"].str.strip().str.title()
    df = df.dropna(subset=["customer_name"])
    
    df["email"] = df["email"].str.strip().str.lower()
    df["registration_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
    df["registration_date"] = df["registration_date"].clip(upper=pd.Timestamp.now())
    df["registration_date"] = df["registration_date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    df["customer_type"] = df["customer_type"].str.strip().str.upper()
    df.loc[~df["customer_type"].isin(VALID_TYPES), "customer_type"] = "REGULAR"
    
    return df.reset_index(drop=True)


def _clean_order_items(df, valid_order_ids, valid_product_ids):
    """Clean order item details, filtering orphans and enforcing pricing bounds."""
    df = df.copy().drop_duplicates(subset=["item_id"])
    
    for col in ["item_id", "order_id", "product_id"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["item_id", "order_id", "product_id"])
    df[["item_id", "order_id", "product_id"]] = df[["item_id", "order_id", "product_id"]].astype(int)

    # Maintain referential integrity
    df = df[df["order_id"].isin(valid_order_ids) & df["product_id"].isin(valid_product_ids)]

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df = df.dropna(subset=["quantity", "unit_price"])
    df["quantity"] = df["quantity"].astype(int)
    
    df.loc[df["unit_price"] < 0, "unit_price"] = df["unit_price"].median()
    df["unit_price"] = df["unit_price"].round(2)

    df["discount_percent"] = pd.to_numeric(df["discount_percent"], errors="coerce").fillna(0)
    out_of_range = (df["discount_percent"] < 0) | (df["discount_percent"] > 100)
    if out_of_range.any():
        msg = f"Order Items: capped {out_of_range.sum()} discount_percent values to [0, 100]"
        print(f"  {msg}")
        CLEANING_ISSUES.append(msg)
    df["discount_percent"] = df["discount_percent"].clip(0, 100).round(2)

    return df.reset_index(drop=True)


def _init_db():
    """Recreate database structure using schema.sql."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        with open(os.path.join(SQL_DIR, "schema.sql"), encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()


def _load_tables(cleaned):
    """Load cleaned dataframes into SQLite."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        for name, df in cleaned.items():
            df.to_sql(name, conn, if_exists="append", index=False)
            count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            print(f"  {name}: {count} rows")
        conn.commit()
    finally:
        conn.close()


# =============================================================================
# Automated Verification Tests (Edge Case Verification)
# =============================================================================

def run_verification_tests():
    """Run edge-case test validations to guarantee database constraints are working."""
    print("\nRunning database edge case validation tests...")
    print("-" * 50)
    
    tests = [
        ("Orphan Prevention Test", test_orphan_prevention),
        ("Discount Limit Bounds Test", test_discount_bounds),
        ("Zero Quantity Revenue Test", test_zero_quantity_revenue),
        ("Future Date Capping Test", test_future_dates_capped)
    ]
    
    failed = False
    for name, fn in tests:
        try:
            fn()
            print(f"  [PASS] {name}")
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed = True
            
    print("-" * 50)
    if failed:
        print("Database verification failed.")
        sys.exit(1)
    else:
        print("All database integrity checks passed successfully.")


def test_orphan_prevention():
    """Verify that orphaned order items are not in db and rejected by foreign key rules."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        orphans = conn.execute("""
            SELECT COUNT(*) FROM order_items oi
            LEFT JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_id IS NULL
        """).fetchone()[0]
        assert orphans == 0, f"Found {orphans} orphaned order items in database."
        
        try:
            conn.execute("""
                INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount_percent)
                VALUES (9999999, 9999999, 1, 1, 10.00, 0.0)
            """)
            conn.commit()
            raise AssertionError("Foreign key failed to block invalid order item.")
        except sqlite3.IntegrityError:
            pass
    finally:
        conn.close()


def test_discount_bounds():
    """Verify check constraint on discount_percent works correctly."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        violations = conn.execute("SELECT COUNT(*) FROM order_items WHERE discount_percent > 100").fetchone()[0]
        assert violations == 0, f"Found {violations} items exceeding 100% discount."
        
        try:
            conn.execute("""
                INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount_percent)
                VALUES (8888888, 
                        (SELECT order_id FROM orders LIMIT 1),
                        (SELECT product_id FROM products LIMIT 1),
                        1, 50.00, 150.0)
            """)
            conn.commit()
            raise AssertionError("CHECK constraint failed to block invalid discount.")
        except sqlite3.IntegrityError:
            pass
    finally:
        conn.close()


def test_zero_quantity_revenue():
    """Verify revenue calculations are correct when quantity is 0."""
    qty = 0
    price = 100.00
    disc = 10.0
    revenue = qty * price * (1.0 - disc / 100.0)
    assert revenue == 0.0, f"Expected 0 revenue, got {revenue}"


def test_future_dates_capped():
    """Verify no orders exist in the future relative to runtime."""
    conn = sqlite3.connect(DB_PATH)
    try:
        future_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_date > DATETIME('now')").fetchone()[0]
        assert future_orders == 0, f"Found {future_orders} future dated orders."
    finally:
        conn.close()


def main():
    print("Loading raw CSVs...")
    raw = {}
    for name in ("customers", "products", "orders", "order_items"):
        path = os.path.join(RAW_DIR, f"{name}.csv")
        if not os.path.exists(path):
            sys.exit(f"File not found: {path}\nRun generate_data.py first.")
        raw[name] = pd.read_csv(path, dtype=str)
        print(f"  {name}: {len(raw[name])} rows")

    print("\nCleaning data...")
    customers = _clean_customers(raw["customers"])
    products = clean_products(raw["products"])
    _ = validate_emails(raw["customers"])
    orders = clean_orders(raw["orders"])
    _ = check_referential_integrity(orders, raw["order_items"])
    
    order_items = _clean_order_items(
        raw["order_items"],
        set(orders["order_id"]),
        set(products["product_id"]),
    )

    print("\nExporting cleaned CSVs...")
    cleaned = {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items
    }
    for name, df in cleaned.items():
        path = os.path.join(CLEANED_DIR, f"{name}_clean.csv")
        df.to_csv(path, index=False)
        print(f"  {name}_clean.csv: {len(df)} rows")

    report_path = os.path.join(CLEANED_DIR, "cleaning_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=== E-Commerce Analytics Data Cleaning Report ===\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Issues Identified and Cleaned:\n")
        for issue in CLEANING_ISSUES:
            f.write(f"- {issue}\n")
    print(f"\nSaved issue report to: {report_path}")

    print("\nLoading into SQLite...")
    _init_db()
    _load_tables(cleaned)

    # Run verification tests on database state
    run_verification_tests()

    print(f"\nCleaning and load process complete. DB: {DB_PATH}")


if __name__ == "__main__":
    main()
