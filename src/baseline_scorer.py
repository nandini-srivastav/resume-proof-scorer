"""
The naive keyword-match baseline scorer — simulates a "dumb" ATS.
This is your comparison point for the whole project, so it should
stay deliberately simple (no semantic understanding).
"""

import re
from src.models import KeywordMatchResult

def score_resume_by_keywords(jd_skills: list[str], resume_text: str) -> KeywordMatchResult:
    """
    Score a resume against a job description using naive keyword matching.

    Simulates a "dumb" ATS: counts how many of the JD's required
    skills appear in the resume (case-insensitive, exact word
    boundary match) and how many times each one is mentioned in
    total. Rewards repetition without judgment on whether the skill
    is actually demonstrated — this is the baseline your evidence-
    based Proof Score is meant to improve on.

    Args:
        jd_skills: List of skills required by the job description.
        resume_text: Full extracted resume text to search.

    Returns:
        A KeywordMatchResult with the match count/percentage and
        total mention count. Returns all zeros if jd_skills is empty.
    """
    
    # Edge Case : if there are no skills mentioned in job description
    if not jd_skills :
        return KeywordMatchResult(
            skills_matched = 0, 
            total_skills = 0, 
            match_percentage = 0.0, 
            total_mentions = 0
        )
    
    # Step 1 : initialise to 0
    skills_matched = 0
    total_mentions = 0 
    
    # Step 2 : loop against each skill mentioned in jd_skills
    for skill in jd_skills:
        # Step 3 : count occurences of skill in resume_text
        count = count_occurrences(skill, resume_text)
        # Step 4 : add the occurences count to total_mentions
        total_mentions += count 
        # Step 5 : if the count for a particular jd_skills > 0 increment the skills_matched by 1
        if count > 0:
            skills_matched += 1
            
    # Step 6 : Calculate match_percentage 
    match_percentage = (skills_matched / len(jd_skills)) * 100
    
    return KeywordMatchResult(
        skills_matched=skills_matched,
        total_skills=len(jd_skills),
        match_percentage=match_percentage,
        total_mentions=total_mentions,
    )
    
def count_occurrences(skill : str, text : str) -> int:
    """
    Count how many times a skill appears in a block of text.

    Matches case-insensitively on exact word boundaries, so a skill
    like "Java" won't be counted as a match inside "JavaScript".
    Special regex characters in the skill name (e.g. "C++", ".NET")
    are escaped and treated as literal text.

    Args:
        skill: The skill name to search for.
        text: The text to search within.

    Returns:
        The number of times the skill appears in the text.
    """
    
    # Step 1 : escape any regex special char that might be inside the skill name
    pattern = r'(?<!\w)' + re.escape(skill) + r'(?!\w)'
    # Step 2 : finds every non-overlapping match of the pattern and returns them as a list
    matches = re.findall(pattern, text, re.IGNORECASE)
    # Step 3 : return the count - how many times a skill appeared?
    return len(matches)
