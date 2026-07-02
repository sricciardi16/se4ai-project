import shutil
import env_setup

from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable

# ==========================================
# 1. SMART COPY FROM API CONTRACTS TO 01
# ==========================================
print("="*50)
print("STEP 1: Staging API Contracts for Blueprint Generation")
print("="*50)

env_setup.EXP_01_DIR.mkdir(parents=True, exist_ok=True)

copied_count = 0
for md_file in env_setup.DIR_02_API_CONTRACTS.glob("*.md"):
    dest_file = env_setup.EXP_01_DIR / md_file.name
    
    # Only copy if it doesn't already exist
    if not dest_file.exists():
        shutil.copy2(md_file, dest_file)
        copied_count += 1

print(f"Copied {copied_count} new files to {env_setup.EXP_01_DIR.name}.")

# ==========================================
# 2. LOAD PROMPT
# ==========================================
prompt_file_path = env_setup.PROMPTS_DIR / "blueprint_prompt.md"

try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
    print("\nBlueprint prompt loaded successfully.")
except FileNotFoundError:
    print(f"\nError: Could not find the prompt file at {prompt_file_path}")
    exit(1)

# ==========================================
# 3. RUN LLM BLUEPRINT GENERATION
# ==========================================
print("\n" + "="*50)
print("STEP 2: Generating Blueprints (Public Guarantees)")
print("="*50)

remaining_files = list(env_setup.EXP_01_DIR.glob("*.md"))
print(f"Found {len(remaining_files)} projects to process.\n")

for md_file in remaining_files:
    project_name = md_file.stem
    print(f"Generating blueprint for: {project_name}...")
    
    # Initialize Chase
    chase_worker = Chase(profile="01_blueprint_generation", session_id=project_name)
    
    # Check if already processed (6 messages = 2 from Repo Check + 2 from API Contract + 2 from Blueprint)
    if len(chase_worker.session.messages) >= 6:
        print(f"  -> Skipping: Already processed (found {len(chase_worker.session.messages)} messages).")
        print("-" * 50)
        continue
        
    # Feed the prompt and get the output
    chase_worker.input.feed(prompt_template)
    response = chase_worker.output.get_output()
    
    print("-" * 50)

# ==========================================
# 4. VERIFICATION STEP
# ==========================================
print("\n" + "="*50)
print("VERIFICATION: Checking message counts for 01_blueprint_generation")
print("="*50)

successful_repos = []
problematic_repos = []

for md_file in remaining_files:
    project_name = md_file.stem
    
    check_worker = Chase(profile="01_blueprint_generation", session_id=project_name)
    msg_count = len(check_worker.session.messages)
    
    if msg_count == 6:
        successful_repos.append(project_name)
    else:
        problematic_repos.append((project_name, msg_count))

print(f"\n[SUCCESS] Repositories with exactly 6 messages ({len(successful_repos)}):")
for repo in successful_repos:
    print(f"  - {repo}")

if problematic_repos:
    print(f"\n[WARNING] Repositories with incorrect message counts ({len(problematic_repos)}):")
    for repo, count in problematic_repos:
        print(f"  - {repo} (Messages: {count})")
else:
    print("\n[INFO] All processed repositories have exactly 6 messages. Verification passed.")