-- SQLite Database Schema for E-Commerce Analytics System

PRAGMA foreign_keys = ON;

-- Customer records
CREATE TABLE IF NOT EXISTS customers (
    customer_id       INTEGER PRIMARY KEY,
    customer_name     TEXT    NOT NULL,
    email             TEXT,
    registration_date TEXT,
    customer_type     TEXT    CHECK(customer_type IN ('REGULAR', 'PREMIUM', 'VIP'))
);

-- Product catalog
CREATE TABLE IF NOT EXISTS products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT    NOT NULL,
    category     TEXT,
    subcategory  TEXT,
    cost_price   REAL    CHECK(cost_price >= 0)
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date  TEXT    NOT NULL,
    status      TEXT    CHECK(status IN ('PLACED', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'RETURNED')),
    region_code TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- Order line items
CREATE TABLE IF NOT EXISTS order_items (
    item_id          INTEGER PRIMARY KEY,
    order_id         INTEGER NOT NULL,
    product_id       INTEGER NOT NULL,
    quantity         INTEGER,
    unit_price       REAL    CHECK(unit_price >= 0),
    discount_percent REAL    CHECK(discount_percent >= 0 AND discount_percent <= 100),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- Analytics performance indexes
CREATE INDEX IF NOT EXISTS idx_orders_customer   ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date       ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status     ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_region     ON orders(region_code);
CREATE INDEX IF NOT EXISTS idx_items_order       ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_items_product     ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_customers_type    ON customers(customer_type);
