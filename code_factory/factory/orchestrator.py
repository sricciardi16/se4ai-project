from pathlib import Path
from factory.loop import achieve_goal
from sandbox.engine import setup_environment

BASE_DIR = Path(__file__).resolve().parent.parent

def setup_directories():
    """Ensures all required directories exist before running."""
    directories = [
        "workspace",
        "workspace/tests",
        "experiments/task_splitter",
        "experiments/json_converter",
        "experiments/coder",
        "experiments/architect",
        "experiments/ops",
        "experiments/summarizer",
        "experiments/scout",
        "experiments/reader"
    ]
    for dir_path in directories:
        (BASE_DIR / dir_path).mkdir(parents=True, exist_ok=True)

def build_project(specification: str, max_iterations: int = 20, start_sprint: int = 1):
    """
    Takes a raw project specification string and runs the continuous 
    Agile Factory loop until the project is fully built and tested.
    """
    # 1. Prepare the physical environment
    setup_directories()
    setup_environment()

    print("\n" + "="*80)
    print(f"🚀 STARTING CONTINUOUS FACTORY LOOP")
    print(f"📄 Loaded Specification ({len(specification)} characters)")
    print("="*80)

    # 2. The Outer Loop (Agile Sprints)
    sprint_number = start_sprint
    
    while True:
        print(f"\n" + "░"*80)
        print(f"🏁 STARTING PROJECT SPRINT {sprint_number}")
        print("░"*80)
        
        # ---------------------------------------------------------
        # DYNAMIC META-PROMPT SELECTION
        # ---------------------------------------------------------
        if sprint_number == 1:
            # PHASE 1: The Foundation
            current_objective = (
                f"## PROJECT TO IMPLEMENT\n\n"
                f"{specification}\n\n"
                f"## INSTRUCTIONS\n\n"
                f"Based on the project described above, initialize its foundational project structure "
                f"and make it an installable Python package. "
                f"Do NOT implement any business logic, algorithms, or features yet. Just build the skeleton."
            )
        else:
            # PHASE 2: Adaptive Feature Implementation
            current_objective = (
                f"## PROJECT TO IMPLEMENT\n\n"
                f"{specification}\n\n"
                f"## INSTRUCTIONS\n\n"
                f"We are implementing the project described above. The final goal is to implement it all.\n\n"
                f"1. Carefully analyze the current codebase to determine exactly what has already been implemented according to the specification.\n"
                f"2. Carefully analyze what has NOT yet been implemented.\n"
                f"3. Based on this analysis, decide what to build next. If the remaining work is simple, implement it all. If the remaining work is complex, isolate one specific logical component to build during this stage.\n"
                f"4. Adhere to the specification. If you see that everything requested has already been implemented, do not invent or add unrequested features just to keep going. If you are done, simply output an empty plan."
            )

        # 3. Run the inner self-healing loop for this specific chunk
        status = achieve_goal(current_objective, sprint=sprint_number, max_iterations=max_iterations)
                
        if status == "COMPLETE":
            print("\n🏆 PROJECT FINISHED! The Architect determined all requirements in the specification are met.")
            break
            
        elif status == "SUCCESS":
            print(f"\n✅ Sprint {sprint_number} completed successfully. Moving to the next chunk...")
            sprint_number += 1
            
        elif status == "FAIL":
            print(f"\n💀 Sprint {sprint_number} failed to pass tests after {max_iterations} iterations.")
            print("Halting the Factory to prevent bad code from accumulating. Please check the workspace and logs.")
            break