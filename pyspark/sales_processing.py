"""
PySpark entrypoint for markers (submission layout).
Run:  python pyspark/sales_processing.py

Delegates to the Phase-2 pipeline in spark/pipeline.py.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from spark.pipeline import run  # noqa: E402

if __name__ == "__main__":
    run()
