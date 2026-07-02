# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from tabular_formatter import SEPARATING_LINE, tabulate, tabulate as tabulate_func, tabulate_formats
import tabular_formatter as tabulate_module


def test_tabulate_list_of_lists_default_simple_format():
    data = [
        ["Sun", 696000, 1.9891e9]
    ]
    result = tabulate(data)

    expected = (
        "---  ------  ----------\n"
        "Sun  696000  1.9891e+09\n"
        "---  ------  ----------"
    )

    assert result == expected

def test_tabulate_explicit_headers_plain_format():
    data = [
        ["apple", 5],
        ["banana", 10]
    ]
    headers = ["item", "qty"]
    result = tabulate(data, headers=headers, tablefmt="plain")

    expected = (
        "item      qty\n"
        "apple       5\n"
        "banana     10"
    )

    assert result == expected

def test_tabulate_headers_firstrow_extraction():
    data = [
        ["Name", "Age"],
        ["Alice", 24],
        ["Bob", 19]
    ]
    result = tabulate(data, headers="firstrow", tablefmt="simple")

    expected = (
        "Name      Age\n"
        "------  -----\n"
        "Alice      24\n"
        "Bob        19"
    )

    assert result == expected

def test_tabulate_headers_keys_dict_of_iterables():
    data = {
        "Name": ["Alice", "Bob"],
        "Age": [24, 19]
    }
    result = tabulate(data, headers="keys")

    expected = (
        "Name      Age\n"
        "------  -----\n"
        "Alice      24\n"
        "Bob        19"
    )

    assert result == expected

def test_tabulate_showindex_boolean_toggle():
    """
    When showindex=True is passed, it should prepend a 0-indexed row counter.
    When showindex=False, it should omit this index.
    """
    data = [
        ["Alice", 24],
        ["Bob", 19]
    ]

    # Test showindex=True
    result_true = tabulate(data, showindex=True, tablefmt="plain")
    expected_true = (
        "0  Alice  24\n"
        "1  Bob    19"
    )
    assert result_true == expected_true

    # Test showindex=False
    result_false = tabulate(data, showindex=False, tablefmt="plain")
    expected_false = (
        "Alice  24\n"
        "Bob    19"
    )
    assert result_false == expected_false

def test_tabulate_github_and_grid_formats():
    data = [["Alice", 24], ["Bob", 19]]

    out_github = tabulate(data, tablefmt="github")
    assert "|" in out_github

    out_grid = tabulate(data, tablefmt="grid")
    assert "+" in out_grid

def test_tabulate_headers_keys_list_of_dicts():
    data = [{"name": "Alice", "score": 10}, {"name": "Bob", "score": 20}]
    out = tabulate(data, headers="keys")

    assert "name" in out
    assert "score" in out
    assert "Alice" in out
    assert "20" in out

def test_tabulate_missingval_replaces_none():
    data = [["Alice", 10], ["Bob", None]]
    out = tabulate(data, missingval="N/A")

    assert "N/A" in out
    assert "None" not in out

def test_tabulate_floatfmt_formats_floats():
    data = [["pi", 3.14159]]
    out = tabulate(data, floatfmt=".2f")

    assert "3.14" in out
    assert "3.14159" not in out

def test_tabulate_disable_numparse_preserves_strings():
    data = [["A", "001"], ["B", "010"]]
    out = tabulate(data, disable_numparse=True)

    assert "001" in out
    assert "010" in out

def test_tabulate_maxcolwidths_wraps_text():
    data = [["row1", "alpha beta gamma delta epsilon zeta"]]
    result = tabulate_func(data, maxcolwidths=[None, 10])

    # Verify that the long string is wrapped into multiple lines
    assert "alpha beta" in result
    assert "gamma" in result
    assert "delta" in result
    assert "epsilon" in result
    assert "zeta" in result

    # Verify that wrapping actually introduced newlines in the output
    assert "\n" in result

def test_tabulate_pipe_format_markdown():
    data = [["Alice", 24], ["Bob", 19]]
    headers = ["Name", "Age"]
    result = tabulate_func(data, headers=headers, tablefmt="pipe")

    # Verify the presence of pipe delimiters characteristic of Markdown tables
    assert "|" in result
    assert "| Name" in result or "| Alice" in result

def test_tabulate_supported_table_formats():
    formats = [
        "plain", "simple", "github", "grid", "fancy_grid",
        "pipe", "orgtbl", "jira", "presto", "pretty"
    ]
    data = [["Alice", 24], ["Bob", 19]]
    headers = ["Name", "Age"]

    for fmt in formats:
        result = tabulate_func(data, headers=headers, tablefmt=fmt)
        # Verify it successfully generates a formatted string without crashing
        assert isinstance(result, str)
        assert "Alice" in result
        assert "24" in result

def test_tabulate_handles_mixed_types_and_extreme_shapes():
    # Mixed data types in a single row
    mixed_data = [[1, "Alice", 25, True, 3.14]]
    res_mixed = tabulate_func(mixed_data)
    assert "Alice" in res_mixed
    assert "True" in res_mixed
    assert "3.14" in res_mixed

    # Empty data
    empty_data = []
    res_empty = tabulate_func(empty_data)
    assert isinstance(res_empty, str)

    # Single row data
    single_row = [[1, "Alice", 25]]
    res_single_row = tabulate_func(single_row)
    assert "Alice" in res_single_row

    # Single column data
    single_col = [[1], [2], [3]]
    res_single_col = tabulate_func(single_col)
    assert "1" in res_single_col
    assert "2" in res_single_col
    assert "3" in res_single_col

    # Large dataset (1200 rows)
    large_data = [[i, f"Name{i}"] for i in range(1200)]
    res_large = tabulate_func(large_data)
    assert "Name0" in res_large
    assert "Name1199" in res_large

def test_format_2d_iterable_returns_multiline_string():
    data = [["A", 1000], ["B", 2]]

    # Using tablefmt="plain" to ensure exactly one newline character separates the rows,
    # as the default "simple" format includes header/footer separator lines.
    result = tabulate(data, tablefmt="plain")

    assert isinstance(result, str)

    # The output must contain exactly one newline character \n separating the two rows
    assert result.count("\n") == 1

    # The output must contain padding spaces to align the second column.
    # "1000" is 4 chars, "2" is 1 char. Tabulate right-aligns numbers by default.
    # Expected plain output:
    # A  1000
    # B     2
    assert result == "A  1000\nB     2"

def test_format_diverse_data_structures_no_implicit_headers():
    struct1 = [["Alice", 10], ["Bob", 20]]
    struct2 = [{"name": "Alice", "age": 10}, {"name": "Bob", "age": 20}]
    struct3 = {"name": ["Alice", "Bob"], "age": [10, 20]}

    out1 = tabulate(struct1)
    out2 = tabulate(struct2)
    out3 = tabulate(struct3)

    assert out1 == out2

    # In tabulate 0.9, a dictionary of iterables (struct3) does NOT automatically extract
    # its keys as headers by default. It behaves identically to out1.
    assert out1 == out3
    assert "name" not in out3 and "age" not in out3

def test_provide_explicit_headers_renders_top_header_row():
    data = [[1, 2], [3, 4]]
    headers = ["Alpha", "Beta"]

    result = tabulate(data, headers=headers)
    lines = result.split("\n")

    # The output string must begin with the text Alpha and Beta
    # (Using lstrip because numeric data causes headers to be right-aligned by default)
    assert lines[0].lstrip().startswith("Alpha")
    assert "Beta" in lines[0]

    # The output string must contain a visual separator line immediately below the headers
    assert "-" in lines[1]

    # And above the data row containing 1 and 2
    assert "1" in lines[2]
    assert "2" in lines[2]

def test_headers_firstrow_extracts_initial_item_as_header():
    data = [["Col1", "Col2"], ["Val1", "Val2"], ["Val3", "Val4"]]

    result = tabulate(data, headers="firstrow")
    lines = result.split("\n")

    # The output must render Col1 and Col2 as the header row
    assert "Col1" in lines[0]
    assert "Col2" in lines[0]

    # The output must contain exactly two data rows (Val1/Val2 and Val3/Val4)
    data_lines = [line for line in lines if "Val" in line]
    assert len(data_lines) == 2
    assert "Val1" in data_lines[0] and "Val2" in data_lines[0]
    assert "Val3" in data_lines[1] and "Val4" in data_lines[1]

    # The strings Col1 and Col2 must not appear anywhere in the data body
    data_body = "\n".join(lines[2:])
    assert "Col1" not in data_body
    assert "Col2" not in data_body

def test_headers_keys_extracts_dictionary_keys_as_headers():
    data = [
        {"user_id": 99, "account_status": "active"},
        {"user_id": 100, "account_status": "pending"}
    ]

    result = tabulate(data, headers="keys")
    lines = result.split("\n")

    # The output must contain user_id and account_status formatted as the top header row
    assert "user_id" in lines[0]
    assert "account_status" in lines[0]

    # The output must correctly align the values 99 and 100 under the user_id column,
    # and active and pending under the account_status column.
    assert "99" in lines[2]
    assert "active" in lines[2]
    assert "100" in lines[3]
    assert "pending" in lines[3]

    # Verify alignment visually by checking index positions
    user_id_idx = lines[0].index("user_id")
    account_status_idx = lines[0].index("account_status")

    # 99 should be right-aligned under user_id, active should be left-aligned under account_status
    assert lines[2].index("99") <= user_id_idx + len("user_id")
    assert lines[2].index("active") >= account_status_idx - 1

def test_apply_valid_tablefmt_renders_corresponding_markup():
    data = [["A", 1], ["B", 2]]

    html_out = tabulate(data, tablefmt="html")
    assert "<table>" in html_out
    assert "<tbody>" in html_out
    assert "<tr>" in html_out
    assert "<td>A</td>" in html_out

    pipe_out = tabulate(data, tablefmt="pipe")
    assert "| A | 1 |" in pipe_out

    latex_out = tabulate(data, tablefmt="latex")
    assert "\\begin{tabular}" in latex_out
    assert "A & 1 \\\\" in latex_out

def test_invoke_with_unparseable_data_raises_type_error():
    invalid_data_inputs = [12345, True, object()]

    for invalid_data in invalid_data_inputs:
        with pytest.raises(TypeError):
            tabulate(invalid_data)

def test_apply_floatfmt_formats_numeric_values_correctly():
    data = [["Pi", 3.14159265], ["Zero", 0.0]]

    global_fmt_out = tabulate(data, floatfmt=".2f")
    assert "3.14" in global_fmt_out
    assert "0.00" in global_fmt_out

    per_col_fmt_out = tabulate(data, floatfmt=("", ".4f"))
    assert "3.1416" in per_col_fmt_out
    assert "0.0000" in per_col_fmt_out

def test_apply_colalign_overrides_default_type_alignment():
    data = [["Short", 1], ["VeryLongString", 10000]]

    # Using 'grid' format to ensure the trailing spaces on the rightmost column
    # are preserved and not stripped by the default 'simple' format's rstrip() behavior.
    out = tabulate(data, colalign=("right", "left"), tablefmt="grid")

    # First column (strings) right-aligned: padded with leading spaces to match width 14
    assert "         Short" in out

    # Second column (numbers) left-aligned: padded with trailing spaces to match width 5
    assert "1    " in out

def test_tabulate_with_none_values_replaces_with_missingval_string():
    data = [["Alice", None], [None, 42]]

    # Test omitted missingval (defaults to empty string)
    out_default = tabulate(data, tablefmt="tsv")
    assert "Alice" in out_default
    assert "None" not in out_default

    # Test missingval="N/A"
    out_na = tabulate(data, missingval="N/A", tablefmt="tsv")
    assert "N/A" in out_na

    # Test missingval="UNKNOWN"
    out_unknown = tabulate(data, missingval="UNKNOWN", tablefmt="tsv")
    assert "UNKNOWN" in out_unknown


def test_tabulate_with_uneven_rows_pads_short_rows_with_missingval():
    data = [[1, 2, 3, 4], ["A"], ["X", "Y"]]

    out = tabulate(data, missingval="PAD", tablefmt="tsv")
    lines = out.splitlines()

    assert len(lines) == 3
    # The longest row has 4 columns, so all rows must be padded to 4 columns
    assert lines[0] == "1\t2  \t  3\t  4"
    assert lines[1] == "A\tPAD\tPAD\tPAD"
    assert lines[2] == "X\tY  \tPAD\tPAD"


def test_tabulate_with_showindex_prepends_row_counters_or_custom_sequence():
    data = [["Apple"], ["Banana"], ["Cherry"]]

    # Trigger 1: showindex=True (0-indexed integer counter)
    out_true = tabulate(data, showindex=True, tablefmt="tsv")
    lines_true = out_true.splitlines()
    assert lines_true[0] == "0\tApple"
    assert lines_true[1] == "1\tBanana"
    assert lines_true[2] == "2\tCherry"

    # Trigger 2: showindex with custom iterable
    out_custom = tabulate(data, showindex=["row_a", "row_b", "row_c"], tablefmt="tsv")
    lines_custom = out_custom.splitlines()
    assert lines_custom[0] == "row_a\tApple"
    assert lines_custom[1] == "row_b\tBanana"
    assert lines_custom[2] == "row_c\tCherry"


def test_tabulate_with_disable_numparse_treats_numeric_strings_as_text():
    data = [["12.3400"], ["00042"], ["text"]]

    # disable_numparse=True prevents parsing to floats/ints, preserving exact strings
    # and applying standard string alignment (left-aligned by default) instead of right-aligned.
    out = tabulate(data, disable_numparse=True, tablefmt="grid")

    # The widest string is "12.3400" (7 chars).
    # Left-aligned in a grid format with 1 space padding on each side:
    assert "| 12.3400 |" in out
    assert "| 00042   |" in out
    assert "| text    |" in out


def test_tabulate_with_maxcolwidths_wraps_or_truncates_long_strings():
    data = [["Short", "This is a very long string that exceeds the limit"]]

    # maxcolwidths constrains the second column to 15 characters
    out = tabulate(data, maxcolwidths=[10, 15], tablefmt="grid")

    # Extract only the lines containing table data (ignoring borders like +---+---+)
    data_lines = [line for line in out.splitlines() if line.startswith("|")]

    # The text must be wrapped across multiple lines
    assert len(data_lines) > 1, "Expected the row to be wrapped into multiple lines"

    words_in_out = []
    for line in data_lines:
        cols = line.split("|")
        # cols[0] is empty (before first '|'), cols[1] is col 1, cols[2] is col 2
        col2_text = cols[2].strip()

        # Programmatic check: no single line of text within the column exceeds 15 characters
        assert len(col2_text) <= 15, f"Wrapped line exceeds 15 chars: '{col2_text}'"

        if col2_text:
            words_in_out.extend(col2_text.split())

    # Verify that no text was lost during the wrapping process
    expected_words = "This is a very long string that exceeds the limit".split()
    assert words_in_out == expected_words

def test_tabulate_empty_data_no_headers_returns_empty_string():
    assert tabulate([]) == ""
    assert tabulate(()) == ""
    assert tabulate({}) == ""

def test_tabulate_empty_data_with_headers_returns_header_row_only():
    headers = ["ID", "Name", "Status"]

    # Test with grid format
    grid_out = tabulate([], headers=headers, tablefmt="grid")
    grid_lines = grid_out.splitlines()

    assert len(grid_lines) == 4, "Grid format with empty data and headers should have exactly 4 lines"
    assert grid_lines[0].startswith("+") and grid_lines[0].endswith("+")  # Top border
    assert "ID" in grid_lines[1] and "Name" in grid_lines[1] and "Status" in grid_lines[1]  # Header text
    assert grid_lines[2].startswith("+") and "=" in grid_lines[2]  # Bottom header border
    assert grid_lines[3].startswith("+") and "-" in grid_lines[3]  # Closing bottom border

    # Test with pipe format
    pipe_out = tabulate([], headers=headers, tablefmt="pipe")
    pipe_lines = pipe_out.splitlines()

    assert len(pipe_lines) == 2, "Pipe format with empty data and headers should have exactly 2 lines"
    assert "ID" in pipe_lines[0] and "Name" in pipe_lines[0] and "Status" in pipe_lines[0]
    assert pipe_lines[0].startswith("|") and pipe_lines[0].endswith("|")
    assert pipe_lines[1].startswith("|") and pipe_lines[1].endswith("|")
    assert "-" in pipe_lines[1]  # Alignment indicator line

def test_tabulate_with_separating_line_renders_horizontal_divider():
    tabular_data = [["Apples", 50], SEPARATING_LINE, ["Total", 50]]
    out = tabulate(tabular_data, tablefmt="grid")
    lines = out.splitlines()

    apples_idx = next(i for i, line in enumerate(lines) if "Apples" in line)
    total_idx = next(i for i, line in enumerate(lines) if "Total" in line)

    # Ensure the Total row is below the Apples row
    assert total_idx > apples_idx

    # Extract the separating line
    sep_line = lines[apples_idx + 1]

    # The separating line must consist entirely of grid intersection and horizontal line characters
    assert all(c in "+-" for c in sep_line), f"Separating line contains invalid characters: {sep_line}"
    assert "+" in sep_line and "-" in sep_line

    # The separating line must consist entirely of grid intersection and horizontal line characters
    assert all(c in "+-" for c in sep_line), f"Separating line contains invalid characters: {sep_line}"
    assert "+" in sep_line and "-" in sep_line

def test_tabulate_formats_contains_valid_style_identifiers():
    # Assert it is a list of strings
    assert isinstance(tabulate_formats, list)
    assert all(isinstance(fmt, str) for fmt in tabulate_formats)

    # Assert it contains the known core identifiers
    expected_core_formats = {"simple", "grid", "pipe", "html", "latex"}
    assert expected_core_formats.issubset(set(tabulate_formats))

    # Execute a loop passing every single item to tabulate
    for fmt in tabulate_formats:
        try:
            tabulate([["test", 1]], tablefmt=fmt)
        except ValueError as e:
            pytest.fail(f"tabulate raised ValueError for format '{fmt}': {e}")
