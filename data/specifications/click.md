Project: `cmd_constructor`


## 1. High-Level Goal
Implement a robust Command Line Interface (CLI) framework named `cmd_constructor`. The library must provide a decorator-based API for defining commands, groups (routers), options, and positional arguments. It must handle automatic type casting, input prompting, environment variable fallbacks, help menu generation, and isolated testing utilities.

## 2. Module Structure
* **`cmd_constructor`**: The main module containing all public decorators, functions, types, and exceptions.
* **`cmd_constructor.testing`**: A submodule containing testing utilities (specifically the `CliRunner`).

---

## 3. Core Decorators & Routing

### `@command(name=None, help=None, context_settings=None)`
Implement a decorator that transforms a standard Python function into a CLI command.
* **Naming:** If `name` is not provided, derive it automatically from the decorated function's name by replacing all underscores (`_`) with hyphens (`-`).
* **Documentation:** If `help` is not provided, extract the function's docstring and use it as the command's help description.
* **Context Settings:** Accept a `context_settings` dictionary. If `{"ignore_unknown_options": True}` is passed, the parser must treat unrecognized flags (e.g., `--unknown`) as positional arguments rather than raising an error.

### `@group(name=None, help=None)`
Implement a decorator that creates a command group. A group acts as a router for subcommands.
* **Subcommand Registration:** The returned group object must have a `.command()` method, which functions exactly like `@command` but registers the decorated function as a subcommand of this group.
* **Routing:** When the group is executed with a subcommand name as an argument, it must route execution strictly to that subcommand.
* **Default Behavior:** If a group is invoked without any subcommand arguments, it must print the help menu (which must include a list of registered subcommands) and exit cleanly with an exit code of `0`.

### `@pass_context`
Implement a decorator that injects a context object (`ctx`) as the first positional argument to the decorated command/group function.
* **State Propagation:** The `ctx` object must have an `.obj` attribute (defaulting to an empty dictionary or mutable object). Modifications to `ctx.obj` made in a group function must persist and be accessible to the executed subcommand.

---

## 4. Arguments & Options

### `@argument(name, type=str, required=True, nargs=1)`
Implement a decorator to define positional arguments.
* **Parsing:** Arguments are parsed strictly in the order they are defined.
* **Unlimited Arguments:** If `nargs=-1`, capture all remaining positional arguments provided in the CLI into a single Python `tuple`.
* **Missing Arguments:** If a required argument is missing, halt execution, exit with code `2`, and print an error message containing `"Error: Missing argument '<ARG_NAME>'."` (where the name is uppercase) followed by the command's `"Usage:"` instructions.

### `@option(name_declaration, type=str, default=None, is_flag=False, envvar=None, prompt=False, hide_input=False, confirmation_prompt=False, required=False, multiple=False)`
Implement a decorator to define optional flags.
* **Name Resolution:** Convert CLI flag names to snake_case keyword arguments for the Python function (e.g., `--custom-header-value` becomes `custom_header_value`).
* **Boolean Flags:** If the name declaration contains a slash (e.g., `--flag/--no-flag`), treat it as a mutually exclusive boolean flag. Passing `--flag` passes strict boolean `True` to the function; `--no-flag` passes strict boolean `False`.
* **Environment Variables:** If `envvar` is provided and the option is omitted from the CLI, extract the value from the specified environment variable. CLI arguments must take absolute precedence over environment variables. If the envvar is empty/None, fall back to `default`.
* **Multiple Values:** If `multiple=True`, allow the flag to be passed multiple times. Aggregate all provided values into an ordered `tuple`. If omitted, pass an empty tuple `()`.
* **Prompting:** 
  * If `prompt=True` (or a string) and the option is omitted, prompt the user via standard input. 
  * If `prompt` is a string, use it as the prompt text. 
  * Strip trailing newlines from the user's input.
  * If `hide_input=True`, the input should be visually hidden (simulated in tests).
  * If `confirmation_prompt=True`, prompt the user twice. If the inputs do not match, print `"Error: The two entered values do not match."` and prompt again until they match.
  * If `required=True`, reject empty inputs during the prompt and ask again.

---

## 5. Types & Validation

All arguments and options must cast string inputs to their specified `type`. If casting fails, halt execution, exit with a non-zero code, and print: `"Invalid value for '<option_name>': '<input>' is not a valid <type>."`

### Built-in Types
Support standard Python types like `int`, `str`, and `bool`.

### `Path(exists=False, dir_okay=True, file_okay=True)`
Implement a custom class for path validation.
* If `exists=True` and the path does not exist, raise a validation error containing `"does not exist"`.
* If `dir_okay=False` and the path is a directory, raise a validation error containing `"is a directory"`.
* If `file_okay=False` and the path is a file, raise a validation error containing `"is a file"`.

### `Choice(choices: list, case_sensitive: bool)`
Implement a custom class that restricts input to a specific list of strings.
* If `case_sensitive=True`, enforce exact case matching.
* If an invalid choice is provided, raise a validation error containing `"Invalid value for '<option_name>'"` and display the valid choices.

---

## 6. Output & Exceptions

### `echo(message, err=False)`
Implement a function to print output.
* **Unicode:** It must safely handle and print Unicode characters without encoding errors.
* **ANSI Stripping:** If the output stream is non-interactive (e.g., captured by a test runner), it must automatically strip ANSI color/style codes from the message.
* **Routing:** If `err=True`, route the output strictly to `stderr` instead of `stdout`.

### `style(text, fg=None, bold=False)`
Implement a function that wraps the provided `text` in standard ANSI color and style codes based on the arguments.

### `ClickException(Exception)`
Implement a custom exception class.
* **Handling:** If this exception is raised during command execution, the framework must catch it, suppress the standard Python traceback, print `"Error: <exception_message>"` to `stderr`, and exit cleanly with an exit code of `1`.

---

## 7. Testing Utilities (`cmd_constructor.testing`)

### `CliRunner(mix_stderr=True)`
Implement a test runner class to simulate CLI execution.
* **Initialization:** If `mix_stderr=False`, the runner must capture `stdout` and `stderr` independently. Otherwise, they are combined.
* **`invoke(cli, args=None, input=None, env=None, default_map=None)`:**
  * **Execution:** Executes the provided `cli` command.
  * **String Parsing:** If `args` is provided as a single string instead of a list, parse it using shell-like syntax (e.g., `shlex.split`), respecting quotes for arguments with spaces.
  * **Input:** Simulate standard input using the `input` string.
  * **Environment:** Temporarily patch the environment variables with the `env` dictionary.
  * **Default Map:** Accept a `default_map` (a nested dictionary mapping subcommand names to option key-value pairs) to override default option values at runtime.
  * **Return Value:** Return a `Result` object containing:
    * `.exit_code` (integer)
    * `.output` (string, combined output)
    * `.stdout` (string)
    * `.stderr` (string)
* **`isolated_filesystem()`:**
  * Implement a context manager that creates a temporary, empty directory, changes the current working directory (`os.chdir`) to this temporary directory for the duration of the `with` block, and restores the original directory afterward.

---

## 8. Global Help Menu Behavior
Whenever `--help` is passed to any command or group:
1. Intercept execution (do not run the command's logic).
2. Exit with code `0`.
3. Print a formatted help menu containing:
   * The command/group's help description.
   * A list of all registered option flags (e.g., `--verbose`).
   * A list of all registered subcommands (if it is a group).