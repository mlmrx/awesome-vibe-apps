# Awesome Vibe Apps

An open directory and research corpus for apps built with AI coding tools, including polished launches, rough prototypes, templates, clones, experiments, and likely low-effort projects.

## Current snapshot

<!-- SNAPSHOT:START -->
As of 2026-10-23, this repository contains:

- **18,892 unique public GitHub repository candidates** from the recorded query set.
- **6,814 app or website candidates** based on repository metadata cues.
- **30 human-reviewed examples** with first-party build evidence.
- **29 curated project URLs returned HTTP 200; 1 returned HTTP 404** on the checked date. Product workflows were not tested.
- **1,610 unreviewed public web/X leads**.
- **6,318 public DEV/Hacker News metadata records** behind those leads.
- **11,511 GitHub candidates with two or more possible low-effort signals**, for review only.

The corpus is intentionally broad and noisy. Source hits and machine labels are discovery aids, not proof of AI authorship, app status, quality, safety, or current availability.
<!-- SNAPSHOT:END -->

## Browse

- [Full categorized candidate index](catalog/index.md)
- [Unreviewed web/X project lead index](catalog/external-leads.md)
- [Machine-readable catalog](data/catalog.jsonl)
- [Raw GitHub metadata snapshot](data/raw/github-repositories.jsonl)
- [Manual web/X discovery leads](data/raw/external-leads.jsonl)
- [Generated API-derived project leads](data/raw/generated-external-leads.jsonl)
- [API-collected DEV article metadata](data/raw/devto-articles.jsonl)
- [API-collected Hacker News stories](data/raw/hackernews-stories.jsonl)
- [Public web collection query snapshot](data/raw/public-web-search-snapshot.json)
- [Search queries and collection details](data/raw/github-search-snapshot.json)
- [Reviewed examples and first-party build evidence](data/curated.jsonl)
- [Classification and evaluation methodology](docs/methodology.md)
- [Project evaluation rubric](docs/evaluation-rubric.md)
- [How to contribute](CONTRIBUTING.md)

## Human-reviewed examples

The complete first-party evidence list, including 30 records in the current snapshot, is in [data/curated.jsonl](data/curated.jsonl). Project URL checks only establish the HTTP response on the recorded date; they do not establish that an app works.

- **[Dev Confessions](https://worksnever.dev/)** — Anonymous space for developers to share confessions, wins, failures, and discoveries. The creator describes building it with Lovable in a [first-person build story](https://dev.to/willdew-dev/building-my-first-vibe-coded-app-without-touching-a-line-of-code-4pld).
- **[MenuGen](https://menugen.app/)** — Turns a photo of a restaurant menu into images that help explain the dishes. The creator describes the Cursor and Claude build in a [first-person write-up](https://karpathy.bearblog.dev/vibe-coding-menugen/) and a companion [post on X](https://x.com/karpathy/status/1917961248031080455).
- **[Expense Manager for Small Businesses](https://github.com/maanuanubhav999/vibe-coded-expense-manager)** — Android expense tracker. Its [repository README](https://github.com/maanuanubhav999/vibe-coded-expense-manager#readme) says it was built with ChatGPT and Claude.
- **[FastTodo](https://vibe-coded-todo-app.vercel.app/)** — Offline-first task manager. The creator identifies it as vibe coded in the [project repository](https://github.com/imran-baitham/vibe-coded-todo-app).
- **[Bedtime Adventures](https://testflight.apple.com/join/eBz3jQx2)** — Kids' bedtime story app in public TestFlight beta. The creator describes building it mostly with Claude Code in a [project post](https://www.reddit.com/r/vibecoding/comments/1ugj1b3/vibecoded_a_kids_bedtimestory_app_from_zero_to/). Installation and runtime are not tested here.
- **[Stupido](https://www.producthunt.com/products/stupido)** — iOS voice-driven to-do app. The creator describes building it with Cursor in a [launch discussion](https://www.reddit.com/r/vibecoding/comments/1mrxq4z/i_vibe_coded_a_whole_ass_ios_app_and_its_live/). App installation and runtime are not tested here.
- **[Storypot](https://thestorypot.com/)** — Children's story creation app. The creator describes vibe coding it in a [project discussion](https://www.reddit.com/r/vibecoding/comments/1mf94ao/vibe_coded_a_kids_storytelling_app_with_my_5yo_we/); a later reply says the project is paused, and current site availability is unverified.
- **[Vibe-Coding Café demo site](https://vibe-cafe-launch.lovable.app/)** — One-page fictional event site created with Lovable for a [first-person tutorial](https://www.inc.com/ben-sherry/vibe-code-a-website-for-free-how-to-make-one-for-your-company/91264441). It is included as a demo example, not presented as a real café.

## AI slop, prototypes, and unfinished apps are in scope

This directory is meant to capture the whole landscape, including disposable demos and low-effort clones. We keep their observable signals visible so researchers can inspect and debate them. “Possible AI slop” is a screening label, not a claim about the builder or a quality verdict.

## What “evaluated” means here

Every candidate receives a deterministic metadata screen for likely category, project kind, source lead, and possible low-effort signals. A reviewed app can receive further checks for creator evidence, reachability, basic functionality, user experience, maintenance, and security/privacy. Those checks are recorded separately; a metadata label never stands in for a runtime evaluation.

## Build the snapshot

Requires Python 3.10+ and the GitHub CLI (gh) authenticated to GitHub. The collector uses the CLI session and does not write credentials into the repository.

~~~powershell
python scripts/collect_github.py
python scripts/collect_public_web.py
python scripts/build_catalog.py
~~~

The collectors use the public GitHub, DEV, and Hacker News APIs. They store metadata, source links, and query provenance; they do not copy article bodies. Search APIs cap result depth, so the checked-in snapshot is a reproducible, source-limited sample rather than an exhaustive census. X and other sites can be added as sourced leads; the project does not bypass logins, robots rules, or API restrictions.
