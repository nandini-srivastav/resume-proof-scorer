"""
Batch pipeline test: runs the full process_resume() pipeline against
every resume in tests/fixtures/real_resumes/ — not just extract_text()
like robustness_runner.py did. Surfaces bugs that only show up at scale
on messy real-world PDFs/DOCX, and gives score distribution stats to
sanity-check the scoring formula.
"""

import os
from app import process_resume

REAL_RESUMES_DIR = os.path.join("tests", "fixtures", "real_resumes")

SAMPLE_JD_SKILLS = [
    "Python", "Java", "JavaScript", "SQL", "AWS",
    "Docker", "Git", "Linux", "C++", "Excel",
]


def run_batch_pipeline_test(folder_path: str, jd_skills: list[str]) -> dict:
    """Run process_resume() against every file in folder_path.

    Args:
        folder_path (str): Directory of resume files to test.
        jd_skills (list[str]): Skills to score every resume against.

    Returns:
        dict: Stats including success/failure counts, failure details,
            and score distributions for successful runs.
    """
    files = [f for f in os.listdir(folder_path)
             if os.path.isfile(os.path.join(folder_path, f))]

    stats = {
        "total_files": len(files),
        "success_count": 0,
        "failure_count": 0,
        "failures": [],
        "keyword_scores": [],
        "proof_scores": [],
        "unknown_name_count": 0,
    }

    for filename in files:
        filepath = os.path.join(folder_path, filename)
        print(f"Processing {filename}...")

        with open(filepath, "rb") as f:
            try:
                result = process_resume(f, filename, jd_skills)

                stats["success_count"] += 1
                stats["keyword_scores"].append(result.keyword_score)
                stats["proof_scores"].append(result.proof_score)
                if result.candidate_name == "Unknown":
                    stats["unknown_name_count"] += 1

            except Exception as e:
                stats["failure_count"] += 1
                stats["failures"].append({
                    "filename": filename,
                    "error_type": type(e).__name__,
                    "message": str(e),
                })

    return stats


def print_report(stats: dict):
    print(f"Total files processed: {stats['total_files']}")
    print(f"Successes: {stats['success_count']}")
    print(f"Failures: {stats['failure_count']}")
    print(f"Unknown candidate names: {stats['unknown_name_count']}")

    if stats["keyword_scores"]:
        avg_keyword = sum(stats["keyword_scores"]) / len(stats["keyword_scores"])
        avg_proof = sum(stats["proof_scores"]) / len(stats["proof_scores"])
        print(f"Average keyword_score: {avg_keyword:.1f}")
        print(f"Average proof_score: {avg_proof:.1f}")

    if stats["failures"]:
        print("\nFailures by type:")
        by_type = {}
        for failure in stats["failures"]:
            by_type.setdefault(failure["error_type"], []).append(failure["filename"])
        for error_type, filenames in by_type.items():
            print(f"  {error_type}: {len(filenames)} files")
            for name in filenames[:5]:
                print(f"    - {name}")


if __name__ == "__main__":
    result = run_batch_pipeline_test(REAL_RESUMES_DIR, SAMPLE_JD_SKILLS)
    print_report(result)
    
    
    