import json
import shutil
import re
import math
import env_setup

from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable

# ==========================================
# 1. SMART COPY & RENAME FROM 01_REPO_KNOWLEDGE
# ==========================================
print("="*60)
print("STEP 1: Staging Repo Knowledge for Test Generation")
print("="*60)

env_setup.EXP_01_DIR.mkdir(parents=True, exist_ok=True)
env_setup.GENERATED_CODE_DIR.mkdir(parents=True, exist_ok=True)

copied_count = 0
for old_file in env_setup.DIR_01_REPO_KNOWLEDGE.glob("*.md"):
    if old_file.name in env_setup.NAME_MAPPING:
        clean_name = env_setup.NAME_MAPPING[old_file.name]
        dest_file = env_setup.EXP_01_DIR / clean_name
        
        if not dest_file.exists():
            shutil.copy2(old_file, dest_file)
            copied_count += 1

print(f"Copied and renamed {copied_count} files to {env_setup.EXP_01_DIR.name}.")

# ==========================================
# 2. LOAD DATA & PROMPT
# ==========================================
if not env_setup.VERSIONS_FILE.exists() or not env_setup.TEST_PLAN_FILE.exists():
    print("[ERROR] Missing input JSON files. Check previous phases.")
    exit(1)

with open(env_setup.VERSIONS_FILE, "r", encoding="utf-8") as f:
    versions_data = json.load(f)

with open(env_setup.TEST_PLAN_FILE, "r", encoding="utf-8") as f:
    test_plan_data = json.load(f)

prompt_file_path = env_setup.PROMPTS_DIR / "test_generation_prompt.md"
try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
except FileNotFoundError:
    print(f"[ERROR] Could not find {prompt_file_path}")
    exit(1)

BATCH_SIZE = 5

# ==========================================
# 3. EXECUTE TEST GENERATION
# ==========================================
print("\n" + "="*60)
print("STEP 2: Generating Python Test Files")
print("="*60)

for project_name, project_data in test_plan_data.items():
    print(f"\nProcessing: {project_name}")
    
    # 1. Setup Project Directory for Python files
    project_code_dir = env_setup.GENERATED_CODE_DIR / project_name
    project_code_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Get Target Version
    target_version = versions_data.get(project_name, {}).get("target_version", "UNKNOWN")
    if target_version == "UNKNOWN":
        print(f"  [WARNING] Target version is UNKNOWN. Proceeding anyway.")
        
    # 3. Get Tests
    all_tests = project_data.get("functional_tests", [])
    if not all_tests:
        print(f"  [SKIP] No tests found for {project_name}.")
        continue
        
    total_batches = math.ceil(len(all_tests) / BATCH_SIZE)
    print(f"  Found {len(all_tests)} tests. Processing in {total_batches} batches...")
    
    # Initialize Chase
    chase_worker = Chase(profile="01_generate_tests", session_id=project_name)
    
    # Ensure we have the base 2 messages (Prompt + Repo Knowledge)
    if len(chase_worker.session.messages) < 2:
        print(f"  [ERROR] {project_name} does not have the required 2 base messages. Skipping.")
        continue
        
    # Save the pristine base context
    base_context = chase_worker.session.messages[:2]
    
    for batch_idx in range(total_batches):
        batch_num = batch_idx + 1
        py_file_path = project_code_dir / f"{batch_num}.py"
        
        # RESUMABILITY: If the python file already exists, skip this batch!
        if py_file_path.exists():
            print(f"    -> [SKIP] Batch {batch_num}/{total_batches} already exists ({py_file_path.name}).")
            continue
            
        print(f"    -> Generating Batch {batch_num}/{total_batches}...")
        
        # Slice the tests for this batch
        start_idx = batch_idx * BATCH_SIZE
        end_idx = start_idx + BATCH_SIZE
        batch_tests = all_tests[start_idx:end_idx]
        
        # Format the tests into plain text
        formatted_tests_str = ""
        for test in batch_tests:
            formatted_tests_str += f"### `{test['test_name']}`\n\n"
            formatted_tests_str += f"* **Target API:** {test['target_api']}\n"
            formatted_tests_str += f"* **Behavioral Specification:** {test['behavioral_specification']}\n"
            formatted_tests_str += f"* **Crucial Data / Edge Cases:**  \n    {test['crucial_data']}\n\n"
            
        # Inject into prompt
        current_prompt = prompt_template.replace("[TARGET_VERSION]", target_version)
        current_prompt = current_prompt.replace("[TEST_SPECIFICATIONS]", formatted_tests_str.strip())
        
        # CRITICAL: Truncate memory to exactly 2 messages
        chase_worker.session.messages = base_context.copy()
        
        # Feed prompt
        chase_worker.input.feed(current_prompt)
        response = chase_worker.output.get_output()
        
        # Extract Python code using Regex
        match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
        if match:
            python_code = match.group(1).strip()
        else:
            # Fallback if LLM forgot backticks
            print(f"      [WARNING] No ```python block found. Saving raw response.")
            python_code = response.strip()
            
        # Save the Python file
        with open(py_file_path, "w", encoding="utf-8") as f:
            f.write(python_code)
            
        print(f"      [SUCCESS] Saved {py_file_path.name}")

print("\n" + "="*60)
print("[DONE] All test generation complete!")
print(f"Check the '{env_setup.GENERATED_CODE_DIR.name}' folder for the Python files.")
print("="*60)