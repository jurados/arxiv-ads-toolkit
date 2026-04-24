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

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, render_template, Response
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)


def _paper_to_dict(paper: dict) -> dict:
    """Normalize a NASA ADS paper dict for JSON response."""
    import urllib.parse
    bibcode = paper.get("bibcode", "")
    title_raw = paper.get("title", [])
    title = title_raw[0] if title_raw else "No title"
    authors = paper.get("author", [])
    author_str = ", ".join(authors[:4])
    if len(authors) > 4:
        author_str += f" +{len(authors)-4} more"
    return {
        "bibcode": bibcode,
        "title": title,
        "year": paper.get("year", ""),
        "doctype": paper.get("doctype", ""),
        "authors": author_str,
        "abstract": paper.get("abstract", ""),
        "url": f"https://ui.adsabs.harvard.edu/abs/{urllib.parse.quote(bibcode)}",
        "level": paper.get("level", None),
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
        from ads_search import search_author
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
        from ads_topics import search_topics
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
        from ads_references import fetch_references, is_arxiv_id, arxiv_to_bibcode
        bibcode = identifier
        if is_arxiv_id(identifier):
            bibcode = arxiv_to_bibcode(identifier)
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
        from ads_citations import fetch_citations, is_arxiv_id, arxiv_to_bibcode
        bibcode = identifier
        if is_arxiv_id(identifier):
            bibcode, _ = arxiv_to_bibcode(identifier)
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
        from ads_similar import search_similar_bibcode, search_similar_text, is_arxiv_id, extract_keywords
        import urllib.parse
        if mode == "bibcode":
            bibcode = data.get("bibcode", "").strip()
            if not bibcode:
                return jsonify({"error": "Bibcode required"}), 400
            if is_arxiv_id(bibcode):
                from ads_similar import ADS_API, ADS_TOKEN
                import urllib.request
                clean = bibcode.replace("arXiv:", "").replace("arxiv:", "")
                params = urllib.parse.urlencode({"q": f'identifier:"arXiv:{clean}"', "fl": "bibcode", "rows": 1})
                req = urllib.request.Request(f"{ADS_API}?{params}", headers={"Authorization": f"Bearer {ADS_TOKEN}"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    docs = json.load(r).get("response", {}).get("docs", [])
                bibcode = docs[0]["bibcode"] if docs else None
                if not bibcode:
                    return jsonify({"error": "Could not resolve arXiv ID"}), 404
            papers, total = search_similar_bibcode(bibcode, year=year, rows=rows)
            return jsonify({"papers": [_paper_to_dict(p) for p in papers], "total": total, "mode": "bibcode"})
        else:
            text = data.get("text", "").strip()
            if not text:
                return jsonify({"error": "Text required"}), 400
            papers, total, keywords = search_similar_text(text, year=year, rows=rows)
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
        from ads_chain import build_chain, is_arxiv_id, arxiv_to_bibcode
        bibcode = identifier
        if is_arxiv_id(identifier):
            bibcode = arxiv_to_bibcode(identifier)
            if not bibcode:
                return jsonify({"error": f"Could not resolve arXiv ID: {identifier}"}), 404
        papers = build_chain(bibcode, levels=levels, max_per_level=max_per_level, rows_per_paper=rows, year=year)
        return jsonify({"papers": [_paper_to_dict(p) for p in papers], "total": len(papers), "bibcode": bibcode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json()
    identifier = data.get("identifier", "").strip()
    if not identifier:
        return jsonify({"error": "Bibcode or arXiv ID required"}), 400
    try:
        import tempfile
        from ads_download import download_pdf, is_arxiv_id, arxiv_to_bibcode, get_paper_metadata, get_pdf_url, make_filename
        bibcode = identifier
        if is_arxiv_id(identifier):
            bibcode = arxiv_to_bibcode(identifier)
            if not bibcode:
                return jsonify({"error": f"Could not resolve: {identifier}"}), 404
        pdf_url, source = get_pdf_url(bibcode)
        if not pdf_url:
            return jsonify({"error": "No open-access PDF found for this paper"}), 404
        metadata = get_paper_metadata(bibcode)
        filename = make_filename(bibcode, metadata)
        import urllib.request
        req = urllib.request.Request(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            pdf_bytes = r.read()
        if not pdf_bytes[:4] == b"%PDF":
            return jsonify({"error": "Source returned non-PDF content (likely paywalled)"}), 403
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
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


@app.route("/api/arxiv/dryrun", methods=["POST"])
def api_arxiv_dryrun():
    try:
        from fetcher import fetch_papers
        papers = fetch_papers()
        return jsonify({"papers": papers, "total": len(papers)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
