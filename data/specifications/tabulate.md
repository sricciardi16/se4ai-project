Project: `tabular_formatter`


## 1. High-Level Goal
Implement a Python library named `tabular_formatter` that converts 2D data structures (lists of lists, lists of dictionaries, dictionaries of iterables) into highly customizable, formatted plain-text tables. The library must support multiple output formats (e.g., Markdown, HTML, LaTeX, ASCII grids), text wrapping, column alignment, and custom data formatting.

## 2. Module Structure & Exports
Create a module named `tabular_formatter`. The module must publicly export the following:
*   **`tabulate`**: The primary function for generating tables.
*   **`SEPARATING_LINE`**: A constant sentinel object (e.g., an instance of a dummy class) used to inject horizontal dividers into data rows.
*   **`tabulate_formats`**: A list of strings containing all supported table format identifiers.

## 3. Constants & Attributes
### `tabulate_formats`
Define a public list of strings named `tabulate_formats`. 
*   It must contain at least the following format identifiers: `"plain", "simple", "github", "grid", "fancy_grid", "pipe", "orgtbl", "jira", "presto", "pretty", "html", "latex", "tsv"`.
*   Every string in this list must be a valid argument for the `tablefmt` parameter in the `tabulate` function.

### `SEPARATING_LINE`
Define a public constant named `SEPARATING_LINE`. 
*   When this exact object is passed as a row within the input data, the function must render a format-specific horizontal divider line (e.g., a line of `+` and `-` characters in grid formats) spanning the entire width of the table at that exact row index.

## 4. The `tabulate` Function
Implement the core function with the following signature and default behaviors:

```python
def tabulate(
    tabular_data, 
    headers=None, 
    tablefmt="simple", 
    floatfmt="g", 
    missingval="", 
    showindex=False, 
    disable_numparse=False, 
    colalign=None, 
    maxcolwidths=None
) -> str:
```

### 4.1. Data Parsing & Validation Rules
*   **Valid Inputs:** Accept iterables of iterables (e.g., lists of lists), lists of dictionaries, and dictionaries of iterables.
*   **Invalid Inputs:** Raise a `TypeError` immediately if `tabular_data` is a non-iterable scalar (e.g., `int`, `bool`) or a generic `object()`.
*   **Empty Data:** 
    *   If `tabular_data` is empty (e.g., `[]`, `()`, `{}`) and no explicit headers are provided, return an empty string `""`.
    *   If `tabular_data` is empty but explicit `headers` are provided, return a string containing *only* the rendered header row and its associated borders/markup for the requested `tablefmt` (e.g., in `grid` format, render the top border, header text, bottom header border, and closing bottom border).
*   **Uneven Rows:** Calculate the maximum number of columns across all rows. Pad any shorter rows with the `missingval` string so that all rows have the same number of columns.
*   **Mixed Types:** Gracefully handle rows containing mixed data types (integers, strings, booleans, floats) by converting them to strings during rendering.

### 4.2. Header Resolution Rules (`headers`)
*   **Explicit Iterable:** If `headers` is a list or tuple of strings (e.g., `["Name", "Age"]`), render them as the top header row.
*   **`"firstrow"`:** If `headers="firstrow"`, extract the first row of `tabular_data` to use as the header row. Remove this row from the data body.
*   **`"keys"`:** If `headers="keys"`:
    *   If `tabular_data` is a dictionary of iterables, extract the dictionary keys as the headers and use the iterables as the column data.
    *   If `tabular_data` is a list of dictionaries, extract the keys from the dictionaries as the headers.
*   **Default Behavior:** If `headers` is omitted or `None`, do *not* render a header row. Do *not* implicitly extract keys from dictionaries; treat dictionaries as standard data rows.

### 4.3. Indexing Rules (`showindex`)
*   **Boolean `True`:** If `showindex=True`, prepend a new column at index 0 containing a 0-based integer counter for the data rows.
*   **Custom Iterable:** If `showindex` is an iterable (e.g., `["row_a", "row_b"]`), prepend a new column at index 0 using the values from the provided iterable.
*   **Boolean `False`:** If `showindex=False` (the default), do not prepend an index column.

### 4.4. Value Formatting Rules
*   **Missing Values:** Replace any `None` values in the data with the string provided in `missingval`.
*   **Numeric Parsing:** By default, attempt to parse string values to determine if they are numeric. If they are numeric, apply numeric alignment (right-aligned).
*   **`disable_numparse`:** If `disable_numparse=True`, bypass numeric parsing. Treat numeric strings (e.g., `"001"`, `"12.3400"`) strictly as text, preserving their exact characters and applying standard string alignment (left-aligned).
*   **Float Formatting (`floatfmt`):** 
    *   Format floating-point numbers according to the provided format specifier (e.g., `".2f"`).
    *   If `floatfmt` is a single string, apply it globally to all float values.
    *   If `floatfmt` is an iterable of strings (e.g., `("", ".4f")`), apply the formats positionally to each respective column.
    *   Default formatting must support scientific notation for very large numbers (e.g., `1.9891e+09`).

### 4.5. Alignment & Width Rules
*   **Default Alignment:** Left-align strings and right-align numbers. Pad cells with spaces to match the width of the widest cell in that column.
*   **Custom Alignment (`colalign`):** If `colalign` is provided as an iterable of strings (e.g., `("right", "left")`), override the default type-based alignment for each respective column.
*   **Text Wrapping (`maxcolwidths`):** 
    *   If `maxcolwidths` is provided as an iterable (containing integers or `None`), constrain the width of the respective columns.
    *   If a cell's text exceeds the specified integer width, wrap the text at word boundaries into multiple lines by inserting newline (`\n`) characters within the cell. Ensure no single line of text within that column exceeds the maximum width.

### 4.6. Table Format Styles (`tablefmt`)
Implement rendering logic for the following specific formats:
*   **`plain`:** Render data with no borders or separator lines. Separate rows with exactly one newline (`\n`).
*   **`simple` (Default):** Render headers separated from data by a line of dashes (e.g., `------`). Include a matching line of dashes at the bottom of the table.
*   **`github`:** Render a Markdown-compatible table using pipe (`|`) delimiters.
*   **`pipe`:** Render a Markdown-compatible table using pipe (`|`) delimiters and alignment indicators (e.g., `|:---|---:|`).
*   **`grid`:** Render an ASCII grid table using `+` for intersections, `-` for horizontal lines, and `|` for vertical lines.
*   **`html`:** Render standard HTML table tags (`<table>`, `<tbody>`, `<tr>`, `<td>`).
*   **`latex`:** Render standard LaTeX table syntax (`\begin{tabular}`, `&` for column separation, `\\` for row termination).
*   **`tsv`:** Render tab-separated values (`\t` between columns).