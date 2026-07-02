# env_setup.py
import os
import sys
from pathlib import Path

# ==========================================
# 1. PATH DEFINITIONS
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()           # .../data_processing/07_test_calibration
DATA_PROCESSING_DIR = BASE_DIR.parent                # .../data_processing
PROJECT_ROOT = DATA_PROCESSING_DIR.parent            # .../my_se4ai_proj

# Root-level directories
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"
REPOS_DIR = PROJECT_ROOT / "repositories"
TESTS_DIR = PROJECT_ROOT / "tests"

# Local Experiment Directories
BASELINE_RESULTS_DIR = BASE_DIR / "experiments" / "baseline_results"

# ==========================================
# 2. SYSTEM PATH CONFIGURATION
# ==========================================
# Add project root to sys.path so we can import eval_engine cleanly
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# ==========================================
# 3. CHASE CONFIGURATION
# ==========================================
HOME_DIR = Path.home()
SHARED_CONFIG_PATH = HOME_DIR / "chase_workspace" / "shared" / "common.yaml"
LOCAL_CONFIG_PATH = BASE_DIR / "config.yaml"
PROMPTS_DIR = BASE_DIR / "prompts"

os.environ["CHASE_CONFIG_PATH"] = f"{SHARED_CONFIG_PATH},{LOCAL_CONFIG_PATH}"
os.environ["CHASE_INSTRUCTIONS_DIR"] = str(PROMPTS_DIR)


EXP_01_TRIAGE_DIR = BASE_DIR / "experiments" / "01_zero_test_triage"
EXP_02_TRIAGE_DIR = BASE_DIR / "experiments" / "02_zero_test_triage"
EXP_03_FAILING_TRIAGE_DIR = BASE_DIR / "experiments" / "03_failing_tests_triage"

EXP_05_SEMANTIC_AUDIT_DIR = BASE_DIR / "experiments" / "05_semantic_name_audit"