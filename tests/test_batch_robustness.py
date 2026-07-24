"""
Batch robustness test: runs extract_text() + segment_sections() against
every real resume in tests/fixtures/real_resumes/ and reports how the
parser holds up at volume — not pass/fail assertions, just stats.

"""

import os
import tempfile
from robustness_runner import run_batch_test
 
FIXTURES_DIR = os.path.join("tests", "fixtures")
 
 
def test_batch_reports_correct_success_count():
    result = run_batch_test(FIXTURES_DIR)
    assert result["success_count"] == 3
 
 
def test_batch_reports_correct_failure_count():
    result = run_batch_test(FIXTURES_DIR)
    assert result["failure_count"] == 5
 
 
def test_batch_groups_failures_by_error_type():
    result = run_batch_test(FIXTURES_DIR)
    failed_filenames = {f["filename"] for f in result["failures"]}
    expected_failures = {
        "password_protected.pdf",
        "corrupted.pdf",
        "scanned_no_text.pdf",
        "fake_docx.docx",
        "wrong_format.jpg",
    }
    assert failed_filenames == expected_failures
    # every failure entry should have a non-empty error type and message
    for failure in result["failures"]:
        assert failure["error_type"]
        assert failure["message"]
 
 
def test_batch_handles_empty_directory():
    with tempfile.TemporaryDirectory() as empty_dir:
        result = run_batch_test(empty_dir)
        assert result["total_files"] == 0
        assert result["success_count"] == 0
        assert result["failure_count"] == 0