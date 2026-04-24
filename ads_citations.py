#!/home/jurados/arxiv-agent/venv/bin/python
"""
NASA ADS — Ver Citaciones de un Paper
======================================
Dado un bibcode o ID de arXiv, muestra todos los papers
que citan ese trabajo.

Uso:
    ads-citations 2022AJ....164..195F           # bibcode
    ads-citations 2204.05018                    # ID de arXiv
    ads-citations 2022AJ....164..195F --year 2023-2026
    ads-citations 2022AJ....164..195F --rows 50
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
    clean  = identifier.replace("arXiv:", "").replace("arxiv:", "")
    parts  = clean.split(".")
    return len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit()


def arxiv_to_bibcode(arxiv_id: str) -> tuple[str | None, str | None]:
    """Convierte un arXiv ID a bibcode. Devuelve (bibcode, título)."""
    clean  = arxiv_id.replace("arXiv:", "").replace("arxiv:", "")
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
        return None, None

    bibcode = docs[0]["bibcode"]
    title   = docs[0].get("title", ["?"])[0]
    return bibcode, title


def fetch_citations(bibcode: str, year: str = None, rows: int = 200) -> tuple[list, int]:
    """
    Obtiene todos los papers que citan el paper con ese bibcode.

    La query citations(bibcode:XXXX) le dice a ADS:
    'dame todos los papers que tienen a XXXX en su bibliografía'
    """
    query = f"citations(bibcode:{bibcode})"

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


def display_results(papers: list, total: int, bibcode: str, paper_title: str, year: str = None):
    filtro = f" | filtro: {year}" if year else ""
    print(f"\n{'='*60}")
    print(f"  Citaciones de: {bibcode}")
    if paper_title:
        wrapped = textwrap.shorten(paper_title, width=55)
        print(f"  \"{wrapped}\"")
    print(f"  {total} citación(es) total{filtro} | mostrando {len(papers)}")
    print(f"{'='*60}")

    if not papers:
        print("\nNadie ha citado este paper aún (o es muy reciente).")
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
        description="Muestra todos los papers que citan un trabajo dado."
    )
    parser.add_argument("identifier", help="Bibcode (2022AJ....164..195F) o ID de arXiv (2204.05018)")
    parser.add_argument("--year",     help="Filtrar citaciones por año o rango: 2023 o 2020-2023", default=None)
    parser.add_argument("--rows",   help="Máximo de resultados a mostrar (default: 200)", type=int, default=200)
    parser.add_argument("--export", help="Exportar resultados a CSV (ej: --export matriz.csv)", default=None)

    args = parser.parse_args()

    paper_title = None

    if is_arxiv_id(args.identifier):
        print(f"Buscando bibcode para arXiv:{args.identifier}...")
        bibcode, paper_title = arxiv_to_bibcode(args.identifier)
        if not bibcode:
            print(f"ERROR: No se encontró arXiv:{args.identifier} en NASA ADS.")
            sys.exit(1)
        print(f"[→] Bibcode: {bibcode}")
        if paper_title:
            print(f"    {paper_title[:70]}")
    else:
        bibcode = args.identifier

    print(f"\nBuscando papers que citan {bibcode}...")
    papers, total = fetch_citations(bibcode, args.year, args.rows)
    display_results(papers, total, bibcode, paper_title, args.year)

    if args.export:
        papers_to_csv(papers, args.export)


if __name__ == "__main__":
    main()
