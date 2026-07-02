import re
import math
import shutil
import env_setup

from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable

# ==========================================
# 1. SMART COPY FROM 01 TO 02
# ==========================================
print("="*50)
print("STEP 1: Staging Blueprints for Expansion")
print("="*50)

env_setup.EXP_02_DIR.mkdir(parents=True, exist_ok=True)

copied_count = 0
for md_file in env_setup.EXP_01_DIR.glob("*.md"):
    dest_file = env_setup.EXP_02_DIR / md_file.name
    if not dest_file.exists():
        shutil.copy2(md_file, dest_file)
        copied_count += 1

print(f"Copied {copied_count} new files to {env_setup.EXP_02_DIR.name}.")

# ==========================================
# 2. LOAD PROMPT & HELPER
# ==========================================
prompt_file_path = env_setup.PROMPTS_DIR / "batch_expansion_prompt.md"
try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
except FileNotFoundError:
    print(f"Error: Could not find {prompt_file_path}")
    exit(1)

def get_total_tests(blueprint_text: str) -> int:
    """Finds the highest numbered item in the blueprint list."""
    max_num = 0
    pattern = re.compile(r"^(\d+)\.", re.MULTILINE)
    for match in pattern.finditer(blueprint_text):
        num = int(match.group(1))
        if num > max_num:
            max_num = num
    return max_num

BATCH_SIZE = 5

# ==========================================
# 3. EXECUTE BATCH EXPANSION
# ==========================================
print("\n" + "="*50)
print("STEP 2: Expanding Specs in Batches")
print("="*50)

remaining_files = list(env_setup.EXP_02_DIR.glob("*.md"))

for md_file in remaining_files:
    project_name = md_file.stem
    print(f"\nProcessing: {project_name}")
    
    chase_worker = Chase(profile="02_detailed_spec_generation", session_id=project_name)
    
    # Ensure we have the base 6 messages (up to the blueprint)
    if len(chase_worker.session.messages) < 6:
        print(f"  [SKIP] {project_name} does not have the required 6 base messages.")
        continue
        
    # Extract the blueprint text (message index 5)
    blueprint_message = chase_worker.session.messages[5].content.to_text()
    total_tests = get_total_tests(blueprint_message)
    
    if total_tests == 0:
        print(f"  [SKIP] Could not find numbered tests for {project_name}.")
        continue
        
    # Calculate expected batches and messages
    total_batches = math.ceil(total_tests / BATCH_SIZE)
    expected_total_messages = 6 + (total_batches * 2)
    
    # Check if already fully processed
    if len(chase_worker.session.messages) >= expected_total_messages:
        print(f"  [SKIP] Already fully expanded. Found {len(chase_worker.session.messages)} messages (Expected {expected_total_messages}).")
        continue
        
    print(f"  Found {total_tests} tests. Processing in {total_batches} batches of {BATCH_SIZE}...")
    
    # Calculate how many batches are already done (in case of a previous crash)
    completed_batches = (len(chase_worker.session.messages) - 6) // 2
    
    for i in range(completed_batches, total_batches):
        start_idx = (i * BATCH_SIZE) + 1
        end_idx = min(start_idx + BATCH_SIZE - 1, total_tests)
        print(f"    -> Expanding tests {start_idx} to {end_idx} (Batch {i+1}/{total_batches})...")
        
        # CRITICAL: Truncate the session history back to the original 6 messages
        # This keeps the LLM's context window clean for this specific batch
        chase_worker.session.messages = chase_worker.session.messages[:6]
        
        current_prompt = prompt_template.replace("[START_INDEX]", str(start_idx)).replace("[END_INDEX]", str(end_idx))
        
        chase_worker.input.feed(current_prompt)
        response = chase_worker.output.get_output()
        
    print(f"  [DONE] {project_name} fully expanded.")

# ==========================================
# 4. VERIFICATION
# ==========================================
print("\n" + "="*50)
print("VERIFICATION: Checking Message Counts")
print("="*50)

successful = []
problematic = []

for md_file in remaining_files:
    project_name = md_file.stem
    check_worker = Chase(profile="02_detailed_spec_generation", session_id=project_name)
    
    if len(check_worker.session.messages) < 6:
        problematic.append((project_name, len(check_worker.session.messages), "Missing base messages"))
        continue
        
    blueprint_message = check_worker.session.messages[5].content.to_text()
    total_tests = get_total_tests(blueprint_message)
    
    if total_tests == 0:
        problematic.append((project_name, len(check_worker.session.messages), "Regex found 0 tests"))
        continue
        
    expected_msgs = 6 + (math.ceil(total_tests / BATCH_SIZE) * 2)
    actual_msgs = len(check_worker.session.messages)
    
    if actual_msgs == expected_msgs:
        successful.append(project_name)
    else:
        problematic.append((project_name, actual_msgs, f"Expected {expected_msgs}"))

print(f"\n[SUCCESS] {len(successful)} repositories are fully expanded.")
if problematic:
    print(f"\n[WARNING] {len(problematic)} repositories have issues:")
    for repo, count, reason in problematic:
        print(f"  - {repo} | Messages: {count} | {reason}")