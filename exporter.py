"""
Módulo compartido para exportar resultados de NASA ADS a CSV.
Usado por ads_search.py, ads_topics.py, ads_references.py y ads_citations.py.
"""

import csv
import os


BASE_COLUMNS = [
    "bibcode",
    "title",
    "year",
    "doctype",
    "first_author",
    "url",
    "method",
    "key_finding",
    "relevance",
    "notes",
]


def papers_to_csv(papers: list, filepath: str, extra_columns: list = None):
    """
    Exporta una lista de papers (dicts de NASA ADS) a un archivo CSV.

    Si el archivo ya existe, agrega las filas sin duplicar
    bibcodes que ya estén presentes — útil para ir acumulando
    búsquedas distintas en una misma matriz.

    extra_columns: columnas adicionales opcionales (ej: ["level"] para ads_chain.py).
    Los papers deben tener esas claves en su dict para que se escriban.
    """
    filepath = os.path.expanduser(filepath)
    columns  = BASE_COLUMNS + (extra_columns or [])

    # Cargamos bibcodes ya existentes para evitar duplicados
    existing_bibcodes = set()
    file_exists = os.path.exists(filepath)
    if file_exists:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_bibcodes.add(row.get("bibcode", ""))

    new_rows = 0
    skipped  = 0

    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)

        if not file_exists:
            writer.writeheader()

        for paper in papers:
            bibcode = paper.get("bibcode", "")

            if bibcode in existing_bibcodes:
                skipped += 1
                continue

            title        = paper.get("title",  [""])[0] if paper.get("title") else ""
            first_author = paper.get("author", [""])[0] if paper.get("author") else ""
            year         = paper.get("year",    "")
            doctype      = paper.get("doctype", "")
            url          = f"https://ui.adsabs.harvard.edu/abs/{bibcode}"

            row = {
                "bibcode":      bibcode,
                "title":        title,
                "year":         year,
                "doctype":      doctype,
                "first_author": first_author,
                "url":          url,
                "method":       "",
                "key_finding":  "",
                "relevance":    "",
                "notes":        "",
            }
            # Agregar columnas extra si existen en el paper dict
            for col in (extra_columns or []):
                row[col] = paper.get(col, "")

            writer.writerow(row)
            existing_bibcodes.add(bibcode)
            new_rows += 1

    print(f"\n[export] Guardado en: {filepath}")
    print(f"         {new_rows} fila(s) nueva(s) agregada(s)" +
          (f" | {skipped} duplicado(s) omitido(s)" if skipped else ""))
