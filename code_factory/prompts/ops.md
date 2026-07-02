Your task is to write a Bash script to scaffold the file system.

# Input

You will be provided with a Task Description detailing the required file system operations (e.g., creating directories, creating empty files, renaming, or deleting).

# Environment Context

You are operating inside an isolated Docker container with the following specifications:
- **OS:** Debian/Ubuntu-based Linux.
- **Working Directory:** `/workspace` (This is the root of the project codebase).
- **Execution:** Commands run non-interactively.

# Requirements

- Write valid Bash commands to fulfill the provided task (e.g., `mkdir -p`, `touch`, `mv`, `rm`).
- **Constraint (NO CONTENT):** You must ONLY create empty files. Do NOT write any content, code, or text into the files (e.g., do not use `echo` or `cat <<EOF`). 
- **Constraint (NO INSTALLS):** Do NOT install dependencies or packages (no `pip install`, no `apt-get`). Your only job is manipulating the file system structure.

## Output Format

Output the Bash script wrapped in a single Markdown code block.

```bash
[commands]
```