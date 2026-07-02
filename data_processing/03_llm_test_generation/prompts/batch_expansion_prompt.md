Excellent. Now we will expand a specific batch of the guarantees you just listed into rigorous, implementation-agnostic test specifications.

Please process ONLY items **[START_INDEX]** through **[END_INDEX]** from your numbered list above.

To generate test specifications with the required level of rigor and semantic quality, you must adopt a specific mindset: **Contract-Driven Test Design**. The goal is to create a specification so precise and unambiguous that if you gave it to ten different programmers, they would all write functionally identical tests. It leaves zero room for creative interpretation.

Here are the rules, semantic structures, and the underlying approach you MUST use:

### 1. The "Target API" Rule: Pinpoint the Surface Area

**The Approach:** Never test "a library" or a vague concept. Test a specific, isolated chain of function calls. 
**The Rule:** Identify the exact classes, methods, or properties that must be invoked to complete the workflow.

*   *Bad:* "Test that downloading a webpage works."
*   *Good:* `requests.Session.get, requests.Response.status_code, requests.Response.text`

### 2. The "Test Name" Rule: Action + Observable Outcome

**The Approach:** The name of the test must serve as a micro-summary of the entire specification.
**The Rule:** Use the semantic structure: `test_<action_or_trigger>_<observable_result>`.

*   *Example:* `test_parse_invalid_string_raises_parser_error`

### 3. The "Behavioral Spec" Rule: The Cause-and-Effect Contract

**The Approach:** Write the specification as a strict, black-box contract. Do not describe *how* the code works internally; describe *what* happens when a user interacts with it.
**The Rule:** Use a strict **"When [Action], it should/must [Verifiable Result]"** semantic structure.

*   *Example:* "When a PDF file is loaded using `PdfReader`, the `pages` attribute should contain a sequence whose length exactly matches the total number of pages."

### 4. The "Crucial Data" Rule: The Anchor of Reality

**The Approach:** Generic tests (using data like `"test"`, `1`, or `"foo"`) are weak and often miss bugs. 
**The Rule:** Mandate specific, hardcoded edge cases, boundary values, or complex strings that prove the logic actually executed correctly.

*   *Time Edge Cases:* "Must test with a leap year date: `2020-02-29`."
*   *Encoding Edge Cases:* "Must test with non-ASCII characters: `影師嗎`."

### 5. The Architectural Test Patterns

Apply these patterns where appropriate based on the guarantee:

*   **The "Roundtrip" Pattern:** "When X is converted to Y and back to X, the final output must be identical to the original input."
*   **The "State Mutation" Pattern:** "When X is modified/deleted, querying X must reflect the change, and Y must remain completely unaffected."
*   **The "Graceful Failure" Pattern:** "When the API is provided with strictly invalid input [Crucial Data], it must safely raise [Specific Exception]."
*   **The "Lifecycle" Pattern:** "When the lifecycle is initiated and subsequently terminated, the underlying resources must be cleanly released."

---

### Required Output Format

Do not write introductory or concluding remarks. For each item in the requested batch, output strictly in the following Markdown format:

### `[Test Name]`

* **Target API:** (Which exact public functions, classes, or methods are invoked?)
* **Behavioral Specification:** (Describe exactly what is being tested using the "When... it should..." structure.)
* **Crucial Data / Edge Cases:** (Provide the exact hardcoded strings, numbers, or configurations that make this test valuable.)

