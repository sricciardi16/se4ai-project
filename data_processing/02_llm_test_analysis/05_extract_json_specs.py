import json
import shutil
import env_setup

from chase.facade import Chase
from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable

from chase.components.pipelines.response_sanitization import json_fence_enforcer
from chase.components.pipelines.normalization import json_code_block_tagger
from chase.components.pipelines.post_response_normalization import json_escape_repair
from chase.components.pipelines.presentation import json_fence_stripper
import test_spec_validator

# ==========================================
# 1. SMART COPY FROM 04 TO 05
# ==========================================
print("="*50)
print("STEP 1: Copying files to 05 and 05b")
print("="*50)

env_setup.EXP_05_DIR.mkdir(parents=True, exist_ok=True)
env_setup.EXP_05B_DIR.mkdir(parents=True, exist_ok=True)

for md_file in env_setup.EXP_04_DIR.glob("*.md"):
    dest = env_setup.EXP_05_DIR / md_file.name
    if not dest.exists():
        shutil.copy2(md_file, dest)

for md_file in env_setup.EXP_04B_DIR.glob("*.md"):
    dest = env_setup.EXP_05B_DIR / md_file.name
    if not dest.exists():
        shutil.copy2(md_file, dest)

print("Copy complete.")

# ==========================================
# 2. REGISTRY SETUP
# ==========================================
registry_path = env_setup.BASE_DIR / "experiments" / "master_registry.json"

def load_registry():
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_registry(registry_data):
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, indent=2, ensure_ascii=False)

def init_project(registry, project_name):
    if project_name not in registry:
        registry[project_name] = {
            "project_name": project_name,
            "functional_behaviors": [],
            "robustness_behaviors": [],
            "processed_05": False,
            "processed_05b": False
        }

master_registry = load_registry()
print(f"Loaded {len(master_registry)} existing projects from registry.")

# ==========================================
# 3. LOAD PROMPT
# ==========================================
prompt_file_path = env_setup.PROMPTS_DIR / "json_extraction_prompt.md"
try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
except FileNotFoundError:
    print(f"Error: Could not find {prompt_file_path}")
    exit(1)

# ==========================================
# 4. PROCESS FUNCTIONAL JSON (05)
# ==========================================
print("\n" + "="*50)
print("STEP 2: Extracting Functional JSON (05)")
print("="*50)

for md_file in env_setup.EXP_05_DIR.glob("*.md"):
    project_name = md_file.stem
    init_project(master_registry, project_name)
    
    if master_registry[project_name]["processed_05"]:
        print(f"  [SKIP] {project_name} already processed for 05.")
        continue
        
    print(f"  -> Extracting JSON for: {project_name}")
    chase_worker = Chase(profile="05_functional_json_extraction", session_id=project_name)
    chase_worker.input.feed(prompt_template)
    
    # The middleware guarantees this is valid JSON
    response = chase_worker.output.get_output()
    data = json.loads(response.strip())
    
    master_registry[project_name]["functional_behaviors"].extend(data.get("functional_behaviors", []))
    master_registry[project_name]["robustness_behaviors"].extend(data.get("robustness_behaviors", []))
        
    master_registry[project_name]["processed_05"] = True
    save_registry(master_registry)
    print(f"     [SUCCESS] Saved state for {project_name}")

# ==========================================
# 5. PROCESS ROBUSTNESS JSON (05b)
# ==========================================
print("\n" + "="*50)
print("STEP 3: Extracting Robustness JSON (05b)")
print("="*50)

for md_file in env_setup.EXP_05B_DIR.glob("*.md"):
    project_name = md_file.stem
    init_project(master_registry, project_name)
    
    if master_registry[project_name]["processed_05b"]:
        print(f"  [SKIP] {project_name} already processed for 05b.")
        continue
        
    print(f"  -> Extracting JSON for: {project_name}")
    chase_worker = Chase(profile="05b_robustness_json_extraction", session_id=project_name)
    chase_worker.input.feed(prompt_template)
    
    response = chase_worker.output.get_output()
    data = json.loads(response.strip())
    
    master_registry[project_name]["functional_behaviors"].extend(data.get("functional_behaviors", []))
    master_registry[project_name]["robustness_behaviors"].extend(data.get("robustness_behaviors", []))
        
    master_registry[project_name]["processed_05b"] = True
    save_registry(master_registry)
    print(f"     [SUCCESS] Saved state for {project_name}")

# ==========================================
# 6. EXPORT ARTIFACTS
# ==========================================
print("\n" + "="*50)
print("STEP 4: Generating Final JSON Artifacts")
print("="*50)

clean_registry_path = env_setup.BASE_DIR / "experiments" / "master_test_specs.json"
functional_plan_path = env_setup.BASE_DIR / "experiments" / "ral_bench_functional_test_plan.json"

# A. Clean Registry (master_test_specs.json)
clean_registry = {}
for project_name, project_data in master_registry.items():
    clean_registry[project_name] = {
        "project_name": project_data["project_name"],
        "functional_behaviors": project_data["functional_behaviors"],
        "robustness_behaviors": project_data["robustness_behaviors"]
    }

with open(clean_registry_path, "w", encoding="utf-8") as f:
    json.dump(clean_registry, f, indent=2, ensure_ascii=False)
print(f"Saved: {clean_registry_path.name}")

# B. Functional Plan (ral_bench_functional_test_plan.json)
functional_plan = {}
for project_name, project_data in clean_registry.items():
    clean_functional_tests = []
    for behavior in project_data.get("functional_behaviors", []):
        clean_test = {
            "test_name": behavior.get("new_test_name", "test_unknown"),
            "target_api": behavior.get("target_api", ""),
            "behavioral_specification": behavior.get("behavioral_specification", ""),
            "crucial_data": behavior.get("crucial_data", "")
        }
        clean_functional_tests.append(clean_test)
        
    functional_plan[project_name] = {
        "project_name": project_name,
        "functional_tests": clean_functional_tests
    }

with open(functional_plan_path, "w", encoding="utf-8") as f:
    json.dump(functional_plan, f, indent=2, ensure_ascii=False)
print(f"Saved: {functional_plan_path.name}")

# ==========================================
# 7. VERIFICATION
# ==========================================
print("\n" + "="*50)
print("VERIFICATION: Checking Messages and JSON Integrity")
print("="*50)

def verify_messages(directory, profile_name):
    problematic = []
    expected_projects = []
    for md_file in directory.glob("*.md"):
        project_name = md_file.stem
        expected_projects.append(project_name)
        check_worker = Chase(profile=profile_name, session_id=project_name)
        msg_count = len(check_worker.session.messages)
        if msg_count != 8:
            problematic.append((project_name, msg_count))
    return expected_projects, problematic

# 1. Check Messages
expected_05, prob_05 = verify_messages(env_setup.EXP_05_DIR, "05_functional_json_extraction")
expected_05b, prob_05b = verify_messages(env_setup.EXP_05B_DIR, "05b_robustness_json_extraction")

all_expected_projects = set(expected_05 + expected_05b)

print("--- Message Counts (Expected: 8) ---")
if prob_05 or prob_05b:
    if prob_05: print(f"[WARNING] 05 Functional issues: {prob_05}")
    if prob_05b: print(f"[WARNING] 05b Robustness issues: {prob_05b}")
else:
    print("[SUCCESS] All processed files in 05 and 05b have exactly 8 messages.")

# 2. Check JSON Files
print("\n--- JSON Integrity ---")
missing_in_json = False

for project in all_expected_projects:
    if project not in master_registry:
        print(f"[ERROR] {project} missing from master_registry.json")
        missing_in_json = True
    if project not in clean_registry:
        print(f"[ERROR] {project} missing from master_test_specs.json")
        missing_in_json = True
    if project not in functional_plan:
        print(f"[ERROR] {project} missing from ral_bench_functional_test_plan.json")
        missing_in_json = True

if not missing_in_json:
    print(f"[SUCCESS] All {len(all_expected_projects)} projects are present in all 3 JSON files.")