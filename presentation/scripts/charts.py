"""
Charts for the presentation, generated from the current results/parsed/*.json.

Usage:
    .venv/bin/python presentation/scripts/charts.py

Writes to presentation/assets/:
    ram_s{1,2,4}.png   RSS over time (all runs faded, median run bold), same plot as bench/visualize.py
    exec_s{1,2,4}.png  execution time, hyperfine median (error bar = stddev)
    tail_chart.png     S4: number of events in the latency tail (>= 0.1 / 0.4 / 0.8 ms)
    step_timeline_s3.png  S3: step time at P = 12 (resource-monitor run 1), slowdown hitting Rust
    summary.png        Java/Rust ratio of execution time and peak RSS for all 4 scenarios

The per-scenario RAM/time PNGs under results/charts/scenario{1,2,4}/ predate the current data
(bench/visualize.py now only draws the combined poster version), so the slides use these instead.
Style and colours come from bench/visualize.py; font sizes are scaled up for a projector.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bench"))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from visualize import JAVA_COLOR, RUST_COLOR, gc_pauses_on_steps, plot_rss_runs, setup_style  # noqa: E402

PARSED = ROOT / "results" / "parsed"
ASSETS = ROOT / "presentation" / "assets"
DPI = 200
ACCENT = "#3d4a5c"
TAIL_THRESHOLDS_NS = (102_400, 409_600, 819_200)


def load(name):
    return json.loads((PARSED / name).read_text())


def presentation_style():
    setup_style()
    plt.rcParams.update({
        "font.size": 15,
        "axes.labelsize": 16,
        "axes.titlesize": 17,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "legend.fontsize": 14,
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
    })


def save(fig, name):
    out = ASSETS / name
    fig.savefig(out)
    plt.close(fig)
    print(f"  Saved: {out.relative_to(ROOT)}")


def chart_ram(resources):
    for n in (1, 2, 4):
        data = resources[f"scenario{n}"]
        fig, ax = plt.subplots(figsize=(9, 5.6))
        plot_rss_runs(ax, data["java"], JAVA_COLOR, "Java 25")
        plot_rss_runs(ax, data["rust"], RUST_COLOR, "Rust")
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("RSS Memory [MB]")
        ax.set_ylim(bottom=0)
        ax.set_xlim(left=0)
        ax.legend(loc="upper right" if n != 2 else "upper left")
        save(fig, f"ram_s{n}.png")


def chart_exec(timing):
    for n in (1, 2, 4):
        data = timing[f"scenario{n}"]
        fig, ax = plt.subplots(figsize=(3.0, 4.0))
        for i, (lang, color, name) in enumerate([("java", JAVA_COLOR, "Java 25"), ("rust", RUST_COLOR, "Rust")]):
            med = data[lang]["median"]
            ax.bar(i, med, 0.6, yerr=data[lang]["stddev"], color=color, capsize=4,
                   edgecolor="black", linewidth=0.5)
            ax.annotate(f"{med:.2f} s", xy=(i, med), xytext=(0, 6), textcoords="offset points",
                        ha="center", fontsize=14)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Java 25", "Rust"])
        ax.set_ylabel("Execution time [s]")
        ax.set_ylim(0, max(data[lang]["median"] for lang in ("java", "rust")) * 1.18)
        ax.grid(axis="x", visible=False)
        save(fig, f"exec_s{n}.png")


def tail_counts(lat):
    lower = [100 * 2 ** i for i in range(len(lat["buckets"]))]
    return [sum(c for lo, c in zip(lower, lat["buckets"]) if lo >= t) for t in TAIL_THRESHOLDS_NS]


def chart_tail():
    lat = load("latency_scenario4.json")
    gc = load("gc_pauses_scenario4.json")
    java, rust = tail_counts(lat["java"]), tail_counts(lat["rust"])
    x = np.arange(len(TAIL_THRESHOLDS_NS))
    width = 0.36

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for offset, vals, color, name in [(-width / 2, java, JAVA_COLOR, "Java 25"), (width / 2, rust, RUST_COLOR, "Rust")]:
        bars = ax.bar(x + offset, vals, width, color=color, label=name, edgecolor="black", linewidth=0.5)
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:d}", xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 4),
                        textcoords="offset points", ha="center", fontsize=15, fontweight="bold")

    n_pauses = gc["total_pauses"]
    ax.axhline(n_pauses, color=ACCENT, linestyle="--", linewidth=1.4)
    mean_ms = f"{gc['summary']['mean_pause_ms']:.2f}".replace(".", ",")
    ax.annotate(f"{n_pauses} pauz G1 (śr. {mean_ms} ms)",
                xy=(1.5, n_pauses), xytext=(0, 6), textcoords="offset points",
                ha="center", fontsize=15, color=ACCENT)

    ax.set_yscale("log")
    ax.set_ylim(1, 3000)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xticks(x)
    # thresholds are log2 bucket boundaries (102.4 / 409.6 / 819.2 µs), labelled rounded to 0.1 ms
    ax.set_xticklabels([f"≥ {t / 1e6:.1f} ms".replace(".", ",") for t in TAIL_THRESHOLDS_NS])
    ax.set_xlabel("Latencja zdarzenia")
    ax.set_ylabel("Liczba zdarzeń (oś log)")
    ax.set_title("Ile z 10⁹ zdarzeń trwało co najmniej…", loc="left")
    ax.legend(loc="upper right", ncol=2)
    ax.grid(axis="x", visible=False)
    save(fig, "tail_chart.png")


def chart_step_timeline():
    """S3 step time at P = 12 from resource-monitor run 1: a case where the multi-step slowdown hits Rust.
    GC pauses come from the separate GC-logged Java run. Drawn in the bench/visualize.py style
    (normal font sizes), the same layout as results/charts/scenario3/step_time_timeline.png."""
    p, run_id = 12, 1
    raw = ROOT / "results" / "raw" / "steps"
    runs = [(json.loads((raw / f"scenario3_{lang}_p{p}_run{run_id}.json").read_text()), color, name)
            for lang, color, name in [("java", JAVA_COLOR, "Java 25"), ("rust", RUST_COLOR, "Rust")]]
    java_gc_run = load("steps_scenario3.json")["java"][str(p)]["gc_run"]
    gc_xs, gc_ms = gc_pauses_on_steps(load(f"gc_pauses_scenario3_p{p}.json"), java_gc_run)

    with plt.rc_context():
        setup_style()
        fig, (ax, ax_gc) = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True,
                                        gridspec_kw={"height_ratios": [3, 1]})
        warmup = java_gc_run["discarded_steps"]
        ax.axvspan(0.5, warmup + 0.5, color="0.5", alpha=0.12, linewidth=0,
                   label=f"Excluded from statistics (first {warmup} steps)")
        ax_gc.axvspan(0.5, warmup + 0.5, color="0.5", alpha=0.12, linewidth=0)

        for run, color, name in runs:
            step_ms = [v / 1e6 for v in run["step_ns"]]
            ax.plot(np.arange(1, len(step_ms) + 1), step_ms, color=color, linewidth=1.2, label=name)

        for gx in gc_xs:
            ax.axvline(gx, color=JAVA_COLOR, linestyle=":", linewidth=0.8, alpha=0.5)
        ax_gc.vlines(gc_xs, 0, gc_ms, color=JAVA_COLOR, linewidth=1.5)
        ax_gc.plot(gc_xs, gc_ms, "o", color=JAVA_COLOR, markersize=4)
        ax_gc.set_ylim(bottom=0)

        ax.set_ylabel("Step time [ms]")
        ax.set_title(f"Step Time Timeline (P = {p}): Concurrency - Particle Sim (108k)")
        ax.legend(loc="upper right")
        ax_gc.set_ylabel("G1 pause [ms]")
        ax_gc.set_xlabel(f"Step  ({len(gc_xs)} Java GC pauses during the loop, from a separate GC-logged run)")
        fig.tight_layout(h_pad=0.4)
        fig.savefig(ASSETS / "step_timeline_s3.png", dpi=300)
        plt.close(fig)
    print(f"  Saved: {(ASSETS / 'step_timeline_s3.png').relative_to(ROOT)}")


def chart_summary(timing, resources):
    mib = 1024 ** 2
    t, r = timing, resources
    labels = ["S1\nCPU", "S2\nI/O", "S3 (P = 6)\nwspółbieżność", "S4\npamięć"]
    time_ratio = [
        t["scenario1"]["java"]["median"] / t["scenario1"]["rust"]["median"],
        t["scenario2"]["java"]["median"] / t["scenario2"]["rust"]["median"],
        t["scenario3"]["java"]["by_threads"]["6"]["median"] / t["scenario3"]["rust"]["by_threads"]["6"]["median"],
        t["scenario4"]["java"]["median"] / t["scenario4"]["rust"]["median"],
    ]

    def peak(d):
        return d["memory"]["peak_rss_bytes_mean"] / mib

    rss_ratio = [
        peak(r["scenario1"]["java"]) / peak(r["scenario1"]["rust"]),
        peak(r["scenario2"]["java"]) / peak(r["scenario2"]["rust"]),
        peak(r["scenario3"]["java"]["by_threads"]["6"]) / peak(r["scenario3"]["rust"]["by_threads"]["6"]),
        peak(r["scenario4"]["java"]) / peak(r["scenario4"]["rust"]),
    ]

    fig, (ax_t, ax_m) = plt.subplots(1, 2, figsize=(11, 4.6))
    x = np.arange(len(labels))
    for ax, vals, title, fmt in [
        (ax_t, time_ratio, "Czas wykonania: Java / Rust", lambda v: f"×{v:.2f}"),
        (ax_m, rss_ratio, "Szczytowy RSS: Java / Rust (oś log)", lambda v: f"×{v:.1f}"),
    ]:
        bars = ax.bar(x, vals, 0.6, color=ACCENT, edgecolor="black", linewidth=0.5)
        for bar, v in zip(bars, vals):
            ax.annotate(fmt(v).replace(".", ","), xy=(bar.get_x() + bar.get_width() / 2, v), xytext=(0, 5),
                        textcoords="offset points", ha="center", fontsize=16, fontweight="bold")
        ax.axhline(1, color="black", linewidth=1.0)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_title(title, loc="left")
        ax.grid(axis="x", visible=False)
    ax_t.set_ylim(0, 2.4)
    ax_t.set_ylabel("ile razy dłużej trwa Java")
    ax_m.set_yscale("log")
    ax_m.set_ylim(1, 120)
    ax_m.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax_m.set_ylabel("ile razy więcej RAM zużywa Java")
    fig.tight_layout(w_pad=3)
    save(fig, "summary.png")


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    presentation_style()
    timing = load("timing.json")
    resources = load("resources.json")
    chart_ram(resources)
    chart_exec(timing)
    chart_tail()
    chart_step_timeline()
    chart_summary(timing, resources)


if __name__ == "__main__":
    main()
