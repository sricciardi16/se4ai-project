import os
import json
import tempfile
import env_setup
from pathlib import Path

from eval_engine import build_sandbox_image, evaluate_project

# ==========================================
# THE IMPORT HOOK TEMPLATE
# ==========================================
# This is the magic code injected at the top of the temp file.
# It intercepts the fake name and seamlessly loads the real name.
# ==========================================
# THE IMPORT HOOK TEMPLATE (GOD MODE)
# ==========================================
# ==========================================
# THE IMPORT HOOK TEMPLATE (SAFE MODE)
# ==========================================
HOOK_TEMPLATE = """
import sys
import importlib
import importlib.util
from importlib.abc import MetaPathFinder, Loader

class AliasLoader(Loader):
    def __init__(self, real_name):
        self.real_name = real_name
        
    def create_module(self, spec):
        # Load the real module, but DO NOT mutate its __name__
        return importlib.import_module(self.real_name)
        
    def exec_module(self, module):
        pass

class AliasFinder(MetaPathFinder):
    def __init__(self, fake_name, real_name):
        self.fake_name = fake_name
        self.real_name = real_name

    def find_spec(self, fullname, path, target=None):
        if fullname == self.fake_name or fullname.startswith(self.fake_name + '.'):
            real_fullname = fullname.replace(self.fake_name, self.real_name, 1)
            
            real_spec = importlib.util.find_spec(real_fullname)
            if not real_spec:
                return None
            
            fake_spec = importlib.util.spec_from_loader(fullname, AliasLoader(real_fullname))
            
            # THE FIX FOR LIFELINES: Tell Python this is a package so sub-imports work
            if real_spec.submodule_search_locations is not None:
                fake_spec.submodule_search_locations = real_spec.submodule_search_locations
                
            return fake_spec
        return None

sys.meta_path.insert(0, AliasFinder('{fake_name}', '{real_name}'))

# --- ORIGINAL TEST CODE BELOW ---
"""

def main():
    env_setup.EXP_04_VERIFICATION_DIR.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("STEP 1: Ensuring Docker Sandbox is Built")
    print("="*60)
    build_sandbox_image()

    print("\n" + "="*60)
    print("STEP 2: Verifying Anonymized Tests")
    print("="*60)

    metadata_files = sorted(list(env_setup.METADATA_DIR.glob("*.json")))
    print(f"Found {len(metadata_files)} projects to verify.\n")

    for meta_file in metadata_files:
        project_id = meta_file.stem
        
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        real_name = metadata.get("import_name")
        fake_name = metadata.get("import_name_gen")
        test_dependencies = metadata.get("test_dependencies", [])
        
        if not real_name or not fake_name:
            print(f"[SKIP] {project_id.ljust(15)} | Missing import names in metadata.")
            continue
        
        repo_dir = env_setup.REPOS_DIR / project_id
        test_file = env_setup.TESTS_GEN_DIR / f"test_{project_id}.py"
        
        if not repo_dir.exists() or not test_file.exists():
            print(f"[SKIP] {project_id.ljust(15)} | Missing repo or tests_gen file.")
            continue
            
        print(f"Verifying: {project_id.ljust(15)} | {fake_name} -> {real_name}")

        # 1. Read the anonymized test code
        with open(test_file, "r", encoding="utf-8") as f:
            test_code = f.read()

        # 2. Prepare the injected code
        injected_code = HOOK_TEMPLATE.format(fake_name=fake_name, real_name=real_name) + test_code

        # 3. Create the temporary file
        # delete=False is needed so Docker can read it before it disappears
        temp_fd, temp_path_str = tempfile.mkstemp(suffix=".py", prefix=f"verify_{project_id}_")
        temp_path = Path(temp_path_str)
        
        try:
            # Write the injected code to the temp file
            with os.fdopen(temp_fd, 'w', encoding="utf-8") as f:
                f.write(injected_code)

            # 4. Run the evaluation!
            # Notice we pass `real_name` to import_name so coverage still tracks the real library
            status = evaluate_project(
                project_id=project_id,
                import_name=real_name, 
                repo_dir=repo_dir,
                test_file=temp_path,
                base_output_dir=env_setup.EXP_04_VERIFICATION_DIR,
                test_dependencies=test_dependencies
            )
            print(f"  -> Status: {status}")

        finally:
            # 5. CLEANUP: Guarantee the temp file is deleted immediately
            if temp_path.exists():
                temp_path.unlink()

    print("\n" + "="*60)
    print("STEP 3: Compiling Verification Scorecard")
    print("="*60)

    master_scorecard = {}
    for project_dir in env_setup.EXP_04_VERIFICATION_DIR.iterdir():
        if project_dir.is_dir():
            eval_file = project_dir / "evaluation.json"
            if eval_file.exists():
                with open(eval_file, "r", encoding="utf-8") as f:
                    master_scorecard[project_dir.name] = json.load(f)

    master_file_path = env_setup.EXP_04_VERIFICATION_DIR / "master_verification_report.json"
    with open(master_file_path, "w", encoding="utf-8") as f:
        json.dump(master_scorecard, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Compiled verifications into {master_file_path.name}")
    print("="*60)

if __name__ == "__main__":
    main()