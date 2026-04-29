"""
Genera el digest diario de arXiv como HTML autocontenido.
Guardado en digests/digest_YYYY-MM-DD.html.
"""

import os
import html as _html

DIGEST_DIR = os.path.join(os.path.dirname(__file__), "digests")


def save_digest_html(papers: list, date_str: str) -> str:
    os.makedirs(DIGEST_DIR, exist_ok=True)
    filepath = os.path.join(DIGEST_DIR, f"digest_{date_str}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(_build_html(papers, date_str))
    return filepath


def save_digest_md(papers: list, date_str: str) -> str:
    """Save a plain Markdown digest alongside the HTML one."""
    os.makedirs(DIGEST_DIR, exist_ok=True)
    filepath = os.path.join(DIGEST_DIR, f"digest_{date_str}.md")
    lines = [f"# arXiv Digest — {date_str}", f"{len(papers)} paper(s)\n"]
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.get("authors", [])[:3])
        if len(p.get("authors", [])) > 3:
            authors += f" +{len(p['authors']) - 3} más"
        abstract = p.get("abstract", "")
        if len(abstract) > 500:
            abstract = abstract[:500] + "..."
        lines += [
            f"## [{i}] {p.get('title', '')}",
            f"**{authors}** · {p.get('published', '')}",
            f"🔗 {p.get('url', '')}",
            f"\n{abstract}\n",
        ]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filepath


def list_digests() -> list[str]:
    """Devuelve los digests HTML ordenados por fecha descendente.
    Los .md paralelos no se listan —se accede a ellos por el mismo
    nombre base cambiando la extensión."""
    if not os.path.exists(DIGEST_DIR):
        return []
    return sorted(
        [f for f in os.listdir(DIGEST_DIR)
         if f.startswith("digest_") and f.endswith(".html")],
        reverse=True,
    )


def has_md_digest(html_filename: str) -> bool:
    """Devuelve True si existe el .md correspondiente al digest HTML dado."""
    md_name = html_filename.replace(".html", ".md")
    return os.path.exists(os.path.join(DIGEST_DIR, md_name))


def _e(s: str) -> str:
    return _html.escape(str(s))


def _build_html(papers: list, date_str: str) -> str:
    n = len(papers)

    cards = ""
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.get("authors", [])[:3])
        if len(p.get("authors", [])) > 3:
            authors += f" +{len(p['authors']) - 3} más"
        abstract = p.get("abstract", "")
        cards += f"""
<div class="paper">
  <div class="paper-title">
    <a href="{_e(p.get('url', '#'))}" target="_blank">[{i}] {_e(p.get('title', ''))}</a>
  </div>
  <div class="paper-meta">{_e(authors)} &nbsp;·&nbsp; <span class="badge">{_e(p.get('published', ''))}</span></div>
  <details>
    <summary>Abstract</summary>
    <p class="paper-abstract">{_e(abstract)}</p>
  </details>
</div>"""

    if not papers:
        cards = '<div class="empty">No hay papers nuevos con los keywords actuales.</div>'

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>arXiv Digest — {_e(date_str)}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#e6edf3;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;padding:32px;max-width:860px;margin:0 auto}}
h1{{font-size:1.4rem;font-weight:800;margin-bottom:4px}}
.subtitle{{color:#8b949e;font-size:.88rem;margin-bottom:28px}}
.paper{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px 20px;margin-bottom:14px;transition:border-color .15s}}
.paper:hover{{border-color:#58a6ff}}
.paper-title{{font-size:.95rem;font-weight:700;margin-bottom:6px;line-height:1.4}}
.paper-title a{{color:#e6edf3;text-decoration:none}}
.paper-title a:hover{{color:#58a6ff}}
.paper-meta{{font-size:.78rem;color:#8b949e;margin-bottom:8px}}
details summary{{font-size:.78rem;color:#58a6ff;cursor:pointer;user-select:none;margin-top:4px}}
.paper-abstract{{font-size:.83rem;color:#8b949e;line-height:1.6;margin-top:8px}}
.badge{{background:#1f3d6e;color:#79c0ff;font-size:.7rem;font-weight:700;padding:2px 8px;border-radius:20px}}
.empty{{text-align:center;padding:60px;color:#8b949e}}
footer{{margin-top:32px;text-align:center;font-size:.72rem;color:#8b949e;border-top:1px solid #30363d;padding-top:16px}}
</style>
</head>
<body>
<h1>🔭 arXiv Digest</h1>
<p class="subtitle">{_e(date_str)} &nbsp;·&nbsp; {n} paper(s) nuevo(s)</p>
{cards}
<footer>Generado por arXiv Agent</footer>
</body>
</html>"""
