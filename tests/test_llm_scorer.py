"""
Unit tests for src/llm_scorer.py.

"""

import pytest
from unittest.mock import patch, MagicMock

from src.llm_scorer import classify_all_skills, build_prompt
from src.models import SkillEvidence


def make_mock_response(json_text: str):
    mock_content_block = MagicMock()
    mock_content_block.text = json_text
    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    return mock_response


# ---------------------------------------------------------------------
# build_prompt() — pure string checks, no API involved
# ---------------------------------------------------------------------

def test_build_prompt_includes_jd_skills():
    prompt = build_prompt(["Python", "SQL"], {"skills": ["Python"], "experience": [], "projects": []})
    assert "Python" in prompt
    assert "SQL" in prompt


def test_build_prompt_includes_section_content():
    sections = {"skills": ["Python"], "experience": ["Built an API"], "projects": ["Side project"]}
    prompt = build_prompt(["Python"], sections)
    assert "Built an API" in prompt
    assert "Side project" in prompt


def test_build_prompt_instructs_json_only_response():
    prompt = build_prompt(["Python"], {"skills": [], "experience": [], "projects": []})
    assert "JSON" in prompt


def test_build_prompt_handles_missing_section_key_gracefully():
    # No "skills" key at all in the dict
    prompt = build_prompt(["Python"], {"experience": ["Built something"]})
    assert isinstance(prompt, str)
    assert "Python" in prompt


def test_build_prompt_returns_string():
    prompt = build_prompt(["Python"], {"skills": [], "experience": [], "projects": []})
    assert isinstance(prompt, str)


# ---------------------------------------------------------------------
# classify_all_skills() — mocked API responses
# ---------------------------------------------------------------------

@patch("src.llm_scorer.client.messages.create")
def test_classify_all_skills_parses_valid_json(mock_create):
    mock_json = '[{"skill": "Python", "tier": 2, "excerpt": "Built a REST API using Python."}]'
    mock_create.return_value = make_mock_response(mock_json)

    result = classify_all_skills(
        ["Python"],
        {"skills": ["Python"], "experience": ["Built a REST API using Python."], "projects": []},
    )

    assert len(result) == 1
    assert isinstance(result[0], SkillEvidence)
    assert result[0].skill == "Python"
    assert result[0].tier == 2
    assert result[0].excerpt == "Built a REST API using Python."
    assert result[0].github_verified is None


@patch("src.llm_scorer.client.messages.create")
def test_classify_all_skills_parses_multiple_skills(mock_create):
    mock_json = (
        '[{"skill": "Python", "tier": 1, "excerpt": "Python"},'
        ' {"skill": "SQL", "tier": 2, "excerpt": "Wrote complex SQL queries for reporting."}]'
    )
    mock_create.return_value = make_mock_response(mock_json)

    result = classify_all_skills(["Python", "SQL"], {"skills": ["Python", "SQL"], "experience": [], "projects": []})

    assert len(result) == 2
    assert result[0].skill == "Python"
    assert result[1].skill == "SQL"


@patch("src.llm_scorer.client.messages.create")
def test_classify_all_skills_raises_on_invalid_json(mock_create):
    mock_create.return_value = make_mock_response("this is not valid JSON at all")

    with pytest.raises(ValueError):
        classify_all_skills(["Python"], {"skills": ["Python"], "experience": [], "projects": []})


@patch("src.llm_scorer.client.messages.create")
def test_classify_all_skills_raises_on_empty_response(mock_create):
    mock_create.return_value = make_mock_response("")

    with pytest.raises(ValueError):
        classify_all_skills(["Python"], {"skills": ["Python"], "experience": [], "projects": []})


# ---------------------------------------------------------------------
# classify_all_skills() — real API calls (integration tests)
# ---------------------------------------------------------------------

@pytest.mark.integration
def test_classify_all_skills_real_api_tier_1_bare_list():
    sections = {"skills": ["Python", "SQL"], "experience": [], "projects": []}
    result = classify_all_skills(["Python"], sections)
    assert len(result) == 1
    assert result[0].tier == 1


@pytest.mark.integration
def test_classify_all_skills_real_api_tier_2_with_context():
    sections = {
        "skills": ["Python"],
        "experience": ["Built a REST API using Python and Django, serving 10K requests per day."],
        "projects": [],
    }
    result = classify_all_skills(["Python"], sections)
    assert len(result) == 1
    assert result[0].tier >= 2


@pytest.mark.integration
def test_classify_all_skills_real_api_tier_3_with_link():
    sections = {
        "skills": ["Python"],
        "experience": [],
        "projects": ["Built a resume scoring tool in Python — github.com/johndoe/resume-scorer"],
    }
    result = classify_all_skills(["Python"], sections)
    assert len(result) == 1
    assert result[0].tier == 3