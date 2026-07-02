import shutil
import env_setup

from chase.facade import Chase
from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable


# ==========================================
# 1. DATA STRUCTURES
# ==========================================
NAME_MAPPING = {
    "astanin_python-tabulate.md": "tabulate.md",
    "martinblech_xmltodict.md": "xmltodict.md",
    "pallets_click.md": "click.md",
    "pygments_pygments.md": "pygments.md",
    "python-cmd2_cmd2.md": "cmd2.md",
    "CamDavidsonPilon_lifelines.md": "lifelines.md",
    "dateutil_dateutil.md": "dateutil.md",
    "jazzband_tablib.md": "tablib.md",
    "petl-developers_petl.md": "petl.md",
    "pudo_dataset.md": "dataset.md",
    "sdispater_pendulum.md": "pendulum.md", # Just in case
    "fastapi_sqlmodel.md": "sqlmodel.md",
    "psf_requests.md": "requests.md",
    "python-visualization_folium.md": "folium.md",
    "cedricbonhomme_Stegano.md": "stegano.md",
    "jpadilla_pyjwt.md": "pyjwt.md",
    "dbader_schedule.md": "schedule.md",
    "fastapi_typer.md": "typer.md",
    "msiemens_tinydb.md": "tinydb.md",
    "tkem_cachetools.md": "cachetools.md",
    "Delgan_loguru.md": "loguru.md",
    "Textualize_rich.md": "rich.md",
    "gorakhargosh_watchdog.md": "watchdog.md",
    "python-humanize_humanize.md": "humanize.md",
    "imageio_imageio.md": "imageio.md",
    "py-pdf_pypdf.md": "pypdf.md",
    "quodlibet_mutagen.md": "mutagen.md",
    "sffjunkie_astral.md": "astral.md",
    "un33k_python-slugify.md": "slugify.md",
    
    # The 8 we are discarding
    "fail2ban_fail2ban.md": "fail2ban.md",
    "sqlmapproject_sqlmap.md": "sqlmap.md",
    "nvbn_thefuck.md": "thefuck.md",
    "nicolargo_glances.md": "glances.md",
    "mailpile_Mailpile.md": "mailpile.md",
    "mitmproxy_mitmproxy.md": "mitmproxy.md",
    "celery_celery.md": "celery.md",
    "mkaz_termgraph.md": "termgraph.md",
    "Python-Markdown_markdown.md": "markdown.md"

}

DISCARD_LIST = [
    "fail2ban.md", "sqlmap.md", "thefuck.md", "glances.md", 
    "mailpile.md", "mitmproxy.md", "celery.md", "termgraph.md",
    "markdown.md"
]

# ==========================================
# 2. SMART COPY & RENAME
# ==========================================
print("="*50)
print("STEP 1: Smart Copy & Rename")
print("="*50)

# Ensure the destination directory exists
env_setup.EXP_02_DIR.mkdir(parents=True, exist_ok=True)

copied_count = 0
for old_file in env_setup.EXP_01_DIR.glob("*.md"):
    if old_file.name in NAME_MAPPING:
        clean_name = NAME_MAPPING[old_file.name]
        
        # Skip if it's in the discard list
        if clean_name in DISCARD_LIST:
            continue
            
        new_file = env_setup.EXP_02_DIR / clean_name
        
        # Only copy if it doesn't already exist in 02 (protects existing progress)
        if not new_file.exists():
            shutil.copy2(old_file, new_file)
            copied_count += 1

print(f"Copied {copied_count} new files to {env_setup.EXP_02_DIR.name}.")

# ==========================================
# 3. LOAD PROMPT
# ==========================================
api_prompt_path = env_setup.PROMPTS_DIR / "api_contract_prompt.md"

try:
    with open(api_prompt_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
    print("\nAPI Contract prompt loaded successfully.")
except FileNotFoundError:
    print(f"\nError: Could not find the prompt file at {api_prompt_path}")
    exit(1)

# ==========================================
# 4. PROCESS API CONTRACTS
# ==========================================
print("\n" + "="*50)
print("STEP 2: Generating API Contracts")
print("="*50)

remaining_files = list(env_setup.EXP_02_DIR.glob("*.md"))
print(f"Found {len(remaining_files)} projects to process.\n")

for md_file in remaining_files:
    project_name = md_file.stem  # e.g., "slugify"
    print(f"Processing API Contract for: {project_name}...")
    
    # Initialize Chase
    chase_worker = Chase(profile="02_api_contracts", session_id=project_name)
    
    # Check if this repository has already been processed (4 messages = 2 from step 1 + 2 from step 2)
    if len(chase_worker.session.messages) >= 4:
        print(f"  -> Skipping: Already processed (found {len(chase_worker.session.messages)} messages).")
        print("-" * 50)
        continue
    
    # Feed the prompt and get the output
    chase_worker.input.feed(prompt_template)
    response = chase_worker.output.get_output()
    
    print("-" * 50)

# ==========================================
# 5. VERIFICATION STEP
# ==========================================
print("\n" + "="*50)
print("VERIFICATION: Checking message counts for all API Contracts")
print("="*50)

successful_repos = []
problematic_repos = []

for md_file in remaining_files:
    project_name = md_file.stem
    
    # Initialize Chase just to read the session state
    check_worker = Chase(profile="02_api_contracts", session_id=project_name)
    msg_count = len(check_worker.session.messages)
    
    if msg_count == 4:
        successful_repos.append(project_name)
    else:
        problematic_repos.append((project_name, msg_count))

# Print the ones that are OK
print(f"\n[SUCCESS] Repositories with exactly 4 messages ({len(successful_repos)}):")
for repo in successful_repos:
    print(f"  - {repo}")

# Print the ones that have issues
if problematic_repos:
    print(f"\n[WARNING] Repositories with incorrect message counts ({len(problematic_repos)}):")
    for repo, count in problematic_repos:
        print(f"  - {repo} (Messages: {count})")
else:
    print("\n[INFO] All repositories have exactly 4 messages. Verification passed.")