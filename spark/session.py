"""SparkSession factory for local prototype (same jobs would scale to a cluster)."""
import os
import sys

from pyspark.sql import SparkSession


def _ensure_python_workers() -> None:
    """Point Spark RDD workers at this interpreter (avoids Windows Store python stub)."""
    py = sys.executable
    os.environ.setdefault("PYSPARK_PYTHON", py)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", py)


def get_spark(app_name: str = "RetailSupplyChain") -> SparkSession:
    _ensure_python_workers()
    # Avoid Docker/k8s hostname quirks on some Windows setups
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
    spark = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "2g")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.pyspark.driver.python", sys.executable)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark
