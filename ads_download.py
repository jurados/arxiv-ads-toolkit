#!/home/jurados/arxiv-agent/venv/bin/python
"""
NASA ADS — Descargador de PDFs Open Access
============================================
Descarga PDFs de papers usando los links de acceso abierto de NASA ADS.
Prioriza arXiv (siempre gratuito) sobre otras fuentes.

Uso — paper individual:
    ads-download "2022AJ....164..195F"
    ads-download "2208.04310"                        # arXiv ID
    ads-download "2022AJ....164..195F" --dir ~/papers

Uso — desde el CSV de tu matriz:
    ads-download --from-csv matriz.csv
    ads-download --from-csv matriz.csv --dir ~/papers/matriz
"""

import json
import argparse
import urllib.request
import urllib.parse
import csv
import os
import sys
import re
import unicodedata
import time
from dotenv import load_dotenv
from utils import is_arxiv_id

load_dotenv()

ADS_TOKEN  = os.getenv("ADS_TOKEN")
ADS_API    = "https://api.adsabs.harvard.edu/v1/search/query"
ADS_LINKS  = "https://api.adsabs.harvard.edu/v1/resolver"
DEFAULT_DIR = os.path.expanduser("~/Downloads")

# Orden de preferencia de fuentes (de más a menos confiable para acceso abierto)
SOURCE_PRIORITY = [
    "ESOURCE|EPRINT_PDF",   # arXiv PDF — siempre gratuito
    "ESOURCE|ADS_PDF",      # ADS hosted PDF — gratuito
    "ESOURCE|ADS_SCAN",     # ADS scan — gratuito
    "ESOURCE|PUB_PDF",      # Publisher PDF — puede requerir suscripción
]




def arxiv_to_bibcode(arxiv_id: str) -> str | None:
    clean  = arxiv_id.replace("arXiv:", "").replace("arxiv:", "")
    params = urllib.parse.urlencode({
        "q":    f'identifier:"arXiv:{clean}"',
        "fl":   "bibcode",
        "rows": 1,
    })
    req = urllib.request.Request(
        f"{ADS_API}?{params}",
        headers={"Authorization": f"Bearer {ADS_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    docs = data.get("response", {}).get("docs", [])
    return docs[0]["bibcode"] if docs else None


def get_paper_metadata(bibcode: str) -> dict:
    """Obtiene título, año y autor para construir el nombre del archivo."""
    params = urllib.parse.urlencode({
        "q":    f"bibcode:{bibcode}",
        "fl":   "title,year,author",
        "rows": 1,
    })
    req = urllib.request.Request(
        f"{ADS_API}?{params}",
        headers={"Authorization": f"Bearer {ADS_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    docs = data.get("response", {}).get("docs", [])
    return docs[0] if docs else {}


def get_papers_metadata_batch(bibcodes: list) -> dict:
    """Fetch title, year, author for a list of bibcodes in a single ADS call.
    Returns a dict keyed by bibcode."""
    if not bibcodes:
        return {}
    q = " OR ".join(f"bibcode:{bc}" for bc in bibcodes)
    params = urllib.parse.urlencode({
        "q":    q,
        "fl":   "bibcode,title,year,author",
        "rows": len(bibcodes),
    })
    req = urllib.request.Request(
        f"{ADS_API}?{params}",
        headers={"Authorization": f"Bearer {ADS_TOKEN}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
        docs = data.get("response", {}).get("docs", [])
        return {d["bibcode"]: d for d in docs if "bibcode" in d}
    except Exception:
        return {}


def fetch_pdf_bytes(pdf_url: str) -> bytes | None:
    """Fetch raw PDF bytes from a URL. Returns None if not a PDF or on network error."""
    req = urllib.request.Request(pdf_url, headers={"User-Agent": "Mozilla/5.0 (arxiv-ads-toolkit)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        return data if data[:4] == b"%PDF" else None
    except Exception:
        return None


def get_pdf_url(bibcode: str) -> tuple[str | None, str]:
    """
    Consulta el resolver de ADS y devuelve (url_pdf, tipo_fuente).
    Sigue el orden de prioridad: arXiv > ADS > Publisher.
    """
    url = f"{ADS_LINKS}/{urllib.parse.quote(bibcode)}/esource"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {ADS_TOKEN}"})

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
    except Exception:
        return None, ""

    records = data.get("links", {}).get("records", [])
    link_map = {r["link_type"]: r["url"] for r in records}

    for source in SOURCE_PRIORITY:
        if source in link_map:
            return link_map[source], source.replace("ESOURCE|", "")

    return None, ""


def make_filename(bibcode: str, metadata: dict) -> str:
    """
    Genera un nombre de archivo legible:
    YYYY_PrimerApellido_PrimeraPalabraTitulo.pdf
    Ej: 2022_Forster_DELIGHT.pdf
    """
    year   = metadata.get("year", "????")
    authors = metadata.get("author", [])
    title   = metadata.get("title",  ["unknown"])[0] if metadata.get("title") else "unknown"

    # Primer apellido del autor principal (antes de la coma)
    if authors:
        last_name = authors[0].split(",")[0].strip()
        last_name = unicodedata.normalize("NFC", last_name)
        last_name = re.sub(r"[^\w]", "", last_name)   # solo alfanumérico
    else:
        last_name = "Unknown"

    # Primera palabra significativa del título (>= 3 letras, no artículo)
    skip = {"the", "a", "an", "of", "in", "on", "for", "and"}
    words = [w for w in re.findall(r"[A-Za-z]{3,}", title) if w.lower() not in skip]
    short_title = words[0] if words else "paper"

    return f"{year}_{last_name}_{short_title}.pdf"


def download_pdf(bibcode: str, output_dir: str) -> bool:
    """
    Descarga el PDF de un paper al directorio indicado.
    Devuelve True si tuvo éxito.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Resolver arXiv ID si es necesario
    if is_arxiv_id(bibcode):
        resolved = arxiv_to_bibcode(bibcode)
        if not resolved:
            print(f"  ✗ No se encontró {bibcode} en ADS")
            return False
        bibcode = resolved

    # Metadatos para el nombre del archivo
    metadata = get_paper_metadata(bibcode)
    filename  = make_filename(bibcode, metadata)
    filepath  = os.path.join(output_dir, filename)

    # Saltar si ya existe
    if os.path.exists(filepath):
        print(f"  → Ya existe: {filename}")
        return True

    # Obtener URL del PDF
    pdf_url, source = get_pdf_url(bibcode)
    if not pdf_url:
        print(f"  ✗ Sin PDF de acceso abierto: {bibcode}")
        return False

    title = metadata.get("title", [""])[0][:55] if metadata.get("title") else bibcode
    print(f"  ↓ [{source}] {title}")

    content = fetch_pdf_bytes(pdf_url)
    if content is None:
        print(f"  ✗ Sin PDF válido (paywall o error de red): {bibcode}")
        return False

    with open(filepath, "wb") as f:
        f.write(content)
    print(f"  ✓ Guardado: {filename} ({len(content) // 1024} KB)")
    return True


def download_from_csv(csv_path: str, output_dir: str):
    """Lee el CSV de la matriz y descarga los PDFs de todos los papers."""
    if not os.path.exists(csv_path):
        print(f"ERROR: No se encontró {csv_path}")
        sys.exit(1)

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    bibcodes = [r["bibcode"] for r in rows if r.get("bibcode")]
    print(f"  {len(bibcodes)} papers en la matriz → intentando descargar PDFs\n")

    success = 0
    failed  = 0
    skipped = 0

    for i, bibcode in enumerate(bibcodes, 1):
        print(f"[{i:03d}/{len(bibcodes)}] {bibcode}")
        result = download_pdf(bibcode, output_dir)
        if result:
            success += 1
        else:
            failed += 1
        time.sleep(0.5)   # pausa para no saturar la API

    print(f"\n{'='*50}")
    print(f"  Descargados: {success}  |  Sin acceso abierto: {failed}")
    print(f"  Directorio: {output_dir}")


def main():
    if not ADS_TOKEN:
        print("ERROR: Falta ADS_TOKEN en el archivo .env")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Descarga PDFs de papers desde NASA ADS (acceso abierto)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("bibcode",       nargs="?",  help="Bibcode o arXiv ID del paper")
    group.add_argument("--from-csv",    metavar="CSV", help="Descargar todos los papers de un CSV")

    parser.add_argument("--dir", default=DEFAULT_DIR,
                        help=f"Directorio de descarga (default: {DEFAULT_DIR})")

    args = parser.parse_args()

    output_dir = os.path.expanduser(args.dir)
    print(f"Directorio de descarga: {output_dir}\n")

    if args.from_csv:
        download_from_csv(args.from_csv, output_dir)
    else:
        download_pdf(args.bibcode, output_dir)


if __name__ == "__main__":
    main()
