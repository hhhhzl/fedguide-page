"""Export the research page's learning curves with legends below the axes.

Run from any working directory with Python, NumPy, and Matplotlib installed:
    python research-page/scripts/export_curves.py

The data loading, five-seed aggregation, standard-error bands, and smoothing
are imported from the original plotting code, so this only changes presentation.
Original training outputs and paper figures are not modified.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile

SITE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(os.environ.get("FEDGUIDE_SOURCE_ROOT", SITE_ROOT.parent)).resolve()
if not (REPO_ROOT / "scripts/viz/plot_posttrain.py").is_file():
    raise SystemExit("Set FEDGUIDE_SOURCE_ROOT to the original FedGuide research checkout containing scripts/viz and metrics.")
sys.path.insert(0, str(REPO_ROOT))
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "fedguide-web-mpl"))

# Install the same lightweight Flower History and NumPy pickle compatibility
# stubs used by the existing results-table exporter. No training stack is needed.
from scripts.viz import compute_table_metrics as _history_compat  # noqa: E402,F401
from scripts.viz.plot_posttrain import (  # noqa: E402
    ENV_DISPLAY,
    MAIN_ALGOS,
    MAIN_ENVS,
    aggregate_at,
    smooth,
    smooth_window_for,
)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MaxNLocator, StrMethodFormatter  # noqa: E402

OUTPUT = SITE_ROOT / "dist/assets/curves"
SEEDS = [0, 1, 2, 3, 4]


def export_environment(environment: str, formats: list[str]) -> None:
    """Keep the original curves and reserve two separate rows for their legend."""
    with plt.rc_context({
        "font.family": "DejaVu Sans",
        "font.size": 9.5,
        "text.color": "#34435a",
        "axes.labelcolor": "#526279",
        "axes.edgecolor": "#b6c1cf",
        "axes.linewidth": 0.8,
        "xtick.color": "#64748b",
        "ytick.color": "#64748b",
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
        "savefig.bbox": None,
    }):
        fig, ax = plt.subplots(figsize=(8, 5), dpi=180)
        fig.subplots_adjust(left=0.12, right=0.975, bottom=0.27, top=0.88)
        handles = []
        for algorithm, label, color in MAIN_ALGOS:
            aggregate = aggregate_at(
                REPO_ROOT / "metrics" / environment,
                algorithm,
                SEEDS,
                "metrics_distributed_fit",
                "eval/return",
            )
            if aggregate is None:
                raise RuntimeError(f"Missing results for {environment}/{algorithm}")
            rounds, mean, standard_error, seed_count = aggregate
            if seed_count != 5 or len(rounds) != 100:
                raise RuntimeError(
                    f"Expected 5 seeds and 100 rounds for {environment}/{algorithm}; "
                    f"found {seed_count} seeds and {len(rounds)} rounds"
                )
            window = smooth_window_for(environment, algorithm)
            plotted_mean, indices = smooth(mean, window)
            plotted_error, _ = smooth(standard_error, window)
            x = rounds[indices]
            ax.fill_between(
                x, plotted_mean - plotted_error, plotted_mean + plotted_error,
                color=color, alpha=0.18, linewidth=0, zorder=1,
            )
            line, = ax.plot(
                x, plotted_mean, color=color,
                linewidth=2.1 if algorithm == "fedguide" else 1.7,
                label=label, solid_capstyle="round", zorder=2,
            )
            handles.append(line)

        ax.set_title(ENV_DISPLAY[environment], loc="left", fontsize=12, fontweight="normal", pad=14)
        ax.text(
            1, 1.035, "5 seeds · mean ± 1 SE", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8.5, color="#64748b",
        )
        ax.set_xlabel("Federated round", fontsize=9.5, labelpad=10)
        ax.set_ylabel("Client-average return", fontsize=9.5, labelpad=10)
        ax.set_xlim(1, 100)
        ax.set_xticks([1, 20, 40, 60, 80, 100])
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.margins(y=0.08)
        ax.grid(axis="y", color="#e8edf3", linewidth=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", length=3, width=0.7, pad=5)
        ax.spines[["top", "right"]].set_visible(False)

        # Separate baseline and FedGuide-family rows retain the original method
        # order. Figure-coordinate legends never occupy any data coordinates.
        legends = []
        for row_handles, vertical_position in [(handles[:4], 0.125), (handles[4:], 0.066)]:
            legends.append(fig.legend(
                row_handles, [line.get_label() for line in row_handles],
                loc="center", bbox_to_anchor=(0.54, vertical_position),
                bbox_transform=fig.transFigure,
                ncol=len(row_handles), frameon=False, fontsize=9.2,
                handlelength=2.2, handletextpad=0.65, columnspacing=1.7,
                borderaxespad=0,
            ))

        # Check rendered bounding boxes, including ticks and axis labels, before
        # writing. These checks catch future font/layout changes that cause overlap.
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        axes_bounds = ax.get_tightbbox(renderer)
        legend_bounds = [legend.get_window_extent(renderer) for legend in legends]
        for bounds in legend_bounds:
            if bounds.overlaps(axes_bounds):
                raise RuntimeError(f"Legend overlaps chart or axis labels: {environment}")
            if not (fig.bbox.contains(bounds.x0, bounds.y0) and fig.bbox.contains(bounds.x1, bounds.y1)):
                raise RuntimeError(f"Legend is clipped by image edge: {environment}")
        if legend_bounds[0].overlaps(legend_bounds[1]):
            raise RuntimeError(f"Legend rows overlap: {environment}")

        OUTPUT.mkdir(parents=True, exist_ok=True)
        for extension in formats:
            target = OUTPUT / f"{environment}.{extension}"
            fig.savefig(target, dpi=180, metadata={"Creator": "FedGuide research-page/scripts/export_curves.py"})
            if extension == "svg":
                target.write_text("\n".join(line.rstrip() for line in target.read_text().splitlines()) + "\n")
            print(target.relative_to(SITE_ROOT))
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--envs", nargs="+", choices=MAIN_ENVS, default=MAIN_ENVS)
    parser.add_argument("--formats", nargs="+", choices=["png", "svg"], default=["png", "svg"])
    args = parser.parse_args()
    for environment in args.envs:
        export_environment(environment, args.formats)


if __name__ == "__main__":
    main()
