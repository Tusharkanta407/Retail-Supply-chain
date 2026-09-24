"""Step 2: PySpark processing - clean, transform, aggregate, MapReduce."""
from pyspark.sql import SparkSession, functions as F
spark = SparkSession.builder.appName("SupplyChain").master("local[*]").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

df = spark.read.csv("data/sales.csv", header=True, inferSchema=True)
raw_n = df.count()
df = (df.dropna().dropDuplicates()
        .filter((F.col("Sales_Quantity") >= 0) & (F.col("Stock_Quantity") >= 0))
        .withColumn("Date", F.to_date("Date"))
        .withColumn("Revenue", F.round(F.col("Sales_Quantity") * F.col("Price"), 2)))
print(f"Rows before cleaning: {raw_n}, after: {df.count()}")

# --- MapReduce (RDD): total units sold per warehouse ---
wh = (df.rdd.map(lambda r: (r.Warehouse_ID, r.Sales_Quantity))   # map
        .reduceByKey(lambda a, b: a + b)                         # reduce
        .sortByKey().collect())
print("MapReduce - units sold per warehouse:")
for k, v in wh: print(f"  Warehouse {k}: {v}")

# --- DataFrame aggregations ---
prod = (df.groupBy("Product_ID").agg(
    F.sum("Sales_Quantity").alias("total_sales"),
    (F.sum("Sales_Quantity") / F.countDistinct("Date")).alias("avg_daily_sales"),
    F.avg("Stock_Quantity").alias("avg_stock"),
    F.sum("Revenue").alias("revenue")))
wsum = df.groupBy("Warehouse_ID").agg(
    F.sum("Sales_Quantity").alias("units_sold"),
    F.avg("Stock_Quantity").alias("avg_stock"),
    F.sum("Revenue").alias("revenue"))

df.toPandas().to_csv("data/clean_sales.csv", index=False)
prod.toPandas().to_csv("data/product_features.csv", index=False)
wsum.toPandas().to_csv("data/warehouse_summary.csv", index=False)
spark.stop()
