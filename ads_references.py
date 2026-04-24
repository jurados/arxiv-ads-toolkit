#!/home/jurados/arxiv-agent/venv/bin/python
"""
NASA ADS — Extraer Referencias de un Paper
==========================================
Dado un bibcode o ID de arXiv, muestra todas las referencias
que ese paper cita.

Uso:
    ads-references 2022AJ....164..195F           # bibcode
    ads-references 2204.05018                    # ID de arXiv
    ads-references 2204.05018 --year 2020-2022   # filtrar por año
    ads-references 2204.05018 --rows 50          # más resultados
"""

import json
import argparse
import urllib.request
import urllib.parse
import textwrap
import os
import sys
from dotenv import load_dotenv
from exporter import papers_to_csv

load_dotenv()

ADS_TOKEN = os.getenv("ADS_TOKEN")
ADS_API   = "https://api.adsabs.harvard.edu/v1/search/query"


def is_arxiv_id(identifier: str) -> bool:
    """
    Detecta si el identificador es un ID de arXiv.
    arXiv IDs tienen el formato YYMM.NNNNN o YYMM.NNNNNN
    Los bibcodes empiezan con un año de 4 dígitos y contienen puntos.
    """
    clean = identifier.replace("arXiv:", "").replace("arxiv:", "")
    # Si tiene puntos y la parte antes del punto son solo dígitos → arXiv
    parts = clean.split(".")
    return len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit()


def arxiv_to_bibcode(arxiv_id: str) -> str | None:
    """
    Busca en ADS el bibcode correspondiente a un ID de arXiv.
    ADS indexa los papers de arXiv y los vincula con su bibcode oficial.
    """
    clean = arxiv_id.replace("arXiv:", "").replace("arxiv:", "")
    params = urllib.parse.urlencode({
        "q":    f'identifier:"arXiv:{clean}"',
        "fl":   "bibcode,title",
        "rows": 1,
    })
    req = urllib.request.Request(
        f"{ADS_API}?{params}",
        headers={"Authorization": f"Bearer {ADS_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)

    docs = data.get("response", {}).get("docs", [])
    if not docs:
        return None

    bibcode = docs[0]["bibcode"]
    title   = docs[0].get("title", ["?"])[0]
    print(f"[→] arXiv:{clean} encontrado como: {bibcode}")
    print(f"    {title[:70]}")
    return bibcode


def fetch_references(bibcode: str, year: str = None, rows: int = 200) -> tuple[list, int]:
    """
    Obtiene todas las referencias que cita el paper con ese bibcode.

    La query references(bibcode:XXXX) le dice a ADS:
    'dame todos los papers que aparecen en la bibliografía de XXXX'
    """
    query = f"references(bibcode:{bibcode})"

    # Filtro de año opcional
    if year:
        if "-" in year and len(year) > 4:
            start, end = year.split("-", 1)
            query += f" pubdate:[{start}-01 TO {end}-12]"
        else:
            query += f" pubdate:[{year}-01 TO {year}-12]"

    params = urllib.parse.urlencode({
        "q":    query,
        "fl":   "title,bibcode,year,author,doctype,abstract",
        "rows": rows,
        "sort": "date desc",
    })

    req = urllib.request.Request(
        f"{ADS_API}?{params}",
        headers={"Authorization": f"Bearer {ADS_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)

    response = data.get("response", {})
    return response.get("docs", []), response.get("numFound", 0)


def display_results(papers: list, total: int, bibcode: str, year: str = None):
    filtro = f" | filtro: {year}" if year else ""
    print(f"\n{'='*60}")
    print(f"  Referencias de: {bibcode}")
    print(f"  {total} referencia(s) total{filtro} | mostrando {len(papers)}")
    print(f"{'='*60}")

    if not papers:
        print("\nSin referencias encontradas.")
        return

    for i, paper in enumerate(papers, 1):
        title    = paper.get("title", ["Sin título"])[0]
        bibcode_ = paper.get("bibcode", "")
        year_p   = paper.get("year", "?")
        authors  = paper.get("author", [])
        doctype  = paper.get("doctype", "?")
        abstract = paper.get("abstract", "Abstract no disponible.")

        url = f"https://ui.adsabs.harvard.edu/abs/{urllib.parse.quote(bibcode_)}"

        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += f" +{len(authors)-3} más"

        abstract_short   = abstract[:500] + ("..." if len(abstract) > 500 else "")
        abstract_wrapped = textwrap.fill(
            abstract_short, width=70,
            initial_indent="      ",
            subsequent_indent="      ",
        )

        print(f"\n[{i:03d}] {title}")
        print(f"       Año: {year_p}  |  Tipo: {doctype}")
        print(f"       Autores: {author_str}")
        print(f"       🔗 {url}")
        print(f"\n       Abstract:")
        print(abstract_wrapped)
        print(f"\n       {'─'*56}")


def main():
    if not ADS_TOKEN:
        print("ERROR: Falta ADS_TOKEN en el archivo .env")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Extrae las referencias de un paper desde NASA ADS."
    )
    parser.add_argument("identifier", help="Bibcode (2022AJ....164..195F) o ID de arXiv (2204.05018)")
    parser.add_argument("--year",     help="Filtrar referencias por año o rango: 2023 o 2020-2023", default=None)
    parser.add_argument("--rows",   help="Máximo de referencias a mostrar (default: 200)", type=int, default=200)
    parser.add_argument("--export", help="Exportar resultados a CSV (ej: --export matriz.csv)", default=None)

    args = parser.parse_args()

    # Si es arXiv ID, primero convertimos a bibcode
    if is_arxiv_id(args.identifier):
        print(f"Buscando bibcode para arXiv:{args.identifier}...")
        bibcode = arxiv_to_bibcode(args.identifier)
        if not bibcode:
            print(f"ERROR: No se encontró el paper arXiv:{args.identifier} en NASA ADS.")
            print("Puede que sea muy reciente. Prueba con el bibcode directamente.")
            sys.exit(1)
    else:
        bibcode = args.identifier

    print(f"\nExtrayendo referencias de {bibcode}...")
    papers, total = fetch_references(bibcode, args.year, args.rows)
    display_results(papers, total, bibcode, args.year)

    if args.export:
        papers_to_csv(papers, args.export)


if __name__ == "__main__":
    main()
