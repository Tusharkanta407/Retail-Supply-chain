"""Data-quality profiling, cleaning, and enrichment."""
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def profile_dq(df: DataFrame) -> dict:
    """Compute before-clean DQ metrics for the case-study report."""
    total = df.count()
    null_sales = df.filter(F.col("Sales_Quantity").isNull()).count()
    null_stock = df.filter(F.col("Stock_Quantity").isNull()).count()
    null_any = df.filter(
        F.col("Date").isNull()
        | F.col("Product_ID").isNull()
        | F.col("Store_ID").isNull()
        | F.col("Warehouse_ID").isNull()
        | F.col("Sales_Quantity").isNull()
        | F.col("Stock_Quantity").isNull()
        | F.col("Price").isNull()
    ).count()
    neg_sales = df.filter(F.col("Sales_Quantity") < 0).count()
    neg_stock = df.filter(F.col("Stock_Quantity") < 0).count()
    dupes = total - df.dropDuplicates().count()
    return {
        "stage": "before_clean",
        "total_rows": total,
        "null_any_key_field": null_any,
        "null_sales_quantity": null_sales,
        "null_stock_quantity": null_stock,
        "negative_sales": neg_sales,
        "negative_stock": neg_stock,
        "duplicate_rows": dupes,
    }


def clean_sales(df: DataFrame) -> DataFrame:
    """Drop nulls/duplicates and remove invalid quantities."""
    return (
        df.dropna(
            subset=[
                "Date",
                "Product_ID",
                "Store_ID",
                "Warehouse_ID",
                "Sales_Quantity",
                "Stock_Quantity",
                "Price",
            ]
        )
        .dropDuplicates()
        .filter((F.col("Sales_Quantity") >= 0) & (F.col("Stock_Quantity") >= 0))
        .withColumn("Sales_Quantity", F.col("Sales_Quantity").cast("int"))
        .withColumn("Stock_Quantity", F.col("Stock_Quantity").cast("int"))
    )


def enrich_sales(df: DataFrame) -> DataFrame:
    """Add date parts, recompute revenue, weekend flag."""
    return (
        df.withColumn("Date", F.to_date("Date"))
        .filter(F.col("Date").isNotNull())
        .withColumn("Year", F.year("Date"))
        .withColumn("Month", F.month("Date"))
        .withColumn("Week", F.weekofyear("Date"))
        .withColumn("DayOfWeek", F.dayofweek("Date"))  # 1=Sun ... 7=Sat
        .withColumn(
            "IsWeekend",
            F.when(F.col("DayOfWeek").isin(1, 7), F.lit(1)).otherwise(F.lit(0)),
        )
        .withColumn(
            "Revenue",
            F.round(F.col("Sales_Quantity") * F.col("Price"), 2),
        )
    )


def after_clean_metrics(before: dict, cleaned: DataFrame) -> list[dict]:
    after_n = cleaned.count()
    removed = before["total_rows"] - after_n
    return [
        before,
        {
            "stage": "after_clean",
            "total_rows": after_n,
            "rows_removed": removed,
            "pct_removed": round(100.0 * removed / max(before["total_rows"], 1), 2),
            "null_any_key_field": 0,
            "null_sales_quantity": 0,
            "null_stock_quantity": 0,
            "negative_sales": 0,
            "negative_stock": 0,
            "duplicate_rows": 0,
        },
    ]
