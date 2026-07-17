"""
Data schemas shared across modules.

TODO (yours to design): decide the exact fields you need for
EvidenceTier, SkillEvidence, and CandidateScore based on what your
scoring logic in llm_scorer.py and aggregator.py actually produces.
The shapes below are placeholders to unblock the other stub files —
change them freely.
"""

from pydantic import BaseModel
from typing import Optional


class SkillEvidence(BaseModel):
    skill: str
    tier: int  # TODO: define what 1 / 2 / 3 mean and document it here
    excerpt: str
    github_verified: Optional[bool] = None


class CandidateScore(BaseModel):
    candidate_name: str
    keyword_score: float
    proof_score: float
    evidence: list[SkillEvidence]
