"""
Standalone resource monitor — launches a subprocess and samples RSS + CPU via psutil.
Separate from hyperfine to avoid measurement interference.

Usage:
    python bench/resource_monitor.py --output result.json --interval-ms 10 -- java -jar degree.jar
    python bench/resource_monitor.py --output result.json --interval-ms 50 -- rust.exe
"""

import argparse
import ctypes
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil


def set_timer_resolution():
    """Set Windows timer resolution to 1ms for accurate sub-16ms sampling."""
    try:
        winmm = ctypes.windll.winmm
        winmm.timeBeginPeriod(1)
        return True
    except Exception:
        return False


def restore_timer_resolution():
    try:
        winmm = ctypes.windll.winmm
        winmm.timeEndPeriod(1)
    except Exception:
        pass


def monitor_process(cmd_parts, interval_s, output_path):
    start_time = time.perf_counter_ns()
    proc = subprocess.Popen(cmd_parts)
    ps_proc = psutil.Process(proc.pid)

    samples = []

    try:
        ps_proc.cpu_percent()

        while proc.poll() is None:
            sample_start = time.perf_counter_ns()

            try:
                mem_info = ps_proc.memory_info()
                cpu_pct = ps_proc.cpu_percent()

                total_rss = mem_info.rss
                for child in ps_proc.children(recursive=True):
                    try:
                        total_rss += child.memory_info().rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                elapsed_ms = (sample_start - start_time) / 1_000_000
                samples.append({
                    "timestamp_ms": round(elapsed_ms, 2),
                    "rss_bytes": total_rss,
                    "cpu_percent": round(cpu_pct, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

            measurement_time = (time.perf_counter_ns() - sample_start) / 1e9
            sleep_time = max(0, interval_s - measurement_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        proc.wait()

    end_time = time.perf_counter_ns()
    wall_time_ms = (end_time - start_time) / 1_000_000

    rss_values = [s["rss_bytes"] for s in samples]
    cpu_values = [s["cpu_percent"] for s in samples]

    result = {
        "command": cmd_parts,
        "wall_time_ms": round(wall_time_ms, 2),
        "exit_code": proc.returncode,
        "sample_count": len(samples),
        "sample_interval_ms": round(interval_s * 1000, 1),
        "memory": {
            "peak_rss_bytes": max(rss_values) if rss_values else 0,
            "mean_rss_bytes": int(sum(rss_values) / len(rss_values)) if rss_values else 0,
            "min_rss_bytes": min(rss_values) if rss_values else 0,
        },
        "cpu": {
            "mean_percent": round(sum(cpu_values) / len(cpu_values), 1) if cpu_values else 0,
            "max_percent": max(cpu_values) if cpu_values else 0,
        },
        "timeseries": samples,
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def main():
    parser = argparse.ArgumentParser(description="Monitor subprocess resource usage")
    parser.add_argument("--output", "-o", required=True, help="Output JSON path")
    parser.add_argument("--interval-ms", type=int, default=10, help="Sampling interval in ms")
    parser.add_argument("command", nargs="+", help="Command to monitor (use -- before it)")

    args = parser.parse_args()
    interval_s = args.interval_ms / 1000.0

    high_res = set_timer_resolution()
    if not high_res and args.interval_ms < 16:
        print(f"Warning: could not set high-res timer. Actual interval may be ~16ms.", file=sys.stderr)

    try:
        result = monitor_process(args.command, interval_s, args.output)
    finally:
        restore_timer_resolution()

    peak_mb = result["memory"]["peak_rss_bytes"] / (1024 ** 2)
    print(f"Done: {result['wall_time_ms']:.0f}ms, peak RSS {peak_mb:.1f} MB, "
          f"{result['sample_count']} samples -> {args.output}")


if __name__ == "__main__":
    main()
