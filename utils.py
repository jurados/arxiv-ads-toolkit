"""Shared utilities for all ads_* modules."""
import os
import json
import urllib.parse
import urllib.request
from dotenv import load_dotenv

load_dotenv()

ADS_TOKEN = os.getenv("ADS_TOKEN")
ADS_API   = "https://api.adsabs.harvard.edu/v1/search/query"

# Stopwords compartidas por ads_topics (búsqueda por título) y ads_similar
# (extracción de keywords). Combina stopwords gramaticales y términos
# científicos genéricos que no aportan valor a las queries.
STOP_WORDS = {
    "a", "all", "also", "although", "an", "and", "approach", "are",
    "as", "at", "based", "be", "been", "between", "both", "but", "by",
    "can", "could", "data", "did", "do", "does", "each", "find", "first",
    "for", "found", "from", "given", "had", "has", "have", "here", "high",
    "how", "however", "in", "into", "is", "it", "its", "large", "may",
    "method", "might", "model", "models", "more", "most", "new", "not",
    "number", "of", "on", "one", "or", "our", "paper", "present",
    "presents", "results", "sample", "second", "set", "should", "show",
    "shown", "such", "than", "that", "the", "their", "then", "these",
    "they", "therefore", "this", "those", "three", "through", "thus",
    "to", "two", "up", "us", "use", "used", "using", "very", "was", "we",
    "well", "were", "what", "when", "where", "which", "while", "who",
    "will", "with", "work", "would",
}


def fetch_arxiv_doc(arxiv_id: str, fl: str = "bibcode,title") -> dict | None:
    """Resuelve un arXiv ID y devuelve el documento ADS completo (o None).

    fl: campos ADS a devolver (ej. "bibcode,title,citation_count").
    Función base reutilizable; arxiv_to_bibcode la envuelve para el caso común.
    """
    clean = arxiv_id.replace("arXiv:", "").replace("arxiv:", "").strip()
    params = urllib.parse.urlencode({
        "q":    f'identifier:"arXiv:{clean}"',
        "fl":   fl,
        "rows": 1,
    })
    req = urllib.request.Request(
        f"{ADS_API}?{params}",
        headers={"Authorization": f"Bearer {ADS_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        docs = json.load(r).get("response", {}).get("docs", [])
    return docs[0] if docs else None


def arxiv_to_bibcode(arxiv_id: str, verbose: bool = False) -> str | None:
    """Resuelve un arXiv ID a bibcode de NASA ADS.

    verbose=True imprime el resultado (útil en scripts CLI).
    verbose=False (default) es silencioso (seguro para uso en app.py).
    """
    doc = fetch_arxiv_doc(arxiv_id)
    if not doc:
        return None
    bibcode = doc["bibcode"]
    if verbose:
        title = doc.get("title", ["?"])[0]
        clean = arxiv_id.replace("arXiv:", "").replace("arxiv:", "").strip()
        print(f"[→] arXiv:{clean} → {bibcode}")
        print(f"    {title[:70]}")
    return bibcode


def is_arxiv_id(identifier: str) -> bool:
    """Return True if identifier looks like an arXiv ID (YYMM.NNNNN[vN])."""
    clean = identifier.replace("arXiv:", "").replace("arxiv:", "").strip()
    if "v" in clean.split(".")[-1]:
        clean = clean.rsplit("v", 1)[0]
    parts = clean.split(".")
    return len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit()


def pubdate_filter(year: str) -> str:
    """
    Convert a year string to an ADS pubdate filter clause (without leading space).

    Formats supported:
      "2023"      → pubdate:[2023-01 TO 2023-12]
      "2020-2023" → pubdate:[2020-01 TO 2023-12]
      "2020-"     → pubdate:[2020-01 TO 9999-12]   (from 2020 onwards)
      "-2024"     → pubdate:[0000-01 TO 2024-12]   (up to 2024)
    """
    year = year.strip()
    if year.endswith("-"):
        return f"pubdate:[{year[:-1]}-01 TO 9999-12]"
    if year.startswith("-"):
        return f"pubdate:[0000-01 TO {year[1:]}-12]"
    if "-" in year:
        start, end = year.split("-", 1)
        return f"pubdate:[{start}-01 TO {end}-12]"
    return f"pubdate:[{year}-01 TO {year}-12]"
