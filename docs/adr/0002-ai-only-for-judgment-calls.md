# ADR 0002: Use AI only where judgment on unstructured text is required

## Status

Accepted

## Context

The project could use Claude for many things: parsing resume sections,
counting keyword matches, deciding which GitHub repos count as evidence,
combining scores. Using AI everywhere would be faster to build but
would make the scoring non-deterministic, harder to test, harder to
explain, and harder to trust — a problem for a tool whose entire premise
is verifying claims rigorously.

## Decision

Claude is used only for tasks that require judgment on unstructured
text, where a fixed rule genuinely cannot do the job:

- Classifying each skill's evidence tier from resume text
  (`classify_all_skills`) — requires reading a paragraph and judging
  whether it describes real, specific experience.
- Extracting the required skills from a raw job description
  (`extract_skills_from_jd`) — job descriptions are free-form prose,
  not structured data.
- Extracting the candidate's name from resume text
  (`extract_candidate_name`) — no reliable fixed pattern exists across
  resume formats.

Everything else stays deterministic Python: section detection (fuzzy
string matching against a synonym list), keyword counting (regex with
word-boundary matching), GitHub verification (direct API checks against
language/text data, no AI judgment involved), and final score
aggregation (fixed arithmetic formula).

## Consequences

- The scoring formula (`compute_proof_score`) is fully deterministic and
  unit-testable without mocking an LLM — same inputs always produce the
  same score.
- Only 3 functions in the entire codebase make API calls, keeping the
  AI usage auditable and the cost/latency footprint predictable.
- Failure modes are easier to reason about: a parsing bug is a Python
  bug with a stack trace; an evidence-tier disagreement is a prompt
  quality issue, not a mystery buried in end-to-end AI behavior.
- Trade-off: rule-based section detection (fuzzy synonym matching) is
  less flexible than an LLM would be at handling wildly unconventional
  resume layouts — accepted as a reasonable limit, documented in the
  README.
