"""Generate ER and star-schema PNGs for the submission diagrams/ folder."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "diagrams"
SHOT = ROOT / "screenshots"


def _box(ax, xy, w, h, text, fc="#E8F1F8"):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.5,
        edgecolor="#1a365d",
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=8.5,
        fontfamily="monospace",
        color="#1a202c",
    )


def _arrow(ax, start, end):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.2,
            color="#2d3748",
        )
    )


def er_diagram(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    ax.axis("off")
    ax.set_title("ER Diagram — Retail Supply Chain", fontsize=14, pad=12)

    _box(ax, (0.5, 5.2), 2.6, 1.6, "dim_warehouse\n─────────────\nPK warehouse_id", "#D6EAF8")
    _box(ax, (4.2, 5.2), 2.8, 1.6, "dim_store\n─────────────\nPK store_id\nFK warehouse_id", "#D5F5E3")
    _box(ax, (8.0, 5.2), 2.6, 1.6, "dim_product\n─────────────\nPK product_id\nproduct_name\nprice", "#FCF3CF")
    _box(ax, (0.5, 0.6), 2.8, 1.8, "dim_date\n─────────────\nPK date_id\nfull_date\nyear month day\nweekday", "#FADBD8")
    _box(
        ax,
        (4.0, 2.4),
        3.4,
        2.2,
        "fact_sales\n─────────────\nPK sale_id\nFK date_id\nFK product_id\nFK store_id\nFK warehouse_id\nsales_qty stock_qty\nrevenue",
        "#E8DAEF",
    )
    _box(
        ax,
        (8.0, 0.6),
        2.6,
        1.8,
        "product_clusters\n─────────────\nproduct_id\ndemand_level\navg_daily_sales\navg_stock\nrevenue",
        "#D5F5E3",
    )

    _arrow(ax, (3.1, 5.8), (4.2, 5.8))  # warehouse -> store
    _arrow(ax, (5.5, 5.2), (5.5, 4.6))  # store -> fact
    _arrow(ax, (8.0, 5.5), (7.4, 4.0))  # product -> fact
    _arrow(ax, (2.0, 2.4), (4.0, 3.2))  # date -> fact
    _arrow(ax, (4.5, 5.2), (5.2, 4.6))  # warehouse via store area
    ax.annotate(
        "1:N",
        xy=(3.5, 6.1),
        fontsize=8,
        color="#4a5568",
    )
    ax.annotate("product_id links\nclusters to dim_product", xy=(8.2, 2.6), fontsize=7, color="#4a5568")

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {path}")


def star_schema(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("Star Schema — Fact_Sales", fontsize=14, pad=12)

    # Center fact
    _box(
        ax,
        (3.3, 3.2),
        3.4,
        2.0,
        "FACT_SALES\n─────────────\nsale_id (PK)\ndate_id (FK)\nproduct_id (FK)\nstore_id (FK)\nwarehouse_id (FK)\nsales_qty\nstock_qty\nrevenue",
        "#E8DAEF",
    )
    # Surrounding dims
    _box(ax, (3.5, 6.2), 3.0, 1.3, "DIM_DATE\ndate_id PK\nyear month day", "#FADBD8")
    _box(ax, (0.3, 3.4), 2.6, 1.4, "DIM_PRODUCT\nproduct_id PK\nname price", "#FCF3CF")
    _box(ax, (7.2, 3.4), 2.6, 1.4, "DIM_STORE\nstore_id PK\nwarehouse_id FK", "#D5F5E3")
    _box(ax, (3.5, 0.5), 3.0, 1.3, "DIM_WAREHOUSE\nwarehouse_id PK", "#D6EAF8")

    _arrow(ax, (5.0, 6.2), (5.0, 5.2))
    _arrow(ax, (2.9, 4.1), (3.3, 4.1))
    _arrow(ax, (7.2, 4.1), (6.7, 4.1))
    _arrow(ax, (5.0, 3.2), (5.0, 1.8))

    ax.text(
        5.0,
        7.7,
        "Classic star: dimensions surround a single grain fact (one sale line)",
        ha="center",
        fontsize=9,
        color="#4a5568",
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {path}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SHOT.mkdir(parents=True, exist_ok=True)
    er = OUT / "er_diagram.png"
    star = OUT / "star_schema.png"
    er_diagram(er)
    star_schema(star)
    # Copy into screenshots evidence pack
    import shutil

    shutil.copy(er, SHOT / "schema_er_diagram.png")
    shutil.copy(star, SHOT / "schema_star_diagram.png")
    print(f"copied diagrams -> {SHOT}")


if __name__ == "__main__":
    main()
