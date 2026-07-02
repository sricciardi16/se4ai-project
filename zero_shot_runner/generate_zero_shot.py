import json
import re
import argparse
import yaml
from pathlib import Path
import env_setup

from chase.facade import Chase
from chase.components.archives import markdown
from chase.components.feedback import console
from chase.components.io import variable
from chase.components.providers import gemini
from chase.components.providers import gemini
from chase.components.providers import vertex_openai
from chase.components.providers import utils
from chase.components.pipelines.response_sanitization import think_tag_remover


# ==========================================
# MODEL TO PROVIDER MAPPING
# ==========================================
# Add new models here as you expand your experiments
MODEL_MAPPING = {
    "gemini": "provider.gemini.vertex.3-1-pro-preview",
    "gpt": "provider.groq.openai-gpt-oss-120b",
    "glm": "provider.vertex_openai.glm-5",
    "qwen": "provider.vertex_openai.qwen3-coder-480b-a35b-instruct",
    "deepseek": "provider.vertex_openai.deepseek-r1-0528"
}

def update_chase_config(model_name: str):
    """Dynamically updates the config.yaml with the correct provider."""
    provider_string = MODEL_MAPPING.get(model_name)
    if not provider_string:
        print(f"[ERROR] Model '{model_name}' is not in the MODEL_MAPPING.")
        print(f"Available models: {list(MODEL_MAPPING.keys())}")
        exit(1)

    config_path = env_setup.LOCAL_CONFIG_PATH
    
    # Read the existing YAML
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Update the provider
    try:
        config_data["profiles"]["zero_shot_generation"]["provider"] = provider_string
    except KeyError:
        print("[ERROR] Malformed config.yaml. Could not find profiles -> zero_shot_generation -> provider")
        exit(1)

    # Write it back
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
    print(f"  [CONFIG] Updated Chase provider to: {provider_string}")


def main():
    # --- ARGUMENT PARSING ---
    parser = argparse.ArgumentParser(description="Run Zero-Shot Code Generation.")
    parser.add_argument("--model", required=True, help="The model to use (e.g., gemini-3.1-pro-preview)")
    parser.add_argument("--project-id", required=False, help="Optional: Run only for a specific project (e.g., tabulate)")
    args = parser.parse_args()

    model_name = args.model
    target_project = args.project_id

    print("="*60)
    print(f"STEP 1: Initializing Zero-Shot Generation")
    print(f"Model: {model_name}")
    if target_project:
        print(f"Target Project: {target_project}")
    print("="*60)

    # --- CONFIGURATION & PATHS ---
    update_chase_config(model_name)

    # Dynamically set the output directory based on the model
    generated_code_dir = env_setup.ZERO_SHOT_DIR / model_name / "generated_code"
    generated_code_dir.mkdir(parents=True, exist_ok=True)
    print(f"  [OUTPUT] {generated_code_dir.relative_to(env_setup.PROJECT_ROOT)}")

    # --- FIND SPECIFICATIONS ---
    if target_project:
        spec_files = [env_setup.SPECS_DIR / f"{target_project}.md"]
        if not spec_files[0].exists():
            print(f"[ERROR] Specification not found for project: {target_project}")
            exit(1)
    else:
        spec_files = sorted(list(env_setup.SPECS_DIR.glob("*.md")))
        
    print(f"\nFound {len(spec_files)} specifications to process.\n")

    # --- GENERATION LOOP ---
    for spec_file in spec_files:
        project_id = spec_file.stem
        project_out_dir = generated_code_dir / project_id

        # Resumability: Skip if we already generated code for this project
        if project_out_dir.exists() and any(project_out_dir.iterdir()):
            print(f"[SKIP] {project_id.ljust(15)} | Code already generated.")
            continue

        print(f"Generating: {project_id}...")

        # Read the raw Specification
        with open(spec_file, "r", encoding="utf-8") as f:
            specification_text = f.read()

        # Initialize Chase
        chase_worker = Chase(profile="zero_shot_generation", session_id=f"{model_name}_{project_id}")

        # Feed the raw specification directly
        chase_worker.input.feed(specification_text)
        response = chase_worker.output.get_output()

        # --- PARSE THE XML OUTPUT ---
        file_matches = re.findall(r'<file\s+path=["\'](.*?)["\']\s*>(.*?)</file>', response, re.DOTALL | re.IGNORECASE)

        if not file_matches:
            print(f"  [ERROR] No valid <file> tags found in LLM response for {project_id}.")
            continue

        project_out_dir.mkdir(parents=True, exist_ok=True)
        files_created = 0

        for file_path_str, file_content in file_matches:
            # Sanitize the path to prevent directory traversal attacks
            safe_path = Path(file_path_str.strip().lstrip('/\\'))
            
            if ".." in safe_path.parts:
                print(f"  [WARNING] Skipping unsafe path: {safe_path}")
                continue

            final_file_path = project_out_dir / safe_path
            final_file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(final_file_path, "w", encoding="utf-8") as f:
                f.write(file_content.strip() + "\n")
            
            files_created += 1

        print(f"  [SUCCESS] {project_id.ljust(15)} | Created {files_created} files.")

    print("\n" + "="*60)
    print("[DONE] Zero-Shot Generation Complete.")
    print("="*60)

if __name__ == "__main__":
    main()
