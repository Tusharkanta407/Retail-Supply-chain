"""Step 3: load processed data into a SQL star schema (SQLite)."""
import sqlite3, pandas as pd
SCHEMA = """
DROP TABLE IF EXISTS fact_sales; DROP TABLE IF EXISTS dim_product; DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_warehouse; DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_warehouse(warehouse_id INTEGER PRIMARY KEY);
CREATE TABLE dim_store(store_id INTEGER PRIMARY KEY, warehouse_id INTEGER REFERENCES dim_warehouse);
CREATE TABLE dim_product(product_id INTEGER PRIMARY KEY, product_name TEXT, price REAL);
CREATE TABLE dim_date(date_id INTEGER PRIMARY KEY, full_date TEXT, year INT, month INT, day INT, weekday INT);
CREATE TABLE fact_sales(
  sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_id INT REFERENCES dim_date, product_id INT REFERENCES dim_product,
  store_id INT REFERENCES dim_store, warehouse_id INT REFERENCES dim_warehouse,
  sales_qty INT, stock_qty INT, revenue REAL);
"""
df = pd.read_csv("data/clean_sales.csv", parse_dates=["Date"])
con = sqlite3.connect("data/supply_chain.db"); con.executescript(SCHEMA)
df[["Warehouse_ID"]].drop_duplicates().rename(columns=str.lower).to_sql("dim_warehouse", con, if_exists="append", index=False)
df[["Store_ID", "Warehouse_ID"]].drop_duplicates("Store_ID").rename(columns=str.lower).to_sql("dim_store", con, if_exists="append", index=False)
df[["Product_ID", "Product_Name", "Price"]].drop_duplicates("Product_ID").rename(columns=str.lower).to_sql("dim_product", con, if_exists="append", index=False)
d = df[["Date"]].drop_duplicates().assign(
    date_id=lambda x: x.Date.dt.strftime("%Y%m%d").astype(int), full_date=lambda x: x.Date.dt.strftime("%Y-%m-%d"),
    year=lambda x: x.Date.dt.year, month=lambda x: x.Date.dt.month, day=lambda x: x.Date.dt.day, weekday=lambda x: x.Date.dt.dayofweek).drop(columns="Date")
d.to_sql("dim_date", con, if_exists="append", index=False)
f = pd.DataFrame({"date_id": df.Date.dt.strftime("%Y%m%d").astype(int), "product_id": df.Product_ID, "store_id": df.Store_ID,
    "warehouse_id": df.Warehouse_ID, "sales_qty": df.Sales_Quantity, "stock_qty": df.Stock_Quantity, "revenue": df.Revenue})
f.to_sql("fact_sales", con, if_exists="append", index=False)
con.commit(); print("fact rows:", len(f))
