Project: `typed_orm`


## 1. High-Level Goal
Implement a Python Object-Relational Mapping (ORM) library named `typed_orm`. This library must seamlessly bridge data validation (via Pydantic) and database interactions (via SQLAlchemy). It must allow developers to define a single class that acts as both a data validation model and a database schema definition.

## 2. Module Structure
The library must be importable as `typed_orm` and expose the following public API at its root level:
*   `SQLModel` (Base Class)
*   `Field` (Function)
*   `Relationship` (Function)
*   `Session` (Class)
*   `create_engine` (Function)
*   `select` (Function)

---

## 3. Core Components & Strict Behaviors

### 3.1. `SQLModel` (Base Class)
Implement `SQLModel` as the foundational base class for all models. It must inherit from or fully replicate the behavior of a Pydantic `BaseModel` while conditionally integrating with SQLAlchemy's declarative mapping.

**Class Definition Rules:**
*   **The `table` flag:** The class must accept a boolean keyword argument `table` during subclassing (e.g., `class Hero(SQLModel, table=True):`).
*   **When `table=True`:**
    *   The class must be registered as a SQLAlchemy table within a shared `SQLModel.metadata` attribute (which must be a `sqlalchemy.MetaData` instance).
    *   The class must require at least one field marked as a primary key.
    *   If the `__tablename__` attribute is not explicitly defined, the library must automatically generate the table name by converting the class name to lowercase (e.g., `HeroTable` becomes `"herotable"`).
*   **When `table=False` (or omitted):**
    *   The class must act strictly as a data validation model.
    *   It MUST NOT be added to `SQLModel.metadata.tables`.
    *   It must still support instantiation and validation.

**Instantiation & Validation Rules:**
*   **`model_validate(payload: dict)`:** Must parse and validate a dictionary into a model instance.
    *   Raise `pydantic.ValidationError` if a required field is missing.
    *   Raise `pydantic.ValidationError` if a value cannot be coerced into the declared type (e.g., passing a string to an integer field).
    *   Raise `pydantic.ValidationError` if a value violates a field constraint (e.g., `min_length`, `max_length`).
*   **Default Values:** If a field has a default value defined via `Field(default=...)` or a standard assignment, instantiation must succeed even if that field is omitted from the input.
*   **Serialization (`.dict()`):** Instances must expose a `.dict()` method that returns a standard Python dictionary. This dictionary must exactly preserve special data types (e.g., `datetime` objects, booleans, `None`) and Unicode strings without altering them.

**Type Hinting & Schema Generation Rules:**
*   **Nullability:** 
    *   If a field's type hint is wrapped in `Optional[...]` (e.g., `Optional[str]`), the generated database column must be `nullable=True`.
    *   If a field's type hint is strict (e.g., `str`), the generated database column must be `nullable=False`.

### 3.2. `Field` (Function)
Implement a `Field` function used to configure both validation rules and database column properties simultaneously.

**Signature & Argument Mapping:**
*   `default`: Sets the default value for the attribute. Can be `None`.
*   `primary_key` (bool): If `True`, marks the generated database column as the primary key.
*   `foreign_key` (str): If provided (e.g., `"table_name.id"`), generates a SQLAlchemy `ForeignKey` constraint linking to the specified table and column.
*   `index` (bool): If `True`, creates a database index for this column.
*   `unique` (bool): If `True`, applies a `UNIQUE` constraint to the database column.
*   `max_length` (int): Must enforce a maximum string length during validation AND set the maximum length on the database column type (e.g., `VARCHAR(N)`).
*   `min_length` (int): Must enforce a minimum string length during validation.

### 3.3. `Relationship` (Function)
Implement a `Relationship` function to define ORM-level relationships between `table=True` models.

**Behavior:**
*   Accepts a `back_populates` string argument, which specifies the attribute name on the related model to establish a bidirectional relationship.
*   When accessed on an instance, it must dynamically resolve and return the linked model instance(s):
    *   For a "Many" side (type hinted as `List[Model]`), it must return a list of related instances.
    *   For a "One" side (type hinted as `Optional[Model]`), it must return the single related instance or `None`.

### 3.4. `create_engine` (Function)
Implement a function that initializes the database connection.

**Behavior:**
*   Must accept a database URL string as the first positional/keyword argument (`url`).
*   Must accept arbitrary keyword arguments (like `connect_args` and `poolclass`) and pass them to the underlying SQLAlchemy engine.
*   Must return a valid `sqlalchemy.engine.Engine` instance.
*   **Exception Handling:** Must raise `sqlalchemy.exc.ArgumentError` if the provided URL is malformed, missing a scheme, or otherwise invalid.

### 3.5. `Session` (Class)
Implement a `Session` class that manages database transactions and acts as a context manager.

**Initialization:**
*   Must be instantiated with an `Engine` object (e.g., `Session(engine)`).

**Context Manager Behaviors (`__enter__` / `__exit__`):**
*   Must provide transaction isolation. Uncommitted records added in one session must be completely invisible to other concurrent sessions.
*   **Automatic Rollback:** If the context manager exits and `commit()` was not explicitly called, the session MUST automatically roll back all pending transactions, discarding any ephemeral changes.

**Methods:**
*   `add(instance)`: Stages a model instance for insertion or update in the database.
*   `commit()`: Flushes all staged changes to the database.
    *   Must raise `sqlalchemy.exc.IntegrityError` if a database constraint is violated (e.g., attempting to commit a duplicate value to a field marked with `unique=True`).
*   `refresh(instance)`: Reloads the instance's data from the database. Must populate any auto-generated fields (such as auto-incrementing primary keys) onto the Python object.
*   `delete(instance)`: Marks an instance for deletion from the database upon the next commit.
*   `get(ModelClass, primary_key)`: Queries the database for a specific record by its primary key.
    *   Returns the strictly typed model instance if found.
    *   Returns `None` if no record matches the primary key.
*   `exec(statement)`: Executes a `select` statement. Returns a result proxy object that must support the following methods:
    *   `.all()`: Returns a standard Python list of strictly typed model instances.
    *   `.first()`: Returns the first matching model instance, or `None` if the result set is empty.
    *   `.one()`: Returns exactly one matching model instance (assumes standard SQLAlchemy `.one()` behavior for raising errors on 0 or >1 results).

### 3.6. `select` (Function)
Implement a `select` function used to construct database queries.

**Behavior:**
*   Must accept a `SQLModel` class as its argument.
*   Must return a query object that supports method chaining for the following methods:
    *   `.where(*conditions)`: Applies SQL `WHERE` clauses. Must accept binary expressions using model attributes (e.g., `Model.name == "string"`, `Model.price > 5`, `Model.foreign_id == other.id`). Multiple `.where()` calls must be combined with logical AND.
    *   `.order_by(attribute)`: Applies SQL `ORDER BY` using the provided model attribute.
    *   `.limit(int)`: Applies a SQL `LIMIT` clause. Must accept `0` and positive integers.
    *   `.offset(int)`: Applies a SQL `OFFSET` clause.
*   The resulting query object must be executable by `Session.exec()`.
*   When compiled, the query object must accurately translate the chained methods into standard SQL syntax (e.g., `LIMIT X`, `OFFSET Y`).