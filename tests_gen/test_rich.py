# 1. Testing Framework & Mocking
from unittest.mock import patch
import pytest

# 2. The Subject Under Test
from termform import box, inspect
from termform.align import Align
from termform.columns import Columns
from termform.console import Console
from termform.errors import MarkupError, StyleSyntaxError, MissingStyle
from termform.markdown import Markdown
from termform.panel import Panel
from termform.progress import Progress
from termform.table import Table
from termform.text import Text
from termform.traceback import Traceback
import termform as rich

# 4. Auxiliary: Standard Library
import datetime
import inspect as py_inspect
import io
import os
import re
import sys
import time


def test_console_print_markup_and_rule_generates_ansi_output():
    output = io.StringIO()
    # force_terminal=True ensures ANSI escape codes are generated even when writing to a StringIO buffer
    console = Console(file=output, force_terminal=True, color_system="truecolor")

    console.print("[bold magenta]Hello[/bold magenta] [green]World[/green]!")
    console.rule("Section")

    result = output.getvalue()

    assert "Hello" in result
    assert "World" in result
    assert "Section" in result
    assert "\x1b[" in result

def test_console_print_table_renders_headers_rows_and_borders():
    output = io.StringIO()
    console = Console(file=output)

    table = Table(title="Planets")
    table.add_column("Name")
    table.add_column("Radius")
    table.add_column("Mass")
    table.add_row("Mercury", "2439", "3.30e23")

    console.print(table)

    result = output.getvalue()

    assert "Planets" in result
    assert "Name" in result
    assert "Radius" in result
    assert "Mass" in result
    assert "Mercury" in result
    assert "2439" in result
    assert "3.30e23" in result
    # Verify the presence of box-drawing characters (Rich uses characters like │, ┼, ┌ by default)
    assert any(char in result for char in ["│", "┼", "+", "|", "┌", "└"])

def test_progress_update_completes_task_and_renders_description():
    output = io.StringIO()
    console = Console(file=output)

    with Progress(console=console) as progress:
        task_id = progress.add_task("Processing", total=5)
        progress.update(task_id, completed=5)

        # Verify internal state reflects completion
        task = next(t for t in progress.tasks if t.id == task_id)
        assert task.completed == 5
        assert task.finished is True

    result = output.getvalue()
    assert "Processing" in result

def test_console_renders_mixed_sequential_elements_without_interference():
    output = io.StringIO()
    console = Console(file=output, width=100)

    console.log("Starting mixed output test")

    t1 = Table(title="Users")
    t1.add_column("Name")
    t1.add_column("Role")
    t1.add_row("Alice", "admin")
    console.print(t1)

    console.rule("Separator")

    t2 = Table(title="Servers")
    t2.add_column("Host")
    t2.add_column("Status")
    t2.add_row("srv-2", "DOWN")
    console.print(t2)

    result = output.getvalue()

    # Verify all elements are present
    assert "Starting mixed output test" in result
    assert "Users" in result
    assert "Alice" in result
    assert "admin" in result
    assert "Separator" in result
    assert "Servers" in result
    assert "srv-2" in result
    assert "DOWN" in result

    # Verify they were rendered in the correct sequential order
    idx_log = result.find("Starting mixed output test")
    idx_t1 = result.find("Alice")
    idx_rule = result.find("Separator")
    idx_t2 = result.find("srv-2")

    assert idx_log < idx_t1 < idx_rule < idx_t2

def test_console_log_renders_message_with_timestamp_brackets():
    output = io.StringIO()
    console = Console(file=output)

    console.log("A log message")

    result = output.getvalue()

    assert "A log message" in result
    # Console.log prepends a timestamp and appends caller info, both wrapped in brackets
    assert "[" in result
    assert "]" in result

def test_console_print_text_object_applies_ansi_styles():
    f = io.StringIO()
    # force_terminal and color_system are required to ensure ANSI codes are emitted to a StringIO object
    console = Console(file=f, force_terminal=True, color_system="standard")
    text = Text("StyledText", style="bold red")

    console.print(text)
    output = f.getvalue()

    assert "StyledText" in output
    assert "\x1b[" in output

def test_console_print_panel_renders_inner_content_and_titles():
    f = io.StringIO()
    console = Console(file=f)
    panel = Panel("Inside Panel", title="PanelTitle", subtitle="PanelSub")

    console.print(panel)
    output = f.getvalue()

    assert "Inside Panel" in output
    assert "PanelTitle" in output
    assert "PanelSub" in output

def test_console_print_aligned_content_preserves_text():
    f = io.StringIO()
    console = Console(file=f)
    aligned = Align.center("Centered", vertical="middle")

    console.print(aligned)
    output = f.getvalue()

    assert "Centered" in output

def test_console_print_columns_renders_all_iterable_items():
    f = io.StringIO()
    console = Console(file=f)
    columns = Columns(["One", "Two", "Three"], equal=True, expand=True)

    console.print(columns)
    output = f.getvalue()

    assert "One" in output
    assert "Two" in output
    assert "Three" in output

def test_console_print_markdown_renders_text_content():
    f = io.StringIO()
    console = Console(file=f)
    md = Markdown("# Heading\n\nThis is **bold** and *italic*.")

    console.print(md)
    output = f.getvalue()

    assert "Heading" in output
    assert "bold" in output
    assert "italic" in output

def test_console_print_traceback_renders_exception_details_and_ansi_codes():
    console_file = io.StringIO()
    console = Console(file=console_file, force_terminal=True, color_system="truecolor")

    try:
        1 / 0
    except ZeroDivisionError:
        exc_type, exc_value, traceback = sys.exc_info()
        tb = Traceback.from_exception(exc_type, exc_value, traceback)
        console.print(tb)

    output = console_file.getvalue()

    assert "ZeroDivisionError" in output
    assert "\x1b[" in output

def test_module_supports_dir():
    dir_output = dir(rich)
    assert "print" in dir_output
    assert "get_console" in dir_output

def test_console_renders_core_components_and_exports_text():
    console = Console(record=True, force_terminal=False, width=80)

    console.print("[bold red]Hello[/bold red]")

    table = Table()
    table.add_column("Col1")
    table.add_row("Row1")
    console.print(table)

    panel = Panel("Panel Content", expand=False)
    console.print(panel)

    text = Text("Text Content", justify="center")
    text.stylize("bold magenta")
    console.print(text)

    output = console.export_text()

    assert "Hello" in output
    assert "Col1" in output
    assert "Row1" in output
    assert "Panel Content" in output
    assert "Text Content" in output

def test_console_handles_large_tables_and_invalid_markup():
    console_file = io.StringIO()
    console = Console(file=console_file)

    table = Table()
    table.add_column("Index")
    for i in range(200):
        table.add_row(str(i))

    console.print(table)

    # To raise MarkupError, we must close a tag that was never opened
    with pytest.raises(MarkupError):
        console.print("Closing unopened tag[/bold]")

def test_print_nested_data_structure_outputs_indented_and_highlighted_text():
    console_file = io.StringIO()
    console = Console(file=console_file, force_terminal=True, color_system="truecolor")

    data = {
        "users": [
            {"id": 1, "active": True, "role": "admin"},
            {"id": 2, "active": False, "role": None}
        ]
    }

    console.print(data)

    output = console_file.getvalue()

    # Check for structural indentation (newlines and spaces)
    assert "\n" in output
    assert "  " in output

    # Check for ANSI escape codes (syntax highlighting)
    assert "\x1b[" in output

    # Check for content
    assert "users" in output
    assert "admin" in output

def test_print_string_with_markup_tags_outputs_ansi_styled_text_without_tags():
    string_io = io.StringIO()
    console = Console(file=string_io, force_terminal=True, color_system="standard")

    text = "[bold red]Error:[/bold red] [cyan]System failure[/cyan] at [u]10:00[/u]"
    console.print(text)

    output = string_io.getvalue()

    assert "[bold red]" not in output
    assert "[/bold red]" not in output
    assert "[cyan]" not in output
    assert "[/cyan]" not in output
    assert "[u]" not in output
    assert "[/u]" not in output

    assert "\x1b[" in output

    assert "Error:" in output
    assert "System failure" in output
    # Split the assertion to account for ANSI codes injected between "at " and "10:00"
    assert "at " in output
    assert "10:00" in output

def test_print_without_arguments_outputs_single_newline():
    string_io = io.StringIO()
    console = Console(file=string_io)

    console.print()

    output = string_io.getvalue()
    assert output == "\n"

def test_print_unformattable_custom_object_outputs_standard_string_representation():
    class OpaqueObject:
        def __repr__(self):
            return "<OpaqueObject id=999>"

    string_io = io.StringIO()
    console = Console(file=string_io)

    console.print(OpaqueObject())

    output = string_io.getvalue()
    assert output == "<OpaqueObject id=999>\n"

def test_inspect_arbitrary_object_outputs_type_value_and_attributes_report():
    string_io = io.StringIO()
    console = Console(file=string_io)

    obj = datetime.datetime(2023, 10, 31, 12, 0, 0)
    inspect(obj, console=console)

    output = string_io.getvalue()

    assert "datetime" in output
    # Asserting the components of the repr() rather than a formatted date string
    assert "2023" in output
    assert "10" in output
    assert "31" in output
    assert "year" in output
    assert "month" in output
    assert "day" in output


def test_inspect_object_with_failing_property_displays_error_inline_without_crashing():
    class BrokenObject:
        @property
        def broken_attribute(self):
            raise RuntimeError("Simulated property failure")

    string_io = io.StringIO()
    console = Console(file=string_io)

    obj = BrokenObject()

    # The inspect call should catch the exception and not crash the test
    inspect(obj, console=console)

    output = string_io.getvalue()

    # Verify the exception message is rendered inline within the report
    assert "Simulated property failure" in output

def test_inspect_none_value_generates_report_without_crashing():
    console = Console(record=True)
    inspect(None, console=console)
    output = console.export_text()

    assert "NoneType" in output


def test_console_initialization_detects_terminal_dimensions_and_color_capabilities():
    env_mocks = {
        "COLUMNS": "120",
        "LINES": "40",
        "TERM": "xterm-256color"
    }
    with patch.dict(os.environ, env_mocks):
        with patch("sys.stdout.isatty", return_value=True):
            console = Console()

            assert console.size == (120, 40)
            assert console.color_system == "256"


def test_console_log_prepends_timestamp_and_caller_location():
    console = Console(record=True, width=200)

    frame = py_inspect.currentframe()
    line_number = frame.f_lineno + 1
    console.log("System initialized")

    output = console.export_text()

    assert "System initialized" in output
    assert re.search(r"\[\d{2}:\d{2}:\d{2}\]", output) is not None

    filename = os.path.basename(__file__)
    assert f"{filename}:{line_number}" in output


def test_console_log_with_log_locals_outputs_local_variable_grid():
    console = Console(record=True, width=200)
    active_connections = 42
    status_code = "OK"

    console.log("Testing locals", log_locals=True)

    output = console.export_text()

    assert "active_connections" in output
    assert "42" in output
    assert "status_code" in output
    assert "OK" in output


def test_console_status_context_manager_renders_animated_spinner():
    output_file = io.StringIO()
    # force_terminal=True is required to emit ANSI escape codes for the spinner and cursor
    console = Console(file=output_file, force_terminal=True, width=80)

    status_msg = "Processing complex data 影師嗎..."
    with console.status(status_msg, spinner="dots"):
        # Allow the background thread to render at least one frame
        time.sleep(0.15)

    output = output_file.getvalue()

    assert status_msg in output
    # Verify cursor is hidden at start and restored at exit (clean teardown)
    assert "\x1b[?25l" in output
    assert "\x1b[?25h" in output

def test_print_populated_table_renders_bordered_grid():
    console = Console(file=io.StringIO(), force_terminal=False, width=80)
    table = Table(box=box.HEAVY_HEAD)
    table.add_column("ID")
    table.add_column("Status")
    table.add_row("1", "[green]Active[/green]")
    console.print(table)
    output = console.file.getvalue()

    assert "ID" in output
    assert "Status" in output
    assert "1" in output
    assert "Active" in output
    # HEAVY_HEAD uses heavy horizontal lines (━)
    assert "━" in output

def test_add_row_with_missing_columns_renders_empty_trailing_cells():
    console = Console(file=io.StringIO(), force_terminal=False, width=80)
    table = Table()
    table.add_column("Col A")
    table.add_column("Col B")
    table.add_column("Col C")
    table.add_row("Only A")
    console.print(table)
    output = console.file.getvalue()

    assert "Col A" in output
    assert "Col B" in output
    assert "Col C" in output
    assert "Only A" in output

def test_add_row_with_excess_columns_is_handled_gracefully():
    table = Table()
    table.add_column("Col1")
    table.add_column("Col2")
    
    # Rich handles excess columns gracefully without raising an exception
    table.add_row("Data1", "Data2", "Data3")
    assert table.row_count == 1

def test_add_task_renders_progress_bar_with_percentage_and_eta():
    console = Console(file=io.StringIO(), force_terminal=True, width=120)
    with Progress(console=console, auto_refresh=False) as progress:
        progress.add_task("Downloading payload_v2.bin", total=100.0)
        progress.refresh()
        output = console.file.getvalue()

        assert "Downloading payload_v2.bin" in output
        assert "0%" in output
        # At 0% progress, ETA is unknown and renders as "-:--:-"
        assert "-:--:--" in output

def test_update_progress_task_modifies_output_in_place_without_newlines():
    console = Console(file=io.StringIO(), force_terminal=True, width=120, legacy_windows=False)
    with Progress(console=console, auto_refresh=False) as progress:
        task = progress.add_task("Task", total=100.0)
        progress.refresh()

        # Clear the buffer to capture only the update frames
        console.file.seek(0)
        console.file.truncate(0)

        progress.update(task, advance=25.5)
        progress.refresh()

        progress.update(task, completed=100.0)
        progress.refresh()

        output = console.file.getvalue()

        assert "\r" in output or "\x1b[" in output
        assert "\n" not in output

def test_render_panel_draws_borders_with_aligned_titles():
    output_stream = io.StringIO()
    console = Console(file=output_stream, width=80, color_system=None, legacy_windows=False)

    payload = "Core System Active\nAll systems nominal."
    panel = Panel(
        payload,
        box=box.ROUNDED,
        title="Status",
        title_align="right",
        subtitle="v1.0.4",
        subtitle_align="left"
    )

    console.print(panel)
    result = output_stream.getvalue()

    assert "╭" in result
    assert "╮" in result
    assert "╰" in result
    assert "╯" in result

    lines = result.splitlines()
    top_line = lines[0]
    bottom_line = lines[-1]

    assert "Status" in top_line
    # Account for the horizontal line character connecting the text to the corner
    assert top_line.endswith("Status ─╮")

    assert "v1.0.4" in bottom_line
    # Account for the horizontal line character connecting the corner to the text
    assert bottom_line.startswith("╰─ v1.0.4")

def test_print_malformed_markup_raises_markup_errors():
    # 1. Closing unopened tag (Unclosed tags are auto-closed, so we must test an unopened closure)
    output_stream = io.StringIO()
    console = Console(file=output_stream)
    with pytest.raises(MarkupError):
        console.print("Hello[/bold]", markup=True)
    assert output_stream.getvalue() == ""

    # 2. Mismatched closing tag
    output_stream = io.StringIO()
    console = Console(file=output_stream)
    with pytest.raises(MarkupError):
        console.print("[red]Text[/bold]", markup=True)
    assert output_stream.getvalue() == ""

    # 3. Unrecognized tag is ignored by the markup parser (does not raise)
    output_stream = io.StringIO()
    console = Console(file=output_stream)
    console.print("[not-a-real-tag]Text[/not-a-real-tag]", markup=True)
    assert "Text" in output_stream.getvalue()

def test_parse_invalid_style_string_raises_errors():
    # 1. Invalid color name raises MissingStyle
    output_stream = io.StringIO()
    console = Console(file=output_stream)
    with pytest.raises(MissingStyle):
        console.print("Test", style="fakecolor on white")
    assert output_stream.getvalue() == ""

    # 2. Dangling preposition raises MissingStyle (not StyleSyntaxError)
    output_stream = io.StringIO()
    console = Console(file=output_stream)
    with pytest.raises(MissingStyle):
        console.print("Test", style="bold red on")
    assert output_stream.getvalue() == ""

    # 3. Unrecognized attribute raises StyleSyntaxError or MissingStyle
    output_stream = io.StringIO()
    console = Console(file=output_stream)
    with pytest.raises((StyleSyntaxError, MissingStyle)):
        console.print("Test", style="blink underline 123")
    assert output_stream.getvalue() == ""