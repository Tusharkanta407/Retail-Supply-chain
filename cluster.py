"""Thin wrappers so root cluster.py still works for older docs / API process hook."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "clustering" / "demand_clustering.py"), run_name="__main__")
