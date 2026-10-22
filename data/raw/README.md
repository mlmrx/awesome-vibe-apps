# Raw discovery data

GitHub repository metadata and external leads live here. External leads are one JSON object per line in external-leads.jsonl:

~~~json
{"id":"x:unique-post-or-project-slug","name":"Project name","description":"Short factual description","project_url":"https://project.example","repository_url":null,"source_platform":"x","discovery_url":"https://x.com/account/status/123","discovered_at":"YYYY-MM-DD","discovery_note":"Why this is a lead","suggested_category":"Other / Needs Review","suggested_project_kind":"unknown"}
~~~

Supported source_platform values are web and x. Leave suggested values out when uncertain. The generated catalog keeps these records unreviewed until a contributor finds and records first-party build evidence.
