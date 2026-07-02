You are reviewing a `pytest` suite for the `[PROJECT_NAME]` library. 

Your task is to find test names that are actively misleading or contradict the code inside them.

**CRITICAL RULE:** ONLY suggest a rename if the current name confuses the reader or lies about what the test does (e.g., the name implies a successful return, but the code actually asserts an Exception).   
**DO NOT** suggest renames for style, verbosity, or minor clarity. If the name is accurate enough, ignore it.

Output a strict JSON array of the tests that strictly require renaming. If no tests need renaming, return `[]`.

```json
[
  {
    "original_name": "...",
    "proposed_name": "...",
    "reason": "..."
  }
]
```

### Test Code:

```python
[TEST_CODE]
```

