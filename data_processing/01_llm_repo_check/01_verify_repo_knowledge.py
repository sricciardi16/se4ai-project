import env_setup

from chase.facade import Chase
from chase.components.archives import markdown
from chase.components.providers import gemini
from chase.components.io import variable


# ==========================================
# 1. DEFINE REPOSITORIES
# ==========================================
repos = [
    "astanin/python-tabulate", "martinblech/xmltodict", "mkaz/termgraph",
    "pallets/click", "pygments/pygments", "python-cmd2/cmd2",
    "CamDavidsonPilon/lifelines", "dateutil/dateutil", "jazzband/tablib",
    "petl-developers/petl", "pudo/dataset", "python-pendulum/pendulum",
    "Python-Markdown/markdown", "fastapi/sqlmodel", "psf/requests",
    "python-visualization/folium", "cedricbonhomme/Stegano", "fail2ban/fail2ban",
    "jpadilla/pyjwt", "mitmproxy/mitmproxy", "sqlmapproject/sqlmap",
    "celery/celery", "dbader/schedule", "fastapi/typer",
    "msiemens/tinydb", "nvbn/thefuck", "tkem/cachetools",
    "Delgan/loguru", "Textualize/rich", "gorakhargosh/watchdog",
    "nicolargo/glances", "python-humanize/humanize", "imageio/imageio",
    "mailpile/Mailpile", "py-pdf/pypdf", "quodlibet/mutagen",
    "sffjunkie/astral", "un33k/python-slugify"
]
print(f"Loaded {len(repos)} repositories to check.")

# ==========================================
# 2. LOAD PROMPT TEMPLATE
# ==========================================
prompt_file_path = env_setup.PROMPTS_DIR / "repo_check_prompt.md"

try:
    with open(prompt_file_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()
    print("Prompt template loaded successfully.\n")
except FileNotFoundError:
    print(f"Error: Could not find the prompt file at {prompt_file_path}")
    exit(1)

# ==========================================
# 3. PROCESS MAIN REPOSITORIES
# ==========================================
for repo in repos:
    print(f"Checking repository: {repo}...")
    
    current_prompt = prompt_template.replace("[INSERT REPO NAME HERE]", repo)
    safe_session_id = repo.replace("/", "_")
    
    # Initialize the Chase worker
    chase_worker = Chase(profile="01_repo_knowledge", session_id=safe_session_id)
    
    # Check if this repository has already been processed
    if len(chase_worker.session.messages) >= 2:
        print(f"  -> Skipping: Already processed (found {len(chase_worker.session.messages)} messages).")
        print("-" * 50)
        continue
    
    # Feed the prompt and get the output
    chase_worker.input.feed(current_prompt)
    response = chase_worker.output.get_output()
    
    print("-" * 50)

# ==========================================
# 4. PROCESS CORRECTED REPOSITORY
# ==========================================
corrected_repo = "sdispater/pendulum"
print(f"Checking corrected repository: {corrected_repo}...")

current_prompt = prompt_template.replace("[INSERT REPO NAME HERE]", corrected_repo)
safe_session_id = corrected_repo.replace("/", "_")

chase_worker = Chase(profile="01_repo_knowledge", session_id=safe_session_id)

if len(chase_worker.session.messages) >= 2:
    print(f"  -> Skipping: Already processed (found {len(chase_worker.session.messages)} messages).")
else:
    chase_worker.input.feed(current_prompt)
    response = chase_worker.output.get_output()
    print(f"Finished checking {corrected_repo}")

print("-" * 50)
print("All repository checks completed.")


# ==========================================
# 5. VERIFICATION STEP
# ==========================================
print("\n" + "="*50)
print("VERIFICATION: Checking message counts for all repositories")
print("="*50)

# Combine the main list and the corrected repo for the final check
all_repos_to_check = repos + [corrected_repo]

successful_repos = []
problematic_repos = []

for repo in all_repos_to_check:
    safe_session_id = repo.replace("/", "_")
    # Initialize Chase just to read the session state
    check_worker = Chase(profile="01_repo_knowledge", session_id=safe_session_id)
    msg_count = len(check_worker.session.messages)
    
    if msg_count == 2:
        successful_repos.append(repo)
    else:
        problematic_repos.append((repo, msg_count))

# Print the ones that are OK
print(f"\n[SUCCESS] Repositories with exactly 2 messages ({len(successful_repos)}):")
for repo in successful_repos:
    print(f"  - {repo}")

# Print the ones that have issues
if problematic_repos:
    print(f"\n[WARNING] Repositories with incorrect message counts ({len(problematic_repos)}):")
    for repo, count in problematic_repos:
        print(f"  - {repo} (Messages: {count})")
else:
    print("\n[INFO] All repositories have exactly 2 messages. Verification passed.")