import json
import argparse
import env_setup

from eval_engine import build_sandbox_image, evaluate_project

def main():

    parser = argparse.ArgumentParser(description="Run test evaluations in the Docker sandbox.")
    parser.add_argument("run_id", type=str, help="The ID for this run (e.g., 0, 1, 2)")
    args = parser.parse_args()

    run_id = args.run_id

    current_run_dir = env_setup.BASELINE_RESULTS_DIR / run_id
    current_run_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("STEP 1: Ensuring Docker Sandbox is Built")
    print("="*60)
    build_sandbox_image()

    print("\n" + "="*60)
    print("STEP 2: Running Baseline Evaluations")
    print("="*60)

    metadata_files = sorted(list(env_setup.METADATA_DIR.glob("*.json")))
    print(f"Found {len(metadata_files)} projects to evaluate.\n")

    for meta_file in metadata_files:
        project_id = meta_file.stem
        
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        import_name = metadata.get("import_name")
        test_dependencies = metadata.get("test_dependencies", [])
        if not import_name:
            print(f"[ERROR] {project_id}: No 'import_name' found. Skipping.")
            continue
        
        repo_dir = env_setup.REPOS_DIR / project_id
        test_file = env_setup.TESTS_DIR / f"test_{project_id}.py"
        
        if not repo_dir.exists():
            print(f"[SKIP] {project_id.ljust(15)} | Missing repository folder.")
            continue
        if not test_file.exists():
            print(f"[SKIP] {project_id.ljust(15)} | Missing test file.")
            continue
            
        print(f"Evaluating: {project_id.ljust(15)} | Import: {import_name}")
        
        status = evaluate_project(
            project_id=project_id,
            import_name=import_name,
            repo_dir=repo_dir,
            test_file=test_file,
            base_output_dir=current_run_dir,
            test_dependencies=test_dependencies
        )
        
        print(f"  -> Status: {status}")

    print("\n" + "="*60)
    print("STEP 3: Compiling Master Scorecard")
    print("="*60)

    master_scorecard = {}

    # Loop through the output directories we just created
    for project_dir in current_run_dir.iterdir():
        if project_dir.is_dir():
            eval_file = project_dir / "evaluation.json"
            if eval_file.exists():
                with open(eval_file, "r", encoding="utf-8") as f:
                    master_scorecard[project_dir.name] = json.load(f)

    # Save the master file
    master_file_path = current_run_dir / "master_baseline_report.json"
    with open(master_file_path, "w", encoding="utf-8") as f:
        json.dump(master_scorecard, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Compiled {len(master_scorecard)} evaluations into {master_file_path.name}")


if __name__ == "__main__":
    main()