import os
import json
import zipfile
import requests
import env_setup

# ==========================================
# 1. SETUP & LOAD METADATA
# ==========================================
env_setup.REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)

if not env_setup.METADATA_FILE.exists():
    print(f"[ERROR] Could not find {env_setup.METADATA_FILE.name}. Run 03_generate_metadata.py first.")
    exit(1)

with open(env_setup.METADATA_FILE, "r", encoding="utf-8") as f:
    metadata = json.load(f)

# ==========================================
# 2. DOWNLOAD AND EXTRACT LOGIC
# ==========================================
print("="*60)
print(f"Downloading Repositories to: {env_setup.REPOSITORIES_DIR}")
print("="*60)

headers = {}
if "GITHUB_TOKEN" in os.environ:
    headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"

success_count = 0
skip_count = 0
error_count = 0

for project_name, data in metadata.items():
    zip_url = data.get("zipball_url")
    final_repo_path = env_setup.REPOSITORIES_DIR / project_name
    
    # 1. Check if we already downloaded it
    if final_repo_path.exists():
        print(f"[SKIP] {project_name.ljust(15)} | Already exists in repositories/")
        skip_count += 1
        continue
        
    # 2. Check if we have a URL
    if not zip_url:
        print(f"[ERROR] {project_name.ljust(15)} | No zipball_url found in metadata.")
        error_count += 1
        continue
        
    print(f"Downloading: {project_name.ljust(15)} | {data['exact_tag']}")
    
    # 3. Download the zip file
    temp_zip_path = env_setup.REPOSITORIES_DIR / f"{project_name}_temp.zip"
    
    try:
        response = requests.get(zip_url, headers=headers, stream=True)
        if response.status_code != 200:
            print(f"  [ERROR] Download failed with status {response.status_code}")
            error_count += 1
            continue
            
        with open(temp_zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        # 4. Extract the zip file
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            # GitHub zips always have a single root folder (e.g., owner-repo-sha/)
            top_level_dir = zip_ref.namelist()[0].split('/')[0]
            zip_ref.extractall(env_setup.REPOSITORIES_DIR)
            
        extracted_folder_path = env_setup.REPOSITORIES_DIR / top_level_dir
        
        # 5. Rename the strange GitHub folder to the clean project name
        if extracted_folder_path.exists():
            extracted_folder_path.rename(final_repo_path)
            print(f"  [SUCCESS] Extracted and renamed to '{project_name}'")
            success_count += 1
        else:
            print(f"  [ERROR] Could not find extracted folder {top_level_dir}")
            error_count += 1
            
    except Exception as e:
        print(f"  [ERROR] Exception occurred: {e}")
        error_count += 1
        
    finally:
        # 6. Clean up the temporary zip file
        if temp_zip_path.exists():
            temp_zip_path.unlink()

# ==========================================
# 3. SUMMARY
# ==========================================
print("\n" + "="*60)
print("DOWNLOAD SUMMARY")
print("="*60)
print(f"Successfully downloaded: {success_count}")
print(f"Skipped (already exist): {skip_count}")
print(f"Errors                 : {error_count}")
print(f"Total projects         : {len(metadata)}")
print("="*60)