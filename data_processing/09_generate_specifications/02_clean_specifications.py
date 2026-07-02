import json
import env_setup

def main():
    print("="*60)
    print("STEP 1: Cleaning and Formatting Specifications")
    print("="*60)

    # 1. Define input and output files
    input_specs_file = env_setup.BASE_DIR / "experiments" / "project_specifications.json"
    output_specs_file = env_setup.BASE_DIR / "experiments" / "cleaned_project_specifications.json"

    if not input_specs_file.exists():
        print(f"[ERROR] Input file not found: {input_specs_file.name}")
        exit(1)

    # 2. Load the raw specifications
    with open(input_specs_file, "r", encoding="utf-8") as f:
        raw_specs = json.load(f)

    cleaned_specs = {}
    processed_count = 0

    for project_name, data in raw_specs.items():
        raw_text = data.get("specification", "")
        
        # 3. Get the import_name_gen from metadata
        meta_file = env_setup.METADATA_DIR / f"{project_name}.json"
        if not meta_file.exists():
            print(f"  [WARNING] Metadata missing for {project_name}. Skipping.")
            continue
            
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        import_name_gen = metadata.get("import_name_gen", "UNKNOWN")

        # 4. Process the text line by line
        lines = raw_text.split("\n")
        cut_index = -1

        for i, line in enumerate(lines):
            # Look strictly for a line starting with exactly "# "
            if line.startswith("# "):
                cut_index = i
                break

        if cut_index != -1:
            # Delete everything up to and including the cut_index
            cleaned_lines = lines[cut_index + 1:]
        else:
            # If no "# " was found, we just keep the whole text (fallback)
            print(f"  [WARNING] {project_name.ljust(15)} | No '# ' header found. Keeping original text.")
            cleaned_lines = lines

        # 5. Prepend the new standardized header
        new_header = f"# Project: `{import_name_gen}`\n"
        cleaned_lines.insert(0, new_header)

        # Rejoin the text
        final_text = "\n".join(cleaned_lines).strip()

        # Save to the new dictionary
        cleaned_specs[project_name] = {
            "specification": final_text
        }
        
        print(f"  [SUCCESS] {project_name.ljust(15)} | Cleaned and formatted.")
        processed_count += 1

    # 6. Save the new JSON file
    with open(output_specs_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_specs, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print(f"[DONE] Processed {processed_count} specifications.")
    print(f"Saved to: {output_specs_file.name}")
    print("="*60)

if __name__ == "__main__":
    main()