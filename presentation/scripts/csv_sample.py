"""
First rows of the scenario 2 input, reproduced in memory for the presentation.

Replays the RNG sequence of bench/gen_scenario2.py (same seed, same order of rng calls)
for the first few rows only; the 5 GB file is not generated and output/ is not touched.
Expected total size is computed from the format (fixed-width fields + variable-width
transaction_id/amount), not from a generated file.

Writes presentation/assets/csv_sample.json.

Usage:
    .venv/bin/python presentation/scripts/csv_sample.py [--rows 3]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True  # do not write __pycache__ into bench/
sys.path.insert(0, str(ROOT / "bench"))
import gen_scenario2 as gen  # noqa: E402  (constants only; main() is not called)

OUTPUT = ROOT / "presentation" / "assets" / "csv_sample.json"


def rows(count: int):
    # Identical to the loop body of gen_scenario2.main().
    rng = gen.random.Random(gen.SEED)
    ts = gen.TIMESTAMP_BASE_MS
    for i in range(1, count + 1):
        ts += rng.randint(gen.TIMESTAMP_STEP_MIN, gen.TIMESTAMP_STEP_MAX)
        amount = round(rng.uniform(1.0, 99999.99), 2)
        sender = f"ACC{rng.randint(0, 999_999_999_999):012d}"
        receiver = f"ACC{rng.randint(0, 999_999_999_999):012d}"
        category = rng.choice(gen.CATEGORIES)
        ref_num = rng.randint(0, 99_999_999)
        yield f"{i},{ts},{amount:.2f},{sender},{receiver},{category},Payment ref #{ref_num:08d}"


def expected_size_bytes(n: int) -> float:
    """Approximate file size: exact for the integer columns, expected value for the rest."""
    # transaction_id: sum of decimal lengths of 1..n
    id_chars, lo, digits = 0, 1, 1
    while lo <= n:
        hi = min(n, lo * 10 - 1)
        id_chars += (hi - lo + 1) * digits
        lo, digits = lo * 10, digits + 1
    ts_chars = 13  # 1.7e12 + at most 50M * 1000 ms stays 13 digits
    # amount ~ U(1, 99999.99) printed with 2 decimals: "d.dd" .. "ddddd.dd"
    span = 99999.99 - 1.0
    amount_chars = sum(((min(10 ** k, 99999.99) - max(10 ** (k - 1), 1.0)) / span) * (k + 3) for k in range(1, 6))
    acc_chars = 2 * 15
    cat_chars = sum(len(c) for c in gen.CATEGORIES) / len(gen.CATEGORIES)
    desc_chars = len("Payment ref #") + 8
    commas_newline = 6 + 1
    per_row = ts_chars + amount_chars + acc_chars + cat_chars + desc_chars + commas_newline
    return len(gen.HEADER) + id_chars + n * per_row


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce the first rows of the scenario 2 CSV")
    parser.add_argument("--rows", type=int, default=3)
    args = parser.parse_args()

    size = expected_size_bytes(gen.ROW_COUNT)
    data = {
        "header": gen.HEADER.rstrip("\n"),
        "rows": list(rows(args.rows)),
        "seed": gen.SEED,
        "total_rows": gen.ROW_COUNT,
        "approx_size_gb": round(size / 1024 ** 3, 2),
        "approx_size_gb_decimal": round(size / 1e9, 2),
        "filter_column": "amount",
        "filter": "top 1% by amount: threshold = sorted(amounts)[int(N * 0.99)], rows with amount >= threshold are written",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
