#!/bin/bash
# Launcher para la interfaz web de arXiv Agent.
# Inicia Flask si no está corriendo, luego abre el browser.

URL="http://localhost:5000"
PYTHON="/home/jurados/arxiv-agent/venv/bin/python"
APP="/home/jurados/arxiv-agent/app.py"
LOG="/home/jurados/arxiv-agent/web.log"

if lsof -ti:5000 >/dev/null 2>&1; then
    # Ya está corriendo — solo abrir el browser
    xdg-open "$URL"
else
    # Arrancar Flask en background
    nohup "$PYTHON" "$APP" >> "$LOG" 2>&1 &
    # Esperar a que esté listo
    for i in $(seq 1 10); do
        sleep 0.5
        curl -s "$URL" >/dev/null 2>&1 && break
    done
    xdg-open "$URL"
fi
