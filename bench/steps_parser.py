"""
Consolidation of per-step JSON files written by scenario 3 (one file per program run).

Raw inputs (copied by run_benchmarks.py into results/raw/steps/):
    {scenario}_{lang}_p{P}.json          last hyperfine run for P          -> "timing_run"
    {scenario}_{lang}_p{P}_run{k}.json   resource-monitor runs (pooled)    -> "resource_runs"
    {scenario}_java_p{P}_gc.json         run with -Xlog:gc*                -> "gc_run"

Output: results/parsed/steps_{scenario}.json, keyed by language, then by P (as a string).

Distribution statistics use the steady state only: the first WARMUP_FRACTION of steps of every run
(JIT warm-up, melting of the initial crystal) is discarded. Raw arrays are kept in full.

Usage:
    python bench/steps_parser.py scenario3
"""

import argparse
import sys

from utils import get_scenarios, load_config, load_json, results_path, save_json

WARMUP_FRACTION = 0.1
PHASES = ["positions", "cells", "forces", "velocities"]
LANGS = ["java", "rust"]


def discarded_steps(steps):
    return int(steps * WARMUP_FRACTION)


def steady(values):
    return values[discarded_steps(len(values)):]


def percentile(sorted_values, pct):
    """Linear interpolation between closest ranks (numpy's default method)."""
    pos = (len(sorted_values) - 1) * pct / 100
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def median(values):
    return percentile(sorted(values), 50)


def step_percentiles(values):
    s = sorted(values)
    return {
        "p50": percentile(s, 50),
        "p95": percentile(s, 95),
        "p99": percentile(s, 99),
        "max": s[-1],
    }


def summarize_run(data):
    """Steady-state summary of one run plus its raw step timeline."""
    step_ns = steady(data["step_ns"])
    phases = {name: steady(data["phase_ns"][name]) for name in PHASES}
    summary = {
        "n": data["n"],
        "steps": data["steps"],
        "discarded_steps": discarded_steps(data["steps"]),
        "step_median_ns": median(step_ns),
        "step_percentiles_ns": step_percentiles(step_ns),
        "phase_median_ns": {name: median(v) for name, v in phases.items()},
        # Share of the serial cell-list phase in the step time (Amdahl's s when P = 1).
        "serial_fraction": sum(phases["cells"]) / sum(step_ns),
        "step_ns": data["step_ns"],
        "step_start_ns": data["step_start_ns"],
    }
    if "t0_uptime_ms" in data:
        summary["t0_uptime_ms"] = data["t0_uptime_ms"]
    return summary


def summarize_pooled(runs):
    pooled = [v for data in runs for v in steady(data["step_ns"])]
    return {
        "runs": len(runs),
        "samples": len(pooled),
        "step_mean_ns": sum(pooled) / len(pooled),
        "step_percentiles_ns": step_percentiles(pooled),
    }


def run_index(path):
    return int(path.stem.rsplit("_run", 1)[1])


def consolidate_steps(config, scenario_id, scenario):
    """Writes results/parsed/steps_{scenario_id}.json from whatever raw step files exist."""
    if "threads" not in scenario:
        return None
    steps_dir = results_path(config, "raw", "steps")
    result = {"scenario": scenario_id, "warmup_fraction": WARMUP_FRACTION}
    found = False

    for lang in LANGS:
        by_threads = {}
        for p in scenario["threads"]:
            prefix = f"{scenario_id}_{lang}_p{p}"
            entry = {}

            timing_path = steps_dir / f"{prefix}.json"
            if timing_path.exists():
                entry["timing_run"] = summarize_run(load_json(timing_path))

            run_paths = sorted(steps_dir.glob(f"{prefix}_run*.json"), key=run_index)
            if run_paths:
                entry["resource_runs"] = summarize_pooled([load_json(r) for r in run_paths])

            gc_path = steps_dir / f"{prefix}_gc.json"
            if gc_path.exists():
                entry["gc_run"] = summarize_run(load_json(gc_path))

            if entry:
                by_threads[str(p)] = entry
        if by_threads:
            result[lang] = by_threads
            found = True

    if not found:
        return None
    out = results_path(config, "parsed", f"steps_{scenario_id}.json")
    save_json(result, out)
    return out


def main():
    parser = argparse.ArgumentParser(description="Consolidate scenario 3 per-step JSON files")
    parser.add_argument("scenarios", nargs="*", help="Scenario IDs (default: all with 'threads')")
    parser.add_argument("--config", default=None, help="Path to config.toml")
    args = parser.parse_args()

    config = load_config(args.config)
    scenarios = get_scenarios(config)
    ids = args.scenarios or [s for s, v in scenarios.items() if "threads" in v]
    for scenario_id in ids:
        out = consolidate_steps(config, scenario_id, scenarios[scenario_id])
        print(f"  {scenario_id}: {out or 'no step files found'}")


if __name__ == "__main__":
    sys.exit(main())
