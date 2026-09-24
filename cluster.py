"""Step 4: K-Means demand clustering (Low / Medium / High)."""
import sqlite3, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
df = pd.read_csv("data/product_features.csv")
X = StandardScaler().fit_transform(df[["total_sales", "avg_daily_sales", "avg_stock", "revenue"]])
df["cluster"] = KMeans(n_clusters=3, n_init=10, random_state=42).fit_predict(X)
order = df.groupby("cluster").avg_daily_sales.mean().sort_values().index      # rank clusters by demand
df["demand_level"] = df.cluster.map(dict(zip(order, ["Low", "Medium", "High"])))
df.to_csv("data/product_clusters.csv", index=False)
df.to_sql("product_clusters", sqlite3.connect("data/supply_chain.db"), if_exists="replace", index=False)
for lvl, c in zip(["Low", "Medium", "High"], ["tab:green", "tab:orange", "tab:red"]):
    s = df[df.demand_level == lvl]; plt.scatter(s.avg_daily_sales, s.revenue, c=c, label=f"{lvl} ({len(s)})")
plt.xlabel("Avg daily sales"); plt.ylabel("Revenue"); plt.title("K-Means demand clusters"); plt.legend()
plt.savefig("data/clusters.png", dpi=150); print(df.demand_level.value_counts())
