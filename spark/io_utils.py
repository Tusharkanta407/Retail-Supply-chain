"""Persist Spark DataFrames and small reports under data/processed/."""
import csv
import json
from pathlib import Path

from pyspark.sql import DataFrame


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_single_csv(df: DataFrame, out_csv: str | Path) -> None:
    """
    Write a DataFrame to one CSV via collect (avoids Hadoop winutils on Windows).
    Analysis still runs in Spark; only the final materialization is local.
    """
    out_csv = Path(out_csv)
    ensure_dir(out_csv.parent)
    cols = df.columns
    rows = df.collect()
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])
    print(f"  wrote {out_csv} ({len(rows):,} rows)")


def write_json(obj, path: str | Path) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    print(f"  wrote {path}")
