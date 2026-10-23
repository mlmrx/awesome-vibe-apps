# Raw discovery data

## Hand-entered external leads

Add one JSON object per line to `external-leads.jsonl`:

~~~json
{"id":"x:unique-post-or-project-slug","name":"Project name","description":"Short factual description","project_url":"https://project.example","repository_url":null,"source_platform":"x","discovery_url":"https://x.com/account/status/123","discovered_at":"YYYY-MM-DD","discovery_note":"Why this is a lead","suggested_category":"Other / Needs Review","suggested_project_kind":"unknown"}
~~~

Supported `source_platform` values are `web` and `x`. Leave suggested values out when uncertain. The generated catalog keeps these records unreviewed until a contributor finds and records first-party build evidence.

## API-collected metadata

- `github-repositories.jsonl` stores public repository metadata from GitHub Search.
- `devto-articles.jsonl` stores titles, descriptions, dates, tags, author names, and links from the public DEV Articles API. Article bodies are not copied.
- `hackernews-stories.jsonl` stores story titles, links, dates, author names, and engagement counters from the Hacker News Algolia API. Comment bodies are not copied.
- `generated-external-leads.jsonl` is rebuilt from likely first-person DEV build posts and `Show HN` submissions returned by the recorded searches. Treat every record as unreviewed.
- `github-search-snapshot.json` and `public-web-search-snapshot.json` preserve query and pagination coverage, including known caps.

Run `python scripts/collect_github.py` or `python scripts/collect_public_web.py` to refresh a source. Run `python scripts/build_catalog.py` to regenerate catalog/index files after collection.
