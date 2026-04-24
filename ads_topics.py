#!/home/jurados/arxiv-agent/venv/bin/python
"""
NASA ADS — Búsqueda por Conceptos o Palabras Clave
===================================================
Busca papers en NASA ADS que mencionen una frase o concepto
en el título y/o abstract.

Uso:
    ads-topics "supernova machine learning"
    ads-topics "core collapse supernova" --year 2023
    ads-topics "kilonova" --field title
    ads-topics "deep learning transient classification" --rows 20
    ads-topics "multimodal astronomy" --year 2024 --field abstract

Opciones:
    --year    Filtrar por año (opcional)
    --field   Dónde buscar: title, abstract, all (default: all)
    --rows    Número máximo de resultados (default: 20)
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
DOCTYPES  = ["article", "thesis", "book"]


def pubdate_filter(year: str) -> str:
    """
    Convierte un año o rango de años al filtro pubdate de ADS.

    Ejemplos:
      "2023"       → pubdate:[2023-01 TO 2023-12]
      "2020-2023"  → pubdate:[2020-01 TO 2023-12]
    """
    if "-" in year and len(year) > 4:
        start, end = year.split("-", 1)
        return f"pubdate:[{start}-01 TO {end}-12]"
    return f"pubdate:[{year}-01 TO {year}-12]"


def build_query(keywords: str, field: str, year: str = None) -> str:
    """
    Construye la query para ADS según el campo de búsqueda.

    ADS soporta búsqueda en:
      title:"frase"    → solo en título
      abs:"frase"      → solo en abstract
      title + abs      → en ambos (lo más completo)

    Las frases entre comillas se buscan de forma exacta.
    Sin comillas, ADS busca los términos de forma individual.
    """
    # Normalizamos: si la frase tiene más de una palabra, la ponemos entre comillas
    # para que ADS la trate como frase exacta
    phrase = f'"{keywords}"' if " " in keywords else keywords

    if field == "title":
        kw_query = f"title:{phrase}"
    elif field == "abstract":
        kw_query = f"abs:{phrase}"
    else:  # all: buscamos en título Y abstract
        kw_query = f"(title:{phrase} OR abs:{phrase})"

    doctype_filter = " OR ".join(f"doctype:{d}" for d in DOCTYPES)
    query = f"{kw_query} ({doctype_filter})"

    if year:
        query += f" {pubdate_filter(year)}"

    return query


def search_topics(keywords: str, field: str = "all", year: str = None, rows: int = 20) -> list:
    query  = build_query(keywords, field, year)
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


def display_results(papers: list, keywords: str, field: str, year: str = None):
    campo  = {"title": "título", "abstract": "abstract", "all": "título y abstract"}[field]
    filtro = f'"{keywords}"' + (f" ({year})" if year else "")

    print(f"\n{'='*60}")
    print(f"  NASA ADS — {filtro}")
    print(f"  {len(papers)} resultado(s)  |  buscado en: {campo}")
    print(f"{'='*60}")

    if not papers:
        print("\nSin resultados. Prueba con otros términos o sin --field.")
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

        abstract_short   = abstract[:600] + ("..." if len(abstract) > 600 else "")
        abstract_wrapped = textwrap.fill(
            abstract_short, width=70,
            initial_indent="      ",
            subsequent_indent="      ",
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
        description="Busca papers en NASA ADS por palabras clave o frases."
    )
    parser.add_argument("keywords", help='Frase o palabras a buscar (ej: "supernova machine learning")')
    parser.add_argument("--year",  help="Año o rango: 2023 o 2020-2023 (opcional)", default=None)
    parser.add_argument("--field", help="Dónde buscar: title, abstract, all (default: all)",
                        choices=["title", "abstract", "all"], default="all")
    parser.add_argument("--rows",   help="Número máximo de resultados (default: 20)", type=int, default=20)
    parser.add_argument("--export", help="Exportar resultados a CSV (ej: --export matriz.csv)", default=None)

    args = parser.parse_args()

    campo = {"title": "título", "abstract": "abstract", "all": "título y abstract"}[args.field]
    print(f'\nBuscando "{args.keywords}" en {campo}' + (f" ({args.year})" if args.year else "") + "...")

    papers = search_topics(args.keywords, args.field, args.year, args.rows)
    display_results(papers, args.keywords, args.field, args.year)

    if args.export:
        papers_to_csv(papers, args.export)


if __name__ == "__main__":
    main()
