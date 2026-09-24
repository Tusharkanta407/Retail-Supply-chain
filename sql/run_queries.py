"""Run all queries in sql/queries.sql and print / save results for screenshots."""
from pathlib import Path
import re
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "supply_chain.db"
QUERIES = ROOT / "sql" / "queries.sql"
OUT = ROOT / "screenshots" / "query_results"


def split_queries(text: str) -> list[tuple[str, str]]:
    chunks = re.split(r"\n(?=-- Q\d+:)", text.strip())
    out = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk or not chunk.upper().lstrip().startswith("-- Q"):
            continue
        first = chunk.splitlines()[0]
        title = first.lstrip("- ").strip()
        sql = "\n".join(
            ln for ln in chunk.splitlines() if not ln.strip().startswith("--")
        ).strip().rstrip(";")
        if sql:
            out.append((title, sql))
    return out


def run() -> None:
    if not DB.exists():
        raise FileNotFoundError("Run python build_db.py (and clustering) first.")
    OUT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    for i, (title, sql) in enumerate(split_queries(QUERIES.read_text(encoding="utf-8")), 1):
        print(f"\n=== {title} ===")
        try:
            df = pd.read_sql(sql, con)
        except Exception as e:
            print(f"  SKIP ({e})")
            continue
        print(df.to_string(index=False))
        path = OUT / f"Q{i}_{title.split(':')[0].replace(' ', '_')}.csv"
        df.to_csv(path, index=False)
        print(f"  saved {path.name}")
    con.close()


if __name__ == "__main__":
    run()
