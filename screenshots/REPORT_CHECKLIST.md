# Report & screenshot checklist (submission evidence)

Use these files in `report.pdf`. Tick when captured / embedded.

## Required by brief

| Evidence | File / how | Done |
|---|---|---|
| Schema diagrams | `diagrams/er_diagram.png`, `diagrams/star_schema.png` (also under `screenshots/`) | [ ] |
| SQL query results | Run `python sql/run_queries.py` → `screenshots/query_results/Q*.csv` + paste tables into report | [ ] |

## Strongly recommended (4 mark areas)

| Mark area | Evidence | File |
|---|---|---|
| PySpark / Big Data | Console DQ + MapReduce + `data/processed/dq_report.json` | `screenshots/pyspark_dq_report.json` (copy) |
| PySpark | MapReduce warehouse totals | `screenshots/pyspark_mapreduce.csv` (copy) |
| ML / Clustering | Scatter plot Low/Med/High | `screenshots/clustering_visualization.png` |
| ML / Clustering | Cluster counts | print from `clustering/demand_clustering.py` |
| AI | GPT / fallback scenarios JSON | `screenshots/gpt_demand_scenarios.json` |
| Security | STRIDE table | `STRIDE.md` + `screenshots/stride_table.png` |

## How to regenerate evidence

```bash
# 1) Dataset (if needed)
python generate_data.py

# 2) PySpark
python pyspark/sales_processing.py
# or: python spark_process.py

# 3) Star schema
python build_db.py

# 4) Clustering
python clustering/demand_clustering.py

# 5) SQL results
python sql/run_queries.py

# 6) Diagrams
python diagrams/generate_diagrams.py

# 7) GPT scenarios (fallback works without OPENAI_API_KEY)
python ai/demand_scenarios.py --all

# 8) API (optional live demo for STRIDE)
uvicorn app:app --reload --port 8000
```

## report.pdf outline

1. Problem & dataset  
2. PySpark pipeline & findings (DQ, MapReduce, KPIs)  
3. Data model (ER + star + query results)  
4. K-Means demand clusters  
5. GPT demand scenarios  
6. Supply Chain API + STRIDE  
7. Appendix: how to run  

`report.pdf` is written by you (Word/Google Docs → PDF) using the screenshots above.
