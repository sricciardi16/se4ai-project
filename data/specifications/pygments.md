Project: `code_styler`


## 1. High-Level Goal
Implement a syntax highlighting library named `code_styler`. The library must parse source code strings into categorized tokens using language-specific **Lexers**, and then render those tokens into various output formats (like HTML or ANSI terminal text) using **Formatters**.

## 2. Module Structure
You must create the following package structure and expose the specified classes and functions so they can be imported exactly as shown:

*   `code_styler` (Root package)
    *   `__init__.py` (Must expose `highlight` and `lex`)
    *   `util.py`
    *   `token.py`
    *   `lexer.py`
    *   `lexers.py`
    *   `formatters.py`

---

## 3. Core Components & Strict Behaviors

### 3.1. Exceptions (`code_styler.util`)
*   **`ClassNotFound`**: Implement a custom exception class inheriting from `Exception`. This will be raised when a requested lexer or formatter cannot be found.

### 3.2. Tokens (`code_styler.token`)
*   **`Token`**: Implement a hierarchical namespace or dynamic object named `Token`. 
    *   **Rule:** It must support chained attribute access to represent token types (e.g., `Token.Keyword`, `Token.Name.Function`). 
    *   **Rule:** These attributes must resolve to unique identifiers (strings or objects) that can be yielded by lexers and recognized by formatters.

### 3.3. Lexers (`code_styler.lexer` & `code_styler.lexers`)
*   **`Lexer`** (`code_styler.lexer`): Implement a base class for all lexers.
    *   **Rule:** The constructor (`__init__`) must accept arbitrary keyword arguments (`**kwargs`).
    *   **Rule:** It must accept and store a boolean `stripall` keyword argument (defaulting to `False`).
    *   **Rule:** Every lexer instance must have a `name` attribute (a string representing the human-readable language name).

*   **Specific Lexer Implementations** (`code_styler.lexers`):
    Implement subclasses of `Lexer` for various languages. At a minimum, you must implement lexers that correspond to the following `name` attributes:
    *   `PythonLexer` (name: `'Python'`)
    *   JSON Lexer (name: `'JSON'`)
    *   HTML Lexer (name: `'HTML'`)
    *   Bash Lexer (name: `'Bash'`)
    *   JavaScript Lexer (name: `'JavaScript'`)

*   **`get_lexer_by_name(alias: str, **kwargs)`** (`code_styler.lexers`):
    Implement a factory function that returns an instantiated lexer based on a string alias.
    *   **Rule:** Pass any `**kwargs` directly to the lexer's constructor.
    *   **Rule:** Map the alias `"python"` and `"py"` to the Python lexer.
    *   **Rule:** Map the alias `"json"` to the JSON lexer.
    *   **Rule:** Map the aliases `"javascript"` and `"html"` to their respective lexers.
    *   **Rule:** If the alias is an empty string (`""`) or an unknown string (e.g., `"not-a-real-language-12345"`), raise a `code_styler.util.ClassNotFound` exception.

*   **`guess_lexer(text: str, **kwargs)`** (`code_styler.lexers`):
    Implement a function that infers the correct lexer by analyzing the content of the source code string.
    *   **Rule:** If the text contains a Python shebang (e.g., `#!/usr/bin/env python`), return a Python lexer instance.
    *   **Rule:** If the text contains a Bash shebang (e.g., `#!/bin/bash`), return a Bash lexer instance.
    *   **Rule:** If the text contains an HTML doctype (e.g., `<!DOCTYPE html>`), return an HTML lexer instance.

### 3.4. Formatters (`code_styler.formatters`)
*   **Base Formatter Concept**: All formatters must accept `**kwargs` in their constructor. Every formatter instance must have an `aliases` attribute (a list, tuple, or set of strings) containing the valid aliases used to look it up.

*   **`HtmlFormatter`**: Implement a formatter that outputs HTML.
    *   **Rule:** It must wrap tokens in `<span>` tags with a `class=` attribute corresponding to the token type.
    *   **Rule:** Specifically, it must map Python keyword tokens (like `def`) to the CSS class `"k"` (e.g., `<span class="k">def</span>`).
    *   **Rule:** If instantiated with `full=True`, the output must be wrapped in a complete HTML document structure containing `<!DOCTYPE html`, `<html>`, `<body>`, and `</body></html>`.
    *   **Rule:** If `full=True` is provided but the input source code is an empty string, it must return *only* the HTML boilerplate without any `<span>` tags.
    *   **Rule:** If instantiated with `linenos=True`, the output must include HTML elements that contain the string `"lineno"` to represent line numbers.
    *   **Rule:** If instantiated with `style='monokai'`, the output must include inline CSS or a `<style>` block containing the Monokai background hex color `"272822"`.
    *   **Rule:** Implement a method `get_style_defs(self, selector: str) -> str`. This method must return a string of CSS definitions. The returned CSS must include the provided `selector` (e.g., `".highlight"`) and standard CSS styling properties (must include at least one of `color:`, `background:`, or `background-color:`).

*   **Other Formatters**:
    *   **Terminal Formatter**: Must output ANSI escape sequences (e.g., strings containing `\x1b[`).
    *   **Text Formatter**: Must output plain text without any markup.

*   **`get_formatter_by_name(alias: str, **kwargs)`**:
    Implement a factory function that returns an instantiated formatter based on a string alias.
    *   **Rule:** Pass any `**kwargs` directly to the formatter's constructor.
    *   **Rule:** Map `"html"` to the `HtmlFormatter`. Ensure `'html'` is in its `aliases` attribute.
    *   **Rule:** Map `"terminal"` and `"terminal256"` to terminal formatters. Ensure `'terminal256'` is in the respective formatter's `aliases` attribute.
    *   **Rule:** Map `"latex"` to a LaTeX formatter. Ensure `'latex'` is in its `aliases` attribute.
    *   **Rule:** Map `"text"` to the plain text formatter.
    *   **Rule:** If the alias is an empty string (`""`) or an unknown string (e.g., `"fake-formatter-xyz"`), raise a `code_styler.util.ClassNotFound` exception.

### 3.5. Core API (`code_styler`)
*   **`lex(code: str, lexer: Lexer)`**:
    Implement a function (or generator) that processes source code.
    *   **Rule:** It must return an iterable (e.g., a list or generator) of tuples.
    *   **Rule:** The first element of each tuple must be a `Token` type (e.g., `Token.Keyword`).
    *   **Rule:** If the provided `lexer` was instantiated with `stripall=True`, this function must strip all leading and trailing whitespace from the `code` string *before* generating tokens.

*   **`highlight(code: str, lexer: Lexer, formatter, outfile=None)`**:
    Implement the main orchestration function.
    *   **Rule:** It must use the `lexer` to tokenize the `code`, and the `formatter` to format those tokens.
    *   **Rule:** If `outfile` is `None` (the default), the function must return the final formatted output as a string.
    *   **Rule:** If `outfile` is provided (expect a file-like object, such as `io.StringIO`), the function must write the formatted output to `outfile` using `outfile.write()` and **must return `None`**.