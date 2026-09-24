"""
Load Phase-2 processed sales into SQLite star schema.
Run:  python build_db.py

Reads:  data/processed/clean_sales.csv  (fallback: data/clean_sales.csv)
Schema: sql/create_tables.sql
Writes: data/supply_chain.db
"""
from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "supply_chain.db"
SCHEMA = ROOT / "sql" / "create_tables.sql"
PROCESSED = ROOT / "data" / "processed" / "clean_sales.csv"
FALLBACK = ROOT / "data" / "clean_sales.csv"


def load(csv_path: Path | None = None) -> int:
    src = Path(csv_path) if csv_path else (PROCESSED if PROCESSED.exists() else FALLBACK)
    if not src.exists():
        raise FileNotFoundError(f"Missing cleaned sales CSV: {src}. Run spark_process.py first.")

    df = pd.read_csv(src, parse_dates=["Date"])
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))

    # Dimensions
    (
        df[["Warehouse_ID"]]
        .drop_duplicates()
        .rename(columns=str.lower)
        .to_sql("dim_warehouse", con, if_exists="append", index=False)
    )
    (
        df[["Store_ID", "Warehouse_ID"]]
        .drop_duplicates("Store_ID")
        .rename(columns=str.lower)
        .to_sql("dim_store", con, if_exists="append", index=False)
    )
    (
        df[["Product_ID", "Product_Name", "Price"]]
        .drop_duplicates("Product_ID")
        .rename(columns=str.lower)
        .to_sql("dim_product", con, if_exists="append", index=False)
    )
    dates = (
        df[["Date"]]
        .drop_duplicates()
        .assign(
            date_id=lambda x: x.Date.dt.strftime("%Y%m%d").astype(int),
            full_date=lambda x: x.Date.dt.strftime("%Y-%m-%d"),
            year=lambda x: x.Date.dt.year,
            month=lambda x: x.Date.dt.month,
            day=lambda x: x.Date.dt.day,
            weekday=lambda x: x.Date.dt.dayofweek,
        )
        .drop(columns="Date")
    )
    dates.to_sql("dim_date", con, if_exists="append", index=False)

    fact = pd.DataFrame(
        {
            "date_id": df.Date.dt.strftime("%Y%m%d").astype(int),
            "product_id": df.Product_ID,
            "store_id": df.Store_ID,
            "warehouse_id": df.Warehouse_ID,
            "sales_qty": df.Sales_Quantity,
            "stock_qty": df.Stock_Quantity,
            "revenue": df.Revenue,
        }
    )
    fact.to_sql("fact_sales", con, if_exists="append", index=False)
    con.commit()
    n = len(fact)
    print(f"Loaded {src.name} -> {DB.name}")
    print(f"  dim_warehouse: {con.execute('SELECT COUNT(*) FROM dim_warehouse').fetchone()[0]}")
    print(f"  dim_store:     {con.execute('SELECT COUNT(*) FROM dim_store').fetchone()[0]}")
    print(f"  dim_product:   {con.execute('SELECT COUNT(*) FROM dim_product').fetchone()[0]}")
    print(f"  dim_date:      {con.execute('SELECT COUNT(*) FROM dim_date').fetchone()[0]}")
    print(f"  fact_sales:    {n}")
    con.close()
    return n


if __name__ == "__main__":
    load()
