import shutil
import env_setup


from chase.facade import Chase
from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable

# ==========================================
# 1. SMART COPY FROM 02 TO 03
# ==========================================
print("="*50)
print("STEP 1: Copying API Contracts to 03")
print("="*50)

env_setup.EXP_03_DIR.mkdir(parents=True, exist_ok=True)

copied_count = 0
for md_file in env_setup.DIR_02_API_CONTRACTS.glob("*.md"):
    dest_file = env_setup.EXP_03_DIR / md_file.name
    
    # Only copy if it doesn't already exist (protects existing progress)
    if not dest_file.exists():
        shutil.copy2(md_file, dest_file)
        copied_count += 1

print(f"Copied {copied_count} new files to {env_setup.EXP_03_DIR.name}.")

# ==========================================
# 2. LOAD PROMPT
# ==========================================
prompt_file_path = env_setup.PROMPTS_DIR / "functional_test_analysis_prompt.md"

try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
    print("\nFunctional Test Analysis prompt loaded successfully.")
except FileNotFoundError:
    print(f"\nError: Could not find the prompt file at {prompt_file_path}")
    exit(1)

# ==========================================
# 3. RUN LLM ANALYSIS
# ==========================================
print("\n" + "="*50)
print("STEP 2: Analyzing Functional Tests")
print("="*50)

remaining_files = list(env_setup.EXP_03_DIR.glob("*.md"))
print(f"Found {len(remaining_files)} projects to process.\n")

for md_file in remaining_files:
    project_name = md_file.stem
    test_file_path = env_setup.RAL_BENCH_TESTS_DIR / project_name / "functional_test.py"
    
    if not test_file_path.exists():
        print(f"[SKIP] {project_name}: No functional_test.py found in ral_bench.")
        continue
        
    print(f"Analyzing functional tests for: {project_name}...")
    
    # Initialize Chase
    chase_worker = Chase(profile="03_functional_test_analysis", session_id=project_name)
    
    # Check if already processed (6 messages = 2 from 01 + 2 from 02 + 2 from 03)
    if len(chase_worker.session.messages) >= 6:
        print(f"  -> Skipping: Already processed (found {len(chase_worker.session.messages)} messages).")
        print("-" * 50)
        continue
        
    # Read the original test code
    with open(test_file_path, "r", encoding="utf-8") as f:
        test_code = f.read()
        
    # Inject the code into the prompt
    current_prompt = prompt_template.replace("[INSERT TEST CODE HERE]", test_code)
    
    # Feed the prompt and get the output
    chase_worker.input.feed(current_prompt)
    response = chase_worker.output.get_output()
    
    print("-" * 50)


# ==========================================
# 4. VERIFICATION STEP
# ==========================================
print("\n" + "="*50)
print("VERIFICATION: Checking message counts for 03_functional_test_analysis")
print("="*50)

successful_repos = []
problematic_repos = []
skipped_repos = []

for md_file in remaining_files:
    project_name = md_file.stem
    test_file_path = env_setup.RAL_BENCH_TESTS_DIR / project_name / "functional_test.py"
    
    # If there is no test file, it was skipped intentionally
    if not test_file_path.exists():
        skipped_repos.append(project_name)
        continue
    
    # Initialize Chase just to read the session state
    check_worker = Chase(profile="03_functional_test_analysis", session_id=project_name)
    msg_count = len(check_worker.session.messages)
    
    if msg_count == 6:
        successful_repos.append(project_name)
    else:
        problematic_repos.append((project_name, msg_count))

# Print the ones that are OK
print(f"\n[SUCCESS] Repositories with exactly 6 messages ({len(successful_repos)}):")
for repo in successful_repos:
    print(f"  - {repo}")

# Print the ones that were skipped
if skipped_repos:
    print(f"\n[INFO] Repositories skipped (No functional_test.py) ({len(skipped_repos)}):")
    for repo in skipped_repos:
        print(f"  - {repo}")

# Print the ones that have issues
if problematic_repos:
    print(f"\n[WARNING] Repositories with incorrect message counts ({len(problematic_repos)}):")
    for repo, count in problematic_repos:
        print(f"  - {repo} (Messages: {count})")
else:
    print("\n[INFO] All processed repositories have exactly 6 messages. Verification passed.")