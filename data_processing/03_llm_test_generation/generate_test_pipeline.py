# %% [markdown]
# # Phase 1: Blueprint Generation Setup
# This cell sets up the environment and safely copies the API Contract 
# conversations into our new workspace so we can continue the chat.

# %%
import os
import shutil
from pathlib import Path

# 1. Define Paths
current_dir = Path.cwd().resolve() # Must be inside data_processing/llm_test_generation
data_processing_dir = current_dir.parent

# Source: The API Contracts we generated previously
source_dir = data_processing_dir / "llm_repo_check" / "experiments" / "02_api_contracts"

# Destination: Our new workspace
dest_dir = current_dir / "experiments" / "01_blueprint_generation"
dest_dir.mkdir(parents=True, exist_ok=True)

# 2. Copy the files safely
print(f"Copying API Contracts from: {source_dir.name} -> {dest_dir.name}")
copied_count = 0

for md_file in source_dir.glob("*.md"):
    dest_file = dest_dir / md_file.name
    # shutil.copy2 preserves metadata and overwrites safely if re-run
    shutil.copy2(md_file, dest_file)
    copied_count += 1

print(f"Success! Copied {copied_count} files.")
print("The conversation history is now staged and ready for the Blueprint Prompt.")



# %% [markdown]
# # Phase 1: Execute Blueprint Generation
# This cell runs the LLM to generate the flat, numbered list of 
# black-box guarantees based on the API Contracts.

# %%
import os
from pathlib import Path


from chase.facade import Chase

from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable



# 1. Configure Chase Environment
home_dir = Path.home()
current_dir = Path.cwd().resolve()

shared_config_path = home_dir / "chase_workspace" / "shared" / "common.yaml"
local_config_path = current_dir / "config.yaml"
os.environ["CHASE_CONFIG_PATH"] = f"{shared_config_path},{local_config_path}"

instructions_dir = current_dir / "prompts"
os.environ["CHASE_INSTRUCTIONS_DIR"] = str(instructions_dir)

print("Chase environment configured.")

# 2. Load the Prompt
prompt_file_path = instructions_dir / "blueprint_prompt.md"
try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        blueprint_prompt = file.read()
    print("Blueprint prompt loaded successfully.")
except FileNotFoundError:
    print(f"[ERROR] Could not find prompt at {prompt_file_path}")
    blueprint_prompt = None

# 3. Run the LLM on all staged files
if blueprint_prompt:
    dest_dir = current_dir / "experiments" / "01_blueprint_generation"
    md_files = list(dest_dir.glob("*.md"))
    
    print(f"Starting Blueprint Generation for {len(md_files)} projects...\n")
    
    for md_file in md_files:
        project_name = md_file.stem
        print(f"-> Generating blueprint for: {project_name}")
        
        # Initialize Chase. Because the file exists, it will append to it.
        chase_worker = Chase(profile="01_blueprint_generation", session_id=project_name)
        
        # Feed the prompt
        chase_worker.input.feed(blueprint_prompt)
        response = chase_worker.output.get_output()
        
        print(f"   [DONE] {project_name}")

    print("\nAll blueprints generated successfully!")





# %%
import os
import re
import shutil
from pathlib import Path

# 1. Setup Paths
current_dir = Path.cwd().resolve()
dir_01 = current_dir / "experiments" / "01_blueprint_generation"
dir_02 = current_dir / "experiments" / "02_detailed_spec_generation"

dir_02.mkdir(parents=True, exist_ok=True)

# Copy files from Phase 1 to Phase 2
print("Copying files from Phase 1 to Phase 2...")
for md_file in dir_01.glob("*.md"):
    if not (dir_02 / md_file.name).exists():
        shutil.copy2(md_file, dir_02 / md_file.name)

# 2. Load the Prompt
prompt_file_path = current_dir / "prompts" / "batch_expansion_prompt.md"
with open(prompt_file_path, "r", encoding="utf-8") as file:
    prompt_template = file.read()

# 3. Helper function to find the total number of tests
def get_total_tests(blueprint_text: str) -> int:
    """Finds the highest numbered item in the blueprint list."""
    max_num = 0
    # Matches lines starting with a number followed by a dot (e.g., "19. If a user...")
    pattern = re.compile(r"^(\d+)\.", re.MULTILINE)
    for match in pattern.finditer(blueprint_text):
        num = int(match.group(1))
        if num > max_num:
            max_num = num
    return max_num

# 4. Execute Batch Processing
BATCH_SIZE = 5

for md_file in dir_02.glob("*.md"):
    project_name = md_file.stem
    print(f"\nProcessing: {project_name}")
    
    # Initialize Chase
    chase_worker = Chase(profile="02_detailed_spec_generation", session_id=project_name)
    
    # The blueprint is the last message from the previous phase (index 5)
    # We extract the text to find out how many tests there are.
    if len(chase_worker.session.messages) < 6:
        print(f"  [SKIP] {project_name} does not have the required 6 messages.")
        continue
        
    blueprint_message = chase_worker.session.messages[5].content.to_text()
    total_tests = get_total_tests(blueprint_message)
    
    if total_tests == 0:
        print(f"  [SKIP] Could not find numbered tests for {project_name}.")
        continue
        
    print(f"  Found {total_tests} tests. Processing in batches of {BATCH_SIZE}...")
    
    # We will collect all the expanded outputs into a single string
    # so we can save a clean version of the final specs later.
    all_expanded_specs = []
    
    # Loop through the batches
    for start_idx in range(1, total_tests + 1, BATCH_SIZE):
        end_idx = min(start_idx + BATCH_SIZE - 1, total_tests)
        print(f"    -> Expanding tests {start_idx} to {end_idx}...")
        
        # CRITICAL: Truncate the session history back to the original 6 messages
        # This deletes messages[6] and messages[7] from previous batches
        chase_worker.session.messages = chase_worker.session.messages[:6]
        
        # Format the prompt for this specific batch
        current_prompt = prompt_template.replace("[START_INDEX]", str(start_idx)).replace("[END_INDEX]", str(end_idx))
        
        # Feed the prompt and get the response
        chase_worker.input.feed(current_prompt)
        response = chase_worker.output.get_output()
        
        # Store the response
        all_expanded_specs.append(response)
        
    # Optional: Save the combined expanded specs to a clean text file
    # This makes it much easier to parse into JSON in the next step, 
    # without having to dig through the Chase markdown archives.
    clean_output_dir = current_dir / "experiments" / "02_clean_expanded_specs"
    clean_output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(clean_output_dir / f"{project_name}_specs.md", "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_expanded_specs))
        
    print(f"  [DONE] {project_name} fully expanded and saved.")

print("\nAll projects have been successfully expanded!")


# %%
from pathlib import Path

# 1. Setup Paths
current_dir = Path.cwd().resolve()
dp = current_dir.parent # data_processing directory

# Map every single experiment folder across the whole project
folders = {
    "repo_01": dp / "llm_repo_check/experiments/01_repo_knowledge",
    "repo_02": dp / "llm_repo_check/experiments/02_api_contracts",
    "ana_03": dp / "llm_test_analysis/experiments/03_functional_test_analysis",
    "ana_04": dp / "llm_test_analysis/experiments/04_behavioral_extraction",
    "ana_04b": dp / "llm_test_analysis/experiments/04b_robustness_extraction",
    "ana_05": dp / "llm_test_analysis/experiments/05_functional_json_extraction",
    "ana_05b": dp / "llm_test_analysis/experiments/05b_robustness_json_extraction",
    "gen_01": dp / "llm_test_generation/experiments/01_blueprint_generation",
    "gen_02": dp / "llm_test_generation/experiments/02_detailed_spec_generation",
    "gen_03": dp / "llm_test_generation/experiments/03_json_conversion",
}

def count_messages(filepath: Path) -> str:
    if not filepath.exists():
        return "-"
    content = filepath.read_text(encoding="utf-8")
    count = content.count("### Silvestro :eyes:") + content.count("### Chase :seedling:")
    return str(count)

def find_repo_01_file(project: str, folder: Path) -> Path:
    # Handle the author prefix in the very first folder (e.g., Textualize_rich.md)
    matches = list(folder.glob(f"*_{project}.md"))
    return matches[0] if matches else folder / f"{project}.md"

# Get the canonical list of 30 projects from repo_02
all_projects = sorted([p.stem for p in folders["repo_02"].glob("*.md")])

# Print Header
header = f"{'Project'.ljust(12)} | " + " | ".join([k.ljust(8) for k in folders.keys()])
print(header)
print("-" * len(header))

# Print Data
for project in all_projects:
    row = [project.ljust(12)]
    
    for key, folder in folders.items():
        if key == "repo_01":
            file_path = find_repo_01_file(project, folder)
        else:
            file_path = folder / f"{project}.md"
            
        count = count_messages(file_path)
        row.append(count.ljust(8))
        
    print(" | ".join(row))


# %% [markdown]
# # TEMPORARY: Check Message Counts
# Run this to see exactly how many messages are in the history for each project.

# %%
from pathlib import Path

current_dir = Path.cwd().resolve()
dir_02 = current_dir / "experiments" / "01_blueprint_generation"

print("Current Message Counts:\n" + "-"*25)

for md_file in sorted(dir_02.glob("*.md")):
    project_name = md_file.stem
    
    # Load the session history
    chase_worker = Chase(profile="01_blueprint_generation", session_id=project_name)
    msg_count = len(chase_worker.session.messages)
    
    # Print nicely aligned
    print(f"{project_name.ljust(15)} : {msg_count} messages")


# %% [markdown]
# # Phase 2.5: Manual Fix for Skipped Projects
# This cell manually defines the test counts for projects where the regex failed
# (like rich and cachetools) and runs the batch expansion for them.

# %%
import os
from pathlib import Path

current_dir = Path.cwd().resolve()
dir_02 = current_dir / "experiments" / "02_detailed_spec_generation"

# Load the Phase 2 prompt
prompt_file_path = current_dir / "prompts" / "batch_expansion_prompt.md"
with open(prompt_file_path, "r", encoding="utf-8") as file:
    prompt_template = file.read()

# --- UPDATE THESE NUMBERS ---
# Look at the Phase 1 markdown files and enter the total number of tests here:
manual_counts = {
    "rich": 15,        
    "cachetools": 16   
}

BATCH_SIZE = 5

for project_name, total_tests in manual_counts.items():
    if total_tests == 0:
        print(f"[SKIP] Please update the manual count for {project_name} in the code.")
        continue
        
    print(f"\nProcessing Manual Fix: {project_name}")
    chase_worker = Chase(profile="02_detailed_spec_generation", session_id=project_name)
    
    # Check if it somehow already got processed
    if len(chase_worker.session.messages) >= 8:
        print(f"  [SKIP] {project_name} already has expanded messages.")
        continue
        
    print(f"  Found {total_tests} tests. Processing in batches of {BATCH_SIZE}...")
    all_expanded_specs = []
    
    for start_idx in range(1, total_tests + 1, BATCH_SIZE):
        end_idx = min(start_idx + BATCH_SIZE - 1, total_tests)
        print(f"    -> Expanding tests {start_idx} to {end_idx}...")
        
        # Truncate back to the base 6 messages
        chase_worker.session.messages = chase_worker.session.messages[:6]
        
        current_prompt = prompt_template.replace("[START_INDEX]", str(start_idx)).replace("[END_INDEX]", str(end_idx))
        chase_worker.input.feed(current_prompt)
        response = chase_worker.output.get_output()
        
        all_expanded_specs.append(response)
        
    print(f"  [DONE] {project_name} fully expanded and saved.")




# %% [markdown]
# # Phase 3: JSON Conversion via Context Manipulation
# This script copies the expanded specifications, calculates the exact number 
# of batches, and surgically manipulates the session history to convert 
# each batch into a clean JSON array.

# %%
import os
import json
import shutil
from pathlib import Path

from chase.components.pipelines.response_sanitization import json_fence_enforcer
from chase.components.pipelines.normalization import json_code_block_tagger
from chase.components.pipelines.post_response_normalization import json_escape_repair
from chase.components.pipelines.presentation import json_fence_stripper
import test_spec_validator

# 1. Setup Paths
current_dir = Path.cwd().resolve()
dir_02 = current_dir / "experiments" / "02_detailed_spec_generation"
dir_03 = current_dir / "experiments" / "03_json_conversion"

dir_03.mkdir(parents=True, exist_ok=True)

# Copy files from Phase 2 to Phase 3
print("Copying files from Phase 2 to Phase 3...")
for md_file in dir_02.glob("*.md"):
    if not (dir_03 / md_file.name).exists():
        shutil.copy2(md_file, dir_03 / md_file.name)

# 2. Load the Prompt
prompt_file_path = current_dir / "prompts" / "json_extraction_prompt.md"
with open(prompt_file_path, "r", encoding="utf-8") as file:
    prompt_template = file.read()

# 3. Initialize the Master JSON Dictionary
# This will hold the final, aggregated arrays for all projects
master_json_path = current_dir / "experiments" / "final_functional_tests.json"

if master_json_path.exists():
    with open(master_json_path, "r", encoding="utf-8") as f:
        master_json = json.load(f)
else:
    master_json = {}

# 4. Execute the Surgical JSON Conversion
for md_file in dir_03.glob("*.md"):
    project_name = md_file.stem
    print(f"\nProcessing: {project_name}")
    
    # Initialize Chase
    chase_worker = Chase(profile="03_json_conversion", session_id=project_name)
    
    # Save the full message history before we start manipulating it
    original_messages = chase_worker.session.messages[:]
    total_messages = len(original_messages)
    
    # Calculate the exact number of iterations (batches)
    if total_messages <= 8:
        print(f"  [SKIP] Not enough messages to process ({total_messages}).")
        continue
        
    num_iterations = (total_messages - 6) // 2
    print(f"  Found {num_iterations} batches to convert.")
    
    # Initialize the project in our master JSON if it doesn't exist
    if project_name not in master_json:
        master_json[project_name] = {
            "project_name": project_name,
            "functional_tests": []
        }
    
    # The base context is always the first 6 messages (indices 0 through 5)
    base_context = original_messages[:6]
    
    for i in range(num_iterations):
        print(f"    -> Converting batch {i + 1} of {num_iterations} to JSON...")
        
        # Calculate the indices for this specific batch
        # Iteration 0: indices 6 and 7
        # Iteration 1: indices 8 and 9
        batch_start = 6 + (i * 2)
        batch_end = batch_start + 2
        
        # Extract the 2 messages for this batch
        batch_context = original_messages[batch_start:batch_end]
        
        # Surgically stitch the session history together
        chase_worker.session.messages = base_context + batch_context
        
        # Feed the JSON extraction prompt
        chase_worker.input.feed(prompt_template)
        
        # Get the guaranteed pure JSON string
        response = chase_worker.output.get_output()
        
        # Parse and extend our master list
        parsed_json_array = json.loads(response)
        master_json[project_name]["functional_tests"].extend(parsed_json_array)
        
        # Save incrementally after every successful batch
        with open(master_json_path, "w", encoding="utf-8") as f:
            json.dump(master_json, f, indent=2, ensure_ascii=False)
            
    print(f"  [DONE] {project_name} fully converted. Total tests: {len(master_json[project_name]['functional_tests'])}")

print(f"\nAll projects successfully converted! Final JSON saved to: {master_json_path.name}")