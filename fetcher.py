import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from config import CATEGORIES, KEYWORDS, MAX_RESULTS, HOURS_BACK

# arXiv usa el namespace Atom estándar — necesitamos esto para parsear el XML
ATOM_NS = "{http://www.w3.org/2005/Atom}"

def build_query():
    """
    Construye la query para la API de arXiv.

    La API acepta queries con operadores booleanos:
      - OR entre términos del mismo campo
      - AND entre campos distintos

    Ejemplo: (cat:astro-ph.HE OR cat:astro-ph.SR) AND (ti:supernova OR abs:transient)
    """
    # Une todas las categorías con OR
    cat_query = " OR ".join(f"cat:{c}" for c in CATEGORIES)

    # Une todas las keywords con OR, buscando en título (ti:) o abstract (abs:)
    # Solo tomamos las keywords simples (sin espacios) para la query de arXiv
    # Las compuestas las filtramos después en Python
    simple_keywords = [k for k in KEYWORDS if " " not in k]
    kw_query = " OR ".join(
        f"ti:{k} OR abs:{k}" for k in simple_keywords[:10]  # arXiv limita el largo
    )

    return f"({cat_query}) AND ({kw_query})"

def fetch_papers():
    """
    Llama a la API de arXiv y devuelve lista de papers publicados
    en las últimas HOURS_BACK horas que coincidan con keywords.

    Cada paper es un dict con: id, title, abstract, authors, url, published
    """
    query = build_query()

    # Construimos la URL con urllib.parse.urlencode para escapar caracteres especiales
    params = urllib.parse.urlencode({
        "search_query": query,
        "max_results": MAX_RESULTS,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = f"http://export.arxiv.org/api/query?{params}"

    print(f"[fetcher] Consultando arXiv...")

    with urllib.request.urlopen(url, timeout=30) as response:
        xml_data = response.read().decode("utf-8")

    # Parseamos el XML con ElementTree
    root = ET.fromstring(xml_data)

    # Calculamos el límite de tiempo: solo papers de las últimas HOURS_BACK horas
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)

    papers = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        # Extraemos los campos que nos interesan
        paper_id  = entry.find(f"{ATOM_NS}id").text.strip()
        title     = entry.find(f"{ATOM_NS}title").text.strip().replace("\n", " ")
        abstract  = entry.find(f"{ATOM_NS}summary").text.strip().replace("\n", " ")
        published = entry.find(f"{ATOM_NS}updated").text.strip()

        # Convertimos la fecha a objeto datetime para comparar
        # Formato arXiv: "2026-04-23T15:06:35Z"
        pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))

        # Descartamos papers más viejos que el cutoff
        if pub_dt < cutoff:
            continue

        # Filtramos por keywords compuestas (las que tienen espacios)
        # arXiv no las maneja bien en la query, así que las chequeamos manualmente
        text = (title + " " + abstract).lower()
        if not any(kw.lower() in text for kw in KEYWORDS):
            continue

        # Extraemos autores (puede haber varios)
        authors = [
            a.find(f"{ATOM_NS}name").text
            for a in entry.findall(f"{ATOM_NS}author")
        ]

        papers.append({
            "id":       paper_id,
            "title":    title,
            "abstract": abstract,
            "authors":  authors,
            "url":      paper_id,  # el id ya es la URL de arXiv
            "published": pub_dt.strftime("%Y-%m-%d %H:%M UTC"),
        })

    print(f"[fetcher] {len(papers)} papers relevantes en las últimas {HOURS_BACK}h")
    return papers
