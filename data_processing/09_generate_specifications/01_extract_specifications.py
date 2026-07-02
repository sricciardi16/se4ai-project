import json
import env_setup

from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable



def main():
    env_setup.EXP_01_SPECS_DIR.mkdir(parents=True, exist_ok=True)
    master_specs_file = env_setup.BASE_DIR / "experiments" / "project_specifications.json"

    # 1. Load Prompt
    prompt_path = env_setup.PROMPTS_DIR / "generate_specs_prompt.md"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"[ERROR] Prompt not found at {prompt_path.name}")
        exit(1)

    # Load existing specs if resuming
    if master_specs_file.exists():
        with open(master_specs_file, "r", encoding="utf-8") as f:
            master_specs = json.load(f)
    else:
        master_specs = {}

    print("="*60)
    print("STEP 1: Generating Natural Language Specifications")
    print("="*60)

    # We use the anonymized tests!
    test_files = sorted(list(env_setup.TESTS_GEN_DIR.glob("test_*.py")))
    print(f"Found {len(test_files)} test suites to process.\n")

    for test_file in test_files:
        project_name = test_file.stem.replace("test_", "")
        
        if project_name in master_specs:
            print(f"  [SKIP] {project_name.ljust(15)} | Specification already generated.")
            continue

        print(f"Processing: {project_name}...")

        # --- Gather Data ---
        
        # 1. Read the anonymized test code
        with open(test_file, "r", encoding="utf-8") as f:
            test_code = f.read()

        # 2. Read the Metadata to get the import names
        meta_file = env_setup.METADATA_DIR / f"{project_name}.json"
        if not meta_file.exists():
            print(f"  [ERROR] Metadata missing for {project_name}. Skipping.")
            continue
            
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        original_import_name = metadata.get("import_name", "UNKNOWN")
        new_import_name = metadata.get("import_name_gen", "UNKNOWN")

        # --- Execute LLM ---

        # Initialize Chase
        chase_worker = Chase(profile="01_generate_specifications", session_id=project_name)

        # Inject into prompt
        current_prompt = prompt_template.replace("[ORIGINAL_IMPORT_NAME]", original_import_name)
        current_prompt = current_prompt.replace("[NEW_IMPORT_NAME]", new_import_name)
        current_prompt = current_prompt.replace("[TEST_CODE]", test_code)
        
        chase_worker.input.feed(current_prompt)
        
        # Get the raw text response from the LLM
        response_text = chase_worker.output.get_output().strip()

        # Save the raw text into our master dictionary
        master_specs[project_name] = {
            "specification": response_text
        }
        
        print(f"  [SUCCESS] {project_name.ljust(15)} | Specification extracted.")
        
        # Save incrementally to the master JSON file
        with open(master_specs_file, "w", encoding="utf-8") as f:
            json.dump(master_specs, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print(f"[DONE] All specifications saved to {master_specs_file.name}")
    print("="*60)

if __name__ == "__main__":
    main()