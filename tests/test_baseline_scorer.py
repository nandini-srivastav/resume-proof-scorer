"""
Unit tests for src/baseline_scorer.py.
"""

import pytest
from src.baseline_scorer import score_resume_by_keywords, count_occurrences
from src.models import KeywordMatchResult


# ---------------------------------------------------------------------
# count_occurrences()
# ---------------------------------------------------------------------

def test_count_occurrences_single_match():
    assert count_occurrences("Python", "I know Python well.") == 1


def test_count_occurrences_multiple_matches():
    text = "Python Python Python are my main skills, I use Python daily."
    assert count_occurrences("Python", text) == 4


def test_count_occurrences_case_insensitive():
    text = "I use PYTHON and python and Python."
    assert count_occurrences("python", text) == 3


def test_count_occurrences_word_boundary_avoids_false_positive():
    # "Java" should NOT match inside "JavaScript"
    assert count_occurrences("Java", "I know JavaScript well.") == 0


def test_count_occurrences_word_boundary_matches_whole_word():
    assert count_occurrences("Java", "I know Java and JavaScript.") == 1


def test_count_occurrences_zero_when_absent():
    assert count_occurrences("Rust", "I only know Python and SQL.") == 0


def test_count_occurrences_handles_special_regex_characters():
    assert count_occurrences("C++", "I am proficient in C++ programming.") == 1
    assert count_occurrences(".NET", "I have worked with .NET before.") == 1


def test_count_occurrences_multi_word_skill():
    text = "I have experience in Machine Learning and machine learning research."
    assert count_occurrences("Machine Learning", text) == 2


# ---------------------------------------------------------------------
# score_resume_by_keywords()
# ---------------------------------------------------------------------

def test_score_returns_keyword_match_result_type():
    result = score_resume_by_keywords(["Python"], "I know Python.")
    assert isinstance(result, KeywordMatchResult)


def test_score_empty_jd_skills_returns_all_zeros():
    result = score_resume_by_keywords([], "Some resume text.")
    assert result.skills_matched == 0
    assert result.total_skills == 0
    assert result.match_percentage == 0.0
    assert result.total_mentions == 0


def test_score_all_skills_matched_once_each():
    jd_skills = ["Python", "SQL"]
    resume_text = "I know Python and SQL."
    result = score_resume_by_keywords(jd_skills, resume_text)
    assert result.skills_matched == 2
    assert result.total_skills == 2
    assert result.match_percentage == 100.0
    assert result.total_mentions == 2


def test_score_partial_match():
    jd_skills = ["Python", "SQL", "React"]
    resume_text = "I know Python and SQL, but not the third one."
    result = score_resume_by_keywords(jd_skills, resume_text)
    assert result.skills_matched == 2
    assert result.total_skills == 3
    assert result.match_percentage == pytest.approx(66.67, rel=1e-2)
    assert result.total_mentions == 2


def test_score_no_skills_matched():
    jd_skills = ["Rust", "Go"]
    resume_text = "I only know Python and SQL."
    result = score_resume_by_keywords(jd_skills, resume_text)
    assert result.skills_matched == 0
    assert result.total_skills == 2
    assert result.match_percentage == 0.0
    assert result.total_mentions == 0


def test_score_rewards_keyword_stuffing():
    jd_skills = ["Python"]
    stuffed_resume = "Python Python Python Python Python Python Python Python Python Python"
    modest_resume = "I built three real Python projects using Django and Flask."

    stuffed_result = score_resume_by_keywords(jd_skills, stuffed_resume)
    modest_result = score_resume_by_keywords(jd_skills, modest_resume)

    # Both match the single required skill...
    assert stuffed_result.skills_matched == 1
    assert modest_result.skills_matched == 1
    # ...but the stuffed resume has far more total mentions.
    assert stuffed_result.total_mentions > modest_result.total_mentions


def test_score_does_not_false_positive_on_substring():
    jd_skills = ["Java"]
    resume_text = "I am an expert in JavaScript."
    result = score_resume_by_keywords(jd_skills, resume_text)
    assert result.skills_matched == 0
    assert result.total_mentions == 0