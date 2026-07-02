import argparse
import json
import shutil
import yaml
from pathlib import Path
import sys
import os
import multiprocessing

# ==========================================
# 1. PATH RESOLUTION
# ==========================================
# This script lives inside my_se4ai_proj/code_factory/
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent

HOME_DIR = Path.home()

SHARED_CONFIG_PATH = HOME_DIR / "chase_workspace" / "shared" / "common.yaml"
LOCAL_CONFIG_PATH = BASE_DIR / "config.yaml"
PROMPTS_DIR = BASE_DIR / "prompts"

os.environ["CHASE_CONFIG_PATH"] = f"{SHARED_CONFIG_PATH},{LOCAL_CONFIG_PATH}"
os.environ["CHASE_INSTRUCTIONS_DIR"] = str(PROMPTS_DIR)


# Inputs
SPECS_DIR = PROJECT_ROOT / "data" / "specifications"

# Outputs
EVALUATIONS_DIR = PROJECT_ROOT / "evaluations" / "agentic"
ARCHIVE_DIR = BASE_DIR / "archived_experiments"

# Factory Internal Paths
WORKSPACE_DIR = BASE_DIR / "workspace"
EXPERIMENTS_DIR = BASE_DIR / "experiments"
STORY_FILE = BASE_DIR / "project_story.md"
CONFIG_FILE = BASE_DIR / "config.yaml"

# ==========================================
# 2. FACTORY IMPORTS
# ==========================================
# Adjust these imports based on exactly how your files are named in code_factory
from factory.orchestrator import build_project
# Assuming you saved the story script as story_builder.py
from generate_story import build_story 

# ==========================================
# 3. MODEL MAPPING
# ==========================================
MODEL_MAPPING = {
    "gemini": "provider.gemini.vertexse4ai.3-1-pro-preview",
    "gpt": "provider.groq.openai-gpt-oss-120b",
    "glm": "provider.vertex_openai.glm-5",
    "qwen": "HYBRID"
}

def update_factory_config(model_name: str):
    """Updates all agent profiles EXCEPT json_converter."""
    provider_string = MODEL_MAPPING.get(model_name)
    if not provider_string:
        print(f"[ERROR] Model '{model_name}' is not in the MODEL_MAPPING.")
        sys.exit(1)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    updated_count = 0
    for profile_name, profile_data in config_data.get("profiles", {}).items():
        # CRITICAL: Do not touch the json_converter!
        if profile_name == "json_converter":
            continue
            
        if "provider" in profile_data:
            # --- SPECIAL ISOLATED CASE: DEEPSEEK + QWEN ---
            if model_name == "deepseek":
                if profile_name == "coder":
                    profile_data["provider"] = "provider.vertex_openai.qwen3-coder-480b-a35b-instruct"     
                else:
                    profile_data["provider"] = "provider.vertex_openai.qwen3-235b-a22b-instruct-2507" 
            
            # --- STANDARD CASE ---
            else:
                profile_data["provider"] = MODEL_MAPPING[model_name]

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
    print(f"  [CONFIG] Updated {updated_count} agent profiles to: {provider_string}")
    print(f"  [CONFIG] Skipped 'json_converter' (kept original provider).")

def clean_slate():
    """Wipes the factory floor clean before starting a new project."""
    if WORKSPACE_DIR.exists():
        shutil.rmtree(WORKSPACE_DIR)
    if EXPERIMENTS_DIR.exists():
        shutil.rmtree(EXPERIMENTS_DIR)
    if STORY_FILE.exists():
        STORY_FILE.unlink()

def main():

    multiprocessing.set_start_method('spawn', force=True)

    parser = argparse.ArgumentParser(description="Run the Multi-Agent Code Factory.")
    parser.add_argument("--model", required=True, help="The model to use (e.g., gemini-3.1-pro-preview)")
    parser.add_argument("--project-id", required=False, help="Optional: Run only for a specific project")
    
    args = parser.parse_args()

    model_name = args.model
    target_project = args.project_id

    print("="*60)
    print(f"STEP 1: Initializing Agentic Factory")
    print(f"Model: {model_name}")
    print("="*60)

    # 1. Update Configuration
    update_factory_config(model_name)

    # 2. Define Output Directories
    model_eval_dir = EVALUATIONS_DIR / model_name / "generated_code"
    model_eval_dir.mkdir(parents=True, exist_ok=True)
    
    model_archive_dir = ARCHIVE_DIR / model_name
    model_archive_dir.mkdir(parents=True, exist_ok=True)

    # 3. Find Specifications
    if target_project:
        spec_files = [SPECS_DIR / f"{target_project}.md"]
        if not spec_files[0].exists():
            print(f"[ERROR] Specification not found: {spec_files[0]}")
            sys.exit(1)
    else:
        spec_files = sorted(list(SPECS_DIR.glob("*.md")))
        
    print(f"\nFound {len(spec_files)} specifications to process.\n")

    # 4. The Conveyor Belt Loop
    for spec_file in spec_files:
        project_id = spec_file.stem
        final_project_dir = model_eval_dir / project_id

        # Resumability
        if final_project_dir.exists():
            print(f"[SKIP] {project_id.ljust(15)} | Already generated in evaluations.")
            continue

        print("\n" + "█"*60)
        print(f"🏭 STARTING FACTORY FOR: {project_id}")
        print("█"*60)

        # A. Clean the factory floor
        clean_slate()

        # B. Read Specification
        with open(spec_file, "r", encoding="utf-8") as f:
            specification_text = f.read()

        # C. Run the Factory (Even if it fails, we proceed to extraction)
        # C. Run the Factory in an ISOLATED PROCESS
        # The OS will violently close all open files and clear RAM when this process ends.
        factory_process = multiprocessing.Process(
            target=build_project, 
            args=(specification_text,), 
            kwargs={"start_sprint": 1} # Use 1 if you hardcoded it
        )
        
        factory_process.start()
        factory_process.join() # Pauses the main script until the factory finishes

        if factory_process.exitcode != 0:
            print(f"  [WARNING] Factory process crashed or was killed (Exit code: {factory_process.exitcode})")

        # D. Generate the Story
        print(f"\n[EXTRACTION] Generating project story...")
        build_story()

        # E. Move Story into Workspace
        if STORY_FILE.exists():
            shutil.move(str(STORY_FILE), str(WORKSPACE_DIR / "project_story.md"))
        else:
            print(f"  [WARNING] project_story.md was not generated.")

        # F. Move Workspace to Evaluations (Renaming it to project_id)
        if WORKSPACE_DIR.exists():
            shutil.move(str(WORKSPACE_DIR), str(final_project_dir))
            print(f"  [SUCCESS] Code extracted to: {final_project_dir.relative_to(PROJECT_ROOT)}")
        else:
            print(f"  [ERROR] Workspace was not created. Nothing to extract.")

        # G. Archive the Raw Experiments
        if EXPERIMENTS_DIR.exists():
            project_archive_dir = model_archive_dir / f"{project_id}_experiments"
            # If an old archive exists for some reason, remove it first
            if project_archive_dir.exists():
                shutil.rmtree(project_archive_dir)
            shutil.move(str(EXPERIMENTS_DIR), str(project_archive_dir))
            print(f"  [SUCCESS] Logs archived to: {project_archive_dir.relative_to(BASE_DIR)}")

        # H. Final Cleanup
        clean_slate()

    print("\n" + "="*60)
    print("[DONE] Agentic Generation Complete.")
    print("="*60)

if __name__ == "__main__":
    main()
