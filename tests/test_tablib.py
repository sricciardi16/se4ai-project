# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from tablib.exceptions import UnsupportedFormat
import tablib

# 4. Auxiliary: Standard Library
import datetime
import json


def test_dataset_csv_and_json_export_import_roundtrip():
    ds = tablib.Dataset(headers=['id', 'name', 'role'])
    ds.append([1, 'Alice', 'Admin'])
    ds.append([2, 'Bob', 'User'])
    ds.append([3, 'Charlie', 'Moderator'])

    # CSV Roundtrip
    csv_data = ds.export('csv')
    ds_csv = tablib.Dataset().load(csv_data, format='csv')

    assert ds_csv.headers == ['id', 'name', 'role']
    assert ds_csv.height == 3
    assert ds_csv.width == 3
    
    # CSV coerces all data to strings, so we assert against stringified values
    assert ds_csv[0] == ('1', 'Alice', 'Admin')
    assert ds_csv[1] == ('2', 'Bob', 'User')
    assert ds_csv[2] == ('3', 'Charlie', 'Moderator')

    # JSON Roundtrip
    json_data = ds.export('json')
    ds_json = tablib.Dataset().load(json_data, format='json')

    assert ds_json.headers == ['id', 'name', 'role']
    assert ds_json.height == 3
    assert ds_json.width == 3
    assert ds_json.dict == ds.dict


def test_dataset_tsv_export_import_roundtrip():
    ds = tablib.Dataset(headers=['product', 'price'])
    ds.append(['Apple', '1.00'])
    ds.append(['Banana', '0.50'])

    tsv_data = ds.export('tsv')
    assert '\t' in tsv_data

    ds_tsv = tablib.Dataset().load(tsv_data, format='tsv')

    assert ds_tsv.headers == ['product', 'price']
    assert ds_tsv.height == 2
    assert ds_tsv.width == 2
    assert ds_tsv[0] == ('Apple', '1.00')
    assert ds_tsv[1] == ('Banana', '0.50')


def test_dataset_export_csv_format():
    ds = tablib.Dataset(headers=['A', 'B'])
    ds.append([1, 2])

    csv_output = ds.export('csv')
    expected_output = "A,B\r\n1,2"

    assert csv_output.strip() == expected_output.strip()


def test_dataset_append_rows_columns_and_slicing():
    ds = tablib.Dataset(headers=['name'])
    ds.append(['Alice'])
    ds.append(['Bob'])
    ds.append(['Charlie'])

    assert ds.height == 3
    assert ds.width == 1

    ds.append_col(['New York', 'Los Angeles', 'Chicago'], header='city')

    assert ds.width == 2
    assert ds.headers == ['name', 'city']

    ds_dict = ds.dict
    assert 'city' in ds_dict[0]
    assert ds_dict[0]['city'] == 'New York'
    assert ds_dict[1]['city'] == 'Los Angeles'

    slice_2 = ds[:2]
    assert len(slice_2) == 2
    assert slice_2[0] == ('Alice', 'New York')
    assert slice_2[1] == ('Bob', 'Los Angeles')

    city_col = ds['city']
    assert list(city_col) == ['New York', 'Los Angeles', 'Chicago']


def test_dataset_insert_and_pop_rows():
    ds = tablib.Dataset(headers=['letter'])
    ds.append(['A'])
    ds.append(['C'])
    ds.append(['D'])

    assert ds.height == 3

    ds.insert(1, ['B'])

    assert ds.height == 4
    assert ds[0] == ('A',)
    assert ds[1] == ('B',)
    assert ds[2] == ('C',)
    assert ds[3] == ('D',)

    last_row = ds.pop()

    assert last_row == ('D',)
    assert ds.height == 3
    assert ds[-1] == ('C',)


def test_dataset_dict_property_maps_headers_to_row_values():
    dataset = tablib.Dataset()
    dataset.headers = ('col1', 'col2')
    dataset.append(('val1', 'val2'))

    data_dict = dataset.dict
    assert isinstance(data_dict, list)
    assert len(data_dict) == 1

    first_row = data_dict[0]
    assert list(first_row.keys()) == ['col1', 'col2']
    assert first_row['col1'] == 'val1'
    assert first_row['col2'] == 'val2'


def test_dataset_title_and_headers_persist_after_appending_rows():
    dataset = tablib.Dataset()
    dataset.title = "My Title"
    dataset.headers = ('A', 'B')

    dataset.append((1, 2))
    dataset.append((3, 4))

    assert dataset.title == "My Title"
    assert tuple(dataset.headers) == ('A', 'B')


def test_dataset_export_json_serializes_all_rows():
    dataset = tablib.Dataset(headers=('id', 'name'))
    dataset.append((1, 'Alice'))
    dataset.append((2, 'Bob'))

    json_str = dataset.export('json')
    assert isinstance(json_str, str)
    assert 'Alice' in json_str

    parsed = json.loads(json_str)
    assert isinstance(parsed, list)
    assert len(parsed) == dataset.height


def test_databook_json_export_import_preserves_multiple_sheets():
    ds1 = tablib.Dataset(headers=('id', 'name'))
    ds1.title = 'Sheet1'
    ds1.append((1, 'Alice'))

    ds2 = tablib.Dataset(headers=('age', 'city'))
    ds2.title = 'Sheet2'
    ds2.append((30, 'New York'))

    db = tablib.Databook([ds1, ds2])

    json_str = db.export('json')

    db_imported = tablib.Databook()
    db_imported.load(json_str, 'json')

    assert len(db_imported.sheets()) == 2

    imported_ds1 = db_imported.sheets()[0]
    imported_ds2 = db_imported.sheets()[1]

    assert imported_ds1.title == 'Sheet1'
    assert list(imported_ds1.headers) == ['id', 'name']
    assert imported_ds1[0] == (1, 'Alice')

    assert imported_ds2.title == 'Sheet2'
    assert list(imported_ds2.headers) == ['age', 'city']
    assert imported_ds2[0] == (30, 'New York')


def test_databook_add_sheet_and_iteration_preserves_order():
    book = tablib.Databook()

    ds1 = tablib.Dataset(["row1_col1", "row1_col2"], title="Sheet1")
    ds2 = tablib.Dataset(["row2_col1", "row2_col2"], title="Sheet2")
    ds3 = tablib.Dataset(["row3_col1", "row3_col2"], title="Sheet3")

    book.add_sheet(ds1)
    book.add_sheet(ds2)
    book.add_sheet(ds3)

    sheets = book.sheets()
    assert len(sheets) == 3

    assert sheets[0].title == "Sheet1"
    assert sheets[0][0] == ("row1_col1", "row1_col2")

    assert sheets[1].title == "Sheet2"
    assert sheets[1][0] == ("row2_col1", "row2_col2")

    assert sheets[2].title == "Sheet3"
    assert sheets[2][0] == ("row3_col1", "row3_col2")


def test_dataset_sequence_protocols_and_export_unsupported_format():
    ds = tablib.Dataset(headers=["ID", "Name"])
    ds.append([1, "Alice"])
    ds.append([2, "Bob"])

    assert len(ds) == 2
    assert ds[0] == (1, "Alice")
    assert ds[-1] == (2, "Bob")

    with pytest.raises(tablib.UnsupportedFormat):
        ds.export("invalid_format")


def test_dataset_export_large_payload_json_csv():
    ds = tablib.Dataset(headers=["IntCol", "FloatCol", "StringCol"])
    for i in range(600):
        ds.append([i, float(i) + 0.5, f"String_{i}"])

    json_data = ds.export("json")
    csv_data = ds.export("csv")

    assert isinstance(json_data, str)
    assert isinstance(csv_data, str)

    parsed_json = json.loads(json_data)
    assert len(parsed_json) == 600
    assert len(csv_data.splitlines()) == 601


def test_instantiate_dataset_with_args_populates_attributes():
    ds = tablib.Dataset(
        (1, "Alice", 25.5),
        (2, "Bob", None),
        (3, "Charlie", 0),
        headers=["ID", "Name", "Score"],
        title="Q1_Performance_Metrics"
    )

    assert ds.headers == ["ID", "Name", "Score"]
    assert ds.title == "Q1_Performance_Metrics"
    assert ds.width == 3
    assert ds.height == 3


def test_append_valid_row_increases_height_and_stores_data():
    ds = tablib.Dataset(headers=["Col1", "Col2", "Col3"])
    assert ds.width == 3
    initial_height = ds.height

    row_to_append = ["Dépôt", 9999999999, True]
    ds.append(row_to_append)

    assert ds.height == initial_height + 1
    assert ds[-1] == tuple(row_to_append)

def test_append_row_with_tags_allows_subsequent_filtering():
    dataset = tablib.Dataset(headers=["Name", "Role"])

    dataset.append(["Alice", "Admin"], tags=["active", "admin"])
    dataset.append(["Bob", "User"], tags=["inactive", "user"])

    admin_filtered = dataset.filter("admin")
    assert isinstance(admin_filtered, tablib.Dataset)
    assert len(admin_filtered) == 1
    assert admin_filtered[0] == ("Alice", "Admin")

    nonexistent_filtered = dataset.filter("nonexistent")
    assert isinstance(nonexistent_filtered, tablib.Dataset)
    assert len(nonexistent_filtered) == 0

    assert len(dataset) == 2


def test_append_valid_column_increases_width_and_updates_headers():
    dataset = tablib.Dataset(headers=["ID", "Name"])
    dataset.append([1, "Alice"])
    dataset.append([2, "Bob"])

    initial_width = dataset.width

    col_data = [datetime.date(2020, 2, 29), datetime.date(2024, 12, 31)]
    dataset.append_col(col_data, header="Hire Date")

    assert dataset.width == initial_width + 1
    assert dataset.headers[-1] == "Hire Date"
    assert dataset[0][-1] == datetime.date(2020, 2, 29)
    assert dataset[1][-1] == datetime.date(2024, 12, 31)


def test_append_col_with_mismatched_length():
    dataset = tablib.Dataset(headers=["ID"])
    dataset.append([1])
    dataset.append([2])
    dataset.append([3])

    with pytest.raises(Exception):
        dataset.append_col(['A', 'B'], header="Letters")

    with pytest.raises(Exception):
        dataset.append_col(['A', 'B', 'C', 'D'], header="Letters")

    with pytest.raises(Exception):
        dataset.append_col([], header="Letters")


def test_sort_by_header_and_index_returns_sorted_dataset():
    dataset = tablib.Dataset(headers=['ID', 'Name', 'Score'])
    dataset.append([3, 'Charlie', 85.5])
    dataset.append([1, 'Alice', 92.0])
    dataset.append([2, 'Bob', -15.0])

    # Sort returns a new dataset
    sorted_ds = dataset.sort('ID')
    assert sorted_ds[0][0] == 1
    assert sorted_ds[1][0] == 2
    assert sorted_ds[2][0] == 3

    sorted_ds2 = dataset.sort(2)
    assert sorted_ds2[0][2] == -15.0
    assert sorted_ds2[1][2] == 85.5
    assert sorted_ds2[2][2] == 92.0


def test_sort_with_nonexistent_column_raises_value_or_index_error():
    dataset = tablib.Dataset(headers=['A', 'B'])
    dataset.append([1, 2])
    dataset.append([3, 4])

    original_data = list(dataset)

    with pytest.raises(KeyError):
        dataset.sort('C')
    assert list(dataset) == original_data

    with pytest.raises(IndexError):
        dataset.sort(5)
    assert list(dataset) == original_data

    with pytest.raises(IndexError):
        dataset.sort(-99)
    assert list(dataset) == original_data


def test_filter_by_tag_returns_new_dataset_without_mutating_original():
    dataset = tablib.Dataset(headers=['Col1'])
    dataset.append(['Row 1'], tags=['active', 'admin'])
    dataset.append(['Row 2'], tags=['inactive'])
    dataset.append(['Row 3'], tags=['active', 'user'])

    filtered_dataset = dataset.filter('active')

    assert filtered_dataset.height == 2
    assert filtered_dataset[0] == ('Row 1',)
    assert filtered_dataset[1] == ('Row 3',)
    assert dataset.height == 3


def test_export_to_text_format_returns_valid_serialized_string():
    dataset = tablib.Dataset(headers=['ID', 'Description'])
    dataset.append([1, 'Text with "quotes" and, commas'])
    dataset.append([2, 'Unicode: 影師嗎'])

    csv_output = dataset.export('csv')
    assert isinstance(csv_output, str)
    assert '"Text with ""quotes"" and, commas"' in csv_output

    json_output = dataset.export('json')
    assert isinstance(json_output, str)

    parsed_json = json.loads(json_output)
    assert isinstance(parsed_json, list)
    assert len(parsed_json) == 2
    assert parsed_json[0]['ID'] == 1
    assert parsed_json[0]['Description'] == 'Text with "quotes" and, commas'
    assert parsed_json[1]['ID'] == 2
    assert parsed_json[1]['Description'] == 'Unicode: 影師嗎'


def test_export_binary_format_returns_byte_stream():
    dataset = tablib.Dataset(headers=['Name', 'Age', 'Score', 'Active'])
    dataset.append(['Alice', 42, 3.14, True])

    output = dataset.export('xlsx')
    assert isinstance(output, bytes)
    assert output.startswith(b'PK\x03\x04')


def test_export_unsupported_format_raises_unsupported_format_error():
    dataset = tablib.Dataset(headers=['A'])
    dataset.append([1])

    invalid_formats = ['pdf', 'docx', 'unknown_format_123', '', None, 'CSV']

    for fmt in invalid_formats:
        with pytest.raises(tablib.exceptions.UnsupportedFormat):
            dataset.export(fmt)


def test_export_dict_format_without_headers():
    dataset = tablib.Dataset()
    dataset.append(['Data1', 'Data2'])

    # Should export to JSON even without headers
    json_output = dataset.export('json')
    assert isinstance(json_output, str)

    # Should export to dict even without headers
    dict_output = dataset.dict
    assert isinstance(dict_output, list)


def test_load_valid_payload_populates_dataset_accurately():
    payload = "Name,Age,City\nJohn Doe,30,New York\n\"Smith, Jane\",25,London\n"
    dataset = tablib.Dataset()
    dataset.load(payload, format='csv')

    assert dataset.headers == ['Name', 'Age', 'City']
    assert dataset[0] == ('John Doe', '30', 'New York')
    assert dataset[1] == ('Smith, Jane', '25', 'London')

    exported = dataset.export('csv')

    dataset2 = tablib.Dataset()
    dataset2.load(exported, format='csv')

    assert dataset.headers == dataset2.headers
    assert dataset.dict == dataset2.dict


def test_load_without_format_autodetects_and_parses_payload():
    payload1 = '[{"id": 1, "name": "Test"}]'
    payload2 = 'id,name\n1,Test\n'
    payload3 = '  \n\n  [{"id": 1}]'

    ds1 = tablib.Dataset()
    ds1.load(payload1, format=None)
    assert ds1.headers == ['id', 'name']
    assert ds1[0] == (1, 'Test')

    ds2 = tablib.import_set(payload2, format=None)
    assert ds2.headers == ['id', 'name']
    assert ds2[0] == ('1', 'Test')

    ds3 = tablib.Dataset()
    ds3.load(payload3, format=None)
    assert ds3.headers == ['id']
    assert ds3[0] == (1,)


def test_load_new_data_clears_existing_dataset_state():
    dataset = tablib.Dataset(headers=['Old_Col_1', 'Old_Col_2'])
    dataset.append(['Stale_Data_A', 'Stale_Data_B'])

    payload = '[{"New_Col_1": "Fresh_Data_X", "New_Col_2": "Fresh_Data_Y"}]'
    dataset.load(payload, format='json')

    assert dataset.height == 1
    assert dataset.headers == ['New_Col_1', 'New_Col_2']

    # Verify the old data is completely gone
    for row in dataset:
        assert 'Stale_Data_A' not in row


def test_load_unsupported_format_raises_unsupported_format_error():
    dataset = tablib.Dataset()

    with pytest.raises(tablib.exceptions.UnsupportedFormat):
        dataset.load('some data', format='obscure_custom_format_xyz')

    with pytest.raises(tablib.exceptions.UnsupportedFormat):
        tablib.import_set('some data', format='obscure_custom_format_xyz')

    unrecognizable_payload = b'\x00\x01\x02\x03\x04\x05\xFF\xFE'
    with pytest.raises(tablib.exceptions.UnsupportedFormat):
        dataset.load(unrecognizable_payload, format=None)


def test_add_sheet_groups_multiple_datasets_into_databook():
    ds1 = tablib.Dataset(title="Alpha_Sheet")
    for i in range(5):
        ds1.append([f"alpha_data_{i}"])

    ds2 = tablib.Dataset(title="Beta_Sheet")

    ds3 = tablib.Dataset(title="Gamma_Sheet")
    for i in range(10):
        ds3.append([f"gamma_data_{i}"])

    db = tablib.Databook()
    db.add_sheet(ds1)
    db.add_sheet(ds2)
    db.add_sheet(ds3)

    sheets = db.sheets()

    assert len(sheets) == 3
    assert sheets[1].title == "Beta_Sheet"


def test_export_databook_serializes_to_multisheet_binary_with_titles():
    ds1 = tablib.Dataset(headers=['Metric', 'Value'], title='Q1_Financials_2023')
    ds1.append(['Revenue', 15000])

    ds2 = tablib.Dataset(headers=['Metric', 'Value'], title='Q2_Financials_2023')
    ds2.append(['Revenue', 18500])

    db = tablib.Databook()
    db.add_sheet(ds1)
    db.add_sheet(ds2)

    result = db.export('xlsx')
    assert isinstance(result, bytes)
    assert result.startswith(b'PK\x03\x04')


def test_export_databook_to_singlesheet_format_raises_unsupported_format_error():
    ds1 = tablib.Dataset(headers=['ID', 'Name'])
    ds1.append([1, 'Alice'])
    ds1.append([2, 'Bob'])

    ds2 = tablib.Dataset(headers=['ID', 'Name'])
    ds2.append([3, 'Charlie'])
    ds2.append([4, 'Diana'])

    db = tablib.Databook()
    db.add_sheet(ds1)
    db.add_sheet(ds2)

    with pytest.raises(UnsupportedFormat):
        db.export('csv')

    with pytest.raises(UnsupportedFormat):
        db.export('tsv')