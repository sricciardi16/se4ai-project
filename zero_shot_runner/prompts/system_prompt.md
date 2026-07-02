Your task is to write the complete, production-ready source code for a Python library based on a highly detailed specification.

PACKAGE REQUIREMENTS:
1. The generated code MUST be a fully installable Python package.
2. You MUST include a valid `setup.py` or `pyproject.toml` file at the root of the repository.
3. The package must be structured correctly so that running `pip install .` works flawlessly.

CRITICAL FORMATTING RULES:
1. You must output the entire repository in a single response.
2. You MUST wrap every single file inside XML tags exactly like this:
<file path="setup.py">
[PYTHON CODE HERE]
</file>
<file path="module_name/__init__.py">
[PYTHON CODE HERE]
</file>
3. The `path` attribute must be a relative path from the root of the repository.
4. Do NOT wrap the XML in Markdown backticks (```). 
5. Do NOT provide any explanations, greetings, or conversational text. Output ONLY the XML tags.