import json
import re
import env_setup

from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.providers import vertex_openai
from chase.components.io import variable

from chase.components.pipelines.response_sanitization import think_tag_remover
from chase.components.pipelines.response_sanitization import json_fence_enforcer
from chase.components.pipelines.normalization import json_code_block_tagger
from chase.components.pipelines.post_response_normalization import json_escape_repair
from chase.components.pipelines.presentation import json_fence_stripper

def main():
    env_setup.EXP_01_ANONYMIZATION_DIR.mkdir(parents=True, exist_ok=True)
    mapping_file = env_setup.EXP_01_ANONYMIZATION_DIR / "anonymized_mapping.json"

    # 1. Load Prompt
    prompt_path = env_setup.PROMPTS_DIR / "anonymize_name_prompt.md"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"[ERROR] Prompt not found at {prompt_path.name}")
        exit(1)

    # Load existing mapping if it exists (for resumability)
    if mapping_file.exists():
        with open(mapping_file, "r", encoding="utf-8") as f:
            anonymized_mapping = json.load(f)
    else:
        anonymized_mapping = {}

    print("="*60)
    print("STEP 1: Generating Anonymized Library Names")
    print("="*60)

    test_files = sorted(list(env_setup.TESTS_DIR.glob("test_*.py")))
    print(f"Found {len(test_files)} test suites to process.\n")

    for test_file in test_files:
        project_name = test_file.stem.replace("test_", "")
        
        if project_name in anonymized_mapping:
            print(f"  [SKIP] {project_name.ljust(15)} | Already mapped to: {anonymized_mapping[project_name]}")
            continue

        print(f"Processing: {project_name}...")

        with open(test_file, "r", encoding="utf-8") as f:
            test_code = f.read()

        # Initialize Chase
        chase_worker = Chase(profile="01_anonymized_names", session_id=project_name)

        # Inject into prompt
        current_prompt = prompt_template.replace("[TEST_CODE]", test_code)
        
        chase_worker.input.feed(current_prompt)
        response = chase_worker.output.get_output()

        # Parse the JSON response
        try:
            data = json.loads(response)
            
            new_name = data.get("anonymized_name", f"anon_{project_name}")
            
            # Ensure it's a valid python module name (just in case the LLM hallucinates)
            new_name = new_name.lower().replace("-", "_").replace(" ", "_")
            
            anonymized_mapping[project_name] = new_name
            print(f"  [SUCCESS] {project_name.ljust(15)} -> {new_name}")
            
            # Save incrementally
            with open(mapping_file, "w", encoding="utf-8") as f:
                json.dump(anonymized_mapping, f, indent=2, ensure_ascii=False)
                
        except json.JSONDecodeError:
            print(f"  [ERROR] Invalid JSON returned for {project_name}.")

    print("\n" + "="*60)
    print(f"[DONE] Mapping saved to {mapping_file.name}")
    print("="*60)

if __name__ == "__main__":
    main()