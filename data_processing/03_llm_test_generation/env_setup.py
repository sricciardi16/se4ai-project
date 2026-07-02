import os
from pathlib import Path

# ==========================================
# 1. PATH DEFINITIONS
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()           # .../data_processing/03_llm_test_generation
DATA_PROCESSING_DIR = BASE_DIR.parent                # .../data_processing
HOME_DIR = Path.home()

# Chase Configuration Paths
SHARED_CONFIG_PATH = HOME_DIR / "chase_workspace" / "shared" / "common.yaml"
LOCAL_CONFIG_PATH = BASE_DIR / "config.yaml"
PROMPTS_DIR = BASE_DIR / "prompts"

# Source Data (The API Contracts from the very first phase)
DIR_02_API_CONTRACTS = DATA_PROCESSING_DIR / "01_llm_repo_check" / "experiments" / "02_api_contracts"

# Local Experiment Directories
EXP_01_DIR = BASE_DIR / "experiments" / "01_blueprint_generation"
EXP_02_DIR = BASE_DIR / "experiments" / "02_detailed_spec_generation"
EXP_03_DIR = BASE_DIR / "experiments" / "03_json_conversion"

# ==========================================
# 2. ENVIRONMENT CONFIGURATION
# ==========================================
os.environ["CHASE_CONFIG_PATH"] = f"{SHARED_CONFIG_PATH},{LOCAL_CONFIG_PATH}"
os.environ["CHASE_INSTRUCTIONS_DIR"] = str(PROMPTS_DIR)

print(f"[Setup] Environment configured automatically for llm_test_generation.")