import json
from pathlib import Path

# ==========================================
# 1. PATH RESOLUTION
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent

# Point directly to Run 6 in the calibration folder
BASELINE_RUN_DIR = PROJECT_ROOT / "data_processing" / "07_test_calibration" / "experiments" / "baseline_results" / "6"
OUTPUT_JSON = BASE_DIR / "baseline_coverage.json"

def main():
    print("="*60)
    print("Extracting Baseline Code Coverage (Run 6)")
    print("="*60)

    if not BASELINE_RUN_DIR.exists():
        print(f"[ERROR] Baseline directory not found: {BASELINE_RUN_DIR}")
        exit(1)

    coverage_data = {}

    # 2. Loop through the projects in Run 6
    for project_dir in BASELINE_RUN_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        project_id = project_dir.name
        eval_file = project_dir / "evaluation.json"

        if not eval_file.exists():
            print(f"  [WARNING] Missing evaluation.json for {project_id}")
            continue

        # Read the scorecard
        with open(eval_file, "r", encoding="utf-8") as f:
            scorecard = json.load(f)

        # Extract coverage
        coverage = scorecard.get("code_coverage", 0.0)
        coverage_data[project_id] = coverage

    # 3. Sort alphabetically by project name
    sorted_projects = sorted(coverage_data.items(), key=lambda x: x[0])

    # 4. Print the results in a clean table
    print(f"{'Project Name'.ljust(20)} | {'Code Coverage (%)'}")
    print("-" * 40)
    
    total_coverage = 0.0
    
    for project_id, coverage in sorted_projects:
        print(f"{project_id.ljust(20)} | {coverage:>6.2f}%")
        total_coverage += coverage

    # Calculate average coverage across the benchmark
    if sorted_projects:
        avg_coverage = total_coverage / len(sorted_projects)
        print("-" * 40)
        print(f"{'AVERAGE'.ljust(20)} | {avg_coverage:>6.2f}%")

    # 5. Save to JSON for later use
    # Convert back to dict but keep the sorted order (Python 3.7+ preserves dict insertion order)
    sorted_dict = {k: v for k, v in sorted_projects}
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(sorted_dict, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print(f"[DONE] Saved to {OUTPUT_JSON.name}")
    print("="*60)

if __name__ == "__main__":
    main()