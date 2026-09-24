"""Case-study analytics: MapReduce + DataFrame aggregations."""
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def mapreduce_warehouse_units(df: DataFrame) -> DataFrame:
    """
    MapReduce case-study job: (Warehouse_ID, Sales_Quantity) -> sum units.

    1) Distributed Spark reduce (DataFrame groupBy) — Catalyst runs map/combine/reduce.
    2) Explicit Python map → reduceByKey verification on the key/value stream
       (RDD lambdas crash on some Windows/Python 3.12 setups; this keeps the
       MapReduce algorithm visible and checkable for the report).
    """
    spark = df.sparkSession

    # --- Distributed MapReduce analogue (Spark SQL / Catalyst) ---
    spark_reduced = (
        df.groupBy("Warehouse_ID")
        .agg(F.sum("Sales_Quantity").alias("units_sold_mr"))
        .orderBy("Warehouse_ID")
    )

    # --- Explicit map → reduceByKey (algorithm evidence) ---
    # MAP: emit (warehouse_id, sales_qty) pairs from the cleaned fact table
    mapped_pairs = [
        (int(r["Warehouse_ID"]), int(r["Sales_Quantity"]))
        for r in df.select("Warehouse_ID", "Sales_Quantity").collect()
    ]
    # REDUCE: sum values per key
    reduced: dict[int, int] = {}
    for key, value in mapped_pairs:
        reduced[key] = reduced.get(key, 0) + value
    rows = sorted(reduced.items(), key=lambda x: x[0])

    print("=== MapReduce: units sold per warehouse ===")
    print(f"  mapped pairs: {len(mapped_pairs):,}  reduced keys: {len(rows)}")
    for wid, units in rows:
        print(f"  Warehouse {wid}: {units:,} units")

    # Sanity: Python reduce must match Spark aggregate
    spark_map = {
        int(r["Warehouse_ID"]): int(r["units_sold_mr"]) for r in spark_reduced.collect()
    }
    assert spark_map == dict(rows), "MapReduce mismatch vs Spark groupBy"
    return spark_reduced


def warehouse_summary(df: DataFrame) -> DataFrame:
    """Sales + inventory health by warehouse with over/under stock flags."""
    agg = df.groupBy("Warehouse_ID").agg(
        F.sum("Sales_Quantity").alias("units_sold"),
        F.round(F.sum("Revenue"), 2).alias("revenue"),
        F.round(F.avg("Stock_Quantity"), 1).alias("avg_stock"),
        F.count("*").alias("txn_count"),
        F.countDistinct("Product_ID").alias("products"),
        F.countDistinct("Store_ID").alias("stores"),
    )
    # stock_to_sales: avg stock per unit sold (higher => more overstocked)
    agg = agg.withColumn(
        "stock_to_sales",
        F.round(F.col("avg_stock") / F.greatest(F.col("units_sold") / F.lit(1000.0), F.lit(0.01)), 2),
    )
    stats = agg.agg(
        F.expr("percentile_approx(stock_to_sales, 0.33)").alias("p33"),
        F.expr("percentile_approx(stock_to_sales, 0.66)").alias("p66"),
    ).collect()[0]
    p33, p66 = stats["p33"], stats["p66"]
    return agg.withColumn(
        "stock_risk",
        F.when(F.col("stock_to_sales") <= p33, F.lit("understock"))
        .when(F.col("stock_to_sales") >= p66, F.lit("overstock"))
        .otherwise(F.lit("balanced")),
    ).orderBy("Warehouse_ID")


def store_summary(df: DataFrame) -> DataFrame:
    return (
        df.groupBy("Store_ID", "Warehouse_ID")
        .agg(
            F.sum("Sales_Quantity").alias("units_sold"),
            F.round(F.sum("Revenue"), 2).alias("revenue"),
            F.round(F.avg("Stock_Quantity"), 1).alias("avg_stock"),
            F.count("*").alias("txn_count"),
        )
        .orderBy(F.desc("revenue"))
    )


def product_features(df: DataFrame) -> DataFrame:
    """Feature table for Phase 4 K-Means (includes volatility + stock ratio)."""
    return (
        df.groupBy("Product_ID", "Product_Name")
        .agg(
            F.sum("Sales_Quantity").alias("total_sales"),
            F.round(F.sum("Sales_Quantity") / F.countDistinct("Date"), 2).alias(
                "avg_daily_sales"
            ),
            F.round(F.stddev_pop("Sales_Quantity"), 2).alias("sales_volatility"),
            F.round(F.avg("Stock_Quantity"), 1).alias("avg_stock"),
            F.round(F.sum("Revenue"), 2).alias("revenue"),
            F.round(F.avg("Price"), 2).alias("avg_price"),
            F.countDistinct("Store_ID").alias("store_count"),
        )
        .withColumn(
            "stock_to_sales_ratio",
            F.round(
                F.col("avg_stock")
                / F.greatest(F.col("avg_daily_sales"), F.lit(0.01)),
                2,
            ),
        )
        .orderBy(F.desc("total_sales"))
    )


def time_summary(df: DataFrame) -> DataFrame:
    return (
        df.groupBy("Year", "Month")
        .agg(
            F.sum("Sales_Quantity").alias("units_sold"),
            F.round(F.sum("Revenue"), 2).alias("revenue"),
            F.round(F.avg("Stock_Quantity"), 1).alias("avg_stock"),
            F.count("*").alias("txn_count"),
        )
        .orderBy("Year", "Month")
    )


def top_products(df: DataFrame, n: int = 20) -> DataFrame:
    """Top-N products by revenue + cumulative share (Pareto / concentration)."""
    by_prod = (
        df.groupBy("Product_ID", "Product_Name")
        .agg(
            F.sum("Sales_Quantity").alias("units_sold"),
            F.round(F.sum("Revenue"), 2).alias("revenue"),
        )
    )
    total_rev = by_prod.agg(F.sum("revenue")).collect()[0][0] or 1.0
    w = Window.orderBy(F.desc("revenue"))
    return (
        by_prod.withColumn("rank", F.row_number().over(w))
        .withColumn("revenue_share_pct", F.round(100.0 * F.col("revenue") / total_rev, 2))
        .withColumn(
            "cumulative_share_pct",
            F.round(100.0 * F.sum("revenue").over(w.rowsBetween(Window.unboundedPreceding, 0)) / total_rev, 2),
        )
        .filter(F.col("rank") <= n)
        .orderBy("rank")
    )


def kpi_snapshot(df: DataFrame) -> dict:
    row = df.agg(
        F.count("*").alias("transactions"),
        F.sum("Sales_Quantity").alias("total_units"),
        F.round(F.sum("Revenue"), 2).alias("total_revenue"),
        F.countDistinct("Product_ID").alias("products"),
        F.countDistinct("Store_ID").alias("stores"),
        F.countDistinct("Warehouse_ID").alias("warehouses"),
        F.min("Date").alias("date_min"),
        F.max("Date").alias("date_max"),
    ).collect()[0]
    return {
        "transactions": row["transactions"],
        "total_units": int(row["total_units"] or 0),
        "total_revenue": float(row["total_revenue"] or 0),
        "products": row["products"],
        "stores": row["stores"],
        "warehouses": row["warehouses"],
        "date_min": str(row["date_min"]),
        "date_max": str(row["date_max"]),
    }
