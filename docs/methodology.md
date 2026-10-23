# Collection, classification, and evaluation

## Collection snapshot

The GitHub corpus is collected from direct public GitHub repository search queries. The exact queries, reported result counts, page counts, and collection dates are in [the query snapshot](../data/raw/github-search-snapshot.json). The collector stores repository metadata only; it does not copy READMEs, source files, or another directory's app records.

The current queries search public, non-fork repositories matching vibe-coding topic tags, README phrases such as “vibe coded”, “vibe-coded”, and “vibecoded”, and explicit tool phrases such as “built with Lovable”, “built with Bolt”, “built with Cursor”, and “built with Claude”. Some overlapping term searches are intentional; repositories are deduplicated by GitHub's stable numeric repository ID, so renames stay one candidate. Search is indexed and can change between refreshes. GitHub limits pagination and result depth, so this is a snapshot of discovery leads rather than an exhaustive census. See the [GitHub Search overview](https://docs.github.com/en/search-github/getting-started-with-searching-on-github/about-searching-on-github), [REST API rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api), and [REST API pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api).

High-volume README searches are also split into star ranges (0–1, 2–5, and, for selected tool phrases, 6–10 and over 10) so low-star prototypes are represented alongside better-known projects. Every query is capped at 1,000 results by the collector; the snapshot flags partial queries. Low star counts are a queueing signal only.

## Public web discovery

[`scripts/collect_public_web.py`](../scripts/collect_public_web.py) collects metadata from the [DEV public Articles API](https://developers.forem.com/api/v1) for the `vibecoding` tag and the [Hacker News Algolia Search API](https://hn.algolia.com/api) for six recorded phrase searches. It stores titles, dates, links, and limited counters, not article bodies. Page caps, query counts, collection time, and totals are in [the public web snapshot](../data/raw/public-web-search-snapshot.json). Likely first-person build posts and `Show HN` product submissions are kept as unreviewed leads; search phrase matches are not treated as proof of an AI-built product.

The [external lead index](../catalog/external-leads.md) combines generated API leads with contributor-entered leads from [external-leads.jsonl](../data/raw/external-leads.jsonl), including manually reviewed public Reddit showcase threads and X profile links. Public search-engine results can be used to add individual X or other web links with their original source URL. There is no authenticated X API collection in this project. Reddit's unauthenticated JSON endpoint returned 403 during this collection, so Reddit pages are not crawled; a public indexed source can still be entered as a sourced lead. This is not a complete search of the web, X, Reddit, product galleries, app stores, or private content.

The collector does not access authenticated/private pages, bypass access controls, or bulk-copy another directory's dataset. Where a gallery or directory is encountered, its own terms and removal process must be checked before any reuse; prefer source links and individual review over rehosting its catalog.

## Evidence levels

| Level | What it means |
|---|---|
| vibe_topic_tag_only_unverified | GitHub repository matched a vibe-coding topic query. Authorship is unknown. |
| readme_phrase_search_hit_unverified | GitHub repository matched a README phrase search. The hit is a lead and has not been manually checked. |
| creator_stated | A human reviewer recorded a first-party public build statement and linked the evidence. |
| unreviewed_source_lead | A public page or API result matched a discovery query; creator claim and project identity remain to be checked. |

Only the last level is used for the human-reviewed examples. Even then, it records what the creator says; it is not forensic verification of code authorship.

## Category and project-kind rules

metadata_rules_v1 applies ordered keyword rules to a repository's name, description, and topic tags. Domain/function categories take precedence over the AI & Agents fallback, so an AI-assisted finance app can still be browsed under Finance. Project kinds distinguish app candidates, website candidates, developer tools, templates/demos, resource directories, and unknowns. These labels can be wrong and should be treated as navigation aids. Other / Needs Review is a valid result, not a quality rating.

## Possible “AI slop” review screen

The screen reports observable signals: missing description, no homepage linked, zero or one star, very small repository metadata, resource/template/demo/example wording, or archived status. Two signals put a record in the review queue; three or more are marked to review first. Star count, repository size, or missing links alone do not establish project quality or origin. The screen does not inspect code, run the app, assess user value, or infer AI authorship.

## Evaluation status

Machine-screened candidates have evaluation.level = repository_metadata_screen; their build origin, availability, functionality, user experience, security/privacy, and maintenance have not been independently assessed. Human-reviewed examples currently document first-party build evidence and project-link reachability on a date. Their functionality, user experience, security/privacy, and maintenance remain unevaluated unless a record explicitly says otherwise.

Future evaluations should record the evaluated URL and version, date, reproducible steps, findings, and evidence. Keep availability, functional behavior, usability, maintenance, and security/privacy as separate fields so one successful check does not imply the others passed.
