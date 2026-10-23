"""
Correctness checks for scenario 3 (run by the 'validate' phase of run_benchmarks.py).

Expects, for every language and thread count P, the per-step JSON and the final positions written
with --dump-final (u32 N, then N x (x, y, z) as little-endian f64). Criteria (all must pass):
    1. energy:      max_t |E(t) - E(0)| / |E(0)| < 1e-3 for every run
    2. determinism: final positions bytewise identical for all P (per language)
    3. Java <-> Rust: max minimum-image position difference < 1e-6 (per P)

Usage:
    python bench/validate_scenario3.py
    python bench/validate_scenario3.py --input output/scenario3_n4000.bin \\
        --steps-json "output/scenario3_steps_{lang}_n4000_p{threads}.json" --threads 1 12
"""

import argparse
import json
import struct
import sys
from pathlib import Path

ENERGY_TOLERANCE = 1e-3
POSITION_TOLERANCE = 1e-6
LANGS = ["java", "rust"]


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def fill(template, lang, threads):
    return project_root() / template.replace("{lang}", lang).replace("{threads}", str(threads))


def read_box_length(input_path):
    with open(input_path, "rb") as f:
        _, box_len = struct.unpack("<Id", f.read(12))
    return box_len


def read_final(path):
    data = path.read_bytes()
    (n,) = struct.unpack_from("<I", data)
    if len(data) != 4 + n * 24:
        raise ValueError(f"{path}: expected {4 + n * 24} bytes for N={n}, got {len(data)}")
    return n, struct.unpack_from(f"<{3 * n}d", data, 4)


def energy_drift(steps_json):
    with open(steps_json, encoding="utf-8") as f:
        energy = json.load(f)["energy"]
    e0 = energy[0]["total"]
    return max(abs(e["total"] - e0) / abs(e0) for e in energy[1:])


def max_position_diff(a, b, box_len):
    half = 0.5 * box_len
    worst = 0.0
    for u, v in zip(a, b):
        d = abs(u - v)
        if d > half:
            d = box_len - d
        worst = max(worst, d)
    return worst


def verdict(ok):
    return "PASS" if ok else "FAIL"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scenario 3 results (energy, determinism, Java vs Rust)")
    parser.add_argument("--input", default="output/scenario3_n108000.bin", help="Simulation input (for L)")
    parser.add_argument("--steps-json", default="output/scenario3_steps_{lang}_n108000_p{threads}.json")
    parser.add_argument("--final", default="output/scenario3_final_{lang}_p{threads}.bin")
    parser.add_argument("--threads", type=int, nargs="+", default=[1, 12])
    args = parser.parse_args()

    box_len = read_box_length(project_root() / args.input)
    all_ok = True

    print(f"1. Energy conservation (max |E(t) - E(0)| / |E(0)| < {ENERGY_TOLERANCE:g})")
    for lang in LANGS:
        for p in args.threads:
            drift = energy_drift(fill(args.steps_json, lang, p))
            ok = drift < ENERGY_TOLERANCE
            all_ok &= ok
            print(f"   {lang:<4} P={p:<3} drift = {drift:.3e}  {verdict(ok)}")

    print("2. Determinism across thread counts (final positions bytewise identical)")
    finals = {}
    for lang in LANGS:
        reference = fill(args.final, lang, args.threads[0]).read_bytes()
        for p in args.threads:
            finals[lang, p] = read_final(fill(args.final, lang, p))
            if p == args.threads[0]:
                continue
            ok = fill(args.final, lang, p).read_bytes() == reference
            all_ok &= ok
            print(f"   {lang:<4} P={args.threads[0]} vs P={p:<3} {'identical' if ok else 'DIFFERENT'}  {verdict(ok)}")

    print(f"3. Java vs Rust (max minimum-image position difference < {POSITION_TOLERANCE:g}, L = {box_len:.6f})")
    for p in args.threads:
        (n_java, java), (n_rust, rust) = finals["java", p], finals["rust", p]
        if n_java != n_rust:
            all_ok = False
            print(f"   P={p:<3} N differs: java {n_java}, rust {n_rust}  FAIL")
            continue
        diff = max_position_diff(java, rust, box_len)
        ok = diff < POSITION_TOLERANCE
        all_ok &= ok
        print(f"   P={p:<3} max |dx| = {diff:.3e}{' (bitwise identical)' if java == rust else ''}  {verdict(ok)}")

    print(f"\nValidation {verdict(all_ok)}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
