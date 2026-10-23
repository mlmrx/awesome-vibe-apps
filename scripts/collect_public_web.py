#!/usr/bin/env python3
"""Collect public article and Hacker News metadata for vibe-app discovery.

This collector stores titles, links, and limited public metadata only. It does
not fetch article bodies, crawl arbitrary sites, or treat a source hit as proof
that a linked product used AI coding tools.
"""

from __future__ import annotations

import argparse
import calendar
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DEV_PATH = RAW_DIR / "devto-articles.jsonl"
HN_PATH = RAW_DIR / "hackernews-stories.jsonl"
LEADS_PATH = RAW_DIR / "generated-external-leads.jsonl"
SNAPSHOT_PATH = RAW_DIR / "public-web-search-snapshot.json"
USER_AGENT = "awesome-vibe-apps-research/1.0 (public metadata discovery; github.com/mlmrx/awesome-vibe-apps)"
DEV_TAGS = ["vibecoding"]
HN_QUERIES = ["vibe coding", "vibe coded", "vibe-coded", "vibecoding", "vibecoded", "vibe-code"]
HN_DATE_RANGES = [
    ("through-2024", "2007-01-01", "2025-01-01"),
    ("2025-H1", "2025-01-01", "2025-07-01"),
    ("2025-H2", "2025-07-01", "2026-01-01"),
    ("2026-Q1", "2026-01-01", "2026-04-01"),
    ("2026-Q2", "2026-04-01", "2026-07-01"),
    ("2026-Q3", "2026-07-01", "2026-10-01"),
    ("2026-Q4-to-2026-10-23", "2026-10-01", "2026-10-23"),
]
DEV_MAX_PAGES = 25
HN_MAX_PAGES = 10
PER_PAGE = 100

CREATOR_BUILD_RE = re.compile(
    r"\b(i|we)\s+(built|made|created|shipped|launched|vibe[- ]coded)\b"
    r"|\bmy\s+(first|new|personal|side[- ]project)\s+"
    r"(app|website|web app|game|project|tool|saas)\b"
    r"|\bwhat\s+i\s+(built|made|shipped)\b",
    re.I,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def fetch_json(url: str, delay: float) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read())
            if delay:
                time.sleep(delay)
            return payload
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 4:
                raise
            retry_after = error.headers.get("Retry-After")
            wait = min(60.0, float(retry_after)) if retry_after and retry_after.isdigit() else 2 ** (attempt + 1)
            print(f"HTTP {error.code}; retrying after {wait:g}s", flush=True)
            time.sleep(wait)


def load_jsonl(path: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    if path.exists():
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    row = json.loads(line)
                    records[row["id"]] = row
    return records


def write_jsonl(path: Path, records: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as stream:
        for key in sorted(records):
            stream.write(json.dumps(records[key], ensure_ascii=False, sort_keys=True) + "\n")
    temp.replace(path)


def collect_dev(tag: str, max_pages: int, delay: float, records: dict[str, dict]) -> dict:
    query = f"tag:{tag}"
    pages_received = 0
    new_count = 0
    exhausted = False
    for page in range(1, max_pages + 1):
        params = urllib.parse.urlencode({"tag": tag, "per_page": PER_PAGE, "page": page})
        url = f"https://dev.to/api/articles?{params}"
        try:
            payload = fetch_json(url, delay)
        except urllib.error.HTTPError as error:
            if error.code in (404, 422):
                break
            raise
        if not isinstance(payload, list):
            raise RuntimeError(f"DEV API returned unexpected payload for {query}, page {page}")
        pages_received += 1
        if not payload:
            exhausted = True
            break
        for item in payload:
            key = f"devto:{item['id']}"
            collected_at = utc_now()
            record = records.get(key, {
                "id": key,
                "source_platform": "web",
                "source_name": "DEV Community public Articles API",
                "source_url": item.get("url"),
                "source_record_id": item["id"],
                "first_collected_at": collected_at,
                "matched_queries": [],
            })
            record.update({
                "title": item.get("title"),
                "description": item.get("description"),
                "url": item.get("url"),
                "published_at": item.get("published_at"),
                "tag_list": item.get("tag_list") or [],
                "author": (item.get("user") or {}).get("username"),
                "author_url": (item.get("user") or {}).get("website_url"),
                "reading_time_minutes": item.get("reading_time_minutes"),
                "public_reactions_count": item.get("public_reactions_count"),
                "matched_queries": sorted(set(record.get("matched_queries", [])) | {query}),
                "last_collected_at": collected_at,
            })
            if key not in records:
                new_count += 1
            records[key] = record
        print(f"DEV {query} page {page}: {len(payload)} articles; {len(records)} unique", flush=True)
        if len(payload) < PER_PAGE:
            exhausted = True
            break
    return {
        "query": query,
        "reported_total": None,
        "pages_requested_max": max_pages,
        "pages_received": pages_received,
        "records_seen": sum(query in row.get("matched_queries", []) for row in records.values()),
        "new_records_this_run": new_count,
        "page_cap_partial": pages_received == max_pages and not exhausted,
        "completed_at": utc_now(),
    }


def epoch(date_string: str) -> int:
    date = datetime.strptime(date_string, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return calendar.timegm(date.utctimetuple())


def collect_hn(query: str, max_pages: int, delay: float, records: dict[str, dict], date_range: tuple[str, str, str]) -> dict:
    range_label, start_date, end_date = date_range
    query_label = f"{query} [{range_label}]"
    pages_received = 0
    total = None
    pages_available = None
    new_count = 0
    for page in range(max_pages):
        params = urllib.parse.urlencode({
            "query": query,
            "tags": "story",
            "hitsPerPage": PER_PAGE,
            "page": page,
            "numericFilters": f"created_at_i>={epoch(start_date)},created_at_i<{epoch(end_date)}",
        })
        url = f"https://hn.algolia.com/api/v1/search_by_date?{params}"
        payload = fetch_json(url, delay)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Hacker News Algolia returned unexpected payload for {query}")
        pages_received += 1
        total = payload.get("nbHits")
        pages_available = payload.get("nbPages")
        hits = payload.get("hits") or []
        if not hits:
            break
        for hit in hits:
            if hit.get("_tags") and "story" not in hit["_tags"]:
                continue
            object_id = hit.get("objectID")
            if not object_id:
                continue
            key = f"hn:{object_id}"
            collected_at = utc_now()
            record = records.get(key, {
                "id": key,
                "source_platform": "web",
                "source_name": "Hacker News Algolia Search API",
                "source_record_id": object_id,
                "first_collected_at": collected_at,
                "matched_queries": [],
            })
            record.update({
                "title": hit.get("title") or hit.get("story_title"),
                "url": hit.get("url") or hit.get("story_url"),
                "author": hit.get("author"),
                "published_at": hit.get("created_at"),
                "points": hit.get("points"),
                "num_comments": hit.get("num_comments"),
                "discussion_url": f"https://news.ycombinator.com/item?id={object_id}",
                "matched_queries": sorted(set(record.get("matched_queries", [])) | {query_label}),
                "last_collected_at": collected_at,
            })
            if key not in records:
                new_count += 1
            records[key] = record
        print(f"HN {query_label!r} page {page + 1}: {len(hits)} stories; {len(records)} unique", flush=True)
        if page + 1 >= min(max_pages, pages_available or max_pages) or len(hits) < PER_PAGE:
            break
    return {
        "query": query_label,
        "date_range_utc": {"start_inclusive": start_date, "end_exclusive": end_date},
        "reported_total": total,
        "reported_pages": pages_available,
        "pages_requested_max": max_pages,
        "pages_received": pages_received,
        "records_seen": sum(query in row.get("matched_queries", []) for row in records.values()),
        "new_records_this_run": new_count,
        "search_cap_partial": bool(total and total > pages_received * PER_PAGE),
        "completed_at": utc_now(),
    }


def candidate_leads(dev_rows: dict[str, dict], hn_rows: dict[str, dict]) -> dict[str, dict]:
    leads: dict[str, dict] = {}
    for row in dev_rows.values():
        combined = f"{row.get('title') or ''} {row.get('description') or ''}"
        if not CREATOR_BUILD_RE.search(combined):
            continue
        leads[row["id"]] = {
            "id": row["id"],
            "name": row.get("title"),
            "description": row.get("description"),
            "project_url": None,
            "source_platform": "web",
            "discovery_url": row.get("url"),
            "discovery_source": "DEV Community",
            "discovered_at": (row.get("published_at") or "")[:10] or None,
            "discovery_note": "Article matched the public vibecoding tag and a first-person build/launch title or description pattern; app identity and AI build claim are unreviewed.",
            "suggested_project_kind": "unknown",
        }
    for row in hn_rows.values():
        title = row.get("title") or ""
        project_url = row.get("url")
        if not re.match(r"^Show HN\s*:", title, re.I) or not project_url:
            continue
        leads[row["id"]] = {
            "id": row["id"],
            "name": title,
            "description": None,
            "project_url": project_url,
            "source_platform": "web",
            "discovery_url": row.get("discussion_url"),
            "discovery_source": "Hacker News",
            "discovered_at": (row.get("published_at") or "")[:10] or None,
            "discovery_note": "Show HN submission matched a public vibe-coding phrase query; submitted product identity and AI build claim are unreviewed.",
            "suggested_project_kind": "app_candidate",
        }
    return leads


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev-max-pages", type=int, default=DEV_MAX_PAGES, help="Maximum DEV pages for each tag; 100 articles per page.")
    parser.add_argument("--hn-max-pages", type=int, default=HN_MAX_PAGES, help="Maximum Hacker News pages for each phrase; 100 stories per page.")
    parser.add_argument("--delay", type=float, default=0.4, help="Seconds between public API requests.")
    args = parser.parse_args()
    if args.dev_max_pages < 1 or args.hn_max_pages < 1 or args.delay < 0:
        parser.error("page caps must be positive and delay must be nonnegative")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dev_records = load_jsonl(DEV_PATH)
    hn_records = load_jsonl(HN_PATH)
    query_stats = []
    for tag in DEV_TAGS:
        query_stats.append(collect_dev(tag, args.dev_max_pages, args.delay, dev_records))
        write_jsonl(DEV_PATH, dev_records)
    for query in HN_QUERIES:
        for date_range in HN_DATE_RANGES:
            query_stats.append(collect_hn(query, args.hn_max_pages, args.delay, hn_records, date_range))
            write_jsonl(HN_PATH, hn_records)

    leads = candidate_leads(dev_records, hn_records)
    write_jsonl(LEADS_PATH, leads)
    snapshot = {
        "collected_at": utc_now(),
        "sources": [
            {"name": "DEV Community public Articles API", "api": "https://developers.forem.com/api/v1", "records": len(dev_records), "query_stats": [s for s in query_stats if s["query"].startswith("tag:")]},
            {"name": "Hacker News Algolia Search API", "api": "https://hn.algolia.com/api", "records": len(hn_records), "query_stats": [s for s in query_stats if not s["query"].startswith("tag:")]},
        ],
        "generated_candidate_leads": len(leads),
        "limits": [
            "Article and story metadata only; no article bodies were copied.",
            "DEV collection is limited to the vibecoding tag and the requested page cap.",
            "Hacker News collection uses six phrase searches split into the recorded UTC time ranges and the requested page cap per query/range.",
            "Hacker News Algolia may cap each date-sliced phrase result at 1,000 records; partial slices are flagged.",
            "Search results are leads, not proof that a product used AI coding tools.",
        ],
    }
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"devto_records": len(dev_records), "hackernews_stories": len(hn_records), "generated_candidate_leads": len(leads), "snapshot": str(SNAPSHOT_PATH)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
