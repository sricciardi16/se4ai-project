import json
import env_setup

def main():
    print("="*60)
    print("STEP 1: Injecting 'import_name_gen' into Metadata")
    print("="*60)

    # 1. Load the anonymized mapping we created in step 01
    mapping_file = env_setup.EXP_01_ANONYMIZATION_DIR / "anonymized_mapping.json"
    if not mapping_file.exists():
        print(f"[ERROR] Mapping file not found at {mapping_file.name}. Run step 01 first.")
        exit(1)

    with open(mapping_file, "r", encoding="utf-8") as f:
        anonymized_mapping = json.load(f)

    # 2. Update Metadata files
    metadata_files = sorted(list(env_setup.METADATA_DIR.glob("*.json")))
    print(f"Found {len(metadata_files)} metadata files to check.\n")

    updated_count = 0

    for meta_file in metadata_files:
        project_name = meta_file.stem
        
        # Check if we have an anonymized name for this project
        anonymized_name = anonymized_mapping.get(project_name)
        
        if not anonymized_name:
            print(f"  [SKIP] {project_name.ljust(15)} | No anonymized name found in mapping.")
            continue

        # Load existing metadata
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Inject the new field
        metadata["import_name_gen"] = anonymized_name

        # Save it back
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"  [UPDATED] {project_name.ljust(15)} | import_name_gen: {anonymized_name}")
        updated_count += 1

    print("\n" + "="*60)
    print(f"[DONE] Successfully updated {updated_count} metadata files.")
    print("="*60)

if __name__ == "__main__":
    main()