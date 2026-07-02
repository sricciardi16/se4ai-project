Project: `tabular_manager`


## 1. High-Level Goal
Build a Python library named `tabular_manager` for managing, manipulating, and exporting/importing tabular data. The library must support single-sheet datasets and multi-sheet databooks, with built-in support for format conversions (CSV, TSV, JSON, and XLSX). 

## 2. Module Structure
Create the following module structure:
* `tabular_manager/` (Root package)
  * `__init__.py` (Exposes public API)
  * `exceptions.py` (Contains custom exceptions)

### 2.1. Exceptions (`tabular_manager.exceptions`)
* **`UnsupportedFormat`**: Implement this as a custom exception inheriting from `Exception`. It must be raised whenever an invalid, unknown, or unsupported format string is provided to export/import methods.

### 2.2. Public API Exports
The root module (`tabular_manager`) must expose the following:
* `Dataset` (Class)
* `Databook` (Class)
* `import_set` (Function)
* `UnsupportedFormat` (Exception)

---

## 3. Core Classes & Functions

### 3.1. `Dataset` Class
Implement the `Dataset` class to represent a single table of data.

#### Initialization
* **Signature:** `def __init__(self, *args, headers=None, title=None):`
* **Behavior:** 
  * `*args` represents an arbitrary number of initial rows (iterables) to populate the dataset.
  * `headers` is an optional list of strings representing column names.
  * `title` is an optional string representing the name of the dataset (used as sheet names in multi-sheet exports).

#### Properties
* **`headers`**: Get or set the list of column headers.
* **`title`**: Get or set the title of the dataset.
* **`height`**: (Read-only) Return the integer number of rows currently in the dataset.
* **`width`**: (Read-only) Return the integer number of columns in the dataset.
* **`dict`**: (Read-only) 
  * If `headers` are set, return a list of dictionaries where each dictionary maps header names to the corresponding row values.
  * If `headers` are NOT set, return a list of the raw rows (lists/tuples).

#### Sequence Protocols (Magic Methods)
* **`__len__(self)`**: Return the number of rows (same as `height`).
* **`__getitem__(self, index)`**: 
  * If `index` is an integer or a slice, return the row(s) at that index as a `tuple` (or list of tuples for slices).
  * If `index` is a string, treat it as a header name and return an iterable (list or tuple) of all values in that specific column.

#### Row & Column Manipulation
* **`append(self, row, tags=None)`**: 
  * Append a new row (iterable) to the bottom of the dataset. 
  * Store the row internally such that it is returned as a `tuple` when accessed.
  * `tags` is an optional list of strings. Associate these tags with the appended row for later filtering.
* **`insert(self, index, row)`**: Insert a row (iterable) at the specified integer index.
* **`pop(self)`**: Remove and return the last row of the dataset as a `tuple`.
* **`append_col(self, col_data, header=None)`**: 
  * Append a new column to the right side of the dataset.
  * `col_data` is an iterable of values for the new column.
  * If `header` is provided, append it to the `headers` list.
  * **Rule:** If the length of `col_data` does not exactly match the current `height` of the dataset, raise an `Exception`.

#### Sorting & Filtering
* **`sort(self, key)`**: 
  * Return a **new** `Dataset` instance sorted by the specified key. Do **not** mutate the original dataset.
  * If `key` is a string, sort by the column with that header name. Raise a `KeyError` if the header does not exist.
  * If `key` is an integer, sort by the column at that index. Raise an `IndexError` if the index is out of bounds.
* **`filter(self, tag)`**: 
  * Return a **new** `Dataset` instance containing only the rows that were appended with the specified `tag` string. Do **not** mutate the original dataset.

#### Export & Import
* **`export(self, format)`**: 
  * Serialize the dataset into the requested format.
  * **Rule:** `format` must be strictly lowercase (e.g., `'csv'`, `'json'`). If the format is uppercase (e.g., `'CSV'`), empty, `None`, or unknown, raise `tabular_manager.exceptions.UnsupportedFormat`.
* **`load(self, payload, format=None)`**: 
  * **Rule:** Before loading new data, completely clear the dataset's existing state (remove all current rows and headers).
  * Parse the `payload` and populate the dataset's headers and rows.
  * If `format` is provided, parse using that format.
  * If `format=None`, auto-detect the format (JSON or CSV) from the payload string. The auto-detection must ignore leading and trailing whitespace.
  * If the format is unknown or the payload cannot be recognized, raise `UnsupportedFormat`.
  * Return `self` to allow method chaining.

---

### 3.2. `Databook` Class
Implement the `Databook` class to manage multiple `Dataset` objects (like sheets in an Excel workbook).

#### Initialization & Management
* **Signature:** `def __init__(self, sheets=None):`
  * `sheets` is an optional iterable of `Dataset` objects to initialize the databook.
* **`add_sheet(self, dataset)`**: Append a `Dataset` instance to the databook.
* **`sheets(self)`**: Return a list of the `Dataset` instances in the exact order they were added.

#### Export & Import
* **`export(self, format)`**: 
  * Serialize all sheets into a single multi-sheet format (e.g., `'json'`, `'xlsx'`).
  * **Rule:** If a single-sheet format is requested (e.g., `'csv'`, `'tsv'`), raise `UnsupportedFormat`.
* **`load(self, payload, format)`**: 
  * Parse a multi-sheet payload and populate the databook with `Dataset` objects.
  * Ensure that each reconstructed `Dataset` retains its original `title`, `headers`, and row data.

---

### 3.3. Module-Level Functions
* **`import_set(payload, format=None)`**: 
  * Create a new, empty `Dataset` instance.
  * Call its `load()` method with the provided `payload` and `format`.
  * Return the populated `Dataset` instance.
  * Must raise `UnsupportedFormat` if the payload is unrecognizable and `format=None`.

---

## 4. Format Serialization Rules

When implementing the `export` and `load` logic, you must strictly adhere to the following format-specific rules:

### CSV (`'csv'`)
* **Line Endings:** Must use `\r\n` (CRLF) for line separators.
* **Headers:** If headers exist, they must be the first row of the output.
* **Data Types:** CSV export and import must coerce all values to strings.
* **Escaping:** Must properly escape strings containing commas or quotes (standard CSV escaping rules).

### TSV (`'tsv'`)
* **Delimiter:** Must use the tab character (`\t`) as the delimiter.
* **Data Types:** Like CSV, TSV export and import must coerce all values to strings.

### JSON (`'json'`)
* **Structure (Dataset):** Serializes to a JSON array. If headers exist, it must be an array of JSON objects (dictionaries mapping headers to values).
* **Structure (Databook):** Serializes to a JSON structure capable of holding multiple sheets (e.g., an array of sheet objects containing titles and data).
* **Data Types:** Must preserve native Python types (integers, floats, booleans) and properly handle Unicode characters without corrupting them.

### Excel / Binary (`'xlsx'`)
* **Return Type:** Must return a binary byte stream (`bytes`), NOT a string.
* **Signature:** The byte stream must start with the standard ZIP file signature: `b'PK\x03\x04'`.
* **Multi-sheet:** When exporting a `Databook`, the `title` attribute of each `Dataset` must be used as the name of the corresponding sheet in the Excel file.