"""
Generator for scenario 4 (IoT streaming).

Writes a binary file of fixed-size 20-byte records:
    little-endian u64 timestamp_ns, u32 sensor_id, f64 value.

Edit the constants below to change scale or output path; the script takes no CLI args.
"""

import struct
import random
import sys
from pathlib import Path

# --- Configuration ---
OUTPUT_PATH = "output/scenario4_events.bin"
EVENT_COUNT = 100_000_000
SENSOR_COUNT = 1000
SEED = 42
ANOMALY_RATE = 0.02
# ---------------------

RECORD_FORMAT = "<QId"
RECORD_SIZE = 20
WRITE_BUFFER_BYTES = 1024 * 1024
PROGRESS_INTERVAL = 1_000_000


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    rng = random.Random(SEED)
    baselines = [10.0 + rng.random() * 80.0 for _ in range(SENSOR_COUNT)]

    out_path = project_root() / OUTPUT_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pack = struct.Struct(RECORD_FORMAT).pack
    expected_size = EVENT_COUNT * RECORD_SIZE

    print(f"Writing {EVENT_COUNT:,} events ({expected_size:,} bytes) to {out_path}...", flush=True)

    ts = 0
    written = 0
    with open(out_path, "wb", buffering=WRITE_BUFFER_BYTES) as f:
        for _ in range(EVENT_COUNT):
            ts += rng.randint(50, 200)
            sid = rng.randrange(SENSOR_COUNT)
            if rng.random() < ANOMALY_RATE:
                sign = 1.0 if rng.random() < 0.5 else -1.0
                value = baselines[sid] + sign * rng.uniform(5.0, 10.0)
            else:
                value = baselines[sid] + rng.gauss(0.0, 1.0)
            f.write(pack(ts, sid, value))
            written += 1
            if written % PROGRESS_INTERVAL == 0:
                print(f"  {written:,} / {EVENT_COUNT:,}", flush=True)

    actual = out_path.stat().st_size
    print(f"Done. Wrote {written:,} events, {actual:,} bytes.", flush=True)
    if actual != expected_size:
        print(f"ERROR: size mismatch (expected {expected_size:,})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
