Project: `flexidb`


## 1. High-Level Goal
Implement a Python library named `flexidb` that provides a dynamic, schema-less, dictionary-based wrapper around SQLAlchemy. The library must automatically manage database connections, dynamically generate and alter table schemas based on inserted dictionary keys, and provide a simplified, Pythonic API for CRUD operations, querying, and transaction management.

## 2. Module Structure & Dependencies
*   **Module Name:** `flexidb`
*   **Underlying Engine:** The library must be built on top of `sqlalchemy`.
*   **Exposed Exceptions:** The library must allow standard SQLAlchemy exceptions (`ArgumentError`, `NoSuchModuleError`, `IntegrityError`, `OperationalError`) to bubble up naturally when underlying SQLAlchemy operations fail.

## 3. Core API: Connection Management

### `flexidb.connect(url: str)`
Implement a module-level function that establishes a database connection.
*   **Behavior:** 
    *   Accepts a standard SQLAlchemy database URL string.
    *   Automatically handles connection pooling and setup.
    *   Uses lazy-loading: the actual connection to the database engine should be deferred until an operation requires it (e.g., accessing the tables list).
    *   If connecting to a pre-existing database, it must automatically reflect the existing schema and tables.
*   **Returns:** An instance of the `Database` class.
*   **Exception Rules:**
    *   Raise `sqlalchemy.exc.NoSuchModuleError` if the URL scheme/dialect is unrecognized.
    *   Raise `sqlalchemy.exc.ArgumentError` if the connection string is empty (`""`).
    *   Raise `sqlalchemy.exc.ArgumentError` or `sqlalchemy.exc.OperationalError` if the protocol is malformed.
    *   Raise `sqlalchemy.exc.ArgumentError`, `sqlalchemy.exc.OperationalError`, or `ModuleNotFoundError` if the host/port is unreachable (this must trigger when forcing the connection, such as accessing the `.tables` property).

## 4. Class: `Database`
Implement a class representing the active database connection and schema.

### Properties & Attributes
*   **`tables` (property):** Returns a `list` of strings representing the names of all tables currently existing in the database.
*   **`engine` (attribute/property):** Exposes the underlying SQLAlchemy engine object (must support standard engine methods like `dispose()`).

### Methods
*   **`__getitem__(table_name: str)`:** 
    *   Allows bracket notation access (e.g., `db['users']`).
    *   **Behavior:** Returns a `Table` instance for the requested `table_name`. 
    *   **Staging Rule:** If the table does not exist in the database yet, it must return a valid `Table` object staged in memory. It MUST NOT create the table in the actual database or add it to the `tables` property list until data is actually inserted.
*   **`query(sql: str, **kwargs)`:**
    *   Executes a raw SQL query string.
    *   **Security/Binding Rule:** Must use SQLAlchemy-style named parameters (e.g., `:param_name`) in the SQL string. The `**kwargs` must be securely bound to these parameters to prevent SQL injection. Malicious strings passed via kwargs must be treated as literal values, not executable SQL.
    *   **Returns:** An iterator of dictionaries, where each dictionary represents a row.
*   **Transaction Management:**
    *   **`begin()`:** Starts a database transaction.
    *   **`commit()`:** Commits the current transaction.
    *   **`rollback()`:** Rolls back the current transaction.
    *   **Context Manager (`__enter__`, `__exit__`):** The `Database` object must function as a context manager (`with db:`). If an exception is raised inside the `with` block, it must automatically roll back the transaction. If the block completes successfully, it must commit.

## 5. Class: `Table`
Implement a class representing a single database table.

### Properties
*   **`name` (property):** Returns the string name of the table.
*   **`columns` (property):** Returns a `list` of strings representing the current column names in the table.

### Data Modification Methods
*   **`insert(row: dict)`:**
    *   **Dynamic Schema Rule:** If the dictionary contains keys that do not exist as columns in the table, the table schema must be dynamically altered to add these columns before inserting.
    *   **Primary Key Rule:** If the table is being created for the first time, it must automatically generate an integer primary key column named `id`.
    *   **Returns:** The auto-generated primary key (as an `int`) of the inserted row.
    *   **Exception Rule:** Raise `sqlalchemy.exc.IntegrityError` if the insert violates a UNIQUE constraint.
*   **`insert_many(rows: list[dict])`:**
    *   Accepts a list of dictionaries and inserts them all in a bulk operation.
*   **`update(row: dict, keys: list[str])`:**
    *   Updates existing records. The `keys` list specifies which dictionary keys to use as the `WHERE` clause to identify the record(s) to update.
    *   Must leave unspecified columns in the database unaffected.
    *   **Returns:** An `int` representing the number of rows modified.
*   **`upsert(row: dict, keys: list[str])`:**
    *   Checks if a record exists based on the columns provided in the `keys` list.
    *   If a matching record exists: Updates the record and returns the boolean `True`.
    *   If no matching record exists: Inserts the record and returns the new primary key as an `int`.
*   **`delete(**kwargs)`:**
    *   **Behavior with kwargs:** Deletes all rows matching the equality filters provided in `kwargs`. Returns the boolean `True` upon successful deletion.
    *   **Behavior without kwargs:** If called with no arguments (`table.delete()`), it must truncate/empty the entire table (row count drops to 0).
*   **`drop()`:**
    *   Completely drops the table from the database.
    *   After execution, the table's name must no longer appear in the parent `Database.tables` list.

### Querying & Retrieval Methods
*   **`all()`:**
    *   **Returns:** An iterator of dictionaries representing every row in the table. Every dictionary must include the auto-generated `id` key.
*   **`find(**kwargs)`:**
    *   Filters records based on the provided keyword arguments (combined using AND logic).
    *   **Null Rule:** If a kwarg value is `None`, it must translate to an `IS NULL` SQL query.
    *   **Advanced Operators Rule:** Must support dictionary-based comparison operators as values (e.g., `age={">=": 40}`).
    *   **Pagination & Sorting Rules:** Must accept and process the following special kwargs:
        *   `order_by` (str): Sorts the results ascending by the specified column.
        *   `_limit` (int): Limits the maximum number of returned rows.
        *   `_offset` (int): Skips the first N rows.
    *   **Returns:** An iterator of dictionaries representing the matching rows.
*   **`find_one(**kwargs)`:**
    *   Applies the same filtering logic as `find()`.
    *   **Returns:** A single dictionary representing the first matching row. If no records match, it MUST return `None`.
*   **`distinct(column_name: str)`:**
    *   **Returns:** An iterator of dictionaries, where each dictionary contains a single key-value pair representing a unique value found in the specified column (e.g., `[{"city": "New York"}, {"city": "Los Angeles"}]`).

### Utility Methods
*   **`__len__()` and `count()`:**
    *   Both methods must return the total number of rows currently in the table as an `int`.
*   **`create_index(columns: list[str])`:**
    *   Creates a database index on the specified list of column names.
*   **`has_index(columns: list[str])`:**
    *   **Returns:** A boolean indicating whether an index currently exists for the exact specified list of column names.