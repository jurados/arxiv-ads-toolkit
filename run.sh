#!/bin/bash
if ! systemctl --user is-active --quiet whatsapp-bridge 2>/dev/null; then
    echo "  ⚠️  whatsapp-bridge is not running — notifications won't be delivered"
    echo "      Start it: systemctl --user start whatsapp-bridge"
    echo ""
fi
cd /home/jurados/arxiv-agent
/home/jurados/arxiv-agent/venv/bin/python main.py
