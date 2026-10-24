"""
Recompute every number shown on the slides from results/parsed/*.json.

Usage:
    .venv/bin/python presentation/scripts/key_numbers.py     # prints a table, writes presentation/assets/numbers.json

RSS is reported in MiB (bytes / 1024^2), the same unit the bench/visualize.py charts label "MB",
so numbers on the slides match the chart axes.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARSED = ROOT / "results" / "parsed"
OUT = ROOT / "presentation" / "assets" / "numbers.json"
MIB = 1024 ** 2
LANGS = ("java", "rust")
TAIL_THRESHOLDS_NS = (102_400, 409_600, 819_200)


def load(name):
    return json.loads((PARSED / name).read_text())


def ratio(java, rust):
    return java / rust


def timing_numbers(timing):
    out = {}
    for s in ("scenario1", "scenario2", "scenario4"):
        out[s] = {lang: timing[s][lang]["median"] for lang in LANGS}
    for s in ("scenario3", "scenario3_small"):
        out[s] = {lang: {int(p): v["median"] for p, v in timing[s][lang]["by_threads"].items()} for lang in LANGS}
    return out


def speedup(times):
    return {p: times[1] / t for p, t in times.items()}


def peak_rss(resources):
    out = {}
    for s in ("scenario1", "scenario2", "scenario4"):
        out[s] = {lang: resources[s][lang]["memory"]["peak_rss_bytes_mean"] / MIB for lang in LANGS}
    out["scenario3"] = {
        int(p): {lang: resources["scenario3"][lang]["by_threads"][p]["memory"]["peak_rss_bytes_mean"] / MIB
                 for lang in LANGS}
        for p in resources["scenario3"]["java"]["by_threads"]
    }
    out["startup_mib"] = {
        s: {lang: max(x["rss_bytes"] for x in resources[s][lang]["median_run_timeseries"][:30]) / MIB
            for lang in LANGS}
        for s in ("scenario1",)
    }
    return out


def gc_numbers():
    out = {}
    for name in ("scenario2", "scenario4", "scenario3_p6", "scenario3_p12"):
        d = load(f"gc_pauses_{name}.json")
        pauses = d["pauses"]
        ts = [p["timestamp_s"] for p in pauses]
        gaps = [(b - a, a, b) for a, b in zip(ts, ts[1:])]
        longest = max(gaps) if gaps else (0, 0, 0)
        out[name] = {
            "count": d["total_pauses"],
            "mean_ms": d["summary"]["mean_pause_ms"],
            "median_ms": d["summary"]["median_pause_ms"],
            "max_ms": d["summary"]["max_pause_ms"],
            "total_ms": d["summary"]["total_pause_time_ms"],
            "longest_gap_s": longest[0],
            "longest_gap_from_s": longest[1],
            "longest_gap_to_s": longest[2],
            "max_heap_capacity_mb": max((p["heap_capacity_mb"] for p in pauses), default=0),
        }
    return out


def latency_numbers():
    d = load("latency_scenario4.json")
    out = {}
    for lang in LANGS:
        x = d[lang]
        lower = [100 * 2 ** i for i in range(len(x["buckets"]))]
        tail = {t: sum(c for lo, c in zip(lower, x["buckets"]) if lo >= t) for t in TAIL_THRESHOLDS_NS}
        out[lang] = {
            "events": x["total_events"],
            "p50_us": x["p50_ns"] / 1000, "p95_us": x["p95_ns"] / 1000,
            "p99_us": x["p99_ns"] / 1000, "p999_us": x["p999_ns"] / 1000,
            "max_ms": x["max_ns"] / 1e6, "mean_ns": x["mean_ns"],
            "tail": tail,
        }
    return out


def step_numbers():
    d = load("steps_scenario3.json")
    out = {}
    for p in ("6", "12"):
        out[int(p)] = {}
        for lang in LANGS:
            r = d[lang][p]["resource_runs"]
            pct = {k: v / 1e6 for k, v in r["step_percentiles_ns"].items()}
            out[int(p)][lang] = {**pct, "runs": r["runs"], "tail_ratio_p99_p50": pct["p99"] / pct["p50"]}
    phases = {}
    for lang in LANGS:
        t = d[lang]["1"]["timing_run"]
        phases[lang] = {k: v / 1e6 for k, v in t["phase_median_ns"].items()}
        phases[lang]["serial_fraction"] = t["serial_fraction"]
    out["phases_p1_ms"] = phases
    return out


def main():
    timing = load("timing.json")
    resources = load("resources.json")
    t = timing_numbers(timing)
    rss = peak_rss(resources)
    nums = {
        "time_s": t,
        "time_ratio": {
            "scenario1": ratio(*t["scenario1"].values()),
            "scenario2": ratio(*t["scenario2"].values()),
            "scenario4": ratio(*t["scenario4"].values()),
            "scenario3": {p: ratio(t["scenario3"]["java"][p], t["scenario3"]["rust"][p]) for p in t["scenario3"]["java"]},
        },
        "rust_faster_pct_s1": (1 - t["scenario1"]["rust"] / t["scenario1"]["java"]) * 100,
        "speedup": {s: {lang: speedup(t[s][lang]) for lang in LANGS} for s in ("scenario3", "scenario3_small")},
        "peak_rss_mib": rss,
        "rss_ratio": {
            "scenario1": ratio(*rss["scenario1"].values()),
            "scenario2": ratio(*rss["scenario2"].values()),
            "scenario4": ratio(*rss["scenario4"].values()),
            "scenario3": {p: ratio(*v.values()) for p, v in rss["scenario3"].items()},
        },
        "gc": gc_numbers(),
        "latency_s4": latency_numbers(),
        "steps_s3": step_numbers(),
    }
    nums["efficiency_s3"] = {lang: {p: s / p for p, s in nums["speedup"]["scenario3"][lang].items()} for lang in LANGS}
    OUT.write_text(json.dumps(nums, indent=2))
    print(json.dumps(nums, indent=1))


if __name__ == "__main__":
    main()
