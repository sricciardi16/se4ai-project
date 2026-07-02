import json
import env_setup

# ==========================================
# 1. HELPER FUNCTION
# ==========================================
def get_import_name(project_name: str) -> str:
    """Determines the actual Python import name for a given project."""
    if project_name == "pyjwt":
        return "jwt"
    return project_name.replace("-", "_")

# ==========================================
# 2. EXPORT LOGIC
# ==========================================
print("="*60)
print(f"Exporting Metadata to: {env_setup.METADATA_DIR}")
print("="*60)

if not env_setup.METADATA_FILE.exists():
    print(f"[ERROR] Could not find {env_setup.METADATA_FILE.name}. Run previous steps first.")
    exit(1)

with open(env_setup.METADATA_FILE, "r", encoding="utf-8") as f:
    master_metadata = json.load(f)

exported_count = 0

for project_name, data in master_metadata.items():
    # 1. Inject the new import_name field
    data["import_name"] = get_import_name(project_name)
    
    # 2. Define the individual output file path
    output_file = env_setup.METADATA_DIR / f"{project_name}.json"
    
    # 3. Save the individual JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    exported_count += 1
    print(f"  [SUCCESS] Created {project_name}.json (Import: {data['import_name']})")

print("\n" + "="*60)
print(f"[DONE] Exported {exported_count} metadata files to the root data/ directory.")
print("="*60)