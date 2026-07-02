import json
from pathlib import Path

# ==========================================
# 1. PATH DEFINITIONS
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()           # .../data_processing/test_plan_merger
DATA_PROCESSING_DIR = BASE_DIR.parent                # .../data_processing

# Input Files
RAL_BENCH_PLAN_PATH = DATA_PROCESSING_DIR / "02_llm_test_analysis" / "experiments" / "ral_bench_functional_test_plan.json"
GENERATED_PLAN_PATH = DATA_PROCESSING_DIR / "03_llm_test_generation" / "experiments" / "final_functional_tests.json"

# Output File
OUTPUT_DIR = BASE_DIR / "experiments"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MERGED_PLAN_PATH = OUTPUT_DIR / "functional_test_plan.json"

# ==========================================
# 2. LOAD DATA
# ==========================================
def load_json(filepath):
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print(f"[ERROR] Could not find {filepath.name}")
        return {}

print("Loading test plans...")
ral_bench_data = load_json(RAL_BENCH_PLAN_PATH)
generated_data = load_json(GENERATED_PLAN_PATH)

# ==========================================
# 3. MERGE LOGIC
# ==========================================
print("Merging test plans...\n")

merged_data = {}
stats = []

# Get a unique list of all projects from both files
all_projects = sorted(set(ral_bench_data.keys()).union(set(generated_data.keys())))

for project in all_projects:
    merged_tests = []
    
    # 1. Get RalBench Tests (and add flag = True)
    ral_tests = ral_bench_data.get(project, {}).get("functional_tests", [])
    for test in ral_tests:
        test["is_ral_bench"] = True
        merged_tests.append(test)
        
    # 2. Get Generated Tests (and add flag = False)
    gen_tests = generated_data.get(project, {}).get("functional_tests", [])
    for test in gen_tests:
        test["is_ral_bench"] = False
        merged_tests.append(test)
        
    # 3. Save to merged dictionary
    merged_data[project] = {
        "project_name": project,
        "functional_tests": merged_tests
    }
    
    # 4. Record stats for the console output
    stats.append({
        "project": project,
        "ral_count": len(ral_tests),
        "gen_count": len(gen_tests),
        "total": len(merged_tests)
    })

# ==========================================
# 4. SAVE OUTPUT
# ==========================================
with open(MERGED_PLAN_PATH, "w", encoding="utf-8") as f:
    json.dump(merged_data, f, indent=2, ensure_ascii=False)

# ==========================================
# 5. PRINT STATISTICS
# ==========================================
print("=" * 65)
print(f"{'Project Name'.ljust(20)} | {'RalBench'.rjust(10)} | {'Generated'.rjust(10)} | {'Total'.rjust(10)}")
print("=" * 65)

total_ral = 0
total_gen = 0

for stat in stats:
    total_ral += stat['ral_count']
    total_gen += stat['gen_count']
    print(f"{stat['project'].ljust(20)} | {str(stat['ral_count']).rjust(10)} | {str(stat['gen_count']).rjust(10)} | {str(stat['total']).rjust(10)}")

print("-" * 65)
print(f"{'GRAND TOTAL'.ljust(20)} | {str(total_ral).rjust(10)} | {str(total_gen).rjust(10)} | {str(total_ral + total_gen).rjust(10)}")
print("=" * 65)

print(f"\n[SUCCESS] Merged JSON saved to: {MERGED_PLAN_PATH}")