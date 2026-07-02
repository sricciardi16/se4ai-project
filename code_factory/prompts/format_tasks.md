### Required Schema

```json
[
  {
    "task_name": "string (snake_case)",
    "task_type": "string (must be exactly 'scaffold', 'implement', or 'execute')",
    "target_file": "string (file path, or empty string if omitted)",
    "description": "string (preserve formatting with \\n)"
  }
]
```

### Text Input

{markdown_text}