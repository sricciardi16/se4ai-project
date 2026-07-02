from pathlib import Path

from factory import agents
from factory import memory
from sandbox.engine import run_in_sandbox

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR / "workspace"

def achieve_goal(initial_objective: str, sprint: int = 1, max_iterations: int = 5) -> str:
    """
    Takes a specific goal, executes the autonomous CI/CD loop to build it,
    and self-heals if tests fail. 
    
    Returns True if the goal was successfully achieved and tested.
    Returns False if it failed after max_iterations.
    """
    
    iteration = 1
    failure_message = ""

    print("\n" + "="*60)
    print(f"🎯 NEW GOAL STARTED (Max Iterations: {max_iterations})")
    print("="*60)

    while iteration <= max_iterations:
        print(f"\n🔄 --- SPRINT ITERATION {iteration} ---")
        
        # ---------------------------------------------------------
        # PHASE 1: Context & Planning
        # ---------------------------------------------------------
        print("    -> 🧠 Architect is analyzing the project and writing the Spec...")
        tree = memory.get_project_tree()
        summaries = memory.get_formatted_summaries()
        
        # Construct the dynamic goal for this specific iteration (The North Star Pattern)
        if iteration == 1:
            current_goal = initial_objective
        else:
            current_goal = (
                f"## ORIGINAL OBJECTIVE\n\n"
                f"While fixing the issues, ensure the system still fulfills this original objective:\n\n"
                f"{initial_objective}\n\n"
                f"{failure_message}\n\n"
            )
        
        prefix = f"s{sprint}_i{iteration}"
        
        technical_spec = agents.generate_technical_spec(current_goal, tree, summaries, WORKSPACE_DIR, prefix)

        
        print("    -> 📋 Task Splitter is breaking down the Spec...")
        task_list = agents.generate_task_list(technical_spec, prefix)


        if not task_list:
            print("    ✅ No tasks generated. The Objective appears to be complete!")
            return "COMPLETE"
            
        print(f"    -> 🎯 Generated {len(task_list)} tasks.")

        # ---------------------------------------------------------
        # PHASE 2: Generation (The Wave Engine)
        # ---------------------------------------------------------
        # Load current file states for the files we are about to modify
        current_states = {}
        for task in task_list:
            if task.get("task_type") == "implement":
                target = task.get("target_file")
                if target and target not in current_states:
                    current_states[target] = memory.read_file(target)

        print("    -> ⚡ Executing tasks in parallel waves...")
        # Note: agents.execute_tasks_in_parallel modifies current_states in-place!
        results = agents.execute_tasks_in_parallel(task_list, current_states, prefix)
        
        # ---------------------------------------------------------
        # PHASE 3: Physical Execution (Sandbox & Disk)
        # ---------------------------------------------------------
        files_to_write = {}
        
        for task, generated_content in zip(task_list, results):
            task_type = task.get("task_type")
            
            if task_type == "scaffold":
                print(f"    -> 🔧 Running Ops Script: {task.get('task_name')}")
                # Write to a temp file to avoid bash escaping nightmares
                temp_script_path = WORKSPACE_DIR / ".chase_temp_ops.sh"
                temp_script_path.write_text(generated_content, encoding="utf-8")
                
                run_in_sandbox(["bash", ".chase_temp_ops.sh"])
                
                if temp_script_path.exists():
                    temp_script_path.unlink()
                

        # Safely grab the final accumulated state of all code files from the Wave Engine
        for file_key, final_code in current_states.items():
            files_to_write[file_key] = final_code

        if files_to_write:
            print("    -> 💾 Writing files to disk...")
            memory.write_files(files_to_write)
            
            print("    -> 📝 Generating summaries for new code...")
            new_summaries_list = agents.generate_summaries(list(files_to_write.values()), list(files_to_write.keys()), prefix)
            
            # Zip the file paths with their new summaries and update memory
            new_summaries_dict = dict(zip(files_to_write.keys(), new_summaries_list))
            memory.update_summaries(new_summaries_dict)


        memory.sync_summaries_with_disk()

        # ---------------------------------------------------------
        # PHASE 4: Verification (The CI/CD Gate)
        # ---------------------------------------------------------
        print("    -> 📦 Installing project in Sandbox...")
        install_cmd = "pip install -e ."
        install_result = run_in_sandbox(["bash", "-c", install_cmd])

        if install_result["exit_code"] != 0:
            print(f"\n❌ [FAIL] Installation failed. Triggering Self-Healing Loop (Iteration {iteration + 1})...")
            failure_message = (
                f"## CURRENT OBJECTIVE\n\n"
                f"I want to install the project in editable mode. I ran the command `pip install -e .`, "
                f"however it gives me this output:\n\n"
                f"```text\n{install_result['stdout']}\n{install_result['stderr']}\n```\n\n"
                f"Analyze carefully what has been done in the project that leads to this packaging or structural error. "
                f"Fix the project structure or dependencies so it installs correctly."
            )
            iteration += 1
            continue

        print("    -> 🧪 Running Test Suite in Sandbox...")
        test_cmd = """
        set -e
        pip install -e . > /dev/null 2>&1
        pytest tests/ -v
        """
        test_result = run_in_sandbox(["bash", "-c", test_cmd])
                
        allowed_exit_codes = [0, 5] if sprint == 1 else [0]
        
        if test_result["exit_code"] in allowed_exit_codes:
            print("\n🎉 [SUCCESS] All tests passed (or safely skipped)! Goal Achieved! 🎉")
            return "SUCCESS"
        else:
            print(f"\n❌ [FAIL] Tests failed. Triggering Self-Healing Loop (Iteration {iteration + 1})...")
            failure_message = (
                f"## CURRENT OBJECTIVE\n\n"
                f"I ran the tests in the `tests/` folder with the command `pytest tests/`. "
                f"However, I get this output:\n\n"
                f"```text\n{test_result['stdout']}\n{test_result['stderr']}\n```\n\n"
                f"What happened? Why did this specific output occur?\n\n"
                f"Analyze the project thoroughly. Do not just look at the surface-level traceback. "
                f"Once you find the exact root cause, evaluate the failure using the specification as the absolute source of truth:\n"
                f"- If the tests correctly reflect the specification, then the application code is flawed and must be corrected.\n"
                f"- If the tests contradict the specification, or are themselves implemented incorrectly, then the tests are flawed and must be corrected or removed.\n\n"
                f"Tell me exactly what I need to do to fix the root cause directly in the relevant files.\n"
                f"WARNING: Do NOT modify correct application code just to satisfy a flawed test. You have full permission to rewrite or delete any file in the `tests/` folder if it contradicts the Master Specification."                
            )
            iteration += 1
            continue

    print(f"\n⚠️ [ABORT] Exceeded maximum iterations ({max_iterations}). Goal failed.")
    return "FAIL"
