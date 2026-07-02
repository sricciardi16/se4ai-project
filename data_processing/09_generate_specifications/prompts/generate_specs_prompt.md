You are an Expert Software Architect. Your task is to reverse-engineer a Python test suite into a comprehensive, imperative implementation specification.

### Context & Anonymization

The test suite provided below is designed to test a library named `[NEW_IMPORT_NAME]`. 
This library is actually a subset of the real-world library `[ORIGINAL_IMPORT_NAME]`. The tests have been modified to run against the new name.

**CRITICAL RULE 1: TOTAL ANONYMITY** 
You are writing this specification for a developer who will build `[NEW_IMPORT_NAME]` completely from scratch. Your final specification MUST NOT mention `[ORIGINAL_IMPORT_NAME]` in any way. Act as if `[NEW_IMPORT_NAME]` is a brand new, independent project. Do not leak the original identity.

**CRITICAL RULE 2: EXHAUSTIVENESS (100% TEST PASS RATE)**
The developer will NOT have access to the test suite. They will ONLY have your specification. Therefore, you must extract the exact requirements from every single test, but you must extract the **underlying logic**, not just the test data. 

* **DO NOT** instruct the developer to hardcode specific test inputs and outputs (e.g., do NOT say "If input is 5, return 10").
* **DO** define the general behavior, formulas, formatting rules, or state changes that will naturally produce the expected outputs for any valid input (e.g., "The function must multiply the input by 2").
* If a test checks a specific boundary condition or edge case, define the logical rule for that boundary.
* If a test expects a specific Exception, define the exact logical condition that triggers it.
* If you leave out a single detail, the developer's code will fail the tests.

### Your Task
Read the provided test suite carefully. The tests define the exact expected behavior, public API, and edge cases of the library. 

Write a highly detailed, imperative prompt (e.g., "Write a library...", "Implement a class...") that instructs a developer on exactly how to build this library so that it passes every single test.

Your specification MUST include all the necessary ingredients:

1. **High-Level Goal:** A brief imperative summary of what the library must do.
2. **Module Structure:** The exact module name (`[NEW_IMPORT_NAME]`) and any required submodules implied by the imports.
3. **Classes & Functions:** Every public class, method, and function that the tests invoke.
4. **Signatures & Types:** Exact argument names, default values, and expected return types based on how the tests call them.
5. **Strict Behaviors & Rules:** Translate the tests into strict logical rules. What exactly must happen when specific inputs are provided? What specific Exceptions (e.g., `ValueError`, `TypeError`) must be raised, and under what exact conditions?
6. **Constants/Attributes:** Any public variables, properties, or constants the tests expect to read or modify.

### Formatting
* Use clear Markdown formatting (headers, bullet points, code blocks for signatures).
* Use the imperative mood ("Implement a function that...", "Raise a ValueError if...").
* **DO NOT** write the actual implementation code. Only write the specification.

### The Test Suite

```python
[TEST_CODE]
```