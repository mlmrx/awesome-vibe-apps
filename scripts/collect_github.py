#!/usr/bin/env python3
"""Collect public GitHub repository metadata for the independent catalog.

Uses the GitHub CLI's authenticated session, so no token is read from or written
to this project. Search results are leads, not proof that a project was
AI-built, is an app, or is currently usable.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
REPOS_PATH = RAW_DIR / "github-repositories.jsonl"
SNAPSHOT_PATH = RAW_DIR / "github-search-snapshot.json"
PER_PAGE = 100
MAX_PAGES = 10  # GitHub repository search exposes at most 1,000 results per query.

QUERIES = [
    "topic:vibe-coding stars:0..1 is:public fork:false",
    "topic:vibe-coding stars:2..5 is:public fork:false",
    "topic:vibe-coding stars:6..10 is:public fork:false",
    "topic:vibe-coding stars:>10 is:public fork:false",
    "topic:vibecoding stars:0..1 is:public fork:false",
    "topic:vibe-coded stars:0..1 is:public fork:false",
    '"vibe coded" in:readme is:public fork:false',
    '"vibe coding" in:readme is:public fork:false',
    '"vibe-coded" in:readme is:public fork:false',
    '"vibecoded" in:readme is:public fork:false',
    '"vibe-coded app" in:readme is:public fork:false',
    '"built with lovable" in:readme is:public fork:false',
    '"made with lovable" in:readme is:public fork:false',
    '"built with bolt" in:readme is:public fork:false',
    '"built with cursor" in:readme is:public fork:false',
    '"built with claude" in:readme is:public fork:false',
    '"built using claude" in:readme is:public fork:false',
    "topic:lovable is:public fork:false",
    "topic:bolt-new is:public fork:false",
    '"vibe coded" in:readme stars:0..1 is:public fork:false',
    '"vibe coded" in:readme stars:2..5 is:public fork:false',
    '"vibe coding" in:readme stars:0..1 is:public fork:false',
    '"vibe coding" in:readme stars:2..5 is:public fork:false',
    '"vibe-coded" in:readme stars:0..1 is:public fork:false',
    '"vibe-coded" in:readme stars:2..5 is:public fork:false',
    '"vibecoded" in:readme stars:0..1 is:public fork:false',
    '"vibecoded" in:readme stars:2..5 is:public fork:false',
    '"vibe-coded app" in:readme stars:0..1 is:public fork:false',
    '"vibe-coded app" in:readme stars:2..5 is:public fork:false',
    '"built with cursor" in:readme stars:0..1 is:public fork:false',
    '"built with cursor" in:readme stars:2..5 is:public fork:false',
    '"built with lovable" in:readme stars:0..1 is:public fork:false',
    '"built with lovable" in:readme stars:2..5 is:public fork:false',
    '"built with lovable" in:readme stars:6..10 is:public fork:false',
    '"built with lovable" in:readme stars:>10 is:public fork:false',
    '"built with claude" in:readme stars:0..1 is:public fork:false',
    '"built with claude" in:readme stars:2..5 is:public fork:false',
    '"built with claude" in:readme stars:6..10 is:public fork:false',
    '"built with claude" in:readme stars:>10 is:public fork:false',
]

FIELDS = (
    "id",
    "name",
    "full_name",
    "html_url",
    "description",
    "homepage",
    "topics",
    "stargazers_count",
    "watchers_count",
    "forks_count",
    "open_issues_count",
    "language",
    "created_at",
    "updated_at",
    "pushed_at",
    "archived",
    "disabled",
    "fork",
    "size",
    "license",
    "default_branch",
    "visibility",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def run_gh_api(endpoint: str, *, q: str | None = None, page: int | None = None) -> dict:
    command = ["gh", "api", "-X", "GET", endpoint]
    if q is not None:
        command.extend(["-f", f"q={q}", "-F", f"per_page={PER_PAGE}", "-F", f"page={page}"])
    for attempt in range(6):
        try:
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
        except subprocess.TimeoutExpired:
            if attempt == 5:
                raise RuntimeError("gh api request timed out after six attempts")
            wait = min(30, 2 ** (attempt + 1))
            print(f"GitHub request timed out; retrying in {wait} seconds ({attempt + 1}/6).", flush=True)
            time.sleep(wait)
            continue
        if result.returncode == 0:
            return json.loads(result.stdout)
        message = result.stderr.strip() or result.stdout.strip()
        lower = message.lower()
        if "rate limit" in lower or "secondary rate limit" in lower:
            wait = 65
            print(f"GitHub search rate limit reached; waiting {wait} seconds before retry {attempt + 1}/6.", flush=True)
            time.sleep(wait)
            continue
        transient_markers = (
            "forcibly closed", "wsarecv", "connection reset", "connection aborted",
            "timed out", "timeout", "unexpected eof", "tls handshake", "temporarily unavailable",
        )
        if any(marker in lower for marker in transient_markers) and attempt < 5:
            wait = min(30, 2 ** (attempt + 1))
            print(f"Transient GitHub connection error; retrying in {wait} seconds ({attempt + 1}/6).", flush=True)
            time.sleep(wait)
            continue
        raise RuntimeError(f"gh api failed ({result.returncode}): {message}")
    raise RuntimeError("gh api failed after six attempts")


def read_jsonl(path: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    if path.exists():
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    row = json.loads(line)
                    records[str(row["id"])] = row
    return records


def write_jsonl(path: Path, records: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as stream:
        for key in sorted(records):
            stream.write(json.dumps(records[key], ensure_ascii=False, sort_keys=True) + "\n")
    temp.replace(path)


def compact_repo(repo: dict, query: str) -> dict:
    item = {field: repo.get(field) for field in FIELDS}
    item["source_platform"] = "github"
    item["source_url"] = repo["html_url"]
    item["matched_queries"] = [query]
    item["first_collected_at"] = utc_now()
    item["last_collected_at"] = item["first_collected_at"]
    return item


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", help="Run only a matching query string; may repeat.")
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES, help="Maximum pages per query, up to 10.")
    parser.add_argument("--delay", type=float, default=2.1, help="Seconds between search requests.")
    args = parser.parse_args()
    if not 1 <= args.max_pages <= 10:
        parser.error("--max-pages must be between 1 and 10")

    selected = args.query or QUERIES
    records = read_jsonl(REPOS_PATH)
    snapshot = {"source": "GitHub REST Search API", "collected_at": utc_now(), "queries": []}
    if SNAPSHOT_PATH.exists():
        previous = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        snapshot = previous
        snapshot.setdefault("queries", [])

    for query in selected:
        print(f"Searching: {query}", flush=True)
        page_one = run_gh_api("search/repositories", q=query, page=1)
        total = int(page_one.get("total_count", 0))
        pages = min(args.max_pages, MAX_PAGES, max(1, math.ceil(total / PER_PAGE)))
        query_record = {
            "query": query,
            "reported_total": total,
            "pages_requested": pages,
            "pages_received": 0,
            "search_cap_partial": total > MAX_PAGES * PER_PAGE,
            "completed_at": None,
        }
        page_results = [(1, page_one)]
        for page in range(2, pages + 1):
            time.sleep(args.delay)
            page_results.append((page, run_gh_api("search/repositories", q=query, page=page)))

        for page, payload in page_results:
            for repo in payload.get("items", []):
                if repo.get("visibility") not in (None, "public") or repo.get("fork"):
                    continue
                key = str(repo["id"])
                if key not in records:
                    records[key] = compact_repo(repo, query)
                else:
                    record = records[key]
                    if record.get("full_name") != repo.get("full_name"):
                        previous_names = set(record.get("renamed_from", []))
                        if record.get("full_name"):
                            previous_names.add(record["full_name"])
                        previous_names.discard(repo.get("full_name"))
                        if previous_names:
                            record["renamed_from"] = sorted(previous_names)
                    for field in FIELDS:
                        if field in repo:
                            record[field] = repo.get(field)
                    if query not in record.setdefault("matched_queries", []):
                        record["matched_queries"].append(query)
                    record["last_collected_at"] = utc_now()
            query_record["pages_received"] += 1
            print(
                f"  page {page}/{pages}: {len(payload.get('items', []))} repos; "
                f"{len(records)} unique total",
                flush=True,
            )

        query_record["unique_repositories_seen"] = sum(
            query in row.get("matched_queries", []) for row in records.values()
        )
        query_record["completed_at"] = utc_now()
        snapshot["collected_at"] = utc_now()
        old = [q for q in snapshot["queries"] if q.get("query") != query]
        snapshot["queries"] = old + [query_record]
        write_jsonl(REPOS_PATH, records)
        SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  checkpointed {len(records)} unique repositories", flush=True)

    print(f"Complete: {len(records)} unique public repository candidates at {REPOS_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
