"""
Unit tests for src/parser.py, using the synthetic fixtures in
tests/fixtures/. Covers each function individually plus a few
integration-style checks combining them.
"""

import os
import pytest

from src.parser import (
    extract_text,
    is_valid_docx,
    extract_text_from_pdf,
    extract_text_from_docx,
    segment_sections,
    is_heading,
    extract_github_link,
    extract_linkedin_link,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def fixture_path(filename: str) -> str:
    return os.path.join(FIXTURES_DIR, filename)


# ---------------------------------------------------------------------
# extract_text()
# ---------------------------------------------------------------------

def test_extract_text_valid_pdf():
    with open(fixture_path("clean_single_column.pdf"), "rb") as f:
        text = extract_text(f, "clean_single_column.pdf")
    assert isinstance(text, str)
    assert len(text.strip()) > 0
    assert "Skills" in text


def test_extract_text_valid_docx():
    with open(fixture_path("clean.docx"), "rb") as f:
        text = extract_text(f, "clean.docx")
    assert isinstance(text, str)
    assert len(text.strip()) > 0
    assert "Skills" in text


def test_extract_text_rejects_unsupported_format():
    with open(fixture_path("wrong_format.jpg"), "rb") as f:
        with pytest.raises(ValueError):
            extract_text(f, "wrong_format.jpg")


def test_extract_text_rejects_fake_docx():
    with open(fixture_path("fake_docx.docx"), "rb") as f:
        with pytest.raises(ValueError):
            extract_text(f, "fake_docx.docx")


def test_extract_text_rejects_password_protected():
    with open(fixture_path("password_protected.pdf"), "rb") as f:
        with pytest.raises(ValueError):
            extract_text(f, "password_protected.pdf")


def test_extract_text_rejects_corrupted_file():
    with open(fixture_path("corrupted.pdf"), "rb") as f:
        with pytest.raises(ValueError):
            extract_text(f, "corrupted.pdf")


def test_extract_text_rejects_scanned_pdf():
    with open(fixture_path("scanned_no_text.pdf"), "rb") as f:
        with pytest.raises(ValueError):
            extract_text(f, "scanned_no_text.pdf")


# ---------------------------------------------------------------------
# is_valid_docx()
# ---------------------------------------------------------------------

def test_is_valid_docx_true_for_real_docx():
    with open(fixture_path("clean.docx"), "rb") as f:
        assert is_valid_docx(f) is True


def test_is_valid_docx_false_for_fake_docx():
    with open(fixture_path("fake_docx.docx"), "rb") as f:
        assert is_valid_docx(f) is False


def test_is_valid_docx_false_for_non_zip():
    with open(fixture_path("wrong_format.jpg"), "rb") as f:
        assert is_valid_docx(f) is False


# ---------------------------------------------------------------------
# extract_text_from_pdf() / extract_text_from_docx()
# ---------------------------------------------------------------------

def test_extract_text_from_pdf_multi_column():
    # Multi-column layout won't necessarily read in perfect order —
    # this just confirms it doesn't crash and returns something.
    with open(fixture_path("multi_column.pdf"), "rb") as f:
        text = extract_text_from_pdf(f)
    assert isinstance(text, str)
    assert len(text.strip()) > 0


def test_extract_text_from_docx_returns_paragraphs():
    with open(fixture_path("clean.docx"), "rb") as f:
        text = extract_text_from_docx(f)
    assert "John Doe" in text
    assert "Experience" in text


# ---------------------------------------------------------------------
# is_heading()
# ---------------------------------------------------------------------

def test_is_heading_matches_exact_section_name():
    assert is_heading("Skills") == "skills"
    assert is_heading("Experience") == "experience"
    assert is_heading("Education") == "education"


def test_is_heading_matches_synonym():
    assert is_heading("Work Experience") == "experience"
    assert is_heading("Technical Skills") == "skills"


def test_is_heading_rejects_long_sentence():
    assert is_heading("Developed strong Python skills over three years") is None


def test_is_heading_rejects_unrelated_short_line():
    assert is_heading("New York, NY") is None


# ---------------------------------------------------------------------
# segment_sections()
# ---------------------------------------------------------------------

def test_segment_sections_standard_headings():
    raw_text = (
        "John Doe\n"
        "Skills\n"
        "Python, SQL, React\n"
        "Experience\n"
        "Built a REST API using Django.\n"
        "Education\n"
        "B.S. Computer Science\n"
    )
    result = segment_sections(raw_text)
    assert result["skills"] == ["Python, SQL, React"]
    assert result["experience"] == ["Built a REST API using Django."]
    assert result["education"] == ["B.S. Computer Science"]
    assert result["projects"] == []  # not present in this resume, still a key
    assert result["certifications"] == []


def test_segment_sections_synonym_heading():
    raw_text = "Work Experience\nLed a team of 3 engineers.\n"
    result = segment_sections(raw_text)
    assert result["experience"] == ["Led a team of 3 engineers."]


def test_segment_sections_discards_text_before_first_heading():
    raw_text = "John Doe\njohn@email.com\nSkills\nPython\n"
    result = segment_sections(raw_text)
    assert result["skills"] == ["Python"]
    # "John Doe" and the email should not appear anywhere in the result
    all_lines = [line for section in result.values() for line in section]
    assert "John Doe" not in all_lines


def test_segment_sections_does_not_false_positive_on_body_text():
    raw_text = "Experience\nDeveloped strong Python skills over three years\n"
    result = segment_sections(raw_text)
    # The word "skills" appears inside a sentence here — should stay under
    # "experience", not be mistaken for a new "Skills" heading.
    assert result["experience"] == ["Developed strong Python skills over three years"]
    assert result["skills"] == []


# ---------------------------------------------------------------------
# extract_github_link() / extract_linkedin_link()
# ---------------------------------------------------------------------

def test_extract_github_link_single_match():
    text = "Contact: github.com/johndoe"
    assert extract_github_link(text) == ["github.com/johndoe"]


def test_extract_github_link_multiple_matches():
    text = "github.com/johndoe and also github.com/johndoe/my-project"
    result = extract_github_link(text)
    assert "github.com/johndoe" in result
    assert "github.com/johndoe/my-project" in result


def test_extract_github_link_deduplicates():
    text = "github.com/johndoe mentioned twice: github.com/johndoe"
    assert extract_github_link(text) == ["github.com/johndoe"]


def test_extract_github_link_none_when_absent():
    assert extract_github_link("No links here.") is None


def test_extract_github_link_handles_prefixes():
    text = "https://www.github.com/johndoe"
    assert extract_github_link(text) == ["https://www.github.com/johndoe"]


def test_extract_linkedin_link_single_match():
    text = "linkedin.com/in/johndoe"
    assert extract_linkedin_link(text) == ["linkedin.com/in/johndoe"]


def test_extract_linkedin_link_none_when_absent():
    assert extract_linkedin_link("No links here.") is None
