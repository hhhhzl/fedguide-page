"""Export the research page's learning curves with legends below the axes.

Run from any working directory with Python, NumPy, and Matplotlib installed:
    python research-page/scripts/export_curves.py
    python research-page/scripts/export_curves.py --envs reacher_hard hopper_hard walker_hard halfcheetah_hard --update-results

The data loading, five-seed aggregation, standard-error bands, and smoothing
are imported from the original plotting code, so this only changes presentation.
Original training outputs and paper figures are not modified.
"""
from __future__ import annotations

import argparse
import json
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

# Load Matplotlib's compiled extensions before installing NumPy 2 pickle aliases
# into a NumPy 1 environment; otherwise some Matplotlib builds import the aliases
# as if they were a native NumPy 2 installation.
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MaxNLocator, StrMethodFormatter  # noqa: E402

# Install the same lightweight Flower History and NumPy pickle compatibility
# stubs used by the existing results-table exporter. No training stack is needed.
from scripts.viz import compute_table_metrics as _history_compat  # noqa: E402,F401
from scripts.viz.compute_fg_family_table import cv_sigma_t  # noqa: E402
from scripts.viz.plot_ablation_hard import ABLATION_ENVS  # noqa: E402
from scripts.viz.plot_posttrain import (  # noqa: E402
    ENV_DISPLAY,
    MAIN_ALGOS,
    MAIN_ENVS,
    aggregate_at,
    smooth,
    smooth_window_for,
)

OUTPUT = SITE_ROOT / "dist/assets/curves"
SEEDS = [0, 1, 2, 3, 4]
HARD_ENVS = {key: (name, root, scale) for key, name, root, scale in ABLATION_ENVS}
ALL_ENVS = [*MAIN_ENVS, *HARD_ENVS]
HARD_DESCRIPTIONS = {
    "reacher_hard": "Stronger heterogeneity in reaching goals, action noise, reward scale and physical dynamics (ablation C).",
    "hopper_hard": "Stronger client variation in mass, damping, friction, actuator strength and reward preferences.",
    "walker_hard": "Stronger client variation in mass, damping, friction, actuator strength and reward preferences.",
    "halfcheetah_hard": "A stronger-heterogeneity locomotion benchmark with the same eight-client experimental protocol.",
}


def environment_config(environment: str) -> tuple[str, Path, str]:
    if environment in HARD_ENVS:
        name, root, scale = HARD_ENVS[environment]
        return name, REPO_ROOT / root, scale
    return ENV_DISPLAY[environment], REPO_ROOT / "metrics" / environment, "linear"


def update_hard_results() -> None:
    """Append the four paper hard benchmarks using its executable metric definitions."""
    destination = SITE_ROOT / "dist/results-data.json"
    data = json.loads(destination.read_text())
    main_environments = [env for env in data["environments"] if env["key"] in MAIN_ENVS]
    for env in main_environments:
        env["suite"] = "main"
    hard_environments = []
    for environment in HARD_ENVS:
        name, root, scale = environment_config(environment)
        metrics, family_cv = {}, {}
        for algorithm, _label, _color in MAIN_ALGOS:
            stack = _history_compat.load_stack(str(root), algorithm)
            if stack is None or stack.shape != (5, 100):
                raise RuntimeError(f"Expected 5 seeds and 100 rounds: {environment}/{algorithm}")
            mean, std, worst_seed = _history_compat.compute(stack)
            metrics[algorithm] = {"mean": mean, "std": std, "worstSeed": worst_seed}
            if algorithm in {"fedguide_a", "fedguide_p", "fedguide"}:
                family_cv[algorithm] = cv_sigma_t(stack)
        best_method = max((key for key, _, _ in MAIN_ALGOS[:4]), key=lambda key: metrics[key]["mean"])
        best_mean = metrics[best_method]["mean"]
        difference = metrics["fedguide"]["mean"] - best_mean
        best_baseline = {"method": best_method, "mean": best_mean, "difference": difference}
        if best_mean > 0:
            best_baseline.update({
                "ratio": metrics["fedguide"]["mean"] / best_mean,
                "percentImprovement": 100 * difference / best_mean,
            })
        env = {
            "key": environment, "name": name, "suite": "hard", "clientCount": 8,
            "description": HARD_DESCRIPTIONS[environment],
            "metrics": metrics, "familyCV": family_cv, "bestExternalBaseline": best_baseline,
            "curve": f"assets/curves/{environment}.png",
            "sourceRoot": str(root.relative_to(REPO_ROOT)),
        }
        if scale == "symlog":
            env["yScale"] = scale
        hard_environments.append(env)
    data["environments"] = main_environments + hard_environments
    metadata = data["metadata"]
    metadata["verification"] = (
        "Recomputed from the existing training_history.pkl files. Rounded values match the paper tables. "
        "All 63 environment-method combinations (five main and four hard benchmarks, seven methods) "
        "have five seeds and 100 common evaluation rounds."
    )
    metadata["curveDefinition"] = (
        "Mean across five seeds with shaded plus/minus one standard error, using trailing-mean smoothing. "
        "Window 5 for all methods, except FedAvg and FedKL use window 1 on Reacher, Hopper, Walker2D "
        "and HalfCheetah, including their hard variants. Reacher-Hard uses a symmetric-logarithmic "
        "return axis with a linear threshold of 10; aggregation is performed before the axis transform."
    )
    metadata["hardSuiteDefinition"] = (
        "Four stronger-heterogeneity benchmarks from the paper's hard ablation: Reacher-Hard "
        "(ablation C), Hopper-Hard, Walker2D-Hard and HalfCheetah-Hard. The experimental protocol "
        "fixes eight clients, five seeds and 100 communication rounds."
    )
    for source in ["scripts/viz/plot_ablation_hard.py", "latex/latex_fedguide/tex/ablation_results.tex"]:
        if source not in metadata["sourceFiles"]:
            metadata["sourceFiles"].append(source)
    destination.write_text(json.dumps(data, indent=2) + "\n")
    print(destination.relative_to(SITE_ROOT))


def export_environment(environment: str, formats: list[str]) -> None:
    """Keep the original curves and reserve two separate rows for their legend."""
    name, root, scale = environment_config(environment)
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
                root,
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

        ax.set_title(name, loc="left", fontsize=12, fontweight="normal", pad=14)
        ax.text(
            1, 1.035, "5 seeds · mean ± 1 SE", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8.5, color="#64748b",
        )
        ax.set_xlabel("Federated round", fontsize=9.5, labelpad=10)
        ax.set_ylabel("Client-average return" + (" (symlog)" if scale == "symlog" else ""), fontsize=9.5, labelpad=10)
        ax.set_xlim(1, 100)
        ax.set_xticks([1, 20, 40, 60, 80, 100])
        if scale == "symlog":
            # Match the paper's hard-ablation plotting code; linear scaling hides
            # the positive-return methods beside the strongly negative baselines.
            ax.set_yscale("symlog", linthresh=10, linscale=1.0)
        else:
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
    parser.add_argument("--envs", nargs="+", choices=ALL_ENVS, default=ALL_ENVS)
    parser.add_argument("--formats", nargs="+", choices=["png", "svg"], default=["png", "svg"])
    parser.add_argument("--update-results", action="store_true", help="Recompute and append hard-suite metrics in results-data.json.")
    args = parser.parse_args()
    for environment in args.envs:
        export_environment(environment, args.formats)
    if args.update_results:
        update_hard_results()


if __name__ == "__main__":
    main()
