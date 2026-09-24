"""Step 1: synthetic retail sales + stock dataset (with a few dirty rows to justify cleaning)."""
import numpy as np, pandas as pd
from pathlib import Path
rng = np.random.default_rng(42)
P, S, W, D, N = 150, 20, 10, 90, 60000
dates = pd.date_range("2026-06-01", periods=D)
popularity = rng.gamma(2, 4, P + 1)          # product demand level -> gives real clusters
price = rng.uniform(5, 100, P + 1).round(2)
prod = rng.integers(1, P + 1, N)
store = rng.integers(1, S + 1, N)
date = rng.choice(dates, N)
weekend = (pd.DatetimeIndex(date).dayofweek >= 5) * 0.3
df = pd.DataFrame({
    "Date": pd.DatetimeIndex(date).strftime("%Y-%m-%d"),
    "Product_ID": prod, "Product_Name": [f"Product_{p}" for p in prod],
    "Store_ID": store, "Warehouse_ID": (store - 1) % W + 1,
    "Sales_Quantity": rng.poisson(popularity[prod] * (1 + weekend)),
    "Stock_Quantity": rng.integers(20, 500, N), "Price": price[prod]})
df["Revenue"] = (df.Sales_Quantity * df.Price).round(2)
df.loc[rng.choice(N, 200, replace=False), "Sales_Quantity"] = np.nan   # dirty: nulls
df.loc[rng.choice(N, 100, replace=False), "Stock_Quantity"] = -5       # dirty: negatives
df = pd.concat([df, df.sample(150, random_state=1)])                   # dirty: duplicates
Path("data").mkdir(exist_ok=True)
df.to_csv("data/sales.csv", index=False)
print("rows:", len(df))
