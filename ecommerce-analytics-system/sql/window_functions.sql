-- Advanced SQL: Window Functions and Complex CTEs

-- Query 7: Running total revenue per region ordered by date
WITH daily_region_revenue AS (
    SELECT
        o.region_code,
        DATE(o.order_date) AS order_date,
        ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS daily_revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.quantity > 0
      AND o.status NOT IN ('CANCELLED')
    GROUP BY o.region_code, DATE(o.order_date)
)
SELECT
    region_code,
    order_date,
    daily_revenue,
    ROUND(
        SUM(daily_revenue) OVER (
            PARTITION BY region_code
            ORDER BY order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2
    ) AS running_total
FROM daily_region_revenue
ORDER BY region_code, order_date;

-- Query 8: Product rankings by revenue within each category (DENSE_RANK)
WITH product_revenue AS (
    SELECT
        p.category,
        p.product_name,
        ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS total_revenue
    FROM products p
    JOIN order_items oi ON p.product_id = oi.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE oi.quantity > 0
      AND o.status NOT IN ('CANCELLED')
    GROUP BY p.category, p.product_name
)
SELECT
    category,
    product_name,
    total_revenue,
    DENSE_RANK() OVER (
        PARTITION BY category
        ORDER BY total_revenue DESC
    ) AS rank_in_category
FROM product_revenue
ORDER BY category, rank_in_category;

-- Query 9: Days elapsed between consecutive customer orders (LAG)
WITH order_gaps AS (
    SELECT
        o.customer_id,
        o.order_date,
        LAG(o.order_date) OVER (
            PARTITION BY o.customer_id
            ORDER BY o.order_date
        ) AS previous_order_date,
        CAST(
            JULIANDAY(o.order_date) -
            JULIANDAY(LAG(o.order_date) OVER (
                PARTITION BY o.customer_id ORDER BY o.order_date
            ))
            AS INTEGER
        ) AS days_gap
    FROM orders o
    WHERE o.status NOT IN ('CANCELLED')
),
avg_gaps AS (
    SELECT
        customer_id,
        AVG(days_gap) AS avg_gap_days
    FROM order_gaps
    WHERE days_gap IS NOT NULL
    GROUP BY customer_id
)
SELECT
    og.customer_id,
    og.order_date,
    og.previous_order_date,
    og.days_gap,
    ROUND(ag.avg_gap_days, 1) AS avg_gap_days,
    CASE
        WHEN ag.avg_gap_days > 30 THEN 'At Risk'
        ELSE 'Normal'
    END AS risk_flag
FROM order_gaps og
LEFT JOIN avg_gaps ag ON og.customer_id = ag.customer_id
ORDER BY og.customer_id, og.order_date;

-- Query 10: Multi-level CTE categorizing monthly customer revenue counts
WITH monthly_cust_revenue AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS month,
        ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS monthly_revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.quantity > 0
      AND o.status NOT IN ('CANCELLED')
    GROUP BY o.customer_id, month
),
categorized AS (
    SELECT
        month,
        customer_id,
        monthly_revenue,
        CASE
            WHEN monthly_revenue > 10000 THEN 'High'
            WHEN monthly_revenue >= 5000 THEN 'Medium'
            ELSE                              'Low'
        END AS revenue_category
    FROM monthly_cust_revenue
)
SELECT
    month,
    revenue_category,
    COUNT(DISTINCT customer_id) AS customer_count,
    ROUND(AVG(monthly_revenue), 2) AS avg_monthly_revenue
FROM categorized
GROUP BY month, revenue_category
ORDER BY month, revenue_category;

-- Query 11: Customer Lifetime Value Quartiles (NTILE)
WITH customer_ltv AS (
    SELECT
        o.customer_id,
        ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS total_value
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.quantity > 0
      AND o.status NOT IN ('CANCELLED')
    GROUP BY o.customer_id
)
SELECT
    c.customer_id,
    c.customer_name,
    ltv.total_value,
    NTILE(4) OVER (ORDER BY ltv.total_value DESC) AS quartile,
    CASE NTILE(4) OVER (ORDER BY ltv.total_value DESC)
        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        WHEN 4 THEN 'Bronze'
    END AS quartile_label
FROM customer_ltv ltv
JOIN customers c ON ltv.customer_id = c.customer_id
ORDER BY ltv.total_value DESC;

-- Query 12: Year-over-Year monthly revenue comparison
WITH monthly_rev AS (
    SELECT
        strftime('%Y', o.order_date) AS year,
        strftime('%m', o.order_date) AS month,
        ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.quantity > 0
      AND o.status NOT IN ('CANCELLED')
    GROUP BY year, month
)
SELECT
    cur.year,
    cur.month,
    cur.revenue,
    prev.revenue AS prev_year_revenue,
    CASE
        WHEN prev.revenue IS NULL OR prev.revenue = 0 THEN NULL
        ELSE ROUND((cur.revenue - prev.revenue) / prev.revenue * 100.0, 2)
    END AS yoy_growth_percent
FROM monthly_rev cur
LEFT JOIN monthly_rev prev
    ON cur.month = prev.month
   AND CAST(cur.year AS INTEGER) = CAST(prev.year AS INTEGER) + 1
ORDER BY cur.year, cur.month;

-- Query 13: Customer category shift (First vs Last purchased category)
WITH ranked_purchases AS (
    SELECT
        o.customer_id,
        p.category,
        o.order_date,
        ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date ASC) AS rn_first,
        ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date DESC) AS rn_last
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE oi.quantity > 0
      AND o.status NOT IN ('CANCELLED')
),
first_cat AS (
    SELECT customer_id, category AS first_category
    FROM ranked_purchases WHERE rn_first = 1
),
last_cat AS (
    SELECT customer_id, category AS last_category
    FROM ranked_purchases WHERE rn_last = 1
)
SELECT
    fc.customer_id,
    fc.first_category,
    lc.last_category,
    CASE
        WHEN fc.first_category != lc.last_category THEN 'Yes'
        ELSE 'No'
    END AS category_shift
FROM first_cat fc
JOIN last_cat lc ON fc.customer_id = lc.customer_id
ORDER BY fc.customer_id;

-- Query 14: Cumulative revenue distribution (Pareto analysis)
WITH customer_rev AS (
    SELECT
        o.customer_id,
        ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.quantity > 0
      AND o.status NOT IN ('CANCELLED')
    GROUP BY o.customer_id
),
cumulative AS (
    SELECT
        customer_id,
        revenue,
        SUM(revenue) OVER (
            ORDER BY revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue,
        SUM(revenue) OVER () AS total_revenue
    FROM customer_rev
)
SELECT
    customer_id,
    ROUND(revenue, 2) AS revenue,
    ROUND(cumulative_revenue, 2) AS cumulative_revenue,
    ROUND(cumulative_revenue / total_revenue * 100.0, 2) AS cumulative_percent
FROM cumulative
ORDER BY revenue DESC;

-- Query 15: Cohort monthly retention analysis (using registration date)
WITH customer_cohort AS (
    SELECT
        customer_id,
        strftime('%Y-%m', registration_date) AS cohort_month
    FROM customers
    WHERE registration_date IS NOT NULL
),
order_activity AS (
    SELECT
        cc.customer_id,
        cc.cohort_month,
        CAST(
            (CAST(strftime('%Y', o.order_date) AS INTEGER) -
             CAST(strftime('%Y', cc.cohort_month || '-01') AS INTEGER)) * 12
            + (CAST(strftime('%m', o.order_date) AS INTEGER) -
               CAST(strftime('%m', cc.cohort_month || '-01') AS INTEGER))
            AS INTEGER
        ) AS months_since_reg
    FROM customer_cohort cc
    JOIN orders o ON cc.customer_id = o.customer_id
    WHERE o.status NOT IN ('CANCELLED')
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM customer_cohort
    GROUP BY cohort_month
),
retention AS (
    SELECT
        cohort_month,
        months_since_reg,
        COUNT(DISTINCT customer_id) AS active_count
    FROM order_activity
    WHERE months_since_reg IN (0, 1, 2, 3)
    GROUP BY cohort_month, months_since_reg
)
SELECT
    r.cohort_month,
    cs.cohort_size,
    r.months_since_reg AS month_number,
    r.active_count,
    ROUND(r.active_count * 100.0 / cs.cohort_size, 1) AS retention_rate_pct
FROM retention r
JOIN cohort_sizes cs ON r.cohort_month = cs.cohort_month
ORDER BY r.cohort_month, r.months_since_reg;

-- Query 16: Frequently bought-together products (self-join)
WITH product_pairs AS (
    SELECT
        a.order_id,
        a.product_id AS pid_a,
        b.product_id AS pid_b
    FROM order_items a
    JOIN order_items b
        ON a.order_id = b.order_id
        AND a.product_id < b.product_id
    WHERE a.quantity > 0
      AND b.quantity > 0
),
pair_counts AS (
    SELECT
        pid_a,
        pid_b,
        COUNT(DISTINCT order_id) AS times_bought_together
    FROM product_pairs
    GROUP BY pid_a, pid_b
)
SELECT
    pa.product_name AS product_a,
    pb.product_name AS product_b,
    pa.category AS category_a,
    pb.category AS category_b,
    pc.times_bought_together
FROM pair_counts pc
JOIN products pa ON pc.pid_a = pa.product_id
JOIN products pb ON pc.pid_b = pb.product_id
ORDER BY times_bought_together DESC
LIMIT 25;
