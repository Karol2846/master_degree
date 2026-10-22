"""Tile rendered slide PNGs (presentation/build/png) into contact sheets for review.

Usage: .venv/bin/python presentation/scripts/contact_sheet.py OUT_DIR [PER_SHEET]
"""
import sys
from pathlib import Path

from PIL import Image

src = Path(__file__).resolve().parents[1] / "build" / "png"
out = Path(sys.argv[1])
per = int(sys.argv[2]) if len(sys.argv) > 2 else 6
out.mkdir(parents=True, exist_ok=True)
files = sorted(src.glob("slide-*.png"))
for k in range(0, len(files), per):
    ims = [Image.open(f).convert("RGB") for f in files[k:k + per]]
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * 2 + 10, (h + 10) * ((len(ims) + 1) // 2)), "#888")
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % 2) * (w + 10), (i // 2) * (h + 10)))
    sheet.save(out / f"sheet_{k // per + 1:02d}.png")
    print(out / f"sheet_{k // per + 1:02d}.png")
