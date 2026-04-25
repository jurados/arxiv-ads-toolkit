#!/home/jurados/arxiv-agent/venv/bin/python
"""
NASA ADS — Cadena de Referencias Multinivel
============================================
Dado un paper semilla, rastrea sus referencias nivel por nivel.
Cada nivel expande las referencias de los papers del nivel anterior.

El resultado incluye una columna "level" para saber a qué profundidad
se encontró cada paper — útil para construir la matriz de literatura.

Advertencia sobre el crecimiento exponencial:
  Nivel 1: ~50 referencias
  Nivel 2: hasta 50×50 = 2,500 (controlado por --max-per-level)
  Nivel 3: puede ser enorme — usar --max-per-level bajo (ej: 5)

Uso:
    ads-chain 2022AJ....164..195F
    ads-chain 2022AJ....164..195F --levels 3
    ads-chain 2022AJ....164..195F --levels 4 --max-per-level 5
    ads-chain 2022AJ....164..195F --levels 2 --year 2018-2026
    ads-chain 2022AJ....164..195F --levels 3 --export cadena.csv
"""

import json
import argparse
import urllib.request
import urllib.parse
import time
import os
import sys
from dotenv import load_dotenv
from exporter import papers_to_csv
from utils import is_arxiv_id, pubdate_filter

load_dotenv()

ADS_TOKEN = os.getenv("ADS_TOKEN")
ADS_API   = "https://api.adsabs.harvard.edu/v1/search/query"



def arxiv_to_bibcode(arxiv_id: str) -> str | None:
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
        return None
    bibcode = docs[0]["bibcode"]
    title   = docs[0].get("title", ["?"])[0]
    print(f"  [→] arXiv:{clean} → {bibcode}")
    print(f"      {title[:65]}")
    return bibcode


def fetch_references_for(bibcode: str, rows: int = 50, year: str = None) -> list:
    """
    Obtiene las referencias de un paper. Devuelve lista de dicts con
    bibcode, title, year, author, doctype.
    """
    query = f"references(bibcode:{bibcode})"
    if year:
        query += f" {pubdate_filter(year)}"

    params = urllib.parse.urlencode({
        "q":    query,
        "fl":   "bibcode,title,year,author,doctype,citation_count,abstract,doi,identifier",
        "rows": rows,
        "sort": "date desc",
    })
    req = urllib.request.Request(
        f"{ADS_API}?{params}",
        headers={"Authorization": f"Bearer {ADS_TOKEN}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
        return data.get("response", {}).get("docs", [])
    except Exception as e:
        print(f"  [!] Error fetching {bibcode}: {e}")
        return []


def build_chain(seed_bibcode: str, levels: int, max_per_level: int,
                rows_per_paper: int = 30, year: str = None) -> list:
    """
    Recorre la cadena de referencias nivel por nivel.

    Retorna lista de papers con campo extra 'level' indicando
    en qué nivel fueron encontrados (1 = referencias directas del semilla).

    Estrategia para controlar la explosión:
    - seen_bibcodes: evita expandir o duplicar papers ya visitados
    - max_per_level: limita cuántos papers del nivel anterior se expanden
    """
    seen_bibcodes = {seed_bibcode}
    all_papers    = []

    # Papers del nivel actual cuyas referencias vamos a expandir
    current_level_bibcodes = [seed_bibcode]

    for level in range(1, levels + 1):
        print(f"\n  Nivel {level}: expandiendo {len(current_level_bibcodes)} paper(s)...")

        next_level_bibcodes = []
        level_papers        = []

        # Limitamos cuántos papers expandimos en este nivel
        to_expand = current_level_bibcodes[:max_per_level]

        for i, bibcode in enumerate(to_expand, 1):
            print(f"    [{i}/{len(to_expand)}] {bibcode}...", end=" ", flush=True)
            refs = fetch_references_for(bibcode, rows=rows_per_paper, year=year)
            new  = [r for r in refs if r.get("bibcode") not in seen_bibcodes]
            print(f"{len(new)} nuevas referencias")

            for paper in new:
                bc = paper.get("bibcode", "")
                if bc:
                    paper["level"] = level
                    paper["parent"] = bibcode
                    seen_bibcodes.add(bc)
                    level_papers.append(paper)
                    next_level_bibcodes.append(bc)

            # Pequeña pausa para no saturar la API
            if i < len(to_expand):
                time.sleep(0.3)

        all_papers.extend(level_papers)
        print(f"  → {len(level_papers)} papers nuevos en el nivel {level}")

        if not next_level_bibcodes:
            print(f"  → Sin más referencias nuevas. Deteniendo en nivel {level}.")
            break

        current_level_bibcodes = next_level_bibcodes

    return all_papers


def display_summary(papers: list, seed: str, levels: int):
    """Muestra un resumen por nivel en vez de imprimir todos los papers."""
    from collections import Counter
    level_counts = Counter(p.get("level") for p in papers)

    print(f"\n{'='*60}")
    print(f"  Cadena de referencias — semilla: {seed}")
    print(f"  {len(papers)} papers únicos encontrados en {levels} nivel(es)")
    print(f"{'='*60}")

    for lvl in sorted(level_counts):
        count = level_counts[lvl]
        label = "referencias directas" if lvl == 1 else f"referencias de nivel {lvl-1}"
        print(f"\n  Nivel {lvl} ({label}): {count} papers")
        level_papers = [p for p in papers if p.get("level") == lvl]
        for p in level_papers[:5]:
            title = p.get("title", ["?"])[0] if p.get("title") else "?"
            year  = p.get("year", "?")
            print(f"    [{year}] {title[:60]}")
        if count > 5:
            print(f"    ... y {count - 5} más")


def main():
    if not ADS_TOKEN:
        print("ERROR: Falta ADS_TOKEN en el archivo .env")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Rastrea la cadena de referencias de un paper en múltiples niveles."
    )
    parser.add_argument("identifier",
                        help="Bibcode (2022AJ....164..195F) o ID de arXiv (2204.05018)")
    parser.add_argument("--levels",        help="Niveles de profundidad (default: 2, max recomendado: 4)",
                        type=int, default=2)
    parser.add_argument("--max-per-level", help="Máx. papers a expandir por nivel (default: 10)",
                        type=int, default=10)
    parser.add_argument("--rows",          help="Máx. referencias a buscar por paper (default: 30)",
                        type=int, default=30)
    parser.add_argument("--year",          help="Filtrar por año o rango: 2023 o 2018-2023",
                        default=None)
    parser.add_argument("--export",        help="Exportar a CSV con columna 'level'",
                        default=None)

    args = parser.parse_args()

    # Resolver arXiv ID si es necesario
    if is_arxiv_id(args.identifier):
        print(f"Buscando bibcode para arXiv:{args.identifier}...")
        bibcode = arxiv_to_bibcode(args.identifier)
        if not bibcode:
            print(f"ERROR: No se encontró arXiv:{args.identifier} en NASA ADS.")
            sys.exit(1)
    else:
        bibcode = args.identifier

    print(f"\nIniciando cadena desde: {bibcode}")
    print(f"Niveles: {args.levels}  |  Máx. por nivel: {args.max_per_level}  |  Refs por paper: {args.rows}")
    if args.year:
        print(f"Filtro de año: {args.year}")

    papers = build_chain(
        seed_bibcode   = bibcode,
        levels         = args.levels,
        max_per_level  = args.max_per_level,
        rows_per_paper = args.rows,
        year           = args.year,
    )

    display_summary(papers, bibcode, args.levels)

    if args.export and papers:
        papers_to_csv(papers, args.export, extra_columns=["level"])


if __name__ == "__main__":
    main()
