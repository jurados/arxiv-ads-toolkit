#!/home/jurados/arxiv-agent/venv/bin/python
"""
NASA ADS — Búsqueda por Similitud
==================================
Encuentra papers similares dado un bibcode o un párrafo/abstract.

Modo bibcode (similitud semántica real de ADS):
    ads-similar --bibcode 2022AJ....164..195F
    ads-similar --bibcode 2022AJ....164..195F --year 2020-2026

Modo texto (extrae términos clave del párrafo y busca):
    ads-similar --text "We use a recurrent neural network to classify supernovae light curves from ZTF"
    ads-similar --text "párrafo de tu paper" --year 2022-2026 --rows 15

Modo archivo (pega el texto en un .txt y pásalo):
    ads-similar --file mi_abstract.txt
    ads-similar --file mi_abstract.txt --export matriz.csv
"""

import json
import argparse
import urllib.request
import urllib.parse
import textwrap
import os
import sys
import re
from dotenv import load_dotenv
from exporter import papers_to_csv
from utils import pubdate_filter

load_dotenv()

ADS_TOKEN = os.getenv("ADS_TOKEN")
ADS_API   = "https://api.adsabs.harvard.edu/v1/search/query"

# Palabras vacías en inglés y español que no aportan a la búsqueda
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "this", "that", "these", "those", "we", "our",
    "us", "they", "their", "it", "its", "as", "which", "who", "when",
    "where", "how", "what", "than", "then", "here", "also", "both", "each",
    "all", "such", "into", "through", "using", "used", "use", "show", "shown",
    "present", "presents", "find", "found", "can", "not", "more", "most",
    "while", "between", "up", "well", "new", "high", "large", "based",
    "number", "results", "data", "sample", "paper", "work", "method",
    "approach", "model", "models", "set", "given", "two", "three", "one",
    "first", "second", "however", "although", "thus", "therefore",
}


def extract_keywords(text: str, top_n: int = 8) -> list[str]:
    """
    Extrae los términos más relevantes de un texto.

    Estrategia:
    1. Limpia el texto (quita puntuación, números sueltos)
    2. Elimina stop words
    3. Queda con palabras >= 5 caracteres
    4. Cuenta frecuencias y devuelve las top_n más frecuentes

    Para texto científico esto funciona bien porque los términos
    técnicos (supernovae, photometric, transient, classification)
    son largos y aparecen varias veces.
    """
    # Normalizar: minúsculas, quitar puntuación excepto guiones
    text  = text.lower()
    words = re.findall(r"[a-z][a-z\-]{3,}", text)

    # Filtrar stop words y palabras muy cortas
    words = [w for w in words if w not in STOP_WORDS and len(w) >= 5]

    # Contar frecuencias
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    # Ordenar por frecuencia y devolver top_n
    sorted_words = sorted(freq, key=freq.get, reverse=True)
    return sorted_words[:top_n]


def build_text_query(keywords: list[str], year: str = None) -> str:
    """
    Construye una query ADS buscando los keywords en título O abstract.
    Cuantos más keywords coincidan, más relevante será el resultado (OR).
    """
    kw_parts = " OR ".join(f'abs:"{k}" OR title:"{k}"' for k in keywords)
    query    = f"({kw_parts})"

    if year:
        query += f" {pubdate_filter(year)}"

    return query


def search_similar_bibcode(bibcode: str, year: str = None, rows: int = 20) -> tuple[list, int]:
    """Usa el operador similar() de ADS para similitud semántica real."""
    query = f"similar(bibcode:{bibcode})"

    if year:
        query += f" {pubdate_filter(year)}"

    params = urllib.parse.urlencode({
        "q":    query,
        "fl":   "title,bibcode,year,author,doctype,abstract,citation_count,doi,identifier",
        "rows": rows,
        "sort": "score desc",
    })
    req = urllib.request.Request(
        f"{ADS_API}?{params}",
        headers={"Authorization": f"Bearer {ADS_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    response = data.get("response", {})
    return response.get("docs", []), response.get("numFound", 0)


def search_similar_text(text: str, year: str = None, rows: int = 20) -> tuple[list, int, list]:
    """Extrae keywords del texto y busca en ADS."""
    keywords = extract_keywords(text)
    if not keywords:
        return [], 0, []
    query    = build_text_query(keywords, year)

    params = urllib.parse.urlencode({
        "q":    query,
        "fl":   "title,bibcode,year,author,doctype,abstract,citation_count,doi,identifier",
        "rows": rows,
        "sort": "score desc",
    })
    req = urllib.request.Request(
        f"{ADS_API}?{params}",
        headers={"Authorization": f"Bearer {ADS_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    response = data.get("response", {})
    return response.get("docs", []), response.get("numFound", 0), keywords


def display_results(papers: list, total: int, mode: str, source: str, year: str = None):
    filtro = f" | filtro: {year}" if year else ""
    print(f"\n{'='*60}")
    print(f"  Papers similares — modo: {mode}")
    print(f"  Fuente: {textwrap.shorten(source, 55)}")
    print(f"  {total} resultado(s) total{filtro} | mostrando {len(papers)}")
    print(f"{'='*60}")

    if not papers:
        print("\nSin resultados. Prueba con otros términos.")
        return

    for i, paper in enumerate(papers, 1):
        title    = paper.get("title",    ["Sin título"])[0]
        bibcode  = paper.get("bibcode",  "")
        year_p   = paper.get("year",     "?")
        authors  = paper.get("author",   [])
        doctype  = paper.get("doctype",  "?")
        abstract = paper.get("abstract", "Abstract no disponible.")

        url = f"https://ui.adsabs.harvard.edu/abs/{urllib.parse.quote(bibcode)}"

        first_author = authors[0] if authors else "?"

        abstract_short   = abstract[:500] + ("..." if len(abstract) > 500 else "")
        abstract_wrapped = textwrap.fill(
            abstract_short, width=70,
            initial_indent="      ",
            subsequent_indent="      ",
        )

        print(f"\n[{i:02d}] {title}")
        print(f"       Año: {year_p}  |  Tipo: {doctype}")
        print(f"       Autor principal: {first_author}")
        print(f"       🔗 {url}")
        print(f"\n       Abstract:")
        print(abstract_wrapped)
        print(f"\n       {'─'*56}")


def main():
    if not ADS_TOKEN:
        print("ERROR: Falta ADS_TOKEN en el archivo .env")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Encuentra papers similares dado un bibcode o texto."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bibcode", help="Bibcode del paper de referencia")
    group.add_argument("--text",    help="Párrafo o abstract para buscar similares")
    group.add_argument("--file",    help="Archivo .txt con el párrafo o abstract")

    parser.add_argument("--year",   help="Año o rango: 2023 o 2020-2023", default=None)
    parser.add_argument("--rows",   help="Número de resultados (default: 20)", type=int, default=20)
    parser.add_argument("--export", help="Exportar a CSV (ej: --export matriz.csv)", default=None)

    args = parser.parse_args()

    if args.bibcode:
        print(f"Buscando papers similares a {args.bibcode}...")
        papers, total = search_similar_bibcode(args.bibcode, args.year, args.rows)
        # El primer resultado suele ser el mismo paper — lo omitimos
        papers = [p for p in papers if p.get("bibcode") != args.bibcode]
        display_results(papers, total, "bibcode (similitud ADS)", args.bibcode, args.year)

    elif args.file:
        if not os.path.exists(args.file):
            print(f"ERROR: No se encontró el archivo {args.file}")
            sys.exit(1)
        with open(args.file) as f:
            text = f.read().strip()
        print(f"Extrayendo keywords de {args.file}...")
        papers, total, keywords = search_similar_text(text, args.year, args.rows)
        print(f"Keywords extraídos: {', '.join(keywords)}")
        display_results(papers, total, "texto (keywords extraídos)", args.file, args.year)

    else:  # --text
        print("Extrayendo keywords del texto...")
        papers, total, keywords = search_similar_text(args.text, args.year, args.rows)
        print(f"Keywords extraídos: {', '.join(keywords)}")
        display_results(papers, total, "texto (keywords extraídos)", args.text, args.year)

    if args.export and papers:
        papers_to_csv(papers, args.export)


if __name__ == "__main__":
    main()
