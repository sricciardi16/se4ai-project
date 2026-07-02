import os
from pathlib import Path

# ==========================================
# 1. PATH DEFINITIONS
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()           # .../data_processing/05_versioning_and_download
DATA_PROCESSING_DIR = BASE_DIR.parent                # .../data_processing
PROJECT_ROOT = DATA_PROCESSING_DIR.parent            # .../my_se4ai_proj
HOME_DIR = Path.home()

# Chase Configuration Paths
SHARED_CONFIG_PATH = HOME_DIR / "chase_workspace" / "shared" / "common.yaml"
LOCAL_CONFIG_PATH = BASE_DIR / "config.yaml"
PROMPTS_DIR = BASE_DIR / "prompts"

# Source Data (The API Contracts from Phase 2)
DIR_02_API_CONTRACTS = DATA_PROCESSING_DIR / "01_llm_repo_check" / "experiments" / "02_api_contracts"

# Local Experiment Directories
EXP_01_DIR = BASE_DIR / "experiments" / "01_version_inference"

# ==========================================
# 2. ENVIRONMENT CONFIGURATION
# ==========================================
os.environ["CHASE_CONFIG_PATH"] = f"{SHARED_CONFIG_PATH},{LOCAL_CONFIG_PATH}"
os.environ["CHASE_INSTRUCTIONS_DIR"] = str(PROMPTS_DIR)

# ==========================================
# 3. FILE & FOLDER DEFINITIONS
# ==========================================
VERSIONS_FILE = BASE_DIR / "experiments" / "inferred_versions.json"
TAGS_FILE = BASE_DIR / "experiments" / "github_tags.json"
METADATA_FILE = BASE_DIR / "experiments" / "final_metadata.json"

REPOSITORIES_DIR = PROJECT_ROOT / "repositories"

# New Formal Data Directory
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"

# Ensure the new directory exists automatically
METADATA_DIR.mkdir(parents=True, exist_ok=True)

print(f"[Setup] Environment configured automatically for versioning_and_download.")