import os
import re
import json
import time
import requests
import env_setup



GITHUB_REPOS = {
    "tabulate": "astanin/python-tabulate",
    "xmltodict": "martinblech/xmltodict",
    "click": "pallets/click",
    "pygments": "pygments/pygments",
    "cmd2": "python-cmd2/cmd2",
    "lifelines": "CamDavidsonPilon/lifelines",
    "dateutil": "dateutil/dateutil",
    "tablib": "jazzband/tablib",
    "petl": "petl-developers/petl",
    "dataset": "pudo/dataset",
    "pendulum": "sdispater/pendulum",
    "sqlmodel": "fastapi/sqlmodel",
    "requests": "psf/requests",
    "folium": "python-visualization/folium",
    "stegano": "cedricbonhomme/Stegano",
    "pyjwt": "jpadilla/pyjwt",
    "schedule": "dbader/schedule",
    "typer": "fastapi/typer",
    "tinydb": "msiemens/tinydb",
    "cachetools": "tkem/cachetools",
    "loguru": "Delgan/loguru",
    "rich": "Textualize/rich",
    "watchdog": "gorakhargosh/watchdog",
    "humanize": "python-humanize/humanize",
    "imageio": "imageio/imageio",
    "pypdf": "py-pdf/pypdf",
    "mutagen": "quodlibet/mutagen",
    "astral": "sffjunkie/astral",
    "slugify": "un33k/python-slugify"
}

# ==========================================
# 1. LOAD INFERRED VERSIONS
# ==========================================
if not env_setup.VERSIONS_FILE.exists():
    print(f"[ERROR] Could not find {env_setup.VERSIONS_FILE.name}. Run 01_infer_versions.py first.")
    exit(1)

with open(env_setup.VERSIONS_FILE, "r", encoding="utf-8") as f:
    inferred_versions = json.load(f)

# ==========================================
# 2. FETCH AND FILTER TAGS (WITH PAGINATION)
# ==========================================
print("="*60)
print("Fetching GitHub Tags based on Inferred Versions")
print("="*60)

headers = {"Accept": "application/vnd.github.v3+json"}
if "GITHUB_TOKEN" in os.environ:
    headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"
final_tags_data = {}

for project_name, owner_repo in GITHUB_REPOS.items():
    target_version = inferred_versions.get(project_name, {}).get("target_version", "")
    
    if not target_version or target_version == "UNKNOWN":
        print(f"[SKIP] {project_name.ljust(15)} | No valid target version found.")
        continue

    print(f"Fetching: {owner_repo.ljust(30)} | Target: v{target_version}")
    
    # --- ADD THIS REGEX ---
    # Matches optional 'v' or 'release-', then the exact version, then a dot, hyphen, or end of string
    pattern = re.compile(rf"^(v|release-)?{re.escape(target_version)}(\.|-|$)")
    
    filtered_tags = []
    page = 1
    
    # Pagination Loop
    while True:
        # Request 100 tags per page to minimize API calls
        url = f"https://api.github.com/repos/{owner_repo}/tags?per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"  [ERROR] API returned {response.status_code}: {response.text}")
            break
            
        tags = response.json()
        
        # If the page is empty, we've reached the end of the repository's tags
        if not tags:
            break
            
        # Filter tags on the current page
        for tag in tags:
            if pattern.match(tag["name"]):
                filtered_tags.append({
                    "name": tag["name"],
                    "zipball_url": tag["zipball_url"],
                    "commit_sha": tag["commit"]["sha"]
                })
                
                # Stop once we have 5 matches
                if len(filtered_tags) == 5:
                    break
        
        # If we found our 5 tags, break out of the pagination loop
        if len(filtered_tags) == 5:
            break
            
        # Otherwise, go to the next page
        page += 1
        time.sleep(0.2) # Small sleep between pages to respect rate limits

    # Save the results for this project
    final_tags_data[project_name] = filtered_tags
    
    if filtered_tags:
        print(f"  [SUCCESS] Found {len(filtered_tags)} matching tags (Searched {page} pages)")
    else:
        print(f"  [WARNING] Found 0 tags containing '{target_version}' after searching {page} pages")
        
    # Sleep briefly before moving to the next project
    time.sleep(0.5)

# ==========================================
# 3. SAVE OUTPUT
# ==========================================
with open(env_setup.TAGS_FILE, "w", encoding="utf-8") as f:
    json.dump(final_tags_data, f, indent=2, ensure_ascii=False)

print("\n" + "="*60)
print(f"[DONE] Saved filtered tags to: {env_setup.TAGS_FILE.name}")