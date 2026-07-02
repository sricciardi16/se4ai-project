import os
from pathlib import Path
import env_setup

# ==========================================
# 1. SETUP
# ==========================================
env_setup.MERGED_TESTS_DIR.mkdir(parents=True, exist_ok=True)

print("="*60)
print("Merging Generated Tests and Extracting Imports")
print("="*60)

processed_projects = 0

# ==========================================
# 2. PARSING LOGIC
# ==========================================
# Loop through every project folder (e.g., 'tabulate', 'slugify')
for project_dir in env_setup.GENERATED_CODE_DIR.iterdir():
    if not project_dir.is_dir():
        continue
        
    project_name = project_dir.name
    print(f"Processing: {project_name}")
    
    all_imports = []
    all_test_bodies = []
    
    # Sort files numerically (1.py, 2.py, 3.py...) so they merge in order
    py_files = sorted(project_dir.glob("*.py"), key=lambda x: int(x.stem))
    
    for py_file in py_files:
        with open(py_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        imports_for_this_file = []
        test_body_lines = []
        
        is_parsing_imports = True
        in_multiline_import = False
        
        for line in lines:
            stripped = line.strip()
            
            if is_parsing_imports:
                # 1. Skip empty lines but keep searching
                if not stripped:
                    continue
                    
                # 2. Handle the multi-line exceptions (watchdog/5.py, pyjwt/5.py)
                if in_multiline_import:
                    imports_for_this_file.append(line.rstrip())
                    if ")" in stripped:
                        in_multiline_import = False
                    continue
                    
                # 3. Check if it starts with import or from
                if stripped.startswith("import ") or stripped.startswith("from "):
                    imports_for_this_file.append(line.rstrip())
                    # If it opens a parenthesis but doesn't close it, we are in a multi-line import
                    if "(" in stripped and ")" not in stripped:
                        in_multiline_import = True
                    continue
                    
                # 4. If it's not empty, not an import, and not multi-line, STOP searching.
                is_parsing_imports = False
                test_body_lines.append(line.rstrip())
            else:
                # We are past the imports, everything else is the test body
                test_body_lines.append(line.rstrip())
                
        # Add to our project-level lists
        all_imports.extend(imports_for_this_file)
        
        # Join the test body lines and strip leading/trailing whitespace
        clean_body = "\n".join(test_body_lines).strip()
        if clean_body:
            all_test_bodies.append(clean_body)

    # ==========================================
    # 3. DEDUPLICATION & SAVING
    # ==========================================
    # Deduplicate imports while preserving the order they were found
    unique_imports = list(dict.fromkeys(all_imports))
    
    # Define output file paths
    imports_file = env_setup.MERGED_TESTS_DIR / f"{project_name}_imports.py"
    tests_file = env_setup.MERGED_TESTS_DIR / f"{project_name}_tests.py"
    
    # Write the Imports file
    with open(imports_file, "w", encoding="utf-8") as f:
        f.write("\n".join(unique_imports) + "\n")
        
    # Write the Tests file (separated by double newlines)
    with open(tests_file, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_test_bodies) + "\n")
        
    processed_projects += 1

print("\n" + "="*60)
print(f"[SUCCESS] Processed {processed_projects} projects.")
print(f"Merged files saved to: {env_setup.MERGED_TESTS_DIR.name}/")
print("="*60)