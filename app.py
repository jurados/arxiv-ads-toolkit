"""
Flask web interface for arXiv Agent & NASA ADS Toolkit.
Run: /home/jurados/arxiv-agent/venv/bin/python app.py
Then open: http://localhost:5000
"""

import sys
import os
import io
import csv
import json
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, render_template, Response
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)

# Top-level imports so errors surface at startup
from ads_search import search_author
from ads_topics import search_topics
from ads_references import fetch_references, arxiv_to_bibcode as refs_arxiv_to_bibcode
from ads_citations import fetch_citations, arxiv_to_bibcode as cits_arxiv_to_bibcode
from ads_similar import search_similar_bibcode, search_similar_text, ADS_API as SIMILAR_ADS_API, ADS_TOKEN as SIMILAR_ADS_TOKEN
from ads_chain import build_chain, arxiv_to_bibcode as chain_arxiv_to_bibcode
from ads_download import get_pdf_url, get_paper_metadata, make_filename, fetch_pdf_bytes, arxiv_to_bibcode as dl_arxiv_to_bibcode, get_papers_metadata_batch
from utils import is_arxiv_id


def _paper_to_dict(paper: dict) -> dict:
    """Normalize a NASA ADS paper dict for JSON response."""
    import re
    bibcode = paper.get("bibcode", "")
    title_raw = paper.get("title", [])
    title = title_raw[0] if title_raw else "No title"
    authors = paper.get("author", [])
    author_str = ", ".join(authors[:4])
    if len(authors) > 4:
        author_str += f" +{len(authors)-4} more"
    
    abstract = paper.get("abstract", "")

    # Paper-to-Code: buscar links de repositorios en abstract
    code_url    = None
    search_text = abstract

    if search_text:
        # Patrón 1: URL completa
        patterns = [
            r"https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
            r"https?://gitlab\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
            r"https?://bitbucket\.org/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
        ]
        for pattern in patterns:
            match = re.search(pattern, search_text)
            if match:
                code_url = match.group(0)
                code_url = code_url.rstrip(".,;)")
                break
        
        # Patrón 2: github.com/... (sin protocolo)
        if not code_url:
            short_patterns = [
                r"github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
                r"gitlab\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"
            ]
            for pattern in short_patterns:
                match = re.search(pattern, search_text)
                if match:
                    code_url = "https://" + match.group(0)
                    code_url = code_url.rstrip(".,;)")
                    break

    # Patrón 3: Buscar menciones de "pip install [package]"
    if not code_url and search_text:
        pip_match = re.search(r"pip install ([A-Za-z0-9_-]+)", search_text)
        if pip_match:
            package_name = pip_match.group(1)
            code_url = f"https://pypi.org/project/{package_name}/"

    # DOI: ADS returns a list; take first entry
    doi_list = paper.get("doi") or []
    doi = doi_list[0] if doi_list else None

    # arXiv ID: from identifier list (preferred) or from bibcode pattern
    arxiv_id = None
    for ident in (paper.get("identifier") or []):
        if ident.lower().startswith("arxiv:"):
            arxiv_id = ident[6:].strip()
            break
    if not arxiv_id and re.match(r"^\d{4}arXiv(\d{4})(\d+)", bibcode):
        m = re.match(r"^\d{4}arXiv(\d{4})(\d+)", bibcode)
        arxiv_id = f"{m.group(1)}.{m.group(2)}"

    return {
        "bibcode": bibcode,
        "title": title,
        "year": paper.get("year", ""),
        "doctype": paper.get("doctype", ""),
        "authors": author_str,
        "author_list": authors[:4],
        "author_count": len(authors),
        "first_author": authors[0] if authors else "",
        "abstract": abstract,
        "url": f"https://ui.adsabs.harvard.edu/abs/{urllib.parse.quote(bibcode)}",
        "level": paper.get("level", None),
        "citation_count": paper.get("citation_count"),
        "code_url": code_url,
        "doi": doi,
        "arxiv_id": arxiv_id,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json()
    author = data.get("author", "").strip()
    year = data.get("year", "").strip() or None
    first_author = data.get("first_author", False)
    rows = int(data.get("rows", 50))
    if not author:
        return jsonify({"error": "Author required"}), 400
    try:
        papers = search_author(author, year=year, first_author=first_author, rows=rows)
        return jsonify({"papers": [_paper_to_dict(p) for p in papers], "total": len(papers)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/topics", methods=["POST"])
def api_topics():
    data = request.get_json()
    keywords = data.get("keywords", "").strip()
    year = data.get("year", "").strip() or None
    field = data.get("field", "all")
    rows = int(data.get("rows", 20))
    if not keywords:
        return jsonify({"error": "Keywords required"}), 400
    try:
        papers = search_topics(keywords, field=field, year=year, rows=rows)
        return jsonify({"papers": [_paper_to_dict(p) for p in papers], "total": len(papers)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/references", methods=["POST"])
def api_references():
    data = request.get_json()
    identifier = data.get("identifier", "").strip()
    year = data.get("year", "").strip() or None
    rows = int(data.get("rows", 100))
    if not identifier:
        return jsonify({"error": "Bibcode or arXiv ID required"}), 400
    try:
        bibcode = identifier
        if is_arxiv_id(identifier):
            bibcode = refs_arxiv_to_bibcode(identifier)
            if not bibcode:
                return jsonify({"error": f"Could not resolve arXiv ID: {identifier}"}), 404
        papers, total = fetch_references(bibcode, year=year, rows=rows)
        return jsonify({"papers": [_paper_to_dict(p) for p in papers], "total": total, "bibcode": bibcode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/citations", methods=["POST"])
def api_citations():
    data = request.get_json()
    identifier = data.get("identifier", "").strip()
    year = data.get("year", "").strip() or None
    rows = int(data.get("rows", 100))
    if not identifier:
        return jsonify({"error": "Bibcode or arXiv ID required"}), 400
    try:
        bibcode = identifier
        if is_arxiv_id(identifier):
            bibcode = cits_arxiv_to_bibcode(identifier)
            if not bibcode:
                return jsonify({"error": f"Could not resolve arXiv ID: {identifier}"}), 404
        papers, total = fetch_citations(bibcode, year=year, rows=rows)
        return jsonify({"papers": [_paper_to_dict(p) for p in papers], "total": total, "bibcode": bibcode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/similar", methods=["POST"])
def api_similar():
    data = request.get_json()
    mode = data.get("mode", "bibcode")
    year = data.get("year", "").strip() or None
    rows = int(data.get("rows", 20))
    try:
        if mode == "bibcode":
            bibcode = data.get("bibcode", "").strip()
            if not bibcode:
                return jsonify({"error": "Bibcode required"}), 400
            if is_arxiv_id(bibcode):
                clean = bibcode.replace("arXiv:", "").replace("arxiv:", "")
                params = urllib.parse.urlencode({"q": f'identifier:"arXiv:{clean}"', "fl": "bibcode", "rows": 1})
                req = urllib.request.Request(f"{SIMILAR_ADS_API}?{params}", headers={"Authorization": f"Bearer {SIMILAR_ADS_TOKEN}"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    docs = json.load(r).get("response", {}).get("docs", [])
                bibcode = docs[0]["bibcode"] if docs else None
                if not bibcode:
                    return jsonify({"error": "Could not resolve arXiv ID"}), 404
            papers, total = search_similar_bibcode(bibcode, year=year, rows=rows)
            return jsonify({"papers": [_paper_to_dict(p) for p in papers], "total": total, "mode": "bibcode", "bibcode": bibcode})
        else:
            text = data.get("text", "").strip()
            if not text:
                return jsonify({"error": "Text required"}), 400
            papers, total, keywords = search_similar_text(text, year=year, rows=rows)
            if not papers and not keywords:
                return jsonify({"error": "No se pudieron extraer keywords relevantes del texto. Usa un texto más largo y específico."}), 400
            return jsonify({"papers": [_paper_to_dict(p) for p in papers], "total": total, "mode": "text", "keywords": keywords})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chain", methods=["POST"])
def api_chain():
    data = request.get_json()
    identifier = data.get("identifier", "").strip()
    levels = int(data.get("levels", 2))
    max_per_level = int(data.get("max_per_level", 10))
    rows = int(data.get("rows", 30))
    year = data.get("year", "").strip() or None
    if not identifier:
        return jsonify({"error": "Bibcode or arXiv ID required"}), 400
    try:
        bibcode = identifier
        if is_arxiv_id(identifier):
            bibcode = chain_arxiv_to_bibcode(identifier)
            if not bibcode:
                return jsonify({"error": f"Could not resolve arXiv ID: {identifier}"}), 404
        papers = build_chain(bibcode, levels=levels, max_per_level=max_per_level, rows_per_paper=rows, year=year)
        edges = [{"source": p["parent"], "target": p["bibcode"]}
                 for p in papers if p.get("parent") and p.get("bibcode")]
        return jsonify({
            "papers": [_paper_to_dict(p) for p in papers],
            "total": len(papers),
            "bibcode": bibcode,
            "seed": bibcode,
            "edges": edges,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/compare", methods=["POST"])
def api_compare():
    """Return papers that appear in both reference/citation sets of two papers."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    data = request.get_json()
    id_a = data.get("id_a", "").strip()
    id_b = data.get("id_b", "").strip()
    if not id_a or not id_b:
        return jsonify({"error": "Two identifiers required"}), 400
    try:
        def resolve(identifier):
            if is_arxiv_id(identifier):
                return refs_arxiv_to_bibcode(identifier)
            return identifier

        bc_a, bc_b = resolve(id_a), resolve(id_b)
        if not bc_a:
            return jsonify({"error": f"Could not resolve: {id_a}"}), 404
        if not bc_b:
            return jsonify({"error": f"Could not resolve: {id_b}"}), 404

        with ThreadPoolExecutor(max_workers=4) as pool:
            f_refs_a = pool.submit(fetch_references, bc_a, None, 500)
            f_refs_b = pool.submit(fetch_references, bc_b, None, 500)
            f_cits_a = pool.submit(fetch_citations,  bc_a, None, 500)
            f_cits_b = pool.submit(fetch_citations,  bc_b, None, 500)
            refs_a, _ = f_refs_a.result()
            refs_b, _ = f_refs_b.result()
            cits_a, _ = f_cits_a.result()
            cits_b, _ = f_cits_b.result()

        set_refs_a = {p["bibcode"] for p in refs_a if p.get("bibcode")}
        set_refs_b = {p["bibcode"] for p in refs_b if p.get("bibcode")}
        set_cits_a = {p["bibcode"] for p in cits_a if p.get("bibcode")}
        set_cits_b = {p["bibcode"] for p in cits_b if p.get("bibcode")}

        common_refs_bc = set_refs_a & set_refs_b
        common_cits_bc = set_cits_a & set_cits_b

        map_refs_a = {p["bibcode"]: p for p in refs_a if p.get("bibcode")}
        map_refs_b = {p["bibcode"]: p for p in refs_b if p.get("bibcode")}
        map_cits_a = {p["bibcode"]: p for p in cits_a if p.get("bibcode")}
        map_cits_b = {p["bibcode"]: p for p in cits_b if p.get("bibcode")}

        common_refs = [_paper_to_dict(map_refs_a.get(bc) or map_refs_b[bc]) for bc in common_refs_bc]
        common_cits = [_paper_to_dict(map_cits_a.get(bc) or map_cits_b[bc]) for bc in common_cits_bc]

        return jsonify({
            "bibcode_a": bc_a,
            "bibcode_b": bc_b,
            "common_refs": sorted(common_refs, key=lambda p: p.get("year", ""), reverse=True),
            "common_cits": sorted(common_cits, key=lambda p: p.get("year", ""), reverse=True),
            "total_refs_a": len(refs_a),
            "total_refs_b": len(refs_b),
            "total_cits_a": len(cits_a),
            "total_cits_b": len(cits_b),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json()
    identifier = data.get("identifier", "").strip()
    if not identifier:
        return jsonify({"error": "Bibcode or arXiv ID required"}), 400
    try:
        bibcode = identifier
        if is_arxiv_id(identifier):
            bibcode = dl_arxiv_to_bibcode(identifier)
            if not bibcode:
                return jsonify({"error": f"Could not resolve: {identifier}"}), 404
        pdf_url, _ = get_pdf_url(bibcode)
        if not pdf_url:
            return jsonify({"error": "No open-access PDF found for this paper"}), 404
        pdf_bytes = fetch_pdf_bytes(pdf_url)
        if pdf_bytes is None:
            return jsonify({"error": "Source returned non-PDF content (likely paywalled)"}), 403
        metadata = get_paper_metadata(bibcode)
        filename = make_filename(bibcode, metadata)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download_batch", methods=["POST"])
def api_download_batch():
    import zipfile
    data = request.get_json()
    bibcodes = data.get("bibcodes", [])[:15]
    if not bibcodes:
        return jsonify({"error": "No bibcodes provided"}), 400
    try:
        zip_buffer = io.BytesIO()
        found = 0
        metadata_map = get_papers_metadata_batch(bibcodes)
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for bibcode in bibcodes:
                try:
                    pdf_url, _ = get_pdf_url(bibcode)
                    if not pdf_url:
                        continue
                    pdf_bytes = fetch_pdf_bytes(pdf_url)
                    if pdf_bytes is None:
                        continue
                    metadata = metadata_map.get(bibcode) or get_paper_metadata(bibcode)
                    filename = make_filename(bibcode, metadata)
                    zf.writestr(filename, pdf_bytes)
                    found += 1
                except Exception:
                    continue
        if found == 0:
            return jsonify({"error": "No se encontraron PDFs de acceso abierto para los papers seleccionados"}), 404
        zip_buffer.seek(0)
        return Response(
            zip_buffer.read(),
            mimetype="application/zip",
            headers={"Content-Disposition": "attachment; filename=papers.zip"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export_bibtex", methods=["POST"])
def api_export_bibtex():
    import urllib.request
    data = request.get_json()
    bibcodes = data.get("bibcodes", [])
    if not bibcodes:
        return jsonify({"error": "No bibcodes provided"}), 400
    token = os.getenv("ADS_TOKEN")
    if not token:
        return jsonify({"error": "ADS_TOKEN not configured"}), 500
    try:
        payload = json.dumps({"bibcode": bibcodes}).encode("utf-8")
        req = urllib.request.Request(
            "https://api.adsabs.harvard.edu/v1/export/bibtex",
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)
        bibtex = result.get("export", "")
        if not bibtex:
            return jsonify({"error": "ADS returned empty BibTeX"}), 500
        return Response(
            bibtex,
            mimetype="application/x-bibtex",
            headers={"Content-Disposition": "attachment; filename=referencias.bib"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export_csv", methods=["POST"])
def api_export_csv():
    data = request.get_json()
    papers = data.get("papers", [])
    if not papers:
        return jsonify({"error": "No papers to export"}), 400
    output = io.StringIO()
    columns = ["bibcode", "title", "year", "doctype", "authors", "url", "abstract", "level", "method", "key_finding", "relevance", "notes"]
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for p in papers:
        writer.writerow({k: p.get(k, "") or "" for k in columns})
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=literatura.csv"}
    )


@app.route("/api/arxiv/status", methods=["GET"])
def api_arxiv_status():
    try:
        from config import CATEGORIES, KEYWORDS, HOURS_BACK, WHATSAPP_NUMBER
        lock_file = os.path.join(os.path.dirname(__file__), ".last_run")
        last_run = None
        if os.path.exists(lock_file):
            with open(lock_file) as f:
                last_run = f.read().strip()
        masked = "*" * (len(WHATSAPP_NUMBER) - 4) + WHATSAPP_NUMBER[-4:]
        return jsonify({
            "categories": CATEGORIES,
            "keywords": KEYWORDS,
            "keyword_count": len(KEYWORDS),
            "hours_back": HOURS_BACK,
            "whatsapp": masked,
            "last_run": last_run,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _fetch_and_save() -> tuple[list, str]:
    """Shared: fetch arXiv papers and save both digest formats. Returns (papers, date_str)."""
    from fetcher import fetch_papers
    from digester import save_digest_html, save_digest_md
    from datetime import datetime, timezone
    papers   = fetch_papers()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if papers:
        save_digest_html(papers, date_str)
        save_digest_md(papers, date_str)
    return papers, date_str


@app.route("/api/arxiv/send", methods=["POST"])
def api_arxiv_send():
    """Fetch today's arXiv papers and send them to WhatsApp."""
    try:
        from notifier import notify
        papers, date_str = _fetch_and_save()
        if not papers:
            return jsonify({"ok": False, "total": 0, "message": "No hay papers nuevos hoy con los keywords actuales."})
        sent = notify(papers, date_str)
        if sent:
            with open(os.path.join(os.path.dirname(__file__), ".last_run"), "w") as f:
                f.write(date_str)
        return jsonify({
            "ok": sent,
            "total": len(papers),
            "message": f"{len(papers)} paper(s) enviados a WhatsApp." if sent else "Error al enviar — ¿está el bridge activo?",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/arxiv/dryrun", methods=["POST"])
def api_arxiv_dryrun():
    try:
        import importlib, config as cfg
        importlib.reload(cfg)
        papers, _ = _fetch_and_save()
        return jsonify({"papers": papers, "total": len(papers), "hours_back": cfg.HOURS_BACK})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/whatsapp", methods=["POST"])
def api_config_whatsapp():
    import importlib
    data = request.get_json()
    number = data.get("number", "").strip().lstrip("+").replace(" ", "")
    if not number.isdigit() or len(number) < 8:
        return jsonify({"error": "Número inválido — solo dígitos, sin +, sin espacios"}), 400
    try:
        import config as cfg
        importlib.reload(cfg)
        config_path = os.path.join(os.path.dirname(__file__), "config.py")
        with open(config_path, encoding="utf-8") as f:
            content = f.read()
        import re
        content = re.sub(
            r'^WHATSAPP_NUMBER\s*=\s*"[^"]*"',
            f'WHATSAPP_NUMBER = "{number}"',
            content, flags=re.MULTILINE
        )
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        importlib.reload(cfg)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/arxiv/digests", methods=["GET"])
def api_arxiv_digests():
    try:
        from digester import list_digests
        return jsonify({"files": list_digests()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/arxiv/digest", methods=["GET"])
def api_arxiv_digest_file():
    filename = request.args.get("file", "").strip()
    if not filename or "/" in filename or ".." in filename or not filename.endswith(".html"):
        return jsonify({"error": "Invalid filename"}), 400
    filepath = os.path.join(os.path.dirname(__file__), "digests", filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    return Response(content, mimetype="text/html")


@app.route("/api/arxiv/logs", methods=["GET"])
def api_arxiv_logs():
    log_file = os.path.join(os.path.dirname(__file__), "agent.log")
    if not os.path.exists(log_file):
        return jsonify({"lines": [], "exists": False})
    try:
        with open(log_file, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return jsonify({
            "lines": [l.rstrip() for l in lines[-60:]],
            "exists": True,
            "total": len(lines),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/matrix", methods=["GET"])
def api_matrix_load():
    filepath = request.args.get("file", "").strip()
    if not filepath:
        return jsonify({"error": "No file path provided"}), 400
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return jsonify({"error": f"File not found: {filepath}"}), 404
    try:
        rows = []
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            for row in reader:
                rows.append(dict(row))
        return jsonify({"rows": rows, "columns": fieldnames, "total": len(rows)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/matrix/save", methods=["POST"])
def api_matrix_save():
    data = request.get_json()
    filepath = os.path.expanduser(data.get("file", "").strip())
    rows = data.get("rows", [])
    if not filepath:
        return jsonify({"error": "No file path provided"}), 400
    if not rows:
        return jsonify({"error": "No rows provided"}), 400
    try:
        fieldnames = list(rows[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        return jsonify({"ok": True, "saved": len(rows)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/translate", methods=["POST"])
def api_translate():
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="en", target="es").translate(text)
        return jsonify({"translated": translated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/arxiv/resolve", methods=["POST"])
def api_arxiv_resolve():
    """Resuelve IDs de arXiv a bibcodes de ADS en batch."""
    import urllib.request, urllib.parse
    data = request.get_json()
    ids = [i.strip() for i in data.get("ids", []) if i.strip()][:25]
    if not ids:
        return jsonify({"results": {}})
    token = os.getenv("ADS_TOKEN")
    results = {}
    for arxiv_id in ids:
        clean = arxiv_id.replace("arXiv:", "").replace("arxiv:", "")
        try:
            params = urllib.parse.urlencode({
                "q": f'identifier:"arXiv:{clean}"',
                "fl": "bibcode,citation_count",
                "rows": 1,
            })
            req = urllib.request.Request(
                f"https://api.adsabs.harvard.edu/v1/search/query?{params}",
                headers={"Authorization": f"Bearer {token}"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                docs = json.load(r).get("response", {}).get("docs", [])
            if docs:
                bc = docs[0]["bibcode"]
                results[clean] = {
                    "bibcode": bc,
                    "url": f"https://ui.adsabs.harvard.edu/abs/{urllib.parse.quote(bc)}",
                    "citations": docs[0].get("citation_count", 0),
                }
        except Exception:
            pass
    return jsonify({"results": results})


@app.route("/api/arxiv/bibtex_arxiv", methods=["GET"])
def api_arxiv_bibtex_arxiv():
    """Descarga el BibTeX de arXiv directamente (sin ADS)."""
    import urllib.request
    arxiv_id = request.args.get("id", "").strip()
    if not arxiv_id:
        return jsonify({"error": "No ID provided"}), 400
    try:
        req = urllib.request.Request(
            f"https://export.arxiv.org/bibtex/{arxiv_id}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            bibtex = r.read().decode("utf-8").strip()
        return Response(
            bibtex, mimetype="application/x-bibtex",
            headers={"Content-Disposition": f'attachment; filename="{arxiv_id}.bib"'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config", methods=["GET"])
def api_config_get():
    try:
        import importlib, config as cfg
        importlib.reload(cfg)
        return jsonify({
            "categories": cfg.CATEGORIES,
            "keywords": cfg.KEYWORDS,
            "hours_back": cfg.HOURS_BACK,
            "max_results": cfg.MAX_RESULTS,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/save", methods=["POST"])
def api_config_save():
    import importlib
    data = request.get_json()
    categories = [c.strip() for c in data.get("categories", []) if c.strip()]
    keywords   = [k.strip() for k in data.get("keywords",   []) if k.strip()]
    hours_back  = max(1,  min(168, int(data.get("hours_back",  24))))
    max_results = max(10, min(500, int(data.get("max_results", 50))))
    if not categories or not keywords:
        return jsonify({"error": "Categories and keywords cannot be empty"}), 400
    try:
        import config as cfg
        whatsapp = getattr(cfg, "WHATSAPP_NUMBER", "")
        config_path = os.path.join(os.path.dirname(__file__), "config.py")
        cats = json.dumps(categories, indent=4)
        kws  = json.dumps(keywords,   indent=4)
        content = f'''# Número de WhatsApp que recibirá los mensajes (sin + ni espacios)
WHATSAPP_NUMBER = "{whatsapp}"

# Categorías de arXiv a monitorear
CATEGORIES = {cats}

# Palabras clave para filtrar papers relevantes
KEYWORDS = {kws}

# Cuántos papers máximo traer por consulta
MAX_RESULTS = {max_results}

# Cuántas horas hacia atrás buscar papers nuevos (24 = papers del último día)
HOURS_BACK = {hours_back}
'''
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        importlib.reload(cfg)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    import threading
    def stop():
        import time, os, signal
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=stop, daemon=True).start()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=False, port=5000)
