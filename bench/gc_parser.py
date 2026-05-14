"""
Parser for Java GC logs produced by -Xlog:gc*:file=...:time,uptime,level,tags

Usage:
    python bench/gc_parser.py path/to/gc.log -o parsed_output.json

As a module:
    from gc_parser import parse_gc_log
    data = parse_gc_log("gc.log")
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class GCPause:
    gc_id: int
    timestamp_s: float
    pause_type: str
    cause: str
    heap_before_mb: int
    heap_after_mb: int
    heap_capacity_mb: int
    pause_duration_ms: float


PAUSE_PATTERN = re.compile(
    r"\[(\d+\.\d+)s\]"
    r".*?\[gc\s*\]"
    r"\s+GC\((\d+)\)"
    r"\s+Pause\s+"
    r"(\w+)"
    r"\s+\(([^)]+)\)"
    r".*?"
    r"(\d+)M->(\d+)M"
    r"\((\d+)M\)"
    r"\s+(\d+\.\d+)ms"
)


def percentile(values, pct):
    if not values:
        return 0
    sorted_v = sorted(values)
    idx = int(len(sorted_v) * pct / 100)
    idx = min(idx, len(sorted_v) - 1)
    return sorted_v[idx]


def parse_gc_log(log_path):
    pauses = []

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = PAUSE_PATTERN.search(line)
            if m:
                pauses.append(GCPause(
                    gc_id=int(m.group(2)),
                    timestamp_s=float(m.group(1)),
                    pause_type=m.group(3),
                    cause=m.group(4),
                    heap_before_mb=int(m.group(5)),
                    heap_after_mb=int(m.group(6)),
                    heap_capacity_mb=int(m.group(7)),
                    pause_duration_ms=float(m.group(8)),
                ))

    durations = [p.pause_duration_ms for p in pauses]

    by_type = {}
    for p in pauses:
        entry = by_type.setdefault(p.pause_type, {"count": 0, "total_ms": 0.0})
        entry["count"] += 1
        entry["total_ms"] = round(entry["total_ms"] + p.pause_duration_ms, 3)
    for entry in by_type.values():
        entry["mean_ms"] = round(entry["total_ms"] / entry["count"], 3) if entry["count"] else 0

    return {
        "total_pauses": len(pauses),
        "summary": {
            "total_pause_time_ms": round(sum(durations), 3) if durations else 0,
            "mean_pause_ms": round(sum(durations) / len(durations), 3) if durations else 0,
            "median_pause_ms": round(percentile(durations, 50), 3) if durations else 0,
            "p95_pause_ms": round(percentile(durations, 95), 3) if durations else 0,
            "p99_pause_ms": round(percentile(durations, 99), 3) if durations else 0,
            "max_pause_ms": round(max(durations), 3) if durations else 0,
            "min_pause_ms": round(min(durations), 3) if durations else 0,
        },
        "by_type": by_type,
        "pauses": [asdict(p) for p in pauses],
    }


def main():
    parser = argparse.ArgumentParser(description="Parse Java GC log")
    parser.add_argument("log_file", help="Path to GC log file")
    parser.add_argument("--output", "-o", help="Output JSON path (default: stdout)")

    args = parser.parse_args()
    data = parse_gc_log(args.log_file)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Parsed {data['total_pauses']} GC pauses -> {args.output}")
    else:
        json.dump(data, sys.stdout, indent=2)
        print()


if __name__ == "__main__":
    main()
