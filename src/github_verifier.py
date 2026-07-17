"""
Cross-checks claimed skills against a candidate's public GitHub activity.

TODO (yours to implement):
- fetch_repo_languages(): call the GitHub API for a user's repos and languages
- is_skill_verified(): decide what counts as "verified" for a given skill
  (e.g., present in repo language stats, topics, or README)

Handle the edge cases from DESIGN.md: no GitHub link, rate limits,
private/empty repos — none of that should crash the pipeline.
"""

import requests
from src.config import GITHUB_TOKEN


def fetch_repo_languages(github_username: str) -> dict:
    raise NotImplementedError


def is_skill_verified(skill: str, repo_languages: dict) -> bool:
    raise NotImplementedError
