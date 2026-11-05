#!/usr/bin/env bash
# Render a deck (default: slides.html -> prezentacja.pdf) to PDF with headless Chrome.
# Usage: presentation/scripts/build.sh [deck.html] [--png]
#   presentation/scripts/build.sh                -> prezentacja.pdf
#   presentation/scripts/build.sh obrona.html    -> obrona.pdf
#   --png also renders every page to presentation/build/png/<deck>-N.png
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DECK="slides.html"
PNG=0
for arg in "$@"; do
  case "$arg" in
    --png) PNG=1 ;;
    *.html) DECK="$arg" ;;
    *) echo "unknown argument: $arg" >&2; exit 1 ;;
  esac
done

NAME="${DECK%.html}"
[[ "$NAME" == "slides" ]] && PDF="$DIR/prezentacja.pdf" || PDF="$DIR/$NAME.pdf"

google-chrome --headless --disable-gpu --no-pdf-header-footer --virtual-time-budget=5000 \
  --print-to-pdf="$PDF" "file://$DIR/$DECK" 2>/dev/null

pdfinfo "$PDF" | grep -E "Pages|Page size"

if [[ "$PNG" == 1 ]]; then
  mkdir -p "$DIR/build/png"
  rm -f "$DIR/build/png/$NAME"-*.png
  pdftoppm -r 50 -png "$PDF" "$DIR/build/png/$NAME"
fi
