"""
Combines keyword score, evidence tiers, and GitHub verification into
one final Proof Score, deterministically (no LLM involved here — see
ADR 0003 on why AI is scoped out of the final scoring math).

TODO (yours to implement): define the actual weighting formula.
"""

from src.models import SkillEvidence


def compute_proof_score(evidence_list: list[SkillEvidence]) -> float:
    raise NotImplementedError
