import os
from pathlib import Path

# ==========================================
# 1. PATH DEFINITIONS
# ==========================================
# Using __file__ ensures paths are relative to this script's location
BASE_DIR = Path(__file__).parent.resolve()
HOME_DIR = Path.home()

# Chase Configuration Paths
SHARED_CONFIG_PATH = HOME_DIR / "chase_workspace" / "shared" / "common.yaml"
LOCAL_CONFIG_PATH = BASE_DIR / "config.yaml"
PROMPTS_DIR = BASE_DIR / "prompts"

# Experiment Directories
EXP_01_DIR = BASE_DIR / "experiments" / "01_repo_knowledge"
EXP_02_DIR = BASE_DIR / "experiments" / "02_api_contracts"

# ==========================================
# 2. ENVIRONMENT CONFIGURATION
# ==========================================
# This runs automatically as soon as this file is imported
os.environ["CHASE_CONFIG_PATH"] = f"{SHARED_CONFIG_PATH},{LOCAL_CONFIG_PATH}"
os.environ["CHASE_INSTRUCTIONS_DIR"] = str(PROMPTS_DIR)

print(f"[Setup] Environment configured automatically.")
print(f"[Setup] Instructions dir: {PROMPTS_DIR}")