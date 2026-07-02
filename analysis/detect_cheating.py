import json
import re
import ast
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent

EVALUATIONS_DIR = PROJECT_ROOT / "evaluations"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
OUTPUT_JSON = BASE_DIR / "dependency_check.json"

# Known aliases for PyPI packages
KNOWN_ALIASES = {
    "dateutil": ["python-dateutil", "dateutil"],
    "jwt": ["pyjwt", "jwt"],
    "pypdf2": ["pypdf", "pypdf2", "pypdf3"],
    "pypdf": ["pypdf", "pypdf2", "pypdf3"],
    "slugify": ["python-slugify", "slugify", "awesome-slugify"]
}

def extract_setup_py_deps(filepath: Path) -> list:
    """Uses AST to deterministically extract install_requires from setup.py"""
    deps = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'setup':
                for kw in node.keywords:
                    if kw.arg == 'install_requires' and isinstance(kw.value, ast.List):
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Constant): # Python 3.8+
                                deps.append(elt.value.lower())
                            elif isinstance(elt, ast.Str): # Older Python
                                deps.append(elt.s.lower())
    except Exception:
        pass
    return deps

def extract_pyproject_deps(filepath: Path) -> list:
    """Uses Regex to extract arrays assigned to 'dependencies' in TOML"""
    deps = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        matches = re.findall(r'(?:dependencies|requires)\s*=\s*\[(.*?)\]', content, re.DOTALL)
        for match in matches:
            strings = re.findall(r'["\'](.*?)["\']', match)
            deps.extend([s.lower() for s in strings])
    except Exception:
        pass
    return deps

def extract_requirements_txt(filepath: Path) -> list:
    """Reads requirements.txt, ignoring comments"""
    deps = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.split('#')[0].strip()
                if line:
                    pkg_name = re.split(r'[=<>~]', line)[0].strip()
                    deps.append(pkg_name.lower())
    except Exception:
        pass
    return deps

def main():
    print("="*60)
    print("Checking for Original Library Dependencies")
    print("="*60)

    cheat_data = {}
    generated_dirs = list(EVALUATIONS_DIR.glob("*/*/generated_code/*"))

    for gen_dir in generated_dirs:
        if not gen_dir.is_dir():
            continue

        project_id = gen_dir.name
        model_name = gen_dir.parents[1].name
        approach = gen_dir.parents[2].name

        # 1. Get the original library name
        meta_file = METADATA_DIR / f"{project_id}.json"
        if not meta_file.exists():
            continue
            
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        original_name = metadata.get("import_name", "").lower()
        if not original_name:
            continue

        targets_to_check = KNOWN_ALIASES.get(original_name, [original_name, project_id.lower()])

        # 2. Extract all declared dependencies
        declared_deps = []
        if (gen_dir / "setup.py").exists():
            declared_deps.extend(extract_setup_py_deps(gen_dir / "setup.py"))
        if (gen_dir / "pyproject.toml").exists():
            declared_deps.extend(extract_pyproject_deps(gen_dir / "pyproject.toml"))
        if (gen_dir / "requirements.txt").exists():
            declared_deps.extend(extract_requirements_txt(gen_dir / "requirements.txt"))

        declared_deps = [d.strip() for d in declared_deps]

        # 3. Check if any target is in the declared dependencies
        requires_original_lib = False
        
        for target in targets_to_check:
            if any(target in dep for dep in declared_deps):
                requires_original_lib = True
                break

        # 4. Record findings for ALL projects
        if approach not in cheat_data:
            cheat_data[approach] = {}
        if model_name not in cheat_data[approach]:
            cheat_data[approach][model_name] = {}

        cheat_data[approach][model_name][project_id] = {
            "requires_original_lib": requires_original_lib
        }

        if requires_original_lib:
            print(f"  [🚨 FOUND] {approach} | {model_name} | {project_id}")

    # 5. Write to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(cheat_data, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print(f"[DONE] Dependency check saved to {OUTPUT_JSON.name}")
    print("="*60)

if __name__ == "__main__":
    main()