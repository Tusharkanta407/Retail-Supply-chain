# Retail Supply Chain Optimizer — Implementation Plan

Prototype for assignment marks: **Big Data (PySpark)** · **ML (K-Means)** · **Data Modeling (SQL)** · **GPT Simulation** · **STRIDE** · **Working UI**.

---

## Stack

| Layer | Tech | Role |
|---|---|---|
| Frontend | **Next.js** (App Router) | Dashboard: upload, KPIs, clusters, GPT scenarios |
| Backend | **FastAPI** | Orchestrator — all APIs, auth, calls pipelines |
| Big Data | **PySpark** (local[*]) | Clean, aggregate, MapReduce warehouse totals |
| Database | **SQLite** | ER + star schema (`dim_*` / `fact_sales`) |
| ML | **scikit-learn K-Means** | Low / Medium / High demand groups |
| Simulation | **OpenAI GPT** (+ rule fallback) | Normal / Festival / Low demand / Disruption |
| Security | **STRIDE.md** | Threats + mitigations on the APIs |

---

## System architecture

```
┌─────────────────────────────────────────┐
│           Next.js Frontend              │
│  Upload · KPIs · Cluster chart · GPT UI │
└──────────────────┬──────────────────────┘
                   │ HTTP (JSON)
                   ▼
┌─────────────────────────────────────────┐
│              FastAPI                    │
│  /upload  /process  /summaries          │
│  /cluster-demand  /demand-simulation    │
└──────┬──────────┬──────────┬────────────┘
       │          │          │
       ▼          ▼          ▼
   PySpark     SQLite     K-Means
   clean +     star       Low/Med/High
   aggregate   schema     + clusters.png
       │
       └──────────► GPT scenarios (optional key)
```

**Important:** FastAPI is the hub. Steps are separate endpoints, not one giant chained script the UI must wait on forever.

---

## Data flow (happy path)

1. User uploads `sales.csv` via Next.js → `POST /upload`
2. User clicks **Process** → `POST /process` runs:
   - `spark_process.py` → `clean_sales.csv`, `product_features.csv`, `warehouse_summary.csv`
   - `build_db.py` → SQLite star schema
   - `cluster.py` → `product_clusters` table + `clusters.png`
3. Dashboard loads KPIs from `GET /sales-summary`, `/warehouse-summary`, `/inventory-summary`, `/cluster-demand`, `/cluster-plot`
4. User picks a scenario → `POST /demand-simulation` (GPT or rule fallback)
5. Report: attach ER/star diagrams + `STRIDE.md`

---

## Dataset (CSV columns)

```
Date, Product_ID, Product_Name, Store_ID, Warehouse_ID,
Sales_Quantity, Stock_Quantity, Price, Revenue
```

Generate with `generate_data.py` → `data/sales.csv`.

---

## Backend APIs (already in `app.py`)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/upload` | API key | Save CSV (max 20 MB) |
| POST | `/process` | API key | Run Spark → DB → K-Means |
| GET | `/sales-summary` | — | Monthly sales / revenue |
| GET | `/warehouse-summary` | — | Units + stock by warehouse |
| GET | `/inventory-summary` | — | Products + demand level |
| GET | `/cluster-demand` | — | Counts Low/Med/High |
| GET | `/cluster-plot` | — | PNG of K-Means chart |
| POST | `/demand-simulation` | API key | GPT / fallback scenarios |

CORS: enable for Next.js (`http://localhost:3000`).

---

## Next.js frontend (to build)

### Pages / sections (one dashboard page is enough)

1. **Upload** — file picker → `POST /upload` with `x-api-key`
2. **Process** — button → `POST /process` (show loading; Spark can take ~30–60s)
3. **KPIs** — Total sales, stock, warehouses, products (from summary endpoints)
4. **Warehouse table** — from `/warehouse-summary`
5. **Demand clustering** — bar/counts from `/cluster-demand` + image from `/cluster-plot`
6. **GPT simulation** — dropdown (Normal / Festival / Low demand / Supply disruption) → show expected units + explanation

### Suggested folder layout

```
frontend/
  app/
    page.tsx          # main dashboard
    layout.tsx
    globals.css
  lib/
    api.ts            # fetch helpers + API_KEY header
  components/
    UploadPanel.tsx
    KpiCards.tsx
    WarehouseTable.tsx
    ClusterSection.tsx
    SimulationPanel.tsx
```

### Env

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=dev-key
```

Keep UI simple — assignment cares about working demos, not polish.

---

## Existing Python pieces (keep / reuse)

| File | Status | Job |
|---|---|---|
| `generate_data.py` | Done | Fake retail CSV |
| `spark_process.py` | Done | PySpark clean + MapReduce + aggs |
| `build_db.py` | Done | SQLite ER + star schema |
| `cluster.py` | Done | K-Means + plot |
| `app.py` | Done | FastAPI orchestrator |
| `queries.sql` | Done | Demo SQL |
| `STRIDE.md` | Done | Threat table |
| `requirements.txt` | Done | Python deps |

Gaps for Next.js:

- [ ] Add CORS middleware in `app.py`
- [ ] Create `frontend/` Next.js app wired to the APIs
- [ ] Optional: ER/star schema diagram images for the report

---

## Build order

| Step | What | Done? |
|---|---|---|
| 1 | Generate dataset | ✅ |
| 2 | PySpark big-data analysis (`spark/` package → `data/processed/`) | ✅ |
| 3 | SQLite + star schema (rebuild on Phase 2 outputs) | ⬜ scaffold only |
| 4 | K-Means clustering (rebuild on product_features) | ⬜ scaffold only |
| 5 | FastAPI endpoints (rebuild + CORS) | ⬜ scaffold only |
| 6 | GPT simulation (+ fallback) | ⬜ scaffold only |
| 7 | STRIDE write-up | ✅ draft |
| 8 | Next.js dashboard | ⬜ |
| 9 | End-to-end demo + screenshots for report | ⬜ |

---

## How to run (target)

```bash
# Backend
pip install -r requirements.txt
python generate_data.py          # once
uvicorn app:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev                      # http://localhost:3000
```

Optional GPT: set `OPENAI_API_KEY` before starting uvicorn.

---

## Marking map (what to show in demo)

| Component | Show |
|---|---|
| Big Data | Spark logs / warehouse MapReduce totals + cleaned CSVs |
| ML | Cluster counts + `clusters.png` on dashboard |
| Data modeling | ER diagram + star schema + SQL queries |
| GPT | Scenario dropdown output (or fallback text if no key) |
| Security | Live APIs + `STRIDE.md` mitigations |
| Integration | Next.js → FastAPI full flow |

---

## Out of scope (on purpose)

- Production auth (OAuth), cloud Spark clusters, real warehouses
- Microservices, Redis, Docker (optional later)
- Fancy multi-page UI

Stay within: **one CSV → Spark → SQL → K-Means → GPT → Next.js dashboard → STRIDE**.
