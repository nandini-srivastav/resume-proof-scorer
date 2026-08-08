"""
Streamlit entry point.

"""

import streamlit as st
import pandas as pd

from src.parser import extract_text, segment_sections, extract_github_link, extract_github_username
from src.baseline_scorer import score_resume_by_keywords
from src.llm_scorer import classify_all_skills, extract_skills_from_jd, extract_candidate_name
from src.github_verifier import enrich_repos, build_github_report
from src.aggregator import build_candidate_score
from src.models import CandidateScore

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

def initialize_session_state():
    """Set default values for session state keys, if not already set."""
    if "view" not in st.session_state:
        st.session_state["view"] = "setup"
    if "jd_skills" not in st.session_state:
        st.session_state["jd_skills"] = []
    if "results" not in st.session_state:
        st.session_state["results"] = []
    if "selected_candidate" not in st.session_state:
        st.session_state["selected_candidate"] = None

def render_setup_view():
    """Render the JD input + skill review + resume upload screen."""
    st.header("Resume Proof Scorer")

    jd_text = st.text_area("Job description", height=200)

    if st.button("Extract skills"):
        skills = extract_skills_from_jd(jd_text)
        st.session_state["jd_skills"] = skills

    if st.session_state["jd_skills"]:
        skills_df = pd.DataFrame({"skill": st.session_state["jd_skills"]})
        edited_df = st.data_editor(skills_df, num_rows="dynamic", key="skills_editor")
        st.session_state["jd_skills"] = [
            s.strip() for s in edited_df["skill"].tolist() if s and s.strip()
        ]

    uploaded_files = st.file_uploader(
        "Upload resumes", type=["pdf", "docx"], accept_multiple_files=True
    )

    analyze_disabled = not st.session_state["jd_skills"] or not uploaded_files

    if st.button("Analyze", disabled=analyze_disabled):
        results = []
        failures = []

        for file in uploaded_files:
            try:
                score = process_resume(file, file.name, st.session_state["jd_skills"])
                results.append(score)
            except Exception as e:
                failures.append((file.name, str(e)))

        st.session_state["results"] = results

        if failures:
            failed_names = ", ".join(name for name, _ in failures)
            st.warning(f"Could not process: {failed_names}")

        st.session_state["view"] = "results"
        st.rerun()
        
def render_results_view():
    """
    Render the ranked results table: keyword score vs. proof score.
    
    Reads session_state["results"]. On "View details" click, sets
    session_state["selected_candidate"] and switches to the detail view."""
    
    st.header("Results")

    results = st.session_state["results"]
    sorted_results = sorted(results, key=lambda c: c.proof_score, reverse=True)

    header_cols = st.columns([3, 2, 2, 2])
    header_cols[0].markdown("**Candidate**")
    header_cols[1].markdown("**Keyword score**")
    header_cols[2].markdown("**Proof score**")
    header_cols[3].markdown("")

    for i, candidate in enumerate(sorted_results):
        cols = st.columns([3, 2, 2, 2])
        cols[0].write(candidate.candidate_name)
        cols[1].write(f"{candidate.keyword_score:.1f}")
        cols[2].write(f"{candidate.proof_score:.1f}")
        if cols[3].button("View details", key=f"view_{i}"):
            st.session_state["selected_candidate"] = candidate.candidate_name
            st.session_state["view"] = "detail"
            st.rerun()

    if st.button("Start over"):
        st.session_state["view"] = "setup"
        st.session_state["results"] = []
        st.rerun()
        
def render_detail_view():
    """Render the full evidence breakdown for one selected candidate."""
    st.header("Candidate detail")

    candidate_name = st.session_state["selected_candidate"]
    results = st.session_state["results"]
    candidate = next((c for c in results if c.candidate_name == candidate_name), None)

    if candidate is None:
        st.error("Candidate not found.")
        if st.button("Back to results"):
            st.session_state["view"] = "results"
            st.rerun()
        return

    st.subheader(candidate.candidate_name)

    metric_cols = st.columns(2)
    metric_cols[0].metric("Keyword score", f"{candidate.keyword_score:.1f}")
    metric_cols[1].metric("Proof score", f"{candidate.proof_score:.1f}")

    st.divider()

    for evidence in candidate.evidence:
        st.markdown(f"**{evidence.skill}** — Tier {evidence.tier}")
        st.caption(evidence.excerpt)

        if evidence.github_verified is not None:
            gh = evidence.github_verified
            lang_status = "✓" if gh.language_verified else "✗"
            text_status = "✓" if gh.text_verified else "✗"
            st.text(f"GitHub — language: {lang_status}  text: {text_status}")

            if gh.language_evidence:
                st.text(f"  Language match in: {', '.join(gh.language_evidence)}")
            if gh.text_evidence:
                st.text(f"  Text match in: {', '.join(gh.text_evidence)}")

        st.divider()

    if st.button("Back to results"):
        st.session_state["view"] = "results"
        st.rerun()
        
def main():
    initialize_session_state()

    view = st.session_state["view"]

    if view == "setup":
        render_setup_view()
    elif view == "results":
        render_results_view()
    elif view == "detail":
        render_detail_view()


if __name__ == "__main__":
    main()