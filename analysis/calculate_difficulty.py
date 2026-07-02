import json
from pathlib import Path

# ==========================================
# 1. PATH RESOLUTION
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent

# Point directly to Run 6 in the calibration folder
BASELINE_RUN_DIR = PROJECT_ROOT / "data_processing" / "07_test_calibration" / "experiments" / "baseline_results" / "6"
OUTPUT_JSON = BASE_DIR / "target_code_size.json"

def main():
    print("="*60)
    print("Extracting Target Code Size (Covered Lines)")
    print("="*60)

    if not BASELINE_RUN_DIR.exists():
        print(f"[ERROR] Baseline directory not found: {BASELINE_RUN_DIR}")
        exit(1)

    size_data = {}

    print(f"{'Project Name'.ljust(20)} | {'Estimated LOC to Write'}")
    print("-" * 45)

    # Loop through the projects in Run 6
    for project_dir in BASELINE_RUN_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        project_id = project_dir.name
        
        # We need to look at the raw coverage.json, not just the evaluation.json
        coverage_file = project_dir / "raw_artifacts" / "coverage.json"

        if not coverage_file.exists():
            print(f"{project_id.ljust(20)} | [MISSING COVERAGE DATA]")
            continue

        # Read the raw coverage data
        with open(coverage_file, "r", encoding="utf-8") as f:
            cov_data = json.load(f)

        # Extract the exact number of lines executed by the tests
        covered_lines = cov_data.get("totals", {}).get("covered_lines", 0)
        size_data[project_id] = covered_lines

    # Sort by size (Highest to Lowest)
    sorted_projects = sorted(size_data.items(), key=lambda x: x[1], reverse=True)
    
    for project_id, lines in sorted_projects:
        print(f"{project_id.ljust(20)} | {lines} lines")

    # Save to JSON
    sorted_dict = {k: v for k, v in sorted_projects}
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(sorted_dict, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print(f"[DONE] Saved to {OUTPUT_JSON.name}")
    print("="*60)

if __name__ == "__main__":
    main()