"""
Synthetic data generator for e-commerce analytics.
Generates raw CSV files containing synthetic customer, product, order, and order item records,
injecting realistic data quality issues (e.g. malformed emails, date formats, negative quantities)
to simulate real-world cleaning requirements.
"""

import csv
import os
import random
from datetime import datetime, timedelta
from faker import Faker

# Seed for reproducibility
random.seed(42)
fake = Faker("en_US")
Faker.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31, 23, 59, 59)

CATEGORIES = {
    "Electronics": ["Phones", "Laptops", "Tablets", "Audio", "Cameras"],
    "Clothing":    ["Men", "Women", "Kids", "Sportswear", "Accessories"],
    "Home":        ["Furniture", "Decor", "Kitchen", "Bedding", "Lighting"],
    "Books":       ["Fiction", "Non-Fiction", "Academic", "Comics", "Travel"],
}
REGIONS = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]
STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
STATUS_WEIGHTS = [10, 15, 50, 15, 10]
CUST_TYPES = ["REGULAR", "PREMIUM", "VIP"]
CUST_WEIGHTS = [60, 30, 10]

PRODUCT_ADJECTIVES = ["Premium", "Ultra", "Classic", "Essential", "Modern", "Eco", "Smart", "Pro", "Deluxe", "Pocket"]

def get_random_datetime():
    span = int((END_DATE - START_DATE).total_seconds())
    return START_DATE + timedelta(seconds=random.randint(0, span))

def save_to_csv(filename, rows, fieldnames):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {filename}: {len(rows)} rows")

def gen_customers(n=600):
    rows = []
    for i in range(1, n + 1):
        if random.random() < 0.02:
            username = fake.user_name()
            email = username + "example.com" if random.random() < 0.5 else username + "@"
        else:
            email = fake.email().lower()

        rows.append({
            "customer_id": i,
            "customer_name": fake.name(),
            "email": email,
            "registration_date": get_random_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "customer_type": random.choices(CUST_TYPES, weights=CUST_WEIGHTS)[0],
        })
    return rows

def gen_products(n=500):
    cat_list = list(CATEGORIES.items())
    rows = []
    for i in range(1, n + 1):
        category, subcats = random.choice(cat_list)
        subcat = random.choice(subcats)
        
        adj = random.choice(PRODUCT_ADJECTIVES)
        noun = subcat[:-1] if subcat.endswith("s") else subcat
        name = f"{adj} {noun} {random.randint(10, 999)}"
        
        if random.random() < 0.05:
            name = name.upper() if random.random() < 0.5 else f"  {name}  "

        rows.append({
            "product_id": i,
            "product_name": name,
            "category": category,
            "subcategory": subcat,
            "cost_price": round(random.uniform(5.0, 500.0), 2),
        })
    return rows

def gen_orders(n=2500):
    rows = []
    for i in range(1, n + 1):
        customer_id = "" if random.random() < 0.05 else random.randint(1, 600)
        dt = get_random_datetime()
        date_str = dt.strftime("%d-%m-%Y") if random.random() < 0.05 else dt.strftime("%Y-%m-%d %H:%M:%S")

        rows.append({
            "order_id": i,
            "customer_id": customer_id,
            "order_date": date_str,
            "status": random.choices(STATUSES, weights=STATUS_WEIGHTS)[0],
            "region_code": random.choice(REGIONS),
        })
    return rows

def gen_order_items(order_ids, product_ids, target=6000):
    rows = []
    item_id = 1

    for oid in order_ids:
        n_items = random.randint(1, 4)
        for pid in random.sample(product_ids, min(n_items, len(product_ids))):
            qty = -random.randint(1, 5) if random.random() < 0.03 else random.randint(1, 10)
            rows.append({
                "item_id": item_id,
                "order_id": oid,
                "product_id": pid,
                "quantity": qty,
                "unit_price": round(random.uniform(5.0, 999.99), 2),
                "discount_percent": round(random.uniform(0, 40), 2),
            })
            item_id += 1

    while len(rows) < target:
        qty = -random.randint(1, 3) if random.random() < 0.03 else random.randint(1, 8)
        rows.append({
            "item_id": item_id,
            "order_id": random.choice(order_ids),
            "product_id": random.choice(product_ids),
            "quantity": qty,
            "unit_price": round(random.uniform(5.0, 499.99), 2),
            "discount_percent": round(random.uniform(0, 30), 2),
        })
        item_id += 1

    return rows

def main():
    print("Generating raw dataset...")
    
    save_to_csv("customers.csv", gen_customers(), 
                ["customer_id", "customer_name", "email", "registration_date", "customer_type"])
    
    save_to_csv("products.csv", gen_products(),
                ["product_id", "product_name", "category", "subcategory", "cost_price"])
                
    save_to_csv("orders.csv", gen_orders(),
                ["order_id", "customer_id", "order_date", "status", "region_code"])
                
    order_ids = list(range(1, 2501))
    product_ids = list(range(1, 501))
    save_to_csv("order_items.csv", gen_order_items(order_ids, product_ids),
                ["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent"])

    print("\nData generation complete.")

if __name__ == "__main__":
    main()
