"""Phase 2 pipeline: ingest → DQ/clean → enrich → MapReduce → analytics → persist."""
from pathlib import Path

from spark.analyze import (
    kpi_snapshot,
    mapreduce_warehouse_units,
    product_features,
    store_summary,
    time_summary,
    top_products,
    warehouse_summary,
)
from spark.clean import after_clean_metrics, clean_sales, enrich_sales, profile_dq
from spark.ingest import read_sales
from spark.io_utils import ensure_dir, write_json, write_single_csv
from spark.session import get_spark

ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "sales.csv"
PROCESSED = ROOT / "data" / "processed"
# Compat paths for Phase 3/4 scaffolds that still read data/*.csv
COMPAT = ROOT / "data"


def run(raw_csv: str | Path = RAW_CSV, out_dir: str | Path = PROCESSED) -> dict:
    raw_csv = Path(raw_csv)
    out_dir = ensure_dir(out_dir)
    if not raw_csv.exists():
        raise FileNotFoundError(f"Missing dataset: {raw_csv}. Run generate_data.py first.")

    spark = get_spark()
    try:
        # 1) Ingest
        raw = read_sales(spark, str(raw_csv))

        # 2) DQ + clean
        before = profile_dq(raw)
        cleaned = clean_sales(raw)
        print(
            f"=== Clean ===\n"
            f"Rows before: {before['total_rows']}, after: {cleaned.count()} "
            f"(removed nulls/dupes/negatives)"
        )

        # 3) Enrich
        fact = enrich_sales(cleaned).cache()
        dq_rows = after_clean_metrics(before, fact)
        kpis = kpi_snapshot(fact)
        print("=== KPI snapshot ===")
        for k, v in kpis.items():
            print(f"  {k}: {v}")

        # 4) MapReduce evidence
        mr = mapreduce_warehouse_units(fact)

        # 5) DataFrame analytics
        wh = warehouse_summary(fact)
        st = store_summary(fact)
        prod = product_features(fact)
        time_s = time_summary(fact)
        top = top_products(fact, n=20)

        print("=== Warehouse stock risk ===")
        for r in wh.select("Warehouse_ID", "units_sold", "revenue", "stock_risk").collect():
            print(
                f"  WH {r['Warehouse_ID']}: units={r['units_sold']:,} "
                f"rev={r['revenue']:,.0f} risk={r['stock_risk']}"
            )

        # 6) Persist under data/processed/
        print("=== Writing outputs ===")
        write_single_csv(fact, out_dir / "clean_sales.csv")
        write_single_csv(mr, out_dir / "mapreduce_warehouse.csv")
        write_single_csv(wh, out_dir / "warehouse_summary.csv")
        write_single_csv(st, out_dir / "store_summary.csv")
        write_single_csv(prod, out_dir / "product_features.csv")
        write_single_csv(time_s, out_dir / "time_summary.csv")
        write_single_csv(top, out_dir / "top_products.csv")
        write_json({"dq": dq_rows, "kpis": kpis}, out_dir / "dq_report.json")

        # Compat copies for existing Phase 3/4 scaffolds
        write_single_csv(fact, COMPAT / "clean_sales.csv")
        write_single_csv(prod, COMPAT / "product_features.csv")
        write_single_csv(wh, COMPAT / "warehouse_summary.csv")

        summary = {
            "raw_rows": before["total_rows"],
            "clean_rows": kpis["transactions"],
            "outputs": str(out_dir),
            "kpis": kpis,
        }
        print("=== Phase 2 complete ===")
        return summary
    finally:
        spark.stop()


if __name__ == "__main__":
    run()
