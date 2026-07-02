import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR / "workspace"
MEMORY_FILE = WORKSPACE_DIR / ".chase_memory.json"

# ==========================================
# READ OPERATIONS (Context Gathering)
# ==========================================

def get_project_tree() -> str:
    """
    Generates a flat list of all file paths in the workspace.
    This is the most reliable format for LLMs to prevent path hallucinations.
    """
    if not WORKSPACE_DIR.exists():
        return ""

    file_paths = []
    for root, dirs, files in os.walk(WORKSPACE_DIR):
        # Ignore hidden directories (like .git, .pytest_cache) and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'venv', 'env') and not d.endswith('.egg-info')]
        for f in files:
            if not f.startswith('.'): # Ignore hidden files like .chase_memory.json
                # Get the absolute path, then find the relative path from WORKSPACE_DIR
                full_path = Path(root) / f
                relative_path = full_path.relative_to(WORKSPACE_DIR)
                file_paths.append(str(relative_path))
                
    if not file_paths:
        return ""
        
    # Sort alphabetically so it's logically grouped by folders
    file_paths.sort()
    
    return "\n".join(file_paths)

def load_summaries() -> dict:
    """Loads the living memory of file summaries as a dictionary."""
    if not MEMORY_FILE.exists():
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def get_formatted_summaries() -> str:
    """Returns a markdown string of all current file summaries for the Scout."""
    summaries = load_summaries()
    if not summaries:
        return ""
    
    lines = []
    for file_path, summary in summaries.items():
        lines.append(f"### `{file_path}`\n\n{summary}\n")
    return "\n".join(lines)

def read_file(relative_path: str) -> str:
    """Reads a single file from the workspace. Returns empty string if it doesn't exist."""
    full_path = WORKSPACE_DIR / relative_path
    if full_path.exists() and full_path.is_file():
        return full_path.read_text(encoding="utf-8")
    return ""

# ==========================================
# WRITE OPERATIONS (Batch Execution)
# ==========================================

def write_files(files_dict: dict):
    """
    Takes a dictionary of {relative_path: content} and writes them to disk.
    Automatically creates any missing parent directories.
    """
    for relative_path, content in files_dict.items():
        # FIX: Remove leading slashes so pathlib doesn't jump to the root directory!
        safe_relative_path = relative_path.lstrip("/")
        
        full_path = (WORKSPACE_DIR / safe_relative_path).resolve()
        
        if not full_path.is_relative_to(WORKSPACE_DIR.resolve()):
            print(f"    🚨 SECURITY WARNING: LLM attempted path traversal: {relative_path}. Skipping.")
            continue

        # Ensure the directory exists (e.g., src/auth/login.py -> creates src/auth/)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"    💾 Saved: {safe_relative_path}")

def update_summaries(new_summaries_dict: dict):
    """
    Takes a dictionary of {relative_path: summary_text} and updates the living memory.
    """
    if not new_summaries_dict:
        return

    # Load existing memory
    summaries = load_summaries()
    
    # Update with new data
    for relative_path, summary_text in new_summaries_dict.items():
        summaries[relative_path] = summary_text
        print(f"    🧠 Memory Updated: {relative_path}")
    
    # Save back to disk
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=4)


def sync_summaries_with_disk():
    """
    Garbage Collection: Removes summaries from memory for files 
    that have been deleted or renamed by scaffold tasks.
    """
    summaries = load_summaries()
    if not summaries:
        return

    keys_to_delete = []
    for relative_path in summaries.keys():
        full_path = WORKSPACE_DIR / relative_path
        # If the file no longer exists on the hard drive, mark it for deletion
        if not full_path.exists():
            keys_to_delete.append(relative_path)

    if keys_to_delete:
        for k in keys_to_delete:
            del summaries[k]
            print(f"    🧹 Memory Cleanup: Removed ghost summary for {k}")
        
        # Save the cleaned memory back to disk
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(summaries, f, indent=4)