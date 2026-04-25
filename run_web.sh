#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
echo ""
echo "  🔭 arXiv Agent — Web Interface"
echo "  ──────────────────────────────"
echo "  URL: http://localhost:5000"
echo ""
if ! systemctl --user is-active --quiet whatsapp-bridge 2>/dev/null; then
    echo "  ⚠️  whatsapp-bridge is not running — WhatsApp send will fail"
    echo "      Start it: systemctl --user start whatsapp-bridge"
    echo ""
fi
"$DIR/venv/bin/python" "$DIR/app.py"
