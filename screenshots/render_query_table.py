"""Render a sample SQL query-results table PNG for the report."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "screenshots" / "query_results" / "Q1_Q1.csv"
OUT = ROOT / "screenshots" / "sql_query_results_Q1.png"


def main() -> None:
    df = pd.read_csv(CSV)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axis("off")
    ax.set_title("SQL Q1 — Units & revenue per warehouse", fontsize=12, pad=8)
    table = ax.table(
        cellText=df.values,
        colLabels=list(df.columns),
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.6)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#1a365d")
            cell.set_text_props(color="white", weight="bold")
        else:
            cell.set_facecolor("#EDF2F7" if r % 2 else "white")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
