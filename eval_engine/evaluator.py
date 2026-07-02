import subprocess
import json
from pathlib import Path


from .config import (
    DOCKER_IMAGE_NAME,
    DOCKER_CACHE_VOLUME,
    DOCKER_TIMEOUT_SECONDS,
    DOCKER_MEM_LIMIT,
    DOCKER_CPU_LIMIT
)

def evaluate_project(
    project_id: str,
    import_name: str,
    repo_dir: Path,
    test_file: Path,
    base_output_dir: Path,
    test_dependencies: list = None
) -> str:

    """
    Executes a test suite against a Python repository within an isolated Docker sandbox.
    
    This function is completely agnostic to the origin of the tests. It simply takes 
    a source code directory and a test file, attempts to install the library, runs 
    the tests, and extracts structured execution and coverage metrics.
    
    Args:
        project_id: The unique identifier for the project (e.g., 'tabulate').
        import_name: The actual Python module name used for coverage (e.g., 'jwt').
        repo_dir: Path to the physical source code directory of the target library.
        test_file: Path to the pytest file to be executed.
        base_output_dir: The root directory where all results and artifacts are stored.
        
    Returns:
        A string representing the final status: 
        "SUCCESS", "INSTALL_FAILED", "TIMEOUT", "CRASH", or "ALREADY_EVALUATED".
    """

    # 1. Define the internal workspace structure
    project_out_dir = base_output_dir / project_id
    raw_artifacts_dir = project_out_dir / "raw_artifacts"
    evaluation_file = project_out_dir / "evaluation.json"

    # Resumability: If the clean evaluation file already exists, skip entirely.
    if evaluation_file.exists():
        return "ALREADY_EVALUATED"

    # Create the directories
    raw_artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Initialize the base scorecard
    scorecard = {
        "environment_status": "UNKNOWN",
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "success_rate": 0.0,
        "code_coverage": 0.0,
        "test_dossier": {}
    }

    # Convert list to space-separated string (e.g., "numpy pandas")
    test_dependencies = test_dependencies or []
    extra_deps_str = " ".join(test_dependencies)

    # 2. Execute the Docker Sandbox
    cmd = [
        "docker", "run", "--rm",
        
        # --- RESOURCE LIMITS (The Safety Net) ---
        f"--memory={DOCKER_MEM_LIMIT}",        
        f"--cpus={DOCKER_CPU_LIMIT}",  
        #"--network=none",     # OPTIONAL: Disable internet access so LLM tests can't make rogue API calls
        
        # --- ENVIRONMENT & VOLUMES ---
        "-e", f"MODULE_NAME={import_name}",
        "-e", f"EXTRA_DEPS={extra_deps_str}",
        "-v", f"{repo_dir}:/app/repo:ro",
        "-v", f"{test_file}:/app/test_suite.py:ro",
        "-v", f"{raw_artifacts_dir}:/app/results",
        "-v", f"{DOCKER_CACHE_VOLUME}:/root/.cache/pip",  
        DOCKER_IMAGE_NAME                                 
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=DOCKER_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        scorecard["environment_status"] = "TIMEOUT"
        _save_evaluation(evaluation_file, scorecard)
        return "TIMEOUT"

    # 3. Read the Raw Artifacts
    status_file = raw_artifacts_dir / "status.flag"
    report_file = raw_artifacts_dir / "report.json"
    coverage_file = raw_artifacts_dir / "coverage.json"

    # Check if the build succeeded
    if status_file.exists():
        with open(status_file, "r", encoding="utf-8") as f:
            scorecard["environment_status"] = f.read().strip()

    # If installation failed, save the minimal scorecard and exit
    if scorecard["environment_status"] == "INSTALL_FAILED":
        _save_evaluation(evaluation_file, scorecard)
        return "INSTALL_FAILED"

    # If it built successfully but there is no report, something crashed hard
    if not report_file.exists():
        scorecard["environment_status"] = "CRASH"
        _save_evaluation(evaluation_file, scorecard)
        return "CRASH"

    # 4. Parse the Pytest Report (Tier 1 & Tier 2 Data)
    with open(report_file, "r", encoding="utf-8") as f:
        report_data = json.load(f)
        
    summary = report_data.get("summary", {})
    scorecard["total_tests"] = summary.get("collected", 0)
    scorecard["passed"] = summary.get("passed", 0)
    scorecard["failed"] = summary.get("failed", 0) + summary.get("error", 0)
    
    if scorecard["total_tests"] > 0:
        scorecard["success_rate"] = round((scorecard["passed"] / scorecard["total_tests"] * 100), 2)

    # Build the Test Dossier
    for test in report_data.get("tests", []):
        test_name = test.get("nodeid", "").split("::")[-1]
        outcome = test.get("outcome", "unknown").upper()
        duration = test.get("setup", {}).get("duration", 0) + test.get("call", {}).get("duration", 0)
        
        crash_category, crash_message = None, None
        if outcome in ["FAILED", "ERROR"]:
            crash_info = test.get("call", {}).get("crash", {})
            crash_message = crash_info.get("message", "Unknown Error")
            if crash_message and ":" in crash_message:
                crash_category = crash_message.split(":")[0].strip()

        scorecard["test_dossier"][test_name] = {
            "status": outcome,
            "duration_seconds": round(duration, 4),
            "crash_category": crash_category,
            "crash_message": crash_message
        }

    # 5. Parse the Coverage Report
    if coverage_file.exists():
        with open(coverage_file, "r", encoding="utf-8") as f:
            cov_data = json.load(f)
            scorecard["code_coverage"] = round(cov_data.get("totals", {}).get("percent_covered", 0.0), 2)

    # 6. Save the clean evaluation and return success
    _save_evaluation(evaluation_file, scorecard)
    return "SUCCESS"


def _save_evaluation(filepath: Path, data: dict):
    """Helper function to safely save the JSON evaluation file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)