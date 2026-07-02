# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
import tabular_processor as petl
import tabular_processor as etl

# 4. Auxiliary: Standard Library
import os
import tempfile


def test_csv_pipeline_filters_and_sorts_data_correctly(tmp_path):
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"

    # Create input CSV data
    input_csv.write_text("name,age\nAlice,25\nBob,35\nCharlie,30\nDavid,40\nEve,20\n")

    # Pipeline: load, convert, filter, sort, save
    table = petl.fromcsv(str(input_csv))
    table = petl.convert(table, 'age', int)
    table = petl.selectge(table, 'age', 30)
    table = petl.sort(table, 'age')
    petl.tocsv(table, str(output_csv))

    # Verify output CSV physically exists
    assert output_csv.exists()

    # Verify output CSV contains the correct subset of data and original header
    result_table = petl.fromcsv(str(output_csv))
    result_table = petl.convert(result_table, 'age', int)

    assert petl.header(result_table) == ('name', 'age')
    assert list(petl.data(result_table)) == [
        ('Charlie', 30),
        ('Bob', 35),
        ('David', 40)
    ]

def test_addfield_and_select_filters_on_calculated_column():
    dicts = [
        {'id': 1, 'val': 20},
        {'id': 2, 'val': 30},
        {'id': 3, 'val': 40},
        {'id': 4, 'val': 10}
    ]

    table = petl.fromdicts(dicts)
    # Add field using lambda to multiply existing value by 2
    table = petl.addfield(table, 'double_val', lambda rec: rec['val'] * 2)
    # Filter using custom lambda based on the newly created field (>= 60)
    table = petl.select(table, lambda rec: rec['double_val'] >= 60)

    result = list(petl.dicts(table))

    assert len(result) == 2
    assert result[0] == {'id': 2, 'val': 30, 'double_val': 60}
    assert result[1] == {'id': 3, 'val': 40, 'double_val': 80}

def test_join_performs_inner_join_on_shared_key():
    # Left table has unique keys ('id')
    left_table = [
        ['id', 'name'],
        [1, 'Alice'],
        [2, 'Bob'],
        [3, 'Charlie']
    ]

    # Right table has duplicate keys to test 1-to-many relationship fan out
    right_table = [
        ['id', 'order'],
        [1, 'Book'],
        [1, 'Pen'],
        [2, 'Pencil'],
        [4, 'Eraser']
    ]

    joined = petl.join(left_table, right_table, key='id')
    result = list(joined)

    expected = [
        ('id', 'name', 'order'),
        (1, 'Alice', 'Book'),
        (1, 'Alice', 'Pen'),
        (2, 'Bob', 'Pencil')
    ]

    assert result == expected

def test_cut_and_rename_modifies_headers_and_columns():
    # Original columns: ["id", "value", "city"]
    table = [
        ['id', 'value', 'city'],
        [1, 10, 'NY'],
        [2, 20, 'LA']
    ]

    # Cut to: ["id", "value"]
    cut_table = petl.cut(table, 'id', 'value')
    # Rename 'value' to 'val'
    renamed_table = petl.rename(cut_table, 'value', 'val')

    result = list(renamed_table)

    expected = [
        ('id', 'val'),
        (1, 10),
        (2, 20)
    ]

    assert result == expected

def test_selecteq_and_selectin_filter_rows_by_exact_and_set_matches():
    table = [
        ['id', 'city'],
        [1, 'Paris'],
        [2, 'London'],
        [3, 'Berlin'],
        [4, 'Rome'],
        [5, 'Paris']
    ]

    # selecteq matching a single string ("Paris")
    eq_table = petl.selecteq(table, 'city', 'Paris')
    eq_result = list(eq_table)

    expected_eq = [
        ('id', 'city'),
        (1, 'Paris'),
        (5, 'Paris')
    ]
    assert eq_result == expected_eq

    # selectin matching a set of strings ({"London", "Berlin"})
    in_table = petl.selectin(table, 'city', {'London', 'Berlin'})
    in_result = list(in_table)

    expected_in = [
        ('id', 'city'),
        (2, 'London'),
        (3, 'Berlin')
    ]
    assert in_result == expected_in

def test_convert_applies_lambda_transformation_to_specific_column():
    table = [
        ('id', 'val', 'other'),
        (1, '10', 'A'),
        (2, '20', 'B'),
        (3, '30', 'C')
    ]

    # Apply lambda to convert string numbers to integers and add 1
    result = etl.convert(table, 'val', lambda v: int(v) + 1)
    result_list = list(result)

    assert result_list == [
        ('id', 'val', 'other'),
        (1, 11, 'A'),
        (2, 21, 'B'),
        (3, 31, 'C')
    ]

def test_sort_orders_rows_descending_when_reverse_is_true():
    table = [
        ('id', 'score'),
        (1, 10),
        (2, 30),
        (3, 20)
    ]

    # Sort by 'score' in descending order
    result = etl.sort(table, key='score', reverse=True)
    result_list = list(result)

    assert result_list == [
        ('id', 'score'),
        (2, 30),
        (3, 20),
        (1, 10)
    ]

def test_leftjoin_preserves_left_rows_with_missing_right_data():
    left_table = [
        ('key', 'left_val'),
        (1, 'A'),
        (2, 'B'),
        (3, 'C')
    ]
    right_table = [
        ('key', 'right_val'),
        (1, 'X'),
        (3, 'Z')
    ]

    # Perform left join on 'key'
    result = etl.leftjoin(left_table, right_table, key='key')
    result_list = list(result)

    assert result_list == [
        ('key', 'left_val', 'right_val'),
        (1, 'A', 'X'),
        (2, 'B', None),  # Key 2 is preserved with missing right-side data
        (3, 'C', 'Z')
    ]

def test_csv_roundtrip_preserves_headers_and_row_data_as_strings():
    original_table = [
        ('id', 'name'),
        (1, 'Alice'),
        (2, 'Bob')
    ]

    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f:
        filepath = f.name

    try:
        # Write to CSV
        etl.tocsv(original_table, filepath)

        # Read back from CSV
        result = etl.fromcsv(filepath)
        result_list = list(result)

        # Verify headers and data are preserved, noting that CSV reads back as strings
        assert result_list == [
            ('id', 'name'),
            ('1', 'Alice'),
            ('2', 'Bob')
        ]
    finally:
        os.remove(filepath)

def test_stack_concatenates_tables_sequentially():
    table1 = [
        ('col1', 'col2'),
        (1, 2),
        (3, 4)
    ]
    table2 = [
        ('col1', 'col2'),
        (5, 6)
    ]

    # Stack tables sequentially
    result = etl.stack(table1, table2)
    result_list = list(result)

    # Result must have exactly 3 data rows in the correct order
    assert result_list == [
        ('col1', 'col2'),
        (1, 2),
        (3, 4),
        (5, 6)
    ]

def test_distinct_removes_exact_duplicate_rows():
    # Table contains two identical rows as specified
    table = petl.fromdicts([{"id": 1, "v": "x"}, {"id": 1, "v": "x"}])

    # Apply distinct
    result = petl.distinct(table)

    # Verify output contains only one instance of the row
    result_dicts = list(petl.dicts(result))
    assert len(result_dicts) == 1
    assert result_dicts[0] == {"id": 1, "v": "x"}

def test_recordlookup_retrieves_row_by_key():
    table = [['id', 'value'], [10, 'foo'], [20, 'bar']]
    lkp = petl.recordlookup(table, 'id')

    # Querying by an integer key (20)
    records = lkp[20]

    # recordlookup returns a list of records matching the key
    record = records[0] if isinstance(records, list) else records

    # Handle the return type robustly (dict, petl.Record, or standard tuple)
    if isinstance(record, dict):
        assert record['id'] == 20
        assert record['value'] == 'bar'
    else:
        try:
            # petl.Record supports string-based indexing
            assert record['id'] == 20
            assert record['value'] == 'bar'
        except (TypeError, IndexError):
            # Fallback for standard tuples
            assert record[0] == 20
            assert record[1] == 'bar'

def test_petl_exposes_wrap_function():
    assert hasattr(petl, 'wrap')
    assert callable(petl.wrap)

def test_wrap_creates_iterable_table_supporting_sort():
    input_data = [["foo", "bar"], [1, "a"], [2, "b"]]
    table = petl.wrap(input_data)

    # Verify it can be iterated over to retrieve the rows (converting to tuples for strict comparison)
    assert [tuple(row) for row in table] == [("foo", "bar"), (1, "a"), (2, "b")]

    # Verify it supports public transformation functions like petl.sort
    sorted_table = petl.sort(table, "foo")
    assert [tuple(row) for row in sorted_table] == [("foo", "bar"), (1, "a"), (2, "b")]

def test_wrap_sequential_dataset_separates_header_and_data():
    input_iterable = [['id', 'name', 'active'], [1, 'Alice', True], [2, 'Bob', False], [3, '', None]]
    table = petl.wrap(input_iterable)

    # Verify header extraction
    header = petl.header(table)
    assert tuple(header) == ('id', 'name', 'active')

    # Verify data extraction and format exactly as requested
    data = petl.data(table)
    data_output = tuple(list(row) for row in data)
    assert data_output == ([1, 'Alice', True], [2, 'Bob', False], [3, '', None])

def test_transform_pipeline_defers_execution_until_evaluation():
    input_data = [['id'], [1], [2], [3]]
    execution_log = []

    def calc_rule(row):
        execution_log.append(row['id'])
        return row['id']

    table = etl.wrap(input_data)

    # addfield returns a new table view (lazy evaluation)
    transformed_table = etl.addfield(table, 'new_id', calc_rule)

    # Assertion 1: execution_log must be strictly [] immediately after calling addfield
    assert execution_log == []

    # Assertion 2: execution_log must be populated only after explicitly iterating over petl.data()
    list(petl.data(transformed_table))
    assert len(execution_log) > 0
    assert set(execution_log) == {1, 2, 3}


def test_fromcsv_valid_file_loads_tabular_structure(tmp_path):
    csv_content = (
        '"col_a","col_b","col_c"\n'
        '"val1","val,with,commas","val_with_""quotes"""\n'
        '"val3",""," "\n'
    )
    file_path = tmp_path / "test.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    table = etl.fromcsv(str(file_path))

    assert tuple(petl.header(table)) == ('col_a', 'col_b', 'col_c')

    data = list(petl.data(table))
    assert tuple(data[0]) == ('val1', 'val,with,commas', 'val_with_"quotes"')


def test_fromcsv_defers_file_not_found_error_until_iteration():
    invalid_path = "/tmp/non_existent_petl_test_file_999888777.csv"

    # Should not raise during pipeline definition due to lazy evaluation
    table = etl.fromcsv(invalid_path)

    # Should raise strictly when iteration begins
    with pytest.raises(FileNotFoundError):
        list(petl.data(table))


def test_fromdicts_without_explicit_header_dynamically_generates_columns():
    input_dicts = [
        {'user_id': 101, 'role': 'admin'},
        {'role': 'user', 'user_id': 102}
    ]

    table = etl.fromdicts(input_dicts)

    assert tuple(petl.header(table)) == ('user_id', 'role')

    data = list(petl.data(table))
    assert list(data[0]) == [101, 'admin']
    assert list(data[1]) == [102, 'user']


def test_fromdicts_accumulates_all_unique_keys_from_all_rows():
    input_dicts = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "age": 30},
        {"name": "Bob", "city": "NY"}
    ]

    table = etl.fromdicts(input_dicts)

    # petl 1.7 does a full pass to accumulate all unique keys when no header is provided
    assert tuple(petl.header(table)) == ("id", "name", "age", "city")

    data = list(petl.data(table))

    # Row 2: "age" is present, "name" and "city" are missing
    assert tuple(data[1]) == (2, None, 30, None)

    # Row 3: "name" and "city" are present, "id" and "age" are missing
    assert tuple(data[2]) == (None, "Bob", None, "NY")

def test_cut_isolates_and_reorders_specified_columns():
    table = petl.wrap([
        ["first_name", "last_name", "email", "phone"],
        ["John", "Doe", "john@example.com", "555-1234"]
    ])
    result = petl.cut(table, "email", "first_name")

    assert petl.header(result) == ("email", "first_name")
    assert tuple(tuple(row) for row in petl.data(result)) == (("john@example.com", "John"),)

def test_cut_defers_field_selection_error_until_iteration():
    table = petl.wrap([
        ["id", "username", "status"],
        [1, "admin", "active"]
    ])

    # petl evaluates lazily, so we must consume the iterator to trigger the error
    with pytest.raises(petl.errors.FieldSelectionError) as exc_info:
        list(petl.cut(table, "id", "password_hash"))

    assert "password_hash" in str(exc_info.value)

def test_rename_updates_headers_without_altering_data_rows():
    table = petl.wrap([
        ["TxnId", "Amt", "Stat"],
        ["T-001", 99.99, "OK"]
    ])
    result = petl.rename(table, {"TxnId": "transaction_id", "Amt": "amount"})

    assert petl.header(result) == ("transaction_id", "amount", "Stat")
    assert tuple(tuple(row) for row in petl.data(result)) == (("T-001", 99.99, "OK"),)

def test_rename_with_nonexistent_column_raises_error():
    table = petl.wrap([
        ["id", "name"],
        [1, "Alice"]
    ])
    
    # petl strictly validates field selections and raises an error for missing columns
    with pytest.raises(petl.errors.FieldSelectionError) as exc_info:
        result = petl.rename(table, {"id": "user_id", "email": "contact_email"})
        list(result)

    assert "email" in str(exc_info.value)

def test_select_with_conditional_callable_retains_only_passing_rows():
    table = petl.wrap([
        ['id', 'status'],
        [1, 'active'],
        [2, 'inactive'],
        [3, 'active']
    ])
    result = petl.select(table, 'status', lambda v: v == 'active')

    assert tuple(tuple(row) for row in petl.data(result)) == ((1, 'active'), (3, 'active'))

def test_select_on_short_row_passes_none_to_callable():
    table = etl.wrap([['id', 'value', 'notes'], [1, 'A', 'ok'], [2, 'B']])

    # The callable will receive None for the missing 'notes' column in the short row
    result = petl.select(table, 'notes', lambda v: v is None)

    # Verify the short row is retained and matches the expected output
    assert [list(row) for row in petl.data(result)] == [[2, 'B']]

def test_addfield_with_static_value_populates_all_rows():
    table = etl.wrap([['id'], [1], [2]])

    result = petl.addfield(table, 'tenant_id', 999)

    assert list(petl.header(result)) == ['id', 'tenant_id']
    assert [list(row) for row in petl.data(result)] == [[1, 999], [2, 999]]

def test_addfield_with_callable_populates_rows_dynamically():
    table = etl.wrap([['first', 'last'], ['Jane', 'Doe'], ['John', 'Smith']])

    # The callable receives the row as a dictionary-like record
    result = petl.addfield(table, 'full_name', lambda row: f"{row['first']} {row['last']}")

    assert [list(row) for row in petl.data(result)] == [
        ['Jane', 'Doe', 'Jane Doe'],
        ['John', 'Smith', 'John Smith']
    ]

def test_addfield_with_existing_name_creates_duplicate_header():
    table = etl.wrap([['id', 'status'], [1, 'old']])

    result = petl.addfield(table, 'status', 'new')

    # Verify duplicate header is created and original data is untouched
    assert list(petl.header(result)) == ['id', 'status', 'status']
    assert [list(row) for row in petl.data(result)] == [[1, 'old', 'new']]

def test_join_tables_on_shared_key_combines_rows_horizontally():
    left = etl.wrap([['id', 'name'], [1, 'Alice'], [2, 'Bob'], [3, 'Charlie']])
    right = etl.wrap([['id', 'role'], [2, 'Admin'], [3, 'User'], [4, 'Guest']])

    result = etl.join(left, right, key='id')

    data = tuple(tuple(row) for row in petl.data(result))

    # Verify the inner join combines columns horizontally for matching keys
    assert data == ((2, 'Bob', 'Admin'), (3, 'Charlie', 'User'))

    # Strictly verify that non-matching keys are excluded
    ids = [row[0] for row in data]
    assert 1 not in ids
    assert 4 not in ids

def test_tocsv_with_file_path_executes_pipeline_and_writes_csv():
    input_table = [['col1', 'col2'], ['val1', 'val2,with,comma']]

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, 'output.csv')

        # Wrap the input, apply the pending transformation, and execute the pipeline to CSV
        (
            petl.wrap(input_table)
            .addfield('col3', 'static')
            .tocsv(filepath)
        )

        # Read back the file content to verify
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Normalize line endings to ensure cross-platform consistency (Windows \r\n vs Unix \n)
        content = content.replace('\r\n', '\n')

        expected_content = 'col1,col2,col3\nval1,"val2,with,comma",static\n'
        assert content == expected_content

def test_method_chaining_applies_sequential_transformations_without_intermediate_variables():
    initial_table = [['A', 'B', 'C'], [1, 2, 3], [4, 5, 6]]

    # Execute the exact chain specified without intermediate variables
    result = (
        petl.wrap(initial_table)
        .rename({'A': 'X'})
        .cut('X', 'C')
        .select('X', lambda v: v > 1)
    )

    # Verify the final output headers and rows
    assert petl.header(result) == ('X', 'C')
    assert tuple(tuple(row) for row in petl.data(result)) == ((4, 6),)

def test_header_retrieval_evaluates_first_row_only():
    def custom_generator():
        yield ['header1', 'header2']
        raise RuntimeError("Evaluated too far!")

    # Wrap the generator object directly
    table = petl.wrap(custom_generator())

    try:
        headers = petl.header(table)
    except RuntimeError:
        pytest.fail("header() evaluated beyond the first row and raised RuntimeError")

    assert headers == ('header1', 'header2')

def test_data_retrieval_yields_records_excluding_header_row():
    input_table = [['header_A', 'header_B'], ['row1_A', 'row1_B'], ['row2_A', 'row2_B']]

    table = petl.wrap(input_table)
    data_rows = tuple(tuple(row) for row in petl.data(table))

    expected_output = (('row1_A', 'row1_B'), ('row2_A', 'row2_B'))
    assert data_rows == expected_output

    # Explicitly assert that the header string does not exist anywhere in the yielded output
    for row in data_rows:
        assert 'header_A' not in row

def test_invoke_dicts_returns_iterator_of_header_mapped_dictionaries():
    # Standard & Short Row Input
    input_table = [['id', 'name', 'status'], [1, 'Alice', 'active'], [2, 'Bob']]
    table = petl.wrap(input_table)

    dicts_output = list(petl.dicts(table))
    expected_output = [
        {'id': 1, 'name': 'Alice', 'status': 'active'},
        {'id': 2, 'name': 'Bob', 'status': None}
    ]

    assert dicts_output == expected_output

    # Empty Data Edge Case
    empty_table = [['id', 'name', 'status']]
    empty_table_wrapped = petl.wrap(empty_table)

    empty_dicts_output = list(petl.dicts(empty_table_wrapped))
    assert empty_dicts_output == []