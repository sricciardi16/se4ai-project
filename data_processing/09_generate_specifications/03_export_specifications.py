import json
import env_setup

def main():
    print("="*60)
    print("STEP 1: Formatting and Exporting Specifications")
    print("="*60)

    # 1. Define paths
    cleaned_specs_file = env_setup.BASE_DIR / "experiments" / "cleaned_project_specifications.json"
    
    # Create the new specifications directory next to metadata
    # (Assuming env_setup.METADATA_DIR is PROJECT_ROOT / "data" / "metadata" or similar)
    data_dir = env_setup.PROJECT_ROOT / "data"
    specs_dir = data_dir / "specifications"
    specs_dir.mkdir(parents=True, exist_ok=True)

    if not cleaned_specs_file.exists():
        print(f"[ERROR] Input file not found: {cleaned_specs_file.name}")
        exit(1)

    # 2. Load the cleaned specifications
    with open(cleaned_specs_file, "r", encoding="utf-8") as f:
        cleaned_specs = json.load(f)

    exported_count = 0

    for project_id, data in cleaned_specs.items():
        spec_text = data.get("specification", "")
        
        # 3. Remove the leading "# " from the first line
        lines = spec_text.split("\n")
        if lines and lines[0].startswith("# Project:"):
            # Slice off the first 2 characters ("# ")
            lines[0] = lines[0][2:]
            
        final_text = "\n".join(lines)

        # 4. Define the output file path (e.g., data/specifications/tabulate.md)
        output_file = specs_dir / f"{project_id}.md"

        # 5. Write the specification to its own file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_text)
            
        print(f"  [SUCCESS] Exported: {output_file.relative_to(env_setup.PROJECT_ROOT)}")
        exported_count += 1

    print("\n" + "="*60)
    print(f"[DONE] Successfully exported {exported_count} specifications.")
    print(f"They are now located in: {specs_dir.relative_to(env_setup.PROJECT_ROOT)}/")
    print("="*60)

if __name__ == "__main__":
    main()