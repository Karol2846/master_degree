"""
Generator for scenario 2 (I/O - CSV filter).

Writes a CSV file simulating transaction data (~5 GB, 50M rows).
Edit the constants below to adjust scale or output path; the script takes no CLI args.
"""

import random
import sys
from pathlib import Path

# --- Configuration ---
OUTPUT_PATH = "output/scenario2_transactions.csv"
ROW_COUNT = 50_000_000
SEED = 42
WRITE_BUFFER_BYTES = 1024 * 1024
PROGRESS_INTERVAL = 1_000_000
CATEGORIES = ["RETAIL", "TRANSFER", "SALARY", "INVESTMENT", "UTILITY"]
TIMESTAMP_BASE_MS = 1_700_000_000_000
TIMESTAMP_STEP_MIN = 10
TIMESTAMP_STEP_MAX = 1000
# ---------------------

HEADER = "transaction_id,timestamp_ms,amount,sender_id,receiver_id,category,description\n"


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    rng = random.Random(SEED)
    out_path = project_root() / OUTPUT_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing {ROW_COUNT:,} rows to {out_path}...", flush=True)

    ts = TIMESTAMP_BASE_MS
    written = 0
    with open(out_path, "w", newline="", buffering=WRITE_BUFFER_BYTES) as f:
        f.write(HEADER)
        for i in range(1, ROW_COUNT + 1):
            ts += rng.randint(TIMESTAMP_STEP_MIN, TIMESTAMP_STEP_MAX)
            amount = round(rng.uniform(1.0, 99999.99), 2)
            sender = f"ACC{rng.randint(0, 999_999_999_999):012d}"
            receiver = f"ACC{rng.randint(0, 999_999_999_999):012d}"
            category = rng.choice(CATEGORIES)
            ref_num = rng.randint(0, 99_999_999)
            f.write(f"{i},{ts},{amount:.2f},{sender},{receiver},{category},Payment ref #{ref_num:08d}\n")
            written += 1
            if written % PROGRESS_INTERVAL == 0:
                print(f"  {written:,} / {ROW_COUNT:,}", flush=True)

    actual = out_path.stat().st_size
    actual_gb = actual / (1024 ** 3)
    print(f"Done. Wrote {written:,} rows, {actual:,} bytes ({actual_gb:.2f} GB).", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
