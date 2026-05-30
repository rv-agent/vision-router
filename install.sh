#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
pip install --break-system-packages -r "$DIR/requirements.txt" -q
pip install --break-system-packages -e "$DIR" -q
echo "✅ vision-router installed!"
echo "   CLI: vision analyze image.jpg \"prompt\""
echo "   Web: vision serve  →  http://localhost:5050"
