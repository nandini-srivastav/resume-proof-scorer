# ADR 0003: Tier 3 claims are penalized, not just unrewarded, when GitHub verification fails

## Status

Accepted

## Context

Evidence tiers (1/2/3) score a skill's evidence strength based on resume
text alone. Tier 3 specifically means the resume claims something
externally checkable — a named project, repo, or link. `github_verifier.py`
exists to actually check that claim. The open question: what should
happen to the score when a Tier 3 claim is checked and doesn't hold up?

## Decision

- Tier 1 or 2 → score equals the tier weight (1 or 2), unaffected by
  GitHub data, since neither tier claims to be externally verifiable.
- Tier 3 and verified (language or text match found in the candidate's
  repos) → score = 3, full credit, the claim held up.
- Tier 3 and NOT verified → score = 1, not 0 and not 2. Dropped to the
  same level as an unsupported bare-list claim, because promising
  something checkable and having it fail is treated as worse than a
  plain Tier 2 claim that never promised verifiability in the first
  place.

## Consequences

- This directly serves the project's stated thesis — surfacing inflated
  or false claims, not just rewarding evidence quality in isolation. A
  candidate who names a repo that doesn't actually demonstrate the
  skill scores worse than one who wrote a solid but unlinked project
  description.
- Tier 1/2 skills never get penalized for lacking a GitHub profile,
  since GitHub presence isn't something those tiers ever claimed.
- If GitHub verification is unavailable entirely (no username found, API
  failure), Tier 3 claims default to the unverified case (score 1) rather
  than being excluded from scoring — a claim that can't be checked is
  treated the same as one that was checked and failed, not given the
  benefit of the doubt.
