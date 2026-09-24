"""Step 5: FastAPI backend / orchestrator.   Run: uvicorn app:app --reload"""
import json, os, sqlite3, subprocess, sys
import pandas as pd
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Retail Supply Chain Optimizer")
API_KEY = os.getenv("API_KEY", "dev-key")          # simple auth (see STRIDE mitigations)
MAX_UPLOAD = 20 * 1024 * 1024

def auth(key): 
    if key != API_KEY: raise HTTPException(401, "Invalid API key")
def q(sql):
    with sqlite3.connect("data/supply_chain.db") as c: return pd.read_sql(sql, c).to_dict("records")

@app.post("/upload")
async def upload(file: UploadFile = File(...), x_api_key: str = Header("")):
    auth(x_api_key)
    if not file.filename.endswith(".csv"): raise HTTPException(400, "CSV only")
    content = await file.read()
    if len(content) > MAX_UPLOAD: raise HTTPException(413, "File too large")
    open("data/sales.csv", "wb").write(content); return {"status": "uploaded", "bytes": len(content)}

@app.post("/process")
def process(x_api_key: str = Header("")):
    auth(x_api_key)
    for s in ["spark_process.py", "build_db.py", "cluster.py"]:
        r = subprocess.run([sys.executable, s], capture_output=True, text=True)
        if r.returncode: raise HTTPException(500, f"{s} failed: {r.stderr[-300:]}")
    return {"status": "processed"}

@app.get("/sales-summary")
def sales(): return q("SELECT d.year, d.month, SUM(sales_qty) units, ROUND(SUM(revenue),2) revenue FROM fact_sales f JOIN dim_date d USING(date_id) GROUP BY 1,2")
@app.get("/warehouse-summary")
def warehouses(): return q("SELECT warehouse_id, SUM(sales_qty) units_sold, ROUND(AVG(stock_qty),1) avg_stock FROM fact_sales GROUP BY 1")
@app.get("/inventory-summary")
def inventory(): return q("SELECT product_id, demand_level, avg_daily_sales, avg_stock FROM product_clusters ORDER BY avg_daily_sales DESC LIMIT 50")
@app.get("/cluster-demand")
def clusters(): return q("SELECT demand_level, COUNT(*) products FROM product_clusters GROUP BY 1")
@app.get("/cluster-plot")
def plot(): return FileResponse("data/clusters.png")

class Sim(BaseModel):
    scenario: str = "Normal"   # Normal | Festival | Low demand | Supply disruption

@app.post("/demand-simulation")
def simulate(body: Sim, x_api_key: str = Header("")):
    auth(x_api_key)
    if body.scenario not in {"Normal", "Festival", "Low demand", "Supply disruption"}: raise HTTPException(400, "Unknown scenario")
    base = q("SELECT SUM(sales_qty) u, SUM(stock_qty) s FROM fact_sales")[0]
    mult = {"Normal": 1.05, "Festival": 1.4, "Low demand": 0.8, "Supply disruption": 0.85}[body.scenario]
    fallback = {"scenario": body.scenario, "baseline_units": base["u"], "expected_units": round(base["u"] * mult),
                "explanation": "Rule-based fallback (no OPENAI_API_KEY set).", "source": "fallback"}
    if not os.getenv("OPENAI_API_KEY"): return fallback
    try:
        from openai import OpenAI
        prompt = (f"Retail supply chain. Baseline demand {base['u']} units, stock {base['s']} units. Simulate scenario '{body.scenario}'. "
                  'Reply ONLY JSON: {"expected_units": int, "risk": str, "recommendation": str}')
        r = OpenAI().chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
              messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return {"scenario": body.scenario, "baseline_units": base["u"], "source": "gpt", **json.loads(r.choices[0].message.content)}
    except Exception as e:
        return {**fallback, "explanation": f"GPT call failed ({type(e).__name__}); fallback used."}
