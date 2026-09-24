-- Q1: units sold and revenue per warehouse
SELECT warehouse_id, SUM(sales_qty) AS units, ROUND(SUM(revenue),2) AS revenue
FROM fact_sales GROUP BY warehouse_id ORDER BY units DESC;

-- Q2: top 10 products by revenue
SELECT p.product_name, ROUND(SUM(f.revenue),2) AS revenue
FROM fact_sales f JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.product_name ORDER BY revenue DESC LIMIT 10;

-- Q3: monthly sales trend
SELECT d.year, d.month, SUM(f.sales_qty) AS units
FROM fact_sales f JOIN dim_date d ON d.date_id = f.date_id GROUP BY d.year, d.month;

-- Q4: products at stock-out risk (avg stock < 2x avg daily sales) with demand cluster
SELECT c.product_id, c.demand_level, ROUND(c.avg_daily_sales,1) AS avg_daily, ROUND(c.avg_stock,1) AS avg_stock
FROM product_clusters c WHERE c.avg_stock < 2 * c.avg_daily_sales ORDER BY c.avg_daily_sales DESC;
