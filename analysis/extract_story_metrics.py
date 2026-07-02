import json
import re
from pathlib import Path

# ==========================================
# 1. PATH RESOLUTION
# ==========================================
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent

AGENTIC_DIR = PROJECT_ROOT / "evaluations" / "agentic"
OUTPUT_JSON = BASE_DIR / "story_metrics.json"

def parse_story_file(filepath: Path) -> dict:
    """Parses the project_story.md to extract sprints and iterations."""
    sprints = {}
    current_sprint = None

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Match "## Sprint 1"
            sprint_match = re.match(r"^##\s+Sprint\s+(\d+)", line)
            if sprint_match:
                current_sprint = int(sprint_match.group(1))
                if current_sprint not in sprints:
                    sprints[current_sprint] = 0
                continue
                
            # Match "### Iteration 1"
            iter_match = re.match(r"^###\s+Iteration\s+(\d+)", line)
            if iter_match and current_sprint is not None:
                iteration_num = int(iter_match.group(1))
                # Keep track of the highest iteration number seen in this sprint
                if iteration_num > sprints[current_sprint]:
                    sprints[current_sprint] = iteration_num

    # Determine Status based on the LAST sprint
    status = "UNKNOWN"
    if sprints:
        last_sprint = max(sprints.keys())
        last_sprint_iterations = sprints[last_sprint]
        
        if last_sprint_iterations >= 20:
            status = "HALTED_MAX_ITERATIONS"
        elif last_sprint_iterations == 1:
            status = "COMPLETED_SUCCESSFULLY"
        else:
            # Edge case: If it stopped at e.g., 5, it might have crashed or halted for another reason
            status = "HALTED_EARLY"

    return {
        "total_sprints": len(sprints),
        "iterations_per_sprint": sprints,
        "status": status
    }

def main():
    print("="*60)
    print("Extracting Agentic Story Metrics")
    print("="*60)

    if not AGENTIC_DIR.exists():
        print(f"[ERROR] Agentic evaluations directory not found: {AGENTIC_DIR}")
        exit(1)

    metrics_data = {}
    total_processed = 0

    # Crawl the agentic directory: evaluations/agentic/<model>/generated_code/<project_id>/project_story.md
    for model_dir in AGENTIC_DIR.iterdir():
        if not model_dir.is_dir():
            continue
            
        model_name = model_dir.name
        generated_code_dir = model_dir / "generated_code"
        
        if not generated_code_dir.exists():
            continue
            
        metrics_data[model_name] = {}
        
        for project_dir in generated_code_dir.iterdir():
            if not project_dir.is_dir():
                continue
                
            project_id = project_dir.name
            story_file = project_dir / "project_story.md"
            
            if not story_file.exists():
                print(f"  [WARNING] Missing story file for {model_name} -> {project_id}")
                continue
                
            # Parse the file
            story_metrics = parse_story_file(story_file)
            metrics_data[model_name][project_id] = story_metrics
            total_processed += 1

    # Print a quick summary to the console
    print(f"{'Model'.ljust(15)} | {'Project'.ljust(15)} | {'Sprints'} | {'Status'}")
    print("-" * 65)
    
    for model, projects in metrics_data.items():
        for proj, data in projects.items():
            sprints = data['total_sprints']
            status = data['status']
            
            # Color code the status for the console (optional but nice)
            if status == "COMPLETED_SUCCESSFULLY":
                status_str = f"✅ {status}"
            else:
                status_str = f"❌ {status}"
                
            print(f"{model.ljust(15)} | {proj.ljust(15)} | {str(sprints).ljust(7)} | {status_str}")

    # Save to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print(f"[DONE] Processed {total_processed} story files.")
    print(f"Saved metrics to {OUTPUT_JSON.name}")
    print("="*60)

if __name__ == "__main__":
    main()