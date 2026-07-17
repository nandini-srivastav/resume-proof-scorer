"""
The naive keyword-match baseline scorer — simulates a "dumb" ATS.
This is your comparison point for the whole project, so it should
stay deliberately simple (no semantic understanding).

TODO (yours to implement): decide how you count/weight keyword matches
between the JD's required skills and the resume's text.
"""


def score_resume_by_keywords(jd_skills: list[str], resume_text: str) -> float:
    raise NotImplementedError
