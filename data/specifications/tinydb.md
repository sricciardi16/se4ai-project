Project: `docstore`


## 1. High-Level Goal
Implement a lightweight, document-oriented, NoSQL-like database library in Python named `docstore`. The library must store documents (Python dictionaries) either in memory or persistently in a local JSON file. It must support multiple isolated tables, CRUD operations, and a robust, chainable querying API.

## 2. Module Structure
Create the following module structure:
* `docstore/` (Main package)
  * `__init__.py` (Must export `TinyDB`, `Query`, and `where`)
  * `storages.py` (Must export `MemoryStorage`)

## 3. Storage Backend & JSON Schema
### JSON Schema
When persisting to a file, the data must be serialized as JSON. The root of the JSON file must be a dictionary where the keys are table names. The default table name must be `"_default"`. The values for each table must be dictionaries mapping **stringified integer IDs** to the document dictionaries.
* **Example Schema:** `{"_default": {"1": {"name": "Alice"}, "2": {"name": "Bob"}}}`

### `docstore.storages.MemoryStorage`
* Implement a class named `MemoryStorage`.
* It must act as a storage backend that keeps all data in memory (e.g., using a Python dictionary) rather than writing to disk. It must mimic the exact same schema structure as the file storage.

## 4. Core Database Class: `TinyDB`
Implement the main database class named `TinyDB`. 

### Initialization & Lifecycle
* **`__init__(self, path_or_storage, *args, **kwargs)`**
  * If the first argument is a string or `pathlib.Path`, treat it as a file path.
    * If the file exists, parse the JSON and load the state.
    * If the file does not exist, create it.
    * **Exception:** Raise an `OSError` if the path points to a directory, or if the parent directory does not exist.
  * If initialized with the keyword argument `storage=MemoryStorage`, use the in-memory backend instead of file I/O.
* **Context Manager (`__enter__`, `__exit__`)**
  * Support the `with` statement.
  * `__exit__` must safely close the underlying file resource.
  * **Exception:** Any I/O operation (like `insert`) attempted after the database is closed must raise a `ValueError` with the exact message: `"I/O operation on closed file"`.
* **`close(self) -> None`**
  * Closes the underlying file resource.

### Table Management
* **`table(self, name: str) -> Table`**
  * Returns a Table object representing an isolated collection of documents.
  * Operations on one table must have zero effect on other tables.
* **`tables(self) -> set | list`**
  * Returns a collection (set or list) of the names of all currently populated tables.
* **Default Table:** All CRUD methods called directly on the `TinyDB` instance must implicitly operate on the `"_default"` table.

### CRUD Operations (Applies to `TinyDB` and `Table` objects)
* **`insert(self, document: dict) -> int`**
  * Inserts a dictionary into the table.
  * Generates and returns a unique integer ID for the document.
  * **Exception:** Raise a `TypeError` if the document contains unserializable data (e.g., `datetime` objects, `set`s, or custom objects).
* **`insert_multiple(self, documents: Iterable[dict]) -> list[int]`**
  * Inserts multiple documents and returns a list of their generated unique integer IDs.
  * **Edge Case:** If the iterable is empty, return an empty list `[]` immediately. Do not perform any write operations, and do not mutate the file size or storage state.
* **`all(self) -> list[dict]`**
  * Returns a list of all documents in the table.
* **`__len__(self) -> int`**
  * Returns the total number of documents in the table.
* **`get(self, condition=None, doc_id: int = None) -> dict | None`**
  * If `doc_id` is provided: Return the exact document dictionary matching the integer ID, or `None` if it does not exist.
  * If `condition` is provided: Return the *first* document dictionary that satisfies the condition, or `None` if no documents match.
* **`search(self, condition) -> list[dict]`**
  * Returns a list of all document dictionaries that satisfy the provided condition.
  * If no documents match, return an empty list `[]`.
* **`update(self, payload: dict, condition=None, doc_ids: list[int] = None) -> list[int]`**
  * Merges the `payload` dictionary into all documents matching the `condition` OR matching the IDs in `doc_ids`.
  * Existing fields not in the payload must be preserved. New fields in the payload must be added.
  * Returns a list of the integer IDs of the updated documents.
  * If no documents match, return an empty list `[]` and do not modify the database state.
* **`remove(self, condition=None, doc_ids: list[int] = None) -> list[int]`**
  * Deletes all documents matching the `condition` OR matching the IDs in `doc_ids`.
  * Returns a list of the integer IDs of the removed documents.
  * **Exception:** If called with zero arguments (neither condition nor doc_ids), raise a `RuntimeError`.
* **`contains(self, condition) -> bool`**
  * Returns `True` if at least one document matches the condition, otherwise `False`.
* **`count(self, condition) -> int`**
  * Returns the integer count of documents that match the condition.
* **`truncate(self) -> None`**
  * Removes all records from the specific table, leaving the table empty (length 0).
  * Must preserve the underlying file and other tables.

## 5. Querying API: `Query` and `where`
Implement a `Query` class that allows users to build evaluation conditions using Python's magic methods.

### `Query` Class Mechanics
* **Attribute Access:** Accessing an attribute on a `Query` instance (e.g., `Query().age`) must capture the field name and return a chainable query object.
* **Missing Keys:** If a query evaluates a field that does not exist in a given document, the condition must safely evaluate to `False`. It must **never** raise a `KeyError` or `AttributeError`.
* **Operators:** Implement magic methods on the query object to support standard Python operators. They must return a condition object that can be evaluated against a document:
  * `==` (Equality)
  * `!=` (Inequality)
  * `>` (Greater than)
  * `>=` (Greater than or equal to)
  * `<` (Less than)
  * `<=` (Less than or equal to)

### `Query` Methods
The query object must support the following method calls to generate specific conditions:
* **`exists(self)`**
  * Evaluates to `True` if the queried key exists in the document, regardless of its value.
* **`matches(self, pattern: str, flags: int = 0)`**
  * Evaluates to `True` if the string value of the field matches the provided Regex pattern. Must support standard `re` flags (e.g., `re.IGNORECASE`).
* **`test(self, func: Callable)`**
  * Passes the field's value to the provided custom callable `func`. Evaluates to `True` if the callable returns a truthy value.
* **`any(self, condition_or_value)`**
  * Assumes the field in the document is a list.
  * If passed a raw value (e.g., `"editor"`), evaluates to `True` if that value exists anywhere in the list.
  * If passed a nested `Query` condition (e.g., `Query().score >= 90`), evaluates to `True` if *any* dictionary element within the list satisfies the nested condition.

### `where` Function
* Implement a function named `where(field_name: str)`.
* It must act as an exact shorthand for `Query().<field_name>`. For example, `where("city") == "Tokyo"` must produce the exact same condition object as `Query().city == "Tokyo"`.