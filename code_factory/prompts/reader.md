Your task is to analyze a source code file and extract context based on a provided list of questions, organizing the answers into logical Findings.

# Input

You will be provided with:

1. **Source Code:** The complete text of a single file.
2. **Questions:** A list of questions detailing the context required from this file.

# Output

Produce a report of Findings. You are not required to answer the questions sequentially; instead, use them as a lens to locate relevant information and organize it into logical Findings.

When processing the questions:

- If the file contains no relevant information, or if all conditional questions evaluate to false, output exactly and only the word: `NO_FINDINGS`.
- If a question is prefixed with a condition (e.g., `If X:`), evaluate it against the source code. If the condition is false, ignore that question.
- **Ensure that all questions are fully answered.** So, for example, if a question asks for the complete source code, you must make sure that the resulting Finding contains the entire unmodified file, without omitting any methods or lines.

## Output Format

If relevant context is found, present your report using the following structure for each Finding. 

**[Descriptive Name of the Finding]**

[An explanation of the logic and how it relates to the requested context]

```[language]
[Code snippet extracted from the source. Do not modify, truncate, or write pseudo-code.]
```

**[Descriptive Name of the Next Finding]**

[An explanation...]

```[language]
[Code...]
```

