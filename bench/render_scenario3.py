"""
Renders the scenario 3 trajectory (XYZ snapshots) as PNG frames and an animated GIF.
Visualisation only: run manually after the experiment, never part of the measurements.

Usage:
    rust/target/release/particles.exe --input output/scenario3_n4000.bin --steps 1000 --threads 6 --snapshot-every 10
    python bench/render_scenario3.py
    python bench/render_scenario3.py --frames 0 200 1000 --fps 15

Particles keep their colour across frames (shade = initial x position), so the melting of the
initial FCC crystal shows up as the mixing of initially flat slabs. The XYZ file can also be
opened in OVITO.
"""

import argparse
import struct
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from utils import get_project_root, load_config, results_path
from visualize import setup_style

DT = 0.005
POINT_SIZE = 2
GIF_DPI = 100
CMAP = "Blues"
CMAP_FLOOR = 0.3  # lightest shade used, so no particle fades into the white background


def read_xyz(path):
    """[(step, positions[N, 3])] from frames of: N, 'step <k>', N x 'Ar x y z'."""
    frames = []
    with open(path, "r", encoding="utf-8") as f:
        while True:
            header = f.readline()
            if not header.strip():
                break
            n = int(header)
            step = int(f.readline().split()[1])
            coords = np.array([f.readline().split()[1:4] for _ in range(n)], dtype=float)
            frames.append((step, coords))
    return frames


def read_box_length(sim_input):
    with open(sim_input, "rb") as f:
        _, box_len = struct.unpack("<Id", f.read(12))
    return box_len


def make_axes(box_len):
    fig = plt.figure(figsize=(5.0, 5.0))
    ax = fig.add_subplot(projection="3d")
    ax.set_xlim(0, box_len)
    ax.set_ylim(0, box_len)
    ax.set_zlim(0, box_len)
    ax.set_box_aspect((1, 1, 1), zoom=0.85)  # leaves room for the z label
    ax.set_xlabel("x [σ]")
    ax.set_ylabel("y [σ]")
    ax.set_zlabel("z [σ]")
    return fig, ax


def title(step):
    return f"Lennard-Jones particles: step {step} (t* = {step * DT:.2f})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render scenario 3 XYZ trajectory to PNG frames + GIF")
    parser.add_argument("--input", default="output/scenario3_snapshots_rust.xyz", help="XYZ trajectory")
    parser.add_argument("--sim-input", default="output/scenario3_n4000.bin",
                        help="Simulation input file (box length L for the axes)")
    parser.add_argument("--frames", type=int, nargs="+", default=[0, 100, 500, 1000],
                        help="Steps saved as separate PNG frames")
    parser.add_argument("--fps", type=int, default=10, help="GIF frame rate")
    parser.add_argument("--config", default=None, help="Path to config.toml (results directory)")
    args = parser.parse_args()

    root = get_project_root()
    config = load_config(args.config)
    out_dir = results_path(config, "charts", "scenario3")
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = read_xyz(root / args.input)
    if not frames:
        print(f"ERROR: no frames in {args.input}", file=sys.stderr)
        return 1
    box_len = read_box_length(root / args.sim_input)
    print(f"Read {len(frames)} frames, N = {len(frames[0][1])}, L = {box_len:.4f}")

    shade = frames[0][1][:, 0] / box_len
    colors = plt.get_cmap(CMAP)(CMAP_FLOOR + (1 - CMAP_FLOOR) * shade)

    setup_style()
    by_step = dict(frames)
    for step in args.frames:
        if step not in by_step:
            print(f"  WARNING: step {step} not in trajectory, skipped")
            continue
        fig, ax = make_axes(box_len)
        pos = by_step[step]
        ax.scatter(pos[:, 0], pos[:, 1], pos[:, 2], c=colors, s=POINT_SIZE, linewidths=0)
        ax.set_title(title(step), fontsize=11)
        out = out_dir / f"snapshot_step{step:04d}.png"
        fig.savefig(out)
        plt.close(fig)
        print(f"  Saved: {out}")

    fig, ax = make_axes(box_len)
    first = frames[0][1]
    scatter = ax.scatter(first[:, 0], first[:, 1], first[:, 2], c=colors, s=POINT_SIZE, linewidths=0)
    heading = ax.set_title(title(frames[0][0]), fontsize=11)

    def update(k):
        step, pos = frames[k]
        scatter._offsets3d = (pos[:, 0], pos[:, 1], pos[:, 2])
        heading.set_text(title(step))
        return scatter, heading

    out = out_dir / "trajectory.gif"
    anim = FuncAnimation(fig, update, frames=len(frames))
    anim.save(out, writer=PillowWriter(fps=args.fps), dpi=GIF_DPI)
    plt.close(fig)
    print(f"  Saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
