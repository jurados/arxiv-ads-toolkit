import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from config import CATEGORIES, KEYWORDS, HOURS_BACK

ATOM_NS   = "{http://www.w3.org/2005/Atom}"
PAGE_SIZE = 50   # arXiv API page size
MAX_PAGES = 10   # hard cap: 500 results total


def build_query():
    """
    Construye la query para la API de arXiv incluyendo keywords de frase
    usando comillas (ti:"Type Ia" OR abs:"Type Ia").
    """
    cat_query = " OR ".join(f"cat:{c}" for c in CATEGORIES)

    kw_parts = []
    for kw in KEYWORDS:
        safe = kw.replace('"', "")
        if " " in kw:
            kw_parts.append(f'ti:"{safe}" OR abs:"{safe}"')
        else:
            kw_parts.append(f"ti:{safe} OR abs:{safe}")

    kw_query = " OR ".join(kw_parts[:15])
    return f"({cat_query}) AND ({kw_query})"


def _normalize_url(raw: str) -> str:
    """http://arxiv.org/abs/2301.07688v2  →  https://arxiv.org/abs/2301.07688"""
    m = re.search(r"arxiv\.org/abs/([\d.]+)", raw)
    if m:
        return f"https://arxiv.org/abs/{m.group(1)}"
    return raw.replace("http://", "https://")


def _fetch_page(query: str, start: int) -> list:
    """Fetch one page of arXiv results starting at `start`."""
    params = urllib.parse.urlencode({
        "search_query": query,
        "start":        start,
        "max_results":  PAGE_SIZE,
        "sortBy":       "submittedDate",
        "sortOrder":    "descending",
    })
    url = f"http://export.arxiv.org/api/query?{params}"
    with urllib.request.urlopen(url, timeout=30) as r:
        root = ET.fromstring(r.read().decode("utf-8"))
    return root.findall(f"{ATOM_NS}entry")


def fetch_papers() -> list:
    """
    Pagina la API de arXiv hasta que todos los resultados de la página sean
    más viejos que el cutoff, o hasta MAX_PAGES páginas.
    Devuelve sólo papers de las últimas HOURS_BACK horas que coincidan con keywords.
    """
    query  = build_query()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)
    papers = []
    seen   = set()

    print(f"[fetcher] Consultando arXiv (paginado, {PAGE_SIZE}/página, máx {MAX_PAGES} págs)...")

    for page in range(MAX_PAGES):
        entries = _fetch_page(query, start=page * PAGE_SIZE)
        if not entries:
            break

        page_had_recent = False

        for entry in entries:
            raw_id    = entry.find(f"{ATOM_NS}id").text.strip()
            published = entry.find(f"{ATOM_NS}published").text.strip()
            pub_dt    = datetime.fromisoformat(published.replace("Z", "+00:00"))

            if pub_dt >= cutoff:
                page_had_recent = True
            else:
                continue  # paper too old — skip but keep checking this page

            if raw_id in seen:
                continue
            seen.add(raw_id)

            title    = entry.find(f"{ATOM_NS}title").text.strip().replace("\n", " ")
            abstract = entry.find(f"{ATOM_NS}summary").text.strip().replace("\n", " ")

            text = (title + " " + abstract).lower()
            if not any(kw.lower() in text for kw in KEYWORDS):
                continue

            authors = [
                a.find(f"{ATOM_NS}name").text
                for a in entry.findall(f"{ATOM_NS}author")
            ]

            papers.append({
                "id":        raw_id,
                "title":     title,
                "abstract":  abstract,
                "authors":   authors,
                "url":       _normalize_url(raw_id),
                "published": pub_dt.strftime("%Y-%m-%d %H:%M UTC"),
            })

        if not page_had_recent:
            # All entries on this page are past the cutoff — stop paginating
            break

    print(f"[fetcher] {len(papers)} papers relevantes en las últimas {HOURS_BACK}h ({page+1} pág(s))")
    return papers
