Your task is to analyze the provided Project Snapshot against the stated Objective and produce a Technical Specification.

# Input

You will be provided with:
1. **Project Snapshot:** The current state of the project: Project Structure, Brief File Descriptions, and Relevant Code Details.
2. **Objective:** The intended outcome: the specific change or result to be achieved.

# Output

Produce a Technical Specification following this structure:

### Situation Analysis

Analyze the Project Snapshot against the Objective. Identify the specific gap between the current reality and the intended outcome. Explain the logic required to bridge this gap and the reasoning behind it.

### Implementation Plan

Write a detailed, narrative walkthrough of the operations required to achieve the Objective.

**Constraint:** The reader accesses files individually by their path. They cannot search or browse the project structure.

**Requirements:**

1.  **File Paths:** When describing an operation on a file, you must explicitly state the file path. Assume you are operating at the root of the project. Use strict relative paths (e.g., `src/api/routes.py`). Do NOT prepend `/`, `./`, or `workspace/`.
2.  **Implementation Details:** Describe the logic and necessary changes. Focus on *what* needs to be done and *how*. Avoid writing full code blocks.

### Target State

Describe the final state of the project after the implementation is complete. Focus on the outcome: the specific files that have been created or modified, and the resulting behavior of the system. This serves as the confirmation that the Objective has been met.