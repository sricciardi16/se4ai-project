import json
from pathlib import Path
from collections import defaultdict

from chase.facade import Chase

from chase.components.archives import markdown

from chase.components.feedback import console

from chase.components.io import variable


from chase.components.pipelines.response_sanitization import json_fence_enforcer
from chase.components.pipelines.normalization import json_code_block_tagger
from chase.components.pipelines.post_response_normalization import json_escape_repair

from chase.components.pipelines.presentation import json_fence_stripper

from chase.components.pipelines.response_sanitization import think_tag_remover

from chase.components.providers import gemini
from chase.components.providers import vertex_openai
from chase.components.providers import groq
from chase.components.providers import utils


from .chase_middleware import architect_spec_isolator
from .chase_middleware import reader_findings_isolator
from .chase_middleware import scout_plan_isolator
from .chase_middleware import source_code_isolator
from .chase_middleware import summary_isolator
from .chase_middleware import task_list_isolator

# Assuming PROMPTS_DIR is defined or you load templates from files.
# For this implementation, we assume the templates are loaded into strings.
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"

# ==========================================
# UTILITY FUNCTIONS
# ==========================================


def _run_json_converter(markdown_text: str, template_name: str, session_name: str) -> list:
    """Pipes markdown text through the JSON Converter agent."""
    template_path = PROMPTS_DIR / f"{template_name}.md"
    template_content = template_path.read_text(encoding="utf-8")
    prompt = template_content.replace("{markdown_text}", markdown_text)
    
    converter = Chase(profile="json_converter", session_id=session_name)
    converter.input.feed(prompt)
    out_str = converter.output.get_output()
    
    try:
        return json.loads(out_str)
    except json.JSONDecodeError as e:
        print(f"[FATAL ERROR] JSON Converter failed: {e}\nRaw: {out_str}")
        return []

# ==========================================
# PRIVATE INTERNAL FUNCTIONS (Context Engine)
# ==========================================

def _get_scout_plan(goal: str, project_tree: str, summaries: str, prefix: str) -> list:
    """Runs the Scout to determine which files need to be read."""
    
    if not project_tree:
        return []

    prompt = f"## Project Structure\n\n```\n{project_tree}\n```\n\n"
    
    if summaries:
        prompt += f"## File Summaries\n\n{summaries}\n\n"
        
    prompt += f"# Subject\n\n{goal}\n"

    scout = Chase(profile="scout", session_id=prefix)
    scout.input.feed(prompt)
    scout_markdown = scout.output.get_output()
    
    return _run_json_converter(scout_markdown, "format_scout", f"{prefix}_scout")

def _get_reader_findings(scout_plan_list: list, workspace_dir: Path, prefix: str) -> list:
    """
    Fires Readers in parallel. 
    Returns findings in the exact same order as scout_plan_list.
    """
    agents = []
    results = [None] * len(scout_plan_list)
    
    # 1. Initialize and Feed all agents in parallel
    for i, plan in enumerate(scout_plan_list):
        file_path = plan.get("file")
        questions = plan.get("questions", [])
        
        full_path = workspace_dir / file_path
        # Ensure it exists AND is a file (not a directory) before reading
        if full_path.exists() and full_path.is_file():
            try:
                file_content = full_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                file_content = "[This is a binary file. Its contents cannot be displayed as text.]"
        else:
            file_content = ""

        prompt = (
            f"### Source Code ({file_path})\n\n```python\n{file_content}\n```\n\n"
            f"### Questions\n\n" + "\n".join(f"- {q}" for q in questions) + "\n\n"
        )
        
        safe_name = file_path.replace("/", "_").replace(".", "_")
        reader = Chase(profile="reader", session_id=f"{prefix}_{safe_name}")
        reader.input.feed(prompt)
        agents.append((i, reader))
        
    # 2. Block and collect outputs
    for i, reader in agents:
        results[i] = reader.output.get_output()
        
    return results

def _build_project_snapshot(goal: str, project_tree: str, summaries: str, workspace_dir: Path, prefix: str) -> str:
    """Orchestrates Scout and Readers to build the snapshot for the Architect."""

    if not project_tree:
        return f"## Project Structure\n\nThe project is currently empty.\n\n"        

    snapshot = f"## Project Structure\n\n```\n{project_tree}\n```\n\n"
    
    if summaries:
        snapshot += f"## Brief File Descriptions\n\n{summaries}\n\n"

    scout_plan = _get_scout_plan(goal, project_tree, summaries, prefix)
    if scout_plan:
        findings = _get_reader_findings(scout_plan, workspace_dir, prefix)

        valid_findings = []
        for plan, finding in zip(scout_plan, findings):
            if "NO_FINDINGS" not in finding.upper():
                valid_findings.append((plan['file'], finding))
        
        if valid_findings:
            snapshot += "## Relevant Code Details\n\n"

            for file_path, finding in valid_findings:
                snapshot += f"### File: `{file_path}`\n\n{finding}\n\n"
            
    return snapshot.strip()
            
    return snapshot.strip()

# ==========================================
# PUBLIC API (Called by the Orchestrator)
# ==========================================

def generate_technical_spec(goal: str, project_tree: str, summaries: str, workspace_dir: Path, prefix: str) -> str:
    snapshot = _build_project_snapshot(goal, project_tree, summaries, workspace_dir, prefix)
    
    prompt = f"# Project Snapshot\n\n{snapshot}\n\n# Objective\n\n{goal}\n\n"
    
    architect = Chase(profile="architect", session_id=prefix)
    architect.input.feed(prompt)
    return architect.output.get_output()

def generate_task_list(technical_spec: str, prefix: str) -> list:
    splitter = Chase(profile="task_splitter", session_id=prefix)
    splitter.input.feed(technical_spec)
    markdown_tasks = splitter.output.get_output()
    
    if "NO_TASKS" in markdown_tasks:
        return []
    
    task_list = _run_json_converter(markdown_tasks, "format_tasks", f"{prefix}_task_splitter")
    
    filtered_tasks = [t for t in task_list if t.get("task_type") != "execute"]
    
    return filtered_tasks

def execute_tasks_in_parallel(task_list: list, current_file_states: dict, prefix: str) -> list:
    """
    The Wave Execution Engine.
    Runs tasks in parallel across different files, but sequentially for the same file.
    Returns a list of generated code/bash strings IN THE EXACT SAME ORDER as task_list.
    """
    results = [None] * len(task_list)
    
    # 1. Group tasks by target file. 
    # We store tuples of (original_index, task_dict) to preserve order.
    file_queues = defaultdict(list)
    
    for i, task in enumerate(task_list):
        target = task.get("target_file", "").strip()
        # If it's a system task with no target, give it a unique key so it runs immediately in parallel
        if not target or task.get("task_type") == "scaffold":
            target = f"__scaffold_{i}__"
        file_queues[target].append((i, task))

    # 2. Execute Waves until all queues are empty
    wave_number = 1
    while file_queues:
        print(f"    🌊 Starting Execution Wave {wave_number}...")
        current_wave_agents = []
        
        # Pop the first task from every file's queue
        keys_to_process = list(file_queues.keys())
        for file_key in keys_to_process:
            original_index, task = file_queues[file_key].pop(0)
            
            task_type = task.get("task_type")
            description = task.get("description")
            
            # Prepare Prompt and Agent
            if task_type == "scaffold":
                agent = Chase(profile="ops", session_id=f"{prefix}_{original_index}")
                prompt = f"### Task Description\n\n{description}\n"
            elif task_type == "implement":
                safe_name = file_key.replace("/", "_").replace(".", "_")
                agent = Chase(profile="coder", session_id=f"{prefix}_{safe_name}")
                
                # Get the current state (which might have been updated by a previous wave!)
                current_code = current_file_states.get(file_key, "")
                prompt = (
                    f"### Task Description\n\n{description}\n\n"
                    f"### Current File Content ({file_key})\n\n```python\n{current_code}\n```"
                )
            else:
                continue
            
            # FIRE IN PARALLEL
            agent.input.feed(prompt)
            current_wave_agents.append((agent, original_index, file_key, task_type))
            
            # Clean up empty queues
            if not file_queues[file_key]:
                del file_queues[file_key]

        # 3. Block and collect outputs for this wave
        for agent, index, file_key, task_type in current_wave_agents:
            output = agent.output.get_output()
            
            # Save to results array
            results[index] = output
            
            # CRUCIAL: Update the in-memory state so the next wave gets the new code!
            if task_type == "implement":
                current_file_states[file_key] = output
                
        wave_number += 1

    return results

def generate_summaries(source_code_list: list, file_paths: list, prefix: str) -> list:
    """
    Fires Summarizers in parallel. 
    Returns summary strings IN THE EXACT SAME ORDER as source_code_list.
    """
    agents = []
    results = [None] * len(source_code_list)
    
    # 1. Feed all
    for i, (code, path) in enumerate(zip(source_code_list, file_paths)):
        if not code.strip():
            results[i] = "This is an empty file."
        else:
            safe_name = path.replace("/", "_").replace(".", "_")
            summarizer = Chase(profile="summarizer", session_id=f"{prefix}_{safe_name}")
            summarizer.input.feed(f"### Source Code\n\n```\n{code}\n```\n")
            agents.append((i, summarizer))
        
    # 2. Collect all
    for i, summarizer in agents:
        results[i] = summarizer.output.get_output()
        
    return results