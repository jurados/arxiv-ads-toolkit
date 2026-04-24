import requests
import sys
from config import WHATSAPP_NUMBER

WHATSAPP_API = "http://localhost:8080/api"


def translate_to_spanish(text: str) -> str:
    """
    Traduce texto al español usando Google Translate (gratis, sin API key).
    Si falla por cualquier motivo, devuelve el texto original en inglés.
    """
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="en", target="es").translate(text)
    except Exception:
        return text  # fallback: inglés original


def send_whatsapp(message: str) -> bool:
    try:
        response = requests.post(
            f"{WHATSAPP_API}/send",
            json={"recipient": WHATSAPP_NUMBER, "message": message},
            timeout=10,
        )
        return response.json().get("success", False)
    except Exception as e:
        print(f"[notifier] Error enviando WhatsApp: {e}", file=sys.stderr)
        return False


def format_paper_message(paper: dict, index: int, total: int) -> str:
    """
    Formatea un paper como mensaje de WhatsApp.
    Traduce título y abstract al español si es posible.
    """
    title = paper["title"]
    abstract = translate_to_spanish(paper["abstract"])

    # Truncamos el abstract a 800 caracteres para no saturar el mensaje
    if len(abstract) > 800:
        abstract = abstract[:800] + "..."

    authors = ", ".join(paper["authors"][:3])
    if len(paper["authors"]) > 3:
        authors += f" +{len(paper['authors']) - 3} más"

    return (
        f"*[{index}/{total}] {title}*\n\n"
        f"{abstract}\n\n"
        f"👥 {authors}\n"
        f"📅 {paper['published']}\n"
        f"🔗 {paper['url']}"
    )


def notify(papers: list, date_str: str):
    if not papers:
        send_whatsapp(f"🔭 arXiv {date_str}: No hay papers nuevos hoy con tus keywords.")
        return

    total = len(papers)
    print(f"[notifier] Enviando {total + 2} mensajes por WhatsApp...")

    # Encabezado
    header = (
        f"🔭 *arXiv Daily — {date_str}*\n"
        f"📄 {total} paper(s) nuevo(s) en supernovas, transientes y ML\n"
        f"{'─' * 30}"
    )
    send_whatsapp(header)

    # Un mensaje por paper
    for i, paper in enumerate(papers, 1):
        print(f"  [{i}/{total}] Traduciendo y enviando...")
        msg = format_paper_message(paper, i, total)
        ok = send_whatsapp(msg)
        print(f"  {'✓' if ok else '✗'} Enviado")

    send_whatsapp("─── Fin del resumen diario ───")
