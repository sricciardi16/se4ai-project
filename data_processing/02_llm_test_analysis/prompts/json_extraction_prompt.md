Review the behavioral extractions you just provided in your previous response. 

Your task is to act as a strict data parser and classifier. You will filter your previous extractions, sort the valid items by their true intent, and output a single, clean JSON object.

**CRITICAL INSTRUCTIONS:**

1. **Drop the Garbage:** 
   If an item has `Classification: [REJECTED INTERNAL IMPLEMENTATION]`, completely ignore it. Do not include it in the JSON.

2. **Classify the Valid Behaviors (Contextual Authority):**
   You must classify every `[VALID PUBLIC BEHAVIOR]` into one of two arrays. 
   **CRITICAL:** You are the domain expert. The exact boundary between "Functional" and "Robustness" depends heavily on the specific library's core purpose. Use your deep factual knowledge of this specific library to make the final judgment. Completely IGNORE the original test name when classifying. Trust only the behavior and the library's domain.
   * **`functional_behaviors` (The Contract & Domain Logic):** 
     The input satisfies the structural/type contract of the API (correct types, non-`None` where required, satisfies expected duck-typed protocols). The test verifies what the library does with the value — returns a result, returns `None`/`False`, or raises an exception in response to a domain rule violation. *Crucially, if handling a specific type of bad data, error, or edge case is a core, advertised feature of this specific library (e.g., a network library handling timeouts, or a parser handling malformed syntax), classify it here as expected domain logic.*

   * **`robustness_behaviors` (The Shield & Fault Tolerance):** 
    The input violates the structural/type contract (`None` for a required string, `int` for a `list`, or an object missing required duck-typed methods), or the execution environment is hostile in a way that is outside the library's primary domain (missing file, broken socket, concurrent mutation). The test verifies the library fails safely — no crash, no state corruption, no undefined behavior — regardless of whether the documentation explicitly defines behavior for these inputs.

   * **The Golden Rule of Thumb (Use this as a guide, but let the library's API dictate the final answer):** 
     If you are unsure, ask yourself: *"Is the value the wrong kind of thing, or just a bad instance of the right kind of thing?"*
     *  `None` instead of `str` → usually the wrong kind of thing → **Robustness** *(UNLESS the library explicitly advertises handling `None` gracefully as a feature)*
     *  `"abc"` instead of a valid email → bad instance of `str` → **Functional**
     *  `b"\xff\xfe"` instead of valid UTF-8 bytes → bad instance of `bytes` → **Functional**
     *  `123` instead of a `list` → usually the wrong kind of thing → **Robustness**
     *  `str` instead of a file-like object (missing `.read()`) → wrong kind of thing → **Robustness**
     
     **Your Ultimate Freedom:** If a library's core philosophy is to be hyper-flexible and accept any type of garbage input without complaining (e.g., a data-cleaning library), you have the authority to classify those type-mismatches as **Functional**. Trust your knowledge of the library.
   
3. **Generate a Semantic Test Name:**
   The original test names are often poorly formatted or violate Python testing conventions. Based on the "Behavioral Specification", generate a `new_test_name`. 
   * It MUST start with `test_`.
   * It MUST be in `snake_case`.
   * It MUST clearly and semantically describe what is being tested (e.g., `test_parse_invalid_string_raises_parser_error` or `test_merge_two_pdfs_preserves_page_count`).
   
4. **Copy Verbatim:** 
   Do NOT rewrite or summarize the text. Copy the exact text from your previous response into the corresponding JSON fields.
   * `original_test_name`: The name of the test (e.g., "test_sun_times_basic_sanity").
   * `target_api`: The text following "Target API:".
   * `behavioral_specification`: The text following "Behavioral Specification:".
   * `crucial_data`: The text following "Crucial Data / Edge Cases:".

4. **Strict JSON Output:** 
   Output ONLY valid JSON. Provide the output as a JSON object enclosed in markdown backticks (```json ... ```).

**REQUIRED JSON SCHEMA:**  
```json
{
  "functional_behaviors": [
    {
      "original_test_name": "string",
      "new_test_name": "string",
      "target_api": "string",
      "behavioral_specification": "string",
      "crucial_data": "string"
    }
  ],
  "robustness_behaviors": [
    {
      "original_test_name": "string",
      "new_test_name": "string",
      "target_api": "string",
      "behavioral_specification": "string",
      "crucial_data": "string"
    }
  ]
}
```

