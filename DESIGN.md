# Design Document — Resume Proof Scorer

## 1. Problem Statement

High-volume hiring pipelines rely on ATS keyword matching to filter resumes before a human ever sees them, and this filtering breaks more often than most teams realize. In one documented case, a hiring manager submitted his own resume through his company's own applicant tracking system as a test — and it was auto-rejected. The company's ATS had been silently filtering out qualified candidates, including the resume of someone already working there ([source](https://www.yourtango.com/self/manager-proves-hr-system-auto-rejecting-candidates-using-own-resume)). This isn't an isolated glitch — it reflects a structural weakness in keyword-based screening: systems reward keyword density and exact phrasing over demonstrated ability, so a resume that repeats a skill many times can outrank one from a candidate who actually built real projects with it. The result is two failure modes: unqualified but keyword-optimized resumes advancing, and qualified candidates — sometimes even the company's own employees — getting filtered out by their own hiring pipeline.

## 2. Target Audience

Primary: recruiters and hiring teams at companies running high-volume applicant pipelines, who currently rely on keyword-based ATS ranking and want a better signal on which candidates actually demonstrate the skills they claim. Secondary: individual candidates, as a self-check tool to see how their resume would be evaluated for evidence quality, not just keyword presence — useful both as a real feature and as a natural extension if this becomes a two-sided product later.

## 3. Competitive Landscape & Gap

Existing tools split into two camps. Keyword/ATS-optimization tools (Jobscan, Resume Worded) score a resume against a JD by keyword and phrase overlap — useful for candidates trying to pass an ATS filter, but blind to whether a claimed skill is backed by anything real. AI screening platforms (Skima AI, TestGorilla, GoPerfect, Eightfold AI) do semantic matching and explainable scoring, which is a step up from pure keyword counting, but still treat "the resume mentions React" and "the resume describes building three React apps" as roughly the same signal. None of these tools distinguish a claimed skill from a demonstrated one, and none cross-check claims against independently verifiable evidence like a candidate's actual GitHub activity. That's the specific gap this project targets.

## 4. System Design — Data Flow

*(to be drafted — will include a Mermaid diagram)*

## 5. APIs & Dependencies

LLM API (Claude or OpenAI) for skill extraction and evidence-tier classification only — not for final scoring math. GitHub REST API for repo language stats and commit activity, used to verify claimed skills when a candidate links their profile. pdfplumber / python-docx for resume text extraction. Streamlit for the UI. SQLite for persistence (candidate scores, evidence, run history) — upgradeable to Postgres later if needed.

## 6. Edge Cases

Scanned or image-based PDFs with no extractable text (needs OCR fallback or a clear "unsupported format" failure, never a silent wrong score). Multi-column or creative resume layouts that scramble text extraction order. No GitHub link provided (must degrade gracefully, never penalize). GitHub API rate limits on unauthenticated calls (requires a personal access token plus caching). Skill name variants needing normalization ("React" / "ReactJS" / "React.js"). Resumes long enough to hit LLM context limits, requiring chunking. Candidates writing verbose, fabricated-sounding "evidence" with fake specifics — acknowledged as a known limitation rather than solved. Poorly written or vague job descriptions, which should degrade the extraction quality gracefully rather than fail outright.

## 7. Tech Stack Decisions

See `docs/adr/` for individual decision records.

## 8. Production Readiness Checklist

Environment/secrets handled via .env, never hardcoded. Input validation on every API boundary (Pydantic). Real error handling, not bare try/excepts. Unit tests on parsing and scoring logic, plus at least one end-to-end integration test. GitHub Actions running tests on push. Dockerized so it runs anywhere. Caching/rate-limit handling on both the LLM and GitHub API calls. README with architecture diagram, not just usage instructions.
