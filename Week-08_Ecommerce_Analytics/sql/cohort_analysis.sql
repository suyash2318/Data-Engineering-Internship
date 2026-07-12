-- E-Commerce Analytics — Cohort & Retention Analysis

-- 1. Customer Cohort Assignment (First Purchase Month)
WITH first_purchase AS (
    SELECT
        customer_id,
        MIN(order_date) AS first_order_date,
        strftime('%Y-%m', MIN(order_date)) AS cohort_month
    FROM orders
    WHERE status NOT IN ('CANCELLED', 'RETURNED')
    GROUP BY customer_id
)
SELECT
    cohort_month,
    COUNT(DISTINCT customer_id) AS cohort_size
FROM first_purchase
GROUP BY cohort_month
ORDER BY cohort_month;

-- 2. Full Retention Matrix
WITH first_purchase AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', MIN(o.order_date)) AS cohort_month,
        MIN(o.order_date) AS first_order_date
    FROM orders o
    WHERE o.status NOT IN ('CANCELLED', 'RETURNED')
    GROUP BY o.customer_id
),
cohort_orders AS (
    SELECT
        fp.cohort_month,
        fp.customer_id,
        CAST(
            (strftime('%Y', o.order_date) - strftime('%Y', fp.first_order_date)) * 12
            + (strftime('%m', o.order_date) - strftime('%m', fp.first_order_date))
            AS INTEGER
        ) AS period_number
    FROM first_purchase fp
    JOIN orders o ON fp.customer_id = o.customer_id
    WHERE o.status NOT IN ('CANCELLED', 'RETURNED')
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
),
retention_raw AS (
    SELECT
        co.cohort_month,
        co.period_number,
        COUNT(DISTINCT co.customer_id) AS active_customers
    FROM cohort_orders co
    GROUP BY co.cohort_month, co.period_number
)
SELECT
    r.cohort_month,
    cs.cohort_size,
    r.period_number AS months_since_first_purchase,
    r.active_customers,
    ROUND(
        CAST(r.active_customers AS REAL) / cs.cohort_size * 100,
        1
    ) AS retention_rate_pct
FROM retention_raw r
JOIN cohort_sizes cs ON r.cohort_month = cs.cohort_month
WHERE r.period_number <= 12
ORDER BY r.cohort_month, r.period_number;

-- 3. Churned Customers (no orders in last 90 days)
WITH last_activity AS (
    SELECT
        c.customer_id,
        c.customer_name,
        c.customer_type,
        MAX(o.order_date) AS last_order_date,
        COUNT(DISTINCT o.order_id) AS total_orders
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.status NOT IN ('CANCELLED', 'RETURNED')
    GROUP BY c.customer_id, c.customer_name, c.customer_type
)
SELECT
    customer_id,
    customer_name,
    customer_type,
    last_order_date,
    total_orders,
    CAST(JULIANDAY('2025-12-31') - JULIANDAY(last_order_date) AS INTEGER) AS days_since_last_order,
    CASE
        WHEN JULIANDAY('2025-12-31') - JULIANDAY(last_order_date) > 90
            THEN 'Churned'
        ELSE 'Active'
    END AS customer_status
FROM last_activity
ORDER BY days_since_last_order DESC;

-- 4. Churn Summary
WITH last_activity AS (
    SELECT
        c.customer_id,
        MAX(o.order_date) AS last_order_date
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.status NOT IN ('CANCELLED', 'RETURNED')
    GROUP BY c.customer_id
)
SELECT
    CASE
        WHEN JULIANDAY('2025-12-31') - JULIANDAY(last_order_date) > 90
            THEN 'Churned'
        ELSE 'Active'
    END AS customer_status,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_total
FROM last_activity
GROUP BY customer_status;

-- 5. Repeat vs One-Time Buyers
WITH order_counts AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS order_count
    FROM orders
    WHERE status NOT IN ('CANCELLED', 'RETURNED')
    GROUP BY customer_id
)
SELECT
    CASE
        WHEN order_count = 1 THEN 'One-Time Buyer'
        WHEN order_count <= 3 THEN 'Repeat Buyer'
        ELSE                       'Loyal Buyer'
    END AS buyer_type,
    COUNT(*)                      AS customer_count,
    ROUND(AVG(order_count), 2)    AS avg_orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_total
FROM order_counts
GROUP BY buyer_type
ORDER BY customer_count DESC;

-- 6. Cohort Month-0 vs Month-1 Retention Summary
WITH first_purchase AS (
    SELECT
        customer_id,
        strftime('%Y-%m', MIN(order_date)) AS cohort_month
    FROM orders
    WHERE status NOT IN ('CANCELLED', 'RETURNED')
    GROUP BY customer_id
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
),
month1_retained AS (
    SELECT
        fp.cohort_month,
        COUNT(DISTINCT o.customer_id) AS retained
    FROM first_purchase fp
    JOIN orders o ON fp.customer_id = o.customer_id
    WHERE o.status NOT IN ('CANCELLED', 'RETURNED')
      AND strftime('%Y-%m', o.order_date) > fp.cohort_month
    GROUP BY fp.cohort_month
)
SELECT
    cs.cohort_month,
    cs.cohort_size,
    COALESCE(mr.retained, 0) AS retained_after_month0,
    ROUND(
        COALESCE(mr.retained, 0) * 100.0 / cs.cohort_size,
        1
    ) AS retention_rate_pct
FROM cohort_sizes cs
LEFT JOIN month1_retained mr ON cs.cohort_month = mr.cohort_month
ORDER BY cs.cohort_month;
