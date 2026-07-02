import json
import re
import env_setup

from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.providers import vertex_openai
from chase.components.io import variable



def main():
    env_setup.EXP_02_ANONYMIZED_IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    env_setup.TESTS_GEN_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Mapping and Prompt
    mapping_file = env_setup.EXP_01_ANONYMIZATION_DIR / "anonymized_mapping.json"
    if not mapping_file.exists():
        print(f"[ERROR] Mapping file not found. Run step 01 first.")
        exit(1)
        
    with open(mapping_file, "r", encoding="utf-8") as f:
        anonymized_mapping = json.load(f)

    prompt_path = env_setup.PROMPTS_DIR / "anonymize_imports_prompt.md"
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    print("="*60)
    print("STEP 1: Generating Isomorphic Imports via LLM")
    print("="*60)

    test_files = sorted(list(env_setup.TESTS_DIR.glob("test_*.py")))
    rewritten_imports_cache = {}

    for test_file in test_files:
        project_name = test_file.stem.replace("test_", "")
        anonymized_name = anonymized_mapping.get(project_name)
        
        if not anonymized_name:
            print(f"  [SKIP] {project_name} has no anonymized name in mapping.")
            continue

        # Extract the original imports
        with open(test_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        original_imports = []
        in_subject_section = False
        for line in lines:
            if line.strip() == "# 2. The Subject Under Test":
                in_subject_section = True
                continue
            if in_subject_section:
                if line.strip() == "":
                    break
                original_imports.append(line.rstrip())

        original_imports_str = "\n".join(original_imports)

        # Call LLM
        chase_worker = Chase(profile="02_anonymized_imports", session_id=project_name)
        
        if len(chase_worker.session.messages) >= 2:
            print(f"  [SKIP] {project_name.ljust(15)} | Already generated. Reading from history...")
            response = chase_worker.session.messages[-1].content.to_text()
        else:
            print(f"  [LLM]  {project_name.ljust(15)} | Generating imports for '{anonymized_name}'...")
            
            # Handle the special import names (e.g., pyjwt -> jwt)
            # We need to tell the LLM the actual import name used in the code
            actual_import_name = "jwt" if project_name == "pyjwt" else project_name.replace("-", "_")
            if project_name == "pypdf": actual_import_name = "PyPDF2"
            
            current_prompt = prompt_template.replace("[ORIGINAL_NAME]", actual_import_name)
            current_prompt = current_prompt.replace("[ANONYMIZED_NAME]", anonymized_name)
            current_prompt = current_prompt.replace("[ORIGINAL_IMPORTS]", original_imports_str)
            
            chase_worker.input.feed(current_prompt)
            response = chase_worker.output.get_output()

        # Extract Python code safely
        match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
        if match:
            new_imports = match.group(1).strip()
        else:
            # Fallback: strip backticks manually if the regex fails
            new_imports = response.replace('```python', '').replace('```', '').strip()
            
        if not new_imports:
            print(f"  [ERROR] Extracted imports are empty for {project_name}! Raw response: {response}")
        
        rewritten_imports_cache[project_name] = new_imports
        
        # Save the snippet for debugging
        snippet_file = env_setup.EXP_02_ANONYMIZED_IMPORTS_DIR / f"{project_name}_imports.py"
        with open(snippet_file, "w", encoding="utf-8") as f:
            f.write(new_imports + "\n")

    print("\n" + "="*60)
    print("STEP 2: Assembling tests_gen/ Directory")
    print("="*60)

    for test_file in test_files:
        project_name = test_file.stem.replace("test_", "")
        if project_name not in rewritten_imports_cache:
            continue

        new_imports = rewritten_imports_cache[project_name]
        
        with open(test_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_file_lines = []
        in_subject_section = False
        section_replaced = False

        for line in lines:
            if line.strip() == "# 2. The Subject Under Test":
                in_subject_section = True
                new_file_lines.append(line)
                new_file_lines.append(new_imports + "\n")
                section_replaced = True
                continue
            
            if in_subject_section:
                if line.strip() == "":
                    in_subject_section = False
                    new_file_lines.append(line) # Keep the empty line
                continue # Skip the old imports
                
            new_file_lines.append(line)

        if section_replaced:
            output_file = env_setup.TESTS_GEN_DIR / test_file.name
            with open(output_file, "w", encoding="utf-8") as f:
                f.writelines(new_file_lines)
            print(f"  [SUCCESS] Created {output_file.name}")
        else:
            print(f"  [WARNING] Could not find import section in {test_file.name}")

    print("\n" + "="*60)
    print(f"[DONE] All anonymized tests are ready in {env_setup.TESTS_GEN_DIR.name}/")
    print("="*60)

if __name__ == "__main__":
    main()