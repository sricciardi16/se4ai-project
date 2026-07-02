import shutil
import env_setup

from chase.facade import Chase
from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable

# ==========================================
# 1. SMART COPY FROM 02 TO 04 & 04b
# ==========================================
print("="*50)
print("STEP 1: Copying API Contracts to 04 and 04b")
print("="*50)

env_setup.EXP_04_DIR.mkdir(parents=True, exist_ok=True)
env_setup.EXP_04B_DIR.mkdir(parents=True, exist_ok=True)

copied_04 = 0
copied_04b = 0

for md_file in env_setup.DIR_02_API_CONTRACTS.glob("*.md"):
    # Copy to 04 (Functional)
    dest_04 = env_setup.EXP_04_DIR / md_file.name
    if not dest_04.exists():
        shutil.copy2(md_file, dest_04)
        copied_04 += 1
        
    # Copy to 04b (Robustness)
    dest_04b = env_setup.EXP_04B_DIR / md_file.name
    if not dest_04b.exists():
        shutil.copy2(md_file, dest_04b)
        copied_04b += 1

print(f"Copied {copied_04} new files to {env_setup.EXP_04_DIR.name}.")
print(f"Copied {copied_04b} new files to {env_setup.EXP_04B_DIR.name}.")

# ==========================================
# 2. LOAD PROMPT
# ==========================================
prompt_file_path = env_setup.PROMPTS_DIR / "behavioral_extraction_prompt.md"

try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
    print("\nBehavioral Extraction prompt loaded successfully.")
except FileNotFoundError:
    print(f"\nError: Could not find the prompt file at {prompt_file_path}")
    exit(1)

# ==========================================
# 3. PROCESS FUNCTIONAL TESTS (04)
# ==========================================
print("\n" + "="*50)
print("STEP 2: Extracting Functional Behaviors (04)")
print("="*50)

for md_file in env_setup.EXP_04_DIR.glob("*.md"):
    project_name = md_file.stem
    test_file_path = env_setup.RAL_BENCH_TESTS_DIR / project_name / "functional_test.py"
    
    if not test_file_path.exists():
        print(f"[SKIP] {project_name}: No functional_test.py found.")
        continue
        
    print(f"Extracting functional behaviors for: {project_name}...")
    
    chase_worker = Chase(profile="04_behavioral_extraction", session_id=project_name)
    
    # Check if already processed (6 messages = 2 from 01 + 2 from 02 + 2 from 04)
    if len(chase_worker.session.messages) >= 6:
        print(f"  -> Skipping: Already processed (found {len(chase_worker.session.messages)} messages).")
        print("-" * 50)
        continue
        
    with open(test_file_path, "r", encoding="utf-8") as f:
        test_code = f.read()
        
    current_prompt = prompt_template.replace("[INSERT TEST CODE HERE]", test_code)
    chase_worker.input.feed(current_prompt)
    response = chase_worker.output.get_output()
    print("-" * 50)

# ==========================================
# 4. PROCESS ROBUSTNESS TESTS (04b)
# ==========================================
print("\n" + "="*50)
print("STEP 3: Extracting Robustness Behaviors (04b)")
print("="*50)

for md_file in env_setup.EXP_04B_DIR.glob("*.md"):
    project_name = md_file.stem
    test_file_path = env_setup.RAL_BENCH_TESTS_DIR / project_name / "robustness_test.py"
    
    if not test_file_path.exists():
        print(f"[SKIP] {project_name}: No robustness_test.py found.")
        continue
        
    print(f"Extracting robustness behaviors for: {project_name}...")
    
    chase_worker = Chase(profile="04b_robustness_extraction", session_id=project_name)
    
    if len(chase_worker.session.messages) >= 6:
        print(f"  -> Skipping: Already processed (found {len(chase_worker.session.messages)} messages).")
        print("-" * 50)
        continue
        
    with open(test_file_path, "r", encoding="utf-8") as f:
        test_code = f.read()
        
    current_prompt = prompt_template.replace("[INSERT TEST CODE HERE]", test_code)
    chase_worker.input.feed(current_prompt)
    response = chase_worker.output.get_output()
    print("-" * 50)

# ==========================================
# 5. VERIFICATION STEP
# ==========================================
def verify_phase(directory, profile_name, test_filename):
    successful = []
    problematic = []
    skipped = []
    
    for md_file in directory.glob("*.md"):
        project_name = md_file.stem
        test_file_path = env_setup.RAL_BENCH_TESTS_DIR / project_name / test_filename
        
        if not test_file_path.exists():
            skipped.append(project_name)
            continue
            
        check_worker = Chase(profile=profile_name, session_id=project_name)
        msg_count = len(check_worker.session.messages)
        
        if msg_count == 6:
            successful.append(project_name)
        else:
            problematic.append((project_name, msg_count))
            
    return successful, skipped, problematic

print("\n" + "="*50)
print("VERIFICATION: Checking message counts for 04 and 04b")
print("="*50)

# Verify 04
succ_04, skip_04, prob_04 = verify_phase(env_setup.EXP_04_DIR, "04_behavioral_extraction", "functional_test.py")
print(f"\n--- Functional (04) ---")
print(f"[SUCCESS] {len(succ_04)} repos have exactly 6 messages.")
if skip_04: print(f"[INFO] {len(skip_04)} repos skipped (No functional_test.py).")
if prob_04:
    print(f"[WARNING] {len(prob_04)} repos have incorrect message counts:")
    for repo, count in prob_04: print(f"  - {repo} (Messages: {count})")

# Verify 04b
succ_04b, skip_04b, prob_04b = verify_phase(env_setup.EXP_04B_DIR, "04b_robustness_extraction", "robustness_test.py")
print(f"\n--- Robustness (04b) ---")
print(f"[SUCCESS] {len(succ_04b)} repos have exactly 6 messages.")
if skip_04b: print(f"[INFO] {len(skip_04b)} repos skipped (No robustness_test.py).")
if prob_04b:
    print(f"[WARNING] {len(prob_04b)} repos have incorrect message counts:")
    for repo, count in prob_04b: print(f"  - {repo} (Messages: {count})")

if not prob_04 and not prob_04b:
    print("\n[INFO] All processed repositories have exactly 6 messages. Verification passed.")