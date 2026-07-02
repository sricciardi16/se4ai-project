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
import version_validator


# ==========================================
# 1. SMART COPY FROM API CONTRACTS
# ==========================================
print("="*50)
print("STEP 1: Staging API Contracts for Version Inference")
print("="*50)

env_setup.EXP_01_DIR.mkdir(parents=True, exist_ok=True)

copied_count = 0
for md_file in env_setup.DIR_02_API_CONTRACTS.glob("*.md"):
    dest_file = env_setup.EXP_01_DIR / md_file.name
    if not dest_file.exists():
        shutil.copy2(md_file, dest_file)
        copied_count += 1

print(f"Copied {copied_count} new files to {env_setup.EXP_01_DIR.name}.")

# ==========================================
# 2. REGISTRY SETUP
# ==========================================
registry_path = env_setup.BASE_DIR / "experiments" / "inferred_versions.json"

def load_registry():
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_registry(registry_data):
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, indent=2, ensure_ascii=False)

versions_registry = load_registry()
print(f"Loaded {len(versions_registry)} existing projects from registry.")

# ==========================================
# 3. LOAD PROMPT
# ==========================================
prompt_file_path = env_setup.PROMPTS_DIR / "version_inference_prompt.md"
try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
except FileNotFoundError:
    print(f"Error: Could not find {prompt_file_path}")
    exit(1)

# ==========================================
# 4. EXECUTE VERSION INFERENCE
# ==========================================
print("\n" + "="*50)
print("STEP 2: Inferring Target Versions")
print("="*50)

remaining_files = list(env_setup.EXP_01_DIR.glob("*.md"))

for md_file in remaining_files:
    project_name = md_file.stem
    
    if project_name in versions_registry:
        print(f"  [SKIP] {project_name} already processed (Version: {versions_registry[project_name]['target_version']}).")
        continue
        
    print(f"  -> Inferring version for: {project_name}")
    
    # Initialize Chase
    chase_worker = Chase(profile="01_version_inference", session_id=project_name)
    
    # Feed the prompt
    chase_worker.input.feed(prompt_template)
    
    # The middleware guarantees this is valid JSON
    response = chase_worker.output.get_output()
    data = json.loads(response.strip())
    
    # Save to registry incrementally
    versions_registry[project_name] = {
        "project_name": project_name,
        "target_version": data.get("target_version", "UNKNOWN")
    }
    
    save_registry(versions_registry)
    print(f"     [SUCCESS] {project_name} -> v{versions_registry[project_name]['target_version']}")

# ==========================================
# 5. VERIFICATION & SUMMARY
# ==========================================
print("\n" + "="*50)
print("VERIFICATION: Checking Message Counts")
print("="*50)

successful_repos = []
problematic_repos = []

for md_file in remaining_files:
    project_name = md_file.stem
    
    # Initialize Chase just to read the session state
    check_worker = Chase(profile="01_version_inference", session_id=project_name)
    msg_count = len(check_worker.session.messages)
    
    # Expected: 2 (Repo Check) + 2 (API Contract) + 2 (Version Inference) = 6
    if msg_count == 6:
        successful_repos.append(project_name)
    else:
        problematic_repos.append((project_name, msg_count))

if problematic_repos:
    print(f"[WARNING] {len(problematic_repos)} repositories have incorrect message counts:")
    for repo, count in problematic_repos:
        print(f"  - {repo} (Messages: {count}, Expected: 6)")
else:
    print(f"[SUCCESS] All {len(successful_repos)} processed repositories have exactly 6 messages.")

print("\n" + "="*50)
print("SUMMARY: Inferred Versions")
print("="*50)

# Print a clean table of the results
print(f"{'Project Name'.ljust(20)} | {'Inferred Version'}")
print("-" * 40)

for project in sorted(versions_registry.keys()):
    version = versions_registry[project]["target_version"]
    print(f"{project.ljust(20)} | v{version}")

print(f"\n[INFO] Final JSON saved to: {registry_path.name}")