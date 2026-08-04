"""
Tests for src/aggregator.py.

These test the scoring formula directly against constructed 
SkillEvidence / GithubVerification objects.
"""

import pytest
from typing import Optional
from src.aggregator import compute_def_score, compute_proof_score, build_candidate_score
from src.models import SkillEvidence, GithubVerification, KeywordMatchResult, CandidateScore


def make_github_verification(language_verified=False, text_verified=False, skill="Python"):
    return GithubVerification(
        skill=skill,
        language_verified=language_verified,
        language_evidence=["some-repo"] if language_verified else [],
        text_verified=text_verified,
        text_evidence=["some-repo"] if text_verified else [],
    )


def make_skill_evidence(skill="Python", tier=1, github_verified: Optional[GithubVerification] = None):
    return SkillEvidence(
        skill=skill,
        tier=tier,
        excerpt="some excerpt",
        github_verified=github_verified,
    )


# ---------------------------------------------------------------------
# compute_def_score()
# ---------------------------------------------------------------------

def test_returns_zero_when_no_evidence():
    assert compute_def_score(None) == 0


def test_tier_1_returns_1():
    evidence = make_skill_evidence(tier=1)
    assert compute_def_score(evidence) == 1


def test_tier_2_returns_2():
    evidence = make_skill_evidence(tier=2)
    assert compute_def_score(evidence) == 2


def test_tier_3_verified_by_language_returns_3():
    gh = make_github_verification(language_verified=True, text_verified=False)
    evidence = make_skill_evidence(tier=3, github_verified=gh)
    assert compute_def_score(evidence) == 3


def test_tier_3_verified_by_text_returns_3():
    gh = make_github_verification(language_verified=False, text_verified=True)
    evidence = make_skill_evidence(tier=3, github_verified=gh)
    assert compute_def_score(evidence) == 3


def test_tier_3_verified_by_both_returns_3():
    gh = make_github_verification(language_verified=True, text_verified=True)
    evidence = make_skill_evidence(tier=3, github_verified=gh)
    assert compute_def_score(evidence) == 3


def test_tier_3_unverified_returns_1():
    gh = make_github_verification(language_verified=False, text_verified=False)
    evidence = make_skill_evidence(tier=3, github_verified=gh)
    assert compute_def_score(evidence) == 1


def test_tier_3_with_no_github_data_returns_1():
    evidence = make_skill_evidence(tier=3, github_verified=None)
    assert compute_def_score(evidence) == 1


# ---------------------------------------------------------------------
# compute_proof_score()
# ---------------------------------------------------------------------

def test_all_skills_tier_3_verified_returns_100():
    gh = make_github_verification(language_verified=True)
    jd_skills = ["Python", "React"]
    evidence = [
        make_skill_evidence(skill="Python", tier=3, github_verified=gh),
        make_skill_evidence(skill="React", tier=3, github_verified=gh),
    ]

    result = compute_proof_score(jd_skills, evidence)

    assert result == 100.0


def test_no_evidence_returns_zero():
    jd_skills = ["Python", "React"]
    evidence = []

    result = compute_proof_score(jd_skills, evidence)

    assert result == 0.0


def test_mixed_tiers_computes_correctly():
    jd_skills = ["Python", "React", "SQL"]
    evidence = [
        make_skill_evidence(skill="Python", tier=1),   # 1
        make_skill_evidence(skill="React", tier=2),    # 2
        # "SQL" never mentioned -> 0
    ]

    result = compute_proof_score(jd_skills, evidence)

    # (1 + 2 + 0) / (3 * 3) * 100
    assert result == pytest.approx(33.33, abs=0.01)


def test_evidence_for_skill_outside_jd_list_is_ignored():
    jd_skills = ["Python"]
    evidence = [
        make_skill_evidence(skill="Python", tier=1),
        make_skill_evidence(skill="Photoshop", tier=3),   # not in jd_skills, shouldn't count
    ]

    result = compute_proof_score(jd_skills, evidence)

    # only Python counts: 1 / 3 * 100
    assert result == pytest.approx(33.33, abs=0.01)


def test_empty_jd_skills_raises_zero_division():
    # Known edge case: an empty JD skill list has no meaningful proof score.
    # This should be prevented upstream (JD must have at least one skill)
    # rather than silently returning 0 or 100 here.
    with pytest.raises(ZeroDivisionError):
        compute_proof_score([], [])


# ---------------------------------------------------------------------
# build_candidate_score()
# ---------------------------------------------------------------------

def test_returns_candidate_score_instance():
    keyword_result = KeywordMatchResult(
        skills_matched=1, total_skills=2, match_percentage=50.0, total_mentions=1
    )
    jd_skills = ["Python", "React"]
    evidence = [make_skill_evidence(skill="Python", tier=2)]

    result = build_candidate_score("Jane Doe", keyword_result, jd_skills, evidence)

    assert isinstance(result, CandidateScore)


def test_combines_keyword_and_proof_scores_correctly():
    keyword_result = KeywordMatchResult(
        skills_matched=1, total_skills=1, match_percentage=100.0, total_mentions=3
    )
    jd_skills = ["Python"]
    evidence = [make_skill_evidence(skill="Python", tier=1)]

    result = build_candidate_score("Jane Doe", keyword_result, jd_skills, evidence)

    assert result.candidate_name == "Jane Doe"
    assert result.keyword_score == 100.0
    assert result.proof_score == pytest.approx(33.33, abs=0.01)   # tier 1 only -> 1/3 * 100


def test_evidence_list_preserved_on_result():
    keyword_result = KeywordMatchResult(
        skills_matched=1, total_skills=1, match_percentage=100.0, total_mentions=1
    )
    jd_skills = ["Python"]
    evidence = [make_skill_evidence(skill="Python", tier=2)]

    result = build_candidate_score("Jane Doe", keyword_result, jd_skills, evidence)

    assert result.evidence == evidence