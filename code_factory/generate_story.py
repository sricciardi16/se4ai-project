import re
from pathlib import Path

EXPERIMENTS_DIR = Path("experiments")
OUTPUT_FILE = Path("project_story.md")

def strip_yaml_frontmatter(text: str) -> str:
    """
    Removes YAML front matter enclosed in --- at the start of the file.
    """
    # Matches --- at the very beginning, anything in between, and the closing ---
    return re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL).strip()

def flatten_headers(text: str) -> str:
    """
    Converts markdown headers (### Header) into bold text (**Header**)
    so they don't hijack the main document's Table of Contents.
    Ignores anything inside markdown code blocks to protect code comments.
    """
    if not text:
        return ""
        
    lines = text.splitlines()
    in_code_block = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Toggle code block state
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
            
        # Only flatten headers if we are NOT inside a code block
        if not in_code_block and stripped.startswith('#'):
            clean_text = stripped.lstrip('#').strip()
            if clean_text:
                lines[i] = f"**{clean_text}**"
                
    return "\n".join(lines)

def extract_parts(filepath: Path, ai_header: str) -> tuple[str, str]:
    """
    Reads a file, removes YAML front matter and the System header, 
    and splits it at the AI header. Returns (input_text, output_text).
    """
    if not filepath.exists():
        return "", ""
        
    content = filepath.read_text(encoding="utf-8")
    
    # 1. Strip the YAML front matter
    content = strip_yaml_frontmatter(content)
    
    # 2. Clean up the system header from the input
    content = content.replace("### System :robot:\n", "").strip()
    
    # 3. Split into Input and Output
    parts = content.split(ai_header)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    
    # Fallback if header is missing
    return content.strip(), ""

def build_story():
    if not EXPERIMENTS_DIR.exists():
        print("❌ Error: 'experiments' directory not found.")
        return

    # 1. Find all unique Sprint/Iteration prefixes by looking at the Architect folder
    architect_dir = EXPERIMENTS_DIR / "architect"
    if not architect_dir.exists():
        print("❌ Error: 'experiments/architect' directory not found.")
        return

    prefixes = []
    for f in architect_dir.glob("s*_i*.md"):
        # Extract sprint and iteration numbers for proper sorting
        match = re.match(r"s(\d+)_i(\d+)", f.stem)
        if match:
            prefixes.append((int(match.group(1)), int(match.group(2)), f.stem))
            
    # Sort chronologically: Sprint 1 Iteration 1, Sprint 1 Iteration 2, etc.
    prefixes.sort()

    if not prefixes:
        print("⚠️ No iteration logs found in experiments/architect.")
        return

    story_lines = ["# 📖 Project Storybook\n"]
    current_sprint = None

    # 2. Loop through each iteration and build the story
    for sprint_num, iter_num, prefix in prefixes:
        print(f"📄 Processing Sprint {sprint_num}, Iteration {iter_num}...")
        
        # Only print the Sprint header if we are starting a new Sprint
        if sprint_num != current_sprint:
            story_lines.append(f"## Sprint {sprint_num}")
            current_sprint = sprint_num
            
        story_lines.append(f"### Iteration {iter_num}\n")

        # --- SCOUT (Output Only) ---
        scout_file = EXPERIMENTS_DIR / "scout" / f"{prefix}.md"
        _, scout_out = extract_parts(scout_file, "### Scout :eyes:")
        if scout_out:
            story_lines.append("#### Scout")
            story_lines.append(flatten_headers(scout_out) + "\n")

        # --- ARCHITECT (Input & Output) ---
        arch_file = EXPERIMENTS_DIR / "architect" / f"{prefix}.md"
        arch_in, arch_out = extract_parts(arch_file, "### Architect :bulb:")
        if arch_in or arch_out:
            story_lines.append("#### Architect")
            story_lines.append("**[INPUT]**")
            story_lines.append(flatten_headers(arch_in))
            story_lines.append("\n**[OUTPUT]**")
            story_lines.append(flatten_headers(arch_out) + "\n")

        # --- TASK SPLITTER (Output Only) ---
        split_file = EXPERIMENTS_DIR / "task_splitter" / f"{prefix}.md"
        _, split_out = extract_parts(split_file, "### Task Splitter :dart:")
        if split_out:
            story_lines.append("#### Task Splitter")
            story_lines.append(flatten_headers(split_out) + "\n")

        # --- JSON CONVERTER (Output Only) ---
        json_file = EXPERIMENTS_DIR / "json_converter" / f"{prefix}_task_splitter.md"
        _, json_out = extract_parts(json_file, "### JSON Converter :package:")
        if json_out:
            story_lines.append("#### JSON Task List")
            story_lines.append(flatten_headers(json_out) + "\n")

        # --- OPS (Input & Output) ---
        ops_dir = EXPERIMENTS_DIR / "ops"
        if ops_dir.exists():
            ops_files = sorted(ops_dir.glob(f"{prefix}_*.md"))
            if ops_files:
                story_lines.append("#### Ops")
                for ops_file in ops_files:
                    ops_in, ops_out = extract_parts(ops_file, "### Ops :wrench:")
                    # Extract the task index from the filename (e.g., s1_i1_0 -> 0)
                    task_id = ops_file.stem.split("_")[-1]
                    story_lines.append(f"**Task: {task_id}**")
                    story_lines.append("**[INPUT]**")
                    story_lines.append(flatten_headers(ops_in))
                    story_lines.append("\n**[OUTPUT]**")
                    story_lines.append(flatten_headers(ops_out) + "\n")

        # --- CODER (Input & Output) ---
        coder_dir = EXPERIMENTS_DIR / "coder"
        if coder_dir.exists():
            coder_files = sorted(coder_dir.glob(f"{prefix}_*.md"))
            if coder_files:
                story_lines.append("#### Coder")
                for coder_file in coder_files:
                    coder_in, coder_out = extract_parts(coder_file, "### Coder :coffee:")
                    # Extract the target file name from the filename (e.g., s1_i1_src_main_py -> src_main_py)
                    target_name = coder_file.stem.replace(f"{prefix}_", "")
                    story_lines.append(f"**Target: {target_name}**")
                    story_lines.append("**[INPUT]**")
                    story_lines.append(flatten_headers(coder_in))
                    story_lines.append("\n**[OUTPUT]**")
                    story_lines.append(flatten_headers(coder_out) + "\n")

        story_lines.append("---\n") # Add a visual separator between iterations

    # 3. Write the final story to disk
    OUTPUT_FILE.write_text("\n".join(story_lines), encoding="utf-8")
    print(f"\n✅ Success! Project story written to {OUTPUT_FILE.name}")
