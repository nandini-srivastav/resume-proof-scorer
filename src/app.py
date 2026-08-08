"""
Streamlit entry point.

"""

import streamlit as st

from src.parser import extract_text, segment_sections, extract_github_link, extract_github_username
from src.baseline_scorer import score_resume_by_keywords
from src.llm_scorer import classify_all_skills, extract_candidate_name
from src.github_verifier import enrich_repos, build_github_report
from src.aggregator import build_candidate_score
from src.models import CandidateScore

st.title("Resume Proof Scorer")
st.write("Scaffold running. Build the real UI here.")


def process_resume(file_object, file_name: str, jd_skills: list[str]) -> CandidateScore:
    """Run the full pipeline on one resume: parse, score, verify, aggregate.

    Args:
        file_object: Open file object for the resume (PDF or DOCX).
        file_name (str): Original filename, used to detect format.
        jd_skills (list[str]): Skills required by the job description.

    Returns:
        CandidateScore: Final combined result for this candidate.

    Raises:
        Exception: Propagated from extract_text if the file can't be
            parsed at all (corrupted, wrong format, password-protected,
            scanned with no text). GitHub verification failures are
            handled internally and never raise here.
    """
    raw_text = extract_text(file_object, file_name)
    sections = segment_sections(raw_text)

    keyword_result = score_resume_by_keywords(jd_skills, raw_text)
    evidence = classify_all_skills(jd_skills, sections)
    candidate_name = extract_candidate_name(raw_text)

    github_links = extract_github_link(raw_text)
    if github_links:
        try:
            username = extract_github_username(github_links[0])
            repos = enrich_repos(username)

            for skill_evidence in evidence:
                if skill_evidence.tier == 3:
                    skill_evidence.github_verified = build_github_report(skill_evidence.skill, repos)
        except Exception:
            pass

    return build_candidate_score(candidate_name, keyword_result, jd_skills, evidence)