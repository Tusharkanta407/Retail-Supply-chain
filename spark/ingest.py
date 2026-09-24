"""Ingest raw sales CSV with an explicit schema."""
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

SALES_SCHEMA = StructType(
    [
        StructField("Date", StringType(), True),
        StructField("Product_ID", IntegerType(), True),
        StructField("Product_Name", StringType(), True),
        StructField("Store_ID", IntegerType(), True),
        StructField("Warehouse_ID", IntegerType(), True),
        StructField("Sales_Quantity", DoubleType(), True),
        StructField("Stock_Quantity", DoubleType(), True),
        StructField("Price", DoubleType(), True),
        StructField("Revenue", DoubleType(), True),
    ]
)


def read_sales(spark: SparkSession, path: str) -> DataFrame:
    df = spark.read.csv(path, header=True, schema=SALES_SCHEMA)
    print("=== Ingest ===")
    print(f"Source: {path}")
    print(f"Raw rows: {df.count()}")
    df.printSchema()
    return df
