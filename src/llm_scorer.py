"""
The core engine: uses Claude to classify each claimed skill into an
evidence tier and pull a supporting excerpt.

This is the heart of the project — the prompt design, tier definitions,
and stuffing-detection logic are yours to design, not boilerplate.
Only the API call plumbing is scaffolded here.
"""

import anthropic
from src.config import ANTHROPIC_API_KEY
from src.models import SkillEvidence

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def classify_skill_evidence(skill: str, resume_text: str) -> SkillEvidence:
    """
    TODO: design the prompt that asks Claude to:
      1. find where/how `skill` is mentioned in `resume_text`
      2. classify it into a tier (define your tiers in models.py / DESIGN.md)
      3. return a short supporting excerpt
    Parse the model's response into a SkillEvidence object below.
    """
    raise NotImplementedError
