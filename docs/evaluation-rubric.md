# Project evaluation rubric

The directory has two distinct jobs: find a large candidate set and evaluate a smaller, reviewable set with evidence. A search match is never a quality verdict. “Possible AI slop” is a neutral triage label for observable signals, not a statement about a creator's skill or intent.

## Evidence record

For each evaluated project, record:

- The project URL and exact version, release, commit, or date observed.
- The discovery source and any first-party creator statement about AI coding tools.
- Date, environment, device/browser, and the steps actually attempted.
- Separate results for product identity, reachability, functionality, user experience, security/privacy, and maintenance.
- A short finding with links or reproducible evidence. Use `not_checked` when no check was performed.

Do not infer a successful app experience from an HTTP 200 response, a launch post, screenshots, or a source repository alone.

## Status values

Use these values consistently; add a concrete note for every result other than `not_checked`.

| Field | Suggested values | What to check |
|---|---|---|
| `build_origin` | `creator_stated`, `independently_correlated`, `unverified`, `disputed` | First-party statements and linked evidence. Do not call a creator statement forensic proof. |
| `product_identity` | `confirmed`, `probable`, `unresolved`, `not_a_product` | Whether the source and linked URL refer to the same app, demo, template, or directory. |
| `availability` | `reachable`, `limited`, `unavailable`, `not_checked` | The product route, region/account gates, and date. A homepage response alone is limited evidence. |
| `functionality` | `pass`, `partial`, `fail`, `not_checked` | Run named, non-destructive core tasks and record expected versus observed results. |
| `user_experience` | `pass`, `partial`, `fail`, `not_checked` | Task clarity, mobile use where relevant, accessibility basics, loading, empty/error states, and recovery. |
| `security_privacy` | `pass`, `findings`, `not_checked` | Public code/configuration and stated data handling. Do not submit real personal data or credentials. A pass is scoped to the checks listed. |
| `maintenance` | `active`, `stale`, `paused`, `unknown` | Recent releases/commits, working links, issue activity, and creator status statements. |

## Safe, repeatable review

1. Open the original discovery source and follow only public links. Confirm whether the creator speaks for the project.
2. Check the product URL and record the response/date. Avoid sign-up, payments, outbound messages, or data uploads unless a separately authorized test plan exists.
3. If the product is publicly usable without personal data, try the main flow with synthetic inputs. Record the exact steps and any failure.
4. For public repositories, inspect the relevant code and configuration without running untrusted setup scripts. Record the commit inspected.
5. Record privacy/security findings as scoped observations, not certification. Do not infer safety from generated code, a clean dependency scan, or a privacy statement alone.
6. If evidence is missing, preserve the candidate with `not_checked` or `unverified`; do not silently upgrade or remove it.

## Bulk triage versus app evaluation

`metadata_rules_v1` classifies repository candidates and reports possible low-effort signals using repository metadata only. It does not execute apps or read project code. External API/search leads are also unreviewed until a person confirms their identity and source. These bulk states are useful for sorting thousands of leads; they must not be presented as a completed product evaluation.
