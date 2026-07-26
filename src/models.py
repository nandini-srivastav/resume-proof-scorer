"""
Data schemas shared across modules.
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

class KeywordMatchResult(BaseModel):
    """
    Result of naive keyword-based scoring against a job description.

    Represents how a "dumb" ATS would evaluate a resume — counting
    literal keyword matches without any judgment on whether the skill
    is actually demonstrated. Used as the comparison baseline against
    the evidence-based Proof Score.

    Attributes:
        skills_matched: Number of JD-required skills mentioned at
            least once in the resume.
        total_skills: Total number of skills required by the JD.
        match_percentage: skills_matched as a percentage of total_skills.
        total_mentions: Sum of all occurrences of every matched skill,
            across the whole resume — a high value relative to
            skills_matched can indicate keyword stuffing.
    """
    skills_matched : int
    total_skills : int 
    match_percentage : float
    total_mentions : int