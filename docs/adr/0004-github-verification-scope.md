# ADR 0004: GitHub verification checks both language and text evidence, reported separately

## Status

Accepted

## Context

GitHub verification could be scoped narrowly (only check if a skill
appears as a GitHub-detected repo language) or broadly (also read repo
descriptions and READMEs for mentions of the skill). Language-only
verification is more reliable but misses anything GitHub's language
detector doesn't recognize — frameworks, cloud platforms, tools (React,
AWS, Docker) never show up as a "language," even when a repo is
genuinely built with them.

## Decision

Check both signals independently and keep them separate rather than
collapsing into one bool:

- `language_verified` — skill detected via GitHub's repo language API.
- `text_verified` — skill mentioned in a repo's description or README,
  using the same word-boundary matching as `baseline_scorer`.

Both are surfaced separately in `GithubVerification` and shown
separately in the UI, rather than merged into a single "verified"
flag.

## Consequences

- Catches evidence a language-only check would miss entirely (e.g.
  "React" or "AWS" claims), at the cost of being a weaker signal than a
  language match — text mentions are self-reported by the candidate in
  their own README, not detected independently by GitHub.
- Scoring (`compute_def_score`) treats either signal as sufficient for
  full Tier 3 credit (`language_verified or text_verified`), since
  requiring both would be stricter than the tier definition demands —
  the resume only claims something checkable exists, not that it's
  checkable two different ways.
- Capped at 20 most-recently-updated, non-fork repos per candidate to
  bound API calls and avoid rate-limit or latency blowups on candidates
  with very large GitHub histories.
