-- Star schema DDL for retail supply chain (SQLite)
-- Dimensional model: one fact table + four dimensions

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS product_clusters;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_warehouse;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_warehouse (
    warehouse_id INTEGER PRIMARY KEY
);

CREATE TABLE dim_store (
    store_id     INTEGER PRIMARY KEY,
    warehouse_id INTEGER NOT NULL REFERENCES dim_warehouse(warehouse_id)
);

CREATE TABLE dim_product (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    price        REAL NOT NULL
);

CREATE TABLE dim_date (
    date_id   INTEGER PRIMARY KEY,  -- YYYYMMDD
    full_date TEXT NOT NULL,
    year      INTEGER NOT NULL,
    month     INTEGER NOT NULL,
    day       INTEGER NOT NULL,
    weekday   INTEGER NOT NULL     -- 0=Mon .. 6=Sun
);

CREATE TABLE fact_sales (
    sale_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id      INTEGER NOT NULL REFERENCES dim_date(date_id),
    product_id   INTEGER NOT NULL REFERENCES dim_product(product_id),
    store_id     INTEGER NOT NULL REFERENCES dim_store(store_id),
    warehouse_id INTEGER NOT NULL REFERENCES dim_warehouse(warehouse_id),
    sales_qty    INTEGER NOT NULL,
    stock_qty    INTEGER NOT NULL,
    revenue      REAL NOT NULL
);

-- Populated by clustering/demand_clustering.py after K-Means
CREATE TABLE product_clusters (
    Product_ID           INTEGER,
    Product_Name         TEXT,
    total_sales          REAL,
    avg_daily_sales      REAL,
    sales_volatility     REAL,
    avg_stock            REAL,
    revenue              REAL,
    avg_price            REAL,
    store_count          INTEGER,
    stock_to_sales_ratio REAL,
    cluster              INTEGER,
    demand_level         TEXT
);

CREATE INDEX idx_fact_date ON fact_sales(date_id);
CREATE INDEX idx_fact_product ON fact_sales(product_id);
CREATE INDEX idx_fact_warehouse ON fact_sales(warehouse_id);
