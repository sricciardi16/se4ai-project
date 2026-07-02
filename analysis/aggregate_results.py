import json
from pathlib import Path

# ==========================================
# 1. PATH RESOLUTION
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent

EVALUATIONS_DIR = PROJECT_ROOT / "evaluations"
DEPENDENCY_FILE = BASE_DIR / "dependency_check.json"
OUTPUT_JSON = BASE_DIR / "benchmark_results.json"

def main():
    print("="*60)
    print("Aggregating Final Benchmark Results")
    print("="*60)

    if not EVALUATIONS_DIR.exists():
        print(f"[ERROR] Evaluations directory not found: {EVALUATIONS_DIR}")
        exit(1)

    if not DEPENDENCY_FILE.exists():
        print(f"[ERROR] Dependency check file not found: {DEPENDENCY_FILE}")
        exit(1)

    # 1. Load the Cheat Detector data
    with open(DEPENDENCY_FILE, "r", encoding="utf-8") as f:
        dependency_data = json.load(f)

    aggregated_data = {}

    # 2. Crawl the directory structure
    eval_files = list(EVALUATIONS_DIR.glob("*/*/results/*/evaluation.json"))
    print(f"Found {len(eval_files)} individual evaluation files.\n")

    for eval_file in eval_files:
        project_id = eval_file.parent.name
        model_name = eval_file.parents[2].name
        approach = eval_file.parents[3].name

        # Read the JSON scorecard
        with open(eval_file, "r", encoding="utf-8") as f:
            scorecard = json.load(f)

        env_status = scorecard.get("environment_status", "UNKNOWN")
        total_tests = scorecard.get("total_tests", 0)
        raw_success_rate = scorecard.get("success_rate", 0.0)

        # Check if this specific project cheated
        used_original_lib = False
        try:
            used_original_lib = dependency_data.get(approach, {}).get(model_name, {}).get(project_id, {}).get("requires_original_lib", False)
        except AttributeError:
            pass

        # --- APPLY THE CATEGORY LOGIC ---
        category = "UNKNOWN"
        final_success_rate = 0.0

        if env_status == "INSTALL_FAILED":
            category = "build_failure"
            final_success_rate = 0.0
            
        elif total_tests == 0:
            # It installed, but Pytest couldn't collect tests (ImportError, SyntaxError, etc.)
            category = "interface_failure"
            final_success_rate = 0.0
            
        elif total_tests > 0:
            # It reached the testable stage! Now we check for cheating.
            if used_original_lib:
                category = "dependency_violation"
                final_success_rate = 0.0  # Punish the cheater!
            else:
                category = "testable"
                final_success_rate = raw_success_rate

        # --- SAVE TO NESTED DICTIONARY ---
        if approach not in aggregated_data:
            aggregated_data[approach] = {}
        if model_name not in aggregated_data[approach]:
            aggregated_data[approach][model_name] = {}

        # Output ONLY the category and success rate
        aggregated_data[approach][model_name][project_id] = {
            "category": category,
            "success_rate": final_success_rate
        }

    if not aggregated_data:
        print("[WARNING] No data found to aggregate.")
        return

    # 3. Write to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(aggregated_data, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Aggregated data saved to {OUTPUT_JSON.name}")
    print("="*60)

if __name__ == "__main__":
    main()