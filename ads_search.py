#!/home/jurados/arxiv-agent/venv/bin/python
"""
NASA ADS Search
===============
Busca artículos, tesis y libros de un autor en NASA ADS.
Muestra título, abstract y enlace.

Uso:
    ads-search "Apellido, Nombre"
    ads-search "Apellido, Nombre" --year 2023
    ads-search "Apellido, Nombre" --first-author
    ads-search "Apellido, Nombre" --year 2023 --first-author
"""

import sys
import json
import argparse
import urllib.request
import urllib.parse
from dotenv import load_dotenv
import os
import textwrap
from exporter import papers_to_csv

load_dotenv()

ADS_TOKEN  = os.getenv("ADS_TOKEN")
ADS_API    = "https://api.adsabs.harvard.edu/v1/search/query"
DOCTYPES   = ["article", "thesis", "book"]


def pubdate_filter(year: str) -> str:
    """
    Convierte un año o rango de años al filtro pubdate de ADS.

    Ejemplos:
      "2023"       → pubdate:[2023-01 TO 2023-12]
      "2020-2023"  → pubdate:[2020-01 TO 2023-12]
    """
    if "-" in year and len(year) > 4:   # es un rango: "2020-2023"
        start, end = year.split("-", 1)
        return f"pubdate:[{start}-01 TO {end}-12]"
    return f"pubdate:[{year}-01 TO {year}-12]"


def search_author(author: str, year: str = None, first_author: bool = False, rows: int = 100) -> list:
    """
    Consulta NASA ADS filtrando por autor, año o rango de años (opcional)
    y solo doctype article, thesis o book.

    Si first_author=True usa el prefijo ^ de ADS, que restringe
    la búsqueda a papers donde ese autor aparece en primera posición.
    """
    doctype_filter = " OR ".join(f"doctype:{d}" for d in DOCTYPES)
    prefix = "^" if first_author else ""
    query = f'author:"{prefix}{author}" ({doctype_filter})'
    if year:
        query += f" {pubdate_filter(year)}"

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

    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data.get("response", {}).get("docs", [])


def display_results(papers: list, author: str, year: str = None, first_author: bool = False):
    filtro = author + (f" ({year})" if year else "")
    modo   = "solo primer autor" if first_author else "cualquier posición"
    print(f"\n{'='*60}")
    print(f"  NASA ADS — {filtro}")
    print(f"  {len(papers)} resultado(s)  |  artículos, tesis y libros  |  {modo}")
    print(f"{'='*60}")

    if not papers:
        print("\nSin resultados.")
        return

    for i, paper in enumerate(papers, 1):
        title    = paper.get("title", ["Sin título"])[0]
        bibcode  = paper.get("bibcode", "")
        year_p   = paper.get("year", "?")
        authors  = paper.get("author", [])
        doctype  = paper.get("doctype", "article")
        abstract = paper.get("abstract", "Abstract no disponible.")

        url = f"https://ui.adsabs.harvard.edu/abs/{urllib.parse.quote(bibcode)}"

        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += f" +{len(authors)-3} más"

        # Resumen recortado a 600 caracteres con sangría
        abstract_short = abstract[:600] + ("..." if len(abstract) > 600 else "")
        abstract_wrapped = textwrap.fill(
            abstract_short, width=70,
            initial_indent="      ",
            subsequent_indent="      "
        )

        print(f"\n[{i:02d}] {title}")
        print(f"      Año: {year_p}  |  Tipo: {doctype}")
        print(f"      Autores: {author_str}")
        print(f"      🔗 {url}")
        print(f"\n      Abstract:")
        print(abstract_wrapped)
        print(f"\n      {'─'*56}")


def main():
    if not ADS_TOKEN:
        print("ERROR: Falta ADS_TOKEN en el archivo .env")
        print("Obtén tu token en: https://ui.adsabs.harvard.edu/user/settings/token")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Busca artículos, tesis y libros de un autor en NASA ADS."
    )
    parser.add_argument("author", help='Nombre del autor: "Apellido, Nombre"')
    parser.add_argument("--year", help="Año o rango: 2023 o 2020-2023 (opcional)", default=None)
    parser.add_argument("--first-author", action="store_true", help="Solo papers donde es primer autor")
    parser.add_argument("--export", help="Exportar resultados a CSV (ej: --export matriz.csv)", default=None)

    args = parser.parse_args()

    modo = " (solo primer autor)" if args.first_author else ""
    print(f"Buscando papers de '{args.author}'" + (f" del año {args.year}" if args.year else "") + modo + "...")

    papers = search_author(args.author, args.year, args.first_author)
    display_results(papers, args.author, args.year, args.first_author)

    if args.export:
        papers_to_csv(papers, args.export)


if __name__ == "__main__":
    main()
