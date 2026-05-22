"""
Benchmark orchestrator for Java vs Rust comparison.

Usage:
    python bench/run_benchmarks.py --phases all
    python bench/run_benchmarks.py --phases build timing
    python bench/run_benchmarks.py --phases timing --runs 5 --warmup 1
    python bench/run_benchmarks.py --phases generate --regen-data
    python bench/run_benchmarks.py --phases all --scenarios scenario4
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from utils import (
    ensure_dirs,
    get_jar_exe,
    get_java_command,
    get_java_command_with_gc,
    get_javac_exe,
    get_project_root,
    get_rust_command,
    get_scenarios,
    load_config,
    load_json,
    results_path,
    save_json,
)


def phase_build(config, scenarios):
    print("=== Phase: BUILD ===")
    root = get_project_root()
    javac = get_javac_exe(config)
    jar_exe = get_jar_exe(config)
    java_src = root / "java" / "src" / "main" / "java"

    binary_sizes_path = results_path(config, "raw", "binary_sizes.json")
    binary_sizes = load_json(binary_sizes_path) if binary_sizes_path.exists() else {}

    for scenario_id, scenario in scenarios.items():
        package = scenario["java_package"]
        print(f"\n--- {scenario_id}: {scenario['name']} ---")

        print(f"  Building Java ({package})...")
        classes_dir = root / "java" / "target" / "classes" / scenario_id
        jar_path = root / scenario["java_jar"]

        if classes_dir.exists():
            shutil.rmtree(classes_dir)
        classes_dir.mkdir(parents=True, exist_ok=True)

        package_dir = java_src / "org" / "master" / package
        sources = [str(p) for p in package_dir.rglob("*.java")]
        if not sources:
            print(f"  ERROR: No Java sources for package {package} at {package_dir}", file=sys.stderr)
            return False

        result = subprocess.run(
            [javac, "-d", str(classes_dir)] + sources,
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  javac FAILED:\n{result.stderr}", file=sys.stderr)
            return False

        jar_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [jar_exe, "cfe", str(jar_path), f"org.master.{package}.Main", "-C", str(classes_dir), "."],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  jar FAILED:\n{result.stderr}", file=sys.stderr)
            return False

        java_size = jar_path.stat().st_size
        print(f"  Java JAR: {jar_path} ({java_size / 1024:.1f} KB)")

        print(f"  Building Rust ({package})...")
        cargo_toml = root / "rust" / "Cargo.toml"
        result = subprocess.run(
            ["cargo", "build", "--release", "--bin", package, "--manifest-path", str(cargo_toml)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  cargo build FAILED:\n{result.stderr}", file=sys.stderr)
            return False

        rust_bin = root / scenario["rust_binary"]
        rust_size = rust_bin.stat().st_size
        print(f"  Rust EXE: {rust_bin} ({rust_size / 1024:.1f} KB)")

        binary_sizes[scenario_id] = {
            "java_jar_bytes": java_size,
            "rust_exe_bytes": rust_size,
        }

    save_json(binary_sizes, binary_sizes_path)
    print("\nBuild complete.")
    return True


def phase_generate(config, scenarios, regen=False):
    print("=== Phase: GENERATE ===")
    root = get_project_root()
    any_run = False
    for scenario_id, scenario in scenarios.items():
        script_rel = scenario.get("generator_script")
        if not script_rel:
            continue
        any_run = True
        output_rel = scenario.get("generator_output")
        output_abs = (root / output_rel) if output_rel else None
        script_abs = root / script_rel

        if output_abs and output_abs.exists() and not regen:
            size_mb = output_abs.stat().st_size / (1024 * 1024)
            print(f"  [{scenario_id}] {output_abs} exists ({size_mb:.1f} MB), skipping. Use --regen-data to force.")
            continue

        print(f"  [{scenario_id}] Running {script_abs}...")
        result = subprocess.run([sys.executable, str(script_abs)], cwd=str(root))
        if result.returncode != 0:
            print(f"  Generator FAILED for {scenario_id}", file=sys.stderr)
            return False

    if not any_run:
        print("  No scenarios declare a generator_script.")
    print("Generate complete.")
    return True


def phase_timing(config, scenarios, runs, warmup):
    print("=== Phase: TIMING (hyperfine) ===")

    if not shutil.which("hyperfine"):
        print("  ERROR: hyperfine not found. Install with: cargo install hyperfine", file=sys.stderr)
        return False

    root = get_project_root()

    for scenario_id, scenario in scenarios.items():
        print(f"\n--- {scenario['name']} ---")

        for lang in ["java", "rust"]:
            if lang == "java":
                cmd = get_java_command(config, scenario_id)
            else:
                cmd = get_rust_command(config, scenario_id)

            cmd_str = subprocess.list2cmdline(cmd)
            output_json = str(results_path(config, "raw", "hyperfine", f"{scenario_id}_{lang}.json"))

            hyperfine_cmd = [
                "hyperfine",
                "--runs", str(runs),
                "--warmup", str(warmup),
                "--export-json", output_json,
                "--style", "full",
                cmd_str,
            ]

            print(f"  Running hyperfine for {lang}: {runs} runs, {warmup} warmup...")
            result = subprocess.run(hyperfine_cmd, cwd=str(root))
            if result.returncode != 0:
                print(f"  hyperfine FAILED for {lang}", file=sys.stderr)
                return False

    consolidate_timing(config, scenarios)
    consolidate_latency(config, scenarios)
    print("Timing complete.")
    return True


def consolidate_timing(config, scenarios):
    timing = {}
    for scenario_id in scenarios:
        timing[scenario_id] = {}
        for lang in ["java", "rust"]:
            path = results_path(config, "raw", "hyperfine", f"{scenario_id}_{lang}.json")
            if path.exists():
                data = load_json(path)
                r = data["results"][0]
                timing[scenario_id][lang] = {
                    "mean": r["mean"],
                    "stddev": r["stddev"],
                    "median": r["median"],
                    "min": r["min"],
                    "max": r["max"],
                    "times": r["times"],
                }
    save_json(timing, results_path(config, "parsed", "timing.json"))


def consolidate_latency(config, scenarios):
    root = get_project_root()
    for scenario_id in scenarios:
        latency = {}
        for lang in ["java", "rust"]:
            src = root / "output" / f"{scenario_id}_latency_{lang}.json"
            if src.exists():
                latency[lang] = load_json(src)
        if latency:
            save_json(latency, results_path(config, "parsed", f"latency_{scenario_id}.json"))


def phase_resources(config, scenarios, runs):
    print("=== Phase: RESOURCES (psutil) ===")
    root = get_project_root()
    monitor_script = root / "bench" / "resource_monitor.py"
    interval_ms = config["general"]["resource_sample_interval_ms"]

    for scenario_id, scenario in scenarios.items():
        print(f"\n--- {scenario['name']} ---")

        for lang in ["java", "rust"]:
            if lang == "java":
                cmd = get_java_command(config, scenario_id)
            else:
                cmd = get_rust_command(config, scenario_id)

            all_run_results = []

            for run_idx in range(runs):
                run_output = str(results_path(
                    config, "raw", "resource_monitor",
                    f"{scenario_id}_{lang}_run{run_idx}.json",
                ))

                monitor_cmd = [
                    sys.executable, str(monitor_script),
                    "--output", run_output,
                    "--interval-ms", str(interval_ms),
                    "--",
                ] + cmd

                print(f"  {lang} run {run_idx + 1}/{runs}...", end=" ", flush=True)
                result = subprocess.run(monitor_cmd, cwd=str(root), capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"FAILED\n{result.stderr}", file=sys.stderr)
                    continue
                print(result.stdout.strip())
                all_run_results.append(load_json(run_output))

            if all_run_results:
                aggregated = aggregate_resource_runs(all_run_results)
                save_json(aggregated, results_path(
                    config, "raw", "resource_monitor",
                    f"{scenario_id}_{lang}_aggregated.json",
                ))

    consolidate_resources(config, scenarios)
    print("Resources complete.")
    return True


def aggregate_resource_runs(run_results):
    peak_rss_values = [r["memory"]["peak_rss_bytes"] for r in run_results]
    wall_times = [r["wall_time_ms"] for r in run_results]

    median_idx = sorted(range(len(wall_times)), key=lambda i: wall_times[i])[len(wall_times) // 2]
    median_run = run_results[median_idx]

    return {
        "runs": len(run_results),
        "wall_time_ms": {
            "mean": sum(wall_times) / len(wall_times),
            "median": wall_times[median_idx],
            "min": min(wall_times),
            "max": max(wall_times),
        },
        "memory": {
            "peak_rss_bytes_mean": int(sum(peak_rss_values) / len(peak_rss_values)),
            "peak_rss_bytes_max": max(peak_rss_values),
            "peak_rss_bytes_min": min(peak_rss_values),
        },
        "median_run_timeseries": median_run["timeseries"],
        "all_run_timeseries": [r["timeseries"] for r in run_results],
    }


def consolidate_resources(config, scenarios):
    resources = {}
    for scenario_id in scenarios:
        resources[scenario_id] = {}
        for lang in ["java", "rust"]:
            path = results_path(config, "raw", "resource_monitor", f"{scenario_id}_{lang}_aggregated.json")
            if path.exists():
                resources[scenario_id][lang] = load_json(path)
    save_json(resources, results_path(config, "parsed", "resources.json"))


def phase_gc(config, scenarios, runs):
    print("=== Phase: GC LOGS ===")
    root = get_project_root()
    bench_dir = root / "bench"
    sys.path.insert(0, str(bench_dir))
    from gc_parser import parse_gc_log

    for scenario_id, scenario in scenarios.items():
        print(f"\n--- {scenario['name']} (Java GC) ---")

        gc_log_path = str(results_path(config, "raw", "gc_logs", f"{scenario_id}_gc.log"))
        cmd = get_java_command_with_gc(config, scenario_id, gc_log_path)

        print(f"  Running Java with GC logging...")
        result = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  FAILED:\n{result.stderr}", file=sys.stderr)
            continue

        if os.path.exists(gc_log_path):
            parsed = parse_gc_log(gc_log_path)
            out_path = results_path(config, "parsed", f"gc_pauses_{scenario_id}.json")
            save_json(parsed, out_path)
            print(f"  Parsed {parsed['total_pauses']} GC pauses -> {out_path}")
        else:
            print(f"  WARNING: GC log not created at {gc_log_path}")

    print("GC phase complete.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Benchmark runner: Java vs Rust")
    parser.add_argument(
        "--phases", nargs="+",
        choices=["build", "generate", "timing", "resources", "gc", "all"],
        default=["all"],
        help="Which phases to run",
    )
    parser.add_argument("--scenarios", nargs="+", default=None, help="Scenario IDs to run (default: all)")
    parser.add_argument("--runs", type=int, default=None, help="Override number of benchmark runs")
    parser.add_argument("--warmup", type=int, default=None, help="Override number of warmup runs")
    parser.add_argument("--regen-data", action="store_true",
                        help="Force regeneration of data files in 'generate' phase")
    parser.add_argument("--config", default=None, help="Path to config.toml")

    args = parser.parse_args()
    config = load_config(args.config)
    ensure_dirs(config)

    phases = args.phases
    if "all" in phases:
        phases = ["build", "generate", "timing", "resources", "gc"]

    all_scenarios = get_scenarios(config)
    if args.scenarios:
        scenarios = {k: v for k, v in all_scenarios.items() if k in args.scenarios}
    else:
        scenarios = all_scenarios

    runs = args.runs or config["general"]["benchmark_runs"]
    warmup = args.warmup or config["general"]["warmup_runs"]
    resource_runs = args.runs or config["general"]["resource_monitor_runs"]

    print(f"Scenarios: {list(scenarios.keys())}")
    print(f"Phases: {phases}")
    print(f"Runs: {runs} (timing), {resource_runs} (resources), Warmup: {warmup}")
    print()

    success = True
    if "build" in phases:
        success = phase_build(config, scenarios) and success
    if "generate" in phases:
        success = phase_generate(config, scenarios, regen=args.regen_data) and success
    if "timing" in phases:
        success = phase_timing(config, scenarios, runs, warmup) and success
    if "resources" in phases:
        success = phase_resources(config, scenarios, resource_runs) and success
    if "gc" in phases:
        success = phase_gc(config, scenarios, runs) and success

    if success:
        print("\nAll phases complete. Run: python bench/visualize.py")
    else:
        print("\nSome phases failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
