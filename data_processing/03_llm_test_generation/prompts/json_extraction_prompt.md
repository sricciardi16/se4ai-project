Excellent. Now, act as a strict data formatter. Your task is to convert the test specifications you just generated in your immediately preceding response into a JSON array.

**CRITICAL INSTRUCTIONS:**

1. **Zero Reasoning:** Do not summarize, alter, or improve the text. Copy the text verbatim from your previous response.
2. **Extract the Name:** For `test_name`, extract the string from the `###` header (remove the `###` and the backticks).
3. **Preserve Formatting:** The `crucial_data` field MUST be a single string. If your previous output contained nested bullet points or line breaks, preserve them exactly within that single string using newline characters (`\n`). Do not convert bullet points into a JSON array.
4. **Output ONLY JSON:** Output strictly a valid JSON array enclosed in markdown backticks (```json ... ```).

**REQUIRED JSON SCHEMA:**

```json
[
  {
    "test_name": "string",
    "target_api": "string",
    "behavioral_specification": "string",
    "crucial_data": "string"
  }
]
```

