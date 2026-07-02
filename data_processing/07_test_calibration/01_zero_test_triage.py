import json
import argparse
import env_setup

from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable


# The specific projects that suffered Collection Errors
TARGET_PROJECTS = ["stegano", "pypdf", "imageio", "lifelines"]
RUN_ID = "0"  # Hardcoded to look at the first baseline run

def main():
    env_setup.EXP_01_TRIAGE_DIR.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print(f"STEP 1: Triaging Zero-Test Failures (Run ID: {RUN_ID})")
    print("="*60)

    # 1. Load the Prompt
    prompt_path = env_setup.PROMPTS_DIR / "zero_test_triage_prompt.md"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"[ERROR] Prompt not found at {prompt_path.name}")
        exit(1)

    # 2. Process Each Target Project
    for project_name in TARGET_PROJECTS:
        print(f"\nAnalyzing: {project_name}...")

        # Initialize Chase
        chase_worker = Chase(profile="01_zero_test_triage", session_id=project_name)
        
        # Resumability check
        if len(chase_worker.session.messages) >= 2:
            print(f"  [SKIP] Already analyzed. Check markdown file.")
            continue

        # --- Gather Data ---
        
        # A. Target Version
        meta_file = env_setup.METADATA_DIR / f"{project_name}.json"
        target_version = "UNKNOWN"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                target_version = json.load(f).get("inferred_version", "UNKNOWN")

        # B. Test Code
        test_file = env_setup.TESTS_DIR / f"test_{project_name}.py"
        test_code = ""
        if test_file.exists():
            with open(test_file, "r", encoding="utf-8") as f:
                test_code = f.read().strip()

        # C. Pytest Log
        log_file = env_setup.BASELINE_RESULTS_DIR / RUN_ID / project_name / "raw_artifacts" / "pytest.log"
        pytest_log = ""
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                pytest_log = f.read().strip()
        else:
            # Fallback to install.log if pytest didn't even run
            install_log = env_setup.BASELINE_RESULTS_DIR / RUN_ID / project_name / "raw_artifacts" / "install.log"
            if install_log.exists():
                with open(install_log, "r", encoding="utf-8") as f:
                    pytest_log = "[PYTEST LOG MISSING. SHOWING INSTALL LOG INSTEAD]\n" + f.read().strip()

        # --- Execute LLM ---
        
        # Inject variables into prompt
        current_prompt = prompt_template.replace("[PROJECT_NAME]", project_name)
        current_prompt = current_prompt.replace("[TARGET_VERSION]", target_version)
        current_prompt = current_prompt.replace("[TEST_CODE]", test_code)
        current_prompt = current_prompt.replace("[PYTEST_LOG]", pytest_log)

        print(f"  -> Feeding data to LLM...")
        chase_worker.input.feed(current_prompt)
        chase_worker.output.get_output()
        
        print(f"  [SUCCESS] Analysis saved to {env_setup.EXP_01_TRIAGE_DIR.name}/{project_name}.md")

    print("\n" + "="*60)
    print("[DONE] Triage complete. Review the markdown files to see the diagnosis.")
    print("="*60)

if __name__ == "__main__":
    main()