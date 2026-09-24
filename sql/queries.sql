-- Case-study SQL queries against the star schema
-- Run after: python build_db.py && python clustering/demand_clustering.py

-- Q1: Units sold and revenue per warehouse
SELECT
    warehouse_id,
    SUM(sales_qty) AS units,
    ROUND(SUM(revenue), 2) AS revenue
FROM fact_sales
GROUP BY warehouse_id
ORDER BY units DESC;

-- Q2: Top 10 products by revenue
SELECT
    p.product_name,
    ROUND(SUM(f.revenue), 2) AS revenue,
    SUM(f.sales_qty) AS units
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.product_name
ORDER BY revenue DESC
LIMIT 10;

-- Q3: Monthly sales trend
SELECT
    d.year,
    d.month,
    SUM(f.sales_qty) AS units,
    ROUND(SUM(f.revenue), 2) AS revenue
FROM fact_sales f
JOIN dim_date d ON d.date_id = f.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- Q4: Products at stock-out risk with demand cluster
-- (avg stock < 2x avg daily sales)
SELECT
    c.product_id,
    c.demand_level,
    ROUND(c.avg_daily_sales, 1) AS avg_daily,
    ROUND(c.avg_stock, 1) AS avg_stock
FROM product_clusters c
WHERE c.avg_stock < 2 * c.avg_daily_sales
ORDER BY c.avg_daily_sales DESC;

-- Q5: Demand cluster counts (Low / Medium / High)
SELECT
    demand_level,
    COUNT(*) AS products,
    ROUND(AVG(avg_daily_sales), 2) AS avg_daily_sales,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM product_clusters
GROUP BY demand_level
ORDER BY
    CASE demand_level
        WHEN 'Low' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'High' THEN 3
    END;

-- Q6: Weekend vs weekday revenue share
SELECT
    CASE WHEN d.weekday IN (5, 6) THEN 'weekend' ELSE 'weekday' END AS day_type,
    SUM(f.sales_qty) AS units,
    ROUND(SUM(f.revenue), 2) AS revenue
FROM fact_sales f
JOIN dim_date d ON d.date_id = f.date_id
GROUP BY day_type;

-- Q7: Store performance within each warehouse
SELECT
    s.warehouse_id,
    s.store_id,
    SUM(f.sales_qty) AS units,
    ROUND(SUM(f.revenue), 2) AS revenue
FROM fact_sales f
JOIN dim_store s ON s.store_id = f.store_id
GROUP BY s.warehouse_id, s.store_id
ORDER BY s.warehouse_id, revenue DESC;
