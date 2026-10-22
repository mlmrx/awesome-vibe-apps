# Contributing

Help make the directory larger and more useful while keeping evidence and evaluation status clear.

## Add a reviewed project

Add a JSON object on one line to data/curated.jsonl:

~~~json
{"id":"curated:project-slug","name":"Project name","description":"Factual one-sentence description.","category":"Business & Productivity","project_kind":"app","project_url":"https://example.com/","repository_url":"https://github.com/owner/repo","build_evidence_url":"https://example.com/creator-build-story","source_platforms":["github","web","x"],"build_tools_reported":["Tool name"],"checked_at":"YYYY-MM-DD","evidence_note":"What the first-party source says."}
~~~

Use only the platform names that apply. At least one public first-party source must say how AI coding tools were used. A project can be added to the raw lead corpus before that evidence is found, but it must remain marked unreviewed.

## Add discovery leads

For unreviewed web or X leads, add one JSON object per line to data/raw/external-leads.jsonl. Keep the original project URL, discovery post/article URL, platform, discovery date, and a short factual note. The generated catalog will keep these as unreviewed source leads. A launch post, search result, or third-party claim can help discovery, but it does not verify AI authorship or product quality.

## Classification and review

- Automated categories and project kinds are search aids. Correct them through the rules in scripts/build_catalog.py or by adding a human-reviewed record.
- ai_slop_screen_signals lists observable metadata signals such as missing descriptions, no homepage link, very small repository size, or template/demo wording. Do not treat the screen as proof of generated origin or poor quality.
- For a human app evaluation, record separate results for build evidence, reachability, functionality, user experience, maintenance, and security/privacy. Include the date, the exact project version or URL, and concrete findings.
- Keep unavailable projects in the record with their last known status; do not silently erase history.
- Do not copy another directory's bulk dataset or private information. Link to the original project and evidence.

## Regenerate generated files

After editing the curated file or classifier, run:

~~~powershell
python scripts/build_catalog.py
~~~

When refreshing GitHub metadata, run python scripts/collect_github.py first. Review the resulting snapshot and query provenance before submitting it.
