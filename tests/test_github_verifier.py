"""
Tests for src/github_verifier.py.

Mocked unit tests for every function.
"""

import base64
import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException

from src.github_verifier import (
    fetch_repo_list,
    fetch_repo_languages,
    fetch_readme_text,
    enrich_repos,
    verify_by_language,
    verify_by_text,
    build_github_report,
)
from src.models import GithubVerification


def make_mock_response(status_code=200, json_data=None, text=""):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.text = text
    return mock


def make_repo(name, fork=False, updated_at="2024-01-01T00:00:00Z",
              description=None, owner="someuser"):
    return {
        "name": name,
        "fork": fork,
        "updated_at": updated_at,
        "description": description,
        "html_url": f"https://github.com/{owner}/{name}",
        "owner": {"login": owner},
    }


# ---------------------------------------------------------------------
# fetch_repo_list()
# ---------------------------------------------------------------------

@patch("src.github_verifier.requests.get")
def test_fetch_repo_list_filters_forks(mock_get):
    repos = [make_repo("real-project", fork=False), make_repo("a-fork", fork=True)]
    mock_get.return_value = make_mock_response(200, repos)

    result = fetch_repo_list("someuser")

    names = [r["name"] for r in result]
    assert "real-project" in names
    assert "a-fork" not in names


@patch("src.github_verifier.requests.get")
def test_fetch_repo_list_sorts_by_updated_at_descending(mock_get):
    repos = [
        make_repo("old", updated_at="2022-01-01T00:00:00Z"),
        make_repo("newest", updated_at="2024-06-01T00:00:00Z"),
        make_repo("middle", updated_at="2023-01-01T00:00:00Z"),
    ]
    mock_get.return_value = make_mock_response(200, repos)

    result = fetch_repo_list("someuser")

    assert [r["name"] for r in result] == ["newest", "middle", "old"]


@patch("src.github_verifier.requests.get")
def test_fetch_repo_list_caps_at_20(mock_get):
    repos = [make_repo(f"repo{i}", updated_at=f"2024-01-{i+1:02d}T00:00:00Z") for i in range(25)]
    mock_get.return_value = make_mock_response(200, repos)

    result = fetch_repo_list("someuser")

    assert len(result) == 20


@patch("src.github_verifier.requests.get")
def test_fetch_repo_list_raises_on_error_status(mock_get):
    mock_get.return_value = make_mock_response(404, text="Not Found")

    with pytest.raises(ValueError):
        fetch_repo_list("nonexistent-user-xyz")


# ---------------------------------------------------------------------
# fetch_repo_languages()
# ---------------------------------------------------------------------

@patch("src.github_verifier.requests.get")
def test_fetch_repo_languages_success(mock_get):
    mock_get.return_value = make_mock_response(200, {"Python": 12043, "HTML": 891})

    result = fetch_repo_languages("someuser", "somerepo")

    assert result == {"Python": 12043, "HTML": 891}


@patch("src.github_verifier.requests.get")
def test_fetch_repo_languages_returns_empty_on_error_status(mock_get):
    mock_get.return_value = make_mock_response(404)

    result = fetch_repo_languages("someuser", "somerepo")

    assert result == {}


@patch("src.github_verifier.requests.get")
def test_fetch_repo_languages_returns_empty_on_network_error(mock_get):
    mock_get.side_effect = RequestException("connection failed")

    result = fetch_repo_languages("someuser", "somerepo")

    assert result == {}


# ---------------------------------------------------------------------
# fetch_readme_text()
# ---------------------------------------------------------------------

@patch("src.github_verifier.requests.get")
def test_fetch_readme_text_success(mock_get):
    encoded = base64.b64encode(b"# My Project\nBuilt with Python.").decode("utf-8")
    mock_get.return_value = make_mock_response(200, {"content": encoded})

    result = fetch_readme_text("someuser", "somerepo")

    assert result == "# My Project\nBuilt with Python."


@patch("src.github_verifier.requests.get")
def test_fetch_readme_text_returns_empty_on_404(mock_get):
    mock_get.return_value = make_mock_response(404)

    result = fetch_readme_text("someuser", "somerepo")

    assert result == ""


@patch("src.github_verifier.requests.get")
def test_fetch_readme_text_returns_empty_on_other_error_status(mock_get):
    mock_get.return_value = make_mock_response(500)

    result = fetch_readme_text("someuser", "somerepo")

    assert result == ""


@patch("src.github_verifier.requests.get")
def test_fetch_readme_text_returns_empty_on_network_error(mock_get):
    mock_get.side_effect = RequestException("connection failed")

    result = fetch_readme_text("someuser", "somerepo")

    assert result == ""


@patch("src.github_verifier.requests.get")
def test_fetch_readme_text_returns_empty_on_bad_base64(mock_get):
    mock_get.return_value = make_mock_response(200, {"content": "abc"})  # invalid padding

    result = fetch_readme_text("someuser", "somerepo")

    assert result == ""


# ---------------------------------------------------------------------
# enrich_repos()
# ---------------------------------------------------------------------

@patch("src.github_verifier.fetch_readme_text")
@patch("src.github_verifier.fetch_repo_languages")
@patch("src.github_verifier.fetch_repo_list")
def test_enrich_repos_combines_data(mock_list, mock_langs, mock_readme):
    mock_list.return_value = [make_repo("project-one", description="A cool tool")]
    mock_langs.return_value = {"Python": 5000}
    mock_readme.return_value = "Built using Python and pytest."

    result = enrich_repos("someuser")

    assert len(result) == 1
    assert result[0]["name"] == "project-one"
    assert result[0]["description"] == "A cool tool"
    assert result[0]["languages"] == {"Python": 5000}
    assert result[0]["readme"] == "Built using Python and pytest."


@patch("src.github_verifier.fetch_readme_text")
@patch("src.github_verifier.fetch_repo_languages")
@patch("src.github_verifier.fetch_repo_list")
def test_enrich_repos_defaults_none_description_to_empty_string(mock_list, mock_langs, mock_readme):
    mock_list.return_value = [make_repo("no-desc-repo", description=None)]
    mock_langs.return_value = {}
    mock_readme.return_value = ""

    result = enrich_repos("someuser")

    assert result[0]["description"] == ""


@patch("src.github_verifier.fetch_repo_list")
def test_enrich_repos_handles_empty_repo_list(mock_list):
    mock_list.return_value = []

    result = enrich_repos("someuser")

    assert result == []


# ---------------------------------------------------------------------
# verify_by_language()
# ---------------------------------------------------------------------

def test_verify_by_language_finds_match():
    repos = [{"name": "repo-a", "languages": {"Python": 100}}]

    verified, matches = verify_by_language("Python", repos)

    assert verified is True
    assert matches == ["repo-a"]


def test_verify_by_language_case_insensitive():
    repos = [{"name": "repo-a", "languages": {"python": 100}}]

    verified, matches = verify_by_language("Python", repos)

    assert verified is True
    assert matches == ["repo-a"]


def test_verify_by_language_no_match():
    repos = [{"name": "repo-a", "languages": {"HTML": 100}}]

    verified, matches = verify_by_language("Python", repos)

    assert verified is False
    assert matches == []


def test_verify_by_language_multiple_matching_repos():
    repos = [
        {"name": "repo-a", "languages": {"Python": 100}},
        {"name": "repo-b", "languages": {"Python": 50, "HTML": 20}},
        {"name": "repo-c", "languages": {"JavaScript": 80}},
    ]

    verified, matches = verify_by_language("Python", repos)

    assert verified is True
    assert set(matches) == {"repo-a", "repo-b"}


# ---------------------------------------------------------------------
# verify_by_text()
# ---------------------------------------------------------------------

def test_verify_by_text_finds_match_in_description():
    repos = [{"name": "repo-a", "description": "A React dashboard", "readme": ""}]

    verified, matches = verify_by_text("React", repos)

    assert verified is True
    assert matches == ["repo-a"]


def test_verify_by_text_finds_match_in_readme():
    repos = [{"name": "repo-a", "description": "", "readme": "Built with React and Redux."}]

    verified, matches = verify_by_text("React", repos)

    assert verified is True
    assert matches == ["repo-a"]


def test_verify_by_text_no_match():
    repos = [{"name": "repo-a", "description": "A CLI tool", "readme": "Written in Go."}]

    verified, matches = verify_by_text("React", repos)

    assert verified is False
    assert matches == []


def test_verify_by_text_respects_word_boundaries():
    # "Java" should not match inside "JavaScript"
    repos = [{"name": "repo-a", "description": "", "readme": "Uses JavaScript only."}]

    verified, matches = verify_by_text("Java", repos)

    assert verified is False
    assert matches == []


# ---------------------------------------------------------------------
# build_github_report()
# ---------------------------------------------------------------------

def test_build_github_report_combines_both_signals():
    repos = [{
        "name": "repo-a",
        "description": "A React app",
        "readme": "",
        "languages": {"Python": 100},
    }]

    report = build_github_report("Python", repos)

    assert isinstance(report, GithubVerification)
    assert report.skill == "Python"
    assert report.language_verified is True
    assert report.language_evidence == ["repo-a"]


def test_build_github_report_when_neither_verified():
    repos = [{
        "name": "repo-a",
        "description": "A CLI tool",
        "readme": "Written in Go.",
        "languages": {"Go": 100},
    }]

    report = build_github_report("React", repos)

    assert report.language_verified is False
    assert report.text_verified is False
    assert report.language_evidence == []
    assert report.text_evidence == []


def test_build_github_report_text_verified_but_not_language():
    repos = [{
        "name": "repo-a",
        "description": "A dashboard built with React",
        "readme": "",
        "languages": {"HTML": 100},
    }]

    report = build_github_report("React", repos)

    assert report.language_verified is False
    assert report.text_verified is True
    assert report.text_evidence == ["repo-a"]


# ---------------------------------------------------------------------
# Integration tests (real GitHub API calls)
# ---------------------------------------------------------------------

@pytest.mark.integration
def test_fetch_repo_list_real_api():
    result = fetch_repo_list("octocat")
    assert isinstance(result, list)


@pytest.mark.integration
def test_fetch_repo_languages_real_api():
    result = fetch_repo_languages("octocat", "Hello-World")
    assert isinstance(result, dict)