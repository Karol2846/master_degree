"""
Generate publication-quality comparison charts from benchmark results.

Usage:
    python bench/visualize.py                         # all charts
    python bench/visualize.py --charts timing ram      # specific charts
    python bench/visualize.py --format pdf png         # both formats
    python bench/visualize.py --charts speedup phases  # scenario 3 (threaded) charts only
"""

import argparse
import re
import sys
from bisect import bisect_right
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.ticker import FuncFormatter

from utils import get_project_root, load_config, load_json, results_path

JAVA_COLOR = "#E24A33"
RUST_COLOR = "#348ABD"

SCENARIO_LABELS = {
    "scenario1": "CPU\nMandelbrot",
    "scenario2": "I/O\nCSV Processing",
    "scenario3": "Concurrency\nParticle Sim (108k)",
    "scenario3_small": "Concurrency\nParticle Sim (4k)",
    "scenario4": "Memory\nIoT Streaming",
}

# Threaded scenarios (scenario 3)
LANGS = [("java", JAVA_COLOR, "Java 25"), ("rust", RUST_COLOR, "Rust")]
PHYSICAL_CORES = 6  # Ryzen 5 7500X3D: 6 cores / 12 SMT threads
REPRESENTATIVE_THREADS = 6  # P used for single-P charts (execution time, step timeline)
PHASE_STYLES = [
    # key, label, color, hatch (serial phase hatched)
    ("positions", "A: positions", "#1baf7a", None),
    ("cells", "B: cell list (serial)", "#eda100", "//"),
    ("forces", "C: forces", "#6250d6", None),
    ("velocities", "D: velocities", "#e87ba4", None),
]
# Log axes spanning less than a decade: label ticks as plain numbers (60, not 6x10^1)
PLAIN_TICKS = FuncFormatter(lambda v, _: f"{v:g}")
PERCENTILES = [("p50", "p50"), ("p95", "p95"), ("p99", "p99"), ("max", "max")]


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
    "scenario1": "CPU",
    "scenario2": "I/O operations",
    "scenario4": "IoT Streaming",
}


def scenario_label(scenario_id):
    return SCENARIO_LABELS.get(scenario_id, scenario_id).replace("\n", " - ")


def threaded_scenarios(config):
    return [s for s, v in config["scenarios"].items() if "threads" in v]


def by_threads(lang_data):
    """{"by_threads": {"6": x}} -> {6: x}; empty for single-threaded entries."""
    return {int(p): v for p, v in (lang_data or {}).get("by_threads", {}).items()}


def load_steps(config, scenario_id):
    path = results_path(config, "parsed", f"steps_{scenario_id}.json")
    return load_json(path) if path.exists() else None


def split_threads_suffix(name):
    """"scenario3_p6" -> ("scenario3", 6); names without the suffix -> (name, None)."""
    m = re.match(r"^(.*)_p(\d+)$", name)
    return (m.group(1), int(m.group(2))) if m else (name, None)


def chart_execution_time(config, formats):
    path = results_path(config, "parsed", "timing.json")
    if not path.exists():
        print("  Skipping execution time chart (no timing data)")
        return

    timing = load_json(path)
    chart_execution_time_poster(config, timing, formats)
    chart_execution_time_threads(config, timing, formats)


def chart_execution_time_poster(config, timing, formats):
    scenarios = [s for s in POSTER_EXEC_ORDER if s in timing]
    if not scenarios:
        print("  Skipping execution time chart (no poster scenarios in timing data)")
        return

    width = 0.28
    x = np.arange(len(scenarios))
    java_means = [timing[s]["java"]["mean"] for s in scenarios]
    java_stds = [timing[s]["java"]["stddev"] for s in scenarios]
    rust_means = [timing[s]["rust"]["mean"] for s in scenarios]
    rust_stds = [timing[s]["rust"]["stddev"] for s in scenarios]

    fig, ax = plt.subplots(figsize=(14, 7.5))

    bars_j = ax.bar(x - width / 2, java_means, width, yerr=java_stds,
                    label="Java 25", color=JAVA_COLOR, capsize=4,
                    edgecolor="black", linewidth=0.5)
    bars_r = ax.bar(x + width / 2, rust_means, width, yerr=rust_stds,
                    label="Rust", color=RUST_COLOR, capsize=4,
                    edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Execution Time [s]")
    ax.set_xticks(x)
    ax.set_xticklabels([POSTER_EXEC_LABELS[s] for s in scenarios])
    ax.legend()

    for bar in list(bars_j) + list(bars_r):
        h = bar.get_height()
        ax.annotate(f"{h:.2f}s",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=7)

    save_chart(fig, results_path(config, "charts", "execution_time.pdf"), formats)


def chart_execution_time_threads(config, timing, formats):
    """Per-scenario Java vs Rust bars at P = REPRESENTATIVE_THREADS (hyperfine mean +- stddev)."""
    p = REPRESENTATIVE_THREADS
    width = 0.35
    for scenario_id in threaded_scenarios(config):
        data = timing.get(scenario_id, {})
        java = by_threads(data.get("java")).get(p)
        rust = by_threads(data.get("rust")).get(p)
        if not (java and rust):
            continue

        x = np.arange(1)
        fig, ax = plt.subplots(figsize=(4.0, 4.5))
        bars_j = ax.bar(x - width / 2, [java["mean"]], width, yerr=[java["stddev"]],
                        label="Java 25", color=JAVA_COLOR, capsize=4,
                        edgecolor="black", linewidth=0.5)
        bars_r = ax.bar(x + width / 2, [rust["mean"]], width, yerr=[rust["stddev"]],
                        label="Rust", color=RUST_COLOR, capsize=4,
                        edgecolor="black", linewidth=0.5)

        label = scenario_label(scenario_id)
        ax.set_ylabel("Execution Time [s]")
        ax.set_title(f"Execution Time (P = {p}): {label}")
        ax.set_xticks(x)
        ax.set_xticklabels([label])
        ax.legend()

        for bar in list(bars_j) + list(bars_r):
            h = bar.get_height()
            ax.annotate(f"{h:.2f}s",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", fontsize=8)

        save_chart(fig, chart_dir(config, scenario_id) / "execution_time.pdf", formats)


def chart_peak_ram(config, formats):
    path = results_path(config, "parsed", "resources.json")
    if not path.exists():
        print("  Skipping peak RAM chart (no resource data)")
        return

    resources = load_json(path)
    width = 0.35
    threaded = threaded_scenarios(config)

    for scenario_id, data in resources.items():
        if scenario_id in threaded:
            chart_peak_ram_threads(config, scenario_id, data, formats)
            continue
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


def chart_peak_ram_threads(config, scenario_id, data, formats):
    """Peak RSS per measured thread count (resource_threads), Java vs Rust side by side."""
    java = by_threads(data.get("java"))
    rust = by_threads(data.get("rust"))
    ps = sorted(set(java) | set(rust))
    if not ps:
        return
    width = 0.35
    x = np.arange(len(ps))

    def peaks(side):
        return [side.get(p, {}).get("memory", {}).get("peak_rss_bytes_mean", 0) / (1024 ** 2) for p in ps]

    fig, ax = plt.subplots(figsize=(5.0, 4.5))
    bars_j = ax.bar(x - width / 2, peaks(java), width, label="Java 25", color=JAVA_COLOR,
                    edgecolor="black", linewidth=0.5)
    bars_r = ax.bar(x + width / 2, peaks(rust), width, label="Rust", color=RUST_COLOR,
                    edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Peak RSS (MB)")
    ax.set_title(f"Peak Memory Usage: {scenario_label(scenario_id)}")
    ax.set_xticks(x)
    ax.set_xticklabels([f"P = {p}" for p in ps])
    ax.legend()

    for bar in list(bars_j) + list(bars_r):
        h = bar.get_height()
        ax.annotate(f"{h:.0f} MB",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=8)

    save_chart(fig, chart_dir(config, scenario_id) / "peak_ram.pdf", formats)


def plot_rss_runs(ax, lang_data, color, label):
    """All runs thin and faded, the median run bold; returns the median line (or None)."""
    all_runs = lang_data.get("all_run_timeseries") or (
        [lang_data["median_run_timeseries"]] if lang_data.get("median_run_timeseries") else []
    )
    median = lang_data.get("median_run_timeseries", [])

    for ts in all_runs:
        ax.plot(
            [s["timestamp_ms"] / 1000 for s in ts],
            [s["rss_bytes"] / (1024 ** 2) for s in ts],
            color=color, alpha=0.4, linewidth=0.8,
        )
    if not median:
        return None
    line, = ax.plot(
        [s["timestamp_ms"] / 1000 for s in median],
        [s["rss_bytes"] / (1024 ** 2) for s in median],
        color=color, alpha=1.0, linewidth=2, label=label,
    )
    return line


def chart_ram_over_time(config, formats):
    path = results_path(config, "parsed", "resources.json")
    if not path.exists():
        print("  Skipping RAM-over-time charts (no resource data)")
        return

    resources = load_json(path)
    chart_ram_over_time_poster(config, resources, formats)
    chart_ram_over_time_threads(config, resources, formats)


def chart_ram_over_time_poster(config, resources, formats):
    scenarios = [s for s in POSTER_EXEC_ORDER if s in resources]
    if not scenarios:
        print("  Skipping RAM-over-time chart (no poster scenarios in resource data)")
        return

    fig, axes = plt.subplots(
        nrows=len(scenarios), ncols=1,
        figsize=(14, 2.8 * len(scenarios)),
    )
    if len(scenarios) == 1:
        axes = [axes]

    java_handle = None
    rust_handle = None

    for ax, scenario_id in zip(axes, scenarios):
        data = resources[scenario_id]
        line = plot_rss_runs(ax, data.get("java", {}), JAVA_COLOR, "Java 25")
        if java_handle is None:
            java_handle = line
        line = plot_rss_runs(ax, data.get("rust", {}), RUST_COLOR, "Rust")
        if rust_handle is None:
            rust_handle = line

        ax.set_title(POSTER_EXEC_LABELS.get(scenario_id, scenario_id), loc="left", fontsize=11)
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("RSS Memory [MB]")

    handles = [h for h in [java_handle, rust_handle] if h is not None]
    if handles:
        fig.legend(
            handles=handles,
            loc="upper right",
            bbox_to_anchor=(1.0, 1.0),
            ncol=len(handles),
        )

    fig.tight_layout(rect=[0, 0, 1, 0.97], h_pad=0.6)
    save_chart(fig, results_path(config, "charts", "ram_over_time.pdf"), formats)


def chart_ram_over_time_threads(config, resources, formats):
    """One row per measured thread count; Java and Rust on the same axes."""
    for scenario_id in threaded_scenarios(config):
        data = resources.get(scenario_id, {})
        java = by_threads(data.get("java"))
        rust = by_threads(data.get("rust"))
        ps = sorted(set(java) | set(rust))
        if not ps:
            continue

        fig, axes = plt.subplots(nrows=len(ps), ncols=1, figsize=(10, 3.0 * len(ps)), squeeze=False)
        handles = {}
        for ax, p in zip(axes[:, 0], ps):
            for side, color, name in [(java, JAVA_COLOR, "Java 25"), (rust, RUST_COLOR, "Rust")]:
                line = plot_rss_runs(ax, side.get(p, {}), color, name)
                if line is not None:
                    handles.setdefault(name, line)
            ax.set_title(f"P = {p}", loc="left", fontsize=11)
            ax.set_xlabel("Time [s]")
            ax.set_ylabel("RSS Memory [MB]")

        fig.legend(handles=list(handles.values()), loc="upper right", ncol=len(handles))
        fig.suptitle(f"Memory Usage Over Time: {scenario_label(scenario_id)}", x=0.01, ha="left")
        fig.tight_layout(rect=[0, 0, 1, 0.97], h_pad=0.6)
        save_chart(fig, chart_dir(config, scenario_id) / "ram_over_time.pdf", formats)


def chart_gc_histogram(config, formats):
    parsed_dir = results_path(config, "parsed")
    gc_files = list(parsed_dir.glob("gc_pauses_*.json"))

    if not gc_files:
        print("  Skipping GC histogram (no GC data)")
        return

    for gc_file in gc_files:
        gc_data = load_json(gc_file)
        scenario_id, threads = split_threads_suffix(gc_file.stem.replace("gc_pauses_", ""))
        suffix = "" if threads is None else f"_p{threads}"

        if not gc_data["pauses"]:
            continue

        fig, ax = plt.subplots(figsize=(12, 2.7))

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

        ax.set_xlabel("Pause Duration [ms]")
        ax.set_ylabel("Count")
        ax.legend()

        poster_label = POSTER_EXEC_LABELS.get(scenario_id)
        if poster_label:
            ax.text(0.0, -0.1, poster_label, transform=ax.transAxes,
                    fontsize=10, va="top", ha="left", style="italic", clip_on=False)
        if threads is not None:
            ax.set_title(f"GC Pause Durations (Java, P = {threads}): {scenario_label(scenario_id)}")

        save_chart(fig, chart_dir(config, scenario_id) / f"gc_pause_histogram{suffix}.pdf", formats)


def chart_gc_timeline(config, formats):
    parsed_dir = results_path(config, "parsed")
    gc_files = list(parsed_dir.glob("gc_pauses_*.json"))

    if not gc_files:
        print("  Skipping GC timeline (no GC data)")
        return

    for gc_file in gc_files:
        gc_data = load_json(gc_file)
        scenario_id, threads = split_threads_suffix(gc_file.stem.replace("gc_pauses_", ""))
        suffix = "" if threads is None else f"_p{threads}"

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
        if threads is not None:
            label += f" (P = {threads})"
        ax.set_title(f"GC Pause Events Over Time: {label}")
        ax.legend()

        save_chart(fig, chart_dir(config, scenario_id) / f"gc_pause_timeline{suffix}.pdf", formats)


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


def threaded_timing(config):
    """{scenario_id: {lang: {P: hyperfine stats}}} for threaded scenarios with timing data."""
    path = results_path(config, "parsed", "timing.json")
    if not path.exists():
        return {}
    timing = load_json(path)
    out = {}
    for scenario_id in threaded_scenarios(config):
        langs = {lang: by_threads(timing.get(scenario_id, {}).get(lang)) for lang, _, _ in LANGS}
        if any(langs.values()):
            out[scenario_id] = langs
    return out


def serial_fraction(steps, lang):
    """Amdahl's s: share of the serial cell-list phase in the step time at P = 1."""
    try:
        return steps[lang]["1"]["timing_run"]["serial_fraction"]
    except (KeyError, TypeError):
        return None


def mark_physical_cores(ax):
    ax.axvline(PHYSICAL_CORES, color="black", linewidth=0.8, alpha=0.4)
    ax.annotate(f"{PHYSICAL_CORES} physical cores", xy=(PHYSICAL_CORES, 1), xycoords=("data", "axes fraction"),
                xytext=(4, -4), textcoords="offset points", ha="left", va="top", fontsize=8, color="0.3")


def chart_speedup(config, formats):
    timing = threaded_timing(config)
    if not timing:
        print("  Skipping speedup chart (no threaded timing data)")
        return

    for scenario_id, langs in timing.items():
        steps = load_steps(config, scenario_id)
        ps = sorted(set().union(*langs.values()))

        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        ax.plot(ps, ps, color="0.5", linestyle="--", linewidth=1, label="Ideal (S = P)")
        for lang, color, name in LANGS:
            by_p = langs[lang]
            if 1 not in by_p:
                continue
            lang_ps = sorted(by_p)
            speedup = [by_p[1]["median"] / by_p[p]["median"] for p in lang_ps]
            ax.plot(lang_ps, speedup, color=color, marker="o", markersize=5, linewidth=2, label=name)

            s = serial_fraction(steps, lang)
            if s is not None:
                pp = np.linspace(1, max(ps), 200)
                ax.plot(pp, 1 / (s + (1 - s) / pp), color=color, linestyle=":", linewidth=1.5,
                        label=f"{name} Amdahl (s = {s:.3f})")

        mark_physical_cores(ax)
        ax.set_xticks(ps)
        ax.set_xlabel("Worker threads P")
        ax.set_ylabel("Speedup S(P) = T(1) / T(P)")
        ax.set_title(f"Speedup (hyperfine medians): {scenario_label(scenario_id)}")
        ax.legend(loc="upper left")
        save_chart(fig, chart_dir(config, scenario_id) / "speedup.pdf", formats)


def chart_efficiency(config, formats):
    timing = threaded_timing(config)
    if not timing:
        print("  Skipping efficiency chart (no threaded timing data)")
        return

    for scenario_id, langs in timing.items():
        ps = sorted(set().union(*langs.values()))

        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        ax.axhline(1.0, color="0.5", linestyle="--", linewidth=1, label="Ideal (E = 1)")
        for lang, color, name in LANGS:
            by_p = langs[lang]
            if 1 not in by_p:
                continue
            lang_ps = sorted(by_p)
            efficiency = [by_p[1]["median"] / by_p[p]["median"] / p for p in lang_ps]
            ax.plot(lang_ps, efficiency, color=color, marker="o", markersize=5, linewidth=2, label=name)

        mark_physical_cores(ax)
        ax.set_xticks(ps)
        ax.set_ylim(0, 1.15)
        ax.set_xlabel("Worker threads P")
        ax.set_ylabel("Parallel efficiency E(P) = S(P) / P")
        ax.set_title(f"Parallel Efficiency: {scenario_label(scenario_id)}")
        ax.legend(loc="lower left")
        save_chart(fig, chart_dir(config, scenario_id) / "efficiency.pdf", formats)


def chart_phase_breakdown(config, formats):
    found = False
    for scenario_id in threaded_scenarios(config):
        steps = load_steps(config, scenario_id) or {}
        timing_runs = {
            lang: {int(p): v["timing_run"] for p, v in steps.get(lang, {}).items() if "timing_run" in v}
            for lang, _, _ in LANGS
        }
        if not any(timing_runs.values()):
            continue
        found = True

        fig, axes = plt.subplots(1, len(LANGS), figsize=(11, 4.5), sharey=True)
        for ax, (lang, _, name) in zip(axes, LANGS):
            runs = timing_runs[lang]
            ps = sorted(runs)
            x = np.arange(len(ps))
            bottom = np.zeros(len(ps))
            for key, phase_label, color, hatch in PHASE_STYLES:
                vals = np.array([runs[p]["phase_median_ns"][key] / 1e6 for p in ps])
                ax.bar(x, vals, 0.6, bottom=bottom, label=phase_label, color=color, hatch=hatch,
                       edgecolor="black", linewidth=0.5)
                bottom += vals
            for xi, total in zip(x, bottom):
                ax.annotate(f"{total:.1f}", xy=(xi, total), xytext=(0, 3), textcoords="offset points",
                            ha="center", fontsize=8)
            ax.set_xticks(x)
            ax.set_xticklabels([str(p) for p in ps])
            ax.set_xlabel("Worker threads P")
            ax.set_title(name, loc="left", fontsize=11)
        axes[0].set_ylabel("Median phase time per step [ms]")

        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper right", ncol=len(PHASE_STYLES), fontsize=9)
        fig.suptitle(f"Step Phase Breakdown (incl. barrier wait): {scenario_label(scenario_id)}",
                     x=0.01, ha="left")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        save_chart(fig, chart_dir(config, scenario_id) / "phase_breakdown.pdf", formats)

    if not found:
        print("  Skipping phase breakdown (no per-step data)")


def chart_step_time_percentiles(config, formats):
    found = False
    for scenario_id in threaded_scenarios(config):
        steps = load_steps(config, scenario_id)
        if not steps:
            continue
        pooled = {
            lang: {int(p): v["resource_runs"] for p, v in steps.get(lang, {}).items() if "resource_runs" in v}
            for lang, _, _ in LANGS
        }
        ps = sorted(set(pooled["java"]) & set(pooled["rust"]))
        if not ps:
            continue
        found = True

        width = 0.35
        x = np.arange(len(PERCENTILES))
        fig, axes = plt.subplots(1, len(ps), figsize=(5.5 * len(ps), 4.5), sharey=True, squeeze=False)
        for ax, p in zip(axes[0], ps):
            for offset, (lang, color, name) in zip([-width / 2, width / 2], LANGS):
                stats = pooled[lang][p]
                vals = [stats["step_percentiles_ns"][key] / 1e6 for key, _ in PERCENTILES]
                bars = ax.bar(x + offset, vals, width, label=f"{name} ({stats['runs']} runs)",
                              color=color, edgecolor="black", linewidth=0.5)
                for bar in bars:
                    h = bar.get_height()
                    ax.annotate(f"{h:.1f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                                xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7)
            ax.set_yscale("log")
            ax.yaxis.set_major_formatter(PLAIN_TICKS)
            ax.yaxis.set_minor_formatter(PLAIN_TICKS)
            ax.set_xticks(x)
            ax.set_xticklabels([label for _, label in PERCENTILES])
            ax.set_xlabel("Percentile")
            ax.set_title(f"P = {p}", loc="left", fontsize=11)
            ax.legend(loc="upper left")
        axes[0][0].set_ylabel("Step time [ms, log scale]")

        warmup = int(steps["warmup_fraction"] * 100)
        fig.suptitle(f"Step Time Percentiles (first {warmup}% of steps discarded): {scenario_label(scenario_id)}",
                     x=0.01, ha="left")
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        save_chart(fig, chart_dir(config, scenario_id) / "step_time_percentiles.pdf", formats)

    if not found:
        print("  Skipping step time percentiles (no resource-phase step data)")


def gc_pauses_on_steps(gc_data, run):
    """Step numbers (1-based) in which each GC pause started, with durations; pauses outside the loop dropped.
    Pause start (ms since loop start) = log uptime (pause end) - duration - t0_uptime_ms."""
    starts_ms = [v / 1e6 for v in run["step_start_ns"]]
    loop_end_ms = (run["step_start_ns"][-1] + run["step_ns"][-1]) / 1e6
    xs, durations = [], []
    for pause in gc_data["pauses"]:
        t = pause["timestamp_s"] * 1000 - pause["pause_duration_ms"] - run["t0_uptime_ms"]
        k = bisect_right(starts_ms, t) - 1
        if k < 0 or t > loop_end_ms:
            continue
        xs.append(k + 1)
        durations.append(pause["pause_duration_ms"])
    return xs, durations


def chart_step_time_timeline(config, formats):
    p = REPRESENTATIVE_THREADS
    found = False
    for scenario_id in threaded_scenarios(config):
        steps = load_steps(config, scenario_id)
        if not steps:
            continue
        java_entry = steps.get("java", {}).get(str(p), {})
        rust_entry = steps.get("rust", {}).get(str(p), {})
        # Java from the GC-logged run (pauses can be aligned), Rust from the last hyperfine run.
        java_run = java_entry.get("gc_run")
        rust_run = rust_entry.get("timing_run")
        if not (java_run and rust_run):
            continue
        found = True

        fig, (ax, ax_gc) = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True,
                                        gridspec_kw={"height_ratios": [3, 1]})
        warmup = java_run["discarded_steps"]
        ax.axvspan(0.5, warmup + 0.5, color="0.5", alpha=0.12, linewidth=0,
                   label=f"Excluded from statistics (first {warmup} steps)")
        ax_gc.axvspan(0.5, warmup + 0.5, color="0.5", alpha=0.12, linewidth=0)

        for run, color, name in [(java_run, JAVA_COLOR, "Java 25"), (rust_run, RUST_COLOR, "Rust")]:
            step_ms = [v / 1e6 for v in run["step_ns"]]
            ax.plot(np.arange(1, len(step_ms) + 1), step_ms, color=color, linewidth=1.2, label=name)

        gc_path = results_path(config, "parsed", f"gc_pauses_{scenario_id}_p{p}.json")
        gc_xs, gc_ms = gc_pauses_on_steps(load_json(gc_path), java_run) if gc_path.exists() else ([], [])
        for gx in gc_xs:
            ax.axvline(gx, color=JAVA_COLOR, linestyle=":", linewidth=0.8, alpha=0.5)
        if gc_xs:
            ax_gc.vlines(gc_xs, 0, gc_ms, color=JAVA_COLOR, linewidth=1.5)
            ax_gc.plot(gc_xs, gc_ms, "o", color=JAVA_COLOR, markersize=4)
        ax_gc.set_ylim(bottom=0)

        ax.set_ylabel("Step time [ms]")
        ax.set_title(f"Step Time Timeline (P = {p}): {scenario_label(scenario_id)}")
        ax.legend(loc="upper right")
        ax_gc.set_ylabel("G1 pause [ms]")
        ax_gc.set_xlabel(f"Step  ({len(gc_xs)} Java GC pauses during the loop)")
        fig.tight_layout(h_pad=0.4)
        save_chart(fig, chart_dir(config, scenario_id) / "step_time_timeline.pdf", formats)

    if not found:
        print("  Skipping step time timeline (needs Java GC-run and Rust timing-run step data)")


CHART_FUNCTIONS = {
    "timing": chart_execution_time,
    "ram": chart_peak_ram,
    "ram_time": chart_ram_over_time,
    "gc_hist": chart_gc_histogram,
    "gc_timeline": chart_gc_timeline,
    "binary": chart_binary_size,
    "latency": chart_latency_distribution,
    "speedup": chart_speedup,
    "efficiency": chart_efficiency,
    "phases": chart_phase_breakdown,
    "step_pct": chart_step_time_percentiles,
    "step_timeline": chart_step_time_timeline,
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
