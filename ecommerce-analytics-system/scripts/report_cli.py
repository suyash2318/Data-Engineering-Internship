"""
Command-line summary reporting tool.
Generates daily, weekly, or monthly reports on revenue, orders, and customer activity.
"""

import argparse
import sqlite3
import sys
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..")
DB_PATH = os.path.join(ROOT_DIR, "ecommerce.db")

REVENUE_FORMULA = (
    "CASE WHEN oi.quantity > 0 "
    "THEN oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0) "
    "ELSE 0 END"
)


def print_table(headers, rows):
    """Prints a clean, aligned ASCII table."""
    all_rows = [headers] + [[str(c) for c in r] for r in rows]
    col_widths = [max(len(row[i]) for row in all_rows) for i in range(len(headers))]
    
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    print(sep)
    
    # Print header
    header_str = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    print(header_str)
    print(sep.replace("-", "="))
    
    # Print data rows
    for row in rows:
        row_str = "| " + " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)) + " |"
        print(row_str)
    print(sep)


def calculate_pct_change(new_val, old_val):
    """Calculate percentage change, returning a formatted string."""
    if not old_val:
        return "N/A"
    change = ((new_val - old_val) / old_val) * 100.0
    prefix = "+" if change >= 0 else ""
    return f"{prefix}{change:.2f}%"


def get_previous_period(start, end):
    """Return start and end datetimes representing the preceding period of equal length."""
    duration = end - start
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - duration
    return prev_start, prev_end


def get_date_grouping(report_type):
    """Get SQLite date grouping expression based on report type."""
    if report_type == "daily":
        return "DATE(order_date)"
    elif report_type == "weekly":
        return "DATE(order_date, 'weekday 0', '-6 days')"
    else:
        return "strftime('%Y-%m', order_date)"


def fetch_summary(conn, start_str, end_str):
    """Fetch aggregated orders, revenue, and customer metrics for a date range."""
    sql = f"""
        SELECT
            COUNT(DISTINCT o.order_id) AS total_orders,
            ROUND(SUM({REVENUE_FORMULA}), 2) AS total_revenue,
            COUNT(DISTINCT o.customer_id) AS unique_customers
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_date >= ?
          AND o.order_date <= ?
          AND o.status NOT IN ('CANCELLED')
    """
    row = conn.execute(sql, (start_str, end_str)).fetchone()
    return {
        "total_orders": row[0] or 0,
        "total_revenue": row[1] or 0.0,
        "unique_customers": row[2] or 0,
    }


def fetch_top_products(conn, start_str, end_str, limit=3):
    """Fetch the top N products by revenue for a date range."""
    sql = f"""
        SELECT
            p.product_name,
            p.category,
            ROUND(SUM({REVENUE_FORMULA}), 2) AS revenue,
            SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS units_sold
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE o.order_date >= ?
          AND o.order_date <= ?
          AND o.status NOT IN ('CANCELLED')
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY revenue DESC
        LIMIT ?
    """
    return conn.execute(sql, (start_str, end_str, limit)).fetchall()


def fetch_breakdown(conn, start_str, end_str, report_type):
    """Fetch periodic breakdown of orders and revenue within a date range."""
    trunc = get_date_grouping(report_type)
    sql = f"""
        SELECT
            {trunc} AS period,
            COUNT(DISTINCT o.order_id) AS orders,
            ROUND(SUM({REVENUE_FORMULA}), 2) AS revenue
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_date >= ?
          AND o.order_date <= ?
          AND o.status NOT IN ('CANCELLED')
        GROUP BY period
        ORDER BY period
    """
    return conn.execute(sql, (start_str, end_str)).fetchall()


def generate_report(report_type, start, end):
    """Generate and display the complete metrics report."""
    if not os.path.exists(DB_PATH):
        sys.exit(f"Database not found: {DB_PATH}. Please run clean_data.py first.")

    start_str = start.strftime("%Y-%m-%d 00:00:00")
    end_str = end.strftime("%Y-%m-%d 23:59:59")
    
    prev_start, prev_end = get_previous_period(start, end)
    prev_start_str = prev_start.strftime("%Y-%m-%d 00:00:00")
    prev_end_str = prev_end.strftime("%Y-%m-%d 23:59:59")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        curr = fetch_summary(conn, start_str, end_str)
        prev = fetch_summary(conn, prev_start_str, prev_end_str)
        top_products = fetch_top_products(conn, start_str, end_str, limit=3)
        breakdown = fetch_breakdown(conn, start_str, end_str, report_type)
    finally:
        conn.close()

    # Render Report
    width = 60
    print("\n" + "=" * width)
    print(f"  E-COMMERCE ANALYTICS REPORT  [{report_type.upper()}]")
    print(f"  Period : {start.date()} to {end.date()}")
    print(f"  vs Prev: {prev_start.date()} to {prev_end.date()}")
    print("=" * width)

    print("\n  SUMMARY")
    print("  " + "-" * (width - 4))
    
    metrics = [
        ("Total Orders", curr["total_orders"], prev["total_orders"]),
        ("Total Revenue ($)", curr["total_revenue"], prev["total_revenue"]),
        ("Unique Customers", curr["unique_customers"], prev["unique_customers"]),
    ]
    
    for label, c_val, p_val in metrics:
        chg = calculate_pct_change(c_val, p_val)
        c_disp = f"{c_val:,.2f}" if isinstance(c_val, float) else f"{c_val:,}"
        p_disp = f"{p_val:,.2f}" if isinstance(p_val, float) else f"{p_val:,}"
        print(f"  {label:<22} {c_disp:>12}    (Prev: {p_disp:>12} | Chg: {chg})")

    print("\n  TOP 3 PRODUCTS (Current Period)")
    if not top_products:
        print("  No product data found.")
    else:
        headers = ["#", "Product Name", "Category", "Revenue ($)", "Units"]
        rows = [
            [str(i + 1), row["product_name"][:30], row["category"], f"{row['revenue']:,.2f}", f"{row['units_sold']:,}"]
            for i, row in enumerate(top_products)
        ]
        print_table(headers, rows)

    if breakdown:
        print(f"\n  PERIODIC BREAKDOWN ({report_type.upper()})")
        b_headers = ["Period", "Orders", "Revenue ($)"]
        b_rows = [[row["period"], f"{row['orders']:,}", f"{row['revenue']:,.2f}"] for row in breakdown]
        
        # Display the last 12 periods to keep CLI readable
        if len(b_rows) > 12:
            print("  (Showing last 12 periods)")
            b_rows = b_rows[-12:]
            
        print_table(b_headers, b_rows)
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="report_cli",
        description="CLI tool for viewing basic e-commerce aggregates."
    )
    parser.add_argument(
        "--type", "-t",
        required=True,
        choices=["daily", "weekly", "monthly"],
        help="Report period type: daily | weekly | monthly"
    )
    parser.add_argument(
        "--start", "-s",
        required=True,
        help="Start date YYYY-MM-DD"
    )
    parser.add_argument(
        "--end", "-e",
        required=True,
        help="End date YYYY-MM-DD"
    )
    
    args = parser.parse_args()

    try:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
    except ValueError:
        sys.exit("Invalid date format. Please use YYYY-MM-DD.")

    if start_date > end_date:
        sys.exit("Start date must be before or equal to end date.")

    generate_report(args.type, start_date, end_date)


if __name__ == "__main__":
    main()
