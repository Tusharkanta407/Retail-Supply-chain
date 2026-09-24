"""
GPT demand-scenario simulation (with rule-based fallback).
Run:  python ai/demand_scenarios.py
      python ai/demand_scenarios.py --scenario Festival

Grounded in SQLite fact_sales baselines (or Spark KPI JSON fallback).
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "supply_chain.db"
KPI_JSON = ROOT / "data" / "processed" / "dq_report.json"

SCENARIOS = ("Normal", "Festival", "Low demand", "Supply disruption")
MULTIPLIERS = {
    "Normal": 1.05,
    "Festival": 1.4,
    "Low demand": 0.8,
    "Supply disruption": 0.85,
}


def load_baseline() -> dict:
    if DB.exists():
        with sqlite3.connect(DB) as con:
            row = con.execute(
                "SELECT SUM(sales_qty) AS u, SUM(stock_qty) AS s FROM fact_sales"
            ).fetchone()
            if row and row[0] is not None:
                high = con.execute(
                    "SELECT COUNT(*) FROM product_clusters WHERE demand_level='High'"
                ).fetchone()
                return {
                    "baseline_units": int(row[0]),
                    "baseline_stock": int(row[1] or 0),
                    "high_demand_products": int(high[0]) if high else 0,
                    "source_baseline": "sqlite",
                }
    if KPI_JSON.exists():
        kpis = json.loads(KPI_JSON.read_text(encoding="utf-8")).get("kpis", {})
        return {
            "baseline_units": int(kpis.get("total_units", 0)),
            "baseline_stock": 0,
            "high_demand_products": 0,
            "source_baseline": "spark_kpis",
        }
    raise FileNotFoundError("No baseline: run build_db.py (and clustering) first.")


def rule_fallback(scenario: str, baseline: dict) -> dict:
    units = baseline["baseline_units"]
    expected = round(units * MULTIPLIERS[scenario])
    notes = {
        "Normal": "Slight growth vs baseline; maintain current replenishment.",
        "Festival": "Spike in demand; pre-position stock for High-demand products.",
        "Low demand": "Softer sales; reduce inbound to avoid overstock.",
        "Supply disruption": "Constrained availability; protect High-demand SKUs first.",
    }
    return {
        "scenario": scenario,
        "baseline_units": units,
        "baseline_stock": baseline.get("baseline_stock", 0),
        "high_demand_products": baseline.get("high_demand_products", 0),
        "expected_units": expected,
        "risk": "medium" if scenario in {"Festival", "Supply disruption"} else "low",
        "recommendation": notes[scenario],
        "explanation": "Rule-based fallback (no OPENAI_API_KEY or GPT unavailable).",
        "source": "fallback",
        "baseline_from": baseline.get("source_baseline"),
    }


def gpt_simulate(scenario: str, baseline: dict) -> dict:
    from openai import OpenAI

    prompt = (
        f"Retail supply chain simulation. Baseline demand {baseline['baseline_units']} units, "
        f"stock {baseline.get('baseline_stock', 0)} units, "
        f"high-demand products {baseline.get('high_demand_products', 0)}. "
        f"Scenario: '{scenario}'. "
        'Reply ONLY JSON: {"expected_units": int, "risk": str, "recommendation": str}'
    )
    client = OpenAI()
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    payload = json.loads(resp.choices[0].message.content)
    return {
        "scenario": scenario,
        "baseline_units": baseline["baseline_units"],
        "baseline_stock": baseline.get("baseline_stock", 0),
        "high_demand_products": baseline.get("high_demand_products", 0),
        "source": "gpt",
        "baseline_from": baseline.get("source_baseline"),
        **payload,
    }


def simulate(scenario: str = "Normal") -> dict:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Choose from {SCENARIOS}")
    baseline = load_baseline()
    fallback = rule_fallback(scenario, baseline)
    if not os.getenv("OPENAI_API_KEY"):
        return fallback
    try:
        return gpt_simulate(scenario, baseline)
    except Exception as e:
        out = dict(fallback)
        out["explanation"] = f"GPT call failed ({type(e).__name__}); fallback used."
        return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Demand scenario simulation")
    parser.add_argument("--scenario", default="Festival", choices=SCENARIOS)
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    args = parser.parse_args()

    results = [simulate(s) for s in SCENARIOS] if args.all else [simulate(args.scenario)]
    text = json.dumps(results if args.all else results[0], indent=2)
    print(text)

    out_dir = ROOT / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "gpt_demand_scenarios.json"
    out_path.write_text(text, encoding="utf-8")
    print(f"\nSaved {out_path}")


if __name__ == "__main__":
    main()
