Project: `termform`


## 1. High-Level Goal
Implement a Python terminal formatting library named `termform`. The library must provide a robust set of tools for rendering styled text, tables, progress bars, panels, and other complex UI elements in the terminal using ANSI escape sequences. It must handle automatic environment detection, graceful error handling for malformed styles, and sequential rendering of mixed components.

## 2. Module Structure
You must create a root package named `termform` with the following submodules:
* `termform.align`
* `termform.box`
* `termform.columns`
* `termform.console`
* `termform.errors`
* `termform.inspect`
* `termform.markdown`
* `termform.panel`
* `termform.progress`
* `termform.table`
* `termform.text`
* `termform.traceback`

The root `termform/__init__.py` must expose at least the following:
* A global `print` function (which delegates to a global console).
* A `get_console()` function that returns a global `Console` instance.

## 3. Core Components & Strict Behaviors

### 3.1. `termform.console.Console`
Implement the `Console` class. This is the primary engine for rendering all output.

**Initialization Signature:**
`def __init__(self, file=sys.stdout, force_terminal=False, color_system=None, width=None, record=False, legacy_windows=False)`

**Initialization Rules:**
* **Environment Detection:** If `width` or `color_system` are not explicitly provided, the class must detect them from environment variables. Specifically, parse `COLUMNS` and `LINES` to set the `size` property (a tuple of `(width, height)`). Parse the `TERM` environment variable (e.g., if `TERM="xterm-256color"`, set `color_system` to `"256"`).
* **Properties:** Expose `size` (tuple), `color_system` (string), and `file` (file-like object).

**Methods & Behaviors:**
* `print(*args, style=None, markup=True)`:
  * **Empty Call:** If called with no arguments, output a single newline (`\n`).
  * **Markup Parsing:** If `markup=True` and a string is passed, parse bracketed tags (e.g., `[bold red]text[/bold red]`). Strip the tags from the final output and replace them with corresponding ANSI escape codes.
  * **ANSI Emission:** Only emit ANSI escape codes if `force_terminal=True` or if the target `file` is a TTY.
  * **Nested Data Structures:** If passed a dictionary or list, pretty-print it. The output must include structural indentation (newlines and spaces) and syntax highlighting (ANSI codes for keys, strings, booleans, etc.).
  * **Custom Objects:** If passed an unformattable custom object, fall back to printing its standard `__repr__()` followed by a newline.
  * **Renderables:** If passed a `termform` component (Table, Panel, Text, etc.), invoke its rendering logic.
  * **Sequential Integrity:** When multiple different components (e.g., text, tables, rules) are printed sequentially, they must render in the exact order they were called without interfering with each other's layouts.
* `rule(title: str)`:
  * Render a horizontal line across the terminal width with the `title` string embedded within the line.
* `log(*args, log_locals=False)`:
  * Print the provided arguments, but prepend a timestamp wrapped in brackets (format: `[HH:MM:SS]`).
  * Append the caller's location (filename and line number, e.g., `script.py:42`) to the output.
  * If `log_locals=True`, extract the local variables from the calling frame and render them as a formatted grid/table below the log message.
* `export_text() -> str`:
  * If the console was initialized with `record=True`, return all output generated so far as a plain string.
* `status(status_msg: str, spinner: str = "dots")`:
  * Implement as a Context Manager (`with console.status(...):`).
  * **On Enter:** Hide the terminal cursor (emit `\x1b[?25l`). Start a background thread that renders an animated spinner alongside the `status_msg`.
  * **On Exit:** Stop the background thread and restore the terminal cursor (emit `\x1b[?25h`).

### 3.2. `termform.errors` (Exceptions)
Implement the following exception classes. The `Console` must raise these under specific conditions:

* **`MarkupError`**:
  * Raise when a closing tag is encountered that was never opened (e.g., `"Closing unopened tag[/bold]"`). Note: Unclosed tags at the end of a string should be auto-closed gracefully, but explicitly closing a non-existent tag is an error.
  * Raise when a closing tag does not match the currently active open tag (e.g., `"[red]Text[/bold]"`).
  * *Rule:* Unrecognized tags (e.g., `"[not-a-real-tag]"`) must NOT raise an error; they must be ignored by the parser and treated as literal text.
* **`MissingStyle`**:
  * Raise when a style string contains an invalid or non-existent color name (e.g., `"fakecolor on white"`).
  * Raise when a style string ends with a dangling preposition (e.g., `"bold red on"`).
* **`StyleSyntaxError`**:
  * Raise (or allow `MissingStyle` to be raised) when a style string contains completely unrecognized attributes or malformed syntax (e.g., `"blink underline 123"`).

### 3.3. `termform.table.Table`
**Initialization Signature:** `def __init__(self, title=None, box=None)`
**Methods & Behaviors:**
* `add_column(name: str)`: Registers a new column header.
* `add_row(*args)`: Adds a row of data.
  * **Missing Columns:** If fewer arguments are provided than there are columns, render the missing trailing cells as empty space.
  * **Excess Columns:** If more arguments are provided than there are columns, handle it gracefully without raising an exception (e.g., ignore the excess or store it safely).
* **Properties:** Expose `row_count` (integer representing the number of added rows).
* **Rendering:** Must draw headers, rows, and borders using box-drawing characters (e.g., `│`, `┼`, `┌`, `└`).

### 3.4. `termform.progress.Progress`
**Initialization Signature:** `def __init__(self, console=None, auto_refresh=True)`
Must operate as a Context Manager.
**Methods & Behaviors:**
* `add_task(description: str, total: float) -> int`: Registers a new task and returns a unique integer `task_id`.
* `update(task_id: int, completed: float = None, advance: float = None)`: Updates the progress of a specific task.
* `refresh()`: Forces a render of the current state.
* **Properties:** Expose a `tasks` iterable. Each task object must have `id`, `completed` (float), and `finished` (boolean) attributes.
* **Rendering:**
  * Render the task description, a progress bar, the completion percentage, and an ETA.
  * If progress is at 0%, the ETA is unknown and must render exactly as `"-:--:-"` or `"-:--:--"`.
  * **In-place Updates:** When updating, the output must be modified in-place using carriage returns (`\r`) or ANSI cursor movements. It must NOT emit newlines (`\n`) for every frame.

### 3.5. `termform.panel.Panel`
**Initialization Signature:** `def __init__(self, renderable, title=None, subtitle=None, expand=True, box=None, title_align="center", subtitle_align="center")`
**Rendering:**
* Draw a border around the inner `renderable` content.
* Embed the `title` in the top border and the `subtitle` in the bottom border.
* Respect the `title_align` and `subtitle_align` arguments (e.g., "left", "right", "center").
* Connect the text to the border corners using appropriate horizontal line characters (e.g., `─╮` for top-right, `╰─` for bottom-left).

### 3.6. `termform.box`
Implement a module containing constants that define box-drawing character sets.
* `HEAVY_HEAD`: Must utilize heavy horizontal lines (e.g., `━`) for the header separator.
* `ROUNDED`: Must utilize rounded corner characters (`╭`, `╮`, `╰`, `╯`).

### 3.7. `termform.inspect.inspect`
**Signature:** `def inspect(obj, console=None)`
**Behaviors:**
* Output a detailed report of the arbitrary `obj` provided, including its type, string representation/value, and a list of its attributes.
* **Failing Properties:** If the object has a property that raises an exception when accessed, `inspect` must catch the exception, prevent the application from crashing, and display the exception error message inline within the report.
* **None Handling:** If `obj` is `None`, it must successfully generate a report for `NoneType` without crashing.

### 3.8. Additional Renderable Classes
Implement the following classes. They must be printable via `Console.print()`.

* **`termform.text.Text`**:
  * Signature: `def __init__(self, text: str, style: str = None, justify: str = None)`
  * Method: `stylize(style: str)` applies a style to the text.
  * Rendering: Outputs the text wrapped in the appropriate ANSI escape codes.
* **`termform.align.Align`**:
  * Class Method: `def center(cls, renderable, vertical="middle")`
  * Rendering: Preserves the exact text of the inner renderable but pads it with spaces to align it spatially within the console width.
* **`termform.columns.Columns`**:
  * Signature: `def __init__(self, renderables: list, equal=False, expand=False)`
  * Rendering: Takes an iterable of renderables and draws them side-by-side in the terminal.
* **`termform.markdown.Markdown`**:
  * Signature: `def __init__(self, markup: str)`
  * Rendering: Parses standard Markdown (e.g., `# Heading`, `**bold**`, `*italic*`) and translates it into styled console output.
* **`termform.traceback.Traceback`**:
  * Class Method: `def from_exception(cls, exc_type, exc_value, traceback)`
  * Rendering: Formats and prints a Python exception traceback, applying ANSI syntax highlighting to the output.