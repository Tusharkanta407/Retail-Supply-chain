"""Render STRIDE.md table as a PNG for the screenshots pack."""
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "screenshots" / "stride_table.png"


def main() -> None:
    headers = ["Endpoint", "S", "T", "R", "I", "D", "E"]
    rows = [
        ["POST /upload", "Fake client", "Poisoned CSV", "Deny upload", "File exposed", "Huge files", "Path abuse"],
        ["POST /process", "Unauth trigger", "Scripts changed", "No audit", "Stack traces", "Spark overload", "Batch privilege"],
        ["GET summaries", "Impersonate", "MITM response", "—", "Stock leaked", "Flooding", "Recon"],
        ["POST /demand-sim", "Stolen key", "Prompt inject", "No log", "Data to GPT", "Cost abuse", "Scenario bypass"],
    ]
    fig, ax = plt.subplots(figsize=(14, 4.5))
    ax.axis("off")
    ax.set_title("STRIDE — Supply Chain API Threat Summary", fontsize=13, pad=10)
    table = ax.table(
        cellText=rows,
        colLabels=headers,
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.2, 2.0)
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
