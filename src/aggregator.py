"""
It's the module that turns raw evidence into the final comparison your whole 
project is built around: keyword score vs. proof score.

Every other module up to this point produces pieces: baseline_scorer.py gives 
a naive keyword-match percentage, llm_scorer.py gives per-skill evidence with 
a tier (1/2/3), github_verifier.py gives a cross-check on whether Tier 3 
claims actually hold up externally. None of them combine into one number — 
aggregator.py is where that combination happens, deterministically, with plain 
Python (no AI here, per your architecture split — the judgment calls already 
happened in llm_scorer, this is just arithmetic).

Weighing formula: proof_score = (sum of per-skill score) / (num_of_jdskills * 3) * 100
"""

from src.models import SkillEvidence
from src.models import CandidateScore
from typing import Optional

def compute_def_score(skill_evidence: Optional[SkillEvidence]) -> int:
    """
    Score one skill's evidence: 0-3.

    Args:
        skill_evidence (Optional[SkillEvidence]): Evidence for this skill,
            or None if the resume never mentioned it at all.

    Returns:
        int: 0 if no evidence found. Otherwise the tier weight (1/2/3),
            except Tier 3 drops to 1 if github_verified shows neither
            language_verified nor text_verified — a claimed-checkable
            skill that didn't check out scores worse than an unverifiable
            Tier 2 claim, not better.
    """
    if skill_evidence is None:
        return 0
    
    # Step - 1 : If skill shows up inside a real description and also names 
    # something checkable: a specific repo, project name, or link.
    if skill_evidence.tier == 3:
        # Step - 2 : Pull out GithubVerification object for that skill (None : no username provided)
        gh = skill_evidence.github_verified
        # Step - 3 : 2 conditions - (a) if - Gihtub check exists, username was given, 
        #                           (b) else - skills showed in an actual repo or README 
        if gh is not None and (gh.language_verified or gh.text_verified):
            # assign tier 3
            return 3  
        else : 
            # assign tier 1 - claims didn't hold up
            return 1
    return skill_evidence.tier

def compute_proof_score(jd_skills: list[str], evidence_list: list[SkillEvidence]) -> float:
    """
    Aggregate per-skill scores into one 0-100 proof score for a candidate.

    Args:
        jd_skills (list[str]): All skills required by the job description.
        evidence (list[SkillEvidence]): Evidence found for skills that
            appeared in the resume (may be a subset of jd_skills).

    Returns:
        float: 0-100, same scale as keyword_score, for direct comparison.
    """
    # Step - 1 : index evidence by skill name for instant lookup, instead of searching the list each time
    evidence_by_skill = {e.skill: e for e in evidence_list}
    
    # Step - 2 :Initialise score at 0
    total = 0
    # Step - 3 : Loops over every skill job description requires
    for skill in jd_skills:
        # Step - 4 : Looks up the skill in the dict that is built. (None - found nothing)
        skill_evidence = evidence_by_skill.get(skill)
        # Step - 5 : Calls the function on whatever is found, adds a score 0-3
        total += compute_def_score(skill_evidence)
        
    # Step - 6 : If every single JD skill scored a perfect 3 
    max_possible = len(jd_skills) * 3
    return (total / max_possible) * 100
    

def build_candidate_score(candidate_name : str, keyword_results : KeywordMatchResult,
                          jd_skills : list[str], evidence : list[SkillEvidence]) -> CandidateScore:
    """
    Assemble the final CandidateScore combining keyword and proof scores.

    Args:
        candidate_name (str): Candidate's name.
        keyword_result (KeywordMatchResult): Output of score_resume_by_keywords.
        jd_skills (list[str]): All skills required by the job description.
        evidence (list[SkillEvidence]): Evidence found for this candidate.

    Returns:
        CandidateScore: Final combined result.
    """
    return CandidateScore(
        candidate_name=candidate_name,
        keyword_score=keyword_results.match_percentage,
        proof_score=compute_proof_score(jd_skills, evidence),
        evidence=evidence,
    )