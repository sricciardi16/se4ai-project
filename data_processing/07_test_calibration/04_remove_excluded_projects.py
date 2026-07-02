import env_setup

# The projects that are too flaky to be included in the final benchmark
EXCLUDED_PROJECTS = ["cmd2", "typer"]

def main():
    print("="*60)
    print("STEP 1: Purging Excluded Projects from Benchmark")
    print("="*60)

    for project in EXCLUDED_PROJECTS:
        print(f"\nPurging: {project}...")
        
        # 1. Delete the Metadata File
        meta_file = env_setup.METADATA_DIR / f"{project}.json"
        if meta_file.exists():
            meta_file.unlink()
            print(f"  [DELETED] Metadata: {meta_file.name}")
        else:
            print(f"  [SKIP] Metadata not found: {meta_file.name}")

        # 2. Delete the Test File
        test_file = env_setup.TESTS_DIR / f"test_{project}.py"
        if test_file.exists():
            test_file.unlink()
            print(f"  [DELETED] Test Suite: {test_file.name}")
        else:
            print(f"  [SKIP] Test Suite not found: {test_file.name}")

        # 3. (Optional) Delete the downloaded repository to save space
        repo_dir = env_setup.REPOS_DIR / project
        if repo_dir.exists():
            import shutil
            shutil.rmtree(repo_dir)
            print(f"  [DELETED] Repository: {repo_dir.name}/")
        else:
            print(f"  [SKIP] Repository not found: {repo_dir.name}/")

    print("\n" + "="*60)
    print(f"[SUCCESS] {len(EXCLUDED_PROJECTS)} projects have been completely removed.")
    print("="*60)

if __name__ == "__main__":
    main()