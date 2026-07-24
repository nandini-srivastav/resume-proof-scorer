"""
Batch robustness test: runs extract_text() + segment_sections() against
every resume in a given folder and reports how the parser holds up —
not pass/fail assertions, just stats.
"""

import os
from src.parser import extract_text, segment_sections

REAL_RESUMES_DIR = os.path.join("tests", "fixtures", "real_resumes")


def run_batch_test(folder_path: str) -> dict:
    files = [f for f in os.listdir(folder_path)
             if os.path.isfile(os.path.join(folder_path, f))]

    stats = {
        "total_files": len(files),
        "success_count": 0,
        "failure_count": 0,
        "failures": [],
        "text_lengths": [],
        "sections_found_counts": [],
    }

    for filename in files:
        filepath = os.path.join(folder_path, filename)

        with open(filepath, "rb") as f:
            try:
                text = extract_text(f, filename)
                sections = segment_sections(text)

                stats["success_count"] += 1
                stats["text_lengths"].append(len(text))
                non_empty_sections = sum(1 for v in sections.values() if v)
                stats["sections_found_counts"].append(non_empty_sections)

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

    if stats["text_lengths"]:
        avg_length = sum(stats["text_lengths"]) / len(stats["text_lengths"])
        print(f"Average extracted text length: {avg_length:.0f} characters")

    if stats["sections_found_counts"]:
        avg_sections = sum(stats["sections_found_counts"]) / len(stats["sections_found_counts"])
        print(f"Average sections detected per resume (out of 5): {avg_sections:.1f}")

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
    result = run_batch_test(REAL_RESUMES_DIR)
    print_report(result)