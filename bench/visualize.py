"""
Generate publication-quality comparison charts from benchmark results.

Usage:
    python bench/visualize.py                         # all charts
    python bench/visualize.py --charts timing ram      # specific charts
    python bench/visualize.py --format pdf png         # both formats
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from utils import get_project_root, load_config, load_json, results_path

JAVA_COLOR = "#E24A33"
RUST_COLOR = "#348ABD"

SCENARIO_LABELS = {
    "scenario1": "CPU\nMandelbrot",
    "scenario2": "I/O\nCSV Processing",
    "scenario3": "Concurrency\nParticle Sim",
    "scenario4": "Memory\nIoT Streaming",
}


def setup_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.figsize": (6.5, 4.0),
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def chart_dir(config, scenario_id):
    d = results_path(config, "charts", scenario_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_chart(fig, path, formats):
    for fmt in formats:
        out = Path(str(path).rsplit(".", 1)[0] + f".{fmt}")
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out)
        print(f"  Saved: {out}")
    plt.close(fig)


POSTER_EXEC_ORDER = ["scenario1", "scenario2", "scenario4"]
POSTER_EXEC_LABELS = {
    "scenario1": "a) CPU",
    "scenario2": "b) I/O operations",
    "scenario4": "c) IoT Streaming",
}


def chart_execution_time(config, formats):
    path = results_path(config, "parsed", "timing.json")
    if not path.exists():
        print("  Skipping execution time chart (no timing data)")
        return

    timing = load_json(path)
    scenarios = [s for s in POSTER_EXEC_ORDER if s in timing]
    if not scenarios:
        print("  Skipping execution time chart (no poster scenarios in timing data)")
        return

    width = 0.35
    x = np.arange(len(scenarios))
    java_means = [timing[s]["java"]["mean"] for s in scenarios]
    java_stds = [timing[s]["java"]["stddev"] for s in scenarios]
    rust_means = [timing[s]["rust"]["mean"] for s in scenarios]
    rust_stds = [timing[s]["rust"]["stddev"] for s in scenarios]

    fig, ax = plt.subplots(figsize=(11, 5.0))

    bars_j = ax.bar(x - width / 2, java_means, width, yerr=java_stds,
                    label="Java 25", color=JAVA_COLOR, capsize=4,
                    edgecolor="black", linewidth=0.5)
    bars_r = ax.bar(x + width / 2, rust_means, width, yerr=rust_stds,
                    label="Rust", color=RUST_COLOR, capsize=4,
                    edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Execution Time (s)")
    ax.set_xticks(x)
    ax.set_xticklabels([POSTER_EXEC_LABELS[s] for s in scenarios])
    ax.legend()

    for bar in list(bars_j) + list(bars_r):
        h = bar.get_height()
        ax.annotate(f"{h:.2f}s",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=8)

    save_chart(fig, results_path(config, "charts", "execution_time.pdf"), formats)


def chart_peak_ram(config, formats):
    path = results_path(config, "parsed", "resources.json")
    if not path.exists():
        print("  Skipping peak RAM chart (no resource data)")
        return

    resources = load_json(path)
    width = 0.35

    for scenario_id, data in resources.items():
        x = np.arange(1)
        j = data.get("java", {}).get("memory", {})
        r = data.get("rust", {}).get("memory", {})
        java_peak = j.get("peak_rss_bytes_mean", 0) / (1024 ** 2)
        rust_peak = r.get("peak_rss_bytes_mean", 0) / (1024 ** 2)

        fig, ax = plt.subplots(figsize=(4.0, 4.5))

        bars_j = ax.bar(x - width / 2, [java_peak], width,
                        label="Java 25", color=JAVA_COLOR,
                        edgecolor="black", linewidth=0.5)
        bars_r = ax.bar(x + width / 2, [rust_peak], width,
                        label="Rust", color=RUST_COLOR,
                        edgecolor="black", linewidth=0.5)

        label = SCENARIO_LABELS.get(scenario_id, scenario_id).replace("\n", " - ")
        ax.set_ylabel("Peak RSS (MB)")
        ax.set_title(f"Peak Memory Usage: {label}")
        ax.set_xticks(x)
        ax.set_xticklabels([label])
        ax.legend()

        for bar in list(bars_j) + list(bars_r):
            h = bar.get_height()
            ax.annotate(f"{h:.0f} MB",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", fontsize=8)

        save_chart(fig, chart_dir(config, scenario_id) / "peak_ram.pdf", formats)


def chart_ram_over_time(config, formats):
    path = results_path(config, "parsed", "resources.json")
    if not path.exists():
        print("  Skipping RAM-over-time charts (no resource data)")
        return

    resources = load_json(path)
    scenarios = [s for s in POSTER_EXEC_ORDER if s in resources]
    if not scenarios:
        print("  Skipping RAM-over-time chart (no poster scenarios in resource data)")
        return

    fig, axes = plt.subplots(
        nrows=len(scenarios), ncols=1,
        figsize=(17.5, 2.7 * len(scenarios)),
    )
    if len(scenarios) == 1:
        axes = [axes]

    java_handle = None
    rust_handle = None

    for ax, scenario_id in zip(axes, scenarios):
        data = resources[scenario_id]
        java_data = data.get("java", {})
        rust_data = data.get("rust", {})

        java_all = java_data.get("all_run_timeseries") or (
            [java_data["median_run_timeseries"]] if java_data.get("median_run_timeseries") else []
        )
        rust_all = rust_data.get("all_run_timeseries") or (
            [rust_data["median_run_timeseries"]] if rust_data.get("median_run_timeseries") else []
        )
        java_median = java_data.get("median_run_timeseries", [])
        rust_median = rust_data.get("median_run_timeseries", [])

        for ts in java_all:
            ax.plot(
                [s["timestamp_ms"] / 1000 for s in ts],
                [s["rss_bytes"] / (1024 ** 2) for s in ts],
                color=JAVA_COLOR, alpha=0.4, linewidth=0.8,
            )
        if java_median:
            line, = ax.plot(
                [s["timestamp_ms"] / 1000 for s in java_median],
                [s["rss_bytes"] / (1024 ** 2) for s in java_median],
                color=JAVA_COLOR, alpha=1.0, linewidth=2, label="Java 25",
            )
            if java_handle is None:
                java_handle = line

        for ts in rust_all:
            ax.plot(
                [s["timestamp_ms"] / 1000 for s in ts],
                [s["rss_bytes"] / (1024 ** 2) for s in ts],
                color=RUST_COLOR, alpha=0.4, linewidth=0.8,
            )
        if rust_median:
            line, = ax.plot(
                [s["timestamp_ms"] / 1000 for s in rust_median],
                [s["rss_bytes"] / (1024 ** 2) for s in rust_median],
                color=RUST_COLOR, alpha=1.0, linewidth=2, label="Rust",
            )
            if rust_handle is None:
                rust_handle = line

        ax.set_title(POSTER_EXEC_LABELS.get(scenario_id, scenario_id), loc="left", fontsize=11)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("RSS Memory (MB)")

    handles = [h for h in [java_handle, rust_handle] if h is not None]
    if handles:
        fig.legend(
            handles=handles,
            loc="upper right",
            bbox_to_anchor=(1.0, 1.0),
            ncol=len(handles),
        )

    fig.tight_layout(rect=[0, 0, 1, 0.97])
    save_chart(fig, results_path(config, "charts", "ram_over_time.pdf"), formats)


def chart_gc_histogram(config, formats):
    parsed_dir = results_path(config, "parsed")
    gc_files = list(parsed_dir.glob("gc_pauses_*.json"))

    if not gc_files:
        print("  Skipping GC histogram (no GC data)")
        return

    for gc_file in gc_files:
        gc_data = load_json(gc_file)
        scenario_id = gc_file.stem.replace("gc_pauses_", "")

        if not gc_data["pauses"]:
            continue

        fig, ax = plt.subplots(figsize=(14.3, 2.7))

        type_colors = {
            "Young": "#4CAF50",
            "Mixed": "#FFC107",
            "Full": "#F44336",
            "Old": "#9C27B0",
        }

        all_durations = [p["pause_duration_ms"] for p in gc_data["pauses"]]

        for pause_type, color in type_colors.items():
            durations = [p["pause_duration_ms"] for p in gc_data["pauses"]
                         if p["pause_type"] == pause_type]
            if durations:
                ax.hist(durations, bins=min(50, max(10, len(durations) // 2)),
                        alpha=0.7, label=f"{pause_type} ({len(durations)})",
                        color=color, edgecolor="black", linewidth=0.3)

        summary = gc_data["summary"]
        ax.axvline(summary["mean_pause_ms"], color="black", linestyle="--",
                   label=f"Mean ({summary['mean_pause_ms']:.2f} ms)")
        ax.axvline(summary["p99_pause_ms"], color="red", linestyle=":",
                   label=f"P99 ({summary['p99_pause_ms']:.2f} ms)")

        ax.set_xlabel("Pause Duration (ms)")
        ax.set_ylabel("Count")
        ax.legend()

        poster_label = POSTER_EXEC_LABELS.get(scenario_id)
        if poster_label:
            ax.text(0.0, -0.1, poster_label, transform=ax.transAxes,
                    fontsize=10, va="top", ha="left", style="italic", clip_on=False)

        save_chart(fig, chart_dir(config, scenario_id) / "gc_pause_histogram.pdf", formats)


def chart_gc_timeline(config, formats):
    parsed_dir = results_path(config, "parsed")
    gc_files = list(parsed_dir.glob("gc_pauses_*.json"))

    if not gc_files:
        print("  Skipping GC timeline (no GC data)")
        return

    for gc_file in gc_files:
        gc_data = load_json(gc_file)
        scenario_id = gc_file.stem.replace("gc_pauses_", "")

        if not gc_data["pauses"]:
            continue

        fig, ax = plt.subplots(figsize=(10, 4))

        type_colors = {
            "Young": "#4CAF50",
            "Mixed": "#FFC107",
            "Full": "#F44336",
            "Old": "#9C27B0",
        }

        for pause_type, color in type_colors.items():
            pts = [(p["timestamp_s"], p["pause_duration_ms"])
                   for p in gc_data["pauses"] if p["pause_type"] == pause_type]
            if pts:
                xs, ys = zip(*pts)
                ax.scatter(xs, ys, c=color, label=pause_type, s=15, alpha=0.7, edgecolors="none")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Pause Duration (ms)")
        label = SCENARIO_LABELS.get(scenario_id, scenario_id).replace("\n", " - ")
        ax.set_title(f"GC Pause Events Over Time: {label}")
        ax.legend()

        save_chart(fig, chart_dir(config, scenario_id) / "gc_pause_timeline.pdf", formats)


def chart_binary_size(config, formats):
    path = results_path(config, "raw", "binary_sizes.json")
    if not path.exists():
        print("  Skipping binary size chart (no build data)")
        return

    sizes = load_json(path)
    if not sizes:
        print("  Skipping binary size chart (empty file)")
        return

    width = 0.35

    for scenario_id, scenario_sizes in sizes.items():
        if not isinstance(scenario_sizes, dict):
            continue
        x = np.arange(1)
        java_kb = scenario_sizes.get("java_jar_bytes", 0) / 1024
        rust_kb = scenario_sizes.get("rust_exe_bytes", 0) / 1024

        fig, ax = plt.subplots(figsize=(4.0, 4.5))

        bars_j = ax.bar(x - width / 2, [java_kb], width, label="Java JAR",
                        color=JAVA_COLOR, edgecolor="black", linewidth=0.5)
        bars_r = ax.bar(x + width / 2, [rust_kb], width, label="Rust EXE",
                        color=RUST_COLOR, edgecolor="black", linewidth=0.5)

        label = SCENARIO_LABELS.get(scenario_id, scenario_id).replace("\n", " - ")
        ax.set_ylabel("Size (KB)")
        ax.set_title(f"Binary Size: {label}")
        ax.set_xticks(x)
        ax.set_xticklabels([label])
        ax.legend()

        for bar in list(bars_j) + list(bars_r):
            h = bar.get_height()
            unit = "KB" if h < 1024 else "MB"
            val = h if h < 1024 else h / 1024
            ax.annotate(f"{val:.1f} {unit}",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", fontsize=9)

        save_chart(fig, chart_dir(config, scenario_id) / "binary_size.pdf", formats)


def chart_latency_distribution(config, formats):
    parsed_dir = results_path(config, "parsed")
    latency_files = list(parsed_dir.glob("latency_*.json"))

    if not latency_files:
        print("  Skipping latency chart (no latency data)")
        return

    for path in latency_files:
        data = load_json(path)
        scenario_id = path.stem.replace("latency_", "")
        java = data.get("java")
        rust = data.get("rust")
        if not (java or rust):
            continue

        label = SCENARIO_LABELS.get(scenario_id, scenario_id).replace("\n", " - ")

        # --- (1) percentile comparison ---
        percentiles = ["p50_ns", "p95_ns", "p99_ns", "p999_ns", "max_ns"]
        percentile_labels = ["p50", "p95", "p99", "p99.9", "max"]
        x = np.arange(len(percentiles))
        width = 0.35

        java_vals = [(java or {}).get(p, 0) / 1000.0 for p in percentiles]
        rust_vals = [(rust or {}).get(p, 0) / 1000.0 for p in percentiles]

        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.bar(x - width / 2, java_vals, width, label="Java 25",
               color=JAVA_COLOR, edgecolor="black", linewidth=0.5)
        ax.bar(x + width / 2, rust_vals, width, label="Rust",
               color=RUST_COLOR, edgecolor="black", linewidth=0.5)
        ax.set_yscale("log")
        ax.set_ylabel("Per-event latency (µs, log scale)")
        ax.set_xlabel("Percentile")
        ax.set_xticks(x)
        ax.set_xticklabels(percentile_labels)
        ax.set_title(f"Per-event Latency Percentiles: {label}")
        ax.legend()
        save_chart(fig, chart_dir(config, scenario_id) / "latency_percentiles.pdf", formats)

        # --- (2) bucket histogram overlay ---
        fig, ax = plt.subplots(figsize=(8, 4.5))
        plotted_any = False
        for side, color, label_lang in [(java, JAVA_COLOR, "Java 25"), (rust, RUST_COLOR, "Rust")]:
            if not side:
                continue
            buckets = side.get("buckets") or []
            lowers_ns = side.get("bucket_lower_ns") or []
            if not buckets or not lowers_ns:
                continue
            lowers_us = [max(b, 1) / 1000.0 for b in lowers_ns]
            ax.step(lowers_us, buckets, where="post",
                    color=color, label=label_lang, linewidth=1.5, alpha=0.85)
            plotted_any = True

        if plotted_any:
            ax.set_xscale("log")
            ax.set_yscale("symlog", linthresh=1)
            ax.set_xlabel("Per-event latency bucket lower bound (µs, log scale)")
            ax.set_ylabel("Events in bucket")
            ax.set_title(f"Per-event Latency Distribution: {label}")
            ax.legend()
            save_chart(fig, chart_dir(config, scenario_id) / "latency_distribution.pdf", formats)
        else:
            plt.close(fig)


CHART_FUNCTIONS = {
    "timing": chart_execution_time,
    "ram": chart_peak_ram,
    "ram_time": chart_ram_over_time,
    "gc_hist": chart_gc_histogram,
    "gc_timeline": chart_gc_timeline,
    "binary": chart_binary_size,
    "latency": chart_latency_distribution,
}


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark charts")
    parser.add_argument("--charts", nargs="+", default=None,
                        choices=list(CHART_FUNCTIONS.keys()),
                        help="Which charts to generate (default: all)")
    parser.add_argument("--format", nargs="+", default=["pdf"],
                        choices=["pdf", "png", "svg"],
                        help="Output formats (default: pdf)")
    parser.add_argument("--config", default=None, help="Path to config.toml")

    args = parser.parse_args()
    config = load_config(args.config)

    setup_style()

    charts = args.charts or list(CHART_FUNCTIONS.keys())
    formats = args.format

    print(f"Generating charts: {charts}")
    print(f"Formats: {formats}\n")

    for chart_name in charts:
        print(f"Chart: {chart_name}")
        CHART_FUNCTIONS[chart_name](config, formats)
        print()

    print("Done.")


if __name__ == "__main__":
    main()
