import subprocess
from pathlib import Path
from .config import DOCKER_IMAGE_NAME

BASE_DIR = Path(__file__).parent.resolve()

def build_sandbox_image():
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

if __name__ == "__main__":
    build_sandbox_image()