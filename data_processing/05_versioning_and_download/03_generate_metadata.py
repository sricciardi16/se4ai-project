import json
import env_setup

# ==========================================
# 1. REPOSITORY MAPPING
# ==========================================
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
# 2. LOAD INPUT DATA
# ==========================================
if not env_setup.VERSIONS_FILE.exists() or not env_setup.TAGS_FILE.exists():
    print("[ERROR] Missing input files. Ensure 01_infer_versions.py and 02_fetch_tags.py have been run.")
    exit(1)

with open(env_setup.VERSIONS_FILE, "r", encoding="utf-8") as f:
    inferred_versions = json.load(f)

with open(env_setup.TAGS_FILE, "r", encoding="utf-8") as f:
    github_tags = json.load(f)

# Output file path
METADATA_FILE = env_setup.BASE_DIR / "experiments" / "final_metadata.json"

# ==========================================
# 3. GENERATE METADATA
# ==========================================
print("="*60)
print("Generating Final Repository Metadata")
print("="*60)

final_metadata = {}
missing_tags_count = 0

for project_name, github_repo in GITHUB_REPOS.items():
    # 1. Get the inferred version
    inferred_version = inferred_versions.get(project_name, {}).get("target_version", "UNKNOWN")
    
    # 2. Get the FIRST tag from the GitHub results
    project_tags = github_tags.get(project_name, [])
    
    if project_tags:
        first_tag = project_tags[0]
        exact_tag = first_tag["name"]
        commit_sha = first_tag["commit_sha"]
        zipball_url = first_tag["zipball_url"]
    else:
        # Handle the edge case where no tags were found
        exact_tag = None
        commit_sha = None
        zipball_url = None
        missing_tags_count += 1
        print(f"[WARNING] No GitHub tags found for {project_name}")

    # 3. Build the clean metadata object
    final_metadata[project_name] = {
        "github_repo": github_repo,
        "inferred_version": inferred_version,
        "exact_tag": exact_tag,
        "commit_sha": commit_sha,
        "zipball_url": zipball_url
    }

# ==========================================
# 4. SAVE OUTPUT & PRINT SUMMARY
# ==========================================
with open(METADATA_FILE, "w", encoding="utf-8") as f:
    json.dump(final_metadata, f, indent=2, ensure_ascii=False)

print("\n" + "="*60)
print(f"{'Project'.ljust(15)} | {'Repo'.ljust(25)} | {'Tag'.ljust(12)}")
print("-" * 60)

for project, data in final_metadata.items():
    tag_display = data['exact_tag'] if data['exact_tag'] else "MISSING"
    print(f"{project.ljust(15)} | {data['github_repo'].ljust(25)} | {tag_display.ljust(12)}")

print("\n" + "="*60)
if missing_tags_count == 0:
    print(f"[SUCCESS] Metadata generated for all {len(final_metadata)} projects.")
else:
    print(f"[WARNING] Metadata generated, but {missing_tags_count} projects are missing tags.")
    
print(f"[INFO] Saved to: {METADATA_FILE.name}")