import os
from pathlib import Path

# ==========================================
# 1. PATH DEFINITIONS
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()           # .../data_processing/06_test_generation
DATA_PROCESSING_DIR = BASE_DIR.parent                # .../data_processing
PROJECT_ROOT = DATA_PROCESSING_DIR.parent      
HOME_DIR = Path.home()

DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"
      

# Chase Configuration Paths
SHARED_CONFIG_PATH = HOME_DIR / "chase_workspace" / "shared" / "common.yaml"
LOCAL_CONFIG_PATH = BASE_DIR / "config.yaml"
PROMPTS_DIR = BASE_DIR / "prompts"

# Input Data Sources
DIR_01_REPO_KNOWLEDGE = DATA_PROCESSING_DIR / "01_llm_repo_check" / "experiments" / "01_repo_knowledge"
VERSIONS_FILE = DATA_PROCESSING_DIR / "05_versioning_and_download" / "experiments" / "inferred_versions.json"
TEST_PLAN_FILE = DATA_PROCESSING_DIR / "04_test_plan_merger" / "experiments" / "functional_test_plan.json"

# Local Experiment Directories
EXP_01_DIR = BASE_DIR / "experiments" / "01_generate_tests"
GENERATED_CODE_DIR = BASE_DIR / "experiments" / "generated_tests"

# ==========================================
# 2. ENVIRONMENT CONFIGURATION
# ==========================================
os.environ["CHASE_CONFIG_PATH"] = f"{SHARED_CONFIG_PATH},{LOCAL_CONFIG_PATH}"
os.environ["CHASE_INSTRUCTIONS_DIR"] = str(PROMPTS_DIR)

# ==========================================
# 3. RENAMING MAPPING
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
    "sdispater_pendulum.md": "pendulum.md",
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
    "un33k_python-slugify.md": "slugify.md"
}



MERGED_TESTS_DIR = BASE_DIR / "experiments" / "merged_tests"


FORMATTED_IMPORTS_DIR = BASE_DIR / "experiments" / "formatted_imports"
FINAL_TEST_FILES_DIR = BASE_DIR / "experiments" / "final_test_files"

EXP_02_DIR = BASE_DIR / "experiments" / "02_format_imports"


ROOT_TESTS_DIR = PROJECT_ROOT / "tests"

# Add under your Local Experiment Directories
EXP_04_DIR = BASE_DIR / "experiments" / "04_test_suite_audit"