-- E-Commerce Aggregations & Analytical Queries (Basic & Intermediate)

-- Query 1: Total revenue and returns value per product category
SELECT
    p.category,
    COUNT(DISTINCT oi.item_id) AS total_items,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS total_units_sold,
    ROUND(
        SUM(
            CASE WHEN oi.quantity > 0
                 THEN oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)
                 ELSE 0
            END
        ), 2
    ) AS total_revenue,
    ROUND(
        SUM(
            CASE WHEN oi.quantity < 0
                 THEN ABS(oi.quantity) * oi.unit_price
                 ELSE 0
            END
        ), 2
    ) AS total_returns_value
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status NOT IN ('CANCELLED')
GROUP BY p.category
ORDER BY total_revenue DESC;

-- Query 2: Top 10 customers by total purchase value
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_type,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(
        SUM(
            CASE WHEN oi.quantity > 0
                 THEN oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)
                 ELSE 0
            END
        ), 2
    ) AS total_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('CANCELLED')
GROUP BY c.customer_id, c.customer_name, c.customer_type
ORDER BY total_order_value DESC
LIMIT 10;

-- Query 3: Monthly trend of orders and statuses (Last 12 months)
SELECT
    strftime('%Y-%m', order_date) AS order_month,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(CASE WHEN status = 'DELIVERED' THEN 1 ELSE 0 END) AS delivered,
    SUM(CASE WHEN status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled,
    SUM(CASE WHEN status = 'RETURNED' THEN 1 ELSE 0 END) AS returned
FROM orders
WHERE order_date >= DATE('now', '-12 months')
GROUP BY order_month
ORDER BY order_month;

-- Query 4: Customers who placed orders but never had any order successfully DELIVERED
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_type,
    COUNT(DISTINCT o.order_id) AS total_orders,
    GROUP_CONCAT(DISTINCT o.status) AS statuses_seen
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE c.customer_id NOT IN (
    SELECT DISTINCT customer_id
    FROM orders
    WHERE status = 'DELIVERED'
      AND customer_id IS NOT NULL
)
GROUP BY c.customer_id, c.customer_name, c.customer_type
ORDER BY total_orders DESC;

-- Query 5: Products with a higher volume of returns than purchases
WITH product_flow AS (
    SELECT
        oi.product_id,
        SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS total_purchased,
        SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS total_returned
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    GROUP BY oi.product_id
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    pf.total_purchased,
    pf.total_returned,
    ROUND(pf.total_returned * 100.0 / NULLIF(pf.total_purchased, 0), 2) AS return_rate_pct
FROM product_flow pf
JOIN products p ON pf.product_id = p.product_id
WHERE pf.total_returned > pf.total_purchased
ORDER BY return_rate_pct DESC;

-- Query 6: Return rate percentage by product category
WITH category_flow AS (
    SELECT
        p.category,
        SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS total_purchased,
        SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS total_returned,
        COUNT(DISTINCT oi.item_id) AS total_line_items
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category
)
SELECT
    category,
    total_purchased,
    total_returned,
    total_line_items,
    ROUND(total_returned * 100.0 / NULLIF(total_purchased + total_returned, 0), 2) AS return_rate_pct
FROM category_flow
ORDER BY return_rate_pct DESC;
