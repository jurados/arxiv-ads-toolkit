#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
echo ""
echo "  🔭 arXiv Agent — Web Interface"
echo "  ──────────────────────────────"
echo "  URL: http://localhost:5000"
echo ""
"$DIR/venv/bin/python" "$DIR/app.py"
