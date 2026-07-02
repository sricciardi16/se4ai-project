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

from eval_engine import evaluate_project, build_sandbox_image

# Define ground-truth directories
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
TESTS_GEN_DIR = PROJECT_ROOT / "tests_gen"

# ==========================================
# 2. MAIN EXECUTION
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="Evaluate an entire experiment batch (Approach + Model).")
    parser.add_argument("--experiment-dir", required=True, help="Path to the experiment root (e.g., evaluations/zero_shot/gpt-4o)")
    
    args = parser.parse_args()
    experiment_dir = Path(args.experiment_dir).resolve()

    generated_code_dir = experiment_dir / "generated_code"
    results_dir = experiment_dir / "results"

    print("="*60)
    print(f"Evaluating Experiment Batch")
    print(f"Experiment Dir: {experiment_dir.relative_to(PROJECT_ROOT)}")
    print("="*60)

    if not generated_code_dir.exists() or not generated_code_dir.is_dir():
        print(f"[ERROR] 'generated_code' directory not found inside {experiment_dir}")
        sys.exit(1)

    # 1. Ensure Docker Sandbox is ready before a massive batch run
    print("\nSTEP 1: Ensuring Docker Sandbox is Built")
    build_sandbox_image()

    # 2. Find all generated projects
    project_dirs = sorted([d for d in generated_code_dir.iterdir() if d.is_dir()])
    print(f"\nSTEP 2: Evaluating {len(project_dirs)} projects")
    print("="*60)

    results_dir.mkdir(parents=True, exist_ok=True)

    for source_dir in project_dirs:
        project_id = source_dir.name
        print(f"\nEvaluating: {project_id}")

        # Load Metadata
        meta_file = METADATA_DIR / f"{project_id}.json"
        if not meta_file.exists():
            print(f"  [ERROR] Metadata file not found. Skipping.")
            continue

        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        import_name_gen = metadata.get("import_name_gen")
        test_dependencies = metadata.get("test_dependencies", [])

        if not import_name_gen:
            print(f"  [ERROR] 'import_name_gen' missing in metadata. Skipping.")
            continue

        # Locate the Anonymized Test File
        test_file = TESTS_GEN_DIR / f"test_{project_id}.py"
        if not test_file.exists():
            print(f"  [ERROR] Anonymized test file not found. Skipping.")
            continue

        # Run the Evaluation Engine
        status = evaluate_project(
            project_id=project_id,
            import_name=import_name_gen,
            repo_dir=source_dir,
            test_file=test_file,
            base_output_dir=results_dir,
            test_dependencies=test_dependencies
        )

        if status == "SUCCESS":
            print(f"  [SUCCESS] Results saved.")
        elif status == "ALREADY_EVALUATED":
            print(f"  [SKIP] Already evaluated.")
        else:
            print(f"  [FAILED] Status: {status}")

    # 3. Compile the Master Scorecard
    print("\n" + "="*60)
    print("STEP 3: Compiling Master Scorecard")
    print("="*60)

    master_scorecard = {}

    for project_dir in results_dir.iterdir():
        if project_dir.is_dir():
            eval_file = project_dir / "evaluation.json"
            if eval_file.exists():
                with open(eval_file, "r", encoding="utf-8") as f:
                    master_scorecard[project_dir.name] = json.load(f)

    master_file_path = results_dir / "master_scorecard.json"
    with open(master_file_path, "w", encoding="utf-8") as f:
        json.dump(master_scorecard, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Compiled {len(master_scorecard)} evaluations into {master_file_path.relative_to(PROJECT_ROOT)}")
    print("="*60)

if __name__ == "__main__":
    main()