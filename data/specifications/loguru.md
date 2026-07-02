Project: `flexilog`


## 1. High-Level Goal
Implement a robust, thread-safe, and highly configurable logging library named `flexilog`. The library must provide a globally accessible logger instance that supports multiple output destinations (sinks), contextual data injection, asynchronous logging, automatic file rotation/retention, and advanced exception catching.

## 2. Module Structure & Global State
*   **Module Name:** `flexilog`
*   **Global Instance:** The module must instantiate and expose a global object named `logger`. 
    *   Developers must be able to import it directly: `from flexilog import logger`.
*   **Default State:** Out-of-the-box, upon import, the `logger` must have exactly one pre-configured sink routing all logs to `sys.stderr`.

## 3. Core Concept: The `Record` Dictionary
Every time a log is emitted, the library must internally generate a `record` dictionary representing the log event. 
*   This dictionary must be passed to filters, patchers, and JSON serializers.
*   It must contain at least the following keys:
    *   `"message"`: The string message being logged.
    *   `"level"`: An object possessing at least a `"name"` attribute (e.g., `"INFO"`, `"DEBUG"`).
    *   `"extra"`: A dictionary containing contextual key-value pairs.

## 4. Sink Management API

### `logger.add(sink, **kwargs)`
Implement this method to register a new output destination. 
*   **Return Value:** Must return a strictly unique integer (`handler_id`) for every registered sink, even if the exact same sink is added multiple times.
*   **Sink Types:** 
    *   *File-like objects:* (e.g., `sys.stderr`, `io.StringIO`). Write the formatted string to them.
    *   *Callables:* Pass the formatted message string to the callable.
    *   *Strings/Paths:* Treat as a file path.
    *   *Invalid Types:* If an unsupported type is provided (e.g., an empty `object()`), raise a `TypeError`.
*   **Parameters & Behaviors:**
    *   `level` (str): The minimum severity threshold (e.g., `"DEBUG"`, `"INFO"`, `"WARNING"`). Suppress any logs below this threshold. If an invalid level string is provided, raise a `ValueError`.
    *   `format` (str): A standard Python format string (e.g., `"{level}:{message}"`). If omitted, use a default format that includes the level name, the message, and a timestamp (which must contain digits). By default, append a newline (`\n`) to the end of the formatted string.
    *   `filter` (callable): A function accepting the `record` dictionary. If it returns a falsy value, suppress the log for this specific sink.
    *   `serialize` (bool): If `True`, ignore the standard format string and emit a JSON-encoded string. The JSON payload must contain a top-level `"record"` key, which contains at least `"message"` (string) and `"level"` (an object with a `"name"` string).
    *   `enqueue` (bool): If `True`, make the sink thread-safe and non-blocking by routing emissions through an internal queue processed by a dedicated background worker thread.
    *   `diagnose` (bool) & `backtrace` (bool): If `True`, exception tracebacks routed to this sink must include the names and values of local variables from the crashing context.

### File-Specific Sink Behaviors (Triggered when `sink` is a file path)
*   **Directory Creation:** If the file path contains non-existent parent directories, automatically create the entire directory tree before writing.
*   **`rotation` (str):** (e.g., `"500 B"`). Track the size of the active log file. If writing the *next* formatted log emission would cause the file size to strictly exceed the specified byte limit, close the current file, rename/rotate it, and open a new active file *before* writing the emission.
*   **`retention` (int):** (e.g., `2`). Maintain exactly `retention` number of rotated files, plus the 1 active log file. Delete the oldest rotated files when this count is exceeded.

### `logger.remove(handler_id=None)`
Implement this method to unregister sinks.
*   If called with no arguments, clear and remove *all* registered sinks.
*   If called with a valid `handler_id`, stop routing logs to that specific sink.
*   If called with an invalid or non-existent `handler_id`, raise a `ValueError`.
*   **Concurrency Rule:** If the sink being removed was configured with `enqueue=True`, this method MUST block until the internal queue is completely flushed and the background worker thread successfully joins.

## 5. Logging Methods & Formatting

### Standard Logging Methods
Implement methods for standard severity levels: `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()`.
*   Implement a generic `logger.log(level_name: str, message: str, *args, **kwargs)` method that behaves identically to the specific level methods.

### String Formatting Rules
*   The logging methods must accept a message string followed by optional `*args` and `**kwargs`.
*   If placeholders (e.g., `{}`, `{name}`, `{ms:.2f}`) exist in the message string, format the string using the provided arguments via standard Python formatting rules.
*   If arguments are provided but the message string contains *no placeholders*, safely ignore the extra arguments and emit the message normally without crashing.

## 6. Context & Modifiers API

All methods in this section must return a *new* logger instance (or a bound wrapper) so that the original global logger remains unmodified.

### `logger.bind(**kwargs)`
*   Inject the provided `kwargs` into the `extra` dictionary of the `record` for all subsequent logs emitted by the returned logger.
*   If chained (e.g., `logger.bind(a=1).bind(a=2)`), newer keys must overwrite existing keys in the `extra` dictionary.

### `logger.contextualize(**kwargs)`
*   Implement as a Context Manager (`with logger.contextualize(...):`).
*   Inject the provided `kwargs` into the `extra` dictionary *only* for logs emitted within the `with` block.

### `logger.patch(callable)`
*   The provided callable must accept the `record` dictionary.
*   Execute this callable before emission, allowing it to mutate the `record` dictionary (e.g., `record["extra"]`) in place.

### `logger.opt(**kwargs)`
Implement configuration overrides for specific log emissions.
*   `raw=True`: Bypass the sink's format string entirely. Emit the exact, raw message string provided by the user (do not automatically append a newline unless the user's string contains one).
*   `lazy=True`: Defer the evaluation of any callable arguments passed for string formatting. If the log level is suppressed by the sink's threshold, do *not* execute the callables.
*   `exception=True`: Automatically capture the currently active exception traceback and attach it to the log emission.

## 7. Exception Handling API

### `@logger.catch(default=None, reraise=False)`
Implement a decorator to wrap functions and handle internal exceptions.
*   If an exception occurs inside the decorated function, catch it and log the traceback.
*   If `reraise=True`, propagate (re-raise) the exception upward after logging it.
*   If `reraise=False`, suppress the exception entirely and return the value provided in the `default` argument.
*   **AST/Diagnostic Requirement:** Ensure the traceback capture mechanism integrates with the sink's `diagnose=True` feature, successfully extracting local variables from the frame where the exception occurred.