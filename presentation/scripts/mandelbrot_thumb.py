"""
Thumbnail of the scenario 1 output (Mandelbrot) for the presentation.

NumPy port of rust/src/mandelbrot/generate.rs + main.rs: same complex-plane window,
same MAX_ITER, same escape test and the same polynomial colour gradient. Only the
resolution differs (1000x1000 instead of 4096x4096; the aspect ratio is kept, 1:1).

Writes presentation/assets/mandelbrot.png. Does not touch output/.

Usage:
    .venv/bin/python presentation/scripts/mandelbrot_thumb.py [--size 1000]
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

# Same constants as rust/src/mandelbrot/main.rs
MAX_ITER = 1000
RE_MIN, RE_MAX = -2.0, 1.0
IM_MIN, IM_MAX = -1.5, 1.5
ORIGINAL_WIDTH, ORIGINAL_HEIGHT = 4096, 4096

OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "mandelbrot.png"


def escape_iters(width: int, height: int) -> np.ndarray:
    # Same pixel -> plane mapping as generate.rs: px / (WIDTH - 1), py / (HEIGHT - 1); row 0 = IM_MIN.
    cx = RE_MIN + (np.arange(width) / (width - 1)) * (RE_MAX - RE_MIN)
    cy = IM_MIN + (np.arange(height) / (height - 1)) * (IM_MAX - IM_MIN)
    cx, cy = np.meshgrid(cx, cy)
    cx, cy = cx.ravel(), cy.ravel()

    iters = np.zeros(cx.size, dtype=np.uint32)
    zx = np.zeros(cx.size)
    zy = np.zeros(cx.size)
    idx = np.arange(cx.size)  # pixels still iterating

    # while iter < MAX_ITER && zx*zx + zy*zy <= 4.0 { z = z^2 + c; iter += 1 }
    for _ in range(MAX_ITER):
        keep = zx * zx + zy * zy <= 4.0
        idx, zx, zy = idx[keep], zx[keep], zy[keep]
        if idx.size == 0:
            break
        new_zx = zx * zx - zy * zy + cx[idx]
        zy = 2.0 * zx * zy + cy[idx]
        zx = new_zx
        iters[idx] += 1
    return iters.reshape(height, width)


def polynomial_color(iters: np.ndarray) -> np.ndarray:
    t = iters.astype(np.float64) / MAX_ITER
    # Rust f64::round() rounds half away from zero; all values are >= 0, so floor(x + 0.5).
    r = np.floor(9.0 * (1 - t) * t ** 3 * 255.0 + 0.5)
    g = np.floor(15.0 * (1 - t) ** 2 * t ** 2 * 255.0 + 0.5)
    b = np.floor(8.5 * (1 - t) ** 3 * t * 255.0 + 0.5)
    rgb = np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)
    rgb[iters == MAX_ITER] = 0  # points inside the set are black
    return rgb


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--size", type=int, default=1000, help="Width in px (height keeps the 4096x4096 aspect)")
    args = parser.parse_args()
    width = args.size
    height = round(width * ORIGINAL_HEIGHT / ORIGINAL_WIDTH)

    rgb = polynomial_color(escape_iters(width, height))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb, "RGB").save(OUTPUT, optimize=True)
    print(f"Wrote {OUTPUT} ({width}x{height})")


if __name__ == "__main__":
    main()
