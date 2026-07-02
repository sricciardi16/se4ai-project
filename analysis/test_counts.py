import ast
import json
from pathlib import Path

# ==========================================
# 1. PATH RESOLUTION
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent

# Point directly to the anonymized tests folder
TESTS_GEN_DIR = PROJECT_ROOT / "tests_gen"
OUTPUT_JSON = BASE_DIR / "test_counts.json"

def count_tests_in_file(filepath: Path) -> int:
    """Uses AST to safely and accurately count functions starting with 'test_'"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        count = 0
        for node in ast.walk(tree):
            # Check if it's a function definition and the name starts with 'test_'
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                count += 1
        return count
    except Exception as e:
        print(f"  [ERROR] Could not parse {filepath.name}: {e}")
        return 0

def main():
    print("="*60)
    print("Extracting Test Counts per Project")
    print("="*60)

    if not TESTS_GEN_DIR.exists():
        print(f"[ERROR] tests_gen directory not found: {TESTS_GEN_DIR}")
        exit(1)

    test_counts = {}
    total_tests_benchmark = 0

    print(f"{'Project Name'.ljust(20)} | {'Number of Tests'}")
    print("-" * 40)

    # Loop through all test files in tests_gen
    for test_file in TESTS_GEN_DIR.glob("test_*.py"):
        # Extract project name (e.g., "test_tabulate.py" -> "tabulate")
        project_id = test_file.stem.replace("test_", "")
        
        count = count_tests_in_file(test_file)
        test_counts[project_id] = count
        total_tests_benchmark += count

    # Sort by number of tests (Highest to Lowest)
    sorted_projects = sorted(test_counts.items(), key=lambda x: x[1], reverse=True)
    
    for project_id, count in sorted_projects:
        print(f"{project_id.ljust(20)} | {count}")

    print("-" * 40)
    print(f"{'TOTAL BENCHMARK'.ljust(20)} | {total_tests_benchmark} tests")

    # Save to JSON
    sorted_dict = {k: v for k, v in sorted_projects}
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(sorted_dict, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print(f"[DONE] Saved to {OUTPUT_JSON.name}")
    print("="*60)

if __name__ == "__main__":
    main()