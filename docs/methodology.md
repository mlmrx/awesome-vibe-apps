# Collection, classification, and evaluation

## Collection snapshot

The GitHub corpus is collected from direct public GitHub repository search queries. The exact queries, reported result counts, page counts, and collection dates are in [the query snapshot](../data/raw/github-search-snapshot.json). The collector stores repository metadata only; it does not copy READMEs, source files, or another directory's app records.

The current queries search public, non-fork repositories matching the vibe-coding, vibecoding, or vibe-coded topics, plus README phrase searches for “vibe coded” and “vibe coding”. Results are deduplicated by case-insensitive owner/repository name. Search is indexed and can change between refreshes. GitHub limits pagination and result depth, so this is a snapshot of discovery leads rather than an exhaustive census. See the [GitHub Search overview](https://docs.github.com/en/search-github/getting-started-with-searching-on-github/about-searching-on-github), [REST API rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api), and [REST API pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api).

The open-web and X examples are entered with first-party evidence in [the curated file](../data/curated.jsonl). Unreviewed public posts and pages can be tracked in [external leads](../data/raw/external-leads.jsonl). This initial set demonstrates the human-reviewed path; it is not a claim of comprehensive web or X coverage. Add more records as creator sources are found.

## Evidence levels

| Level | What it means |
|---|---|
| vibe_topic_tag_only_unverified | GitHub repository matched a vibe-coding topic query. Authorship is unknown. |
| readme_phrase_search_hit_unverified | GitHub repository matched a README phrase search. The hit is a lead and has not been manually checked. |
| creator_stated | A human reviewer recorded a first-party public build statement and linked the evidence. |

Only the last level is used for the human-reviewed examples. Even then, it records what the creator says; it is not forensic verification of code authorship.

## Category and project-kind rules

metadata_rules_v1 applies ordered keyword rules to a repository's name, description, and topic tags. Project kinds distinguish app candidates, website candidates, developer tools, templates/demos, resource directories, and unknowns. These labels can be wrong and should be treated as navigation aids. Other / Needs Review is a valid result, not a quality rating.

## Possible “AI slop” review screen

The screen reports observable signals: missing description, no homepage linked, zero or one star, very small repository metadata, resource/template/demo/example wording, or archived status. Two signals put a record in the review queue; three or more are marked to review first. Star count, repository size, or missing links alone do not establish project quality or origin. The screen does not inspect code, run the app, assess user value, or infer AI authorship.

## Evaluation status

Machine-screened candidates have evaluation.level = repository_metadata_screen; their build origin, availability, functionality, user experience, security/privacy, and maintenance have not been independently assessed. Human-reviewed examples currently document first-party build evidence and project-link reachability on a date. Their functionality, user experience, security/privacy, and maintenance remain unevaluated unless a record explicitly says otherwise.

Future evaluations should record the evaluated URL and version, date, reproducible steps, findings, and evidence. Keep availability, functional behavior, usability, maintenance, and security/privacy as separate fields so one successful check does not imply the others passed.
