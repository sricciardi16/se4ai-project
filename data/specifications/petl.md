Project: `tabular_processor`


## 1. High-Level Goal
Implement a Python library named `tabular_processor` for processing tabular data. The library must support reading/writing CSVs, loading data from dictionaries, and performing SQL-like transformations (filtering, joining, sorting, adding fields). 

The core architectural requirements are **Strict Lazy Evaluation** and **Fluent Method Chaining**.

## 2. Module Structure
* **Main Module:** `tabular_processor`
* **Exceptions Submodule:** `tabular_processor.errors`

## 3. Core Architecture & Data Model

### 3.1 The Table Object
All data ingestion functions (`wrap`, `fromcsv`, `fromdicts`) and transformation functions must return a custom **Table Object**.
* **Iterable:** The Table Object must be iterable. When iterated, it must yield the header as the first row (a tuple/list of strings), followed by the data rows (tuples/lists of values).
* **Method Chaining:** The Table Object must expose *every* transformation and inspection function defined in this specification as an instance method. This allows fluent chaining (e.g., `table.rename(...).cut(...).select(...)`).

### 3.2 Strict Lazy Evaluation
* **Deferred Execution:** Transformation functions (e.g., `addfield`, `cut`, `select`) must **never** execute their logic or consume the underlying data iterator when called. They must return a new Table Object (a view or generator) immediately.
* **Triggering Execution:** Execution must only occur when the Table Object is explicitly consumed (e.g., by iterating over it, calling `list()`, or invoking terminal methods like `tocsv`, `data`, `dicts`, or `header`).

### 3.3 Short Row Handling
* If a data row has fewer elements than the header row, any missing fields requested by a transformation or inspection method must be evaluated as `None`.

### 3.4 The Record Object
* When a function passes a "row" to a callable (e.g., in `addfield` or `select`), or when returning records via `recordlookup`, the row must be wrapped in a Record object.
* **Dual-Indexing:** The Record object must support both string-based indexing (like a dictionary, using header names as keys) and integer-based indexing (like a standard tuple).

## 4. Exceptions
Implement the following exception in the `tabular_processor.errors` submodule:
* `FieldSelectionError`: Must be raised when a transformation attempts to access, cut, or rename a column name that does not exist in the header. **Rule:** Because of lazy evaluation, this exception must *only* be raised when iteration begins, not when the transformation function is initially called.

## 5. Public API Specification

Implement the following functions in the `tabular_processor` namespace. Ensure they are also available as methods on the Table Object.

### 5.1 Data Ingestion & I/O

*   **`wrap(iterable)`**
    *   **Behavior:** Wraps a standard Python iterable (e.g., a list of lists) into a Table Object. The first item is treated as the header.

*   **`fromcsv(filepath)`**
    *   **Behavior:** Opens and reads a CSV file, returning a Table Object. It must correctly parse standard CSV formatting (including commas inside quotes). All data must be read as strings.
    *   **Edge Case:** If the file does not exist, a `FileNotFoundError` must be raised *only* when the Table Object is iterated, not when `fromcsv` is called.

*   **`fromdicts(dicts)`**
    *   **Behavior:** Converts an iterable of dictionaries into a Table Object.
    *   **Header Generation:** It must perform a full pass over *all* dictionaries to accumulate a deduplicated list of *all* unique keys present in the dataset. These keys form the header.
    *   **Missing Values:** If a dictionary is missing a key present in the generated header, the value for that column in that row must be `None`.

*   **`tocsv(table, filepath)`**
    *   **Behavior:** Forces execution of the pipeline and writes the table (header and data) to a CSV file at the specified `filepath`.

### 5.2 Inspection & Extraction

*   **`header(table)`**
    *   **Behavior:** Returns the header row of the table as a tuple.
    *   **Constraint:** It must evaluate and consume *only* the first row of the underlying iterator. It must strictly halt evaluation before touching the first data row.

*   **`data(table)`**
    *   **Behavior:** Returns an iterator yielding only the data rows (excluding the header row).

*   **`dicts(table)`**
    *   **Behavior:** Returns an iterator of dictionaries, where each dictionary maps the header names to the corresponding values of a data row.
    *   **Edge Cases:** If a row is shorter than the header, missing keys must be assigned `None`. If the table contains only a header and no data, it must return an empty iterator.

*   **`recordlookup(table, key)`**
    *   **Behavior:** Returns a lookup object (e.g., a dictionary) mapping the values of the specified `key` column to a **list** of matching Record objects (see Section 3.4).

### 5.3 Transformations

*   **`cut(table, *fields)`**
    *   **Behavior:** Isolates and reorders columns based on the exact order of the provided `fields` arguments.
    *   **Exceptions:** Raises `FieldSelectionError` (lazily) if any requested field does not exist.

*   **`rename(table, old_name, new_name)` OR `rename(table, mapping_dict)`**
    *   **Behavior:** Renames one or more headers without altering the data rows. Must support being called with two strings (old, new) OR a single dictionary mapping old names to new names.
    *   **Exceptions:** Raises `FieldSelectionError` (lazily) if an old name does not exist in the header.

*   **`addfield(table, field_name, value_or_callable)`**
    *   **Behavior:** Appends a new column to the right side of the table.
    *   **Logic:** If the third argument is a callable, invoke it for each row, passing the Record object (see Section 3.4) as the single argument; the return value becomes the cell value. If it is not callable, use it as a static value for all rows.
    *   **Edge Case:** If `field_name` already exists in the header, do not overwrite it. Create a duplicate header name at the end of the row.

*   **`convert(table, field, callable)`**
    *   **Behavior:** Applies the provided `callable` to the existing value in the specified `field` column, replacing the original value with the return value of the callable.

*   **`select(table, callable)` OR `select(table, field, callable)`**
    *   **Behavior:** Filters rows. 
    *   **Logic:** If called with two arguments, pass the entire Record object to the callable. If called with three arguments, pass only the value of the specified `field` to the callable. Retain the row only if the callable returns a truthy value.

*   **`selecteq(table, field, value)`**
    *   **Behavior:** Retains rows where the value in `field` is strictly equal (`==`) to `value`.

*   **`selectin(table, field, value_set)`**
    *   **Behavior:** Retains rows where the value in `field` exists within the provided `value_set` (e.g., a `set` or `list`).

*   **`selectge(table, field, value)`**
    *   **Behavior:** Retains rows where the value in `field` is greater than or equal to (`>=`) `value`.

*   **`sort(table, key, reverse=False)`**
    *   **Behavior:** Sorts the data rows based on the values in the `key` column. If `reverse=True`, sort in descending order.

*   **`distinct(table)`**
    *   **Behavior:** Removes exact duplicate data rows, retaining only the first occurrence of each unique row.

*   **`stack(table1, table2)`**
    *   **Behavior:** Concatenates `table2` vertically beneath `table1`. The output must yield all rows of `table1` followed by all data rows of `table2`.

*   **`join(left_table, right_table, key)`**
    *   **Behavior:** Performs an inner join on the shared `key` column.
    *   **Output Structure:** The resulting header must be the shared key, followed by the remaining columns of the left table, followed by the remaining columns of the right table.
    *   **Logic:** Must support 1-to-many relationships (fan-out). Rows with keys that do not exist in both tables must be strictly excluded.

*   **`leftjoin(left_table, right_table, key)`**
    *   **Behavior:** Performs a left outer join on the shared `key` column.
    *   **Logic:** All rows from the left table must be preserved. If a matching key is not found in the right table, the resulting right-side columns for that row must be populated with `None`.