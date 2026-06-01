#!/usr/bin/env python3
"""Sync Guy Laban's publications from Google Scholar into ``data/publications.json``.

What it does
------------
1. Pulls the author's profile + publication list from Google Scholar via the
   ``scholarly`` package.
2. For every publication, resolves the right journal / conference logo using
   :mod:`venue_logos` (so new papers automatically show the publisher badge).
3. Merges with the existing ``data/publications.json`` so we never lose data if
   Scholar rate-limits us — existing entries are updated (citation counts, etc.)
   and genuinely new papers are appended.
4. Writes the file back only when something actually changed.

The GitHub Actions workflow runs this on a schedule and commits the result, so
the website's publication list — and the logos next to each paper — stay current
with zero manual work.

Resilience
----------
Google Scholar aggressively blocks automated traffic. This script is written so
that a blocked/failed fetch is a *no-op*: it logs a warning, leaves the existing
seed data untouched, and exits 0 so the pipeline stays green. Optionally set a
``SCRAPERAPI_KEY`` env var to route requests through a proxy for reliability.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# Local module (same directory) — maps a venue string to a logo + type.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from venue_logos import resolve_logo  # noqa: E402

SCHOLAR_ID = os.environ.get("SCHOLAR_ID", "K7-LiJ0AAAAJ")
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "publications.json"

# Scholar truncates long author lists; keep output tidy.
MAX_AUTHORS_SHOWN = 7


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def log(msg: str) -> None:
    print(f"[fetch_publications] {msg}", flush=True)


def load_existing() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            log(f"WARNING: existing data file is invalid JSON ({exc}); starting fresh.")
    return {"metadata": {}, "publications": []}


def norm_title(title: str) -> str:
    """A loose key for de-duplicating the same paper across runs."""
    return "".join(ch for ch in (title or "").lower() if ch.isalnum())


def scholar_pub_url(pub: dict) -> str:
    """Best-effort canonical link for a Scholar publication entry."""
    cid = pub.get("author_pub_id")
    if cid:
        return (
            "https://scholar.google.com/citations?view_op=view_citation"
            f"&hl=en&user={SCHOLAR_ID}&citation_for_view={cid}"
        )
    pub_url = pub.get("pub_url")
    if pub_url:
        return pub_url
    title = pub.get("bib", {}).get("title", "")
    return "https://scholar.google.com/scholar?q=" + title.replace(" ", "+")


def shorten_authors(authors: str) -> str:
    parts = [a.strip() for a in (authors or "").split(",") if a.strip()]
    if len(parts) > MAX_AUTHORS_SHOWN:
        return ", ".join(parts[:MAX_AUTHORS_SHOWN]) + ", et al."
    return ", ".join(parts)


def build_record(pub: dict) -> dict | None:
    """Turn a ``scholarly`` publication dict into our publication schema."""
    bib = pub.get("bib", {}) or {}
    title = (bib.get("title") or "").strip()
    if not title:
        return None
    venue = (bib.get("venue") or bib.get("journal") or bib.get("citation") or "").strip()
    logo, ptype = resolve_logo(venue)
    try:
        year = int(str(bib.get("pub_year") or 0)[:4])
    except (TypeError, ValueError):
        year = 0
    return {
        "title": title,
        "authors": shorten_authors(bib.get("author", "")),
        "venue": venue or "—",
        "year": year,
        "citations": int(pub.get("num_citations") or 0),
        "url": scholar_pub_url(pub),
        "type": ptype,
        "logo": logo,
    }


# --------------------------------------------------------------------------- #
# Google Scholar fetch
# --------------------------------------------------------------------------- #
def fetch_from_scholar() -> tuple[dict | None, list[dict]]:
    """Return ``(metadata, records)``. On any failure returns ``(None, [])``."""
    try:
        from scholarly import scholarly, ProxyGenerator
    except ImportError:
        log("ERROR: the 'scholarly' package is not installed. Run `pip install scholarly`.")
        return None, []

    # Optional proxy for reliability in CI (Scholar blocks data-center IPs).
    api_key = os.environ.get("SCRAPERAPI_KEY")
    if api_key:
        try:
            pg = ProxyGenerator()
            if pg.ScraperAPI(api_key):
                scholarly.use_proxy(pg)
                log("Using ScraperAPI proxy for Google Scholar requests.")
        except Exception as exc:  # noqa: BLE001
            log(f"WARNING: could not initialise ScraperAPI proxy: {exc}")

    try:
        log(f"Fetching Scholar profile {SCHOLAR_ID} …")
        author = scholarly.search_author_id(SCHOLAR_ID)
        author = scholarly.fill(author, sections=["basics", "indices", "publications"])
    except Exception as exc:  # noqa: BLE001
        log(f"WARNING: Google Scholar fetch failed ({type(exc).__name__}: {exc}).")
        log("Keeping existing data unchanged.")
        return None, []

    meta = {
        "total_citations": int(author.get("citedby") or 0),
        "h_index": int(author.get("hindex") or 0),
        "i10_index": int(author.get("i10index") or 0),
        "interests": author.get("interests") or [],
    }

    records: list[dict] = []
    pubs = author.get("publications", []) or []
    log(f"Profile reports {len(pubs)} publications; building records …")
    for pub in pubs:
        rec = build_record(pub)
        if rec:
            records.append(rec)
    return meta, records


# --------------------------------------------------------------------------- #
# Merge + write
# --------------------------------------------------------------------------- #
def merge(existing: dict, meta: dict | None, fetched: list[dict]) -> tuple[dict, int, int]:
    pubs = list(existing.get("publications", []))
    by_key = {norm_title(p["title"]): p for p in pubs}

    added, updated = 0, 0
    for rec in fetched:
        key = norm_title(rec["title"])
        if key in by_key:
            cur = by_key[key]
            # Refresh volatile fields; keep a hand-curated URL if we have one.
            changed = False
            for field in ("citations", "year", "venue", "authors", "type", "logo"):
                if rec.get(field) and rec[field] != cur.get(field):
                    cur[field] = rec[field]
                    changed = True
            if rec.get("url") and not cur.get("url"):
                cur["url"] = rec["url"]
                changed = True
            updated += 1 if changed else 0
        else:
            pubs.append(rec)
            by_key[key] = rec
            added += 1

    pubs.sort(key=lambda p: (p.get("year", 0), p.get("citations", 0)), reverse=True)

    new_meta = dict(existing.get("metadata", {}))
    new_meta.update(
        {
            "name": "Guy Laban",
            "scholar_id": SCHOLAR_ID,
            "scholar_url": f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en",
            "last_updated": date.today().isoformat(),
        }
    )
    if meta:
        for k in ("total_citations", "h_index", "i10_index"):
            if meta.get(k):
                new_meta[k] = meta[k]
        if meta.get("interests"):
            new_meta["interests"] = meta["interests"]
        new_meta["source"] = "google-scholar"
        new_meta["synced_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    return {"metadata": new_meta, "publications": pubs}, added, updated


def main() -> int:
    existing = load_existing()
    meta, fetched = fetch_from_scholar()

    if not fetched:
        # Nothing fetched (offline / blocked). Still refresh last_updated? No —
        # leave the file byte-identical so the pipeline reports "no changes".
        log("No publications fetched; leaving data file untouched.")
        return 0

    merged, added, updated = merge(existing, meta, fetched)

    before = DATA_FILE.read_text(encoding="utf-8") if DATA_FILE.exists() else ""
    after = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"

    if after == before:
        log("Publications already up to date — no changes.")
        return 0

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(after, encoding="utf-8")
    log(f"Updated {DATA_FILE.relative_to(ROOT)}: +{added} new, {updated} refreshed, "
        f"{len(merged['publications'])} total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
