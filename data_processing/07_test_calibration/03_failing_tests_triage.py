import json
import argparse
import env_setup

from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable


def main():
    # 1. Setup Argument Parser
    parser = argparse.ArgumentParser(description="Triage failing tests from a specific baseline run.")
    parser.add_argument("run_id", type=str, help="The ID of the baseline run to analyze (e.g., 2)")
    args = parser.parse_args()

    run_id = args.run_id
    run_dir = env_setup.BASELINE_RESULTS_DIR / run_id

    if not run_dir.exists():
        print(f"[ERROR] Run directory does not exist: {run_dir}")
        exit(1)

    env_setup.EXP_03_FAILING_TRIAGE_DIR.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print(f"STEP 1: Triaging Failing Tests (Run ID: {run_id})")
    print("="*60)

    # 2. Load the Prompt
    prompt_path = env_setup.PROMPTS_DIR / "failing_tests_triage_prompt.md"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"[ERROR] Prompt not found at {prompt_path.name}")
        exit(1)

    # 3. Process Each Project in the Run Directory
    for project_dir in sorted(run_dir.iterdir()):
        if not project_dir.is_dir():
            continue

        project_name = project_dir.name
        eval_file = project_dir / "evaluation.json"

        if not eval_file.exists():
            continue

        # Read the scorecard
        with open(eval_file, "r", encoding="utf-8") as f:
            scorecard = json.load(f)

        # Skip if it crashed entirely (handled in previous steps)
        if scorecard.get("total_tests", 0) == 0:
            print(f"[SKIP] {project_name.ljust(15)} | 0 tests collected (Collection Error).")
            continue

        # Filter for failing tests
        dossier = scorecard.get("test_dossier", {})
        failing_tests = []
        
        for test_name, details in dossier.items():
            if details.get("status") != "PASSED":
                failing_tests.append((test_name, details))

        # Skip if everything passed!
        if not failing_tests:
            print(f"[SUCCESS] {project_name.ljust(15)} | All tests passed! No triage needed.")
            continue

        print(f"\nAnalyzing: {project_name} ({len(failing_tests)} failing tests)...")

        # Initialize Chase
        chase_worker = Chase(profile="03_failing_tests_triage", session_id=project_name)
        
        # Resumability check
        if len(chase_worker.session.messages) >= 2:
            print(f"  [SKIP] Already analyzed. Check markdown file.")
            continue

        # --- Format the Failing Tests Summary ---
        summary_lines = []
        for test_name, details in failing_tests:
            summary_lines.append(f"- Test `{test_name}`")
            summary_lines.append(f"    - Status: `{details.get('status')}`")
            summary_lines.append(f"    - Crash Category: `{details.get('crash_category', 'None')}`")
            summary_lines.append(f"    - Crash Message: `{details.get('crash_message', 'None')}`\n")
            
        failing_tests_summary = "\n\n".join(summary_lines).strip()

        # --- Gather Metadata & Code ---
        meta_file = env_setup.METADATA_DIR / f"{project_name}.json"
        target_version = "UNKNOWN"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                target_version = json.load(f).get("inferred_version", "UNKNOWN")

        test_file = env_setup.TESTS_DIR / f"test_{project_name}.py"
        test_code = ""
        if test_file.exists():
            with open(test_file, "r", encoding="utf-8") as f:
                test_code = f.read().strip()

        # --- Execute LLM ---
        current_prompt = prompt_template.replace("[PROJECT_NAME]", project_name)
        current_prompt = current_prompt.replace("[TARGET_VERSION]", target_version)
        current_prompt = current_prompt.replace("[TEST_CODE]", test_code)
        current_prompt = current_prompt.replace("[FAILING_TESTS_SUMMARY]", failing_tests_summary)

        print(f"  -> Feeding {len(failing_tests)} failures to LLM...")
        chase_worker.input.feed(current_prompt)
        chase_worker.output.get_output()
        
        print(f"  [DONE] Analysis saved to {env_setup.EXP_03_FAILING_TRIAGE_DIR.name}/{project_name}.md")

    print("\n" + "="*60)
    print("[COMPLETE] All failing tests have been triaged.")
    print("="*60)

if __name__ == "__main__":
    main()