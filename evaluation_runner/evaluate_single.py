import argparse
import json
import sys
from pathlib import Path

# ==========================================
# 1. PATH RESOLUTION
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from eval_engine import evaluate_project

# Define ground-truth directories
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
TESTS_GEN_DIR = PROJECT_ROOT / "tests_gen"

# ==========================================
# 2. MAIN EXECUTION
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="Evaluate a single generated project against the benchmark.")
    parser.add_argument("--source-dir", required=True, help="Path to the generated repository code")
    
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()

    # --- AUTOMATIC INFERENCE ---
    # 1. Project ID is just the name of the folder (e.g., 'tabulate')
    project_id = source_dir.name

    # 2. Output Directory Calculation
    if source_dir.parent.name == "generated_code":
        experiment_root = source_dir.parent.parent
    else:
        print(f"[WARNING] Source directory is not inside a 'generated_code' folder.")
        print(f"Falling back to creating 'results' next to the source directory.")
        experiment_root = source_dir.parent

    output_dir = experiment_root / "results"

    print("="*60)
    print(f"Evaluating Single Project: {project_id}")
    print(f"Source Code: {source_dir}")
    print(f"Auto-Output: {output_dir}")
    print("="*60)

    # 1. Validate Source Directory
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"[ERROR] Source directory does not exist: {source_dir}")
        sys.exit(1)

    # 2. Load Metadata
    meta_file = METADATA_DIR / f"{project_id}.json"
    if not meta_file.exists():
        print(f"[ERROR] Metadata file not found: {meta_file}")
        sys.exit(1)

    with open(meta_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    import_name_gen = metadata.get("import_name_gen")
    test_dependencies = metadata.get("test_dependencies", [])

    if not import_name_gen:
        print(f"[ERROR] 'import_name_gen' missing in metadata for {project_id}")
        sys.exit(1)

    # 3. Locate the Anonymized Test File
    test_file = TESTS_GEN_DIR / f"test_{project_id}.py"
    if not test_file.exists():
        print(f"[ERROR] Anonymized test file not found: {test_file}")
        sys.exit(1)

    # 4. Ensure Output Directory Exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 5. Run the Evaluation Engine
    print(f"  -> Target Module: {import_name_gen}")
    print(f"  -> Extra Dependencies: {test_dependencies if test_dependencies else 'None'}")
    print(f"  -> Firing up Docker Sandbox...")

    status = evaluate_project(
        project_id=project_id,
        import_name=import_name_gen,
        repo_dir=source_dir,
        test_file=test_file,
        base_output_dir=output_dir,
        test_dependencies=test_dependencies
    )

    print("\n" + "="*60)
    if status == "SUCCESS":
        print(f"[SUCCESS] Evaluation complete. Results saved to {output_dir.relative_to(PROJECT_ROOT)}/{project_id}/")
    elif status == "ALREADY_EVALUATED":
        print(f"[SKIP] Project already evaluated. Results exist in {output_dir.relative_to(PROJECT_ROOT)}/{project_id}/")
    else:
        print(f"[FAILED] Evaluation ended with status: {status}")
    print("="*60)

if __name__ == "__main__":
    main()