import re
import env_setup

from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable

# ==========================================
# 1. SETUP
# ==========================================
env_setup.EXP_02_DIR.mkdir(parents=True, exist_ok=True) 
env_setup.FORMATTED_IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
env_setup.FINAL_TEST_FILES_DIR.mkdir(parents=True, exist_ok=True)

prompt_file_path = env_setup.PROMPTS_DIR / "format_imports_prompt.md"
try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
except FileNotFoundError:
    print(f"[ERROR] Could not find {prompt_file_path.name}")
    exit(1)

# ==========================================
# 2. FORMAT IMPORTS VIA LLM
# ==========================================
print("="*60)
print("STEP 1: Formatting Imports via LLM")
print("="*60)

raw_import_files = list(env_setup.MERGED_TESTS_DIR.glob("*_imports.py"))
projects_processed = []

for imp_file in raw_import_files:
    project_name = imp_file.name.replace("_imports.py", "")
    projects_processed.append(project_name)
    
    formatted_file_path = env_setup.FORMATTED_IMPORTS_DIR / f"{project_name}_imports.py"
    
    # Initialize Chase
    chase_worker = Chase(profile="02_format_imports", session_id=project_name)
    
    # Resumability check
    if len(chase_worker.session.messages) >= 2:
        print(f"  [SKIP] {project_name} already formatted.")
        continue
        
    print(f"  -> Formatting imports for: {project_name}")
    
    # Read raw imports
    with open(imp_file, "r", encoding="utf-8") as f:
        raw_imports = f.read().strip()
        
    if not raw_imports:
        print(f"    [WARNING] No imports found for {project_name}.")
        with open(formatted_file_path, "w", encoding="utf-8") as f:
            f.write("")
        continue
        
    # Inject into prompt
    current_prompt = prompt_template.replace("[INSERT PROJECT NAME HERE]", project_name)
    current_prompt = current_prompt.replace("[INSERT RAW IMPORTS HERE]", raw_imports)
    
    # Feed to LLM
    chase_worker.input.feed(current_prompt)
    response = chase_worker.output.get_output()
    
    # Extract Python code
    match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
    if match:
        clean_imports = match.group(1).strip()
    else:
        print(f"    [WARNING] No ```python block found. Saving raw response.")
        clean_imports = response.strip()
        
    # Save to the NEW directory
    with open(formatted_file_path, "w", encoding="utf-8") as f:
        f.write(clean_imports + "\n")

# ==========================================
# 3. VERIFICATION
# ==========================================
print("\n" + "="*60)
print("STEP 2: Verifying Chase Message Counts")
print("="*60)

problematic = []
for project_name in projects_processed:
    check_worker = Chase(profile="02_format_imports", session_id=project_name)
    msg_count = len(check_worker.session.messages)
    
    if msg_count != 2:
        # If it had 0 imports, it might have 0 messages, which is fine.
        raw_imp_file = env_setup.MERGED_TESTS_DIR / f"{project_name}_imports.py"
        with open(raw_imp_file, "r", encoding="utf-8") as f:
            if f.read().strip(): 
                problematic.append((project_name, msg_count))

if problematic:
    print(f"[WARNING] {len(problematic)} projects have incorrect message counts:")
    for p, c in problematic:
        print(f"  - {p} (Messages: {c}, Expected: 2)")
else:
    print("[SUCCESS] All processed projects have exactly 2 messages.")

# ==========================================
# 4. FINAL MERGE (IMPORTS + BODY)
# ==========================================
print("\n" + "="*60)
print("STEP 3: Creating Final Executable Test Files")
print("="*60)

for project_name in projects_processed:
    formatted_imports_file = env_setup.FORMATTED_IMPORTS_DIR / f"{project_name}_imports.py"
    test_body_file = env_setup.MERGED_TESTS_DIR / f"{project_name}_tests.py"
    final_test_file = env_setup.FINAL_TEST_FILES_DIR / f"test_{project_name}.py"
    
    # Read formatted imports
    imports_code = ""
    if formatted_imports_file.exists():
        with open(formatted_imports_file, "r", encoding="utf-8") as f:
            imports_code = f.read().strip()
            
    # Read test body
    test_body_code = ""
    if test_body_file.exists():
        with open(test_body_file, "r", encoding="utf-8") as f:
            test_body_code = f.read().strip()
            
    # Combine with exactly two newlines
    final_code = f"{imports_code}\n\n\n{test_body_code}\n"
    
    # Save final file
    with open(final_test_file, "w", encoding="utf-8") as f:
        f.write(final_code)
        
    print(f"  [SUCCESS] Created {final_test_file.name}")

print("\n" + "="*60)
print(f"[DONE] All final test files are ready in: {env_setup.FINAL_TEST_FILES_DIR.name}/")
print("="*60)


# ==========================================
# 5. EXPORT TO ROOT TESTS DIRECTORY
# ==========================================
import shutil

print("\n" + "="*60)
print("STEP 4: Exporting to Root 'tests' Directory")
print("="*60)

env_setup.ROOT_TESTS_DIR.mkdir(parents=True, exist_ok=True)

exported_count = 0
for test_file in env_setup.FINAL_TEST_FILES_DIR.glob("test_*.py"):
    dest_file = env_setup.ROOT_TESTS_DIR / test_file.name
    
    # Copy the file, overwriting if it already exists
    shutil.copy2(test_file, dest_file)
    exported_count += 1

print(f"[SUCCESS] Exported {exported_count} test files to: {env_setup.ROOT_TESTS_DIR}")
print("="*60)