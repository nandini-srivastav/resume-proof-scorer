"""
Data schemas shared across modules.
"""

from pydantic import BaseModel
from typing import Optional


class SkillEvidence(BaseModel):
    skill: str
    tier: int  
    excerpt: str
    github_verified: Optional[GithubVerification] = None


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
    
class GithubVerification(BaseModel):
    """
    Result of checking one skill against a candidate's GitHub repos.

    Two signals are kept separate instead of merged into one bool: whether
    the skill showed up as an actual repo language (GitHub API), and
    whether it showed up in repo text (README or description).

    Args:
        skill (str): The skill being verified, e.g. "React".
        language_verified (bool): True if the skill was detected as a
            language in at least one repo.
        language_evidence (list[str]): Names of repos that matched by language.
        text_verified (bool): True if the skill appeared in a repo's
            README or description text.
        text_evidence (list[str]): Names of repos that matched by text.
    """
    skill: str 
    language_verified: bool
    language_evidence: list[str] # repo where where skill/tool showed up as a language.
    text_verified: bool
    text_evidence: list[str] # repo name where skill/tool showed up in description/README.