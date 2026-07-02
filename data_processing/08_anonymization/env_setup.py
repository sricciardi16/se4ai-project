import os
import sys
from pathlib import Path

# ==========================================
# 1. PATH DEFINITIONS
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()
DATA_PROCESSING_DIR = BASE_DIR.parent
PROJECT_ROOT = DATA_PROCESSING_DIR.parent

TESTS_DIR = PROJECT_ROOT / "tests"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
REPOS_DIR = PROJECT_ROOT / "repositories"

# Local Experiment Directories
EXP_01_ANONYMIZATION_DIR = BASE_DIR / "experiments" / "01_anonymized_names"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# ==========================================
# 2. CHASE CONFIGURATION
# ==========================================
HOME_DIR = Path.home()
SHARED_CONFIG_PATH = HOME_DIR / "chase_workspace" / "shared" / "common.yaml"
LOCAL_CONFIG_PATH = BASE_DIR / "config.yaml"
PROMPTS_DIR = BASE_DIR / "prompts"

os.environ["CHASE_CONFIG_PATH"] = f"{SHARED_CONFIG_PATH},{LOCAL_CONFIG_PATH}"
os.environ["CHASE_INSTRUCTIONS_DIR"] = str(PROMPTS_DIR)

TESTS_GEN_DIR = PROJECT_ROOT / "tests_gen"

EXP_02_ANONYMIZED_IMPORTS_DIR = BASE_DIR / "experiments" / "02_anonymized_imports"


EXP_04_VERIFICATION_DIR = BASE_DIR / "experiments" / "04_verification_results"