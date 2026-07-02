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
# 1. SMART COPY FROM 02 TO 03
# ==========================================
print("="*50)
print("STEP 1: Staging Files for JSON Conversion")
print("="*50)

env_setup.EXP_03_DIR.mkdir(parents=True, exist_ok=True)

copied_count = 0
for md_file in env_setup.EXP_02_DIR.glob("*.md"):
    dest_file = env_setup.EXP_03_DIR / md_file.name
    if not dest_file.exists():
        shutil.copy2(md_file, dest_file)
        copied_count += 1

print(f"Copied {copied_count} new files to {env_setup.EXP_03_DIR.name}.")

# ==========================================
# 2. LOAD PROMPT & JSON STATE
# ==========================================
prompt_file_path = env_setup.PROMPTS_DIR / "json_extraction_prompt.md"
try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
except FileNotFoundError:
    print(f"Error: Could not find {prompt_file_path}")
    exit(1)

master_json_path = env_setup.BASE_DIR / "experiments" / "final_functional_tests.json"

if master_json_path.exists():
    with open(master_json_path, "r", encoding="utf-8") as f:
        master_json = json.load(f)
else:
    master_json = {}

# ==========================================
# 3. EXECUTE SURGICAL JSON CONVERSION
# ==========================================
print("\n" + "="*50)
print("STEP 2: Surgical Context Stitching & JSON Extraction")
print("="*50)

for md_file in env_setup.EXP_02_DIR.glob("*.md"):
    project_name = md_file.stem
    print(f"\nProcessing: {project_name}")
    
    # Initialize the project in our master JSON if it doesn't exist
    if project_name not in master_json:
        master_json[project_name] = {
            "project_name": project_name,
            "functional_tests": [],
            "processed_batches": 0  # Tracks exactly how many batches are done
        }
    
    # CRITICAL FIX: We read the pristine history from the 02 profile
    # This guarantees we never lose the original expanded text, even if 03 gets overwritten.
    reader_worker = Chase(profile="02_detailed_spec_generation", session_id=project_name)
    pristine_messages = reader_worker.session.messages[:]
    total_messages = len(pristine_messages)
    
    if total_messages <= 8:
        print(f"  [SKIP] Not enough messages to process ({total_messages}).")
        continue
        
    total_batches = (total_messages - 6) // 2
    processed_batches = master_json[project_name]["processed_batches"]
    
    if processed_batches >= total_batches:
        print(f"  [SKIP] Already fully converted ({total_batches}/{total_batches} batches).")
        continue
        
    print(f"  Found {total_batches} total batches. Resuming from batch {processed_batches + 1}...")
    
    # The base context is always the first 6 messages (indices 0 through 5)
    base_context = pristine_messages[:6]
    
    # Initialize the writer worker for 03
    writer_worker = Chase(profile="03_json_conversion", session_id=project_name)
    
    for i in range(processed_batches, total_batches):
        print(f"    -> Converting batch {i + 1} of {total_batches} to JSON...")
        
        # Calculate the indices for this specific batch
        batch_start = 6 + (i * 2)
        batch_end = batch_start + 2
        
        # Extract the 2 messages for this batch
        batch_context = pristine_messages[batch_start:batch_end]
        
        # Surgically stitch the session history together
        writer_worker.session.messages = base_context + batch_context
        
        # Feed the JSON extraction prompt
        writer_worker.input.feed(prompt_template)
        
        # Get the guaranteed pure JSON string (thanks to the middleware)
        response = writer_worker.output.get_output()
        
        # Parse and extend our master list
        parsed_json_array = json.loads(response)
        master_json[project_name]["functional_tests"].extend(parsed_json_array)
        
        # Increment state and save incrementally
        master_json[project_name]["processed_batches"] += 1
        
        with open(master_json_path, "w", encoding="utf-8") as f:
            json.dump(master_json, f, indent=2, ensure_ascii=False)
            
    print(f"  [DONE] {project_name} fully converted. Total tests: {len(master_json[project_name]['functional_tests'])}")

# ==========================================
# 4. CLEANUP & VERIFICATION
# ==========================================
print("\n" + "="*50)
print("VERIFICATION: Final JSON Integrity Check")
print("="*50)

# Remove the 'processed_batches' tracker to make the final JSON perfectly clean
clean_json = {}
total_tests_generated = 0
incomplete_projects = []

for project, data in master_json.items():
    clean_json[project] = {
        "project_name": data["project_name"],
        "functional_tests": data["functional_tests"]
    }
    
    test_count = len(data["functional_tests"])
    total_tests_generated += test_count
    
    # Check if the project finished all its batches
    reader = Chase(profile="02_detailed_spec_generation", session_id=project)
    expected_batches = (len(reader.session.messages) - 6) // 2
    
    if data["processed_batches"] != expected_batches:
        incomplete_projects.append((project, data["processed_batches"], expected_batches))

# Save the final, clean JSON
with open(master_json_path, "w", encoding="utf-8") as f:
    json.dump(clean_json, f, indent=2, ensure_ascii=False)

if incomplete_projects:
    print(f"\n[WARNING] {len(incomplete_projects)} projects did not finish all batches:")
    for proj, done, expected in incomplete_projects:
        print(f"  - {proj}: {done}/{expected} batches completed.")
else:
    print(f"\n[SUCCESS] All projects successfully converted!")
    print(f"[INFO] Total functional tests generated across all projects: {total_tests_generated}")
    print(f"[INFO] Final JSON saved to: {master_json_path.name}")