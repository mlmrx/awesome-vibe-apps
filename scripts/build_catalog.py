#!/usr/bin/env python3
"""Classify raw GitHub leads and reviewed public examples into catalog files."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
RAW_REPOS = ROOT / "data" / "raw" / "github-repositories.jsonl"
EXTERNAL_LEADS = ROOT / "data" / "raw" / "external-leads.jsonl"
GENERATED_LEADS = ROOT / "data" / "raw" / "generated-external-leads.jsonl"
CURATED = ROOT / "data" / "curated.jsonl"
DEV_ARTICLES = ROOT / "data" / "raw" / "devto-articles.jsonl"
HN_STORIES = ROOT / "data" / "raw" / "hackernews-stories.jsonl"
CATALOG = ROOT / "data" / "catalog.jsonl"
INDEX = ROOT / "catalog" / "index.md"
EXTERNAL_INDEX = ROOT / "catalog" / "external-leads.md"
CATEGORIES_DIR = ROOT / "catalog" / "categories"

CATEGORY_RULES = [
    ("Developer Tools", r"\b(devtool|developer|sdk|cli|compiler|linter|vscode|extension|plugin|library|framework|api|code editor|coding)\b"),
    ("Education", r"\b(education|learning|learn|course|school|student|teacher|tutor|quiz|flashcard)\b"),
    ("Games & Entertainment", r"\b(game|gaming|arcade|puzzle|chess|music player|stream|entertainment)\b"),
    ("Creative & Media", r"\b(photo|image|video|audio|music|design|art|drawing|animation|editor|creator|content)\b"),
    ("Social & Community", r"\b(social|community|chat|forum|confession|dating|friend|messaging|feed)\b"),
    ("Health & Wellness", r"\b(health|wellness|fitness|medical|mental health|workout|nutrition|habit|meditation)\b"),
    ("Finance", r"\b(finance|expense|budget|banking|invoice|accounting|payment|crypto|wallet|stock|trading)\b"),
    ("Commerce & Food", r"\b(shop|store|commerce|ecommerce|marketplace|restaurant|food|menu|recipe|order|booking)\b"),
    ("Travel & Local", r"\b(travel|trip|hotel|flight|map|navigation|local|city guide|itinerary)\b"),
    ("Data & Analytics", r"\b(data|analytics|dashboard|visuali[sz]ation|chart|database|scraper|search engine|monitoring)\b"),
    ("Business & Productivity", r"\b(productivity|todo|task|project management|crm|business|workflow|calendar|notes|document|automation)\b"),
    # AI terms are a fallback category so vertical products such as AI finance,
    # education, or games remain discoverable by what they do.
    ("AI & Agents", r"\b(ai|artificial intelligence|llm|gpt|claude|agent|chatbot|rag|mcp|machine learning|openai|anthropic)\b"),
]

RESOURCE_RE = re.compile(r"\b(awesome[- ]list|curated list|directory of|list of (apps|tools|projects)|roadmap|dataset|collection of|resource hub)\b", re.I)
TEMPLATE_RE = re.compile(r"\b(template|starter|boilerplate|scaffold|example|tutorial|sample project|demo app|ui kit|landing page starter)\b", re.I)
DEVTOOL_RE = re.compile(r"\b(sdk|cli|library|framework|compiler|linter|extension|plugin|devtool|developer tool|code editor|api client)\b", re.I)
APP_RE = re.compile(r"\b(app|application|website|web app|mobile|saas|platform|dashboard|game|marketplace|service|tool)\b", re.I)


def lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def text_for(repo: dict) -> str:
    values = [repo.get("name"), repo.get("description"), *(repo.get("topics") or [])]
    return " ".join(str(value) for value in values if value).lower()


def classify_category(text: str) -> str:
    for category, pattern in CATEGORY_RULES:
        if re.search(pattern, text, re.I):
            return category
    return "Other / Needs Review"


def classify_kind(text: str, has_homepage: bool) -> str:
    if RESOURCE_RE.search(text):
        return "resource_or_directory"
    if TEMPLATE_RE.search(text):
        return "template_or_demo"
    if DEVTOOL_RE.search(text):
        return "developer_tool"
    if APP_RE.search(text):
        return "app_candidate"
    if has_homepage:
        return "website_candidate"
    return "unknown"


def screen_signals(repo: dict, text: str) -> list[str]:
    signals = []
    if not repo.get("description"):
        signals.append("missing_description")
    if not repo.get("homepage"):
        signals.append("no_homepage_linked")
    if int(repo.get("stargazers_count") or 0) <= 1:
        signals.append("zero_or_one_star")
    if int(repo.get("size") or 0) < 100:
        signals.append("very_small_repository_metadata")
    if RESOURCE_RE.search(text) or TEMPLATE_RE.search(text):
        signals.append("resource_template_demo_or_example_wording")
    if repo.get("archived"):
        signals.append("archived_repository")
    return signals


def markdown_cell(value: object) -> str:
    text = str(value or "").replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()
    for character in ("`", "*", "_", "[", "]", "<", ">"):
        text = text.replace(character, "\\" + character)
    return text


def markdown_link(label: object, url: object) -> str:
    target = str(url or "").strip()
    try:
        scheme = urlsplit(target).scheme
    except ValueError:
        return markdown_cell(label)
    if scheme not in ("http", "https"):
        return markdown_cell(label)
    return f"[{markdown_cell(label)}](<{target}>)"


def external_markdown_row(row: dict) -> str:
    project_url = row.get("project_url")
    discovery_url = row.get("discovery_url")
    project_cell = markdown_link(project_url, project_url) if project_url else "Not identified"
    source_cell = markdown_link("source", discovery_url) if discovery_url else "Not supplied"
    source_name = row.get("discovery_source") or ", ".join(row["source_platforms"])
    return (
        f"| {markdown_cell(row['name'])} | {markdown_cell(source_name)} | "
        f"{project_cell} | {source_cell} |"
    )


def main() -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    output: list[dict] = []
    for row in lines(RAW_REPOS):
        text = text_for(row)
        signals = screen_signals(row, text)
        n = len(signals)
        if n >= 3:
            screen = "multiple_signals_review_first"
        elif n == 2:
            screen = "some_signals_review"
        else:
            screen = "few_or_no_signals"
        readme_query = any("in:readme" in q for q in row.get("matched_queries", []))
        output.append({
            "id": "github:" + str(row["id"]),
            "record_type": "github_repository_candidate",
            "status": "machine_screened_unreviewed",
            "name": row.get("name") or row["full_name"],
            "description": row.get("description"),
            "category": classify_category(text),
            "project_kind": classify_kind(text, bool(row.get("homepage"))),
            "project_url": row.get("homepage") or row["html_url"],
            "repository_url": row["html_url"],
            "source_platforms": ["github"],
            "discovery_queries": row.get("matched_queries", []),
            "build_claim_status": "readme_phrase_search_hit_unverified" if readme_query else "vibe_topic_tag_only_unverified",
            "evaluation_method": "metadata_rules_v1",
            "evaluation_as_of": now,
            "reachability_status": "not_checked",
            "runtime_status": "not_evaluated",
            "evaluation": {
                "level": "repository_metadata_screen",
                "build_origin": "unverified",
                "product_identity": "heuristic",
                "availability": "not_checked",
                "functionality": "not_checked",
                "user_experience": "not_checked",
                "security_privacy": "not_checked",
                "maintenance": "metadata_only",
            },
            "ai_slop_screen": screen,
            "ai_slop_screen_signals": signals,
            "github_metadata": {
                "stars": row.get("stargazers_count"),
                "forks": row.get("forks_count"),
                "language": row.get("language"),
                "topics": row.get("topics") or [],
                "created_at": row.get("created_at"),
                "pushed_at": row.get("pushed_at"),
                "archived": row.get("archived"),
                "size_kb": row.get("size"),
                "license_spdx_id": (row.get("license") or {}).get("spdx_id") if isinstance(row.get("license"), dict) else None,
            },
            "first_collected_at": row.get("first_collected_at"),
            "last_collected_at": row.get("last_collected_at"),
        })

    for row in lines(EXTERNAL_LEADS) + lines(GENERATED_LEADS):
        external_text = f"{row.get('name') or ''} {row.get('description') or ''}".lower()
        output.append({
            "id": row["id"],
            "record_type": "external_discovery_lead",
            "status": "unreviewed_source_lead",
            "name": row.get("name") or row["id"],
            "description": row.get("description"),
            "category": row.get("suggested_category") or classify_category(external_text),
            "project_kind": row.get("suggested_project_kind") or classify_kind(external_text, bool(row.get("project_url"))),
            "project_url": row.get("project_url"),
            "repository_url": row.get("repository_url"),
            "source_platforms": [row["source_platform"]],
            "discovery_url": row.get("discovery_url"),
            "discovery_source": row.get("discovery_source"),
            "matched_queries": row.get("matched_queries", []),
            "discovered_at": row.get("discovered_at"),
            "discovery_note": row.get("discovery_note"),
            "build_claim_status": "unverified",
            "evaluation_method": "source_lead_record",
            "evaluation_as_of": now,
            "reachability_status": "not_checked",
            "runtime_status": "not_evaluated",
            "evaluation": {
                "level": "external_source_lead",
                "build_origin": "unverified",
                "product_identity": "unreviewed",
                "availability": "not_checked",
                "functionality": "not_checked",
                "user_experience": "not_checked",
                "security_privacy": "not_checked",
                "maintenance": "not_checked",
            },
            "ai_slop_screen": "not_scored",
            "ai_slop_screen_signals": [],
        })

    for row in lines(CURATED):
        output.append({
            **row,
            "record_type": "first_party_build_evidence",
            "status": "human_reviewed_example",
            "evaluation_method": "manual_source_review",
            "evaluation_as_of": row.get("checked_at"),
            "reachability_status": row.get("reachability_status", "checked_on_date"),
            "runtime_status": "not_independently_evaluated",
            "evaluation": {
                "level": "first_party_source_review",
                "build_origin": "creator_stated",
                "product_identity": "human_reviewed",
                "availability": row.get("availability_status", "project_link_checked_on_date"),
                "functionality": "not_checked",
                "user_experience": "not_checked",
                "security_privacy": "not_checked",
                "maintenance": "not_checked",
            },
            "ai_slop_screen": "not_scored",
            "ai_slop_screen_signals": [],
        })

    output.sort(key=lambda row: (row.get("category", ""), row.get("name", "").lower(), row["id"]))
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG.open("w", encoding="utf-8", newline="\n") as target:
        for row in output:
            target.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    github_rows = [row for row in output if row["record_type"] == "github_repository_candidate"]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in github_rows:
        grouped[row["category"]].append(row)
    curated_rows = [row for row in output if row["record_type"] == "first_party_build_evidence"]
    external_rows = [row for row in output if row["record_type"] == "external_discovery_lead"]
    external_by_source = Counter(row.get("discovery_source") or row["source_platforms"][0] for row in external_rows)
    curated_http_statuses = Counter(
        f"HTTP {row['http_check_status']}" if isinstance(row.get("http_check_status"), int) else str(row.get("http_check_status", "not_checked"))
        for row in curated_rows
    )
    kinds = Counter(row["project_kind"] for row in github_rows)
    website_app_candidates = kinds.get("app_candidate", 0) + kinds.get("website_candidate", 0)
    screens = Counter(row["ai_slop_screen"] for row in github_rows)
    dev_article_count = len(lines(DEV_ARTICLES))
    hn_story_count = len(lines(HN_STORIES))

    CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)
    for old in CATEGORIES_DIR.glob("*.md"):
        old.unlink()
    category_links = []
    for category in sorted(grouped):
        slug = re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")
        category_file = CATEGORIES_DIR / f"{slug}.md"
        with category_file.open("w", encoding="utf-8", newline="\n") as target:
            target.write(f"# {category}\n\n")
            target.write(f"{len(grouped[category]):,} GitHub repository candidates. These are machine-screened leads, not verified app listings.\n\n")
            target.write("| Project | Summary | Kind | Stars | Slop screen |\n|---|---|---:|---:|---|\n")
            for row in grouped[category]:
                meta = row["github_metadata"]
                target.write(
                    f"| [{markdown_cell(row['name'])}]({row['repository_url']}) | "
                    f"{markdown_cell(row.get('description')) or 'No description supplied'} | "
                    f"{row['project_kind']} | {meta.get('stars') or 0} | {row['ai_slop_screen']} ({len(row['ai_slop_screen_signals'])} signals) |\n"
                )
        category_links.append(f"- [{category}](categories/{category_file.name}) — {len(grouped[category]):,}")

    snapshot_date = now[:10]
    EXTERNAL_INDEX.write_text(
        "# External discovery leads\n\n"
        "These records were discovered through public web APIs, indexed search, or contributor submissions. They are unreviewed leads: product identity, creator claims, availability, and quality have not been confirmed.\n\n"
        f"**{len(external_rows):,} unreviewed leads.**\n\n"
        "| Project or source title | Discovery source | Project URL | Evidence link |\n|---|---|---|---|\n"
        + "\n".join(external_markdown_row(row) for row in external_rows) + "\n",
        encoding="utf-8",
    )
    INDEX.write_text(
        "# Catalog index\n\n"
        f"Generated {snapshot_date}. This index is derived from [`data/catalog.jsonl`](../data/catalog.jsonl).\n\n"
        f"- **{len(github_rows):,}** unique GitHub repository candidates, deduplicated by stable repository ID.\n"
        f"- **{website_app_candidates:,}** have app or website signals by metadata rules (not individually confirmed).\n"
        f"- **{len(curated_rows)}** manually reviewed examples with first-party build evidence.\n"
        f"- Curated project URL checks: {', '.join(f'{label}: {count}' for label, count in sorted(curated_http_statuses.items())) or 'not recorded'}; these are route checks, not runtime tests.\n"
        f"- **{len(external_rows):,}** unreviewed external discovery leads (web/X; source counts in [`data/catalog-summary.json`](../data/catalog-summary.json)).\n"
        "- GitHub candidates have not had their app, AI authorship, reachability, or runtime independently verified.\n\n"
        f"- **{dev_article_count + hn_story_count:,} raw DEV/Hacker News metadata records** are stored separately from project leads.\n\n"
        "## By category\n\n" + "\n".join(category_links) + "\n\n"
        f"## Web and X leads\n\nSee the [external lead index](external-leads.md) and [public source coverage snapshot](../data/raw/public-web-search-snapshot.json).\n\n"
        "## Project kind\n\n" + "\n".join(f"- `{kind}` — {count:,}" for kind, count in sorted(kinds.items())) + "\n\n"
        "## Possible low-effort signals\n\n"
        "These are transparent metadata signals for a review queue. They do not establish that a project is AI-generated, low quality, or ‘AI slop’.\n\n"
        + "\n".join(f"- `{screen}` — {count:,}" for screen, count in sorted(screens.items())) + "\n",
        encoding="utf-8",
    )
    summary = {
        "generated_at": now,
        "github_repository_candidates": len(github_rows),
        "first_party_reviewed_examples": len(curated_rows),
        "curated_project_url_http_statuses": dict(sorted(curated_http_statuses.items())),
        "external_unreviewed_leads": len(external_rows),
        "external_leads_by_source": dict(sorted(external_by_source.items())),
        "public_web_source_records": {"devto_articles": dev_article_count, "hackernews_stories": hn_story_count},
        "app_or_website_candidates_by_metadata": website_app_candidates,
        "by_category": dict(sorted(Counter(row["category"] for row in github_rows).items())),
        "by_project_kind": dict(sorted(kinds.items())),
        "by_ai_slop_screen": dict(sorted(screens.items())),
        "notice": "Automated metadata classification is a lead triage aid, not a verification or quality verdict.",
    }
    (ROOT / "data" / "catalog-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    begin = "<!-- SNAPSHOT:START -->"
    end = "<!-- SNAPSHOT:END -->"
    if begin in readme and end in readme:
        snapshot_block = (
            f"{begin}\nAs of {snapshot_date}, this repository contains:\n\n"
            f"- **{len(github_rows):,} unique public GitHub repository candidates** from the recorded query set.\n"
            f"- **{website_app_candidates:,} app or website candidates** based on repository metadata cues.\n"
            f"- **{len(curated_rows)} human-reviewed examples** with first-party build evidence.\n"
            f"- **{curated_http_statuses.get('HTTP 200', 0)} curated project URLs returned HTTP 200; {curated_http_statuses.get('HTTP 404', 0)} returned HTTP 404** on the checked date. Product workflows were not tested.\n"
            f"- **{len(external_rows):,} unreviewed public web/X leads**.\n"
            f"- **{dev_article_count + hn_story_count:,} public DEV/Hacker News metadata records** behind those leads.\n"
            f"- **{screens.get('multiple_signals_review_first', 0) + screens.get('some_signals_review', 0):,} GitHub candidates with two or more possible low-effort signals**, for review only.\n\n"
            "The corpus is intentionally broad and noisy. Source hits and machine labels are discovery aids, not proof of AI authorship, app status, quality, safety, or current availability.\n"
            f"{end}"
        )
        start_index = readme.index(begin)
        end_index = readme.index(end, start_index) + len(end)
        readme_path.write_text(readme[:start_index] + snapshot_block + readme[end_index:], encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
