import requests
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import WHATSAPP_NUMBER

WHATSAPP_API = "http://localhost:8080/api"


def translate_to_spanish(text: str) -> str:
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="en", target="es").translate(text)
    except Exception:
        return text


def send_whatsapp(message: str) -> bool:
    try:
        response = requests.post(
            f"{WHATSAPP_API}/send",
            json={"recipient": WHATSAPP_NUMBER, "message": message},
            timeout=10,
        )
        return response.json().get("success", False)
    except Exception as e:
        print(f"[notifier] Error enviando WhatsApp: {e}")
        return False


def _translate_paper(paper: dict, index: int, total: int) -> tuple[int, str]:
    """Translate a single paper and return (index, formatted_message)."""
    abstract = translate_to_spanish(paper["abstract"])
    if len(abstract) > 800:
        abstract = abstract[:800] + "..."

    authors = ", ".join(paper["authors"][:3])
    if len(paper["authors"]) > 3:
        authors += f" +{len(paper['authors']) - 3} más"

    msg = (
        f"*[{index}/{total}] {paper['title']}*\n\n"
        f"{abstract}\n\n"
        f"👥 {authors}\n"
        f"📅 {paper['published']}\n"
        f"🔗 {paper['url']}"
    )
    return index, msg


def format_paper_message(paper: dict, index: int, total: int) -> str:
    """Single-paper format (kept for dry-run preview use)."""
    _, msg = _translate_paper(paper, index, total)
    return msg


def notify(papers: list, date_str: str) -> bool:
    """Translate all papers in parallel, then send sequentially. Returns True on success."""
    total = len(papers)
    print(f"[notifier] Traduciendo {total} paper(s) en paralelo...")

    # Translate all abstracts concurrently (up to 6 workers)
    messages: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=min(6, total)) as pool:
        futures = {pool.submit(_translate_paper, p, i, total): i
                   for i, p in enumerate(papers, 1)}
        for fut in as_completed(futures):
            idx, msg = fut.result()
            messages[idx] = msg

    print(f"[notifier] Enviando {total + 2} mensajes por WhatsApp...")

    header = (
        f"🔭 *arXiv Daily — {date_str}*\n"
        f"📄 {total} paper(s) nuevo(s) en supernovas, transientes y ML\n"
        f"{'─' * 30}"
    )
    if not send_whatsapp(header):
        return False

    for i in range(1, total + 1):
        print(f"  [{i}/{total}] Enviando...")
        sent = send_whatsapp(messages[i])
        print(f"  {'✓' if sent else '✗'}")

    send_whatsapp("─── Fin del resumen diario ───")
    return True
