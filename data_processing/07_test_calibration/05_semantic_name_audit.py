import json
import re
import env_setup

from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import vertex_openai
from chase.components.io import variable

from chase.components.pipelines.response_sanitization import think_tag_remover
from chase.components.pipelines.response_sanitization import json_fence_enforcer
from chase.components.pipelines.normalization import json_code_block_tagger
from chase.components.pipelines.post_response_normalization import json_escape_repair
from chase.components.pipelines.presentation import json_fence_stripper

def main():
    env_setup.EXP_05_SEMANTIC_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    global_renames_file = env_setup.EXP_05_SEMANTIC_AUDIT_DIR / "global_renames.json"

    # 1. Load Prompt
    prompt_path = env_setup.PROMPTS_DIR / "semantic_audit_prompt.md"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"[ERROR] Prompt not found at {prompt_path.name}")
        exit(1)

    if global_renames_file.exists():
        with open(global_renames_file, "r", encoding="utf-8") as f:
            global_renames = json.load(f)
        print(f"[INFO] Loaded {len(global_renames)} already processed projects.")
    else:
        global_renames = {}

    print("="*60)
    print("STEP 1: Auditing Test Names via LLM")
    print("="*60)

    test_files = sorted(list(env_setup.TESTS_DIR.glob("test_*.py")))

    for test_file in test_files:
        project_name = test_file.stem.replace("test_", "")
        print(f"Auditing: {project_name}...")

        if project_name in global_renames:
            print("  [SKIP] Already processed and saved in JSON.")
            continue

        chase_worker = Chase(profile="05_semantic_name_audit", session_id=project_name)

        with open(test_file, "r", encoding="utf-8") as f:
            test_code = f.read()

        # Resumability: If already processed, read from Chase history
        if len(chase_worker.session.messages) >= 2:
            print("  [SKIP] Already audited. Reading from history...")
            response = chase_worker.session.messages[-1].content.to_text()
        else:
            current_prompt = prompt_template.replace("[PROJECT_NAME]", project_name)
            current_prompt = current_prompt.replace("[TEST_CODE]", test_code)
            
            chase_worker.input.feed(current_prompt)
            response = chase_worker.output.get_output()


        renames = json.loads(response)

        # Filter out the "reason" and keep only original and proposed
        project_renames = []
        for item in renames:
            if "original_name" in item and "proposed_name" in item:
                project_renames.append({
                    "original_name": item["original_name"],
                    "proposed_name": item["proposed_name"]
                })

        global_renames[project_name] = project_renames
        
        with open(global_renames_file, "w", encoding="utf-8") as f:
            json.dump(global_renames, f, indent=2, ensure_ascii=False)

        if project_renames:
            print(f"  [SAVED] {len(project_renames)} renames suggested.")
        else:
            print("  [SAVED] No renames needed.")

    # Save the Global JSON
    with open(global_renames_file, "w", encoding="utf-8") as f:
        json.dump(global_renames, f, indent=2, ensure_ascii=False)
    print(f"\n[SUCCESS] Saved global renames to {global_renames_file.name}")


    print("\n" + "="*60)
    print("STEP 2: Applying Renames to Test Files")
    print("="*60)

    total_replacements = 0

    for project_name, renames in global_renames.items():
        test_file = env_setup.TESTS_DIR / f"test_{project_name}.py"
        if not test_file.exists():
            continue

        with open(test_file, "r", encoding="utf-8") as f:
            test_code = f.read()

        modified = False
        for rename in renames:
            orig = rename["original_name"]
            prop = rename["proposed_name"]

            # CRITICAL: Safe regex replacement using word boundaries (\b)
            # This prevents replacing 'test_add' inside 'test_add_negative'
            pattern = rf"\b{re.escape(orig)}\b"
            
            if re.search(pattern, test_code):
                test_code = re.sub(pattern, prop, test_code)
                modified = True
                total_replacements += 1
                print(f"  [{project_name}] {orig} -> {prop}")
            else:
                print(f"  [WARNING] Could not find '{orig}' in {project_name} to replace.")

        # Write the modified code back to the file
        if modified:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_code)

    print("\n" + "="*60)
    print(f"[DONE] Applied {total_replacements} total renames across all projects.")
    print("="*60)

if __name__ == "__main__":
    main()