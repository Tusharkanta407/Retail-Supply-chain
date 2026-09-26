"""
Thin Supply Chain API for analytics + GPT scenarios + STRIDE evidence.
Run:  uvicorn app:app --reload --port 8000
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "supply_chain.db"
FRONTEND = ROOT / "frontend"
API_KEY = os.getenv("API_KEY", "dev-key")
MAX_UPLOAD = 20 * 1024 * 1024

app = FastAPI(title="Retail Supply Chain Optimizer", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


def auth(key: str) -> None:
    if key != API_KEY:
        raise HTTPException(401, "Invalid API key")


def q(sql: str):
    if not DB.exists():
        raise HTTPException(503, "Database missing. Run build_db.py first.")
    with sqlite3.connect(DB) as c:
        return pd.read_sql(sql, c).to_dict("records")


@app.get("/")
def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and FRONTEND.exists():
        return FileResponse(FRONTEND / "index.html")
    return {
        "service": "Retail Supply Chain Optimizer",
        "version": "1.0.0",
        "dashboard": "/dashboard",
        "endpoints": [
            "GET /dashboard",
            "POST /upload",
            "POST /process",
            "GET /sales-summary",
            "GET /warehouse-summary",
            "GET /inventory-summary",
            "GET /cluster-demand",
            "GET /cluster-plot",
            "POST /demand-simulation",
            "GET /stride",
        ],
    }


@app.get("/dashboard", response_class=FileResponse)
def dashboard():
    if not (FRONTEND / "index.html").exists():
        raise HTTPException(404, "Dashboard frontend not found")
    return FileResponse(FRONTEND / "index.html")


@app.get("/stride")
def stride():
    return {
        "matrix": [
            {
                "endpoint": "POST /upload",
                "spoofing": "Fake client uploads data",
                "tampering": "Malicious/poisoned CSV alters sales data",
                "repudiation": "User denies uploading",
                "info_disclosure": "Uploaded file exposed on disk",
                "dos": "Huge files exhaust disk/memory",
                "privilege": "Upload path abuse to overwrite files",
                "mitigations": "API Key auth, .csv extension check, 20 MB max upload cap"
            },
            {
                "endpoint": "POST /process",
                "spoofing": "Unauthorised pipeline trigger",
                "tampering": "Process step scripts modified",
                "repudiation": "No durable audit of who ran it",
                "info_disclosure": "Stack traces leak internals",
                "dos": "Repeated Spark runs overload CPU/RAM",
                "privilege": "Caller triggers privileged batch jobs",
                "mitigations": "API Key auth, fixed script whitelist, subprocess isolation"
            },
            {
                "endpoint": "GET /*-summary",
                "spoofing": "Impersonating a partner",
                "tampering": "Response manipulated in transit",
                "repudiation": "—",
                "info_disclosure": "Competitors read stock/demand levels",
                "dos": "Request flooding",
                "privilege": "Read APIs used to recon before write abuse",
                "mitigations": "Read-only parameterized SQL, HTTPS recommended, future RBAC"
            },
            {
                "endpoint": "GET /cluster-plot",
                "spoofing": "Unauthorized caller",
                "tampering": "Image swapped / MITM",
                "repudiation": "—",
                "info_disclosure": "Cluster strategy visible to rivals",
                "dos": "Bandwidth abuse",
                "privilege": "—",
                "mitigations": "Direct static FileResponse, cache headers"
            },
            {
                "endpoint": "POST /demand-simulation",
                "spoofing": "Stolen API key",
                "tampering": "Prompt injection alters GPT output",
                "repudiation": "No log of simulations",
                "info_disclosure": "Business baselines sent to GPT",
                "dos": "Cost/rate abuse of GPT calls",
                "privilege": "Unlisted scenarios / privilege via prompts",
                "mitigations": "API Key auth, strict scenario whitelist, offline rule fallback"
            }
        ]
    }


@app.post("/upload")
async def upload(file: UploadFile = File(...), x_api_key: str = Header("")):
    auth(x_api_key)
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(400, "CSV only")
    content = await file.read()
    if len(content) > MAX_UPLOAD:
        raise HTTPException(413, "File too large (max 20 MB)")
    dest = ROOT / "data" / "sales.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return {"status": "uploaded", "bytes": len(content)}


@app.post("/process")
def process(x_api_key: str = Header("")):
    """Run PySpark → star schema load → K-Means clustering."""
    auth(x_api_key)
    steps = [
        ["spark_process.py"],
        ["build_db.py"],
        ["clustering/demand_clustering.py"],
    ]
    for args in steps:
        r = subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if r.returncode:
            raise HTTPException(500, f"{args[0]} failed: {(r.stderr or r.stdout)[-400:]}")
    return {"status": "processed"}


@app.get("/sales-summary")
def sales():
    return q(
        "SELECT d.year, d.month, SUM(sales_qty) units, ROUND(SUM(revenue),2) revenue "
        "FROM fact_sales f JOIN dim_date d USING(date_id) GROUP BY 1,2 ORDER BY 1,2"
    )


@app.get("/warehouse-summary")
def warehouses():
    return q(
        "SELECT warehouse_id, SUM(sales_qty) units_sold, ROUND(AVG(stock_qty),1) avg_stock, "
        "ROUND(SUM(revenue),2) revenue FROM fact_sales GROUP BY 1 ORDER BY 1"
    )


@app.get("/inventory-summary")
def inventory():
    return q(
        "SELECT product_id, demand_level, avg_daily_sales, avg_stock "
        "FROM product_clusters ORDER BY avg_daily_sales DESC LIMIT 50"
    )


@app.get("/cluster-demand")
def clusters():
    return q(
        "SELECT demand_level, COUNT(*) products FROM product_clusters "
        "GROUP BY 1 ORDER BY CASE demand_level WHEN 'Low' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END"
    )


@app.get("/cluster-plot")
def plot():
    path = ROOT / "data" / "clusters.png"
    if not path.exists():
        raise HTTPException(404, "clusters.png missing — run clustering first")
    return FileResponse(path)


class Sim(BaseModel):
    scenario: str = "Normal"


@app.post("/demand-simulation")
def simulate(body: Sim, x_api_key: str = Header("")):
    auth(x_api_key)
    # Reuse AI module so CLI and API share one implementation
    sys.path.insert(0, str(ROOT))
    from ai.demand_scenarios import SCENARIOS, simulate as run_sim

    if body.scenario not in SCENARIOS:
        raise HTTPException(400, f"Unknown scenario. Choose from {list(SCENARIOS)}")
    return run_sim(body.scenario)
