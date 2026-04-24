# arXiv Agent & NASA ADS Toolkit

A set of tools for astronomers to monitor new papers and build literature matrices. Built for research in supernovae, transients, ML/DL applied to astrophysics, and multimodality.

## Features

| Tool | Description |
|---|---|
| **Web interface** | Browser UI for all NASA ADS tools — dark/light mode, ES/EN toggle, abstract translation |
| **arXiv Daily Agent** | Monitors arXiv daily and sends new papers via WhatsApp (translated to Spanish) |
| `ads-search` | Search NASA ADS papers by author |
| `ads-topics` | Search NASA ADS papers by keyword or phrase |
| `ads-references` | Extract all references from a paper |
| `ads-citations` | Find all papers that cite a given work |
| `ads-similar` | Find papers similar to a bibcode or text paragraph |
| `ads-chain` | Trace reference chains across multiple levels |
| `ads-download` | Download open-access PDFs (arXiv, ADS, publisher) |

All NASA ADS tools are available both from the command line and from the web interface. They support `--export matrix.csv` to build a literature matrix incrementally.

---

## Web Interface

All tools are available as a local web app:

```bash
/home/jurados/arxiv-agent/run_web.sh
# Open: http://localhost:5000
```

Features: dark/light mode toggle · ES/EN language toggle · one-click abstract translation (Google Translate) · CSV export · PDF download directly from the browser.

---

## Requirements

- Python 3.10+
- NASA ADS token (free): https://ui.adsabs.harvard.edu/user/settings/token
- WhatsApp MCP server (for the daily agent): https://github.com/lharries/whatsapp-mcp

```bash
git clone https://github.com/jurados/arxiv-ads-toolkit
cd arxiv-ads-toolkit
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Create a `.env` file:
```
ADS_TOKEN=your_nasa_ads_token
```

Add aliases to `~/.bashrc`:
```bash
alias ads-search="/path/to/arxiv-ads-toolkit/ads_search.py"
alias ads-topics="/path/to/arxiv-ads-toolkit/ads_topics.py"
alias ads-references="/path/to/arxiv-ads-toolkit/ads_references.py"
alias ads-citations="/path/to/arxiv-ads-toolkit/ads_citations.py"
alias ads-similar="/path/to/arxiv-ads-toolkit/ads_similar.py"
alias ads-chain="/path/to/arxiv-ads-toolkit/ads_chain.py"
alias ads-download="/path/to/arxiv-ads-toolkit/ads_download.py"
```

---

## Usage

### Daily arXiv Agent

Runs automatically via cron at 10:00 AM and 15:00 PM (Chile time). Sends new papers matching your keywords via WhatsApp with abstracts translated to Spanish.

```bash
# Manual run
venv/bin/python main.py

# Test without sending
venv/bin/python main.py --dry-run
```

Edit `config.py` to customize keywords, categories, and WhatsApp number.

---

### NASA ADS Tools

All tools accept `--year 2023` or `--year 2020-2023` and `--export matrix.csv`.

**Search by author:**
```bash
ads-search "Forster, Francisco"
ads-search "Forster, Francisco" --year 2020-2023 --first-author
ads-search "Forster, Francisco" --export matrix.csv
```

**Search by topic:**
```bash
ads-topics "supernova classification"
ads-topics "kilonova" --year 2024 --rows 30
ads-topics "deep learning transient" --field title --export matrix.csv
```

**Extract references from a paper:**
```bash
ads-references "2022AJ....164..195F"          # bibcode
ads-references "2301.07688"                   # arXiv ID
ads-references "2022AJ....164..195F" --export matrix.csv
```

**Find papers that cite a work:**
```bash
ads-citations "2022AJ....164..195F"
ads-citations "2022AJ....164..195F" --year 2023-2026 --export matrix.csv
```

**Find similar papers:**
```bash
# By bibcode (semantic similarity from ADS)
ads-similar --bibcode "2022AJ....164..195F"

# By text paragraph
ads-similar --text "We propose a deep learning model to classify supernovae light curves"

# By file
ads-similar --file my_abstract.txt --export matrix.csv
```

**Trace reference chains:**
```bash
ads-chain "2022AJ....164..195F"                            # 2 levels (default)
ads-chain "2022AJ....164..195F" --levels 3 --max-per-level 10
ads-chain "2022AJ....164..195F" --levels 3 --export chain.csv
```

**Download open-access PDFs:**
```bash
ads-download "2022AJ....164..195F"                         # single paper
ads-download "2208.04310"                                  # by arXiv ID
ads-download "2022AJ....164..195F" --dir ~/papers          # custom dir
ads-download --from-csv matrix.csv                         # batch from CSV
ads-download --from-csv matrix.csv --dir ~/papers/matrix   # batch + custom dir
```

Prioritizes arXiv PDF (always free) > ADS hosted PDF > ADS scan > publisher PDF. Filenames follow the pattern `YYYY_LastName_FirstWord.pdf`.

---

## Literature Matrix

All tools export to the same CSV file, accumulating results without duplicates.

```bash
# Build a matrix combining multiple searches
ads-search "Forster, Francisco" --year 2018-2026      --export matrix.csv
ads-topics "supernova classification" --rows 20        --export matrix.csv
ads-references "2022AJ....164..195F"                   --export matrix.csv
ads-citations  "2022AJ....164..195F" --year 2022-2026  --export matrix.csv
ads-similar --file my_abstract.txt                     --export matrix.csv
ads-chain   "2022AJ....164..195F" --levels 3           --export matrix.csv
```

The CSV includes columns pre-filled by ADS (`bibcode`, `title`, `year`, `doctype`, `first_author`, `url`) and empty columns for you to fill (`method`, `key_finding`, `relevance`, `notes`). The `ads-chain` tool adds a `level` column indicating search depth.

---

## License

MIT
