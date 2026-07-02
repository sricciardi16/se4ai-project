import json
import env_setup


from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable

# ==========================================
# 1. SETUP
# ==========================================
env_setup.EXP_04_DIR.mkdir(parents=True, exist_ok=True)

# Load Prompt
prompt_file_path = env_setup.PROMPTS_DIR / "test_suite_audit_prompt.md"
try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
except FileNotFoundError:
    print(f"[ERROR] Could not find {prompt_file_path.name}")
    exit(1)

# Load Versions
if not env_setup.VERSIONS_FILE.exists():
    print(f"[ERROR] Could not find {env_setup.VERSIONS_FILE.name}")
    exit(1)

with open(env_setup.VERSIONS_FILE, "r", encoding="utf-8") as f:
    versions_data = json.load(f)

# ==========================================
# 2. EXECUTE AUDIT
# ==========================================
print("="*60)
print("Executing Senior QA Audit on Final Test Suites")
print("="*60)

# Read the final test files we generated in the previous step
test_files = list(env_setup.FINAL_TEST_FILES_DIR.glob("test_*.py"))
print(f"Found {len(test_files)} test suites to audit.\n")

for test_file in test_files:
    # Extract project name (e.g., "test_tabulate.py" -> "tabulate")
    project_name = test_file.stem.replace("test_", "")
    
    # Get Target Version
    target_version = versions_data.get(project_name, {}).get("target_version", "UNKNOWN")
    
    print(f"Auditing: {project_name} (v{target_version})...")
    
    # Initialize Chase
    chase_worker = Chase(profile="04_test_suite_audit", session_id=project_name)
    
    # Resumability: Skip if already audited
    if len(chase_worker.session.messages) >= 2:
        print(f"  [SKIP] Already audited.")
        continue
        
    # Read the Python code
    with open(test_file, "r", encoding="utf-8") as f:
        test_code = f.read().strip()
        
    if not test_code:
        print(f"  [WARNING] Test file is empty. Skipping.")
        continue
        
    # Inject into prompt
    current_prompt = prompt_template.replace("[PROJECT_NAME]", project_name)
    current_prompt = current_prompt.replace("[TARGET_VERSION]", target_version)
    current_prompt = current_prompt.replace("[INSERT TEST CODE HERE]", test_code)
    
    # Feed to LLM (Chase automatically saves the markdown file!)
    chase_worker.input.feed(current_prompt)
    response = chase_worker.output.get_output()
    
    print(f"  [SUCCESS] Audit complete.")

print("\n" + "="*60)
print(f"[DONE] All audits finished!")
print(f"Open the markdown files in '{env_setup.EXP_04_DIR.name}' to read the reports.")
print("="*60)