"""
Generator for scenario 3 (Lennard-Jones particles, LAMMPS "LJ" benchmark parameters).

Writes an FCC lattice of n x n x n unit cells (N = 4 n^3) with Maxwell-Boltzmann velocities:
    little-endian u32 N, f64 L, then N x (x, y, z, vx, vy, vz) as f64.

Usage:
    python bench/gen_scenario3.py --cells 30 --output output/scenario3_n108000.bin
    python bench/gen_scenario3.py --cells 10 --output output/scenario3_n4000.bin
"""

import argparse
import random
import struct
import sys
from pathlib import Path

# --- Configuration ---
SEED = 42
DENSITY = 0.8442
TEMPERATURE = 1.44
# ---------------------

FCC_BASIS = [(0.0, 0.0, 0.0), (0.5, 0.5, 0.0), (0.5, 0.0, 0.5), (0.0, 0.5, 0.5)]
HEADER_FORMAT = "<Id"
RECORD_FORMAT = "<6d"
WRITE_BUFFER_BYTES = 1024 * 1024


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def fcc_positions(cells: int, a: float):
    # z slowest, x fastest: consecutive indices are spatial neighbours (same order as the cell index).
    positions = []
    for iz in range(cells):
        for iy in range(cells):
            for ix in range(cells):
                for bx, by, bz in FCC_BASIS:
                    positions.append(((ix + bx) * a, (iy + by) * a, (iz + bz) * a))
    return positions


def maxwell_boltzmann(n: int, rng: random.Random):
    velocities = [[rng.gauss(0.0, 1.0) for _ in range(3)] for _ in range(n)]

    # Zero total momentum (m = 1).
    for d in range(3):
        mean = sum(v[d] for v in velocities) / n
        for v in velocities:
            v[d] -= mean

    # Rescale to the target temperature, T = sum(v^2) / (3 (N - 1)).
    sum_v2 = sum(v[0] * v[0] + v[1] * v[1] + v[2] * v[2] for v in velocities)
    scale = (TEMPERATURE * 3 * (n - 1) / sum_v2) ** 0.5
    for v in velocities:
        v[0] *= scale
        v[1] *= scale
        v[2] *= scale
    return velocities


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate scenario 3 input (FCC lattice + MB velocities)")
    parser.add_argument("--cells", type=int, required=True, help="FCC unit cells per dimension (N = 4 n^3)")
    parser.add_argument("--output", required=True, help="Output path (relative to the project root)")
    args = parser.parse_args()

    if args.cells < 1:
        print("ERROR: --cells must be positive", file=sys.stderr)
        return 1

    a = (4.0 / DENSITY) ** (1.0 / 3.0)
    box_len = args.cells * a
    positions = fcc_positions(args.cells, a)
    n = len(positions)
    velocities = maxwell_boltzmann(n, random.Random(SEED))

    out_path = project_root() / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    expected_size = struct.calcsize(HEADER_FORMAT) + n * struct.calcsize(RECORD_FORMAT)

    print(f"Writing N={n:,} particles (a={a:.6f}, L={box_len:.6f}) to {out_path}...", flush=True)

    pack = struct.Struct(RECORD_FORMAT).pack
    with open(out_path, "wb", buffering=WRITE_BUFFER_BYTES) as f:
        f.write(struct.pack(HEADER_FORMAT, n, box_len))
        for (x, y, z), (vx, vy, vz) in zip(positions, velocities):
            f.write(pack(x, y, z, vx, vy, vz))

    actual = out_path.stat().st_size
    temperature = sum(vx * vx + vy * vy + vz * vz for vx, vy, vz in velocities) / (3 * (n - 1))
    print(f"Done. Wrote {actual:,} bytes, T = {temperature:.6f}.", flush=True)
    if actual != expected_size:
        print(f"ERROR: size mismatch (expected {expected_size:,})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
