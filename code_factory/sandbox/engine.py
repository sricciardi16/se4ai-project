import os
import subprocess
from pathlib import Path
from .config import (
    DOCKER_IMAGE_NAME,
    DOCKER_TIMEOUT_SECONDS,
    DOCKER_MEM_LIMIT,
    DOCKER_CPU_LIMIT
)

# Define paths relative to this file
BASE_DIR = Path(__file__).parent.resolve()
WORKSPACE_DIR = BASE_DIR.parent / "workspace"

def setup_environment():
    """Creates the workspace folder and builds the Docker image."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print(f"Building Docker Sandbox Image: {DOCKER_IMAGE_NAME}")
    print("="*60)
    
    try:
        subprocess.run(
            ["docker", "build", "-t", DOCKER_IMAGE_NAME, "."], 
            cwd=BASE_DIR, 
            check=True
        )
        print("\n[SUCCESS] Sandbox image built successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Failed to build Docker image: {e}")
        exit(1)

def write_file(relative_path: str, content: str):
    """
    The Orchestrator uses this to save the LLM's code to the host machine.
    Because the workspace is mounted to Docker, the container sees it instantly.
    """
    file_path = WORKSPACE_DIR / relative_path
    # Ensure subdirectories exist (e.g., http_client/models.py)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[HOST] Wrote file: {relative_path}")

def run_in_sandbox(command: list[str]) -> dict:
    """
    Executes a command inside the Docker container against the live workspace.
    Example command: ["pytest", "tests/test_exceptions.py"]
    """
    docker_cmd = [
        "docker", "run", "--rm",
        f"--memory={DOCKER_MEM_LIMIT}",        
        f"--cpus={DOCKER_CPU_LIMIT}",  
        # Mount the host workspace to /workspace in the container (Read/Write)
        "-v", f"{WORKSPACE_DIR}:/workspace",
        DOCKER_IMAGE_NAME
    ] + command

    try:
        # 1. Run the actual command
        result = subprocess.run(
            docker_cmd, 
            capture_output=True, 
            text=True, 
            timeout=DOCKER_TIMEOUT_SECONDS
        )
        
        # 2. FIX PERMISSIONS (The Magic Trick)
        # Docker runs as root. If it created files/folders, the host user can't touch them.
        # We run a quick chown to give ownership back to the host user (s1lv3str0).
        uid = os.getuid()
        gid = os.getgid()
        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{WORKSPACE_DIR}:/workspace",
            DOCKER_IMAGE_NAME, "chown", "-R", f"{uid}:{gid}", "/workspace"
        ], capture_output=True)
        
        return {
            "status": "SUCCESS" if result.returncode == 0 else "FAILED",
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        # Even on timeout, try to fix permissions just in case
        uid = os.getuid()
        gid = os.getgid()
        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{WORKSPACE_DIR}:/workspace",
            DOCKER_IMAGE_NAME, "chown", "-R", f"{uid}:{gid}", "/workspace"
        ], capture_output=True)
        
        return {
            "status": "TIMEOUT",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {DOCKER_TIMEOUT_SECONDS} seconds."
        }