# explain.md — Full project walkthrough (start → end)

This document explains **everything we built**, step by step, from generating the dataset to the final submission evidence.

You are **not** building a huge real-world retail app. You are demonstrating four marked areas:

| Marks | Area | What proves it |
|------:|------|----------------|
| 5 | Big Data / PySpark | Clean, aggregate, MapReduce on sales data |
| 5 | Data modeling | ER + star schema + SQL queries |
| 5 | ML / Clustering | K-Means → Low / Medium / High demand |
| 5 | AI + Security | GPT demand scenarios + STRIDE on APIs |

```
RETAIL DATA (CSV)
       ↓
   PySpark (clean + analyze)
       ↓
   Clean / aggregate tables
       ↓
   ┌─────────────┬─────────────┐
   ↓             ↓             ↓
 Star schema   K-Means      (features)
 ER + SQL      Low/Med/High
   ↓             ↓
   └──────┬──────┘
          ↓
   Thin FastAPI + GPT scenarios
          ↓
   STRIDE security + screenshots + report
```

---

## Step 0 — Project idea (why this exists)

**Business problem:** A retailer has many products, stores, and warehouses. They need to:

1. Clean and process large sales/stock data (Big Data)
2. Store it in a proper analytic model (SQL star schema)
3. Group products by demand (ML clustering)
4. Simulate future demand shocks (GPT) and secure the APIs (STRIDE)

---

## Step 1 — Generate the dataset

**File:** `generate_data.py`  
**Output:** `data/sales.csv`

### What it does
Creates a **synthetic** retail dataset (~60,000 rows) with columns like:

- `Date`, `Product_ID`, `Product_Name`
- `Store_ID`, `Warehouse_ID`
- `Sales_Quantity`, `Stock_Quantity`, `Price`, `Revenue`

### Why dirty rows exist
It intentionally adds:

- null sales
- negative stock
- duplicate rows

So PySpark has a real **data-quality cleaning** story (important for the case study).

### How to run
```bash
python generate_data.py
```

### Status
This is **Phase 1** — done. You do not need a real company CSV for the assignment.

---

## Step 2 — PySpark big-data processing (5 marks)

**Entry scripts:**

- `python spark_process.py`
- or `python pyspark/sales_processing.py` (same pipeline; nicer folder name for markers)

**Real code lives in:** `spark/`

| File | Role |
|------|------|
| `spark/session.py` | Creates local SparkSession |
| `spark/ingest.py` | Reads CSV with **explicit schema** |
| `spark/clean.py` | DQ profile + clean + enrich (dates, revenue, weekend) |
| `spark/analyze.py` | MapReduce + warehouse/store/product/time analytics |
| `spark/io_utils.py` | Writes CSV/JSON outputs |
| `spark/pipeline.py` | Runs the full pipeline end-to-end |

### Pipeline flow

```
sales.csv
   → Ingest (schema + row count)
   → Data quality profile (nulls, negatives, duplicates)
   → Clean (drop bad rows)
   → Enrich (year/month/week, recompute revenue)
   → MapReduce: units sold per warehouse
   → Aggregations: warehouse, store, product features, time, top products
   → Write outputs to data/processed/
```

### Key outputs (`data/processed/`)

| File | Meaning |
|------|---------|
| `clean_sales.csv` | Cleaned fact-level sales |
| `dq_report.json` | Before/after DQ metrics + KPIs |
| `mapreduce_warehouse.csv` | MapReduce warehouse totals |
| `warehouse_summary.csv` | Sales + stock risk flags |
| `store_summary.csv` | Store performance |
| `product_features.csv` | Features for K-Means |
| `time_summary.csv` | Monthly trend |
| `top_products.csv` | Top products + revenue share |

### Example findings from our run
- Raw → clean: **60,150 → 59,698** rows (~0.75% removed)
- ~**509,720** units, ~**$26.9M** revenue
- 150 products, 20 stores, 10 warehouses

### How to run (Windows note)
Spark needs a valid JDK. If Spark fails, set:

```powershell
$env:JAVA_HOME = "C:\Program Files\Java\jdk-21"
python pyspark/sales_processing.py
```

### What to show markers
- Console MapReduce warehouse lines
- `dq_report.json`
- `mapreduce_warehouse.csv`

---

## Step 3 — Database + data modeling (5 marks)

**Goal:** Put cleaned Spark data into a **star schema** and write SQL that answers business questions.

### 3a — Create tables

**File:** `sql/create_tables.sql`

Tables:

- **Dimensions:** `dim_date`, `dim_product`, `dim_store`, `dim_warehouse`
- **Fact:** `fact_sales` (one row ≈ one sale line)
- **Later:** `product_clusters` (filled after K-Means)

This is classic warehouse modeling:

```
        dim_date
           |
dim_product -- fact_sales -- dim_store
           |                    |
      (clusters)          dim_warehouse
```

### 3b — Load data into SQLite

**File:** `build_db.py`  
**Reads:** `data/processed/clean_sales.csv`  
**Writes:** `data/supply_chain.db`

```bash
python build_db.py
```

Loads dims + ~59,698 fact rows.

### 3c — SQL queries

**File:** `sql/queries.sql`

Examples:

1. Units/revenue per warehouse  
2. Top 10 products by revenue  
3. Monthly sales trend  
4. Stock-out risk products + demand cluster  
5. Low/Medium/High cluster counts  
6. Weekend vs weekday revenue  
7. Store performance by warehouse  

Run and save results:

```bash
python sql/run_queries.py
```

Results go to `screenshots/query_results/`.

### 3d — Diagrams

**Files:**

- `diagrams/er_diagram.png`
- `diagrams/star_schema.png`

Generated by:

```bash
python diagrams/generate_diagrams.py
```

Copies also land in `screenshots/` for the report.

### What to show markers
- ER diagram + star schema PNGs
- `create_tables.sql` + `queries.sql`
- Query result screenshots/CSVs

---

## Step 4 — K-Means demand clustering (5 marks)

**File:** `clustering/demand_clustering.py`  
**Input:** `data/processed/product_features.csv`  
**Outputs:**

- `data/product_clusters.csv`
- `data/clusters.png`
- `product_clusters` table in SQLite
- `screenshots/clustering_visualization.png`

### What it does
1. Takes product features (sales, avg daily sales, volatility, stock, revenue)
2. Scales them (`StandardScaler`)
3. Runs **K-Means with k=3**
4. Labels clusters by demand strength:
   - **Low**
   - **Medium**
   - **High**
5. Draws a scatter plot (avg daily sales vs revenue)

### Our result
| Demand | Products |
|--------|----------|
| Low | 84 |
| Medium | 57 |
| High | 9 |

### How to run
```bash
python clustering/demand_clustering.py
```

(`cluster.py` at the root is only a thin wrapper that calls the same script.)

### What to show markers
- Clustering script
- `clusters.png` / screenshot
- Low/Med/High counts

---

## Step 5 — GPT demand scenarios (part of AI + Security)

**File:** `ai/demand_scenarios.py`

### Important distinction
- **K-Means** = “What demand group is this product in *from history*?”
- **GPT / scenarios** = “What *could happen next* under Normal / Festival / Low demand / Supply disruption?”

### How it works
1. Reads baseline units/stock from SQLite (`fact_sales`)
2. Also knows how many **High** demand products exist
3. If `OPENAI_API_KEY` is set → calls GPT for expected units + risk + recommendation  
4. If no key (or GPT fails) → **rule-based fallback** (still valid for demo)

### How to run
```bash
python ai/demand_scenarios.py --scenario Festival
python ai/demand_scenarios.py --all
```

Output example is saved to:

`screenshots/gpt_demand_scenarios.json`

---

## Step 6 — Thin Supply Chain API (for STRIDE)

**File:** `app.py`  
**Run:**

```bash
uvicorn app:app --reload --port 8000
```

### Why an API exists
Markers want **STRIDE on APIs**. So we keep a **thin FastAPI**, not a big frontend.

### Main endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/upload` | Upload CSV (API key) |
| POST | `/process` | Run Spark → DB → clustering (API key) |
| GET | `/sales-summary` | Monthly sales |
| GET | `/warehouse-summary` | Warehouse KPIs |
| GET | `/inventory-summary` | Products + demand level |
| GET | `/cluster-demand` | Low/Med/High counts |
| GET | `/cluster-plot` | Cluster PNG |
| POST | `/demand-simulation` | GPT/fallback scenarios (API key) |

Write endpoints need header:

```
x-api-key: dev-key
```

(Default key; change with env `API_KEY`.)

---

## Step 7 — STRIDE security analysis (rest of AI + Security)

**File:** `STRIDE.md`  
**Screenshot:** `screenshots/stride_table.png`

STRIDE = six threat types:

| Letter | Meaning |
|--------|---------|
| S | Spoofing |
| T | Tampering |
| R | Repudiation |
| I | Information Disclosure |
| D | Denial of Service |
| E | Elevation of Privilege |

We map each API endpoint to threats and list mitigations already in the prototype (API key, CSV-only, 20 MB limit, scenario whitelist, GPT fallback, etc.).

---

## Step 8 — Screenshots + report (what you hand in)

### Evidence pack folder: `screenshots/`

| File | For |
|------|-----|
| `schema_er_diagram.png` | Data modeling |
| `schema_star_diagram.png` | Data modeling |
| `sql_query_results_Q1.png` + `query_results/*.csv` | SQL results |
| `pyspark_dq_report.json` | Big Data DQ |
| `pyspark_mapreduce.csv` | MapReduce |
| `clustering_visualization.png` | ML |
| `gpt_demand_scenarios.json` | AI |
| `stride_table.png` | Security |
| `REPORT_CHECKLIST.md` | What to put in the PDF |

### You still write: `report.pdf`

Suggested structure:

1. Problem & dataset  
2. PySpark findings  
3. Data model (ER + star + queries)  
4. Clustering interpretation  
5. GPT scenarios  
6. API + STRIDE  
7. How to run (appendix)

---

## Full run order (from empty → ready)

```bash
# 1 Dataset
python generate_data.py

# 2 PySpark
python pyspark/sales_processing.py

# 3 Database
python build_db.py

# 4 Clustering
python clustering/demand_clustering.py

# 5 SQL results for screenshots
python sql/run_queries.py

# 6 Diagrams
python diagrams/generate_diagrams.py

# 7 GPT scenarios
python ai/demand_scenarios.py --all

# 8 API (optional live demo)
uvicorn app:app --reload --port 8000
```

Install deps once:

```bash
pip install -r requirements.txt
```

---

## Final folder map (what each part is for)

```
Retail_Supply_chain/
├── generate_data.py          Step 1 — make sales.csv
├── data/
│   ├── sales.csv             raw dataset
│   ├── processed/            PySpark outputs
│   ├── supply_chain.db       SQLite star schema
│   └── clusters.png          K-Means plot
├── spark/ + spark_process.py Step 2 — Big Data engine
├── pyspark/sales_processing.py  marker-friendly entry
├── sql/                      Step 3 — DDL + queries
├── build_db.py               Step 3 — load DB
├── diagrams/                 Step 3 — ER + star PNGs
├── clustering/               Step 4 — K-Means
├── ai/                       Step 5 — GPT scenarios
├── app.py                    Step 6 — thin API
├── STRIDE.md                 Step 7 — security write-up
├── screenshots/              Step 8 — evidence for report
├── requirements.txt
└── explain.md                this file
```

---

## What we deliberately did **not** build

- Full Next.js / fancy UI (not needed for the four mark areas)
- Cloud Spark cluster / production OAuth
- Perfect enterprise security (prototype mitigations + STRIDE analysis are enough)

---

## One-line summary

**Generate retail CSV → PySpark cleans & analyzes it → load star schema + SQL → K-Means demand groups → GPT scenarios via thin API → STRIDE + screenshots → you write the PDF report.**
