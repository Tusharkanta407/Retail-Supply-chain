"""
Phase 2 entrypoint: PySpark big-data analysis for the retail supply-chain case study.

Run:  python spark_process.py

Pipeline: ingest → DQ/clean → enrich → MapReduce → analytics → data/processed/*
"""
from spark.pipeline import run

if __name__ == "__main__":
    run()
