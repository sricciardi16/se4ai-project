I am now providing you with a suite of functional tests written for this library. 

**Your objective is Behavior-Driven Extraction.** I want you to analyze the *intent* behind each test and extract a clean, implementation-agnostic specification that we can use later to write perfect black-box tests.

Treat the API Contract you generated earlier as a baseline, BUT expand your Source of Truth to include your factual knowledge of the library. If a test targets a legitimate, documented public API feature that you know exists (even if it was omitted from your earlier summary), it is valid. 

Evaluate **every single test function** in the provided code and categorize it into one of two buckets:

**Bucket A: [VALID PUBLIC BEHAVIOR]**
The test intends to verify a feature, edge case, or workflow that belongs to the public API contract. Even if the original author used dirty code, internal mocks, or private tree traversal to achieve it, the *underlying concept* is valid and must be salvaged.

**Bucket B: [REJECTED INTERNAL IMPLEMENTATION]**
The test's fundamental goal is to verify internal state, private variables, legacy fallbacks, or undocumented architecture. It cannot be salvaged because the concept itself violates black-box testing.

---

### Required Output Format

Do not write introductory or concluding remarks. Output strictly in the following format for each test:

### `[Original Test Name]`
**Classification:** `[VALID PUBLIC BEHAVIOR]` or `[REJECTED INTERNAL IMPLEMENTATION]`

*(If VALID PUBLIC BEHAVIOR, provide the following):*
* **Target API:** (Which public function, class, or method is the focus of this test?)
* **Behavioral Specification:** (Describe exactly what is being tested in plain English. E.g., "When function X is called with argument Y, it should produce Z.")
* **Crucial Data / Edge Cases:** (Extract any specific hardcoded strings, numbers, or configurations that make this test valuable. E.g., "Must test with leap year date: 2020-02-29" or "Must test with Chinese characters to verify unicode preservation.")

*(If REJECTED INTERNAL IMPLEMENTATION, provide the following):*
* **Justification:** (Explain exactly why the core intent of this test violates black-box principles, making it invalid for our benchmark.)

---
Here is the original test code:
```python
[INSERT TEST CODE HERE]
```