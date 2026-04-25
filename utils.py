"""Shared utilities for all ads_* modules."""
import os
import json
import urllib.parse
import urllib.request
from dotenv import load_dotenv

load_dotenv()

ADS_TOKEN = os.getenv("ADS_TOKEN")
ADS_API   = "https://api.adsabs.harvard.edu/v1/search/query"


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
