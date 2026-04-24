"""
arXiv Daily Agent
=================
Busca papers nuevos en arXiv, traduce título y abstract al español
y los envía por WhatsApp.

Corre dos veces al día (10:00 y 15:00 Chile). Si ya se envió hoy,
la segunda ejecución se omite automáticamente.

Uso:
    python main.py           → ejecuta normalmente
    python main.py --dry-run → muestra los papers pero no envía nada
"""

import sys
import os
from datetime import datetime, timezone
from fetcher import fetch_papers
from notifier import notify, format_paper_message

LOCK_FILE = os.path.join(os.path.dirname(__file__), ".last_run")


def already_ran_today() -> bool:
    """
    Revisa si el agente ya se ejecutó exitosamente hoy.
    Guarda la fecha del último envío en .last_run.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            return f.read().strip() == today
    return False


def mark_as_ran():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(LOCK_FILE, "w") as f:
        f.write(today)


def main():
    dry_run = "--dry-run" in sys.argv

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"\n{'='*50}")
    print(f"  arXiv Agent — {date_str}")
    print(f"{'='*50}\n")

    # Si ya se envió hoy, no volver a enviar
    if not dry_run and already_ran_today():
        print("Ya se envió el resumen hoy. Omitiendo.")
        return

    papers = fetch_papers()

    if not papers:
        print("Sin papers nuevos hoy.")
        if not dry_run:
            notify([], date_str)
            mark_as_ran()
        return

    print(f"\n--- {len(papers)} PAPERS ENCONTRADOS ---")
    for i, p in enumerate(papers, 1):
        print(f"\n[{i}] {p['title']}")
        print(f"     {p['published']}")

    if dry_run:
        print("\n[dry-run] Mostrando primer paper traducido:\n")
        print(format_paper_message(papers[0], 1, len(papers)))
        print("\n[dry-run] No se envió nada por WhatsApp.")
    else:
        notify(papers, date_str)
        mark_as_ran()
        print("\nListo. Resumen enviado por WhatsApp.")


if __name__ == "__main__":
    main()
