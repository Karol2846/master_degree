#!/usr/bin/env bash
# Render presentation/slides.html to presentation/prezentacja.pdf with headless Chrome.
# Usage: presentation/scripts/build.sh [--png]   (--png also renders every page to presentation/build/png/)
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PDF="$DIR/prezentacja.pdf"

google-chrome --headless --disable-gpu --no-pdf-header-footer --virtual-time-budget=5000 \
  --print-to-pdf="$PDF" "file://$DIR/slides.html" 2>/dev/null

pdfinfo "$PDF" | grep -E "Pages|Page size"

if [[ "${1:-}" == "--png" ]]; then
  rm -rf "$DIR/build/png" && mkdir -p "$DIR/build/png"
  pdftoppm -r 50 -png "$PDF" "$DIR/build/png/slide"
fi
