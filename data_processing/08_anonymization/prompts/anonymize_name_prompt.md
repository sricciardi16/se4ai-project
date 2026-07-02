I am building a benchmark to evaluate code generation. I need to anonymize the name of a target Python library so the LLM being evaluated cannot cheat by using its pre-trained memory of the original library.

Here is the test suite for a subset of the library's functionality:

```python
[TEST_CODE]
```

Based strictly on the functionalities tested in this code, propose a NEW, anonymized name for this library.

CRITICAL RULES:
1. The name MUST be a valid Python module name (lowercase, underscores only, no spaces, no hyphens).
2. The name MUST describe what the library does.
3. The name MUST NOT contain the original library name or obvious hints.

Return ONLY a JSON object in this exact format:
```json
{
  "anonymized_name": "your_proposed_name"
}
```