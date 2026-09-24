"""
K-Means demand clustering (Low / Medium / High).
Run:  python clustering/demand_clustering.py

Reads:  data/processed/product_features.csv
Writes: data/product_clusters.csv, data/clusters.png, product_clusters table in SQLite
"""
from pathlib import Path
import sqlite3
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ROOT / "data" / "processed" / "product_features.csv"
FALLBACK = ROOT / "data" / "product_features.csv"
OUT_CSV = ROOT / "data" / "product_clusters.csv"
OUT_PNG = ROOT / "data" / "clusters.png"
DB = ROOT / "data" / "supply_chain.db"

FEATURE_COLS = [
    "total_sales",
    "avg_daily_sales",
    "sales_volatility",
    "avg_stock",
    "revenue",
]


def run() -> pd.DataFrame:
    src = FEATURES if FEATURES.exists() else FALLBACK
    if not src.exists():
        raise FileNotFoundError(f"Missing product features: {src}. Run spark_process.py first.")

    df = pd.read_csv(src)
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"product_features missing columns: {missing}")

    # Fill any NaN volatility (single-day products) before scaling
    X = df[FEATURE_COLS].fillna(0.0)
    Xs = StandardScaler().fit_transform(X)

    km = KMeans(n_clusters=3, n_init=10, random_state=42)
    df["cluster"] = km.fit_predict(Xs)

    # Label Low / Medium / High by mean avg_daily_sales
    order = df.groupby("cluster")["avg_daily_sales"].mean().sort_values().index
    df["demand_level"] = df["cluster"].map(dict(zip(order, ["Low", "Medium", "High"])))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    if DB.exists():
        with sqlite3.connect(DB) as con:
            df.to_sql("product_clusters", con, if_exists="replace", index=False)

    plt.figure(figsize=(8, 5))
    for lvl, color in zip(["Low", "Medium", "High"], ["tab:green", "tab:orange", "tab:red"]):
        s = df[df.demand_level == lvl]
        plt.scatter(
            s.avg_daily_sales,
            s.revenue,
            c=color,
            label=f"{lvl} ({len(s)})",
            alpha=0.75,
            edgecolors="none",
        )
    plt.xlabel("Avg daily sales")
    plt.ylabel("Revenue")
    plt.title("K-Means demand clusters (Low / Medium / High)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150)
    plt.close()

    # Also copy plot into screenshots for the evidence pack
    shot = ROOT / "screenshots" / "clustering_visualization.png"
    shot.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    for lvl, color in zip(["Low", "Medium", "High"], ["tab:green", "tab:orange", "tab:red"]):
        s = df[df.demand_level == lvl]
        plt.scatter(s.avg_daily_sales, s.revenue, c=color, label=f"{lvl} ({len(s)})", alpha=0.75)
    plt.xlabel("Avg daily sales")
    plt.ylabel("Revenue")
    plt.title("K-Means demand clusters")
    plt.legend()
    plt.tight_layout()
    plt.savefig(shot, dpi=150)
    plt.close()

    print(f"Source: {src}")
    print("Cluster sizes:")
    print(df.demand_level.value_counts().to_string())
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_PNG}")
    return df


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
