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
    if SkillEvidence is None:
        return 0
    
    # Step - 1 : If skill shows up inside a real description and also names 
    # something checkable: a specific repo, project name, or link.
    if SkillEvidence.tier == 3:
        # Step - 2 : Pull out GithubVerification object for that skill (None : no username provided)
        gh = SkillEvidence.github_verified
        # Step - 3 : 2 conditions - (a) if - Gihtub check exists, username was given, 
        #                           (b) else - skills showed in an actual repo or README 
        if gh is not None and (gh.language_verified or gh.text_evidence):
            # assign tier 3
            return 3  
        else : 
            # assign tier 1 - claims didn't hold up
            return 1
    return SkillEvidence.tier

def compute_proof_score(evidence_list: list[SkillEvidence]) -> float:
    raise NotImplementedError
