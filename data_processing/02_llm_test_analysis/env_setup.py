import os
from pathlib import Path

# ==========================================
# 1. PATH DEFINITIONS
# ==========================================
# Base directories
BASE_DIR = Path(__file__).parent.resolve()           # .../data_processing/02_llm_test_analysis
DATA_PROCESSING_DIR = BASE_DIR.parent                # .../data_processing
PROJECT_ROOT = DATA_PROCESSING_DIR.parent            # .../my_se4ai_proj
HOME_DIR = Path.home()

# Chase Configuration Paths
SHARED_CONFIG_PATH = HOME_DIR / "chase_workspace" / "shared" / "common.yaml"
LOCAL_CONFIG_PATH = BASE_DIR / "config.yaml"
PROMPTS_DIR = BASE_DIR / "prompts"

# External Data Sources
DIR_02_API_CONTRACTS = DATA_PROCESSING_DIR / "01_llm_repo_check" / "experiments" / "02_api_contracts"
RAL_BENCH_TESTS_DIR = PROJECT_ROOT / "ral_bench" / "tests"

# Local Experiment Directories
EXP_03_DIR = BASE_DIR / "experiments" / "03_functional_test_analysis"
EXP_04_DIR = BASE_DIR / "experiments" / "04_behavioral_extraction"
EXP_04B_DIR = BASE_DIR / "experiments" / "04b_robustness_extraction"
EXP_05_DIR = BASE_DIR / "experiments" / "05_functional_json_extraction"
EXP_05B_DIR = BASE_DIR / "experiments" / "05b_robustness_json_extraction"

# ==========================================
# 2. ENVIRONMENT CONFIGURATION
# ==========================================
# This runs automatically as soon as this file is imported
os.environ["CHASE_CONFIG_PATH"] = f"{SHARED_CONFIG_PATH},{LOCAL_CONFIG_PATH}"
os.environ["CHASE_INSTRUCTIONS_DIR"] = str(PROMPTS_DIR)

print(f"[Setup] Environment configured automatically for llm_test_analysis.")