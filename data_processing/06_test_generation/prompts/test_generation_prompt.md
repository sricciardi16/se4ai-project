Building on your factual knowledge of this repository, your task is to write a production-grade `pytest` suite. 

You will be provided with a specific Target Version of the library and a batch of test specifications. 

**Target Version:** `[TARGET_VERSION]`

**CRITICAL RULES - YOU MUST OBEY THESE STRICTLY:**

1. **VERSION SUPREMACY (ABSOLUTE LAW):** The Target Version provided above is absolute law. If a test specification describes a workflow, method, or behavior that conflicts with how `[TARGET_VERSION]` actually operates, **the version wins**. You must adapt, rewrite, or correct the test logic so it perfectly aligns with the factual reality of `[TARGET_VERSION]`.
2. **ANTI-LEGACY & IDIOMATIC ENFORCEMENT:** You must completely ignore backward compatibility. If the library allows multiple ways to achieve a goal, you must choose the **single, most standard, and idiomatic approach** specifically designed for `[TARGET_VERSION]`. Do not use deprecated wrappers or legacy patterns.
3. **STRICTLY BLACK-BOX:** You are an end-user. You are strictly FORBIDDEN from importing private modules, accessing internal variables (starting with `_`), or mocking internal state. You must test the public surface area only.
4. **CRUCIAL DATA ENFORCEMENT:** You must strictly implement the exact edge cases, hardcoded strings, and boundary values requested in the "Crucial Data" section of each specification.
5. **NAMING:** Use the exact string provided in the `###` header as the name of your Python test function.

**REQUIRED OUTPUT FORMAT:**
Output ONLY a single block of Python code enclosed in ```python ... ```. 
You must include all necessary `import` statements at the very top of the block. 

---

Here are the test specifications to implement:

[TEST_SPECIFICATIONS]